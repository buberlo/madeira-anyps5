#!/usr/bin/env python3
"""Replay existing and experimental patches in a disposable copy, without Git changes."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import shlex
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent


def need(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    path = Path(path)
    need(not path.is_symlink(), 'No ambiguous patch source')
    return path.read_bytes() if path.is_file() else None


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def run(argv, cwd):
    result = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=30)
    need(result.returncode == 0, 'Source replay failed: ' + result.stderr.decode(errors='replace'))
    return result.stdout


def paths(patch):
    result = set()
    for line in patch.read_text().splitlines():
        if line.startswith('diff --git '):
            for item in shlex.split(line)[2:4]:
                path = Path(item[2:])
                need(item.startswith(('a/', 'b/')) and not path.is_absolute() and '..' not in path.parts,
                     'Ordinary relative patch path')
                result.add(str(path))
    return result


def check(root, extract_to=None):
    root = Path(root).resolve()
    spec = importlib.util.spec_from_file_location('checkpoint_extractor', HERE / 'extract-controls.py')
    extractor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(extractor)
    manifest = extractor.verify_checkpoint()
    results = {}
    with tempfile.TemporaryDirectory(prefix='native59-public-source-replay-') as temporary:
        scratch = Path(temporary)
        loop_module = None
        for kind, directory in (('fex', 'FEX'), ('wine', 'wine'), ('madeira', 'Madeira')):
            repo = root / 'upstreams' / directory
            need(run(['git', '-C', str(repo), 'rev-parse', 'HEAD'], root).decode().strip() == manifest['pinnedHeads'][kind],
                 'Exact pinned upstream checkout')
            held = sorted((root / 'patches' / kind).glob('*.patch'))
            added = sorted((HERE / 'patches' / kind).glob('*.patch'))
            touched = set().union(*(paths(p) for p in held + added))
            tree = scratch / 'upstreams' / directory
            tree.mkdir(parents=True)
            original = {name: read(repo / name) for name in touched}
            for name, raw in original.items():
                if raw is not None:
                    path = tree / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(raw)
            for patch in reversed(held):
                run(['git', 'apply', '--reverse', str(patch)], tree)
            for name in touched:
                source, relative = repo, name
                if kind == 'fex' and name.startswith('External/rpmalloc/'):
                    source, relative = repo / 'External/rpmalloc', name[len('External/rpmalloc/'):]
                result = subprocess.run(['git', '-C', str(source), 'show', 'HEAD:' + relative], capture_output=True, timeout=30)
                blob = result.stdout if result.returncode == 0 else None
                need(read(tree / name) == blob, 'Exact upstream Git blob: ' + name)
            for patch in held:
                run(['git', 'apply', str(patch)], tree)
            need(all(read(tree / name) == raw for name, raw in original.items()), 'Existing complete patch series')
            for patch in added:
                run(['git', 'apply', str(patch)], tree)
                if kind == 'fex' and patch.name.startswith('0004-'):
                    loop_module = read(tree / 'Source/Windows/ARM64EC/Module.cpp')
            prefix = 'upstreams/' + directory + '/'
            for name, digest in manifest['expectedPatchedSources'].items():
                if name.startswith(prefix):
                    need(sha(read(tree / name[len(prefix):])) == digest, 'Exact experimental source: ' + name)
            results[kind] = {'existingReverseToHead': True, 'existingForwardExact': True,
                             'experimentalForwardExact': True, 'experimentalPatchCount': len(added)}
            need(all(read(repo / name) == raw for name, raw in original.items()), 'Canonical source unchanged')
        if extract_to is not None:
            extractor.extract(scratch, extract_to)
            need(loop_module is not None, 'Exact intermediate LoopTop source')
            loop = Path(extract_to) / 'loop-top'
            loop.mkdir()
            (loop / 'Module.cpp').write_bytes(loop_module)
        # Reverse all experimental additions after extracting, to check overlapping boundaries.
        for kind, directory in (('fex', 'FEX'), ('wine', 'wine'), ('madeira', 'Madeira')):
            tree = scratch / 'upstreams' / directory
            for patch in reversed(sorted((HERE / 'patches' / kind).glob('*.patch'))):
                run(['git', 'apply', '--reverse', str(patch)], tree)
            for name in set().union(*(paths(p) for p in (HERE / 'patches' / kind).glob('*.patch'))):
                need(read(tree / name) == read(root / 'upstreams' / directory / name), 'Experimental reverse boundary')
            results[kind]['experimentalReverseExact'] = True
    return {'status': 'experimental_source_roundtrip_only', 'series': results,
            'canonicalModified': False, 'compilerExecuted': False, 'deviceActions': False,
            'cpuQualified': False, 'gpuQualified': False, 'gameplayQualified': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--extract-to', type=Path)
    args = parser.parse_args()
    print(json.dumps(check(args.source_root, args.extract_to), indent=2, sort_keys=True))
