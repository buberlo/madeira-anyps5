"""Root-only bounded execution of one exact prepared compiler-once candidate."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import stat
import time

HERE = Path(__file__).resolve().parent
FULL = HERE.parent
OUT = FULL/'windows-compiler-once-provider-build-attempt2'
PLAN = OUT/'plan.json'
PLAN_SHA = '4fbce2a2831e0f8b4d8e9f9cd0f0d60a14b3b31c049047dc65f01a8697f7c258'
CANDIDATE = FULL/'windows-compiler-once-direct-provider-proposal'
CANDIDATE_REVIEW = '186dc6e6ed9b98009b7387f5c2a8fee0c652a672211ac54a2b8a18c404744fc3'
RECIPE_SHA = 'ff77342a2a3dacd4e5ea4dfec35ad7558d2f58b9bee5a47efc9fd6e100a833b6'
BORROWED = FULL/'unwind-first-miss-execution-attempt2-proposal'
BORROWED_RUN_SHA = '717fb9edf65a428eb70dd78cb2bd10d0a78148819de104d769cfe5ae6a1ed410'
CHILD_SHA = 'ccc02bafc5e57b55df3208905d849b34427211aca5b21938a7cf8e07b64a33f6'
MIB = 1024**2
TOTAL_SECONDS = 1800
COMPILES = ('provider','bridge-local','bridge-import','cross','focused','original')


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def need(value, message):
    if not value: raise ValueError(message)


def windows_path(token):
    need(re.fullmatch(r'[Zz]:[\\/][^\s#$]+', token), 'Exact absolute Z-drive dependency')
    text = token[2:].replace('\\','/')
    need('..' not in Path(text).parts and Path(text).is_absolute(), 'No dependency traversal')
    return Path(text)


def dependency_record(text, target):
    # Actual GCC -MD output uses both Z:\\native and Z:/native spellings.
    # This exact recipe has no whitespace-bearing source/tool/output paths.
    text = text.replace('\\\r\n',' ').replace('\\\n',' ').strip()
    match = re.fullmatch(r'([^\s]+):\s+([^\r\n]+)', text)
    need(match is not None, 'One complete ordinary GCC dependency record')
    need(windows_path(match[1]) == target, 'Exact fresh compile target in dependency file')
    names = match[2].split()
    need(names, 'Nonempty actual compiler dependency set')
    return set(windows_path(name) for name in names)


def admit_dependencies(plan, reader):
    records = {}
    for name in COMPILES:
        path = OUT/(name+'.d')
        row = reader.read(path)
        need(row['stableStat'][4] <= 2*MIB, 'Bounded actual compiler dependency file')
        names = dependency_record(path.read_text(), OUT/(name+'.obj'))
        values = {}
        for source in sorted(names):
            key = str(source)
            need(key in plan['inputs'], 'Unbound actual compiler dependency: '+key)
            expected = plan['inputs'][key]
            reader.read(source, expected['sha256'], expected['stableStat'])
            values[key] = expected['sha256']
        reader.read(path, row['sha256'], row['stableStat'])
        records[name] = {'dependencyFile':str(path), 'file':row,
            'admittedProviderCount':len(values),
            'admittedProvidersSha256':hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest()}
    return records


def receipt_budget(plan):
    # Names are fixed by the bound recipe. Keep the actual .d files for replay,
    # rather than redundantly embedding their full provider maps in the receipt.
    names = ['plan.json','libc-preserved-exports.def','liblibc.dll.a']
    names += [name+suffix for name in COMPILES for suffix in ('.obj','.d')]
    names += ['runtime/'+name for name in ('libstdc++-6.dll','libgcc_s_seh-1.dll',
              'libwinpthread-1.dll','libc.prx','compiler_once_cross.dll',
              'compiler_once_tests.exe','windows_exception_tests.exe')]
    labels = [c['name'] for c in plan['commands']]+[
        'prefix-graceful-wait','prefix-timeout-kill','prefix-post-kill-wait']
    names += ['execution/'+label+suffix for label in labels for suffix in ('.stdout','.stderr')]
    rows = {str(OUT/name):{'sha256':'f'*64,'stableStat':[2**64-1]*7} for name in names}
    maximum = len(json.dumps(rows,sort_keys=True,indent=2).encode())
    maximum += sum(len(json.dumps(c,sort_keys=True,indent=2).encode())+4096 for c in plan['commands'])
    maximum += 128*1024  # fixed status/dependency summaries and three cleanup rows
    need(maximum<=512*1024, 'Preflight complete receipt budget')
    return maximum


def shape(plan, recipe):
    need(plan['schema']==1 and plan['status']=='inert_compiler_once_candidate_not_executed', 'Actual inert plan status')
    need(plan['sourceReviewSha256']==CANDIDATE_REVIEW and plan['output']==str(OUT)
         and plan['ownedPrefix']==str(OUT/'wine-prefix'), 'Exact prepared source and own paths')
    need(plan['directAndIatRouteRequired'] is True and plan['retainedDirectOnceCallers']==[
         'core/libs/CMakeFiles/libc.dir/prx/libc/src/ApplicationHeap.cpp.obj'], 'Exact observed direct native route')
    need(plan['expectedFocusedOrderedCases']==list(recipe.CASES)
         and plan['expectedOriginalMarker']==recipe.ORIGINAL_MARKER, 'Exact runtime predicates')
    names = ['compile-'+name for name in COMPILES]+['link-libc','link-compiler_once_cross.dll',
             'link-compiler_once_tests.exe','link-windows_exception_tests.exe']+[
             'rename-'+name for name in ('libc.prx','compiler_once_cross.dll',
             'compiler_once_tests.exe','windows_exception_tests.exe')]+[
             'run-compiler_once_tests.exe','run-windows_exception_tests.exe']
    need([c['name'] for c in plan['commands']]==names, 'Exactly sixteen ordered commands')
    need([c['timeoutSeconds'] for c in plan['commands']]==[180]*6+[60]*4+[15]*4+[60]*2,
         'Exact per-command deadlines')
    expected = {'initialAndLiveFreeBytesMinimum':2*1024**3,
        'outputBytesExcludingPrefixMaximum':64*MIB,'ownedPrefixBytesMaximum':512*MIB,
        'capturedStreamBytesMaximum':MIB,'freshPrefixAndOwnedRuntimeOnly':True,
        'allActualCompileDependenciesMustMatchInputs':True,'staticQualificationBeforeRuntime':True,
        'inputReplayBeforeAndAfter':True,'everyDirectChildAndOwnedGroupJoined':True,
        'gracefulWineserverWaitThenKillOnlyIfTimedOut':True,'prefixTerminalJoinRequired':True}
    need(plan['rootExecutionRequirements']==expected, 'Unchanged declared resource and lifetime gates')
    need(all(plan[key] is False for key in ('nativeDllInternalOnceCallsRerouted',
         'posixCancellationQualified','runtimeQualified','fullHleQualified')), 'Exact unqualified boundaries')


def contract(review_sha):
    # Use a private module instance: borrowed helper globals remain untouched.
    r = load(BORROWED/'run.py','private_once_lifetime')
    r.read(BORROWED/'run.py',BORROWED_RUN_SHA)
    r.read(BORROWED/'bounded_local_process.py',CHILD_SHA)
    review = HERE/'source-review.json'
    r.read(review, review_sha)
    proof = json.loads(review.read_text())
    need(proof['status']=='held_inert_compiler_once_execution_source', 'Executor source review status')
    r.replay(proof['inputs'])
    r.read(PLAN,PLAN_SHA)
    r.read(CANDIDATE/'source-review.json',CANDIDATE_REVIEW)
    r.read(CANDIDATE/'recipe.py',RECIPE_SHA)
    recipe = load(CANDIDATE/'recipe.py','held_once_recipe')
    plan = json.loads(PLAN.read_text())
    shape(plan,recipe)
    r.replay(plan['inputs'])
    lines = (recipe.BUILD/'build.ninja').read_text().splitlines()
    block = recipe.block(lines,'build core/libs/libs/unpatched/libc.prx core/libs/libs/implib/liblibc.dll.a:')
    objects = [recipe.BUILD/p for p in block[0].split(': CXX_SHARED_LIBRARY_LINKER__libc_Release ')[1].split()]
    libraries = dict(line.strip().split(' = ',1) for line in block[1:])['LINK_LIBRARIES'].split()
    need(plan['commands']==recipe.commands(OUT,objects,libraries), 'Entire emitted argv/environment equals held recipe')
    need(plan['baselineExports']==recipe.export_contract(recipe.pe(recipe.BUILD/'core/libs/libs/unpatched/libc.prx')),
         'Actual original 1061-export baseline')
    need((OUT/'libc-preserved-exports.def').read_text()==recipe.export_def(plan['baselineExports']), 'Exact preserved export DEF')
    copies = {str(PLAN):r.read(PLAN,PLAN_SHA),
              str(OUT/'libc-preserved-exports.def'):r.read(OUT/'libc-preserved-exports.def')}
    for name in ('libstdc++-6.dll','libgcc_s_seh-1.dll','libwinpthread-1.dll'):
        source = str(recipe.BUILD/'tests'/name)
        copies[str(OUT/'runtime'/name)] = r.read(OUT/'runtime'/name,plan['inputs'][source]['sha256'])
    need(set(str(p) for p in OUT.rglob('*') if not p.is_dir())==set(copies),
         'Exactly five prepared files and no preexisting build/prefix/evidence')
    r.OUT=OUT; r.ARTIFACT_MAX=64*MIB
    r.inventory()
    receipt_budget(plan)
    return plan,recipe,r,proof,copies


def run_commands(plan, recipe, command, dependencies, static, result):
    for index, row in enumerate(plan['commands']):
        if index==6:
            result['actualCompileDependencies'] = dependencies()
        if index==14:
            result['staticQualification'] = static()
            need(result['staticQualification']['staticNamedExportAndOwnedCallerImportsVerified'] is True
                 and result['staticQualification']['directAndIatFreshObjectSymbolsVerified'] is True,
                 'Static export/import and direct/IAT qualification before tests')
        observation = command(row,index)
        need(observation['exitCode']==0, 'Compiler-once command failed: '+row['name'])
        if index>=14:
            recipe.validate_runtime_result(observation, index==14)
            result['focusedTestsPassed' if index==14 else 'originalWindowsExceptionsPassed']=True


def execute(review_sha):
    plan,recipe,r,proof,copies = contract(review_sha)
    need(shutil.disk_usage(OUT).free>=r.MIN_FREE, 'Initial2GiB reserve')
    execution=OUT/'execution'; prefix=OUT/'wine-prefix'
    need(not execution.exists() and not execution.is_symlink() and not prefix.exists()
         and not prefix.is_symlink(), 'Single-use execution and fresh owned prefix')
    execution.mkdir()
    bounded=r.load_module(BORROWED/'bounded_local_process.py')
    started=time.monotonic(); failure=None
    result={'schema':1,'status':'failed','planSha256':PLAN_SHA,'sourceReviewSha256':review_sha,
        'candidateSourceReviewSha256':CANDIDATE_REVIEW,'commands':[],
        'focusedTestsPassed':False,'originalWindowsExceptionsPassed':False,
        'ownedPrefixJoined':False,'fullHleQualified':False,'deviceExecuted':False,
        'preflightReceiptBytesMaximum':receipt_budget(plan),
        'nativeDllInternalOnceCallsRerouted':False,'posixCancellationQualified':False}
    def guard():
        need(time.monotonic()-started<TOTAL_SECONDS, 'Total1800s compiler-once deadline')
        need(shutil.disk_usage(OUT).free>=r.MIN_FREE, 'Live2GiB reserve')
        r.inventory(live=True)
    def environment(row=None):
        env=r.environment(plan)
        if row and row['name'].startswith('run-'):
            env['WINEPATH']=r.win(OUT/'runtime'); env.update(row['extraEnvironment'])
        return env
    def captured(label,argv,cwd,env,timeout,cleanup=False):
        try:
            value=bounded.run(argv,cwd=cwd,env=env,stdout=execution/(label+'.stdout'),
                stderr=execution/(label+'.stderr'),timeout=timeout,stream_maximum=MIB,
                guard=(lambda:None) if cleanup else guard,cleanup_seconds=3)
        except bounded.CommandFailure as error:
            value=error.result; value['name']=label; result['commands'].append(value); raise
        value['name']=label;result['commands'].append(value)
        return value
    def command(row,index):
        guard();r.replay(copies)
        value=captured(row['name'],[plan['wine'],*row['windowsArgv']],
            row.get('cwd',str(OUT)),environment(row),row['timeoutSeconds'])
        if index>=14:
            value=dict(value,stdout=(execution/(row['name']+'.stdout')).read_text(),
                stderr=(execution/(row['name']+'.stderr')).read_text(),
                childJoined=value['directChildJoined'],ownedGroupAbsent=value['groupAbsent'])
        return value
    try:
        run_commands(plan,recipe,command,lambda:admit_dependencies(plan,r),
                     lambda:recipe.qualify(OUT,plan),result)
        result['status']='scoped_compiler_once_and_original_windows_exceptions_pass_not_full_hle'
    except BaseException as error:
        failure=error;result['error']=type(error).__name__+': '+str(error)
    finally:
        try:
            env=environment()
            try:
                joined=captured('prefix-graceful-wait',[plan['wineserver'],'-w'],OUT,env,30,True)
                need(joined['exitCode']==0, 'Graceful prefix join failed')
            except bounded.CommandFailure as error:
                need(error.result['timedOut'], 'Only timed-out graceful wait permits force close')
                killed=captured('prefix-timeout-kill',[plan['wineserver'],'-k'],OUT,env,15,True)
                result['forceCloseExitCode']=killed['exitCode']
                joined=captured('prefix-post-kill-wait',[plan['wineserver'],'-w'],OUT,env,15,True)
                need(joined['exitCode']==0, 'Final prefix join failed')
            result['ownedPrefixJoined']=True
        except BaseException as error:
            result['prefixCleanupError']=type(error).__name__+': '+str(error);failure=failure or error
        try:
            r.replay(plan['inputs']);r.replay(copies);r.replay(proof['inputs'])
            result['providersAndCopiesUnchanged']=True;result['outputInventory']=r.inventory()
            result['outputs']={str(p):r.read(p) for p in OUT.rglob('*')
                if not p.is_relative_to(prefix) and stat.S_ISREG(p.lstat().st_mode)}
        except BaseException as error:
            result['finalReplayError']=type(error).__name__+': '+str(error);failure=failure or error
        if failure:result['status']='failed'
        result['elapsedSeconds']=time.monotonic()-started
        payload=(json.dumps(result,sort_keys=True,indent=2)+'\n').encode()
        need(len(payload)<=512*1024, 'Bounded512KiB receipt')
        with (execution/'receipt.json').open('xb') as f:
            f.write(payload);f.flush();os.fsync(f.fileno())
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--review-sha',required=True)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    if args.execute:
        value=execute(args.review_sha)
        print(json.dumps({'status':value['status'],'receipt':str(OUT/'execution/receipt.json')}))
        raise SystemExit(value['status']=='failed')
    contract(args.review_sha)
    print(json.dumps({'status':'readonly_exact_compiler_once_execution_contract_passed','commandsExecuted':False}))
