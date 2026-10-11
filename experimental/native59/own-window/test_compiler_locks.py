"""Tiny real links and fake race/child controls; no compilers or SDK copies."""
from pathlib import Path
import asyncio,errno,os,stat,tempfile,time,types,unittest
from unittest.mock import patch
import protocol as p,bounded_child as b,compiler_locks as c,direct_build as d
from test_support import FakeChild,kill_fake

class Locks(unittest.TestCase):
 def setUp(self):
  tmp=tempfile.TemporaryDirectory(dir=p.HERE);self.addCleanup(tmp.cleanup);self.root=Path(tmp.name)
  self.path=self.root/'ModuleCache/11RCZM9PV10C/CoreFoundation-37X8IICWG4GXC.pcm.lock'
  self.path.parent.mkdir(parents=True)
 def link(self,target=None):self.path.symlink_to(target or str(self.path)+'-0123abcd')
 def run_inventory(self,limit=8192):
  journal=c.observations();result=c.inventory(self.root,limit,journal);return result,journal
 def test_exact_live_link_metadata_and_logical_bytes_without_target_read(self):
  self.link();s=self.path.lstat()
  original=Path.stat
  def no_target_stat(path,*a,**kw):
   if str(path).startswith(str(self.path)) and kw.get('follow_symlinks') is not False:raise AssertionError('No lock target stat')
   return original(path,*a,**kw)
  with (patch.object(Path,'open',side_effect=AssertionError('No target open')),
       patch.object(Path,'stat',no_target_stat),
       patch.object(p,'sha',side_effect=AssertionError('No target hash'))):
   (rows,logical,allocated),j=self.run_inventory()
  self.assertEqual(logical,s.st_size);self.assertEqual(allocated,s.st_blocks*512)
  self.assertEqual(len(rows),1);self.assertEqual(j['completedScanCount'],1)
  self.assertEqual(j['lockSamples'][0]['target'],str(self.path)+'-0123abcd')
  self.assertFalse(j['lockSamples'][0]['targetFollowedOrHashed'])
 def test_regular_owner_file_is_separately_counted(self):
  target=Path(str(self.path)+'-0123abcd');target.write_bytes(b'host 123');self.link()
  (rows,total,allocated),j=self.run_inventory()
  self.assertEqual(len(rows),2);self.assertEqual(total,len(b'host 123')+self.path.lstat().st_size)
 def test_final_default_inventory_still_rejects_same_link(self):
  self.link()
  with self.assertRaises(b.InventoryRefusal):b.inventory(self.root,8192)
 def test_link_logical_bytes_enforce_unchanged_limit(self):
  self.link()
  with self.assertRaisesRegex(ValueError,'aggregate'):self.run_inventory(self.path.lstat().st_size-1)
 def test_link_allocated_blocks_enforce_limit(self):
  self.link();original=Path.lstat;s=self.path.lstat()
  fields={n:getattr(s,n) for n in ('st_dev','st_ino','st_mode','st_nlink','st_uid','st_size','st_mtime_ns','st_ctime_ns','st_blocks')}
  fields['st_blocks']=100
  def fake(path,*a,**kw):return types.SimpleNamespace(**fields) if path==self.path else original(path,*a,**kw)
  with patch.object(Path,'lstat',fake),self.assertRaisesRegex(ValueError,'aggregate'):self.run_inventory(4096)
 def test_foreign_absolute_target_refused(self):
  self.link('/foreign/CoreFoundation.pcm.lock-0123abcd')
  with self.assertRaises(b.InventoryRefusal):self.run_inventory()
 def test_relative_target_refused(self):
  self.link(self.path.name+'-0123abcd')
  with self.assertRaises(b.InventoryRefusal):self.run_inventory()
 def test_normalized_parent_escape_target_refused(self):
  self.link(str(self.path.parent)+'/../11RCZM9PV10C/'+self.path.name+'-0123abcd')
  with self.assertRaises(b.InventoryRefusal):self.run_inventory()
 def test_other_lock_suffix_refused(self):
  for suffix in ('-0123ABCD','-0123abc','-0123abcde','-0123abcd/child','-0123abcd\n'):
   self.link(str(self.path)+suffix)
   with self.assertRaises(b.InventoryRefusal):self.run_inventory()
   self.path.unlink()
 def test_other_cache_root_refused(self):
  path=self.root/'SDKModuleCache/11RCZM9PV10C/CoreFoundation-37X8IICWG4GXC.pcm.lock';path.parent.mkdir(parents=True)
  path.symlink_to(str(path)+'-0123abcd')
  with self.assertRaises(b.InventoryRefusal):self.run_inventory()
 def test_unknown_module_cache_link_refused(self):
  path=self.path.parent/'unknown.lock';path.symlink_to(str(path)+'-0123abcd')
  with self.assertRaises(b.InventoryRefusal):self.run_inventory()
 def test_unique_owner_name_may_not_itself_be_link(self):
  path=Path(str(self.path)+'-0123abcd');path.symlink_to('/foreign')
  with self.assertRaises(b.InventoryRefusal):self.run_inventory()
 def test_directory_link_refused_without_follow(self):
  (self.root/'foreign-dir').mkdir();self.path.symlink_to(self.root/'foreign-dir',target_is_directory=True)
  with self.assertRaises(b.InventoryRefusal):self.run_inventory()
 def test_metadata_owner_uid_and_nlink_refused(self):
  self.link();original=Path.lstat;s=self.path.lstat()
  fields={n:getattr(s,n) for n in ('st_dev','st_ino','st_mode','st_nlink','st_uid','st_size','st_mtime_ns','st_ctime_ns','st_blocks')}
  for key,value in (('st_uid',os.getuid()+1),('st_nlink',2)):
   changed={**fields,key:value}
   def fake(path,*a,**kw):return types.SimpleNamespace(**changed) if path==self.path else original(path,*a,**kw)
   with patch.object(Path,'lstat',fake),self.assertRaises(b.InventoryRefusal):self.run_inventory()
 def test_changed_link_stamp_after_readlink_refused(self):
  self.link();original=c.read_stat;calls=0
  def fake(root,path):
   nonlocal calls
   s=original(root,path)
   if path==self.path:calls+=1
   if path==self.path and calls==2:
    fields={n:getattr(s,n) for n in ('st_dev','st_ino','st_mode','st_nlink','st_uid','st_size','st_mtime_ns','st_ctime_ns','st_blocks')};fields['st_ino']+=1
    return types.SimpleNamespace(**fields)
   return s
  with patch.object(c,'read_stat',fake),self.assertRaisesRegex(b.InventoryRefusal,'metadata changed'):self.run_inventory()
 def test_unknown_directory_error_is_not_omitted_or_retried(self):
  for error in (FileNotFoundError(errno.ENOENT,'missing',str(self.path.parent)),PermissionError(errno.EACCES,'denied',str(self.path.parent))):
   calls=[]
   def bad(*a,**kw):calls.append(1);raise error
   with patch.object(c,'members',bad),self.assertRaises(type(error)):self.run_inventory()
   self.assertEqual(len(calls),1)
 def test_unknown_leaf_disappearance_not_retried(self):
  path=self.root/'unknown';path.write_bytes(b'x');original=Path.lstat
  def fake(x,*a,**kw):
   if x==path:raise FileNotFoundError(errno.ENOENT,'missing',str(x))
   return original(x,*a,**kw)
  with patch.object(Path,'lstat',fake),self.assertRaises(b.InventoryRefusal):self.run_inventory()
 def test_known_leaf_eacces_not_retried(self):
  self.link();original=Path.lstat
  def fake(x,*a,**kw):
   if x==self.path:raise PermissionError(errno.EACCES,'denied',str(x))
   return original(x,*a,**kw)
  with patch.object(Path,'lstat',fake),self.assertRaises(b.InventoryRefusal):self.run_inventory()
 def test_missing_error_for_other_filename_not_retried(self):
  self.link();original=Path.lstat
  def fake(x,*a,**kw):
   if x==self.path:raise FileNotFoundError(errno.ENOENT,'missing','/other')
   return original(x,*a,**kw)
  with patch.object(Path,'lstat',fake),self.assertRaises(b.InventoryRefusal):self.run_inventory()
 def test_known_owner_disappearance_restarts_whole_counts(self):
  path=Path(str(self.path)+'-0123abcd');path.write_bytes(b'123');original=Path.lstat;calls=0
  def fake(x,*a,**kw):
   nonlocal calls
   if x==path:
    calls+=1
    if calls==1:raise FileNotFoundError(errno.ENOENT,'missing',str(x))
   return original(x,*a,**kw)
  with patch.object(Path,'lstat',fake):(rows,total,allocated),j=self.run_inventory()
  self.assertEqual(total,3);self.assertEqual(len(rows),1);self.assertEqual(j['scanCount'],2);self.assertEqual(j['retryCount'],1)
 def test_known_readlink_enoent_restarts_not_skips(self):
  self.link();original=os.readlink;calls=0
  def fake(x,*a,**kw):
   nonlocal calls
   if Path(x)==self.path:
    calls+=1
    if calls==1:raise FileNotFoundError(errno.ENOENT,'missing',str(x))
   return original(x,*a,**kw)
  with patch.object(c.os,'readlink',fake):(rows,total,allocated),j=self.run_inventory()
  self.assertEqual(len(rows),1);self.assertEqual(j['scanCount'],2);self.assertEqual(total,self.path.lstat().st_size)
 def test_persistent_known_disappearance_fails_four_scans(self):
  self.link();original=Path.lstat;calls=0;j=c.observations()
  def fake(x,*a,**kw):
   nonlocal calls
   if x==self.path:calls+=1;raise FileNotFoundError(errno.ENOENT,'missing',str(x))
   return original(x,*a,**kw)
  with patch.object(Path,'lstat',fake),self.assertRaisesRegex(b.InventoryRefusal,'four complete scans'):c.inventory(self.root,8192,j)
  self.assertEqual(calls,4);self.assertEqual(j['scanCount'],4);self.assertEqual(j['completedScanCount'],0)
 def test_partial_cap_failure_cannot_trigger_retry(self):
  self.link();original=os.readlink
  def fake(x,*a,**kw):raise AssertionError('Quota must fail before readlink')
  with patch.object(c.os,'readlink',fake),self.assertRaisesRegex(ValueError,'aggregate'):self.run_inventory(1)
 def test_file_count_cap_includes_links(self):
  names=['x'+str(i) for i in range(8193)]
  fake=types.SimpleNamespace(st_mode=stat.S_IFREG|0o600,st_nlink=1,st_size=0,st_blocks=0,st_dev=1,st_ino=2,st_mtime_ns=3,st_ctime_ns=4)
  with patch.object(c,'members',return_value=names),patch.object(c,'read_stat',return_value=fake),self.assertRaisesRegex(ValueError,'file cap'):self.run_inventory()
 def test_samples_are_bounded_but_all_links_count(self):
  for i in range(20):
   path=self.path.parent/('Module'+str(i)+'-HASH.pcm.lock');path.symlink_to(str(path)+'-0123abcd')
  (rows,total,allocated),j=self.run_inventory(16384)
  self.assertEqual(len(rows),20);self.assertEqual(len(j['lockSamples']),16);self.assertTrue(j['lockSamplesTruncated'])
 def test_stable_final_regular_output_can_be_fully_hashed(self):
  path=Path(str(self.path)+'-0123abcd');path.write_bytes(b'owner');self.link();self.path.unlink()
  rows,total,allocated=b.inventory(self.root,8192)
  self.assertEqual({n:p.sha(self.root/n) for n in rows},{str(path.relative_to(self.root)):p.sha(path)})
 def test_unique_lock_owner_directory_cannot_be_hidden_by_link(self):
  target=Path(str(self.path)+'-0123abcd');target.mkdir();self.link()
  with self.assertRaisesRegex(b.InventoryRefusal,'cannot be directories'):self.run_inventory()

