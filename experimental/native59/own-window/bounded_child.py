"""Finite exact host-child group, streamed log cap and aggregate disk guard."""
from pathlib import Path
import asyncio,os,resource,signal,stat,time
import protocol as p
class InventoryRefusal(ValueError):
 def __init__(self,message,details):
  self.details=details
  super().__init__(message+'; '+str(details))
def refusal(path,s,message):
 kind=('regular' if stat.S_ISREG(s.st_mode) else 'directory' if stat.S_ISDIR(s.st_mode) else
       'symlink' if stat.S_ISLNK(s.st_mode) else 'fifo' if stat.S_ISFIFO(s.st_mode) else
       'socket' if stat.S_ISSOCK(s.st_mode) else 'other_nonregular')
 raise InventoryRefusal(message,{'path':str(path),'mode':s.st_mode,'modeOctal':oct(s.st_mode),
  'nlink':s.st_nlink,'type':kind,'dev':s.st_dev,'ino':s.st_ino,'size':s.st_size})
def unlinked_parent(root):
 root=Path(root)
 p.need(root.is_absolute() and root==root.resolve() and not any(x.is_symlink() for x in [root,*root.parents]),'Canonical unlinked owned output path before mkdir')
 return root
def inventory(root,limit):
 root=unlinked_parent(root);rows={};total=allocated=0
 def error(e):raise e
 for base,dirs,files in os.walk(root,followlinks=False,onerror=error):
  for name in dirs:
   path=Path(base)/name
   if path.is_symlink():refusal(path,path.lstat(),'Directory link in owned output')
  for name in files:
   path=Path(base)/name
   try:s=path.lstat()
   except OSError as e:
    raise InventoryRefusal('Owned output lstat failed',{'path':str(path),'errno':e.errno,
     'mode':None,'nlink':None,'type':'unobserved_lstat_failure'}) from e
   if not (stat.S_ISREG(s.st_mode) and s.st_nlink==1):
    refusal(path,s,'Only unlinked single-link owned output files')
   total+=s.st_size;allocated+=s.st_blocks*512
   p.need(max(total,allocated)<=limit and len(rows)<8192,'Owned aggregate bytes/file cap')
   rows[str(path.relative_to(root))]=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
 return rows,total,allocated
