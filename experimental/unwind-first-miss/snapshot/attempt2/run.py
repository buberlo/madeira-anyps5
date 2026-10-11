"""Exact isolated first-missing-frame diagnostic; import never starts a child."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RECIPE = HERE/'recipe.json'
OUT = HERE.parent/'unwind-first-miss-diagnostic-build-attempt2'
PREP = OUT/'preparation-receipt.json'
CHILD = HERE/'bounded_local_process.py'
RECIPE_SHA = '4a4c022abbd585f2054c6d7fb1dcfbcde9ddee25cdfc9e940a857ea0004d63db'
ORIGINAL_PREP_SHA = '528463569a83d081256eecac11e3a5aa925ecfaa0acd32d278ccb664fe779351'
CHILD_SHA = 'ccc02bafc5e57b55df3208905d849b34427211aca5b21938a7cf8e07b64a33f6'
MIB = 1024**2
MIN_FREE = 2*1024**3
ARTIFACT_MAX = 32*MIB
PREFIX_MAX = 512*MIB
ENTRY_MAX = 16384
TOTAL_SECONDS = 420


def need(value, message):
    if not value:
        raise ValueError(message)


def stamp(s):
    return [s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_size,
            s.st_mtime_ns, s.st_ctime_ns]


def read(path, expected=None, stable=None):
    path = Path(path)
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode), 'Ordinary provider required: '+str(path))
    need(path.resolve(strict=True) == path, 'No linked provider path: '+str(path))
    if stable is not None:
        need(stamp(before) == stable, 'Provider identity differs: '+str(path))
    h = hashlib.sha256()
    with path.open('rb') as f:
        need(stamp(os.fstat(f.fileno())) == stamp(before), 'Provider FD differs')
        for data in iter(lambda: f.read(MIB), b''):
            h.update(data)
        need(stamp(os.fstat(f.fileno())) == stamp(before), 'Provider changed during FD read')
    need(stamp(path.lstat()) == stamp(before), 'Provider changed during replay')
    digest = h.hexdigest()
    if expected is not None:
        need(digest == expected, 'Provider full bytes differ: '+str(path))
    return {'sha256': digest, 'stableStat': stamp(before)}


def replay(rows):
    for name, row in rows.items():
        read(name, row['sha256'], row['stableStat'])
    for name, row in rows.items():
        need(stamp(Path(name).lstat()) == row['stableStat'], 'Late provider identity drift: '+name)


def load_module(path):
    spec = importlib.util.spec_from_file_location('bounded_diagnostic_child', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def contract(review_sha, preparation_sha):
    review = HERE/'source-review.json'
    read(review, review_sha)
    proof = json.loads(review.read_text())
    need(proof['status'] == 'held_inert_exact_unwind_first_miss_execution_source', 'Source review status')
    replay(proof['inputs'])
    read(RECIPE, RECIPE_SHA)
    need(preparation_sha is not None and len(preparation_sha) == 64, 'Explicit actual preparation digest required')
    read(PREP, preparation_sha)
    read(CHILD, CHILD_SHA)
    recipe = json.loads(RECIPE.read_text())
    prepared = json.loads(PREP.read_text())
    need(recipe['output'] == str(OUT) and recipe['ownedPrefix'] == str(OUT/'wine-prefix'), 'Fixed isolated output')
    need(prepared['status'] == 'diagnostic_source_and_runtime_copies_only_attempt2'
         and prepared['recipeSha256'] == RECIPE_SHA and prepared['commandsExecuted'] is False,
         'Exact genuine copied-source preparation')
    need(prepared['originalPreparationSha256'] == ORIGINAL_PREP_SHA, 'Exact reused fourteen providers')
    need(prepared['inputs'] == recipe['inputs'], 'Prepared original provider map')
    expected = {str(OUT/row['relativeTarget']): recipe['inputs'][row['source']]['sha256'] for row in recipe['copies']}
    need({k:v['sha256'] for k,v in prepared['copies'].items()} == expected and len(expected) == 14,
         'Complete exact fourteen copied source/runtime providers')
    need([r['name'] for r in recipe['commands']] ==
         ['compile-exports','link-libc','rename-eh-frame','first-miss-trace'], 'Only exact four diagnostic commands')
    need([r['timeoutSeconds'] for r in recipe['commands']] == [180,60,15,15], 'Exact command budgets')
    replay(recipe['inputs'])
    replay(prepared['copies'])
    return recipe, prepared, proof


def win(path):
    path = Path(path)
    need(path.is_absolute(), 'Absolute Windows path source')
    return 'Z:'+str(path).replace('/', '\\')


def environment(recipe, runtime=False):
    env = {k:v for k,v in os.environ.items() if not k.startswith(
        ('APS5_','ANYPS5_','MADEIRA_','FEX_','MVK_','WINE','VK_','GCC_','COMPILER_','LIBRARY_','CPLUS_','C_INCLUDE_','DYLD_','CCACHE_'))
        and k not in ('CPATH','INCLUDE','LIB','LIBPATH')}
    wine = Path(recipe['wine'])
    compiler = ROOT/'build/toolchains/winlibs/mingw64/bin'
    env.update(WINEPREFIX=recipe['ownedPrefix'], WINEDEBUG='-all',
               WINEDLLOVERRIDES='winemenubuilder.exe=d;mscoree,mshtml=d',
               PATH=str(wine.parent)+':/usr/bin:/bin',
               WINEPATH=win(OUT/'runtime') if runtime else win(compiler),
               ANYPS5_NO_SHADER_CACHE='1')
    if runtime:
        env.update(recipe['commands'][3]['extraEnvironment'])
    return env


def inventory(live=False):
    totals = {'artifactBytes':0, 'prefixBytes':0, 'entries':0, 'livePrefixDisappearances':0}
    def visit(path, prefix):
        try:
            s = path.lstat()
        except FileNotFoundError:
            if live and prefix:
                totals['livePrefixDisappearances'] += 1
                return
            raise
        totals['entries'] += 1
        need(totals['entries'] <= ENTRY_MAX, 'Owned entry quota')
        if stat.S_ISDIR(s.st_mode):
            try:
                for child in path.iterdir():
                    visit(child, prefix or child == OUT/'wine-prefix')
            except FileNotFoundError:
                if live and prefix:
                    totals['livePrefixDisappearances'] += 1
                    return
                raise
        elif stat.S_ISREG(s.st_mode):
            key = 'prefixBytes' if prefix else 'artifactBytes'
            totals[key] += s.st_size
            need(totals[key] <= (PREFIX_MAX if prefix else ARTIFACT_MAX), 'Owned '+key+' quota')
        elif stat.S_ISLNK(s.st_mode):
            # Wine's own dosdevices links are counted but never followed.
            need(prefix, 'Unexpected linked diagnostic artifact: '+str(path))
        else:
            # The Wine server's own socket is a bounded prefix entry only.
            need(prefix and stat.S_ISSOCK(s.st_mode), 'Unexpected special diagnostic artifact: '+str(path))
    visit(OUT, False)
    return totals


def execute(review_sha, preparation_sha):
    recipe, prepared, proof = contract(review_sha, preparation_sha)
    need(shutil.disk_usage(OUT).free >= MIN_FREE, 'Initial2GiB reserve')
    prefix = OUT/'wine-prefix'
    need(not prefix.exists() and not prefix.is_symlink(), 'Fresh own prefix required')
    execution = OUT/'execution'
    need(not execution.exists() and not execution.is_symlink(), 'Single-use fresh diagnostic execution')
    execution.mkdir()
    bounded = load_module(CHILD)
    started = time.monotonic()
    result = {'schema':1, 'status':'failed', 'sourceReviewSha256':review_sha,
              'recipeSha256':RECIPE_SHA, 'preparationSha256':preparation_sha,
              'commands':[], 'ownedPrefixJoined':False,
              'runtimeQualified':False, 'exceptionRepairClaimed':False,
              'deviceExecuted':False, 'testExitCode':None}
    failure = None
    def guard():
        need(time.monotonic()-started < TOTAL_SECONDS, 'Total diagnostic deadline')
        need(shutil.disk_usage(OUT).free >= MIN_FREE, 'Live2GiB reserve')
        inventory(live=True)
    def command(label, argv, *, cwd, env, timeout, cleanup=False):
        try:
            row = bounded.run(argv, cwd=cwd, env=env,
                stdout=execution/(label+'.stdout'), stderr=execution/(label+'.stderr'),
                timeout=timeout, stream_maximum=MIB,
                guard=(lambda:None) if cleanup else guard, cleanup_seconds=3)
        except bounded.CommandFailure as error:
            row = error.result
            row['name'] = label
            result['commands'].append(row)
            raise
        row['name'] = label
        result['commands'].append(row)
        return row
    try:
        for index, row in enumerate(recipe['commands']):
            guard()
            # Source/caller copies stay exact; libc.prx/object are new outputs.
            replay(prepared['copies'])
            obs = command(row['name'], [recipe['wine'], *row['windowsArgv']],
                cwd=row.get('cwd',str(OUT)), env=environment(recipe,index == 3),
                timeout=row['timeoutSeconds'])
            if index < 3:
                need(obs['exitCode'] == 0, 'Diagnostic build command failed: '+row['name'])
            else:
                result['testExitCode'] = obs['exitCode']
                result['testPassed'] = obs['exitCode'] == 0
                result['testObservation'] = 'ordinary_captured_exit_not_runtime_acceptance'
        result['status'] = 'diagnostic_observed_no_runtime_or_repair_acceptance'
    except BaseException as error:
        failure = error
        result['error'] = type(error).__name__+': '+str(error)
    finally:
        try:
            env = environment(recipe)
            try:
                joined = command('prefix-graceful-wait', [recipe['wineserver'],'-w'],
                    cwd=OUT,env=env,timeout=30,cleanup=True)
                need(joined['exitCode'] == 0, 'Graceful prefix join failed')
            except bounded.CommandFailure as error:
                need(error.result['timedOut'], 'Only timed-out graceful join permits force close')
                killed = command('prefix-timeout-kill',[recipe['wineserver'],'-k'],
                    cwd=OUT,env=env,timeout=15,cleanup=True)
                result['forceCloseExitCode'] = killed['exitCode']
                joined = command('prefix-post-kill-wait',[recipe['wineserver'],'-w'],
                    cwd=OUT,env=env,timeout=15,cleanup=True)
                need(joined['exitCode'] == 0, 'Final prefix join failed')
            result['ownedPrefixJoined'] = True
        except BaseException as error:
            result['prefixCleanupError'] = type(error).__name__+': '+str(error)
            failure = failure or error
        try:
            replay(recipe['inputs']); replay(prepared['copies']); replay(proof['inputs'])
            result['providersAndCopiesUnchanged'] = True
            result['outputInventory'] = inventory()
            result['outputs'] = {}
            for p in OUT.rglob('*'):
                if p.is_relative_to(prefix):
                    continue
                if stat.S_ISREG(p.lstat().st_mode):
                    result['outputs'][str(p)] = read(p)
        except BaseException as error:
            result['finalReplayError'] = type(error).__name__+': '+str(error)
            failure = failure or error
        if failure is not None:
            result['status'] = 'failed'
        result['elapsedSeconds'] = time.monotonic()-started
        payload = (json.dumps(result,indent=2,sort_keys=True)+'\n').encode()
        need(len(payload) <= 512*1024, 'Bounded diagnostic receipt')
        with (execution/'receipt.json').open('xb') as f:
            f.write(payload);f.flush();os.fsync(f.fileno())
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--review-sha', required=True)
    parser.add_argument('--preparation-sha', required=True)
    args = parser.parse_args()
    if args.execute:
        result = execute(args.review_sha,args.preparation_sha)
        print(json.dumps({'status':result['status'],'testExitCode':result['testExitCode'],
                          'receipt':str(OUT/'execution/receipt.json')}))
        raise SystemExit(1 if result['status'] == 'failed' else 0)
    contract(args.review_sha,args.preparation_sha)
    print(json.dumps({'status':'readonly_diagnostic_execution_contract_passed','commandsExecuted':False}))
