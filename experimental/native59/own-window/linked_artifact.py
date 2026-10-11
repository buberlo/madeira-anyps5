#!/usr/bin/env python3
"""Qualify the retained unsigned test bundle. Never compile, copy, sign or launch."""
from pathlib import Path
import argparse, hashlib, json, os, stat, struct

HERE=Path(__file__).absolute().parent
ROOT=HERE.parents[2]
OLD=HERE.with_name('native58-own-window-direct-swift-xctest-overlay-proposal')
BUILD=OLD/'local-build-xctest-overlay'
FAILED_SHA='51d9128d3bf0afd8d9f91ed515b310cbcb3702f48e5c74fbe58944fc48bb03cf'
REVIEW_SHA='d1233d78fae49bd1f9ab610bbf8e26a616c69749263c0b40bd854a608d8415fe'
BINARY='Products/OwnWindowStillTests-Runner.app/PlugIns/OwnWindowStillTests.xctest/OwnWindowStillTests'
BINARY_SHA='746c60df6ed9fa715f4888197768a16b6d085e92956fec3e015d19504ab030ae'
METHOD='_$s19OwnWindowStillTestsAAC04testa10ForegroundC0yyKF'
THUNK=METHOD+'To'
CLASS='_OBJC_CLASS_$__TtC19OwnWindowStillTests19OwnWindowStillTests'
METHODS='__INSTANCE_METHODS__TtC19OwnWindowStillTests19OwnWindowStillTests'
CLASS_NAME='_TtC19OwnWindowStillTests19OwnWindowStillTests'
SELECTOR='testOwnForegroundStillAndReturnError:'

def need(ok,message):
 if not ok:raise ValueError(message)

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def fp(path):
 s=Path(path).lstat()
 return [s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns]

def identity(path):
 p=Path(path);s=p.stat();l=p.lstat()
 return {'literalPath':str(p),'resolvedPath':str(p.resolve()),
  'stat':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_mode,s.st_nlink],
  'literalStat':[l.st_dev,l.st_ino,l.st_size,l.st_mtime_ns,l.st_ctime_ns,l.st_mode,l.st_nlink]}

def receipt_identity(row):
 dev,ino,size,mtime,ctime,mode,nlink=row['stat']
 return {'dev':dev,'ino':ino,'size':size,'mtime_ns':mtime,'ctime_ns':ctime,'mode':mode,'nlink':nlink}

