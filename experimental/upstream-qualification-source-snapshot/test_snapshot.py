"""Portable archival checks only; snapshot modules are never imported."""
import ast
import hashlib
import json
import re
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


class Snapshot(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((HERE / 'source-manifest.json').read_text())

    def test_exact_selected_inventory(self):
        names = {
            'root/promote-latest15.py.snapshot',
            'root/promote-latest16.py.snapshot',
            'root/apply-proof-fixture-successor.py.snapshot',
            'root/run-native-latest15.py.snapshot',
            'root/run-native-latest15-fixture-successor.py.snapshot',
            'root/run-current-shader-memory.py.snapshot',
            'root/run-full-hle-latest16.py.snapshot',
            'color-xor/test_fixture.py.snapshot',
        }
        for folder in (
            'graphics-grouped-stencil-fixture-proposal',
            'graphics-stencil-fixture-complete-proposal',
            'graphics-stencil-and-reserved-fixture-proposal',
            'graphics-exact-barycentric-proof-fallback-proposal',
        ):
            names.add('targeted/' + folder + '/run-targeted.py.snapshot')
        self.assertEqual(set(self.manifest['sourceFiles']), names)
        self.assertEqual({str(p.relative_to(HERE)) for p in HERE.rglob('*.snapshot')}, names)
        self.assertEqual(self.manifest['snapshotCount'], 12)

    def test_exact_snapshot_and_body_hashes(self):
        total = 0
        for name, record in self.manifest['sourceFiles'].items():
            data = (HERE / name).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), record['snapshotSha256'], name)
            self.assertEqual(len(data), record['snapshotBytes'], name)
            body = data[record['guardPrefixBytes']:]
            self.assertEqual(hashlib.sha256(body).hexdigest(), record['normalizedSha256'], name)
            self.assertRegex(record['originalSha256'], r'^[0-9a-f]{64}$')
            total += len(data)
        self.assertEqual(total, self.manifest['snapshotBytes'])

    def test_unconditional_guard_precedes_all_original_logic(self):
        guard = self.manifest['guardPrefix'].encode()
        for name, record in self.manifest['sourceFiles'].items():
            path = HERE / name
            data = path.read_bytes()
            self.assertTrue(data.startswith(guard), name)
            self.assertEqual(hashlib.sha256(guard).hexdigest(), record['guardPrefixSha256'], name)
            parsed = ast.parse(data.decode(), filename=name)
            first = parsed.body[0]
            self.assertIsInstance(first, ast.Raise, name)
            self.assertIsInstance(first.exc, ast.Call, name)
            self.assertIsInstance(first.exc.func, ast.Name, name)
            self.assertEqual(first.exc.func.id, 'RuntimeError', name)
            self.assertEqual(ast.literal_eval(first.exc.args[0]),
                             'Snapshot-only module; use reviewed current tooling instead.', name)
            self.assertFalse(path.stat().st_mode & 0o111, name)

    def test_normalized_ast_is_preserved_without_execution(self):
        for name, record in self.manifest['sourceFiles'].items():
            tree = ast.parse((HERE / name).read_text(), filename=name)
            original_body = ast.Module(body=tree.body[1:], type_ignores=tree.type_ignores)
            digest = hashlib.sha256(ast.dump(original_body, include_attributes=False).encode()).hexdigest()
            self.assertEqual(digest, record['normalizedAstSha256'], name)

    def test_declared_redactions_only(self):
        for name, record in self.manifest['sourceFiles'].items():
            body = (HERE / name).read_bytes()[record['guardPrefixBytes']:].decode()
            self.assertEqual(len(record['redactions']), 1)
            change = record['redactions'][0]
            self.assertEqual(change['kind'], 'absolute-local-project-root')
            self.assertEqual(change['replacement'], '__LOCAL_PROJECT_ROOT__')
            self.assertEqual(body.count(change['replacement']), change['occurrences'], name)
            self.assertTrue(record['originalVerifiedUnchanged'])

    def test_archive_has_no_private_payload_or_result_files(self):
        allowed = {'README.md', 'source-manifest.json', 'test_snapshot.py'}
        for path in HERE.rglob('*'):
            if not path.is_file():
                continue
            relative = str(path.relative_to(HERE))
            self.assertTrue(relative in allowed or relative in self.manifest['sourceFiles'], relative)
            self.assertNotIn(b'/' + b'Users/', path.read_bytes(), relative)
            self.assertNotRegex(path.read_bytes(), rb'100\.(?:89|104)\.')
            self.assertFalse(re.search(r'\.(?:zip|bin|exe|prx|dll|req|log|p12|mobileprovision)$', relative))

    def test_source_preservation_does_not_relabel_runtime_results(self):
        for field in (
            'privateProviderMapsIncluded', 'rawLogsOrReceiptsIncluded', 'gameAssetsIncluded',
            'fullUpstreamSourceCopiesIncluded', 'snapshotModulesImportedOrExecuted',
            'compilerWineDeviceActions', 'historicalFailuresRelabeled',
            'runtimeOrGameplayQualificationClaimed',
        ):
            self.assertFalse(self.manifest[field], field)
        self.assertTrue(self.manifest['privateOriginalsPreserved'])
        self.assertTrue(self.manifest['colorXorOriginalControlsRequireHeldSourceAndCandidate'])


if __name__ == '__main__':
    unittest.main()
