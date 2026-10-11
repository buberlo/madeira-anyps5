"""Tiny fake children/output refusals; no compiler, SDK copy or device calls."""
from pathlib import Path
import asyncio,json,os,stat,tempfile,time,unittest
from unittest.mock import patch
import protocol as p,bounded_child as b,direct_build as d
from test_runner import FakeChild,kill_fake

class Details(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=p.HERE);self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
 def test_hardlink_reports_exact_path_and_inode_without_accepting(self):
  source=self.root/'a';source.write_bytes(b'public');os.link(source,self.root/'b')
  with self.assertRaises(b.InventoryRefusal) as got:b.inventory(self.root,8192)
  x=got.exception.details;self.assertIn(x['path'],[str(source),str(self.root/'b')]);self.assertEqual(x['nlink'],2)
  self.assertEqual(x['type'],'regular');self.assertEqual(x['ino'],source.stat().st_ino)
 def test_symlink_reports_exact_link_type_without_following(self):
  (self.root/'link').symlink_to('/outside/nonexistent')
  with self.assertRaises(b.InventoryRefusal) as got:b.inventory(self.root,8192)
  self.assertEqual(got.exception.details['type'],'symlink');self.assertEqual(got.exception.details['path'],str(self.root/'link'))
 def test_fifo_reports_nonregular_type(self):
  os.mkfifo(self.root/'fifo')
  with self.assertRaises(b.InventoryRefusal) as got:b.inventory(self.root,8192)
  self.assertEqual(got.exception.details['type'],'fifo')
 def test_terminal_receipt_does_not_rerun_refused_inventory(self):
  value={'status':'failed','outputInventoryComplete':False,'logicalBytes':None,'allocatedBytes':None}
  with patch.object(b,'inventory',side_effect=AssertionError('Must not inventory failed tree')):
   path=d.terminal_receipt(self.root,value)
  self.assertEqual(json.loads(path.read_bytes()),value);self.assertEqual(path.stat().st_nlink,1)
 def test_receipt_member_has_fixed_small_cap(self):
  value={'outputInventoryComplete':False,'text':'x'*(d.RECEIPT_CAP+1)}
  with self.assertRaisesRegex(ValueError,'receipt'):d.terminal_receipt(self.root,value)
  self.assertFalse((self.root/'receipt.json').exists())
 def test_unknown_existing_receipt_never_overwritten(self):
  path=self.root/'receipt.json';path.write_bytes(b'original')
  with self.assertRaises(FileExistsError):d.terminal_receipt(self.root,{'outputInventoryComplete':False})
  self.assertEqual(path.read_bytes(),b'original')
 def test_total200mib_preserved_with_reserved_receipt(self):
  self.assertEqual(d.output_limit()+d.RECEIPT_CAP,p.MAX_BUILD)
  value={'outputInventoryComplete':True,'logicalBytes':p.MAX_BUILD,'allocatedBytes':p.MAX_BUILD}
  with self.assertRaisesRegex(ValueError,'200 MiB'):d.terminal_receipt(self.root,value)

class Cleanup(unittest.IsolatedAsyncioTestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=p.HERE);self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
 async def test_live_inventory_refusal_retains_actual_fake_cleanup_observations(self):
  child=FakeChild();journal=[];calls=0
  async def create(*a,**kw):return child
  def inventory(*a):
   nonlocal calls
   calls+=1
   if calls>1:raise b.InventoryRefusal('refused',{'path':str(self.root/'cache'),'nlink':2,'mode':stat.S_IFREG,'type':'regular'})
   return {},0,0
  with patch.object(b.asyncio,'create_subprocess_exec',create),patch.object(b.os,'getpgid',return_value=child.pid),patch.object(b.os,'killpg',side_effect=kill_fake(child)),patch.object(b,'inventory',inventory):
   with self.assertRaises(b.InventoryRefusal):await b.command([str(p.SWIFT),'fake'],self.root,lambda:None,time.monotonic()+1,8192,journal=journal)
  self.assertEqual(len(journal),1);row=journal[0]
  self.assertTrue(row['childReaped'] and row['groupAbsenceObserved'] and row['stdoutDrainJoined'])
  self.assertEqual(row['inventoryFailureDetails']['nlink'],2);self.assertEqual(row['cleanupErrors'],[])
 async def test_reap_failure_is_recorded_and_other_tasks_drained(self):
  child=FakeChild();child.returncode=0;count=0;journal=[]
  async def returned():
   nonlocal count
   count+=1
   if count>1:raise TimeoutError('unreaped')
   return 0
  child.wait=returned
  async def create(*a,**kw):return child
  with patch.object(b.asyncio,'create_subprocess_exec',create),patch.object(b.os,'getpgid',return_value=child.pid),patch.object(b.os,'killpg',side_effect=kill_fake(child)):
   with self.assertRaisesRegex(ValueError,'child reap'):await b.command([str(p.SWIFT),'fake'],self.root,lambda:None,time.monotonic()+1,8192,journal=journal)
  self.assertFalse(journal[0]['childReaped']);self.assertTrue(journal[0]['stdoutDrainJoined']);self.assertTrue(journal[0]['cleanupErrors'])
  self.assertFalse([t for t in asyncio.all_tasks() if t is not asyncio.current_task() and not t.done()])
 async def test_build_writes_failure_receipt_on_persistent_final_inventory_refusal(self):
  fake=self.root/'source';fake.write_bytes(b'x');(self.root/'source-review-freeze.json').write_bytes(b'{}');output=self.root/'local-build-fake'
  failure=b.InventoryRefusal('refused',{'path':str(output/'cache'),'mode':stat.S_IFREG,'nlink':2,'type':'regular'})
  async def command(*a,**kw):
   kw['journal'].append({'spawned':True,'pid':123,'childReaped':True,'groupAbsenceObserved':True,'cleanupErrors':[]})
   raise failure
  with patch.object(p,'HERE',self.root),patch.object(d.held,'review',return_value={'inputs':{str(fake):p.sha(fake)},'runtimeProviders':{}}),patch.object(d,'runtime_map',return_value={}),patch.object(d.shutil,'disk_usage',return_value=type('Disk',(),{'free':1<<40})()),patch.object(b,'command',command),patch.object(b,'inventory',side_effect=failure):
   with self.assertRaisesRegex(ValueError,'Local direct build failed'):await d.build('0'*64,output)
  value=json.loads((output/'receipt.json').read_bytes())
  self.assertTrue(value['status'].startswith('failed_'));self.assertFalse(value['outputInventoryComplete'])
  self.assertEqual(value['outputs'],{});self.assertIsNone(value['logicalBytes'])
  self.assertEqual(value['inventoryFailureDetails']['nlink'],2);self.assertTrue(value['actualChildCleanupJournal'][0]['childReaped'])
  self.assertFalse(value['signed'] or value['deviceActions'] or value['actualCaptureReady'])

if __name__=='__main__':unittest.main()
