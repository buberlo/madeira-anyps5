#!/usr/bin/env python3
"""Replay the existing 14+14 ARM64 LoopTop controls and seven negative mutations.

Only temporary/fresh local outputs are written. No FEX DLL build, Wine, device,
signing, installation or runtime/gameplay qualification is performed.
"""
import argparse
from pathlib import Path
import difflib
import hashlib
import json
import os
import shlex
import signal
import subprocess
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'tools/checks/fex_loop_top'
ORIGINAL_SHA = '124095b22a2f234b16d01af8fce93149e73b91c0dc377c6dda42026393f14e99'
PROPOSED_SHA = '3ae7c7aa0411e425f3ca6565efb25bdce81b0747b531d2017ac2b05bc96a1561'
def need(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    p = Path(path)
    need(p.is_file(), 'Missing input: ' + str(p))
    h = hashlib.sha256()
    with p.open('rb') as f:
        for data in iter(lambda: f.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()


def put(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def function(source, name):
    start = source.index('static ')
    del start
    match = source.index(name + '(')
    start = source.rfind('\n', 0, match) + 1
    opening = source.index('{', match)
    depth = 1
    end = opening + 1
    while depth:
        need(end < len(source), 'Unterminated production helper')
        if source[end] == '{':
            depth += 1
        elif source[end] == '}':
            depth -= 1
        end += 1
    return source[start:end] + '\n'


def harness(source):
    parts = [function(source, name) for name in (
        'ReconstructThreadRegisters', 'ReconstructThreadState') if name + '(' in source]
    parts.append(function(source, 'StoreStateToPackedECContext'))
    rethrow = function(source, 'RethrowGuestException')
    prefix = rethrow[:rethrow.index('  ARM64_NT_CONTEXT GuestContext')]
    prefix = prefix.replace('static void RethrowGuestException', 'static void ReconstructBeforePacking', 1)
    # Fault is unused only because the harness deliberately stops before dispatch.
    prefix = prefix.replace('  auto& Fault = Thread->CurrentFrame->SynchronousFaultData;\n', '')
    parts.append(prefix + '}\n')
    return '#include "native-adapter.hpp"\n' + '\n'.join(parts) + (HERE / 'native-cases.cpp').read_text()


def command(argv, stage, name, expected=0):
    log = stage / (name + '.log')
    child = None
    code = None
    env = {k: v for k, v in os.environ.items() if not k.startswith(('DYLD_', 'LD_')) and k not in {
        'GCC_EXEC_PREFIX', 'COMPILER_PATH', 'LIBRARY_PATH', 'CPATH', 'C_INCLUDE_PATH', 'CPLUS_INCLUDE_PATH'}}
    try:
        with log.open('xb') as out:
            child = subprocess.Popen([str(a) for a in argv], cwd=ROOT, env=env,
                                     stdout=out, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = child.wait(timeout=60)
            except BaseException:
                if child.poll() is None:
                    try:
                        need(os.getpgid(child.pid) == child.pid, 'Foreign compiler group')
                        os.killpg(child.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    child.wait(timeout=10)
                raise
    finally:
        row = dict(argv=[str(a) for a in argv], exitCode=code, logSha256=sha(log),
                   childReaped=child is not None and child.poll() is not None)
        put(stage / (name + '.command.json'), row)
    need(code == expected, 'Unexpected actual command exit: ' + name)
    need(log.stat().st_size <= 4 * 1024 * 1024, 'Diagnostic exceeds local bound')
    return row


def validated_source(source_path, patch_path):
    source_path, patch_path = Path(source_path).resolve(), Path(patch_path).resolve()
    need(sha(source_path) == PROPOSED_SHA, 'Exact qualified LoopTop source required')
    proposed = source_path.read_text()
    with tempfile.TemporaryDirectory(prefix='fex-loop-top-source-') as directory:
        scratch = Path(directory)
        path = scratch / 'Source/Windows/ARM64EC/Module.cpp'
        path.parent.mkdir(parents=True)
        path.write_text(proposed)
        result = subprocess.run(['git', 'apply', '--reverse', str(patch_path)], cwd=scratch,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        need(result.returncode == 0, 'Exact single-source patch must reverse cleanly')
        original = path.read_text()
        need(sha(path) == ORIGINAL_SHA, 'Exact pre-0004 source required')
    diff = ''.join(difflib.unified_diff(original.splitlines(True), proposed.splitlines(True),
        fromfile='a/Source/Windows/ARM64EC/Module.cpp', tofile='b/Source/Windows/ARM64EC/Module.cpp'))
    expected = 'diff --git a/Source/Windows/ARM64EC/Module.cpp b/Source/Windows/ARM64EC/Module.cpp\n' + diff
    need(patch_path.read_text() == expected, 'Patch must describe only the exact qualified source')
    old_registers = function(original, 'ReconstructThreadState').replace('ReconstructThreadState', 'ReconstructThreadRegisters', 1)
    old_registers = old_registers.replace('  State.rip = CTX->RestoreRIPFromHostPC(Thread, Context.Pc);\n\n', '', 1)
    need(old_registers == function(proposed, 'ReconstructThreadRegisters'), 'Original register spill body differs')
    need(function(original, 'StoreStateToPackedECContext') == function(proposed, 'StoreStateToPackedECContext'), 'Packed context body differs')
    need(function(original, 'ResetToConsistentStateImpl') == function(proposed, 'ResetToConsistentStateImpl'), 'Reset path differs')
    return original, proposed

def run(source_path, patch_path, output=None, source_only=False):
    original, proposed = validated_source(source_path, patch_path)
    if source_only:
        print(json.dumps({'status':'exact_loop_top_patch_and_source_verified_no_native_execution',
            'candidateSha256':PROPOSED_SHA,'originalSha256':ORIGINAL_SHA,'deviceActions':False,
            'canonicalChanged':False,'nativeExecuted':False}))
        return 0
    need(os.uname().machine == 'arm64', 'Native tests require an ARM64 Mac')
    stage = Path(output).resolve() if output else ROOT / 'build' / ('fex-loop-top-controls-' + uuid.uuid4().hex[:12])
    need(not stage.exists(), 'Fresh unique output required')
    stage.mkdir(parents=True)
    native_cxx = Path('/Library/Developer/CommandLineTools/usr/bin/clang++')
    sdk = Path('/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk').resolve()
    need((sdk / 'usr/include/c++/v1/array').is_file(), 'Native C++ SDK headers unavailable')
    inputs = {str(Path(p).resolve()):sha(p) for p in [source_path,patch_path,__file__,native_cxx,
        HERE/'native-adapter.hpp',HERE/'native-cases.cpp',HERE/'native-entry.S']}
    commands = []
    body = harness(proposed)
    asm_obj = stage / 'native-entry.o'
    commands.append(command([native_cxx, '-c', HERE / 'native-entry.S', '-o', asm_obj], stage, 'native-assembly'))
    def native_variant(name, source, fixed=True, ios=True, expected=0):
        cpp = stage / (name + '.cpp')
        cpp.write_text(source)
        obj, exe = stage / (name + '.o'), stage / name
        argv = [native_cxx, '-std=c++20', '-O2', '-Wall', '-Wextra', '-Wno-unused-parameter', '-isysroot', sdk, '-I', HERE]
        if fixed:
            argv.append('-DEXPECT_IOS_FIX')
        if ios:
            argv.append('-DFEX_IOS_HOST')
        argv += ['-MD', '-MF', stage / (name + '.d'), '-c', cpp, '-o', obj]
        commands.append(command(argv, stage, name + '-compile'))
        commands.append(command([native_cxx, '-isysroot', sdk, obj, asm_obj, '-o', exe], stage, name + '-link'))
        row = command([exe], stage, name + '-execute', expected=expected)
        commands.append(row)
        output = (stage / (name + '-execute.log')).read_text()
        if expected == 0:
            need(output.count('NATIVE_LOOP_TOP_CONTROLS=14 ') == 1, 'Native control summary missing')
        else:
            need(output.count('ASSERT: ') == 1, 'Negative mutation did not fail a concrete assertion')

    native_variant('candidate', body)
    native_variant('non-ios', body, fixed=False, ios=False)
    native_variant('original', harness(original), expected=1)
    mutants = {
        'no-live-rsp': ('State.gregs[i] = Context.X[Config.SRAGPRMapping[i]];', 'if (i != 4) State.gregs[i] = Context.X[Config.SRAGPRMapping[i]];'),
        'no-live-rcx': ('State.gregs[i] = Context.X[Config.SRAGPRMapping[i]];', 'if (i != 1) State.gregs[i] = Context.X[Config.SRAGPRMapping[i]];'),
        'broader-dispatcher': ('Context.Pc == Thread->CurrentFrame->Pointers.DispatcherLoopTop', 'IsDispatcherAddress(Context.Pc)'),
        'any-exception': ('Rec.ExceptionCode == 0xe0425355u && ', ''),
        'lost-state-rip': ('    ReconstructThreadRegisters(Thread, Context);\n  }\n#endif', '    ReconstructThreadState(Thread, Context);\n  }\n#endif'),
        'no-live-vector': ('memcpy(State.xmm.sse.data[i], &Context.V[Config.SRAFPRMapping[i]], sizeof(__uint128_t));', '(void)i;'),
        'no-live-flags': ('CTX->ReconstructCompactedEFLAGS(Thread, true, Context.X, Context.Cpsr)', 'CTX->ReconstructCompactedEFLAGS(Thread, false, nullptr, 0)'),
    }
    for name, (needle, replacement) in mutants.items():
        need(body.count(needle) == 1, 'Mutation must alter exactly one extracted production operation')
        native_variant('mutant-' + name, body.replace(needle, replacement, 1), expected=1)
    deps = {}
    for depfile in stage.glob('*.d'):
        paths = shlex.split(depfile.read_text().split(':', 1)[1].replace('\\\n', ''))
        for name in paths:
            path = Path(name)
            if not path.is_absolute():
                path = ROOT / path
            path = path.resolve()
            deps[str(path)] = sha(path)
    for path,digest in inputs.items():
        need(sha(path) == digest, 'Source/fixture/compiler input changed during native tests')
    for path,digest in deps.items():
        need(sha(path) == digest, 'Actual native dependency changed')
    outputs = {str(p):sha(p) for p in stage.iterdir() if p.is_file()}
    put(stage/'receipt.json', dict(schema=1,status='exact_loop_top_native_controls_pass_not_runtime_qualification',
        candidateSha256=PROPOSED_SHA,originalSha256=ORIGINAL_SHA,nativeControls=14,nonIosControls=14,
        originalFailsLiveRsp=True,effectiveMutationsDetected=list(mutants),
        actualNativeArm64AssemblyExecuted=True,inputs=inputs,actualCompileDependencies=deps,
        commands=commands,outputs=outputs,canonicalChanged=False,fullDllBuilt=False,
        wineExecuted=False,deviceActions=False,full803Qualified=False,cpuEightQualified=False,
        gameplayQualified=False,nativeCallBoundaryFlagsPreservationQualified=False))
    print(json.dumps({'output':str(stage),'receiptSha256':sha(stage/'receipt.json'),'deviceActions':False}))
    return 0

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT/'upstreams/FEX/Source/Windows/ARM64EC/Module.cpp')
    parser.add_argument('--patch',type=Path,default=ROOT/'patches/fex/0004-ios-loop-top-live-state-spill.patch')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--source-only',action='store_true')
    args=parser.parse_args()
    raise SystemExit(run(args.source,args.patch,args.output,args.source_only))
