"""Portable source preservation only; do not import local snapshot modules."""
import ast
import hashlib
import json
import unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
class Snapshot(unittest.TestCase):
 def test_exact_snapshot_bytes(self):
  manifest=json.loads((HERE/'source-manifest.json').read_text())
  for name,digest in manifest['files'].items():
   self.assertEqual(hashlib.sha256((HERE/name).read_bytes()).hexdigest(),digest,name)
 def test_sources_parse_without_importing(self):
  sources=list(HERE.rglob('*.snapshot'));self.assertEqual(len(sources),60)
  for source in sources:ast.parse(source.read_text(),filename=source.name)
 def test_pending_runtime_tuple(self):
  tree=ast.parse((HERE/'original50/composition.py.snapshot').read_text());values={}
  for node in tree.body:
   if isinstance(node,ast.Assign)and isinstance(node.value,ast.Constant):
    for target in node.targets:
     if isinstance(target,ast.Name):values[target.id]=node.value.value
  self.assertEqual(values['SEALED_INSTALL_SHA'],'PENDING');self.assertEqual(values['SEALED_RESULT_SHA'],'PENDING');self.assertIsNone(values['SEALED_INPUT_COUNT'])
 def test_original50_budget_and_no_sampler(self):
  tree=ast.parse((HERE/'original50/probe.py.snapshot').read_text());values={}
  for node in tree.body:
   if isinstance(node,ast.Assign):
    try:value=ast.literal_eval(node.value)
    except(ValueError,TypeError):continue
    for target in node.targets:
     if isinstance(target,ast.Name):values[target.id]=value
  self.assertEqual(values['EXECUTABLES']['continuing-only-diagnostic'][2],120)
  self.assertEqual((values['TOTAL'],values['SETUP'],values['CLEANUP'],values['MARGIN']),(330,120,90,60))
  self.assertNotIn('MADEIRA_THREAD_SAMPLER',values['BASE_ENV'])
 def test_privacy_and_no_runtime_data(self):
  forbidden=[b'/' + b'Users/',b'00008112' + b'-000924EE14D9A01E',b'pre-cleanup.' + b'owned-log']
  for path in HERE.rglob('*'):
   if path.is_file():
    self.assertNotIn(path.suffix,{'.zip','.bin','.prx','.exe','.mobileprovision','.p12','.owned-log'})
    for token in forbidden:self.assertNotIn(token,path.read_bytes(),str(path))
  self.assertEqual([p.name for p in HERE.rglob('*.json')],['source-manifest.json'])
 def test_no_runtime_acceptance_relabeling(self):
  manifest=json.loads((HERE/'source-manifest.json').read_text())
  self.assertTrue(manifest['actualNative60BuiltSigned'])
  for field in ['actualNative60Installed','actualOriginal50Accepted','actualFull803EightAccepted','deviceActions','privateProviderMapsIncluded','capturedLogIncluded']:
   self.assertFalse(manifest[field])
  self.assertEqual(manifest['updaterSourceControls'],19);self.assertEqual(manifest['original50SourceControls'],24)
 def test_observed_adoption_remains_pending_and_initial_only(self):
  tree=ast.parse((HERE/'observed59-updater60/reference.py.snapshot').read_text())
  values={n.targets[0].id:n.value.value for n in tree.body if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)and isinstance(n.value,ast.Constant)}
  self.assertEqual(values['READ_RECEIPT_SHA'],'PENDING')
  functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
  first=functions['inspect_reference'].body[0]
  self.assertIsInstance(first,ast.Assign);self.assertEqual(first.value.func.id,'observed_evidence')
  transition=ast.unparse(functions['transition'])
  self.assertIn('Only exact observed initial row/absence accepted:',transition)
  self.assertIn("'postInstallPolicyExceptionsAdded': False",transition)
 def test_retention_bounds_and_snapshot_scope(self):
  tree=ast.parse((HERE/'current59-retention/read_current.py.snapshot').read_text());values={}
  for node in tree.body:
   if isinstance(node,ast.Assign):
    try:v=ast.literal_eval(node.value)
    except(ValueError,TypeError):continue
    for target in node.targets:
     if isinstance(target,ast.Name):values[target.id]=v
  self.assertEqual(values['TOTAL'],312179);self.assertEqual(values['SECONDS'],1200)
  manifest=json.loads((HERE/'source-manifest.json').read_text())
  self.assertEqual((manifest['current59RetentionSourceControls'],manifest['observed59InitialAdoptionSourceControls']),(9,33))
  self.assertEqual((manifest['observed59ExactRejectedRecordCount'],manifest['observed59CurrentFileCount'],manifest['observed59AbsentHistoricalLogCount'],manifest['observed59EmptyDirectoryCount']),(10,3,1,6))
  self.assertTrue(manifest['actualRetentionReceiptPinsPending']);self.assertFalse(manifest['actualRetentionAcceptedInThisSnapshot'])
 def test_partial_retention_snapshot_does_not_promote_failure(self):
  text=(HERE/'partial-retention-updater60/reference.py.snapshot').read_text()
  self.assertIn("'failed_or_unconfirmed_exact_current59_retention'",text)
  self.assertIn("'freshFullPreinstallInventoryRequired':True",text)
  self.assertIn("'fullInventoryBeforeAfterEqual':False",text)
  self.assertIn("'providerFingerprintScope':'new_local_filesystem_readback_not_saved_device_copy_stamps'",text)
  manifest=json.loads((HERE/'source-manifest.json').read_text())
  self.assertEqual(manifest['partialRetentionUpdaterSourceControls'],40)
  self.assertFalse(manifest['partialRetentionFailedProducerReclassified'])
 def test_partial_original50_runtime_tuple_pending(self):
  tree=ast.parse((HERE/'partial-retention-original50/composition.py.snapshot').read_text());values={}
  for node in tree.body:
   if isinstance(node,ast.Assign)and isinstance(node.value,ast.Constant):
    for target in node.targets:
     if isinstance(target,ast.Name):values[target.id]=node.value.value
  self.assertEqual(values['SEALED_INSTALL_SHA'],'PENDING');self.assertEqual(values['SEALED_RESULT_SHA'],'PENDING');self.assertIsNone(values['SEALED_INPUT_COUNT'])
  self.assertEqual(json.loads((HERE/'source-manifest.json').read_text())['partialRetentionOriginal50SourceControls'],26)
 def test_initial_quiescence_is_exact_bounded_and_source_only(self):
  text=(HERE/'initial-own59-quiescence-updater60/install.py.snapshot').read_text()
  tree=ast.parse(text);functions={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
  values={n.targets[0].id:n.value.value for n in tree.body if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)and isinstance(n.value,ast.Constant)}
  self.assertEqual(values['INITIAL_QUIESCENCE_SECONDS'],180)
  self.assertIn('Session.close_owned',ast.unparse(functions['initial_owned_quiescence']))
  self.assertIn("'restartOriginProven': False",ast.unparse(functions['initial_owned_quiescence']))
  manifest=json.loads((HERE/'source-manifest.json').read_text())
  self.assertEqual(manifest['initialOwn59QuiescenceSourceControls'],48)
  self.assertFalse(manifest['initialOwn59QuiescenceDeviceExecuted'])
  self.assertTrue(manifest['initialOwn59QuiescenceFutureInstallPolicyUnchanged'])
 def test_initial_quiescence_original50_keeps_pending_installation(self):
  tree=ast.parse((HERE/'initial-own59-quiescence-original50/composition.py.snapshot').read_text());values={}
  for node in tree.body:
   if isinstance(node,ast.Assign)and isinstance(node.value,ast.Constant):
    for target in node.targets:
     if isinstance(target,ast.Name):values[target.id]=node.value.value
  self.assertEqual(values['SEALED_INSTALL_SHA'],'PENDING');self.assertEqual(values['SEALED_RESULT_SHA'],'PENDING');self.assertIsNone(values['SEALED_INPUT_COUNT'])
  manifest=json.loads((HERE/'source-manifest.json').read_text())
  self.assertEqual(manifest['initialOwn59QuiescenceOriginal50SourceControls'],27)
  self.assertTrue(manifest['initialOwn59QuiescenceOriginal50InstallationPinsPending'])
 def test_ordered_quiescence_reader_has_complete_chronology(self):
  text=(HERE/'ordered-own59-quiescence-updater60/binding.py.snapshot').read_text()
  self.assertIn('sequence==list(range(sequence[0],sequence[0]+len(sequence)))',text)
  self.assertIn('observed_queries==query_names',text)
  manifest=json.loads((HERE/'source-manifest.json').read_text())
  self.assertEqual(manifest['orderedOwn59QuiescenceSourceControls'],51)
  self.assertFalse(manifest['initialOwn59QuiescenceOriginalReaderChronologyAccepted'])
 def test_ordered_original50_keeps_actual_pins_pending(self):
  tree=ast.parse((HERE/'ordered-own59-quiescence-original50/composition.py.snapshot').read_text());values={}
  for node in tree.body:
   if isinstance(node,ast.Assign)and isinstance(node.value,ast.Constant):
    for target in node.targets:
     if isinstance(target,ast.Name):values[target.id]=node.value.value
  self.assertEqual(values['SEALED_INSTALL_SHA'],'PENDING');self.assertEqual(values['SEALED_RESULT_SHA'],'PENDING');self.assertIsNone(values['SEALED_INPUT_COUNT'])
  manifest=json.loads((HERE/'source-manifest.json').read_text())
  self.assertEqual(manifest['orderedOwn59QuiescenceOriginal50SourceControls'],27)
  self.assertFalse(manifest['actualNative60Installed'])
 def test_fixture674_source_preserves_hash_and_pending_boundary(self):
  helper=(HERE/'fixture674-own59-quiescence-updater60/providers.py.snapshot').read_text()
  self.assertIn('==674',helper);self.assertIn('Historical logical digest must not change',helper)
  tree=ast.parse((HERE/'fixture674-own59-quiescence-original50/composition.py.snapshot').read_text());values={}
  for node in tree.body:
   if isinstance(node,ast.Assign)and isinstance(node.value,ast.Constant):
    for target in node.targets:
     if isinstance(target,ast.Name):values[target.id]=node.value.value
  self.assertEqual(values['SEALED_INSTALL_SHA'],'PENDING');self.assertEqual(values['SEALED_RESULT_SHA'],'PENDING');self.assertIsNone(values['SEALED_INPUT_COUNT'])
  manifest=json.loads((HERE/'source-manifest.json').read_text())
  self.assertEqual((manifest['fixture674UpdaterSourceControls'],manifest['fixture674Original50SourceControls']),(54,27))
  self.assertFalse(manifest['fixture674HistoricalExpectedHashesRewritten'])
if __name__=='__main__':unittest.main()
