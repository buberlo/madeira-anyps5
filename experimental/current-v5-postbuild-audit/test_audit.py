import copy
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import types
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('v5audit',HERE/'audit.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
helper=a.load(a.ROOT/'scripts/build-hle.py','audit_hle_test')
recipe=a.load(a.FULL/'windows-compiler-once-direct-provider-proposal/recipe.py','audit_recipe_test')

def registration():
    return {'tests':[{'name':'windows_compiler_once','command':['Z:'+str(p) for p in (
        a.BUILD/'tests/compiler_once_tests.exe',a.BUILD/'core/libs/libs/unpatched/libc.prx',
        a.BUILD/'tests/compiler_once_cross.dll')]}]}

def focused(lines=None,name='windows_compiler_once',extra=''):
    text='\n'.join(lines or [*['COMPILER_ONCE_PASS '+n for n in recipe.CASES],
        'COMPILER_ONCE_COMPLETE cases=8 errors=0'])
    return '<testsuite><testcase name="'+name+'" status="run">'+extra+'<system-out>'+text+'</system-out></testcase></testsuite>'

class Routing(unittest.TestCase):
    def test_owned_private_route(self):
        a.route_imports({'libc.prx':[a.PRIVATE],'libwinpthread-1.dll':['pthread_mutex_lock']},True)
    def test_native_once_route_refused(self):
        with self.assertRaisesRegex(ValueError,'native pthread_once'):
            a.route_imports({'libc.prx':[a.PRIVATE],'libwinpthread-1.dll':['pthread_once']},True)
    def test_private_route_missing(self):
        with self.assertRaisesRegex(ValueError,'provider import absent'):a.route_imports({'libc.prx':['guest']},True)
    def test_nonlibc_image_not_claimed(self):a.route_imports({'libwinpthread-1.dll':['pthread_once']},False)
    def test_case_alias_refused(self):
        with self.assertRaisesRegex(ValueError,'Case-aliased'):a.route_imports({'libc.prx':[], 'LIBC.PRX':[]},False)
    def test_done_export_added_only_to_libc(self):
        baseline={'guest':{'ordinal':1,'data':False}}
        a.export_baseline({**baseline,a.PRIVATE:{'ordinal':1062,'data':False}},baseline,True)
    def test_private_ordinal_wrong(self):
        with self.assertRaisesRegex(ValueError,'1062'):a.export_baseline({a.PRIVATE:{'ordinal':1063,'data':False}},{},True)
    def test_baseline_data_changed(self):
        with self.assertRaisesRegex(ValueError,'Existing module'):a.export_baseline({'g':{'ordinal':1,'data':True}},{'g':{'ordinal':1,'data':False}},False)
    def test_helper_export_refused(self):
        with self.assertRaisesRegex(ValueError,'Incidental'):a.export_baseline({'pthread_once':{}},{'pthread_once':{}},False)
    def test_no_export_directory_valid_exe(self):
        r=types.SimpleNamespace(export_contract=lambda _:self.fail('No export table must not be parsed'))
        self.assertEqual(a.exports(r,types.SimpleNamespace(directory=lambda _:(0,0))),{})

class Registration(unittest.TestCase):
    def test_exact_arguments(self):a.once_registration(json.dumps(registration()))
    def test_wrong_cross_module_argument(self):
        value=registration();value['tests'][0]['command'][2]=value['tests'][0]['command'][1]
        with self.assertRaisesRegex(ValueError,'exact libc'):a.once_registration(json.dumps(value))
    def test_duplicate_case(self):
        value=registration();value['tests']*=2
        with self.assertRaises(ValueError):a.once_registration(json.dumps(value))
    def test_focused_ordered_output(self):a.focused_output(focused(),{'windows_compiler_once':'compiler_once_tests'},recipe)
    def test_output_other_case_not_proof(self):
        with self.assertRaisesRegex(ValueError,'One actual'):a.focused_output(focused(name='unrelated'),{'windows_compiler_once':'compiler_once_tests'},recipe)
    def test_missing_marker(self):
        with self.assertRaisesRegex(ValueError,'Eight ordered'):a.focused_output(focused(['COMPILER_ONCE_COMPLETE cases=8 errors=0']),{'windows_compiler_once':'compiler_once_tests'},recipe)
    def test_reordered_cases(self):
        lines=['COMPILER_ONCE_PASS '+n for n in reversed(recipe.CASES)]+['COMPILER_ONCE_COMPLETE cases=8 errors=0']
        with self.assertRaises(ValueError):a.focused_output(focused(lines),{'windows_compiler_once':'compiler_once_tests'},recipe)
    def test_failure_node_even_with_markers(self):
        with self.assertRaisesRegex(ValueError,'really passed'):a.focused_output(focused(extra='<failure/>'),{'windows_compiler_once':'compiler_once_tests'},recipe)
    def test_completion_duplicate(self):
        lines=['COMPILER_ONCE_PASS '+n for n in recipe.CASES]+['COMPILER_ONCE_COMPLETE cases=8 errors=0']*2
        with self.assertRaises(ValueError):a.focused_output(focused(lines),{'windows_compiler_once':'compiler_once_tests'},recipe)

class GraphAndArtifacts(unittest.TestCase):
    def test_actual_link_not_static_archive(self):
        text='build lib.a: CXX_STATIC_LIBRARY_LINKER__x a.obj\n  LINK_LIBRARIES = liblibc.dll.a\nbuild app.exe: CXX_EXECUTABLE_LINKER__x b.obj | dependency\n  LINK_LIBRARIES = core/libs/libs/implib/liblibc.dll.a\n'
        blocks=a.link_blocks(text)
        self.assertEqual(blocks['app.exe']['objects'],['b.obj'])
        self.assertTrue(a.libc_linked(blocks['app.exe']))
        self.assertFalse(a.libc_linked(blocks['lib.a']))
    def test_duplicate_link_output_refused(self):
        with self.assertRaisesRegex(ValueError,'Duplicate'):a.link_blocks('build a: CXX_EXECUTABLE_LINKER__x b\nbuild a: CXX_EXECUTABLE_LINKER__x c\n')
    def test_current_bridge_source_only(self):
        obj='one/caller_bridge.cpp.obj'
        text='build '+obj+': CXX_COMPILER__x Z$:'+str(a.SOURCE/'core/libs/prx/libc/src/specifics/windows/caller_bridge.cpp')+' || order\n'
        a.bridge_sources(text,[obj])
        with self.assertRaisesRegex(ValueError,'exact prepared'):a.bridge_sources(text.replace('qualification-source-v5','qualification-source'),[obj])
    def test_symlink_artifact_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'real').write_bytes(b'x');(p/'link').symlink_to('real')
            with self.assertRaisesRegex(ValueError,'ordinary'):a.read(p/'link')
    def test_artifact_cap(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a';p.write_bytes(b'123')
            with self.assertRaises(ValueError):a.read(p,2)
    def test_renamed_frame_section(self):
        data=bytearray(512);struct.pack_into('<I',data,0x3c,128)
        struct.pack_into('<H',data,134,1);struct.pack_into('<H',data,148,112)
        data[264:272]=b'.ehfram\0';a.frame_section(types.SimpleNamespace(data=bytes(data)))
        data[264:272]=b'.eh_fram'
        with self.assertRaises(ValueError):a.frame_section(types.SimpleNamespace(data=bytes(data)))
    def test_unfinished_archive_refuses_before_source_or_output_reads(self):
        with tempfile.TemporaryDirectory() as d,patch.object(a,'ARCHIVE',Path(d)/'absent'),patch.object(a,'source_replay') as replay:
            with self.assertRaises(FileNotFoundError):a.audit()
            replay.assert_not_called()

class Provenance(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name);patches=root/'patches/anyps5';patches.mkdir(parents=True)
        for i in range(12):(patches/('%04d.patch'%i)).write_bytes(str(i).encode())
        self.prep=json.loads(a.PREPARATION.read_text())
        tests=registration()['tests']
        tests += [{'name':n.removesuffix('_tests'),'command':['Z:/fixture/'+n+'.exe']} for n in self.prep['additionalTestTargets'] if n!='compiler_once_tests']
        self.log=json.dumps({'tests':tests})
        inventory=helper.additional_ctest_inventory(self.prep['additionalTestTargets'],self.log)
        names=set(inventory)
        for values,_ in helper.CTEST_CONTRACTS.values():names.update(values)
        self.provenance={'targets':self.prep['selectedPrxTargets'],'host_tests_passed':list(helper.TESTS),
            'additional_host_tests_passed':self.prep['additionalTestTargets'],
            'host_test_case_results':{n:{'status':'passed'} for n in names},'host_test_cases_skipped':[],
            'host_test_runtime_inputs_verified_unchanged':True,'device_or_gameplay_verified':False,
            'anyps5_commit':self.prep['upstreamCommit'],'patches':{p.name:a.read(p)[1] for p in patches.glob('*.patch')}}
        self.manifest={'schema':1,'kind':'anyps5_unpatched_hle_runtime','source_commit':self.prep['upstreamCommit'],
            'contains_game_data':False,'runtime_verified':False,'build_provenance':self.provenance}
        scoped=patch.object(a,'ROOT',root);scoped.start();self.addCleanup(scoped.stop)
    def check(self):return a.coverage(self.manifest,self.provenance,self.prep,helper,self.log)
    def test_actual_case_mapping_not_target_suffix(self):self.assertEqual(self.check()['windows_compiler_once'],'compiler_once_tests')
    def test_stale_five_target_build_refused(self):
        self.provenance['additional_host_tests_passed']=self.prep['additionalTestTargets'][:-1]
        with self.assertRaisesRegex(ValueError,'six selected'):self.check()
    def test_missing_registered_case_refused(self):
        del self.provenance['host_test_case_results']['windows_compiler_once']
        with self.assertRaisesRegex(ValueError,'Every selected'):self.check()
    def test_skipped_read_failure_not_promoted(self):
        self.provenance['host_test_cases_skipped']=['savedata_memory_growth_read_failure']
        self.provenance['host_test_case_results']['savedata_memory_growth_read_failure']['status']='skipped'
        with self.assertRaisesRegex(ValueError,'Every selected'):self.check()
    def test_zip_provenance_not_external_record(self):
        self.manifest['build_provenance']=copy.deepcopy(self.provenance)
        self.manifest['build_provenance']['patches'].clear()
        with self.assertRaisesRegex(ValueError,'Embedded/external'):self.check()
    def test_cpu_result_not_gameplay_claim(self):
        self.provenance['device_or_gameplay_verified']=True
        with self.assertRaisesRegex(ValueError,'CPU provenance'):self.check()

if __name__=='__main__':unittest.main()
