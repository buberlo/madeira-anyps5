#!/usr/bin/env python3
"""Assemble the already linked unsigned test with exact retained SDK bytes."""
from pathlib import Path
import argparse, asyncio, hashlib, importlib.util, json, os, plistlib, shutil, stat, struct, sys, time
sys.dont_write_bytecode=True
HERE=Path(__file__).absolute().parent
OLD=HERE.with_name('native58-own-window-direct-swift-xctest-overlay-proposal')
QUAL=HERE.with_name('native58-own-window-linked-artifact-revalidation-proposal')
SOURCE_SHA='d1233d78fae49bd1f9ab610bbf8e26a616c69749263c0b40bd854a608d8415fe'
QUAL_SHA='fbcf5f7cd90c937df424f7f24804135bee5421e47068ce2ff32812d38b78a07a'
FINISH_SHA='428b1edb51c2b01726e2afd17d023d0c8c0eca91aaa9d8adad8c3d2d8457bce0'
OUTPUT=HERE/'assembled-unsigned'

def need(ok,message):
 if not ok:raise ValueError(message)

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def load(path):return json.loads(Path(path).read_bytes())

def module(path,name):
 spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

def admission(q):
 need(q['status']=='actual_unsigned_linked_own_test_bundle_requalified_not_assembled_signed_installed_or_executed'
  and q['originalFailedReceipt']['sha256']=='51d9128d3bf0afd8d9f91ed515b310cbcb3702f48e5c74fbe58944fc48bb03cf'
  and q['originalSourceReviewSha256']==SOURCE_SHA and q['qualifierSourceSha256']==FINISH_SHA
  and q['actualCompileAndLinkExitZero'] and q['actualOwnedCommandAndGroupClosureVerified']
  and q['allSourceHashesAndSavedIdentitiesMatched'] and q['finalSourceAndOutputIdentitiesUnchanged']
  and q['outputCount']==len(q['completeOutputs'])==175 and q['sourceProviderCount']==231,
  'Only actual qualified746c test from preserved51d9 build')
 need(all(q[k] is False for k in ('compilerActions','outputsCopiedOrMutated','sdkRunnerAssembled','signed','runnerInstalled','deviceActions','xctestExecuted','screenshotsCaptured','actualCaptureReady')),
  'Unsigned unassembled local artifact boundary')

def output_path(path):
 path=Path(path)
 need(path==OUTPUT and path.is_absolute() and path==path.resolve() and not any(p.is_symlink() for p in (path,*path.parents)) and not path.exists(),'New fixed exclusive ordinary assembly output')
 return path

def targets(mapping):
 need(len(mapping)==125 and len(set(mapping.values()))==125,'Exact125 distinct retained SDK members')
 for name in mapping:
  p=Path(name)
  need(not p.is_absolute() and '..' not in p.parts and p.as_posix()==name and not any(x in ('','.') for x in name.split('/')),'Ordinary exact relative SDK target')
 need(set(n for n in mapping if not n.startswith('Frameworks/'))=={'OwnWindowStillTests-Runner','Info.plist','PkgInfo','version.plist'},'Exact runner leaf scope')