class Route(unittest.IsolatedAsyncioTestCase):
 def setUp(self):
  tmp=tempfile.TemporaryDirectory(dir=p.HERE);self.addCleanup(tmp.cleanup);self.root=Path(tmp.name)
 async def test_only_exact_swift_compile_watch_admits_lock_route(self):
  child=FakeChild();calls=[]
  async def create(*a,**kw):return child
  def live(*a):calls.append(a);raise ValueError('observed live')
  with patch.object(b.asyncio,'create_subprocess_exec',create),patch.object(b.os,'getpgid',return_value=child.pid),patch.object(b.os,'killpg',side_effect=kill_fake(child)),patch.object(c,'inventory',live):
   with self.assertRaisesRegex(ValueError,'observed live'):await b.command([str(p.SWIFT),'fake'],self.root,lambda:None,time.monotonic()+1,8192,label='compile-swift')
  self.assertEqual(len(calls),1)
 async def test_clang_and_other_swift_labels_keep_strict_inventory(self):
  for tool,label in ((p.CLANG,'compile-swift'),(p.SWIFT,'other')):
   child=FakeChild();calls=0
   async def create(*a,**kw):return child
   def strict(*a):
    nonlocal calls
    calls+=1
    if calls>1:raise ValueError('strict refusal')
    return {},0,0
   with patch.object(b.asyncio,'create_subprocess_exec',create),patch.object(b.os,'getpgid',return_value=child.pid),patch.object(b.os,'killpg',side_effect=kill_fake(child)),patch.object(b,'inventory',strict),patch.object(c,'inventory',side_effect=AssertionError('No exception for this route')):
    with self.assertRaisesRegex(ValueError,'strict refusal'):await b.command([str(tool),'fake'],self.root,lambda:None,time.monotonic()+1,8192,label=label)
 async def test_initial_symlink_refusal_precedes_any_spawn(self):
  path=self.root/'ModuleCache/HASH/MOD-HASH.pcm.lock';path.parent.mkdir(parents=True);path.symlink_to(str(path)+'-0123abcd')
  with patch.object(b.asyncio,'create_subprocess_exec',side_effect=AssertionError('Must refuse before spawn')),self.assertRaises(b.InventoryRefusal):
   await b.command([str(p.SWIFT),'fake'],self.root,lambda:None,time.monotonic()+1,8192,label='compile-swift')
 async def test_lingering_lock_after_reaped_swift_is_still_refused(self):
  child=FakeChild();journal=[];original=c.inventory
  async def create(*a,**kw):return child
  def live(root,limit,observations):
   path=self.root/'ModuleCache/HASH/MOD-HASH.pcm.lock';path.parent.mkdir(parents=True);path.symlink_to(str(path)+'-0123abcd')
   row=original(root,limit,observations);child.returncode=0;child.event.set();return row
  with patch.object(b.asyncio,'create_subprocess_exec',create),patch.object(b.os,'getpgid',return_value=child.pid),patch.object(b.os,'killpg',side_effect=kill_fake(child)),patch.object(c,'inventory',live):
   with self.assertRaises(b.InventoryRefusal):await b.command([str(p.SWIFT),'fake'],self.root,lambda:None,time.monotonic()+1,8192,label='compile-swift',journal=journal)
  self.assertTrue(journal[0]['childReaped'] and journal[0]['groupAbsenceObserved'])
  self.assertEqual(len(journal[0]['liveCompilerLockMetadata']['lockSamples']),1)

if __name__=='__main__':unittest.main()
