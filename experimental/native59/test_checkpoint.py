"""Portable source-only checkpoint checks. No compiler or hardware calls."""
from pathlib import Path
import importlib.util
import json
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('extract_controls', HERE / 'extract-controls.py')
extractor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extractor)


class Checkpoint(unittest.TestCase):
    def test_all_preserved_source_digests(self):
        manifest = extractor.verify_checkpoint()
        self.assertFalse(manifest['defaultPatchSeriesChanged'])
        self.assertFalse(manifest['privateFixturesAssetsTokensIncluded'])
        self.assertEqual(manifest['wireProtocolVersion'], 931)

    def test_no_local_identity_or_private_artifact_in_source(self):
        manifest = extractor.verify_checkpoint()
        for name in manifest['files']:
            raw = (HERE / name).read_bytes()
            if name != 'test_checkpoint.py':
                for private in (b'/Users/', b'Authorization: Bearer'):
                    self.assertNotIn(private, raw, name)
        self.assertIn("DEVICE='EXPLICIT_DEVICE_ID_REQUIRED'",
                      (HERE / 'own-window/protocol.py').read_text())

    def test_missing_production_source_refuses_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'output'
            with self.assertRaisesRegex(ValueError, 'All experimental series'):
                extractor.extract(Path(directory), output)
            self.assertFalse(output.exists())

    def test_exact_declaration_not_approximate_or_duplicate(self):
        body = 'static int example(int a) { if (a) { return 1; } return 0; }\n'
        self.assertEqual(extractor.function(body, 'static int example('), body)
        with self.assertRaises(ValueError):
            extractor.function(body + body, 'static int example(')
        with self.assertRaises(ValueError):
            extractor.function(body, 'static int other(')

    def test_complete_body_and_unique_markers_required(self):
        with self.assertRaises(ValueError):
            extractor.function('static int example() {', 'static int example(')
        self.assertEqual(extractor.section('BEGINrealEND', 'BEGIN', 'END'), 'real')
        with self.assertRaises(ValueError):
            extractor.section('BEGINBEGINrealEND', 'BEGIN', 'END')

    def test_fixed_native_and_owner_harnesses_use_production_helpers(self):
        wine = (HERE / 'controls/wine/native-harness.c').read_text()
        self.assertIn('#include "production-server-bodies.inc"', wine)
        self.assertIn('pthread_sigmask', wine)
        self.assertIn('SIGUSR2', wine)
        owner = (HERE / 'controls/owner/native-harness.c').read_text()
        self.assertIn('#include "source/ios_critical_owner_sample.h"', owner)
        self.assertIn('#include "source/ios_critical_owner_mapping.h"', owner)

    def test_native59_addition_is_diagnostic_only(self):
        patch = (HERE / 'patches/madeira/0053-bounded-critical-owner-sampler.patch').read_text()
        self.assertIn('MADEIRA_CRITICAL_OWNER_SAMPLER', patch)
        self.assertIn('IOS_CO_MAX_ROWS 256u', patch)
        self.assertIn('IOS_CO_MAX_MAPPINGS 512u', patch)
        self.assertIn('resume_status != KERN_SUCCESS', patch)
        for operation in ('+        NtResumeThread(', '+        NtSetContextThread('):
            self.assertNotIn(operation, patch)


if __name__ == '__main__':
    unittest.main()