def retained():
 need(sha(QUAL/'artifact-qualification.json')==QUAL_SHA and sha(QUAL/'finish.py')==FINISH_SHA
  and sha(OLD/'source-review-freeze.json')==SOURCE_SHA,'Held artifact qualification/source definitions')
 q=load(QUAL/'artifact-qualification.json');admission(q);source=load(OLD/'source-review-freeze.json')
 f=module(QUAL/'finish.py','assembly_retained_qualifier')
 before={n:f.identity(n) for n in source['inputs']}
 for n,h in source['inputs'].items():
  need(before[n]==source['finalInputFingerprints'][n] and sha(n)==h,'Exact retained source/SDK provider: '+n)
 original=Path(q['originalFailedReceipt']['path'])
 need(original==f.BUILD/'receipt.json' and sha(original)==f.FAILED_SHA,'Original failed receipt remains historical')
 for n,s in q['currentOutputIdentities'].items():need(f.fp(f.BUILD/n)==s,'Retained actual output identity changed: '+n)
 actual=set()
 for base,dirs,files in os.walk(f.BUILD,followlinks=False):
  for n in dirs:need(stat.S_ISDIR((Path(base)/n).lstat().st_mode),'Retained actual output link/special directory')
  for n in files:
   path=Path(base)/n;name=str(path.relative_to(f.BUILD));s=path.lstat()
   need(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and name in q['currentOutputIdentities'],'Retained actual ordinary output closure')
   actual.add(name)
   if name!='receipt.json':need(q['completeOutputs'].get(name)=={'bytes':s.st_size,'sha256':sha(path)},'Retained actual output bytes changed: '+name)
 need(actual==set(q['currentOutputIdentities']),'Retained actual output tree exact')
 linked=Path(q['linkedBinary']['path'])
 need(linked==f.BUILD/f.BINARY and sha(linked)==f.BINARY_SHA,'Actual retained746c linked binary')
 need(f.contract(linked.read_bytes())==q['correctedTestBinaryContract'],'Actual linked method/selector/thunk/deployment contract')
 # Imports run in this new host process only. No retained module/file is modified.
 prior=list(sys.path);sys.path.insert(0,str(OLD))
 try:d=module(OLD/'direct_build.py','assembly_retained_direct')
 finally:sys.path[:]=prior
 mapping=d.runtime_map();need(mapping==source['runtimeProviders'],'Exact held SDK runtime mapping');targets(mapping)
 inputs={**source['inputs'],str(OLD/'source-review-freeze.json'):SOURCE_SHA,
  str(QUAL/'artifact-qualification.json'):QUAL_SHA,str(QUAL/'finish.py'):FINISH_SHA,
  str(original):f.FAILED_SHA,str(linked):f.BINARY_SHA}
 inputs.update({str(f.BUILD/n):r['sha256'] for n,r in q['completeOutputs'].items()})
 snapshots={n:f.fp(n) for n in inputs}
 need(all(f.identity(n)==s for n,s in before.items()),'Retained complete source identity bracket')
 return q,source,f,d,mapping,inputs,snapshots

def runner_header(raw):
 need(len(raw)>=48,'Complete retained universal SDK runner header')
 magic,count=struct.unpack_from('>2I',raw)
 need(magic==0xcafebabe and count==2,'Exact retained arm64/arm64e SDK runner')
 slices=[]
 for i in range(count):
  cpu,subtype,offset,extent,align=struct.unpack_from('>5I',raw,8+i*20)
  need(cpu==0x100000c and subtype in (0,0x80000002) and align==14 and offset>=48
   and offset%(1<<align)==0 and extent>=32 and offset+extent<=len(raw),'Bounded aligned SDK ARM64 slice')
  mh,mc,ms,kind,ncmds,size,flags,reserved=struct.unpack_from('<8I',raw,offset)
  need(mh==0xfeedfacf and mc==cpu and ms==subtype and kind==2 and ncmds<=512 and size<=extent-32,'Actual ARM64 SDK runner executable slice')
  slices.append({'cpuSubtype':subtype,'offset':offset,'bytes':extent,'fileType':kind})
 need({s['cpuSubtype'] for s in slices}=={0,0x80000002} and slices[0]['offset']+slices[0]['bytes']<=slices[1]['offset'],'Distinct retained ARM64/ARM64e runner slices')
 return {'architecture':'arm64_and_arm64e','fileType':2,'slices':slices,'providerBytesCopiedExactly':True}

