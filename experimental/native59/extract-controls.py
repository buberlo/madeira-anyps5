#!/usr/bin/env python3
"""Extract actual opt-in patched production bodies. No compiler or device calls."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

HERE = Path(__file__).resolve().parent


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_checkpoint():
    manifest = json.loads((HERE / 'source-manifest.json').read_bytes())
    for name, digest in manifest['files'].items():
        path = HERE / name
        need(path.is_file() and not path.is_symlink() and sha(path) == digest,
             'Checkpoint source differs: ' + name)
    return manifest


def function(text, start):
    need(text.count(start) == 1, 'Unique production declaration: ' + start)
    pos = text.index(start)
    opening = text.index('{', pos)
    depth, at = 1, opening + 1
    # These hash-bound bodies have no unmatched braces in strings/comments.
    while depth:
        need(at < len(text), 'Complete production body')
        depth += (text[at] == '{') - (text[at] == '}')
        at += 1
    return text[pos:at] + '\n'


def section(text, start, end):
    need(text.count(start) == text.count(end) == 1, 'Unique production markers')
    return text.split(start, 1)[1].split(end, 1)[0]


def extract(root, output):
    manifest = verify_checkpoint()
    root, output = Path(root).resolve(), Path(output).absolute()
    need(not output.exists() and not output.is_symlink(), 'New exclusive controls output')
    for name, digest in manifest['expectedPatchedSources'].items():
        path = root / name
        need(path.is_file() and not path.is_symlink() and sha(path) == digest,
             'All experimental series must be applied together: ' + name)
    output.mkdir(parents=True)
    wine = root / 'upstreams/wine'
    fex = root / 'upstreams/FEX'
    madeira = root / 'upstreams/Madeira'
    wout, fout, oout = (output / name for name in ('wine', 'fex', 'owner'))
    for path in (wout, fout, oout):
        path.mkdir()
    for name in ('native-harness.c', 'ios_fex_critical_abi.h',
                 'ios_fex_critical_native.h', 'ios_fex_critical_server.h'):
        shutil.copyfile(HERE / 'controls/wine' / name, wout / name)
    text = (wine / 'server/thread.c').read_text()
    names = ('static inline int is_thread_suspended(',
             'static int ios_fex_exact_private_pending(',
             'static struct ios_fex_critical_facts ios_fex_thread_facts(',
             'static void ios_fex_clear_pending(', 'static void ios_fex_ack_context(',
             'static void ios_fex_publish_pending(', 'static void ios_fex_cancel_pending(',
             'static void ios_fex_record_suspend(', 'static int is_thread_wait_suspended(',
             'DECL_HANDLER(ios_fex_critical_scope)')
    (wout / 'production-server-bodies.inc').write_text('\n'.join(function(text, n) for n in names))
    module = (fex / 'Source/Windows/ARM64EC/Module.cpp').read_text()
    signal = (fex / 'FEXCore/include/FEXCore/Utils/SignalScopeGuards.h').read_text()
    lookup = (fex / 'FEXCore/Source/Interface/Core/LookupCache.h').read_text()
    rpm = (fex / 'Source/Windows/Common/CRT/Alloc.cpp').read_text()
    windows = signal.split('// Dummy implementations as Windows', 1)[1]
    windows = windows[windows.index('template<template<typename> class LockType'):]
    windows = windows.rsplit('\n#endif\n} // namespace FEXCore', 1)[0]
    replacements = {
        '@BRIDGE@': section(module, '// BEGIN FEX_IOS_NATIVE_CRITICAL_BRIDGE', '// END FEX_IOS_NATIVE_CRITICAL_BRIDGE'),
        '@PAIRS@': section(module, '// BEGIN FEX_IOS_PAIRED_NATIVE_CRITICAL', '// END FEX_IOS_PAIRED_NATIVE_CRITICAL'),
        '@UNMAP_CALLBACK@': 'void NotifyUnmapViewOfSection' + module.split('void NotifyUnmapViewOfSection', 1)[1].split('\nvoid FlushInstructionCacheHeavy', 1)[0],
        '@READ_CALLBACK@': 'void BTCpu64NotifyReadFile' + module.split('void BTCpu64NotifyReadFile', 1)[1].split('\n/* iOS-Madeira ml612', 1)[0],
        '@WINDOWS_TEMPLATES@': windows,
        '@LOOKUP_TOKENS@': section(lookup, 'namespace FEXCore {', 'struct GuestToHostMap {'),
        '@RPM_GUARD@': 'struct IosRpmGuard {' + rpm.split('namespace { struct IosRpmGuard {', 1)[1].split('}; }', 1)[0] + '};',
    }
    body = (HERE / 'controls/fex/test-native-critical.cpp.in').read_text()
    for name, value in replacements.items():
        need(body.count(name) == 1, 'Unique FEX harness insertion')
        body = body.replace(name, value)
    (fout / 'test-native-critical.cpp').write_text(body)
    (fout / 'test-nonios.cpp').write_text((HERE / 'controls/fex/test-nonios.cpp.in').read_text().replace('@WINDOWS_TEMPLATES@', windows))
    headers = fout / 'include/FEXCore/Utils'
    headers.mkdir(parents=True)
    for name in ('NativeCriticalSection.h', 'NativeCriticalSectionABI.h'):
        shutil.copyfile(fex / 'FEXCore/include/FEXCore/Utils' / name, headers / name)
    for name in ('native-harness.c', 'image-fixture.h', 'madeira_cfg.h'):
        shutil.copyfile(HERE / 'controls/owner' / name, oout / name)
    (oout / 'source').mkdir()
    for name in ('ios_critical_owner_sample.h', 'ios_critical_owner_mapping.h'):
        shutil.copyfile(madeira / 'build/ntdll-unix' / name, oout / 'source' / name)
    # Production inputs and generated harnesses are independently reread.
    need(all(sha(root / name) == digest for name, digest in manifest['expectedPatchedSources'].items()),
         'Patched source drift during extraction')
    outputs = {str(p.relative_to(output)): sha(p) for p in sorted(output.rglob('*')) if p.is_file()}
    receipt = {'status': 'exact_production_control_sources_extracted_not_compiled_or_executed',
               'inputs': manifest['expectedPatchedSources'], 'outputs': outputs,
               'compilerExecuted': False, 'deviceActions': False, 'runtimeQualified': False}
    (output / 'extraction.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.source_root or args.output:
        need(args.source_root and args.output, 'Both explicit source root and exclusive output required')
        print(json.dumps(extract(args.source_root, args.output), sort_keys=True))
    else:
        verify_checkpoint()
        print('Public source checkpoint hashes verified; no compile/device action.')
