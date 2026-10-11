#!/usr/bin/env python3
"""Opt-in unsigned SDK test-runner assembly; never test/sign/install/activate."""
from pathlib import Path
import argparse,asyncio,json,os,plistlib,shutil,stat,struct,sys,time
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import protocol as p,bounded_child as b,local_build as held

SDK=Path('/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS27.0.sdk')
PLATFORM=Path('/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer')
TC=p.SWIFT.parent.parent
RUNNER=PLATFORM/'Library/Xcode/Agents/XCTRunner.app'
FRAMEWORKS=('XCTest','XCUIAutomation','XCTestCore','XCTAutomationSupport','XCUnit','XCTestSupport')
NAME='OwnWindowStillTests'
APP=NAME+'-Runner.app'
TARGET='arm64-apple-ios17.0'
RECEIPT_CAP=512<<10
def output_limit():return p.MAX_BUILD-RECEIPT_CAP

def terminal_receipt(root,value):
 # Child cleanup has already run. Refusal of output inventory is never success.
 # A fixed small receipt reserve is counted inside the unchanged200 MiB cap.
 root=b.unlinked_parent(root);p.need(stat.S_ISDIR(root.lstat().st_mode),'Ordinary owned receipt root')
 raw=p.canonical(value)+b'\n';p.need(len(raw)<=RECEIPT_CAP,'Bounded512 KiB terminal receipt')
 if value['outputInventoryComplete']:
  p.need(max(value['logicalBytes'],value['allocatedBytes'])+len(raw)+4096<=p.MAX_BUILD,'Receipt inside whole200 MiB')
 path=root/'receipt.json';flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW
 fd=os.open(path,flags,0o600)
 with os.fdopen(fd,'wb') as f:
  for offset in range(0,len(raw),65536):f.write(raw[offset:offset+65536])
  f.flush();os.fsync(f.fileno())
 return path

def runtime_map():
 rows={}
 for name in FRAMEWORKS:
  location='Frameworks' if name in ('XCTest','XCUIAutomation') else 'PrivateFrameworks'
  source=PLATFORM/'Library'/location/(name+'.framework')
  p.need(source.is_dir() and not source.is_symlink(),'Exact SDK framework directory')
  for path in sorted(source.rglob('*')):
   p.need(not path.is_symlink(),'No ambiguous SDK framework link')
   if path.is_file():rows['Frameworks/'+name+'.framework/'+str(path.relative_to(source))]=str(path)
   else:p.need(path.is_dir(),'Only SDK directory or regular file')
 rows['Frameworks/libXCTestSwiftSupport.dylib']=str(PLATFORM/'usr/lib/libXCTestSwiftSupport.dylib')
 for name in ('XCTRunner','Info.plist','PkgInfo','version.plist'):
  rows[(NAME+'-Runner') if name=='XCTRunner' else name]=str(RUNNER/name)
 return rows