async def command(argv,root,guard,deadline,limit,*,label='child',clock=time.monotonic,journal=None):
 p.need(argv[0] in (str(p.XCODE),str(p.RESULT),str(p.SWIFT),str(p.CLANG)),'Only exact Xcode/result/local compiler tools')
 root=unlinked_parent(root);p.need(root.is_dir(),'Owned output exists before child')
 log=root/(label+'.log');p.need(not log.exists(),'Exclusive child log')
 guard();inventory(root,limit)
 env={k:v for k,v in os.environ.items() if not k.startswith('DEVICECTL_CHILD_') and k not in ('PYMOBILEDEVICE3_TUNNEL','PYMOBILEDEVICE3_NATIVE','PYMOBILEDEVICE3_USERSPACE')}
 env.update(DEVELOPER_DIR='/Applications/Xcode.app/Contents/Developer',TMPDIR=str(root/'tmp'),
            XDG_CACHE_HOME=str(root/'Caches'),SWIFT_MODULECACHE_PATH=str(root/'ModuleCache'))
 (root/'tmp').mkdir(exist_ok=True)
 def file_cap():resource.setrlimit(resource.RLIMIT_FSIZE,(limit,limit))
 child=None;owned_pgid=None;drain=None;monitor=None;wait=None;written=discarded=0;failed=None
 observed={'argv':argv,'label':label,'pid':None,'pgid':None,'spawned':False,
  'groupVerifiedAfterSpawn':False,'groupKillRequested':False,'childReaped':False,
  'monitorAndWaitJoined':False,'stdoutDrainJoined':False,'groupAbsenceObserved':False,
  'cleanupErrors':[],'failure':None,'inventoryFailureDetails':None}
 async def read():
  nonlocal written,discarded
  with log.open('xb') as f:
   while True:
    data=await child.stdout.read(65536)
    if not data:break
    take=min(len(data),(1<<20)-written)
    if take:f.write(data[:take]);written+=take
    discarded+=len(data)-take
   f.flush();os.fsync(f.fileno())
 from compiler_locks import inventory as compiler_inventory,observations
 lock_observations=observations()
 observed['liveCompilerLockMetadata']=lock_observations
 async def watch():
  while True:
   guard()
   if argv[0]==str(p.SWIFT) and label=='compile-swift':compiler_inventory(root,limit,lock_observations)
   else:inventory(root,limit)
   p.need(clock()<deadline,'Owned child deadline')
   p.need(discarded==0,'Child stdout overflow refuses acceptance')
   await asyncio.sleep(.05)
 try:
  child=await asyncio.create_subprocess_exec(*argv,env=env,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.STDOUT,start_new_session=True,preexec_fn=file_cap)
  observed.update(pid=child.pid,spawned=True)
  # Successful subprocess creation with start_new_session has completed setsid
  # in this exact child. Retain that group even if its leader subsequently exits.
  owned_pgid=child.pid
  observed['pgid']=owned_pgid
  try:
   p.need(os.getpgid(child.pid)==owned_pgid,'Exact own host process group')
   observed['groupVerifiedAfterSpawn']=True
  except ProcessLookupError:
   # The session can finish between successful exec and this sanity read.
   p.need(child.returncode is not None,'Host leader disappeared before verification')
  drain=asyncio.create_task(read());monitor=asyncio.create_task(watch());wait=asyncio.create_task(child.wait())
  done,_=await asyncio.wait((wait,monitor),return_when=asyncio.FIRST_COMPLETED)
  if monitor in done:await monitor
  code=await wait;p.need(code==0,'Owned child nonzero exit')
 except BaseException as error:
  failed=error
  observed['inventoryFailureDetails']=getattr(error,'details',None)
 finally:
  cleanup_errors=[]
  if child is not None:
   # A session created for only this command; no global process search/kill.
   try:
    if owned_pgid is not None:
     observed['groupKillRequested']=True;os.killpg(owned_pgid,signal.SIGKILL)
   except ProcessLookupError:pass
   except BaseException as e:cleanup_errors.append('group kill: '+type(e).__name__)
   try:
    await asyncio.wait_for(child.wait(),3);observed['childReaped']=True
   except BaseException as e:cleanup_errors.append('child reap: '+type(e).__name__)
  for task in (monitor,wait):
   if task is not None and not task.done():task.cancel()
  try:
   await asyncio.wait_for(asyncio.gather(*(t for t in (monitor,wait) if t is not None),return_exceptions=True),3)
   observed['monitorAndWaitJoined']=True
  except BaseException as e:cleanup_errors.append('monitor/wait join: '+type(e).__name__)
  if drain is not None:
   try:
    await asyncio.wait_for(drain,3);observed['stdoutDrainJoined']=True
   except BaseException as e:
    drain.cancel();await asyncio.gather(drain,return_exceptions=True)
    cleanup_errors.append('stdout drain: '+type(e).__name__)
  if owned_pgid is not None:
   until=clock()+3
   try:
    while True:
     try:os.killpg(owned_pgid,0)
     except ProcessLookupError:
      observed['groupAbsenceObserved']=True;break
     p.need(clock()<until,'Owned host process group survived cleanup')
     await asyncio.sleep(.05)
   except BaseException as e:cleanup_errors.append('group absence: '+type(e).__name__)
  if cleanup_errors:
   failed=ValueError('Owned host cleanup failed: '+', '.join(cleanup_errors)+
                     ('; original '+type(failed).__name__ if failed is not None else ''))
  observed.update(exitCode=child.returncode if child is not None else None,
   stdoutRetainedBytes=written,discardedBytes=discarded,cleanupErrors=cleanup_errors,
   failure=type(failed).__name__+': '+str(failed) if failed is not None else None)
  if journal is not None:journal.append(observed)
 if failed is not None:raise failed
 guard();inventory(root,limit);p.need(discarded==0,'No discarded output acceptance')
 return {'argv':argv,'pid':child.pid,'exitCode':child.returncode,'ownedHostChildJoined':True,
         'ownedHostGroupAbsentAfterCleanup':True,'stdoutRetainedBytes':written,'discardedBytes':discarded,'remoteTestServicesClosedClaimed':False}
