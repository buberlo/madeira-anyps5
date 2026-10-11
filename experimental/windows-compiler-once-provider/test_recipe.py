"""Pure/temporary admission tests. C++ behavior is tested by the actual fixture."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('once_recipe',HERE/'recipe.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class Admission(unittest.TestCase):
    def imports(self): return {'libc.prx':[m.PRIVATE,'__cxa_throw'], 'libwinpthread-1.dll':['pthread_mutex_lock']}
    def contract(self): return {'e'+str(i):{'ordinal':i,'data':i==2} for i in range(1,1062)}
    def result(self): return {'exitCode':0,'captureComplete':True,'childJoined':True,'ownedGroupAbsent':True,
        'stdout':'\n'.join('COMPILER_ONCE_PASS '+name for name in m.CASES)+'\nCOMPILER_ONCE_COMPLETE cases=8 errors=0\n','stderr':''}
    def test_owned_private_import(self): m.validate_imports(self.imports())
    def test_case_normalized_library(self): m.validate_imports({'LIBC.PRX':[m.PRIVATE]})
    def test_missing_private_refused(self):
        with self.assertRaises(ValueError): m.validate_imports({'libc.prx':['__cxa_throw']})
    def test_private_from_wrong_library_refused(self):
        with self.assertRaises(ValueError): m.validate_imports({'other.dll':[m.PRIVATE]})
    def test_native_once_refused_even_with_private(self):
        value=self.imports(); value['libwinpthread-1.dll'].append('pthread_once')
        with self.assertRaises(ValueError): m.validate_imports(value)
    def test_case_alias_refused(self):
        with self.assertRaises(ValueError): m.validate_imports({'libc.prx':[m.PRIVATE],'LIBC.PRX':[m.PRIVATE]})
    def test_def_preserves_data_and_appends_private(self):
        value=m.export_def(self.contract())
        self.assertIn('"e2" @2 DATA\n',value)
        self.assertTrue(value.endswith(m.PRIVATE+' @1062\n'))
        self.assertEqual(len(value.splitlines()),1064)
    def test_missing_export_refused(self):
        value=self.contract(); value.pop('e1')
        with self.assertRaises(ValueError): m.export_def(value)
    def test_ordinal_collision_refused(self):
        value=self.contract(); value['e1']['ordinal']=2
        with self.assertRaises(ValueError): m.export_def(value)
    def test_export_type_not_truthy(self):
        value=self.contract(); value['e1']['data']=1
        with self.assertRaises(ValueError): m.export_def(value)
    def test_def_injection_refused(self):
        value=self.contract(); value['bad\nname']=value.pop('e1')
        with self.assertRaises(ValueError): m.export_def(value)
    def test_private_already_present_refused(self):
        value=self.contract(); value[m.PRIVATE]=value.pop('e1')
        with self.assertRaises(ValueError): m.export_def(value)
    def test_explicit_link_bridge_and_original_source(self):
        out=m.FULL/'once-test-fake-output'
        commands=m.commands(out,[Path('/retained/object')],['-lkernel32'])
        original=next(c for c in commands if c['name']=='compile-original')
        self.assertEqual(original['windowsArgv'][-1],m.windows(m.SOURCE/'core/libs/tests/WindowsExceptions.cpp'))
        libc=next(c for c in commands if c['name']=='link-libc')
        self.assertIn('-lsynchronization',libc['windowsArgv'])
        self.assertIn(m.windows(out/'bridge-local.obj'),libc['windowsArgv'])
        for name in ('windows_exception_tests.exe','compiler_once_tests.exe','compiler_once_cross.dll'):
            call=next(c for c in commands if c['name']=='link-'+name)
            self.assertIn(m.windows(out/'bridge-import.obj'),call['windowsArgv'])
    def test_runtime_limits_and_exact_paths(self):
        commands=m.commands(m.FULL/'once-test-fake-output',[],[])
        runs=[c for c in commands if c['name'].startswith('run-')]
        self.assertEqual(len(runs),2)
        self.assertTrue(all(c['timeoutSeconds']==60 for c in runs))
        focused=next(c for c in runs if 'compiler_once_tests' in c['name'])
        self.assertEqual(len(focused['windowsArgv']),3)
        self.assertFalse(any('APS5_UNWIND_MISS_TRACE' in c.get('extraEnvironment',{}) for c in runs))
    def test_unknown_output_and_parent_escape_refused(self):
        for path in (Path('relative'),Path('/tmp/output'),m.FULL/'../outside'):
            with self.assertRaises(ValueError): m.output_path(path,True)
    def test_existing_output_refused(self):
        with self.assertRaises(ValueError): m.output_path(HERE,True)
    def test_byte_and_identity_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'input'; path.write_bytes(b'held')
            value=m.row(path); m.replay({str(path):value})
            path.write_bytes(b'changed')
            with self.assertRaises(ValueError): m.replay({str(path):value})
    def test_symlink_provider_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'source'; source.write_bytes(b'x')
            alias=Path(directory)/'alias'; alias.symlink_to(source)
            with self.assertRaises(ValueError): m.row(alias)
    def test_current_baseline_pe_export_def_real_read_only(self):
        contract=m.export_contract(m.pe(m.BUILD/'core/libs/libs/unpatched/libc.prx'))
        self.assertEqual(len(contract),1061)
        self.assertEqual(set(v['ordinal'] for v in contract.values()),set(range(1,1062)))
        self.assertIn(' DATA',m.export_def(contract))
    def test_focused_runtime_policy(self): m.validate_runtime_result(self.result(),True)
    def test_fixture_nonzero_refused(self):
        value=self.result(); value['exitCode']=3
        with self.assertRaises(ValueError): m.validate_runtime_result(value,True)
    def test_missing_or_reordered_case_refused(self):
        for text in (self.result()['stdout'].replace('COMPILER_ONCE_PASS '+m.CASES[0]+'\n',''),
                     self.result()['stdout'].replace(m.CASES[0],'unexpected')):
            value=self.result(); value['stdout']=text
            with self.assertRaises(ValueError): m.validate_runtime_result(value,True)
    def test_unjoined_or_incomplete_refused(self):
        for key in ('captureComplete','childJoined','ownedGroupAbsent'):
            value=self.result(); value[key]=False
            with self.assertRaises(ValueError): m.validate_runtime_result(value,True)
    def test_original_requires_actual_complete_marker(self):
        value=self.result()
        with self.assertRaises(ValueError): m.validate_runtime_result(value,False)
        value['stdout']=m.ORIGINAL_MARKER+'\n'; m.validate_runtime_result(value,False)

if __name__=='__main__': unittest.main()
