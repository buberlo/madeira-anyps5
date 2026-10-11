"""Exact observed Swift cache races; tiny temporary fixtures, no compiler calls."""
from pathlib import Path
import asyncio,errno,json,os,tempfile,time,unittest
from unittest.mock import patch
import compiler_locks as c,bounded_child as b,protocol as p,direct_build as d
from test_runner import FakeChild,kill_fake

class SwiftCache(unittest.TestCase):
 def setUp(self):
  temporary=tempfile.TemporaryDirectory(dir=p.HERE);self.addCleanup(temporary.cleanup)
  self.root=Path(temporary.name);(self.root/'ModuleCache').mkdir()
  self.temp=self.root/'ModuleCache/Foundation-3LG1SXKXY5YLE-b9474bef.swiftmodule.tmp'
  self.lock=self.root/'ModuleCache/XCUIAutomation-1XFP5VQKHE7F3.swiftmodule.lock'
 def test_exact_new_lock_counts_metadata_without_following_target(self):
  self.lock.symlink_to(str(self.lock)+'-0123abcd');s=self.lock.lstat();original=Path.stat
  def no_target(x,*a,**kw):
   if str(x).startswith(str(self.lock)) and kw.get('follow_symlinks')is not False:
    raise AssertionError('Do not follow Swift lock target')
   return original(x,*a,**kw)
  journal=c.observations()
  with patch.object(Path,'stat',no_target),patch.object(Path,'open',side_effect=AssertionError('No lock bytes')):
   rows,total,allocated=c.inventory(self.root,8192,journal)
  self.assertEqual(len(rows),1);self.assertEqual(total,s.st_size);self.assertEqual(allocated,s.st_blocks*512)
  self.assertFalse(journal['lockSamples'][0]['targetFollowedOrHashed'])
  with self.assertRaises(ValueError):c.inventory(self.root,s.st_size-1,c.observations())
 def test_actual_atomic_rename_discards_partial_counts_then_hashes_complete_final(self):
  counted=self.root/'a-counted';counted.write_bytes(b'12345');self.temp.write_bytes(b'123')
  final=self.root/'ModuleCache/Foundation-3LG1SXKXY5YLE.swiftmodule';original=Path.lstat;renames=[]
  def moved(x,*a,**kw):
   if x==self.temp and not renames:
    os.replace(self.temp,final);renames.append(str(x))
   return original(x,*a,**kw)
  journal=c.observations()
  with patch.object(Path,'lstat',moved):rows,total,_=c.inventory(self.root,8192,journal)
  self.assertEqual(journal['retryCount'],1);self.assertEqual(journal['scanCount'],2)
  self.assertEqual(total,8);self.assertEqual(set(rows),{'a-counted',str(final.relative_to(self.root))})
  strict,total,_=b.inventory(self.root,8192);self.assertEqual(total,8)
  self.assertEqual(p.sha(final),'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3')
 def test_other_temp_spelling_root_and_stable_module_disappearance_fail_immediately(self):
  for relative in ('ModuleCache/Foundation-HASH-0123ABCD.swiftmodule.tmp',
   'ModuleCache/Foundation-HASH-0123abc.swiftmodule.tmp','ModuleCache/Foundation-HASH.swiftmodule',
   'ModuleCache/HASH/Foundation-HASH-0123abcd.swiftmodule.tmp',
   'SDKModuleCache/Foundation-HASH-0123abcd.swiftmodule.tmp','ModuleCache/unknown.tmp'):
   path=self.root/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'x')
   original=Path.lstat;calls=[]
   def missing(x,*a,**kw):
    if x==path:calls.append(1);raise FileNotFoundError(errno.ENOENT,'missing',str(x))
    return original(x,*a,**kw)
   with patch.object(Path,'lstat',missing),self.assertRaises(b.InventoryRefusal):
    c.inventory(self.root,8192,c.observations())
   self.assertEqual(len(calls),1);path.unlink()
 def test_persistent_exact_temp_disappearance_fails_after_four_whole_scans(self):
  self.temp.write_bytes(b'x');original=Path.lstat;calls=[];journal=c.observations()
  def missing(x,*a,**kw):
   if x==self.temp:calls.append(1);raise FileNotFoundError(errno.ENOENT,'missing',str(x))
   return original(x,*a,**kw)
  with patch.object(Path,'lstat',missing),self.assertRaisesRegex(b.InventoryRefusal,'four complete scans'):
   c.inventory(self.root,8192,journal)
  self.assertEqual(len(calls),4);self.assertEqual(journal['completedScanCount'],0)
 def test_partial_quota_refuses_before_any_known_temp_rescan(self):
  (self.root/'a-counted').write_bytes(b'x'*32);self.temp.write_bytes(b'x');original=Path.lstat;calls=[]
  def missing(x,*a,**kw):
   if x==self.temp:calls.append(1);raise FileNotFoundError(errno.ENOENT,'missing',str(x))
   return original(x,*a,**kw)
  with patch.object(Path,'lstat',missing),self.assertRaisesRegex(ValueError,'aggregate'):
   c.inventory(self.root,16,c.observations())
  self.assertEqual(calls,[])
 def test_temp_directory_or_symlink_and_foreign_lock_target_never_accepted(self):
  self.temp.mkdir()
  with self.assertRaises(b.InventoryRefusal):c.inventory(self.root,8192,c.observations())
  self.temp.rmdir();self.temp.symlink_to('/foreign')
  with self.assertRaises(b.InventoryRefusal):c.inventory(self.root,8192,c.observations())
  self.temp.unlink();self.lock.symlink_to('/foreign/lock-0123abcd')
  with self.assertRaises(b.InventoryRefusal):c.inventory(self.root,8192,c.observations())
 def test_all_production_files_except_live_helper_and_caps_are_byte_identical(self):
  old=p.HERE.with_name('native58-own-window-direct-swift-compiler-lock-proposal')
  for name in ('bounded_child.py','local_build.py','protocol.py','capture.py',
   'OwnWindowStillTests/OwnWindowStillTests.swift','OwnWindowStill.xcodeproj/project.pbxproj',
   'OwnWindowStill.xcodeproj/xcshareddata/xcschemes/OwnWindowStill.xcscheme'):
   self.assertEqual((p.HERE/name).read_bytes(),(old/name).read_bytes())
  self.assertEqual(p.MAX_BUILD,200<<20);self.assertEqual(p.LIVE_BUILD,7086696039)
  self.assertEqual(c.SCANS,4);self.assertEqual(c.SAMPLES,16)
  self.assertEqual(json.loads((old/'local-build-compiler-lock/receipt.json').read_bytes())['status'],
   'failed_local_direct_swift_own_window_runner_build_not_device_ready')

