"""No compiler or device calls: exact command, parser and local assembly controls."""
from pathlib import Path
import asyncio,copy,json,plistlib,stat,struct,tempfile,time,unittest
from unittest.mock import patch
import protocol as p,direct_build as d,bounded_child as b

def binary(kind=8,cpu=0x100000c):
 command=struct.pack('<6I',0x32,24,2,0x110000,0x1b0000,0)
 return struct.pack('<8I',0xfeedfacf,cpu,0,kind,1,len(command),0,0)+command
class Commands(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(dir=p.HERE);self.addCleanup(self.t.cleanup);self.root=Path(self.t.name)
 def test_no_build_service_or_device_entrypoint(self):
  first,second=d.commands(self.root);self.assertEqual(first[0],str(p.SWIFT));self.assertEqual(second[0],str(p.CLANG))
  for args in (first,second):
   self.assertNotIn(str(p.XCODE),args);self.assertNotIn('xcrun',args);self.assertNotIn('codesign',args)
   self.assertNotIn('test-without-building',args);self.assertNotIn('-allowProvisioningUpdates',args)
 def test_original_swift_only_input(self):
  first,_=d.commands(self.root);self.assertEqual([a for a in first if a.endswith('.swift')],[str(p.HERE/'OwnWindowStillTests/OwnWindowStillTests.swift')])
 def test_exact_arm64_ios17_bundle(self):
  first,second=d.commands(self.root)
  for args in (first,second):self.assertEqual(args[args.index('-target')+1],'arm64-apple-ios17.0')
  self.assertIn('-bundle',second);self.assertNotIn('-dynamiclib',second)
 def test_all_module_caches_owned(self):
  first,_=d.commands(self.root)
  for option in ('-module-cache-path','-sdk-module-cache-path','-clang-scanner-module-cache-path'):
   self.assertTrue(Path(first[first.index(option)+1]).is_relative_to(self.root))
 def test_runner_reachable_framework_rpaths(self):
  _,args=d.commands(self.root);self.assertIn('@loader_path/../../Frameworks',args);self.assertIn('/usr/lib/swift',args)
  self.assertIn('XCTest',args);self.assertIn('-lXCTestSwiftSupport',args)
 def test_runner_plist_exact_sdk_template_replacements(self):
  template={'CFBundleIdentifier':'$(WRAPPEDPRODUCTBUNDLEIDENTIFIER)','CFBundleExecutable':'$(WRAPPEDPRODUCTNAME)','CFBundleName':'$(WRAPPEDPRODUCTNAME)'}
  x=plistlib.loads(d.runner_plist(plistlib.dumps(template)));self.assertEqual(x['CFBundleIdentifier'],p.RUNNER)
  self.assertEqual(x['CFBundleExecutable'],'OwnWindowStillTests-Runner');self.assertEqual(x['MinimumOSVersion'],'17.0')
 def test_unknown_runner_template_refused(self):
  with self.assertRaises(ValueError):d.runner_plist(plistlib.dumps({'CFBundleIdentifier':'foreign','CFBundleExecutable':'$(WRAPPEDPRODUCTNAME)'}))
 def test_unresolved_runner_template_refused(self):
  with self.assertRaises(ValueError):d.runner_plist(plistlib.dumps({'CFBundleIdentifier':'$(WRAPPEDPRODUCTBUNDLEIDENTIFIER)','CFBundleExecutable':'$(WRAPPEDPRODUCTNAME)','unknown':'$(UNBOUND)'}))
 def test_test_bundle_info_contract(self):
  x=plistlib.loads(d.test_plist());self.assertEqual(x['CFBundlePackageType'],'BNDL');self.assertEqual(x['CFBundleIdentifier'],'com.konradkern.anyps5ipad.ownstill.tests')
 def test_actual_arm64_ios17_bundle_header(self):
  x=d.macho(binary(),8);self.assertTrue(x['iOS17DeploymentObserved']);self.assertEqual(x['fileType'],8)
 def test_wrong_architecture_refused(self):
  with self.assertRaises(ValueError):d.macho(binary(cpu=0x1000007),8)
 def test_executable_not_test_bundle_refused(self):
  with self.assertRaises(ValueError):d.macho(binary(kind=2),8)
 def test_wrong_deployment_refused(self):
  raw=bytearray(binary());struct.pack_into('<I',raw,44,0x100000)
  with self.assertRaises(ValueError):d.macho(raw,8)
 def test_truncated_load_command_refused(self):
  with self.assertRaises(ValueError):d.macho(binary()[:-1],8)
 def test_malformed_command_size_refused(self):
  raw=bytearray(binary());struct.pack_into('<I',raw,36,0xfffffffc)
  with self.assertRaises(ValueError):d.macho(raw,8)
 def test_real_sdk_runtime_map_is_complete_current_template(self):
  rows=d.runtime_map();self.assertIn('OwnWindowStillTests-Runner',rows)
  for f in d.FRAMEWORKS:self.assertIn('Frameworks/'+f+'.framework/'+f,rows)
  self.assertLess(sum(Path(q).stat().st_size for q in rows.values()),20<<20)
 def test_exact_copied_sdk_and_original_source_refs(self):
  old=p.HERE.parent/'native58-own-window-xctest-identity-proposal'
  self.assertEqual((p.HERE/'OwnWindowStillTests/OwnWindowStillTests.swift').read_bytes(),(old/'OwnWindowStillTests/OwnWindowStillTests.swift').read_bytes())

class Assembly(unittest.IsolatedAsyncioTestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(dir=p.HERE);self.addCleanup(self.t.cleanup);self.root=Path(self.t.name)
 async def test_full_hash_required_before_runtime_copy(self):
  source=self.root/'source';source.write_bytes(b'current')
  with self.assertRaisesRegex(ValueError,'provider bytes'):
   await d.assemble(self.root,{'Frameworks/x':str(source)},{str(source):'0'*64},lambda:None,time.monotonic()+10)
  self.assertFalse((self.root/'Products').exists())
 async def test_changed_source_bytes_are_never_copied(self):
  source=self.root/'source';source.write_bytes(b'original');h=p.sha(source);source.write_bytes(b'changed')
  with self.assertRaises(ValueError):await d.assemble(self.root,{'Frameworks/x':str(source)},{str(source):h},lambda:None,time.monotonic()+10)
 async def test_deadline_refuses_before_destination_creation(self):
  with self.assertRaisesRegex(ValueError,'deadline'):await d.write(self.root/'new'/ 'x',b'x',self.root,lambda:None,0)
  self.assertFalse((self.root/'new').exists())
 async def test_prewrite_cap_preserves_budget(self):
  with patch.object(p,'MAX_BUILD',1):
   with self.assertRaisesRegex(ValueError,'cap'):await d.write(self.root/'x',b'xx',self.root,lambda:None,time.monotonic()+10)
  self.assertFalse((self.root/'x').exists())
 async def test_regular_exclusive_copy_and_full_bytes(self):
  target=self.root/'new'/'x';await d.write(target,b'exact bytes',self.root,lambda:None,time.monotonic()+10)
  self.assertEqual(target.read_bytes(),b'exact bytes');self.assertEqual(target.stat().st_nlink,1)
  with self.assertRaises(FileExistsError):await d.write(target,b'overwrite',self.root,lambda:None,time.monotonic()+10)

if __name__=='__main__':unittest.main()
