"""Portable archival integrity checks; archived modules are never imported."""
import ast
import hashlib
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def stable_ast(tree):
    # Python 3.12 adds empty generic type-parameter fields to functions/classes.
    # Remove only those empty metadata fields from the portable representation.
    # Keep the original interpreter-specific AST hashes separately in the manifest.
    for node in ast.walk(tree):
        if 'type_params' in node._fields and getattr(node, 'type_params', None) == []:
            node._fields = tuple(name for name in node._fields if name != 'type_params')
    return ast.dump(tree, include_attributes=False)


class Snapshot(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((HERE / 'source-manifest.json').read_text())

    def test_exact_archive_inventory(self):
        names = {'source_diagnosis.py.snapshot', 'verify_source.py.snapshot'}
        self.assertEqual(set(self.manifest['sourceFiles']), names)
        self.assertEqual({p.name for p in HERE.glob('*.snapshot')}, names)
        self.assertEqual({p.name for p in HERE.iterdir()},
                         names | {'README.md', 'test_snapshot.py', 'source-manifest.json'})

    def test_bound_original_and_snapshot_bytes(self):
        for name, row in self.manifest['sourceFiles'].items():
            data = (HERE / name).read_bytes()
            self.assertEqual(len(data), row['snapshotBytes'], name)
            self.assertEqual(hashlib.sha256(data).hexdigest(), row['snapshotSha256'], name)
            original = data[row['guardPrefixBytes']:]
            self.assertEqual(hashlib.sha256(original).hexdigest(), row['originalSha256'], name)
            self.assertEqual(len(original), row['originalBytes'], name)
            self.assertEqual(row['transformations'], ['unconditional-module-level-guard'], name)

    def test_unconditional_guard_precedes_original_logic(self):
        for name, row in self.manifest['sourceFiles'].items():
            data = (HERE / name).read_bytes()
            guard = self.manifest['guardPrefix'].encode()
            self.assertTrue(data.startswith(guard), name)
            self.assertEqual(len(guard), row['guardPrefixBytes'], name)
            first = ast.parse(data.decode()).body[0]
            self.assertIsInstance(first, ast.Raise, name)
            self.assertIsInstance(first.exc, ast.Call, name)
            self.assertIsInstance(first.exc.func, ast.Name, name)
            self.assertEqual(first.exc.func.id, 'RuntimeError', name)
            self.assertEqual(ast.literal_eval(first.exc.args[0]),
                             'Snapshot-only module; use reviewed current tooling instead.', name)
            self.assertFalse((HERE / name).stat().st_mode & 0o111, name)

    def test_original_ast_preserved_as_data(self):
        historical = {
            'source_diagnosis.py.snapshot': '6c2b6c82dff7f620cbf20def2af5f71d7523e4238b92ed5297bce609bbb05530',
            'verify_source.py.snapshot': 'eaa3aefa020e0de992b7678e836f19f423f7123e8c6d9e4292c15b7a61ced010',
        }
        self.assertEqual(self.manifest['originalAstRuntime'], 'Python 3.12.14')
        self.assertEqual(self.manifest['portableAstNormalization'], 'omit-only-empty-type_params-fields')
        for name, row in self.manifest['sourceFiles'].items():
            parsed = ast.parse((HERE / name).read_text())
            original = ast.Module(body=parsed.body[1:], type_ignores=parsed.type_ignores)
            self.assertEqual(row['originalAstSha256'], historical[name], name)
            if 'type_params' in ast.FunctionDef._fields:
                digest = hashlib.sha256(ast.dump(original, include_attributes=False).encode()).hexdigest()
                self.assertEqual(digest, row['originalAstSha256'], name)
            portable = hashlib.sha256(stable_ast(original).encode()).hexdigest()
            self.assertEqual(portable, row['portableAstSha256'], name)

    def test_no_absolute_private_root_or_binary_payload(self):
        for path in HERE.iterdir():
            self.assertTrue(path.is_file() and not path.is_symlink(), path.name)
            self.assertNotIn(b'/' + b'Users/', path.read_bytes(), path.name)
            self.assertNotIn(path.suffix, {'.log', '.zip', '.exe', '.prx', '.req', '.p12'})
        for field in ('privateProviderMapsIncluded', 'rawLogsOrReceiptsIncluded',
                      'fullUpstreamSourceCopiesIncluded', 'gameAssetsIncluded'):
            self.assertFalse(self.manifest[field], field)

    def test_source_archival_does_not_claim_execution(self):
        self.assertTrue(self.manifest['privateOriginalsPreserved'])
        for field in ('snapshotModulesImportedOrExecuted', 'compilerWineDeviceActions',
                      'historicalFailuresRelabeled', 'runtimeOrGameplayQualificationClaimed'):
            self.assertFalse(self.manifest[field], field)
        self.assertTrue(self.manifest['modelRequiresHeldSourceAndIndependentFixture'])


if __name__ == '__main__':
    unittest.main()
