"""Tiny synthetic PNG framing, local temp paths and fake owned host children."""
from pathlib import Path
import asyncio,copy,hashlib,os,plistlib,struct,tempfile,time,types,unittest
from unittest.mock import patch
import protocol as p,bounded_child as b,capture,local_build

def wanted():
 value={'schema':1,'bundle':p.BUNDLE,'generation':'12345678-1234-4234-8234-123456789abc','ownedMainPID':123,
        'observedBundlePath':'/private/var/containers/Bundle/Application/01234567-89AB-CDEF-0123-456789ABCDEF/Madeira.app','manifestSha256':'1'*64}
 return {**value,'contextSha256':p.sha_context(value)}
def fixture():
 w=wanted();png=b'\x89PNG\r\n\x1a\n'+struct.pack('>I',13)+b'IHDR'+struct.pack('>II',2,2)
 row={'schema':1,'status':'own_application_element_still_requires_visual_review',**{k:w[k] for k in ('bundle','generation','ownedMainPID','contextSha256')},
      'stateBefore':4,'stateAfter':4,'pngBytes':len(png),'pngSha256':hashlib.sha256(png).hexdigest(),'pixelWidth':2,'pixelHeight':2,
      'processIdentityCheckedInsideXCTest':False,'gpuQualified':False,'courseObserved':False,'gamePlayable':False}
 manifest=[{'testIdentifier':p.TEST+'()','attachments':[{'exportedFileName':name,'suggestedHumanReadableName':label,'deviceId':p.DEVICE,'isAssociatedWithFailure':False,'repetitionNumber':1} for name,label in [('image.png','own-application-still.png'),('meta.json','own-application-still.json')]]}]
 return w,{'result':'Passed','totalTestCount':1,'passedTests':1,'failedTests':0,'skippedTests':0,'expectedFailures':0},manifest,{'image.png':png,'meta.json':p.canonical(row)}
