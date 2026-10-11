"""Materialize only the separately reviewed diagnostic source/runtime copies.

No command, compiler, Wine, network or device operation is implemented here.
The root executes recipe.json commands through its owned bounded wrapper.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE.parent / 'unwind-first-miss-diagnostic-build'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def fingerprint(path):
    s = path.lstat()
    if not stat.S_ISREG(s.st_mode):
        raise ValueError('Ordinary bound provider required: ' + str(path))
    return [s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_size,
            s.st_mtime_ns, s.st_ctime_ns]


def verify(rows):
    for name, row in rows.items():
        path = Path(name)
        before = fingerprint(path)
        if before != row['stableStat'] or digest(path) != row['sha256']:
            raise ValueError('Bound provider differs: ' + name)
        if fingerprint(path) != before:
            raise ValueError('Provider changed during read: ' + name)


def prepare():
    recipe = json.loads((HERE / 'recipe.json').read_text())
    verify(recipe['inputs'])
    if OUT.exists() or OUT.is_symlink():
        raise ValueError('Fresh separate diagnostic output required')
    OUT.mkdir()
    copied = {}
    for row in recipe['copies']:
        source = Path(row['source'])
        relative = Path(row['relativeTarget'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Fixed output scope')
        target = OUT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with source.open('rb') as src, target.open('xb') as dst:
            for chunk in iter(lambda: src.read(1024 * 1024), b''):
                dst.write(chunk)
            dst.flush()
            os.fsync(dst.fileno())
        if digest(target) != recipe['inputs'][str(source)]['sha256']:
            raise ValueError('Independent copied-provider readback failed')
        copied[str(target)] = {'sha256': digest(target),
                               'stableStat': fingerprint(target)}
    verify(recipe['inputs'])
    # Commands are exact argv rows for the root's separate owned wrapper.
    with (OUT / 'preparation-receipt.json').open('x') as f:
        json.dump({'schema': 1, 'status': 'diagnostic_source_and_runtime_copies_only',
                   'recipeSha256': digest(HERE / 'recipe.json'), 'inputs': recipe['inputs'],
                   'copies': copied, 'commandsExecuted': False,
                   'runtimeQualified': False}, f, indent=2, sort_keys=True)
        f.write('\n')
    return {'output': str(OUT), 'copiedFiles': len(copied),
            'runtimeOrCompilerExecuted': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--prepare', action='store_true')
    args = p.parse_args()
    if args.prepare:
        print(json.dumps(prepare(), sort_keys=True))
    else:
        recipe = json.loads((HERE / 'recipe.json').read_text())
        verify(recipe['inputs'])
        print(json.dumps({'inputFilesReplayed': len(recipe['inputs']),
                          'commandsExecuted': False}, sort_keys=True))