def contract(raw):
 """Bounded parsing of this exact ARM64 bundle and local chained rebase form."""
 need(32<=len(raw)<=1<<20,'Bounded complete linked test binary')
 magic,cpu,subtype,kind,ncmds,size,flags,reserved=struct.unpack_from('<8I',raw)
 need(magic==0xfeedfacf and cpu==0x100000c and kind==8 and ncmds<=512 and size<=len(raw)-32,'ARM64 MH_BUNDLE header')
 end=32+size;pos=32;sections=[];symbols=[];versions=[];rpaths=[];dylibs=[];fixup_segments=[]
 def file_read(at,n):
  need(0<=at and 0<=n and at+n<=len(raw),'Bounded file range')
  return raw[at:at+n]
 def file_cstring(at,extent):
  data=file_read(at,extent);need(b'\0' in data,'Terminated bounded Mach-O string')
  return data.split(b'\0',1)[0].decode('utf8')
 for _ in range(ncmds):
  need(pos+8<=end,'Complete load command');cmd,n=struct.unpack_from('<2I',raw,pos)
  need(n>=8 and n%4==0 and pos+n<=end,'Bounded load command')
  if cmd==0x19:
   need(n>=72,'Complete segment command')
   name,vm,sz,offset,fs,mp,ip,ns,sflags=struct.unpack_from('<16sQQQQiiII',raw,pos+8)
   need(ns<=64 and n==72+ns*80 and offset+fs<=len(raw),'Bounded exact segment sections')
   for i in range(ns):
    r=struct.unpack_from('<16s16sQQIIIIIIII',raw,pos+72+i*80)
    sections.append({'name':r[0].rstrip(b'\0').decode(),'segment':r[1].rstrip(b'\0').decode(),
     'vm':r[2],'size':r[3],'offset':r[4],'flags':r[8]})
  if cmd==0x32:
   need(n>=24,'Complete build version');platform,minos,sdk,tools=struct.unpack_from('<4I',raw,pos+8)
   need(n==24+tools*8 and tools<=8,'Bounded build tool records')
   versions.append({'platform':platform,'minimumOS':minos,'sdk':sdk})
  if cmd in (0xc,0x80000018,0x8000001f,0x8000001c):
   need(n>=12,'Complete load string');at=struct.unpack_from('<I',raw,pos+8)[0]
   need(12<=at<n,'Bounded load string offset')
   (rpaths if cmd==0x8000001c else dylibs).append(file_cstring(pos+at,n-at))
  if cmd==2:
   need(n==24,'Exact symbol-table command');so,count,to,ts=struct.unpack_from('<4I',raw,pos+8)
   need(count<=100000 and so+count*16<=len(raw) and to+ts<=len(raw),'Bounded symbol table')
   for i in range(count):
    index,typ,section,desc,value=struct.unpack_from('<IBBHQ',raw,so+i*16)
    need(index<ts,'Bounded symbol string offset')
    name=file_cstring(to+index,ts-index)
    if not typ&0xe0 and (typ&0xe)==0xe:
     need(1<=section<=len(sections),'Defined symbol section exists')
     symbols.append({'name':name,'section':section,'value':value,'type':typ})
  if cmd==0x80000034:
   need(n==16,'Exact chained fixup command');at,extent=struct.unpack_from('<2I',raw,pos+8)
   data=file_read(at,extent);need(len(data)>=28,'Complete chained fixup header')
   version,starts,imports,strings,count,fmt,sfmt=struct.unpack_from('<7I',data)
   need(version==0 and starts+4<=len(data),'Known chained fixup version')
   ns=struct.unpack_from('<I',data,starts)[0];need(ns<=64 and starts+4+ns*4<=len(data),'Bounded chained segment list')
   for i in range(ns):
    delta=struct.unpack_from('<I',data,starts+4+i*4)[0]
    if not delta:continue
    p=starts+delta;need(p+22<=len(data),'Complete chained segment')
    sz,page,fmt,vm,maxptr,np=struct.unpack_from('<IHHQIH',data,p)
    need(fmt==6 and sz>=22+np*2 and p+sz<=len(data) and page in (4096,16384),'Exact local64-offset chained rebase form')
    fixup_segments.append((vm,vm+page*np))
  pos+=n
 need(pos==end and versions==[{'platform':2,'minimumOS':0x110000,'sdk':0x1b0000}],'Exact iOS17/iOS27 SDK deployment')
 need('@loader_path/../../Frameworks' in rpaths and '@rpath/XCTest.framework/XCTest' in dylibs,'Retained XCTest/rpath linkage')
 def section(vm,n=1):
  rows=[s for s in sections if s['vm']<=vm and vm+n<=s['vm']+s['size']]
  need(len(rows)==1,'Unique bounded VM section');s=rows[0]
  need((s['flags']&0xff) not in (1,12,18) and s['offset']+s['size']<=len(raw),'File-backed VM section')
  return s
 def vmread(vm,n):
  s=section(vm,n);return file_read(s['offset']+vm-s['vm'],n)
 def string(vm):
  s=section(vm);return file_cstring(s['offset']+vm-s['vm'],s['vm']+s['size']-vm)
 def pointer(vm):
  need(any(a<=vm and vm+8<=b for a,b in fixup_segments),'Pointer lies in declared chained64-offset segment')
  bits=struct.unpack('<Q',vmread(vm,8))[0]
  need(not bits>>63 and ((bits>>36)&0x7fff)==0,'Local rebase; no bind, high8 or reserved bits')
  return bits&((1<<36)-1)
 def defined(name):
  rows=[r for r in symbols if r['name']==name];need(len(rows)==1,'Exactly one defined own symbol: '+name)
  r=rows[0];s=sections[r['section']-1]
  need(s['vm']<=r['value']<s['vm']+s['size'],'Defined symbol lies in its section')
  return r
 method=defined(METHOD);thunk=defined(THUNK);cls=defined(CLASS);methods=defined(METHODS)
 for r in (method,thunk):need((sections[r['section']-1]['segment'],sections[r['section']-1]['name'])==('__TEXT','__text'),'Own method and thunk are defined executable text')
 ro=pointer(cls['value']+32)&~7
 need(string(pointer(ro+24))==CLASS_NAME and pointer(ro+32)==methods['value'],'Own class metadata names exact class and owns exact method list')
 flags,count=struct.unpack('<2I',vmread(methods['value'],8));need(flags==0x8000000c and count==4,'Exact four-entry relative own method list')
 entries=[]
 for i in range(count):
  vm=methods['value']+8+i*12;nr,tr,ir=struct.unpack('<3i',vmread(vm,12))
  entries.append({'selector':string(pointer(vm+nr)),'encoding':string(vm+4+tr),'implementation':vm+8+ir})
 selected=[r for r in entries if r['selector']==SELECTOR]
 need(len(selected)==1 and selected[0]['encoding']=='B24@0:8^@16' and selected[0]['implementation']==thunk['value'],'Exact throwing-test selector points to own defined ObjC thunk')
 text=sections[thunk['section']-1];later=[r['value'] for r in symbols if r['section']==thunk['section'] and r['value']>thunk['value']]
 stop=min(later+[text['vm']+text['size']]);need(0<stop-thunk['value']<=4096,'Bounded own thunk extent')
 calls=[]
 for vm in range(thunk['value'],stop,4):
  ins=struct.unpack('<I',vmread(vm,4))[0]
  if ins>>26==0x25:
   imm=ins&0x3ffffff
   if imm&0x2000000:imm-=0x4000000
   if vm+4*imm==method['value']:calls.append(vm)
 need(len(calls)==1,'Own ObjC thunk has one direct BL to exact defined Swift method')
 return {'architecture':'arm64','fileType':8,'deployment':versions[0],'method':method,'objcThunk':thunk,
  'class':CLASS_NAME,'selector':selected[0],'objcThunkCallsSwiftMethodAt':calls[0],
  'rpaths':rpaths,'XCTestDependencies':[n for n in dylibs if 'XCTest' in n],
  'literalSourceNameInRawSwiftSymbolRequired':False,'definedSymbolsOnly':True}

