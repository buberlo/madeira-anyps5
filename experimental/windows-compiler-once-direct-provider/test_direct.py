"""Actual COFF diagnosis and small pure admission controls; no native tools."""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
HERE=Path(__file__).resolve().parent
OLD=HERE.with_name('windows-compiler-once-provider-proposal')
spec=importlib.util.spec_from_file_location('direct_recipe',HERE/'recipe.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def object_bytes(symbols):
    strings=bytearray(b'\0'*4); table=bytearray()
    for name,section in symbols:
        encoded=name.encode('ascii')
        if len(encoded)<=8: word=encoded.ljust(8,b'\0')
        else:
            word=struct.pack('<II',0,len(strings)); strings+=encoded+b'\0'
        table+=word+struct.pack('<IhHBB',0,section,0,2,0)
    struct.pack_into('<I',strings,0,len(strings))
    return struct.pack('<HHIIIHH',0x8664,0,0,20,len(symbols),0,0)+table+strings

class DirectAdmission(unittest.TestCase):
    def test_actual_retained_direct_caller(self):
        lines=(m.BUILD/'build.ninja').read_text().splitlines()
        link=m.block(lines,'build core/libs/libs/unpatched/libc.prx core/libs/libs/implib/liblibc.dll.a:')
        paths=link[0].split(': CXX_SHARED_LIBRARY_LINKER__libc_Release ')[1].split()
        self.assertEqual(len(paths),46)
        self.assertEqual(m.retained_direct_once_callers([m.BUILD/p for p in paths]),
            ['core/libs/CMakeFiles/libc.dir/prx/libc/src/ApplicationHeap.cpp.obj'])
    def test_both_routes_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'local'; b=Path(d)/'import'; f=Path(d)/'focused'
            a.write_bytes(object_bytes([('pthread_once',1),('__imp_pthread_once',2)]))
            b.write_bytes(a.read_bytes()); f.write_bytes(object_bytes([('pthread_once',0),('__imp_pthread_once',0)]))
            m.require_bridge_symbols(a,b,f)
    def test_missing_direct_definition_refused(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a'; f=Path(d)/'f'
            a.write_bytes(object_bytes([('__imp_pthread_once',2)])); f.write_bytes(object_bytes([('pthread_once',0),('__imp_pthread_once',0)]))
            with self.assertRaises(ValueError): m.require_bridge_symbols(a,a,f)
    def test_missing_direct_fixture_reference_refused(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a'; f=Path(d)/'f'
            a.write_bytes(object_bytes([('pthread_once',1),('__imp_pthread_once',2)])); f.write_bytes(object_bytes([('__imp_pthread_once',0)]))
            with self.assertRaises(ValueError): m.require_bridge_symbols(a,a,f)
    def test_incomplete_coff_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'p'; p.write_bytes(object_bytes([('pthread_once',1)])[:-1])
            with self.assertRaises(ValueError): m.coff_symbols(p)
    def test_core_provider_cross_original_unchanged(self):
        for name in ('compiler_once.hpp','provider.cpp','cross_module.cpp'):
            self.assertEqual((HERE/name).read_bytes(),(OLD/name).read_bytes())
        old=__import__('json').loads((OLD/'source-review.json').read_text())
        path=m.SOURCE/'core/libs/tests/WindowsExceptions.cpp'
        self.assertEqual(m.row(path),old['inputs'][str(path)])
    def test_no_duplicate_definition_link_override(self):
        cmds=m.commands(m.FULL/'fake-direct-output',[],[])
        self.assertFalse(any('allow-multiple-definition' in arg for c in cmds for arg in c['windowsArgv']))
    def test_force_direct_reference_and_passive_iat_source(self):
        text=(HERE/'CompilerOnceTests.cpp').read_text()
        self.assertIn('__asm__("pthread_once")',text)
        self.assertIn('direct_native_abi();',text)
        self.assertIn('direct throw reset/destructor',text)
        self.assertIn('direct/IAT same flag passive',text)

if __name__=='__main__': unittest.main()
