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
  sources=list(HERE.rglob('*.snapshot'));self.assertEqual(len(sources),19)
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
if __name__=='__main__':unittest.main()