class PostChild(unittest.IsolatedAsyncioTestCase):
 async def test_new_swift_lock_is_refused_after_successful_child_join(self):
  temporary=tempfile.TemporaryDirectory(dir=p.HERE);self.addCleanup(temporary.cleanup)
  root=Path(temporary.name);child=FakeChild();journal=[];original=c.inventory
  async def create(*a,**kw):return child
  def live(r,limit,observations):
   path=root/'ModuleCache/XCUIAutomation-1XFP5VQKHE7F3.swiftmodule.lock'
   path.parent.mkdir(parents=True);path.symlink_to(str(path)+'-0123abcd')
   value=original(r,limit,observations);child.returncode=0;child.event.set();return value
  with patch.object(b.asyncio,'create_subprocess_exec',create),patch.object(b.os,'getpgid',return_value=child.pid),patch.object(b.os,'killpg',side_effect=kill_fake(child)),patch.object(c,'inventory',live):
   with self.assertRaises(b.InventoryRefusal):
    await b.command([str(p.SWIFT),'fake'],root,lambda:None,time.monotonic()+1,8192,label='compile-swift',journal=journal)
  self.assertTrue(journal[0]['childReaped'] and journal[0]['groupAbsenceObserved'])
  self.assertEqual(len(journal[0]['liveCompilerLockMetadata']['lockSamples']),1)

if __name__=='__main__':unittest.main()
