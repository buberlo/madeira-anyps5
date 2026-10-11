"""Read-only Ninja dependency extraction and fixed diagnostic recipe emitter.

This writes only recipe/source proof metadata beside itself. No build or Wine.
"""
import hashlib
import json
from pathlib import Path
import re
import stat
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FULL = HERE.parent
BUILD = FULL / 'winlibs-build-attempt2'
SOURCE = FULL / 'qualification-source'
TOOL = ROOT / 'build/toolchains/winlibs/mingw64'
OUT = FULL / 'unwind-first-miss-diagnostic-build'
WINE = ROOT / 'build/toolchains/wine-local/Wine Stable.app/Contents/Resources/wine/bin/wine'
SERVER = WINE.with_name('wineserver')
NINJA = Path('/opt/homebrew/bin/ninja')
EXPECTED = 'f06af55ef2c58b24ebfa7cdbc19cf3ba26c7ca3e1c7dbd461d6154fec4b19d6c'


def win(path):
    return 'Z:' + str(path).replace('/', '\\')


def fp(path):
    s = path.lstat()
    if not stat.S_ISREG(s.st_mode):
        raise ValueError('Ordinary provider required: ' + str(path))
    return [s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_size, s.st_mtime_ns, s.st_ctime_ns]


def row(path):
    before = fp(path)
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    if fp(path) != before:
        raise ValueError('Drift during exact input read: ' + str(path))
    return {'sha256': h.hexdigest(), 'stableStat': before}


def block(lines, prefix):
    i = next(i for i, line in enumerate(lines) if line.startswith(prefix))
    end = next(j for j in range(i + 1, len(lines)) if not lines[j].startswith('  '))
    return lines[i:end]


