"""Narrow source/temporary provider controls; no compiler or device calls."""
from pathlib import Path
import copy,importlib.util,json,tempfile,unittest
from unittest.mock import patch
import protocol as p,direct_build as d

OLD=p.HERE.with_name('native58-own-window-direct-swift-modulecache-proposal')
spec=importlib.util.spec_from_file_location('overlay_source_review',p.HERE/'make-source-review.py')
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
APIS=('XCTUnwrap','XCTAssertNotNil','XCTAssertFalse','XCTAssertEqual','XCTAssertGreaterThan','XCTAssertLessThanOrEqual')

class Overlay(unittest.TestCase):
 def fixture(self,root):
  base=root/'usr/lib/XCTest.swiftmodule';base.mkdir(parents=True)
  interface=base/'arm64-apple-ios.swiftinterface'
  interface.write_text('// swift-module-flags: -target '+d.TARGET+' -module-name XCTest\n'+
                       '\n'.join('public func '+n+'()' for n in APIS))
  (base/'arm64-apple-ios.swiftdoc').write_bytes(b'tiny synthetic provider, never compiler input')
  providers={str(x):{'sha256':p.sha(x),'bytes':x.stat().st_size,'stat':review.identity(x)['stat']} for x in base.iterdir()}
  return {'inputs':{n:r['sha256'] for n,r in providers.items()},'xctestOverlayDelta':{
   'target':d.TARGET,'compileOnlyAddedArguments':['-I',str(base.parent)],'providers':providers}}
 def temporary(self):
  t=tempfile.TemporaryDirectory(dir=p.HERE);self.addCleanup(t.cleanup);return Path(t.name)
 def test_actual_arm64_overlay_supplies_assertions_and_exact_failure_is_retained(self):
  evidence=p.unique_json((p.HERE/'api-and-budget-evidence.json').read_bytes())
  rows=review.overlay_inputs(evidence)
  self.assertEqual(len(rows),2);self.assertTrue(all('/arm64-apple-ios.' in n for n in rows))
  self.assertEqual(p.sha(OLD/'local-build-modulecache/receipt.json'),'750586f0bb3b6cfcfcc5496bdaab29a431bbf9f225c1e10049be5413faa77adb')
  self.assertEqual(evidence['xctestOverlayDelta']['predecessorSourceReviewSha256'],p.sha(OLD/'source-review-freeze.json'))
  self.assertFalse(evidence['xctestOverlayDelta']['actualCompilerConsumedSdkDependenciesCaptured'])
  for dependency in (
   d.PLATFORM/'Library/Frameworks/XCTest.framework/Modules/module.modulemap',
   d.PLATFORM/'Library/Frameworks/XCUIAutomation.framework/Modules/module.modulemap',
   d.PLATFORM/'Library/Frameworks/XCUIAutomation.framework/Modules/XCUIAutomation.swiftmodule/arm64-apple-ios.swiftinterface',
   d.PLATFORM/'Library/Frameworks/XCUIAutomation.framework/Modules/XCUIAutomation.swiftmodule/arm64-apple-ios.swiftdoc',
   d.PLATFORM/'usr/lib/libXCTestSwiftSupport.dylib'):
   self.assertEqual(evidence['inputs'][str(dependency)],p.sha(dependency))
 def test_only_two_compile_arguments_changed_entire_other_production_body_exact(self):
  old=(OLD/'direct_build.py').read_text();new=(p.HERE/'direct_build.py').read_text()
  fragment=",'-I',str(PLATFORM/'usr/lib')"
  self.assertEqual(new.count(fragment),1);self.assertEqual(new.replace(fragment,''),old)
  root=p.HERE/'local-build-overlay-control';swift,link=d.commands(root)
  at=swift.index('-I');self.assertEqual(swift[at:at+2],['-I',str(d.PLATFORM/'usr/lib')])
  self.assertEqual(swift.count('-I'),1);self.assertNotIn('-I',link)
 def test_assertions_lifecycle_locks_and_caps_are_unchanged(self):
  for name in ('protocol.py','bounded_child.py','compiler_locks.py','local_build.py','capture.py',
               'OwnWindowStillTests/OwnWindowStillTests.swift','OwnWindowStill.xcodeproj/project.pbxproj',
               'OwnWindowStill.xcodeproj/xcshareddata/xcschemes/OwnWindowStill.xcscheme'):
   self.assertEqual((p.HERE/name).read_bytes(),(OLD/name).read_bytes())
  self.assertEqual(p.MAX_BUILD,200<<20);self.assertEqual(p.LIVE_BUILD,7086696039)
 def test_complete_small_production_validator_route_and_missing_or_foreign_row_refusal(self):
  root=self.temporary();evidence=self.fixture(root)
  with patch.object(d,'PLATFORM',root):
   self.assertEqual(review.overlay_inputs(evidence),evidence['inputs'])
   wrong=copy.deepcopy(evidence);wrong['xctestOverlayDelta']['providers'].pop(next(iter(wrong['inputs'])))
   with self.assertRaisesRegex(ValueError,'Only actual ARM64'):review.overlay_inputs(wrong)
   wrong=copy.deepcopy(evidence);n=next(iter(wrong['inputs']));wrong['inputs'].pop(n)
   with self.assertRaisesRegex(ValueError,'provider bytes'):review.overlay_inputs(wrong)
   wrong=copy.deepcopy(evidence);wrong['xctestOverlayDelta']['providers'][str(root/'foreign')]=next(iter(wrong['xctestOverlayDelta']['providers'].values()))
   with self.assertRaisesRegex(ValueError,'Only actual ARM64'):review.overlay_inputs(wrong)
 def test_saved_identity_or_byte_digest_drift_refuses(self):
  root=self.temporary();evidence=self.fixture(root)
  with patch.object(d,'PLATFORM',root):
   wrong=copy.deepcopy(evidence);next(iter(wrong['xctestOverlayDelta']['providers'].values()))['stat'][1]+=1
   with self.assertRaisesRegex(ValueError,'seven-field'):review.overlay_inputs(wrong)
   wrong=copy.deepcopy(evidence);n=next(iter(wrong['inputs']));wrong['inputs'][n]='0'*64
   with self.assertRaisesRegex(ValueError,'provider bytes'):review.overlay_inputs(wrong)
 def test_wrong_target_missing_api_or_link_refuses(self):
  root=self.temporary();evidence=self.fixture(root)
  with patch.object(d,'PLATFORM',root):
   wrong=copy.deepcopy(evidence);wrong['xctestOverlayDelta']['target']='arm64e-apple-ios17.0'
   with self.assertRaisesRegex(ValueError,'Exact ARM64'):review.overlay_inputs(wrong)
   path=root/'usr/lib/XCTest.swiftmodule/arm64-apple-ios.swiftinterface'
   raw=path.read_text();path.write_text(raw.replace('public func XCTUnwrap()',''))
   evidence['inputs'][str(path)]=p.sha(path);row=evidence['xctestOverlayDelta']['providers'][str(path)]
   row.update(sha256=p.sha(path),bytes=path.stat().st_size,stat=review.identity(path)['stat'])
   with self.assertRaisesRegex(ValueError,'assertion APIs'):review.overlay_inputs(evidence)
   doc=root/'usr/lib/XCTest.swiftmodule/arm64-apple-ios.swiftdoc';other=root/'retained-doc';doc.rename(other);doc.symlink_to(other)
   with self.assertRaisesRegex(ValueError,'Ordinary exact'):review.overlay_inputs(evidence)

if __name__=='__main__':unittest.main()
