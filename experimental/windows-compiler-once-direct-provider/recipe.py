"""Root-only filesystem preparation; emit exact argv, never launch tools/Wine."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import stat
import struct

HERE = Path(__file__).resolve().parent
FULL = HERE.parent
ROOT = FULL.parents[1]
BUILD = FULL / 'winlibs-build-attempt2'
SOURCE = FULL / 'qualification-source'
TOOLS = ROOT / 'build/toolchains/winlibs/mingw64'
BASE = FULL / 'unwind-first-miss-diagnostic-proposal/recipe.json'
PRIVATE = 'APS5NativeCompilerOnce_nid_no_patch'
PE_READER = ROOT / 'tools/runtime-probes/pe_image.py'
SOURCES = ('compiler_once.hpp', 'provider.cpp', 'caller_bridge.cpp',
           'cross_module.cpp', 'CompilerOnceTests.cpp', 'recipe.py',
           'test_recipe.py', 'test_direct.py', 'README.md')
CASES = ('private_iat_cross_module_identity','retry_destructors_passive',
    'nested_distinct_flags','concurrent_single_success','concurrent_exception_retry',
    'independent_flag_overlap','actual_core_spurious_failure_reset','four_byte_abi_invalid_done')
ORIGINAL_MARKER = 'Own Windows exceptions: typed catch, base catch, catch-all, rethrow, destructors, cross DLL passed'


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def identity(path):
    s = Path(path).lstat()
    if not stat.S_ISREG(s.st_mode):
        raise ValueError('Ordinary provider required: ' + str(path))
    return [s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_size, s.st_mtime_ns, s.st_ctime_ns]


def row(path):
    before = identity(path)
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda: f.read(1024**2), b''): h.update(part)
    if identity(path) != before: raise ValueError('Input changed: ' + str(path))
    return {'sha256': h.hexdigest(), 'stableStat': before}


def replay(values):
    for name, expected in values.items():
        if row(Path(name)) != expected: raise ValueError('Pinned provider changed: ' + name)


def pe(path):
    spec = importlib.util.spec_from_file_location('once_pe', PE_READER)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module.PEImage(path)


def export_contract(image):
    names, ordinals = image.exports()
    rva, _ = image.directory(0)
    base, count, _, functions, _, _ = image.unpack('IIIIII', image.offset(rva, 40) + 16)
    header = image.unpack('I', 0x3c)[0]
    count_sections = image.unpack('H', header + 6)[0]
    sections = header + 24 + image.unpack('H', header + 20)[0]
    result = {}
    for name, ordinal in names.items():
        if ordinals[ordinal] is not None: raise ValueError('No forwarded baseline export allowed')
        address = image.unpack('I', image.offset(functions + 4*(ordinal-base), 4))[0]
        matches = []
        for i in range(count_sections):
            position = sections + 40*i
            virtual, start, raw = image.unpack('III', position + 8)
            if start <= address < start + max(virtual, raw):
                matches.append(bool(image.unpack('I', position + 36)[0] & 0x20000000))
        if len(matches) != 1: raise ValueError('Ambiguous export section')
        result[name] = {'ordinal': ordinal, 'data': not matches[0]}
    if len(result) != count or len(result) != len(ordinals):
        raise ValueError('Named ordinary exact baseline export set required')
    return result


def export_def(contract):
    if PRIVATE in contract or len(contract) != 1061 or \
            {v['ordinal'] for v in contract.values()} != set(range(1,1062)) or \
            any(type(v['ordinal']) is not int or type(v['data']) is not bool for v in contract.values()):
        raise ValueError('Exact current baseline 1061 exports required')
    lines = ['LIBRARY libc.prx', 'EXPORTS']
    for name, value in sorted(contract.items(), key=lambda pair: pair[1]['ordinal']):
        if not name or any(c in name for c in '\"\r\n\\'):
            raise ValueError('Unsafe DEF export spelling')
        lines.append('  "' + name + '" @' + str(value['ordinal']) + (' DATA' if value['data'] else ''))
    lines.append('  ' + PRIVATE + ' @' + str(max(v['ordinal'] for v in contract.values()) + 1))
    return '\n'.join(lines) + '\n'


def validate_imports(imports):
    if len({name.lower() for name in imports}) != len(imports):
        raise ValueError('Duplicate DLL import aliases')
    normalized = {name.lower(): values for name, values in imports.items()}
    if PRIVATE not in normalized.get('libc.prx', []):
        raise ValueError('Private libc once import required')
    if any('pthread_once' in values for values in normalized.values()):
        raise ValueError('Native pthread_once import remains in owned caller')


def validate_runtime_result(result, focused):
    if type(result.get('exitCode')) is not int or result['exitCode']!=0 or \
            any(result.get(key) is not True for key in ('captureComplete','childJoined','ownedGroupAbsent')):
        raise ValueError('Actual zero exit, capture and owned closure required')
    stdout=result.get('stdout'); stderr=result.get('stderr')
    if not isinstance(stdout,str) or not isinstance(stderr,str) or \
            any(len(stream.encode())>1024**2 for stream in (stdout,stderr)):
        raise ValueError('Bounded complete streams required')
    if 'COMPILER_ONCE_FAILED' in stdout+stderr: raise ValueError('Explicit fixture failure')
    if focused:
        rows=[line.removeprefix('COMPILER_ONCE_PASS ') for line in stdout.splitlines()
              if line.startswith('COMPILER_ONCE_PASS ')]
        if rows!=list(CASES) or stdout.splitlines().count('COMPILER_ONCE_COMPLETE cases=8 errors=0')!=1:
            raise ValueError('Eight exact ordered actual cases and one completion required')
    elif stdout.splitlines().count(ORIGINAL_MARKER)!=1:
        raise ValueError('Original complete fixture marker required')


def coff_symbols(path):
    """Read bounded ordinary AMD64 COFF symbols without executing native tools."""
    data=Path(path).read_bytes()
    if len(data)>16*1024**2 or len(data)<20: raise ValueError('Bounded COFF object required')
    machine,_,_,offset,count,optional,_=struct.unpack_from('<HHIIIHH',data)
    end=offset+count*18
    if machine!=0x8664 or optional!=0 or not offset or end+4>len(data):
        raise ValueError('Ordinary AMD64 COFF symbol table required')
    length=struct.unpack_from('<I',data,end)[0]
    if length<4 or end+length>len(data): raise ValueError('Complete COFF string table')
    result={}; i=0
    while i<count:
        pos=offset+i*18; raw=data[pos:pos+8]
        value,section,_,storage,aux=struct.unpack_from('<IhHBB',data,pos+8)
        if i+aux>=count: raise ValueError('Complete COFF auxiliary entries')
        if raw[:4]==b'\0'*4:
            start=struct.unpack_from('<I',raw,4)[0]
            if not 4<=start<length: raise ValueError('COFF symbol name offset')
            stop=data.find(b'\0',end+start,end+length)
            if stop<0: raise ValueError('Terminated COFF symbol name')
            name=data[end+start:stop].decode('ascii')
        else: name=raw.rstrip(b'\0').decode('ascii')
        if storage==2:
            if name in result: raise ValueError('Duplicate external COFF symbol')
            result[name]={'section':section,'value':value}
        i+=1+aux
    return result


def require_bridge_symbols(local, imported, focused):
    for path in (local,imported):
        symbols=coff_symbols(path)
        if any(symbols.get(name,{}).get('section',0)<=0 for name in ('pthread_once','__imp_pthread_once')):
            raise ValueError('Both direct function and IAT slot must be owned definitions')
    symbols=coff_symbols(focused)
    if any(symbols.get(name)!={'section':0,'value':0} for name in ('pthread_once','__imp_pthread_once')):
        raise ValueError('Fresh fixture must reference both actual direct and IAT symbols')


def retained_direct_once_callers(objects):
    callers=[str(path.relative_to(BUILD)) for path in objects
        if coff_symbols(path).get('pthread_once')=={'section':0,'value':0}]
    expected=['core/libs/CMakeFiles/libc.dir/prx/libc/src/ApplicationHeap.cpp.obj']
    if callers!=expected: raise ValueError('Exact observed retained direct once caller required')
    return callers


def qualify(out, plan):
    require_bridge_symbols(out/'bridge-local.obj',out/'bridge-import.obj',out/'focused.obj')
    baseline = plan['baselineExports']
    actual = export_contract(pe(out / 'runtime/libc.prx'))
    new = actual.pop(PRIVATE, None)
    if actual != baseline or new != {'ordinal': 1062, 'data': False}:
        raise ValueError('Exact baseline names/ordinals/data and one private export required')
    if any('pthread_once' in values for values in pe(out/'runtime/libc.prx').imports().values()):
        raise ValueError('Native pthread_once import remains in owned libc')
    for name in ('windows_exception_tests.exe', 'compiler_once_tests.exe', 'compiler_once_cross.dll'):
        validate_imports(pe(out / 'runtime' / name).imports())
    for name in ('libc.prx', 'windows_exception_tests.exe', 'compiler_once_tests.exe', 'compiler_once_cross.dll'):
        data = (out / 'runtime' / name).read_bytes()
        header = int.from_bytes(data[0x3c:0x40], 'little')
        optional = header + 24
        count = int.from_bytes(data[header+6:header+8], 'little')
        offset = optional + int.from_bytes(data[header+20:header+22], 'little')
        sections = {data[offset+i*40:offset+i*40+8].rstrip(b'\0') for i in range(count)}
        if b'.ehfram' not in sections or b'.eh_fram' in sections:
            raise ValueError('Custom-unwinder frame section required: ' + name)
    return {'staticNamedExportAndOwnedCallerImportsVerified': True,
            'directAndIatFreshObjectSymbolsVerified': True,
            'runtimeResolvedIatIdentityVerified': False, 'runtimeTestsPassed': False}


def block(lines, prefix):
    i = next(i for i, line in enumerate(lines) if line.startswith(prefix))
    end = next(j for j in range(i+1,len(lines)) if not lines[j].startswith('  '))
    return lines[i:end]


def windows(path): return 'Z:' + str(path).replace('/', '\\')


def output_path(out, fresh):
    if not out.is_absolute() or not out.is_relative_to(FULL) or '..' in out.parts:
        raise ValueError('Absolute isolated output required')
    if out.parent.resolve()!=out.parent or (fresh and out.exists()) or (not fresh and out.resolve()!=out):
        raise ValueError('Unlinked fresh/retained own output required')
    return out


def commands(out, objects, libraries):
    compiler = windows(TOOLS / 'bin/g++.exe')
    objcopy = windows(TOOLS / 'bin/objcopy.exe')
    common = ['-O3', '-DNDEBUG', '-std=gnu++20', '-fno-asynchronous-unwind-tables',
              '-I' + windows(HERE), '-I' + windows(SOURCE / 'core/libs')]
    result = []
    def compile(name, source, extra=()):
        result.append({'name': 'compile-' + name, 'timeoutSeconds': 180,
            'windowsArgv': [compiler, *common, *extra, '-MD', '-MF', windows(out/(name+'.d')),
                '-o', windows(out/(name+'.obj')), '-c', windows(source)]})
    compile('provider', HERE / 'provider.cpp')
    compile('bridge-local', HERE / 'caller_bridge.cpp', ['-DAPS5_ONCE_PROVIDER_LOCAL=1'])
    compile('bridge-import', HERE / 'caller_bridge.cpp')
    compile('cross', HERE / 'cross_module.cpp')
    compile('focused', HERE / 'CompilerOnceTests.cpp')
    compile('original', SOURCE / 'core/libs/tests/WindowsExceptions.cpp', ['-DAPS5_ENABLE_TIMING_LOG=0'])
    result.append({'name':'link-libc','timeoutSeconds':60,'windowsArgv':[compiler,
        '-O3','-DNDEBUG','-shared','-Wl,--exclude-all-symbols',
        '-o',windows(out/'runtime/libc.prx'),
        '-Wl,--out-implib,'+windows(out/'liblibc.dll.a'),
        '-Wl,--major-image-version,0,--minor-image-version,0',
        *[windows(p) for p in objects],windows(out/'provider.obj'),windows(out/'bridge-local.obj'),
        windows(out/'libc-preserved-exports.def'),*libraries,'-lsynchronization']})
    for name, obj, dll in (('compiler_once_cross.dll','cross',True),
                           ('compiler_once_tests.exe','focused',False),
                           ('windows_exception_tests.exe','original',False)):
        result.append({'name':'link-'+name,'timeoutSeconds':60,'windowsArgv':[compiler,
            '-O3','-DNDEBUG', *(['-shared','-Wl,--exclude-all-symbols'] if dll else []),
            '-o',windows(out/'runtime'/name),windows(out/(obj+'.obj')),
            windows(out/'bridge-import.obj'), windows(out/'liblibc.dll.a'),
            '-lkernel32','-luser32','-lgdi32','-lwinspool','-lshell32','-lole32',
            '-loleaut32','-luuid','-lcomdlg32','-ladvapi32']})
    for name in ('libc.prx','compiler_once_cross.dll','compiler_once_tests.exe','windows_exception_tests.exe'):
        result.append({'name':'rename-'+name,'timeoutSeconds':15,
            'windowsArgv':[objcopy,'--rename-section','.eh_frame=.ehfram',windows(out/'runtime'/name)]})
    environment = {'APS5_GUEST_ARENA_LAZY':'1','APS5_GUEST_ARENA_BASE':'0x200000000',
                   'APS5_GUEST_ARENA_SIZE':'0x100000000','APS5_GUEST_ARENA_CHUNK':'0x10000000'}
    for name in ('compiler_once_tests.exe','windows_exception_tests.exe'):
        result.append({'name':'run-'+name,'timeoutSeconds':60,'cwd':str(out/'runtime'),
            'extraEnvironment':environment,'windowsArgv':[windows(out/'runtime'/name),
                *([windows(out/'runtime/libc.prx'),windows(out/'runtime/compiler_once_cross.dll')]
                  if name=='compiler_once_tests.exe' else [])]})
    return result


def prepare(out, expected_review):
    output_path(out,True)
    review_path = HERE / 'source-review.json'
    if row(review_path)['sha256'] != expected_review: raise ValueError('Exact reviewed source required')
    review = json.loads(review_path.read_text()); replay(review['inputs'])
    base = json.loads(BASE.read_text()); replay(base['inputs'])
    lines=(BUILD/'build.ninja').read_text().splitlines()
    link=block(lines,'build core/libs/libs/unpatched/libc.prx core/libs/libs/implib/liblibc.dll.a:')
    paths=link[0].split(': CXX_SHARED_LIBRARY_LINKER__libc_Release ')[1].split()
    if len(paths)!=46 or paths[-1]!='core/libs/CMakeFiles/libc.dir/prx/libc/src/exception/Exports.cpp.obj':
        raise ValueError('Exact actual 46-object libc order required')
    objects=[BUILD / p for p in paths]
    direct_callers=retained_direct_once_callers(objects)
    libraries=dict(line.strip().split(' = ',1) for line in link[1:])['LINK_LIBRARIES'].split()
    # Inherited recorded dependencies/objects/tools/default libraries are replayed
    # by bytes; all possible new source headers are added for fresh .d admission.
    inputs=dict(base['inputs']); inputs.update(review['inputs'])
    paths=set(objects)|{BASE,PE_READER,SOURCE/'core/libs/tests/WindowsExceptions.cpp',
        SOURCE/'core/libs/prx/libkernel/Pthread/Posix/Once.cpp',
        TOOLS/'x86_64-w64-mingw32/lib/libsynchronization.a'}
    for directory in (TOOLS/'include', TOOLS/'x86_64-w64-mingw32/include'):
        paths.update(p for p in directory.rglob('*') if p.is_file())
    for path in paths: inputs[str(path)]=row(path)
    baseline=export_contract(pe(BUILD/'core/libs/libs/unpatched/libc.prx'))
    if len(baseline)!=1061: raise ValueError('Actual baseline export set')
    replay(inputs)
    out.mkdir(); (out/'runtime').mkdir()
    (out/'libc-preserved-exports.def').write_text(export_def(baseline))
    for name in ('libstdc++-6.dll','libgcc_s_seh-1.dll','libwinpthread-1.dll'):
        source=BUILD/'tests'/name; shutil.copyfile(source,out/'runtime'/name)
        if row(out/'runtime'/name)['sha256']!=inputs[str(source)]['sha256']:
            raise ValueError('Exact runtime copy required')
    plan={'schema':1,'status':'inert_compiler_once_candidate_not_executed',
        'sourceReviewSha256':expected_review,'output':str(out),'inputs':inputs,
        'baselineExports':baseline,'commands':commands(out,objects,libraries),
        'wine':base['wine'],'wineserver':base['wineserver'],'ownedPrefix':str(out/'wine-prefix'),
        'rootExecutionRequirements':{'initialAndLiveFreeBytesMinimum':2*1024**3,
            'outputBytesExcludingPrefixMaximum':64*1024**2,'ownedPrefixBytesMaximum':512*1024**2,
            'capturedStreamBytesMaximum':1024**2,
            'freshPrefixAndOwnedRuntimeOnly':True,'allActualCompileDependenciesMustMatchInputs':True,
            'staticQualificationBeforeRuntime':True,'inputReplayBeforeAndAfter':True,
            'everyDirectChildAndOwnedGroupJoined':True,'gracefulWineserverWaitThenKillOnlyIfTimedOut':True,
            'prefixTerminalJoinRequired':True},
        'originalWindowsExceptionsSourceUnchanged':True,'guest16ByteOnceSourceUnchanged':True,
        'retainedDirectOnceCallers':direct_callers,'directAndIatRouteRequired':True,
        'expectedFocusedOrderedCases':list(CASES),'expectedOriginalMarker':ORIGINAL_MARKER,
        'nativeDllInternalOnceCallsRerouted':False,'posixCancellationQualified':False,
        'runtimeQualified':False,'fullHleQualified':False}
    (out/'plan.json').write_bytes(canonical(plan)); replay(inputs)
    return plan


def main():
    p=argparse.ArgumentParser(); p.add_argument('--prepare',action='store_true')
    p.add_argument('--qualify-static',action='store_true'); p.add_argument('--output',type=Path,required=True)
    p.add_argument('--source-review-sha256'); p.add_argument('--plan-sha256'); a=p.parse_args()
    if a.prepare == a.qualify_static: p.error('Exactly one filesystem-only mode required')
    if a.prepare:
        if not re.fullmatch('[0-9a-f]{64}',a.source_review_sha256 or ''): p.error('Exact source review SHA required')
        prepare(a.output,a.source_review_sha256)
    else:
        output_path(a.output,False)
        if not re.fullmatch('[0-9a-f]{64}',a.plan_sha256 or '') or \
                row(a.output/'plan.json')['sha256']!=a.plan_sha256:
            p.error('Exact unchanged plan SHA required')
        plan=json.loads((a.output/'plan.json').read_text()); replay(plan['inputs'])
        if plan['output']!=str(a.output): raise ValueError('Plan output binding')
        proof=qualify(a.output,plan)
        (a.output/'static-qualification.json').write_bytes(canonical(proof)); replay(plan['inputs'])
if __name__=='__main__': main()