def main():
    lines = (BUILD / 'build.ninja').read_text().splitlines()
    link = block(lines, 'build core/libs/libs/unpatched/libc.prx core/libs/libs/implib/liblibc.dll.a:')
    objects = link[0].split(': CXX_SHARED_LIBRARY_LINKER__libc_Release ')[1].split()
    if len(objects) != 46 or objects[-1] != 'core/libs/CMakeFiles/libc.dir/prx/libc/src/exception/Exports.cpp.obj':
        raise ValueError('Exact current libc object order')
    compile_block = block(lines, 'build ' + objects[-1] + ':')
    expected_compile = {'DEFINES': '-DAPS5_ENABLE_TIMING_LOG=0 -Dlibc_EXPORTS',
                        'FLAGS': '-O3 -DNDEBUG -std=gnu++20 -fno-asynchronous-unwind-tables',
                        'INCLUDES': '-I' + 'Z:' + str(SOURCE / 'core/libs')}
    compile_vars = dict(line.strip().split(' = ', 1) for line in compile_block[1:])
    for key, expected in expected_compile.items():
        if compile_vars[key] != expected:
            raise ValueError('Actual retained compile flags differ: ' + key)
    link_vars = dict(line.strip().split(' = ', 1) for line in link[1:])
    if link_vars['LANGUAGE_COMPILE_FLAGS'] != '-O3 -DNDEBUG' or link_vars['LINK_FLAGS'] != '-shared':
        raise ValueError('Exact current libc link flags')
    deps = subprocess.run([str(NINJA), '-C', str(BUILD), '-t', 'deps', *objects],
                          capture_output=True, text=True, check=True)
    (HERE / 'retained-ninja-deps.txt').write_text(deps.stdout)
    paths = set()
    for line in deps.stdout.splitlines():
        if line.startswith('    Z:/'):
            paths.add(Path(line.strip()[2:]))
        elif line.startswith('    '):
            raise ValueError('Unrecognized native recorded dependency: ' + line)
    if not paths or not all(p.is_relative_to(ROOT) for p in paths):
        raise ValueError('Exact project-local retained object dependencies required')
    paths.update(BUILD / name for name in objects)
    paths.update({BUILD / 'build.ninja', BUILD / 'CMakeFiles/rules.ninja',
                  BUILD / '.ninja_deps', BUILD / 'CMakeCache.txt',
                  HERE / 'retained-ninja-deps.txt', HERE / 'prepare.py', HERE / 'make-recipe.py',
                  HERE / 'source-review.json', FULL / 'replacement-stack-v4/provenance.json',
                  FULL / 'replacement-stack-v4/verification.json',
                  BUILD / 'test-windows_exception_tests.log'})
    # Exact current tool executables, their adjacent DLLs, and the compiler's
    # possible default/archive/startup inputs are held by bytes and identities.
    for name in ('g++.exe', 'as.exe', 'ld.exe', 'objcopy.exe'):
        paths.add(TOOL / 'bin' / name)
    paths.update((TOOL / 'bin').glob('*.dll'))
    gcc = TOOL / 'libexec/gcc/x86_64-w64-mingw32/15.2.0'
    paths.update({gcc / 'cc1plus.exe', gcc / 'collect2.exe'})
    for directory in (TOOL / 'lib/gcc/x86_64-w64-mingw32/15.2.0',
                      TOOL / 'x86_64-w64-mingw32/lib', TOOL / 'lib'):
        paths.update(directory.glob('*.a'))
        paths.update(directory.glob('*.o'))
        paths.update(directory.glob('*.specs'))
    paths.update({WINE, SERVER})
    copies = []
    exception = SOURCE / 'core/libs/prx/libc/src/exception'
    for source in sorted(exception.iterdir()):
        if source.name == 'Unwind.cpp':
            source = FULL / 'candidate/core/libs/prx/libc/src/exception/Unwind.cpp'
        if source.is_file():
            paths.add(source)
            copies.append({'source': str(source), 'relativeTarget': 'source/' + source.name})
    for name in ('windows_exception_tests.exe', 'libstdc++-6.dll', 'libgcc_s_seh-1.dll', 'libwinpthread-1.dll'):
        source = BUILD / 'tests' / name
        paths.add(source)
        copies.append({'source': str(source), 'relativeTarget': 'runtime/' + name})
    inputs = {str(p): row(p) for p in sorted(paths)}
    instrumented = FULL / 'candidate/core/libs/prx/libc/src/exception/Unwind.cpp'
    if inputs[str(instrumented)]['sha256'] != EXPECTED:
        raise ValueError('Held diagnostic source required')
    if row(exception / 'Unwind.cpp')['sha256'] != json.loads((HERE / 'source-review.json').read_text())['beforeSha256']:
        raise ValueError('Qualification/v4 source must remain before diagnostic')
    compiler = win(TOOL / 'bin/g++.exe')
    newobj = OUT / 'Exports.cpp.obj'
    compile_argv = [compiler, *compile_vars['DEFINES'].split(), '-I' + win(SOURCE / 'core/libs'),
        *compile_vars['FLAGS'].split(), '-MD', '-MT', win(newobj), '-MF', win(OUT / 'Exports.cpp.obj.d'),
        '-o', win(newobj), '-c', win(OUT / 'source/Exports.cpp')]
    link_argv = [compiler, '-O3', '-DNDEBUG', '-shared', '-o', win(OUT / 'runtime/libc.prx'),
        '-Wl,--out-implib,' + win(OUT / 'liblibc.dll.a'), '-Wl,--major-image-version,0,--minor-image-version,0',
        *[win(BUILD / name) for name in objects[:-1]], win(newobj), *link_vars['LINK_LIBRARIES'].split()]
    commands = [
        {'name': 'compile-exports', 'windowsArgv': compile_argv, 'timeoutSeconds': 180},
        {'name': 'link-libc', 'windowsArgv': link_argv, 'timeoutSeconds': 60},
        {'name': 'rename-eh-frame', 'windowsArgv': [win(TOOL / 'bin/objcopy.exe'), '--rename-section',
             '.eh_frame=.ehfram', win(OUT / 'runtime/libc.prx')], 'timeoutSeconds': 15},
        {'name': 'first-miss-trace', 'windowsArgv': [win(OUT / 'runtime/windows_exception_tests.exe')],
         'cwd': str(OUT / 'runtime'), 'timeoutSeconds': 15,
         'extraEnvironment': {'APS5_UNWIND_MISS_TRACE': '1', 'APS5_GUEST_ARENA_LAZY': '1',
             'APS5_GUEST_ARENA_BASE': '0x200000000', 'APS5_GUEST_ARENA_SIZE': '0x100000000',
             'APS5_GUEST_ARENA_CHUNK': '0x10000000'}}]
    recipe = {'schema': 1, 'status': 'inert_exact_current_objects_diagnostic_recipe_not_runtime_or_repair',
        'output': str(OUT), 'wine': str(WINE), 'wineserver': str(SERVER),
        'ownedPrefix': str(OUT / 'wine-prefix'), 'inputs': inputs, 'copies': copies,
        'reusedLibcObjects': [str(BUILD / name) for name in objects[:-1]],
        'replacedAmalgamationObject': str(BUILD / objects[-1]),
        'actualRetainedCompileRule': compile_block, 'actualRetainedLinkRule': link,
        'commands': commands, 'rootExecutionRequirements': {
           'allInputsHashAndSevenFieldStatBeforeAfter': True,
           'freshCopiedRuntimeHashBeforeAfter': True,
           'windowsPathIncludesOnlyOwnRuntimeAndPinnedCompilerBin': True,
           'initialAndLiveFreeBytesMinimum': 2 * 1024**3,
           'individualCapturedStreamBytesMaximum': 1024**2,
           'commandObjectsAndOutputBytesMaximum': 32 * 1024**2,
           'directChildAndOwnedProcessGroupJoinRequired': True,
           'gracefulWineServerWaitSeconds': 30, 'onlyTimeoutForceCloseThenWaitSeconds': 15,
           'finalWineServerJoinedExitZeroRequired': True,
           'noRuntimeResultAcceptanceOrRepairClaim': True},
        'ninjaDepsStatusNote': 'Native Ninja prints STALE for cross-platform mtime representation; recorded dependency names are used solely for exact current byte closure, not a freshness claim.',
        'commandsExecuted': False, 'deviceActions': False, 'canonicalSourceChanged': False}
    with (HERE / 'recipe.json').open('x') as f:
        json.dump(recipe, f, indent=2, sort_keys=True); f.write('\n')
    print(json.dumps({'inputs': len(inputs), 'inputBytes': sum(r['stableStat'][4] for r in inputs.values()),
                      'recipeSha256': row(HERE / 'recipe.json')['sha256'], 'reusedObjects': len(objects)-1,
                      'copies': len(copies), 'commandsExecuted': False}, sort_keys=True))


if __name__ == '__main__':
    main()