class Protocol(unittest.TestCase):
 def test_no_host_or_target_application_in_new_project(self):
  source=(p.HERE/'OwnWindowStill.xcodeproj/project.pbxproj').read_text()
  self.assertEqual(source.count('isa = PBXNativeTarget;'),1);self.assertNotIn('TEST_TARGET_NAME',source);self.assertNotIn('com.apple.product-type.application',source)
 def test_exact_still_only_swift(self):
  s=(p.HERE/'OwnWindowStillTests/OwnWindowStillTests.swift').read_text()
  for token in ('app.activate(', 'app.launch(', 'app.terminate(', 'XCUIScreen.', '.tap(', 'waitForState('):self.assertNotIn(token,s)
  self.assertEqual(s.count('app.screenshot()'),1);self.assertEqual(s.count('app.state'),2);self.assertEqual(s.count('add('),2)
 def test_destination_artifacts_never_selects_local_target_app(self):
  t=p.xctestrun(wanted())[p.TEST_MODULE];self.assertTrue(t['UseDestinationArtifacts']);self.assertEqual(t['UITargetAppBundleIdentifier'],p.BUNDLE)
  for name in ('TestBundlePath','TestHostPath','UITargetAppPath'):self.assertNotIn(name,t)
  self.assertEqual(t['OnlyTestIdentifiers'],[p.TEST]);self.assertEqual(t['SystemAttachmentLifetime'],'keepNever')
 def test_plist_roundtrip_context(self):self.assertEqual(plistlib.loads(plistlib.dumps(p.xctestrun(wanted()))),p.xctestrun(wanted()))
 def test_foreign_context_refused(self):
  w=wanted();w['bundle']='foreign'
  with self.assertRaises(ValueError):p.xctestrun(w)
 def test_wrong_pid_type_refused(self):
  w=wanted();w['ownedMainPID']=True;w['contextSha256']=p.sha_context(w)
  with self.assertRaises(ValueError):p.context(w)
 def test_changed_generation_digest_refused(self):
  w=wanted();w['generation']='11111111-1111-4111-8111-111111111111'
  with self.assertRaises(ValueError):p.context(w)
 def test_build_local_generic_no_device_no_network_update(self):
  args=p.build_command(p.HERE/'local-build-synthetic');self.assertIn('build-for-testing',args);self.assertIn('generic/platform=iOS',args)
  self.assertNotIn('-allowProvisioningUpdates',args);self.assertIn('CODE_SIGNING_ALLOWED=NO',args);self.assertNotIn('test',args)
  self.assertIn('-disableAutomaticPackageResolution',args);self.assertIn('-skipPackageUpdates',args)
 def test_capture_single_device_no_test_retry(self):
  args=p.capture_commands(p.HERE/'synthetic',wanted())[0];self.assertIn('test-without-building',args);self.assertIn('platform=iOS,id='+p.DEVICE,args)
  self.assertNotIn('-retry-tests-on-failure',args);self.assertEqual(args[args.index('-test-iterations')+1],'1')
 def test_exact_two_successful_attachment_parsing(self):
  w,s,m,f=fixture();r,png=p.accepted_exports(s,m,f,w);self.assertFalse(r['gpuQualified']);self.assertEqual(png,f['image.png'])
 def test_extra_pass_or_skip_refused(self):
  for key in ('totalTestCount','skippedTests','failedTests'):
   w,s,m,f=fixture();s[key]+=1
   with self.assertRaises(ValueError):p.accepted_exports(s,m,f,w)
 def test_unknown_attachment_refused(self):
  w,s,m,f=fixture();m[0]['attachments'].append(dict(m[0]['attachments'][0]))
  with self.assertRaises(ValueError):p.accepted_exports(s,m,f,w)
 def test_missing_attachment_refused(self):
  w,s,m,f=fixture();f.pop('image.png')
  with self.assertRaises(ValueError):p.accepted_exports(s,m,f,w)
 def test_export_path_escape_refused(self):
  w,s,m,f=fixture();m[0]['attachments'][0]['exportedFileName']='../foreign'
  with self.assertRaises(ValueError):p.accepted_exports(s,m,f,w)
 def test_foreign_device_refused(self):
  w,s,m,f=fixture();m[0]['attachments'][0]['deviceId']='foreign'
  with self.assertRaises(ValueError):p.accepted_exports(s,m,f,w)
 def test_bool_repetition_refused(self):
  w,s,m,f=fixture();m[0]['attachments'][0]['repetitionNumber']=True
  with self.assertRaises(ValueError):p.accepted_exports(s,m,f,w)
 def test_attachment_digest_and_foreground_refused(self):
  for key,value in [('pngSha256','0'*64),('stateAfter',3),('gpuQualified',True),('ownedMainPID',124)]:
   w,s,m,f=fixture();row=p.unique_json(f['meta.json']);row[key]=value;f['meta.json']=p.canonical(row)
   with self.assertRaises(ValueError):p.accepted_exports(s,m,f,w)
 def test_duplicate_json_refused(self):
  with self.assertRaises(ValueError):p.unique_json(b'{"x":1,"x":2}')
 def test_signed_runner_lifecycle_is_material_missing_input(self):
  with self.assertRaisesRegex(ValueError,'signed installed'):capture.Capture(None,lambda:None,None)
