from contextlib import chdir
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[2] / 'scripts/build-hle.py'
spec = importlib.util.spec_from_file_location('build_hle_new', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


@unittest.skipIf(os.name == 'nt', 'Wine executable resolution is used on POSIX hosts')
class WineExecutable(unittest.TestCase):
    def executable(self, root):
        path = root / 'tool path' / 'wine'
        path.parent.mkdir()
        path.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
        path.chmod(0o700)
        return path

    def invoke_from_other_directory(self, executable, root):
        working = root / 'build'
        working.mkdir()
        result = subprocess.run([executable, 'cmd', '/c', 'fixture.cmd'], cwd=working,
                                check=True, capture_output=True, text=True)
        self.assertEqual(result.stdout, 'cmd\n/c\nfixture.cmd\n')

    def test_relative_slash_path_survives_test_cwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            expected = self.executable(root)
            with chdir(root):
                executable = m.resolve_wine_executable('./tool path/wine')
            self.assertEqual(executable, str(expected))
            self.invoke_from_other_directory(executable, root)

    def test_bare_command_with_relative_path_entry_survives_test_cwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            expected = self.executable(root)
            with chdir(root), patch.dict(os.environ, {'PATH': 'tool path'}):
                executable = m.resolve_wine_executable('wine')
            self.assertEqual(executable, str(expected))
            self.invoke_from_other_directory(executable, root)

    def test_missing_explicit_path_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp, chdir(tmp):
            with self.assertRaisesRegex(ValueError, 'not found or not executable'):
                m.resolve_wine_executable('./missing/wine')

    def test_missing_bare_command_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'PATH': tmp}):
            with self.assertRaises(ValueError):
                m.resolve_wine_executable('wine')

    def test_non_executable_explicit_file_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'wine'
            path.write_text('not executable')
            path.chmod(0o600)
            with self.assertRaises(ValueError):
                m.resolve_wine_executable(str(path))


class Configured(unittest.TestCase):
    def model(self, root, *, configuration='Release', target='extra_tests', kind='EXECUTABLE'):
        reply = root / '.cmake/api/v1/reply'
        reply.mkdir(parents=True)
        (reply / 'index-1.json').write_text(json.dumps({'reply': {'client-anyps5-hle': {'codemodel-v2': {'jsonFile': 'model.json'}}}}))
        (reply / 'model.json').write_text(json.dumps({'kind': 'codemodel', 'version': {'major': 2}, 'configurations': [{'name': configuration, 'targets': [{'name': target, 'jsonFile': 'target.json'}]}]}))
        (reply / 'target.json').write_text(json.dumps({'name': target, 'type': kind}))
        return reply

    def test_owned_query_and_configured_platform_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            m.prepare_codemodel(root)
            self.assertEqual((root / '.cmake/api/v1/query/client-anyps5-hle/codemodel-v2').read_bytes(), b'')
            self.model(root)
            self.assertEqual(m.configured_targets(root), {'extra_tests': 'EXECUTABLE'})
    def test_last_index_selected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); reply = self.model(root)
            (reply / 'index-0.json').write_text('{}')
            self.assertIn('extra_tests', m.configured_targets(root))
    def test_missing_reply(self):
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(ValueError): m.configured_targets(Path(tmp))
    def test_missing_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.model(root, configuration='Debug')
            with self.assertRaises(ValueError): m.configured_targets(root)
    def test_unsafe_reply_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); reply = self.model(root)
            (reply / 'index-1.json').write_text(json.dumps({'reply': {'client-anyps5-hle': {'codemodel-v2': {'jsonFile': '../model.json'}}}}))
            with self.assertRaises(ValueError): m.configured_targets(root)
    def test_duplicate_and_mismatched_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); reply = self.model(root)
            model = json.loads((reply / 'model.json').read_text()); model['configurations'][0]['targets'] *= 2
            (reply / 'model.json').write_text(json.dumps(model))
            with self.assertRaises(ValueError): m.configured_targets(root)
            model['configurations'][0]['targets'] = [{'name': 'other_tests', 'jsonFile': 'target.json'}]
            (reply / 'model.json').write_text(json.dumps(model))
            with self.assertRaises(ValueError): m.configured_targets(root)
    def test_platform_missing_additional_is_refused(self):
        available = {name: 'EXECUTABLE' for name in ('relinker', 'nid_patcher', *m.TESTS)}
        available['libc'] = 'SHARED_LIBRARY'
        with self.assertRaisesRegex(ValueError, 'platform'): m.validate_configured_targets(available, ['libc'], ['linux_only_tests'])
    def test_missing_required_default_is_refused(self):
        available = {name: 'EXECUTABLE' for name in ('relinker', 'nid_patcher', *m.TESTS)}
        del available[m.TESTS[0]]
        with self.assertRaises(ValueError): m.validate_configured_targets(available, [], [])
    def test_target_types_are_strict(self):
        available = {name: 'EXECUTABLE' for name in ('relinker', 'nid_patcher', *m.TESTS)}
        available['libc'] = 'STATIC_LIBRARY'
        with self.assertRaises(ValueError): m.validate_configured_targets(available, ['libc'], [])
        available['libc'] = 'SHARED_LIBRARY'; available['extra_tests'] = 'SHARED_LIBRARY'
        with self.assertRaises(ValueError): m.validate_configured_targets(available, ['libc'], ['extra_tests'])
    def test_default_tests_remain_exact_42_and_bundled_deps_pinned(self):
        self.assertEqual(len(m.TESTS), 42)
        self.assertEqual(len(set(m.TESTS)), 42)
        self.assertIn('-DANYPS5_USE_SYSTEM_DEPS=OFF', SCRIPT.read_text())
    def test_own_checkout_commit(self):
        with patch.object(m.subprocess, 'check_output', side_effect=['/candidate\n', 'a' * 40 + '\n']):
            self.assertEqual(m.source_commit(Path('/candidate')), 'a' * 40)
    def test_export_cannot_inherit_wrapper_commit(self):
        with patch.object(m.subprocess, 'check_output', return_value='/wrapper\n') as run:
            with self.assertRaises(ValueError): m.source_commit(Path('/wrapper/build/candidate'))
            self.assertEqual(run.call_count, 1)


if __name__ == '__main__': unittest.main()
