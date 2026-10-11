"""Portable preservation controls; no candidate/Wine/compiler execution."""
import ast
import hashlib
import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent


class Checkpoint(unittest.TestCase):
    def test_all_declared_bytes(self):
        record=json.loads((HERE/'manifest.json').read_text())
        expected=record['files']
        actual={str(p.relative_to(HERE)) for p in HERE.rglob('*') if p.is_file() and p.name!='manifest.json'}
        self.assertEqual(actual,set(expected))
        for name,row in expected.items():
            data=(HERE/name).read_bytes()
            self.assertEqual(len(data),row['bytes'],name)
            self.assertEqual(hashlib.sha256(data).hexdigest(),row['sha256'],name)

    def test_exact_held_executor_and_lifetime_snapshots(self):
        expected={'snapshot/run.py':'c021da05547232856e6336eac0796f2669640ecdc622352e9b163da012c28a7a',
                  'snapshot/lifetime/bounded_local_process.py':'ccc02bafc5e57b55df3208905d849b34427211aca5b21938a7cf8e07b64a33f6',
                  'snapshot/lifetime/run.py':'717fb9edf65a428eb70dd78cb2bd10d0a78148819de104d769cfe5ae6a1ed410'}
        for name,digest in expected.items():
            self.assertEqual(hashlib.sha256((HERE/name).read_bytes()).hexdigest(),digest)
            ast.parse((HERE/name).read_text())

    def test_no_private_data_or_execution_claim(self):
        record=json.loads((HERE/'manifest.json').read_text())
        for key in ('privateBindingsIncluded','capturedLogsIncluded','compiledOutputsIncluded','runtimeQualified','deviceExecuted'):
            self.assertIs(record[key],False)
        for name in record['files']:
            data=(HERE/name).read_bytes()
            self.assertNotRegex(data,rb'[/]Users[/][A-Za-z0-9_. -]+[/]',name)
            self.assertNotRegex(data,rb'PPSA[0-9]{5}',name)
            self.assertTrue(Path(name).suffix in {'.py','.md'} or name=='first-attempt-observation.json')


if __name__=='__main__':unittest.main()