class Output(unittest.TestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory(dir=p.HERE);self.addCleanup(t.cleanup);self.root=Path(t.name)
 def test_ordinary_output_cap(self):
  (self.root/'x').write_bytes(b'123');self.assertEqual(b.inventory(self.root,8192)[1],3)
  with self.assertRaises(ValueError):b.inventory(self.root,2)
 def test_symlink_never_followed(self):
  (self.root/'link').symlink_to(p.HERE/'protocol.py')
  with self.assertRaises(ValueError):b.inventory(self.root,8192)
 def test_link_parent_refused_before_foreign_mkdir(self):
  (self.root/'link').symlink_to(p.HERE,target_is_directory=True)
  with self.assertRaises(ValueError):b.unlinked_parent(self.root/'link'/'foreign-new-dir')
  self.assertFalse((p.HERE/'foreign-new-dir').exists())
 def test_unknown_walk_error_fatal(self):
  def bad(*a,**kw):kw['onerror'](PermissionError());return []
  with patch.object(b.os,'walk',bad),self.assertRaises(PermissionError):b.inventory(self.root,8192)
 def test_initial_whole_budget_preserves_native_reserve(self):self.assertGreater(p.LIVE_BUILD+p.MAX_BUILD,int(6.6*1024**3));self.assertEqual(p.MAX_BUILD,200<<20)
 def test_read_access_keeps_current_object_identity(self):
  path=self.root/'source';path.write_bytes(b'actual source');before={str(path):local_build.identity(path)}
  self.assertEqual(path.read_bytes(),b'actual source');local_build.check_identities(before)
 def test_access_stamp_only_does_not_fake_source_drift(self):
  fields=dict(st_dev=1,st_ino=2,st_mode=0o100644,st_nlink=1,st_size=3,st_mtime_ns=4,st_ctime_ns=5,st_atime_ns=6)
  with patch.object(local_build.Path,'stat',return_value=types.SimpleNamespace(**fields)):before={'/synthetic':local_build.identity('/synthetic')}
  fields['st_atime_ns']=99
  with patch.object(local_build.Path,'stat',return_value=types.SimpleNamespace(**fields)):local_build.check_identities(before)
 def test_actual_mtime_change_names_the_exact_input(self):
  path=self.root/'source';path.write_bytes(b'abc');before={str(path):local_build.identity(path)};s=path.stat()
  os.utime(path,ns=(s.st_atime_ns,s.st_mtime_ns+1_000_000))
  with self.assertRaisesRegex(ValueError,str(path)+'.*mtime_ns'):local_build.check_identities(before)
 def test_actual_ctime_change_cannot_be_hidden_by_restored_mode(self):
  path=self.root/'source';path.write_bytes(b'abc');before={str(path):local_build.identity(path)};mode=path.stat().st_mode
  path.chmod(mode^0o100);path.chmod(mode)
  self.assertEqual(path.stat().st_mode,mode)
  with self.assertRaisesRegex(ValueError,str(path)+'.*ctime_ns'):local_build.check_identities(before)
 def test_actual_equal_bytes_replacement_still_changes_inode(self):
  path=self.root/'source';path.write_bytes(b'abc');before={str(path):local_build.identity(path)}
  other=self.root/'replacement';other.write_bytes(b'abc');other.replace(path)
  with self.assertRaisesRegex(ValueError,str(path)+'.*ino'):local_build.check_identities(before)
 def test_full_byte_replay_still_refuses_changed_source(self):
  path=self.root/'source';path.write_bytes(b'abc');review=self.root/'source-review-freeze.json'
  review.write_bytes(p.canonical({'inputs':{str(path):p.sha(path)}}));digest=p.sha(review)
  with patch.object(p,'HERE',self.root):local_build.review(digest)
  path.write_bytes(b'abd')
  with patch.object(p,'HERE',self.root),self.assertRaisesRegex(ValueError,'source/API/tool changed'):local_build.review(digest)
class FakeChild:
 def __init__(self):self.pid=987654;self.returncode=None;self.event=asyncio.Event();self.stdout=self
 async def read(self,n):await self.event.wait();return b''
 async def wait(self):await self.event.wait();return self.returncode
 def kill(self):self.returncode=-9;self.event.set()
def kill_fake(child):
 def call(group,sig):
  if sig==0:
   if child.event.is_set():raise ProcessLookupError()
  elif child.returncode is None:child.kill()
  else:child.event.set()
 return call
class Children(unittest.IsolatedAsyncioTestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory(dir=p.HERE);self.addCleanup(t.cleanup);self.root=Path(t.name)
 async def test_cancel_reaps_child_and_drain(self):
  child=FakeChild();start=asyncio.Event()
  async def create(*a,**kw):self.assertTrue(kw['start_new_session']);start.set();return child
  with patch.object(b.asyncio,'create_subprocess_exec',create),patch.object(b.os,'getpgid',return_value=child.pid),patch.object(b.os,'killpg',side_effect=kill_fake(child)):
   task=asyncio.create_task(b.command([str(p.XCODE),'synthetic'],self.root,lambda:None,time.monotonic()+1,8192));await start.wait();task.cancel()
   with self.assertRaises(asyncio.CancelledError):await task
   self.assertIsNotNone(child.returncode);self.assertTrue(child.event.is_set())
 async def test_deadline_reaps_child(self):
  child=FakeChild()
  async def create(*a,**kw):return child
  with patch.object(b.asyncio,'create_subprocess_exec',create),patch.object(b.os,'getpgid',return_value=child.pid),patch.object(b.os,'killpg',side_effect=kill_fake(child)):
   with self.assertRaisesRegex(ValueError,'deadline'):await b.command([str(p.XCODE),'synthetic'],self.root,lambda:None,0,8192)
  self.assertIsNotNone(child.returncode)
 async def test_guard_failure_before_child(self):
  with patch.object(b.asyncio,'create_subprocess_exec',side_effect=AssertionError('No child')):
   with self.assertRaisesRegex(ValueError,'lost'):await b.command([str(p.XCODE),'synthetic'],self.root,lambda:(_ for _ in ()).throw(ValueError('lost')),0,8192)
 async def test_no_generic_executable(self):
  with self.assertRaises(ValueError):await b.command(['/foreign/tool'],self.root,lambda:None,0,8192)
 async def test_exited_leader_does_not_orphan_stdout_descendant(self):
  child=FakeChild();child.returncode=0;calls=[]
  async def returned():return 0
  child.wait=returned
  async def create(*a,**kw):return child
  def group(pid):
   calls.append(pid)
   if len(calls)>1:raise ProcessLookupError()
   return pid
  with patch.object(b.asyncio,'create_subprocess_exec',create),patch.object(b.os,'getpgid',side_effect=group),patch.object(b.os,'killpg',side_effect=kill_fake(child)) as killing:
   row=await b.command([str(p.XCODE),'synthetic'],self.root,lambda:None,time.monotonic()+1,8192)
  self.assertEqual(calls,[child.pid]);killing.assert_any_call(child.pid,b.signal.SIGKILL)
  self.assertTrue(child.event.is_set());self.assertTrue(row['ownedHostGroupAbsentAfterCleanup']);self.assertEqual(row['exitCode'],0)
 async def test_unreaped_leader_cannot_skip_other_task_drains(self):
  child=FakeChild();child.returncode=0;count=0;drained=[]
  async def returned():
   nonlocal count
   count+=1
   if count>1:raise TimeoutError('Synthetic unreaped leader')
   return 0
  async def read(n):
   await child.event.wait();drained.append(True);return b''
  child.wait=returned;child.read=read
  async def create(*a,**kw):return child
  with patch.object(b.asyncio,'create_subprocess_exec',create),patch.object(b.os,'getpgid',return_value=child.pid),patch.object(b.os,'killpg',side_effect=kill_fake(child)):
   with self.assertRaisesRegex(ValueError,'child reap'):await b.command([str(p.XCODE),'synthetic'],self.root,lambda:None,time.monotonic()+1,8192)
  self.assertEqual(count,2);self.assertEqual(drained,[True])
  self.assertFalse([t for t in asyncio.all_tasks() if t is not asyncio.current_task() and not t.done()])
 async def test_surviving_owned_group_is_not_false_join_success(self):
  child=FakeChild();child.returncode=0;ticks=iter([0,0,0,4,4,4])
  async def returned():return 0
  child.wait=returned
  async def create(*a,**kw):return child
  def signal(pid,sig):
   if sig!=0:child.event.set()
  with patch.object(b.asyncio,'create_subprocess_exec',create),patch.object(b.os,'getpgid',return_value=child.pid),patch.object(b.os,'killpg',side_effect=signal):
   with self.assertRaisesRegex(ValueError,'group absence'):await b.command([str(p.XCODE),'synthetic'],self.root,lambda:None,100,8192,clock=lambda:next(ticks))
if __name__=='__main__':unittest.main()