def qualify():
 need(sha(BUILD/'receipt.json')==FAILED_SHA and sha(OLD/'source-review-freeze.json')==REVIEW_SHA,'Exact historical failure and source review')
 r=json.loads((BUILD/'receipt.json').read_bytes());source=json.loads((OLD/'source-review-freeze.json').read_bytes())
 need(r['sourceReviewSha256']==REVIEW_SHA,'Actual two commands used exact held source review')
 need(r['status']=='failed_local_direct_swift_own_window_runner_build_not_device_ready' and r['failure']=='ValueError: Actual freshly linked own screenshot test and iOS17 deployment','Only exact false symbol predicate failure')
 need(r['outputInventoryComplete'] and r['finalSourceIdentityMatchesInitial'] and not r['finalSourceIdentityErrors'],'Original complete output/source closure')
 need(len(r['commands'])==2 and len(r['actualChildCleanupJournal'])==2,'Exactly two actual compiler/linker rows')
 for command,journal in zip(r['commands'],r['actualChildCleanupJournal']):
  need(command['exitCode']==0 and command['ownedHostChildJoined'] and command['ownedHostGroupAbsentAfterCleanup'] and command['discardedBytes']==0 and journal['argv']==command['argv'] and journal['childReaped'] and journal['groupAbsenceObserved'] and journal['monitorAndWaitJoined'] and journal['stdoutDrainJoined'] and journal['cleanupErrors']==[] and journal['failure'] is None,'Actual two commands completed and all owned tasks/groups closed')
 need(all(r[k] is False for k in ('signed','runnerInstalled','deviceActions','xctestExecuted','screenshotsCaptured','actualCaptureReady')),'Unsigned local artifact only')
 before={n:identity(n) for n in source['inputs']}
 for n,digest in source['inputs'].items():
  need(before[n]==source['finalInputFingerprints'][n] and receipt_identity(before[n])==r['finalSourceInputIdentities'][n] and sha(n)==digest,'Exact retained source/API/tool bytes and stable identity: '+n)
 need(BUILD.resolve()==BUILD and not any(x.is_symlink() for x in (BUILD,*BUILD.parents)),'Unlinked actual output root')
 snapshots={};names=set();logical=allocated=0
 for base,dirs,files in os.walk(BUILD,followlinks=False):
  for name in dirs:
   q=Path(base)/name;need(stat.S_ISDIR(q.lstat().st_mode) and not q.is_symlink(),'Only retained ordinary output directories')
  for name in files:
   q=Path(base)/name;relative=str(q.relative_to(BUILD));s=q.lstat()
   need(stat.S_ISREG(s.st_mode) and s.st_nlink==1,'Only single-link retained output leaves')
   snapshots[relative]=fp(q);logical+=s.st_size;allocated+=s.st_blocks*512
   if relative=='receipt.json':continue
   names.add(relative);need(relative in r['outputs'] and r['outputs'][relative]=={'bytes':s.st_size,'sha256':sha(q)},'Actual output differs from preserved failure row: '+relative)
 need(names==set(r['outputs']) and len(names)==175 and max(logical,allocated)<=200<<20,'Exact complete retained175 outputs and unchanged200 MiB cap')
 need(sha(BUILD/BINARY)==BINARY_SHA,'Exact actually linked binary bytes')
 result=contract((BUILD/BINARY).read_bytes())
 swift=OLD/'OwnWindowStillTests/OwnWindowStillTests.swift'
 need('final class OwnWindowStillTests: XCTestCase' in swift.read_text() and 'func testOwnForegroundStill() throws' in swift.read_text(),'Exact bound source class and throwing selector origin')
 need(all(identity(n)==s for n,s in before.items()) and all(fp(BUILD/n)==s for n,s in snapshots.items()),'Final complete source/output identity bracket')
 need(sha(BUILD/'receipt.json')==FAILED_SHA,'Original failed receipt preserved')
 value={'schema':1,'status':'actual_unsigned_linked_own_test_bundle_requalified_not_assembled_signed_installed_or_executed',
  'originalFailedReceipt':{'path':str(BUILD/'receipt.json'),'sha256':FAILED_SHA,'originalStatusPreserved':True},
  'originalSourceReviewSha256':REVIEW_SHA,'linkedBinary':{'path':str(BUILD/BINARY),'sha256':BINARY_SHA,'bytes':(BUILD/BINARY).stat().st_size},
  'correctedTestBinaryContract':result,'actualCompileAndLinkExitZero':True,'actualOwnedCommandAndGroupClosureVerified':True,
  'outputCount':len(names),'completeOutputs':r['outputs'],'currentOutputIdentities':snapshots,'logicalBytesIncludingFailedReceipt':logical,'allocatedBytesIncludingFailedReceipt':allocated,
  'sourceProviderCount':len(before),'allSourceHashesAndSavedIdentitiesMatched':True,'finalSourceAndOutputIdentitiesUnchanged':True,
  'qualifierSourceSha256':sha(Path(__file__)),'compilerActions':False,'outputsCopiedOrMutated':False,
  'sdkRunnerAssembled':False,'signed':False,'runnerInstalled':False,'deviceActions':False,'xctestExecuted':False,
  'screenshotsCaptured':False,'actualCaptureReady':False,'actualSdkConsumedDependencyClosureCaptured':False}
 path=HERE/'artifact-qualification.json'
 with path.open('x') as f:json.dump(value,f,sort_keys=True,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 print(json.dumps({'path':str(path),'sha256':sha(path),'outputs':len(names),'status':value['status']}))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--qualify',action='store_true');a=p.parse_args()
 if a.qualify:qualify()
 else:print('Inert; no compiler, copy, signing or device action.')
