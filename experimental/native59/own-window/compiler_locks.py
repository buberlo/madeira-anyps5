"""Live Swift ModuleCache lock metadata/atomic-temp rescans; no final exception."""
from pathlib import Path
import errno,os,re,stat
import protocol as p
import bounded_child as b

PCM_LOCK=r'ModuleCache/[A-Z0-9]{1,32}/[A-Za-z_][A-Za-z0-9_]{0,127}-[A-Z0-9]{1,32}\.pcm\.lock'
SWIFT_MODULE=r'ModuleCache/[A-Za-z_][A-Za-z0-9_]{0,127}-[A-Z0-9]{1,32}'
SWIFT_LOCK=SWIFT_MODULE+r'\.swiftmodule\.lock'
SWIFT_TEMP=re.compile(SWIFT_MODULE+r'-[0-9a-f]{8}\.swiftmodule\.tmp')
LOCK=re.compile(r'(?:'+PCM_LOCK+r'|'+SWIFT_LOCK+r')')
SCANS=4;SAMPLES=16
class Disappeared(Exception):
 def __init__(self,path):self.path=path
def name(root,path):return str(path.relative_to(root))
def transient_name(root,path):
 relative=name(root,path)
 return bool(LOCK.fullmatch(relative) or SWIFT_TEMP.fullmatch(relative) or
             (len(relative)>9 and re.fullmatch('[0-9a-f]{8}',relative[-8:]) and
              relative[-9]=='-' and LOCK.fullmatch(relative[:-9])))
def stamp(s):
 return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_uid,s.st_size,s.st_blocks,s.st_mtime_ns,s.st_ctime_ns)
def read_stat(root,path):
 try:return path.lstat()
 except OSError as e:
  if (type(e)is FileNotFoundError and e.errno==errno.ENOENT and
      e.filename==str(path) and transient_name(root,path)):
   raise Disappeared(path) from e
  raise b.InventoryRefusal('Owned output lstat failed',{'path':str(path),'errno':e.errno,
   'mode':None,'nlink':None,'type':'unobserved_lstat_failure'}) from e
def link_metadata(root,path,s):
 if not (LOCK.fullmatch(name(root,path)) and s.st_nlink==1 and s.st_uid==os.getuid()):
  b.refusal(path,s,'Only exact own live LLVM module-lock symlinks')
 try:target=os.readlink(path)
 except OSError as e:
  if type(e)is FileNotFoundError and e.errno==errno.ENOENT and e.filename==str(path):
   raise Disappeared(path) from e
  raise b.InventoryRefusal('Owned compiler-lock readlink failed',{'path':str(path),'errno':e.errno,
   'mode':s.st_mode,'nlink':s.st_nlink,'type':'symlink'}) from e
 prefix=str(path)+'-'
 if not (type(target)is str and len(os.fsencode(target))<=4096 and
         target.startswith(prefix) and re.fullmatch('[0-9a-f]{8}',target[len(prefix):]) and
         s.st_size==len(os.fsencode(target))):
  b.refusal(path,s,'Exact same-parent absolute eight-hex LLVM lock target required')
 # lstat/readlink/lstat brackets only the link itself; never stat/open/hash target.
 after=read_stat(root,path)
 if stamp(after)!=stamp(s):b.refusal(path,after,'Compiler-lock metadata changed during readlink')
 return {'path':name(root,path),'target':target,'dev':s.st_dev,'ino':s.st_ino,
  'mode':s.st_mode,'nlink':s.st_nlink,'uid':s.st_uid,'logicalBytes':s.st_size,
  'allocatedBytes':s.st_blocks*512,'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns,
  'targetFollowedOrHashed':False}
def members(base):
 # os.walk classifies symlink targets with is_dir(); use names only instead.
 # Every member type below comes from lstat, never a target-following stat.
 with os.scandir(base) as scan:return sorted(entry.name for entry in scan)
def inventory(root,limit,journal):
 root=b.unlinked_parent(root)
 for attempt in range(SCANS):
  rows={};total=allocated=0;pending=[root];journal['scanCount']+=1
  try:
   while pending:
    base=pending.pop()
    # Scandir failures are not classified as leaf races or silently omitted.
    for member in members(base):
     path=base/member;s=read_stat(root,path)
     if stat.S_ISDIR(s.st_mode):
      if transient_name(root,path):b.refusal(path,s,'Compiler-lock/temp names cannot be directories')
      pending.append(path);continue
     if not (stat.S_ISREG(s.st_mode) and s.st_nlink==1) and not stat.S_ISLNK(s.st_mode):
      b.refusal(path,s,'Only single-link files or exact live compiler-lock metadata')
     total+=s.st_size;allocated+=s.st_blocks*512
     p.need(max(total,allocated)<=limit and len(rows)<8192,'Owned aggregate bytes/file cap')
     if stat.S_ISLNK(s.st_mode):
      row=link_metadata(root,path,s)
      if row not in journal['lockSamples']:
       if len(journal['lockSamples'])<SAMPLES:journal['lockSamples'].append(row)
       else:journal['lockSamplesTruncated']=True
     rows[name(root,path)]=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
   journal['completedScanCount']+=1
   return rows,total,allocated
  except Disappeared as e:
   journal['retryCount']+=1
   if attempt==SCANS-1:
    raise b.InventoryRefusal('Exact compiler-lock/temp disappearance exhausted four complete scans',
     {'path':str(e.path),'errno':errno.ENOENT,'mode':None,'nlink':None,'type':'live_compiler_cache_disappeared'}) from e
   # Restart whole inventory and all byte/file counters; never skip a missing row.
 raise AssertionError('Bounded compiler inventory must return or refuse')

def observations():
 return {'scope':'only_live_compile_swift_ModuleCache_lock_metadata_atomic_temp_rescan','scanCount':0,
  'completedScanCount':0,'retryCount':0,'lockSamples':[],'lockSamplesTruncated':False,
  'targetFollowedOrHashed':False,'finalInventoryException':False}
