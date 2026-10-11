"""Pure/injected gate tests; no compiler, Wine or candidate execution."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('once_execution_tests',HERE/'run.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
recipe=m.load(m.CANDIDATE/'recipe.py','once_recipe_tests')
plan=json.loads(m.PLAN.read_text())


class Runner(unittest.TestCase):
    def test_actual_plan_shape_and_hash(self):
        import hashlib
        self.assertEqual(hashlib.sha256(m.PLAN.read_bytes()).hexdigest(),m.PLAN_SHA)
        m.shape(plan,recipe)

    def test_actual_complete_receipt_budget_below_cap(self):
        self.assertLess(m.receipt_budget(plan),512*1024)
        self.assertNotIn('dependencies\':values', (HERE/'run.py').read_text())

    def test_observed_direct_route_plan_mismatch_refuses(self):
        for key,value in (('directAndIatRouteRequired',False),('retainedDirectOnceCallers',[])):
            p=copy.deepcopy(plan);p[key]=value
            with self.assertRaises(ValueError):m.shape(p,recipe)

    def test_static_direct_symbol_flag_refuses_before_tests(self):
        seen=[]
        def command(row,index):
            seen.append(row['name']);return {'exitCode':0}
        with self.assertRaises(ValueError):
            m.run_commands(plan,recipe,command,lambda:{},lambda:{
                'staticNamedExportAndOwnedCallerImportsVerified':True,
                'directAndIatFreshObjectSymbolsVerified':False},{})
        self.assertFalse(any(name.startswith('run-') for name in seen))

    def test_command_or_budget_change_refuses(self):
        for mutate in (lambda p:p['commands'].reverse(),
                       lambda p:p['commands'][0].update(timeoutSeconds=181),
                       lambda p:p['rootExecutionRequirements'].update(capturedStreamBytesMaximum=2*m.MIB)):
            value=copy.deepcopy(plan);mutate(value)
            with self.assertRaises(ValueError):m.shape(value,recipe)

    def test_actual_gcc_dependency_format(self):
        p=m.FULL/'unwind-first-miss-diagnostic-build-attempt2/Exports.cpp.obj.d'
        target=p.with_suffix('')
        names=m.dependency_record(p.read_text(),target)
        self.assertGreater(len(names),100)
        self.assertIn(m.FULL/'qualification-source/core/libs/prx/libc/include/exceptions/Unwind.hpp',names)

    def test_dependency_traversal_drive_and_extra_records_refuse(self):
        for value in ('Z:\\output.obj: C:\\source.h','Z:\\output.obj: Z:\\dir\\..\\source.h',
                      'Z:\\output.obj: relative.h','Z:\\other.obj: Z:\\source.h',
                      'Z:\\output.obj: Z:\\source.h\nZ:\\other.obj: Z:\\source.h'):
            with self.assertRaises(ValueError):m.dependency_record(value,Path('/output.obj'))

    def test_unbound_dependency_refuses_before_any_link(self):
        r=m.load(m.BORROWED/'run.py','dependency_reader')
        original=m.OUT
        with tempfile.TemporaryDirectory() as directory:
            m.OUT=Path(directory).resolve()
            try:
                source=m.OUT/'source.h';source.write_text('header')
                for name in m.COMPILES:
                    (m.OUT/(name+'.d')).write_text('Z:'+str(m.OUT/(name+'.obj'))+': Z:'+str(source))
                with self.assertRaisesRegex(ValueError,'Unbound actual compiler dependency'):
                    m.admit_dependencies({'inputs':{}},r)
                row=r.read(source)
                values=m.admit_dependencies({'inputs':{str(source):row}},r)
                self.assertEqual(set(values),set(m.COMPILES))
                source.write_text('changed')
                with self.assertRaises(ValueError):m.admit_dependencies({'inputs':{str(source):row}},r)
            finally:m.OUT=original

    def execute_fake(self, *, bad=None, deps_error=False, static_error=False):
        seen=[];result={}
        def command(row,index):
            seen.append(row['name'])
            output='\n'.join('COMPILER_ONCE_PASS '+name for name in recipe.CASES)+'\nCOMPILER_ONCE_COMPLETE cases=8 errors=0\n'
            if index==15:output=recipe.ORIGINAL_MARKER+'\n'
            value={'exitCode':0,'captureComplete':True,'childJoined':True,
                'ownedGroupAbsent':True,'stdout':output,'stderr':''}
            if index==bad:value['exitCode']=3
            return value
        def deps():
            seen.append('dependency-gate')
            if deps_error:raise ValueError('dependency rejected')
            return {'admitted':True}
        def static():
            seen.append('static-gate')
            if static_error:raise ValueError('static rejected')
            return {'staticNamedExportAndOwnedCallerImportsVerified':True,
                    'directAndIatFreshObjectSymbolsVerified':True}
        try:m.run_commands(plan,recipe,command,deps,static,result)
        except ValueError: return seen,result,False
        return seen,result,True

    def test_gate_order_and_both_actual_policies(self):
        seen,result,passed=self.execute_fake()
        self.assertTrue(passed)
        self.assertEqual(seen[6:8],['dependency-gate','link-libc'])
        self.assertEqual(seen[-3:],['static-gate','run-compiler_once_tests.exe','run-windows_exception_tests.exe'])
        self.assertTrue(result['focusedTestsPassed'] and result['originalWindowsExceptionsPassed'])

    def test_dependency_rejection_never_links(self):
        seen,result,passed=self.execute_fake(deps_error=True)
        self.assertFalse(passed);self.assertEqual(seen[-1],'dependency-gate')
        self.assertFalse(any(name.startswith('link-') for name in seen))

    def test_static_rejection_never_runs(self):
        seen,result,passed=self.execute_fake(static_error=True)
        self.assertFalse(passed);self.assertEqual(seen[-1],'static-gate')
        self.assertFalse(any(name.startswith('run-') for name in seen))

    def test_first_compile_failure_stops(self):
        seen,result,passed=self.execute_fake(bad=0)
        self.assertFalse(passed);self.assertEqual(seen,['compile-provider'])

    def test_focused_failure_never_runs_original(self):
        seen,result,passed=self.execute_fake(bad=14)
        self.assertFalse(passed);self.assertEqual(seen[-1],'run-compiler_once_tests.exe')

    def test_original_failure_never_passes(self):
        seen,result,passed=self.execute_fake(bad=15)
        self.assertFalse(passed);self.assertTrue(result['focusedTestsPassed'])
        self.assertNotIn('originalWindowsExceptionsPassed',result)


if __name__=='__main__':unittest.main()