async def assemble(recipe_sha):
 review_path=HERE/'source-review.json';need(sha(review_path)==recipe_sha,'Exact root-reviewed assembly recipe')
 review=load(review_path)
 for n,h in review['inputs'].items():need(sha(n)==h,'Assembly recipe/provider definition changed')
 q,source,f,d,mapping,inputs,snapshots=retained();root=output_path(OUTPUT)
 inputs.update(review['inputs']);inputs[str(review_path)]=recipe_sha
 for n in inputs:snapshots[n]=f.fp(n)
 need(shutil.disk_usage(HERE).free>=d.p.LIVE_BUILD+d.p.MAX_BUILD,'Unchanged6.6 GiB reserve plus whole200 MiB allowance')
 root.mkdir();deadline=time.monotonic()+180;started=time.monotonic();error=None;app=None
 def guard():
  need(shutil.disk_usage(root).free>=d.p.LIVE_BUILD,'Unchanged6.6 GiB live reserve')
  need(time.monotonic()<deadline,'Assembly180-second deadline')
  for n,s in snapshots.items():need(f.fp(n)==s,'Bound input identity changed: '+n)
 try:
  destination=root/'Products'/d.APP/'PlugIns'/(d.NAME+'.xctest')/d.NAME
  await d.write(destination,Path(q['linkedBinary']['path']).read_bytes(),root,guard,deadline,0o755)
  app=await d.assemble(root,mapping,source['inputs'],guard,deadline)
  need(d.runtime_map()==mapping,'SDK runtime membership unchanged through assembly')
  outputs,logical,allocated=d.b.inventory(root,d.output_limit())
  expected={str(Path('Products')/d.APP/n) for n in mapping}
  expected|={str(Path('Products')/d.APP/'PlugIns'/(d.NAME+'.xctest')/n) for n in (d.NAME,'Info.plist')}
  need(set(outputs)==expected and len(outputs)==127,'Exact125 SDK members plus linked test and plist')
  for target,provider in mapping.items():
   raw=Path(provider).read_bytes()
   if target=='Info.plist':raw=d.runner_plist(raw)
   need((app/target).read_bytes()==raw,'Independent assembled SDK byte readback: '+target)
  test=app/'PlugIns'/(d.NAME+'.xctest')/d.NAME
  need(sha(test)==f.BINARY_SHA and f.contract(test.read_bytes())==q['correctedTestBinaryContract'],'Independent assembled defined test linkage')
  need((app/'PlugIns'/(d.NAME+'.xctest')/'Info.plist').read_bytes()==d.test_plist(),'Exact test plist bytes')
  info=plistlib.loads((app/'Info.plist').read_bytes())
  need(info['CFBundleIdentifier']==d.p.RUNNER and info['CFBundleExecutable']==d.NAME+'-Runner' and info['MinimumOSVersion']=='17.0','Own runner metadata')
  native=runner_header((app/(d.NAME+'-Runner')).read_bytes())
  hashes={n:{'sha256':sha(root/n),'bytes':s[2]} for n,s in outputs.items()}
  need(d.b.inventory(root,d.output_limit())[0]==outputs,'Final assembled output identities stable')
  for n,h in inputs.items():need(sha(n)==h,'Final complete input bytes changed: '+n)
  guard()
 except BaseException as e:error=type(e).__name__+': '+str(e)
 rows,logical,allocated=d.b.inventory(root,d.output_limit())
 value={'schema':1,'status':('actual_unsigned_own_xctest_runner_assembled_not_signed_installed_or_executed' if error is None else 'failed_local_unsigned_runner_assembly'),
  'failure':error,'assemblyOnly':True,'artifactQualificationSha256':QUAL_SHA,'originalFailedReceiptSha256':f.FAILED_SHA,
  'assemblyRecipeSha256':recipe_sha,'linkedTestBinarySha256':f.BINARY_SHA,'sourceReviewSha256':SOURCE_SHA,
  'inputs':inputs,'initialInputIdentities':snapshots,'finalInputIdentities':{n:f.fp(n) for n in snapshots},
  'sdkRuntimeProviders':mapping,'outputs':{n:{'sha256':sha(root/n),'bytes':s[2]} for n,s in rows.items()},
  'outputFileCount':len(rows),'logicalBytes':logical,'allocatedBytes':allocated,'outputCapBytes':d.p.MAX_BUILD,
  'deadlineSeconds':180,'seconds':time.monotonic()-started,'liveReserveBytes':d.p.LIVE_BUILD,
  'runnerExecutableContract':native if error is None else None,'definedOwnTestContract':q['correctedTestBinaryContract'] if error is None else None,
  'actualSdkConsumedDependencyClosureCaptured':False,'compilerActions':False,'hostChildrenSpawned':0,
  'originalBuildOrFailureMutated':False,'signed':False,'runnerInstalled':False,'deviceActions':False,
  'xctestExecuted':False,'screenshotsCaptured':False,'actualCaptureReady':False}
 d.terminal_receipt(root,{**value,'outputInventoryComplete':True})
 print(json.dumps({'status':value['status'],'receiptSha256':sha(root/'receipt.json'),'files':len(rows),'bytes':logical,'failure':error}))
 need(error is None,'Assembly failed; retained partial output and separate truthful receipt')

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--assemble',action='store_true');parser.add_argument('--recipe-sha256');a=parser.parse_args()
 if a.assemble:
  need(a.recipe_sha256,'Explicit root-reviewed assembly source digest');asyncio.run(assemble(a.recipe_sha256))
 else:print('Inert assembly-only recipe; no compiler/signing/install/device action.')
