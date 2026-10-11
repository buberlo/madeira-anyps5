#!/usr/bin/env python3
"""Opt-in LOCAL unsigned build only. No test, signing, install or device CLI."""
from pathlib import Path
import argparse,asyncio,json,os,shutil,sys,time
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import protocol as p,bounded_child as b
def identity(name):
 s=Path(name).stat()
 return {'dev':s.st_dev,'ino':s.st_ino,'mode':s.st_mode,'nlink':s.st_nlink,'size':s.st_size,
         'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns}
def check_identities(before):
 for name,expected in before.items():
  actual=identity(name)
  p.need(actual==expected,'Held source/API identity changed: '+name+'; fields='+
         ','.join(k for k in expected if actual.get(k)!=expected[k]))
def review(digest):
 path=p.HERE/'source-review-freeze.json';p.need(p.sha(path)==digest,'Exact held source review')
 value=p.unique_json(path.read_bytes())
 for name,h in value['inputs'].items():p.need(p.sha(name)==h,'Held source/API/tool changed')
 return value
async def build(digest,root):
 source=review(digest);root=b.unlinked_parent(root)
 p.need(root.parent==p.HERE and not root.exists() and root.name.startswith('local-build-'),'New exclusive own local build root')
 p.need(shutil.disk_usage(root.parent).free>=p.LIVE_BUILD+p.MAX_BUILD,'6.6 GiB live reserve plus whole200 MiB build allowance')
 before={n:identity(n) for n in source['inputs']}
 before[str(p.HERE/'source-review-freeze.json')]=identity(p.HERE/'source-review-freeze.json')
 root.mkdir()
 def guard():
  p.need(shutil.disk_usage(root).free>=p.LIVE_BUILD,'Native installer6.6 GiB reserve retained')
  check_identities(before)
 status='failed_local_own_window_runner_build_not_device_ready';error=None;row=None
 try:
  row=await b.command(p.build_command(root),root,guard,time.monotonic()+180,p.MAX_BUILD,label='local-build')
  product=root/'Products/Debug-iphoneos/OwnWindowStillTests-Runner.app'
  binary=product/'PlugIns/OwnWindowStillTests.xctest/OwnWindowStillTests'
  p.need(binary.is_file() and (product/'OwnWindowStillTests-Runner').is_file(),'Fresh actual runner and test binary required')
  review(digest);guard();status='actual_local_unsigned_own_window_runner_built_not_installed_or_device_executed'
 except BaseException as e:error=type(e).__name__+': '+str(e)
 rows,logical,allocated=b.inventory(root,p.MAX_BUILD)
 result={'schema':1,'status':status,'sourceReviewSha256':digest,'command':row,'failure':error,
  'sourceInputIdentities':before,'finalSourceInputIdentities':{n:identity(n) for n in before},
  'fileIdentityFields':['dev','ino','mode','nlink','size','mtime_ns','ctime_ns'],'accessTimeExcluded':True,
  'outputs':{n:{'sha256':p.sha(root/n),'bytes':s[2]} for n,s in rows.items()},
  'logicalBytes':logical,'allocatedBytes':allocated,'localOutputCapBytes':p.MAX_BUILD,
  'liveNativeInstallerReserveBytes':p.LIVE_BUILD,'signed':False,'runnerInstalled':False,
  'deviceActions':False,'xctestExecuted':False,'screenshotsCaptured':False,'actualCaptureReady':False}
 raw=p.canonical(result)+b'\n';p.need(logical+len(raw)<=p.MAX_BUILD,'Final receipt within200 MiB')
 with (root/'receipt.json').open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 print(json.dumps({'status':status,'receiptSha256':p.sha(root/'receipt.json'),'failure':error,'bytes':logical}))
 p.need(error is None,'Local build failed; retain bounded outputs')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--build-local',action='store_true');a.add_argument('--source-review-sha256');a.add_argument('--output');v=a.parse_args()
 if v.build_local:
  p.need(v.source_review_sha256 and v.output,'Explicit held source digest and new output required')
  asyncio.run(build(v.source_review_sha256,Path(v.output)))
 else:print(json.dumps({'status':'source_only_local_runner_build_inert','buildActions':False,'deviceActions':False}))
