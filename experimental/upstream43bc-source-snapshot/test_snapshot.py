"""Check inert archived source as data; never import a snapshot."""
import ast
import hashlib
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


class SnapshotTests(unittest.TestCase):
    def test_exact_inventory_and_inert_original_logic(self):
        manifest = json.loads((HERE / 'source-manifest.json').read_text())
        self.assertEqual(manifest['snapshotCount'], 30)
        names = {str(p.relative_to(HERE)) for p in HERE.rglob('*.snapshot')}
        self.assertEqual(names, set(manifest['sourceFiles']))
        guard = manifest['guardPrefix'].encode('utf-8')
        for name, row in manifest['sourceFiles'].items():
            data = (HERE / name).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), row['snapshotSha256'], name)
            self.assertTrue(data.startswith(guard), name)
            body = data[row['guardPrefixBytes']:]
            self.assertEqual(hashlib.sha256(body).hexdigest(), row['normalizedSha256'], name)
            tree = ast.parse(data.decode('utf-8'), filename=name)
            self.assertIsInstance(tree.body[0], ast.Raise, name)
            self.assertEqual(ast.literal_eval(tree.body[0].exc.args[0]),
                             'Snapshot only; use reviewed current tooling.', name)
            self.assertFalse((HERE / name).stat().st_mode & 0o111, name)
            for redaction in row['redactions']:
                self.assertEqual(body.decode('utf-8').count(redaction['replacement']),
                                 redaction['normalizedOccurrences'], name)

    def test_public_archive_excludes_private_payload_and_acceptance(self):
        manifest = json.loads((HERE / 'source-manifest.json').read_text())
        self.assertFalse(manifest['snapshotModulesExecuted'])
        self.assertFalse(manifest['sourceMapsRawLogsPairingAssetsIncluded'])
        self.assertFalse(manifest['runtimeOrGameplayQualifiedByArchive'])
        for path in HERE.rglob('*'):
            if path.is_file():
                self.assertIn(path.suffix, {'.snapshot', '.py', '.md', '.json'})
                text = path.read_text()
                if path.name != 'test_snapshot.py':
                    self.assertNotIn('/Users/', text)
                    self.assertNotRegex(text, r'\b[0-9A-F]{8}-[0-9A-F]{16}\b')
                    self.assertNotIn('pre-cleanup.owned-log', text)


if __name__ == '__main__':
    unittest.main()