def commands(root):
 root=b.unlinked_parent(root);obj=root/'Intermediates'/ (NAME+'.o')
 module=root/'Intermediates'/ (NAME+'.swiftmodule')
 output=root/'Products'/APP/'PlugIns'/(NAME+'.xctest')/NAME
 swift=[str(p.SWIFT),'-emit-object','-emit-module','-emit-module-path',str(module),
  '-emit-dependencies','-parse-as-library','-module-name',NAME,'-swift-version','5',
  '-target',TARGET,'-sdk',str(SDK),'-F',str(PLATFORM/'Library/Frameworks'),
  '-F',str(SDK/'Developer/Library/Frameworks'),'-I',str(PLATFORM/'usr/lib'),'-g','-Onone','-enable-testing',
  '-module-cache-path',str(root/'ModuleCache'),'-sdk-module-cache-path',str(root/'SDKModuleCache'),
  '-clang-scanner-module-cache-path',str(root/'ClangScannerCache'),
  '-Xcc','-fmodules-cache-path='+str(root/'ModuleCache'),
  str(p.HERE/'OwnWindowStillTests/OwnWindowStillTests.swift'),'-o',str(obj)]
 # The actual failed Xcode manifest specifies ARM64 iOS17 + MH_BUNDLE,
 # XCTest/XCTestSwiftSupport and these platform framework/runtime searches.
 link=[str(p.CLANG),'-target',TARGET,'-bundle','-isysroot',str(SDK),
  '-iframework',str(PLATFORM/'Library/Frameworks'),
  '-iframework',str(SDK/'Developer/Library/Frameworks'),
  '-L'+str(PLATFORM/'usr/lib'),'-L'+str(TC/'lib/swift/iphoneos'),'-L/usr/lib/swift',
  str(obj),'-Xlinker','-rpath','-Xlinker','/usr/lib/swift',
  '-Xlinker','-rpath','-Xlinker','@loader_path/Frameworks',
  '-Xlinker','-rpath','-Xlinker','@loader_path/../../Frameworks',
  '-Xlinker','-add_ast_path','-Xlinker',str(module),'-rdynamic','-fobjc-link-runtime',
  '-framework','XCTest','-lXCTestSwiftSupport','-o',str(output)]
 return swift,link

def runner_plist(raw):
 row=plistlib.loads(raw)
 p.need(row['CFBundleIdentifier']=='$(WRAPPEDPRODUCTBUNDLEIDENTIFIER)' and
        row['CFBundleExecutable']=='$(WRAPPEDPRODUCTNAME)','Exact SDK runner template')
 row.update(CFBundleIdentifier=p.RUNNER,CFBundleExecutable=NAME+'-Runner',
            CFBundleName=NAME+'-Runner',MinimumOSVersion='17.0')
 p.need('$(' not in json.dumps(row),'No unresolved runner template fields')
 return plistlib.dumps(row,fmt=plistlib.FMT_BINARY,sort_keys=True)

def test_plist():
 return plistlib.dumps({'CFBundleIdentifier':p.RUNNER.removesuffix('.xctrunner'),
  'CFBundleExecutable':NAME,'CFBundleName':NAME,'CFBundlePackageType':'BNDL',
  'CFBundleInfoDictionaryVersion':'6.0','CFBundleVersion':'1','CFBundleShortVersionString':'1.0',
  'CFBundleSupportedPlatforms':['iPhoneOS'],'MinimumOSVersion':'17.0','DTPlatformName':'iphoneos',
  'UIDeviceFamily':[1,2]},fmt=plistlib.FMT_BINARY,sort_keys=True)

def macho(raw,expected):
 # No external parser needed. Reject wrong type/architecture/truncated commands.
 p.need(len(raw)>=32,'Complete thin Mach-O header')
 magic,cpu,subtype,kind,ncmds,size,flags,reserved=struct.unpack_from('<8I',raw)
 p.need(magic==0xfeedfacf and cpu==0x100000c and kind==expected and
        ncmds<=512 and size<=len(raw)-32,'Actual ARM64 thin Mach-O type')
 offset=32;end=32+size;loads=[];rpaths=[];symbols=[];platform=None
 for _ in range(ncmds):
  p.need(offset+8<=end,'Bounded Mach-O command header');cmd,n=struct.unpack_from('<2I',raw,offset)
  p.need(n>=8 and n%4==0 and offset+n<=end,'Bounded Mach-O command')
  if cmd in (0xc,0x80000018,0x8000001f,0x8000001c):
   p.need(n>=12,'Complete Mach-O string command');pos=struct.unpack_from('<I',raw,offset+8)[0]
   p.need(12<=pos<n,'Bounded Mach-O string offset');s=raw[offset+pos:offset+n]
   p.need(b'\0' in s,'Terminated Mach-O string');name=s.split(b'\0',1)[0].decode('utf8')
   (rpaths if cmd==0x8000001c else loads).append(name)
  if cmd==0x32:
   p.need(n>=24,'Complete Mach-O deployment command');platform,minos,sdk,tools=struct.unpack_from('<4I',raw,offset+8)
   p.need(platform==2 and minos==0x110000,'Exact ARM64 iOS17 deployment')
  if cmd==2:
   p.need(n==24,'Exact symbol-table command');symoff,count,stroff,strsize=struct.unpack_from('<4I',raw,offset+8)
   p.need(count<=100000 and symoff+count*16<=len(raw) and stroff+strsize<=len(raw),'Bounded real symbol table')
   for i in range(count):
    index=struct.unpack_from('<I',raw,symoff+i*16)[0]
    p.need(index<strsize,'Bounded symbol string');tail=raw[stroff+index:stroff+strsize]
    p.need(b'\0' in tail,'Terminated symbol string');symbol=tail.split(b'\0',1)[0].decode('utf8')
    if NAME in symbol or 'testOwnForegroundStill' in symbol:symbols.append(symbol)
  offset+=n
 p.need(offset==end,'Exact Mach-O command extent')
 return {'architecture':'arm64','fileType':kind,'loadDylibs':loads,'rpaths':rpaths,
         'iOS17DeploymentObserved':platform==2,'ownTestSymbols':symbols}

