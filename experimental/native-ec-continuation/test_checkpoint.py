"""Source preservation/parser checks; no compilation or runtime acceptance."""
from pathlib import Path
import hashlib
import importlib.util
import json
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('public_ec_extract', HERE/'extract_harness.py')
e = importlib.util.module_from_spec(spec); spec.loader.exec_module(e)

class Checkpoint(unittest.TestCase):
    def test_manifest_exact_public_bytes_and_status_boundary(self):
        manifest = json.loads((HERE/'source-manifest.json').read_text())
        for name, digest in manifest['files'].items():
            self.assertEqual(hashlib.sha256((HERE/name).read_bytes()).hexdigest(), digest, name)
        self.assertEqual(manifest['historicalNativeEvidence']['candidateControls'], 42)
        self.assertEqual(manifest['historicalNativeEvidence']['nonIOSControls'], 16)
        self.assertEqual(manifest['historicalNativeEvidence']['joinedCommands'], 22)
        self.assertEqual(manifest['historicalNativeEvidence']['emitterControls'], 12)
        self.assertFalse(manifest['productionBuildAccepted'])
        self.assertFalse(manifest['deviceExecuted'])
        self.assertFalse(manifest['cpuAccepted'])

    def test_no_local_private_paths_or_evidence_records_published(self):
        for path in HERE.rglob('*'):
            if path.is_file():
                self.assertNotIn(b'/' + b'Users/', path.read_bytes(), str(path))
                self.assertNotIn(b'pre-cleanup.' + b'owned-log', path.read_bytes(), str(path))

    def test_definition_not_earlier_call(self):
        text = 'void Caller() { F(1,2); }\nstatic int F(int a, int b) { return a+b; }\n'
        self.assertTrue(e.function(text, 'F').startswith('static int F'))

    def test_missing_definition_refuses(self):
        with self.assertRaises(ValueError): e.function('void C() { F(); }', 'F')

    def test_unclosed_definition_refuses(self):
        with self.assertRaises(ValueError): e.function('static int F() {', 'F')

    def test_unknown_sources_refuse_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root/'source'
            manifest = json.loads((HERE/'source-manifest.json').read_text())
            for name in manifest['candidateSources']:
                p = source/name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text('unknown')
            output = root/'output'
            with self.assertRaisesRegex(ValueError, 'Exact published production source'):
                e.generate(output, source, root/'signal.c', root/'unwind.h')
            self.assertFalse(output.exists())

if __name__ == '__main__': unittest.main()
