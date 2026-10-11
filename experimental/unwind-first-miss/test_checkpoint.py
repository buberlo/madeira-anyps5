"""Portable source preservation controls; no command, compiler or Wine."""
import ast
import hashlib
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent


class Checkpoint(unittest.TestCase):
    def test_saved_sources_match_manifest(self):
        q = json.loads((HERE/'manifest.json').read_text())
        for name,row in q['files'].items():
            p=HERE/name
            self.assertEqual(len(p.read_bytes()),row['bytes'],name)
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),row['sha256'],name)

    def test_trace_limits_and_exact_opt_in(self):
        text=(HERE/'source/Unwind.cpp').read_text()
        self.assertIn('enabled[0] != \'1\'',text)
        self.assertIn('record >= 8',text)
        self.assertIn('char output[1024]',text)
        self.assertIn('count <= 96',text)
        self.assertNotIn('RtlVirtualUnwind(',text)

    def test_changed_source_only_adds_trace_and_calls(self):
        before=(HERE/'source/Unwind.before.cpp').read_text()
        after=(HERE/'source/Unwind.cpp').read_text()
        for function in ['_Unwind_RaiseException_nid_postfix','_Unwind_Resume_nid_postfix','GetRules','PhaseTwo','Step']:
            def body(text):
                start=text.index(function+'(');opening=text.index('{',start);depth=1;index=opening+1
                while depth:
                    depth+=(text[index]=='{')-(text[index]=='}');index+=1
                return text[opening:index]
            self.assertEqual(body(before),body(after),function)

    def test_snapshot_import_is_definition_only(self):
        tree=ast.parse((HERE/'snapshot/run.py').read_text())
        calls=[node for node in tree.body if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call)]
        self.assertEqual(calls,[])
        text=(HERE/'snapshot/run.py').read_text()
        self.assertIn("'DYLD_','CCACHE_'",text)
        self.assertIn("'runtimeQualified':False",text)

    def test_public_source_has_no_local_absolute_paths(self):
        for p in HERE.rglob('*'):
            if p.is_file() and p.suffix in ('.py','.cpp','.hpp','.patch'):
                self.assertNotIn(b'/'+b'Users/',p.read_bytes(),str(p))


if __name__=='__main__':unittest.main()