async def write(path,data,root,guard,deadline,mode=0o644):
 guard();p.need(time.monotonic()<deadline,'Whole local build180-second deadline')
 p.need(len(data)<=32<<20,'Selected SDK/test member cap')
 rows,total,allocated=b.inventory(root,output_limit())
 p.need(max(total,allocated)+len(data)+4096<=output_limit(),'Prewrite whole200 MiB cap')
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as f:
  for i in range(0,len(data),65536):
   f.write(data[i:i+65536]);await asyncio.sleep(0)
   guard();p.need(time.monotonic()<deadline,'Assembly deadline')
  f.flush();os.fsync(f.fileno())
 path.chmod(mode);b.inventory(root,output_limit())

async def assemble(root,mapping,expected,guard,deadline):
 app=root/'Products'/APP
 for target,source in mapping.items():
  p.need(Path(target).is_relative_to('.') and '..' not in Path(target).parts,'Exact relative SDK output')
  p.need(stat.S_ISREG(Path(source).stat().st_mode) and p.sha(source)==expected[source],'Exact SDK runtime provider bytes')
  raw=Path(source).read_bytes()
  if target=='Info.plist':raw=runner_plist(raw)
  mode=0o755 if target.endswith((NAME+'-Runner', '.dylib')) or Path(source).stat().st_mode&0o111 else 0o644
  await write(app/target,raw,root,guard,deadline,mode)
 await write(app/'PlugIns'/(NAME+'.xctest')/'Info.plist',test_plist(),root,guard,deadline)
 return app

