"""Extract retained production bodies; write C++ sources only, never compile."""
from pathlib import Path
import argparse
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
MODULE = 'Source/Windows/ARM64EC/Module.cpp'

def function(text, name):
    match = re.search(r'(?m)^(?:[A-Za-z_][A-Za-z_0-9]*[ *]+)+' + re.escape(name) + r'\s*\(', text)
    if not match:
        raise ValueError('Missing production definition ' + name)
    start, index = match.start(), match.end()
    opening = text.index('{', index)
    depth, end = 1, opening + 1
    while depth:
        if end >= len(text):
            raise ValueError('Unclosed production function ' + name)
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end] + '\n'

def generate(directory, fex_source, wine_signal, wine_unwind):
    fex_source, wine_signal, wine_unwind = map(Path, (fex_source, wine_signal, wine_unwind))
    manifest = json.loads((HERE/'source-manifest.json').read_text())
    sources = {fex_source/name:digest for name,digest in manifest['candidateSources'].items()}
    sources.update({wine_signal:manifest['wineExtractionSources']['signalSha256'],
                    wine_unwind:manifest['wineExtractionSources']['unwindSha256']})
    for path, digest in sources.items():
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('Exact published production source required: ' + str(path))
    directory = Path(directory)
    directory.mkdir(exist_ok=False)
    module = (fex_source/MODULE).read_text()
    bodies = [function(module, name) for name in (
        'ReconstructThreadRegisters', 'ReconstructThreadState', 'StoreStateToPackedECContext')]
    bodies.append('#ifdef FEX_IOS_HOST\n' + function(module, 'PreserveEnterECNativeLink') + '#endif\n')
    # Stop only after the production snapshot and new selector. Dispatch itself
    # requires the real Wine/FEX runtime and is outside this isolated harness.
    rethrow = function(module, 'RethrowGuestException')
    prefix = rethrow[:rethrow.index('  LogMan::Msg::DFmt("pc:')]
    prefix = prefix.replace('static void RethrowGuestException', 'static ARM64_NT_CONTEXT SnapshotBeforeDispatch', 1)
    prefix = prefix.replace('  auto& Fault = Thread->CurrentFrame->SynchronousFaultData;\n', '')
    bodies.append(prefix + '  return GuestContext;\n}\n')
    unwind = wine_unwind.read_text()
    for name in ('ctx_flags_x64_to_arm', 'ctx_flags_arm_to_x64', 'eflags_to_cpsr', 'cpsr_to_eflags',
                 'mxcsr_to_fpcsr', 'fpcsr_to_mxcsr', 'context_x64_to_arm', 'context_arm_to_x64'):
        bodies.append(function(unwind, name))
    # Exact existing self-apply block: notably skips x18 unless its explicit
    # native flag was requested. No service/server behavior is simulated.
    setter = function(wine_signal.read_text(), 'NtSetContextThread')
    start = setter.index('    if (flags & CONTEXT_INTEGER)')
    end = setter.index('    if (flags & CONTEXT_DEBUG_REGISTERS)', start)
    self_block = setter[start:end]
    bodies.append('static void ApplySelfRegisterBlock(const CONTEXT* context) {\n'
                  '    auto* frame = get_syscall_frame();\n'
                  '    DWORD flags = context->ContextFlags & ~CONTEXT_ARM64;\n' + self_block + '}\n')
    generated = '#include "native-adapter.hpp"\n' + '\n'.join(bodies) + (HERE/'native-cases.cpp').read_text()
    (directory/'candidate.cpp').write_text(generated)
    # The original body has no preservation helper/call. Only those additions
    # are removed, retaining the original LoopTop GPR/vector/flag correction.
    original = generated.replace('#ifdef FEX_IOS_HOST\n' + function(module, 'PreserveEnterECNativeLink') + '#endif\n', '')
    original = original.replace('#ifdef FEX_IOS_HOST\n  PreserveEnterECNativeLink(Thread, Rec, Context, GuestContext);\n#endif\n', '')
    (directory/'original.cpp').write_text(original)
    functions = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (
        fex_source/MODULE, wine_signal, wine_unwind, HERE/'native-adapter.hpp',
        HERE/'native-entry.S', HERE/'native-cases.cpp', Path(__file__))}
    (directory/'extraction.json').write_text(json.dumps({'status':'generated_sources_not_compiled',
        'inputHashes':functions,'generatedSha256':hashlib.sha256(generated.encode()).hexdigest(),
        'selfRegisterBlockSha256':hashlib.sha256(self_block.encode()).hexdigest()},indent=2)+'\n')
    for path, digest in sources.items():
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('Production source changed during extraction: ' + str(path))
    return generated

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--fex-source', type=Path, required=True)
    parser.add_argument('--wine-signal', type=Path, required=True)
    parser.add_argument('--wine-unwind', type=Path, required=True)
    args = parser.parse_args()
    generate(args.output, args.fex_source, args.wine_signal, args.wine_unwind)