async def build(digest,root):
 source=held.review(digest);root=b.unlinked_parent(root)
 p.need(root.parent==p.HERE and root.name.startswith('local-build-') and not root.exists(),'New exclusive own local build')
 p.need(shutil.disk_usage(root.parent).free>=p.LIVE_BUILD+p.MAX_BUILD,'6.6 GiB plus whole200 MiB allowance')
 before={n:held.identity(n) for n in source['inputs']}
 before[str(p.HERE/'source-review-freeze.json')]=held.identity(p.HERE/'source-review-freeze.json')
 mapping=runtime_map();p.need(mapping==source['runtimeProviders'],'Exact declared SDK runner/framework tree')
 root.mkdir();deadline=time.monotonic()+180;rows=[];error=None;contracts=None;journal=[];failure_details=None
 def guard():
  p.need(shutil.disk_usage(root).free>=p.LIVE_BUILD,'Native installer6.6 GiB live reserve')
  held.check_identities(before)
 try:
  for name in ('Intermediates','ModuleCache','SDKModuleCache','ClangScannerCache'):(root/name).mkdir()
  bundle=root/'Products'/APP/'PlugIns'/(NAME+'.xctest');bundle.mkdir(parents=True)
  for label,argv in zip(('compile-swift','link-test-bundle'),commands(root)):
   rows.append(await b.command(argv,root,guard,deadline,output_limit(),label=label,journal=journal))
  contracts=macho((bundle/NAME).read_bytes(),8)
  p.need(contracts['iOS17DeploymentObserved'] and any('testOwnForegroundStill' in n for n in contracts['ownTestSymbols']),
         'Actual freshly linked own screenshot test and iOS17 deployment')
  p.need('@loader_path/../../Frameworks' in contracts['rpaths'],'Test bundle reaches SDK runner frameworks')
  p.need(any(n.endswith('XCTest.framework/XCTest') for n in contracts['loadDylibs']),'Actual XCTest bundle dependency')
  await assemble(root,mapping,source['inputs'],guard,deadline)
  p.need(runtime_map()==source['runtimeProviders'],'SDK runtime tree unchanged through assembly')
  held.review(digest);guard();b.inventory(root,output_limit())
 except BaseException as e:
  error=type(e).__name__+': '+str(e);failure_details=getattr(e,'details',None)
 outputs={};logical=allocated=None;inventory_complete=False;inventory_error=None;output_hashes={}
 try:
  outputs,logical,allocated=b.inventory(root,output_limit())
  output_hashes={n:{'sha256':p.sha(root/n),'bytes':s[2]} for n,s in outputs.items()}
  p.need(b.inventory(root,output_limit())[0]==outputs,'Final output tree changed during hash readback')
  inventory_complete=True
 except BaseException as e:
  inventory_error={'error':type(e).__name__+': '+str(e),'details':getattr(e,'details',None)}
  if error is None:error=inventory_error['error'];failure_details=inventory_error['details']
  output_hashes={};logical=allocated=None
 final_identities={};identity_errors={}
 for n in before:
  try:final_identities[n]=held.identity(n)
  except BaseException as e:identity_errors[n]=type(e).__name__+': '+str(e)
 if identity_errors and error is None:error='Final source identity readback failed'
 if final_identities!=before and error is None:error='Final source identity differs from initial'
 value={'schema':1,'status':('actual_local_unsigned_direct_swift_own_window_runner_built_not_installed_or_device_executed' if error is None else
  'failed_local_direct_swift_own_window_runner_build_not_device_ready'),'failure':error,
  'sourceReviewSha256':digest,'commands':rows,'testBinaryContract':contracts,
  'actualChildCleanupJournal':journal,'inventoryFailureDetails':failure_details,
  'outputInventoryComplete':inventory_complete,'terminalInventoryFailure':inventory_error,
  'sourceInputIdentities':before,'finalSourceInputIdentities':final_identities,'finalSourceIdentityErrors':identity_errors,
  'finalSourceIdentityMatchesInitial':not identity_errors and final_identities==before,
  'outputs':output_hashes,
  'logicalBytes':logical,'allocatedBytes':allocated,'localOutputCapBytes':p.MAX_BUILD,
  'liveNativeInstallerReserveBytes':p.LIVE_BUILD,'deadlineSeconds':180,
  'xcodeBuildServiceUsed':False,'signed':False,'runnerInstalled':False,'deviceActions':False,
  'xctestExecuted':False,'screenshotsCaptured':False,'actualCaptureReady':False,
  'actualSdkConsumedDependencyClosureCaptured':False,'failureReceiptCapBytes':RECEIPT_CAP,
  'compilerOutputLimitBytes':output_limit(),'guardsGenerallyRelaxed':False}
 path=terminal_receipt(root,value)
 print(json.dumps({'status':value['status'],'receiptSha256':p.sha(path),'failure':error,'bytes':logical}))
 p.need(error is None,'Local direct build failed; exact outputs preserved')

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--build-local',action='store_true');parser.add_argument('--source-review-sha256');parser.add_argument('--output');a=parser.parse_args()
 if a.build_local:
  p.need(a.source_review_sha256 and a.output,'Explicit held source digest and new output')
  asyncio.run(build(a.source_review_sha256,Path(a.output)))
 else:print(json.dumps({'status':'source_only_direct_swift_runner_inert','buildActions':False,'deviceActions':False}))
