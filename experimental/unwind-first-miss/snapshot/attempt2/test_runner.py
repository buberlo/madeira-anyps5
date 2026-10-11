import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('diagnostic_runner', HERE/'run.py')
r = importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


class FakeFailure(RuntimeError):
    def __init__(self,result):self.result=result


class Controls(unittest.TestCase):
    def scenario(self, *, fail_compile=False, wait_timeout=False, wait_nonzero=False, late_drift=False):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d).resolve();(out/'runtime').mkdir()
            provider = out/'runtime/caller.exe';provider.write_bytes(b'held caller')
            copies = {str(provider):r.read(provider)}
            recipe = {'wine':'/exact/wine','wineserver':'/exact/wineserver','ownedPrefix':str(out/'wine-prefix'),
                      'inputs':{}, 'commands':[{'name':name,'windowsArgv':[name], 'timeoutSeconds':timeout}
                        for name,timeout in zip(['compile-exports','link-libc','rename-eh-frame','first-miss-trace'],[180,60,15,15])]}
            recipe['commands'][-1]['extraEnvironment']={'APS5_UNWIND_MISS_TRACE':'1'}
            calls=[]
            class Fake:
                CommandFailure=FakeFailure
                @staticmethod
                def run(argv,**kw):
                    name=kw['stdout'].name.split('.')[0];calls.append((name,argv,kw))
                    kw['guard']()
                    kw['stdout'].write_bytes(b'observed');kw['stderr'].write_bytes(b'')
                    row={'argv':list(argv),'exitCode':3 if name=='first-miss-trace' else 0,
                        'timedOut':False,'directChildJoined':True,'groupAbsent':True,
                        'streamsJoined':True,'captureComplete':True,'stdoutDiscarded':0,'stderrDiscarded':0}
                    if name=='compile-exports' and fail_compile:row['exitCode']=1
                    if name=='prefix-graceful-wait' and wait_timeout:
                        row['timedOut']=True;raise FakeFailure(row)
                    if name=='prefix-graceful-wait' and wait_nonzero:row['exitCode']=1
                    if name=='first-miss-trace' and late_drift:provider.write_bytes(b'changed')
                    return row
            with patch.object(r,'OUT',out),patch.object(r,'contract',return_value=(recipe,{'copies':copies},{'inputs':{}})), \
                 patch.object(r,'load_module',return_value=Fake),patch.object(r.shutil,'disk_usage',return_value=type('D',(),{'free':r.MIN_FREE+1})()):
                result=r.execute('review','preparation')
            self.assertEqual(json.loads((out/'execution/receipt.json').read_text())['status'],result['status'])
            return result,calls

    def test_real_recipe_budgets_and_carrier(self):
        q=json.loads(r.RECIPE.read_text())
        self.assertEqual(r.read(r.RECIPE)['sha256'],r.RECIPE_SHA)
        self.assertEqual([x['timeoutSeconds'] for x in q['commands']],[180,60,15,15])
        self.assertEqual(len(q['reusedLibcObjects']),45)
        self.assertEqual(len(q['copies']),14)

    def test_ordinary_nonzero_trace_is_observation(self):
        result,calls=self.scenario()
        self.assertEqual(result['status'],'diagnostic_observed_no_runtime_or_repair_acceptance')
        self.assertEqual(result['testExitCode'],3);self.assertFalse(result['testPassed'])
        self.assertFalse(result['runtimeQualified']);self.assertFalse(result['exceptionRepairClaimed'])
        self.assertEqual(len(calls),5);self.assertEqual(calls[-1][1],['/exact/wineserver','-w'])
        self.assertEqual([x[2]['timeout'] for x in calls],[180,60,15,15,30])

    def test_compile_failure_stops_test_and_closes_prefix(self):
        result,calls=self.scenario(fail_compile=True)
        self.assertEqual(result['status'],'failed')
        self.assertEqual([x[0] for x in calls],['compile-exports','prefix-graceful-wait'])
        self.assertTrue(result['ownedPrefixJoined'])

    def test_only_timeout_permits_kill_then_final_join(self):
        result,calls=self.scenario(wait_timeout=True)
        self.assertEqual([x[1][-1] for x in calls[-3:]],['-w','-k','-w'])
        self.assertTrue(result['ownedPrefixJoined'])
        self.assertEqual(result['commands'][-3]['timedOut'],True)

    def test_nonzero_graceful_join_does_not_force(self):
        result,calls=self.scenario(wait_nonzero=True)
        self.assertEqual(result['status'],'failed');self.assertFalse(result['ownedPrefixJoined'])
        self.assertNotIn('-k',[x[1][-1] for x in calls])

    def test_late_caller_drift_never_accepted(self):
        result,calls=self.scenario(late_drift=True)
        self.assertEqual(result['status'],'failed');self.assertIn('finalReplayError',result)
        self.assertTrue(result['ownedPrefixJoined'])

    def test_exact_environment_routes_and_inherited_flags_removed(self):
        q=json.loads(r.RECIPE.read_text())
        with patch.dict(r.os.environ,{'APS5_UNWIND_MISS_TRACE':'evil','APS5_X':'bad','WINEPREFIX':'/foreign','CPATH':'/foreign',
                                    'DYLD_INSERT_LIBRARIES':'/foreign','CCACHE_PREFIX':'/foreign'}):
            compiler=r.environment(q);runtime=r.environment(q,True)
        self.assertNotIn('APS5_X',compiler);self.assertNotIn('CPATH',compiler)
        self.assertNotIn('DYLD_INSERT_LIBRARIES',compiler);self.assertNotIn('CCACHE_PREFIX',compiler)
        self.assertEqual(runtime['APS5_UNWIND_MISS_TRACE'],'1')
        self.assertEqual(runtime['WINEPATH'],r.win(r.OUT/'runtime'))
        self.assertNotIn('mingw',runtime['WINEPATH'])
        self.assertEqual(compiler['WINEPREFIX'],q['ownedPrefix'])

    def test_artifact_links_refused_prefix_links_not_followed(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d).resolve();(out/'wine-prefix').mkdir();(out/'wine-prefix/drive').symlink_to('/foreign')
            with patch.object(r,'OUT',out):
                self.assertEqual(r.inventory()['entries'],3)
                (out/'bad').symlink_to('/foreign')
                with self.assertRaises(ValueError):r.inventory()

    def test_saved_provider_inode_and_digest_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d).resolve()/'file';p.write_bytes(b'exact');row=r.read(p)
            with self.assertRaises(ValueError):r.read(p,'0'*64,row['stableStat'])
            old=row['stableStat'].copy();old[1]+=1
            with self.assertRaises(ValueError):r.read(p,row['sha256'],old)

    def test_live_prefix_disappearing_leaf_only(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d).resolve();prefix=out/'wine-prefix';prefix.mkdir()
            missing=prefix/'removed.dll';original=Path.iterdir
            def children(path):return iter([missing]) if path==prefix else original(path)
            with patch.object(r,'OUT',out),patch.object(Path,'iterdir',children):
                self.assertEqual(r.inventory(live=True)['livePrefixDisappearances'],1)
                with self.assertRaises(FileNotFoundError):r.inventory(live=False)

    def test_live_static_disappearance_is_strict(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d).resolve();missing=out/'runtime.dll';original=Path.iterdir
            def children(path):return iter([missing]) if path==out else original(path)
            with patch.object(r,'OUT',out),patch.object(Path,'iterdir',children):
                with self.assertRaises(FileNotFoundError):r.inventory(live=True)

    def test_live_prefix_disappearing_directory_enumeration_only(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d).resolve();prefix=out/'wine-prefix';prefix.mkdir();original=Path.iterdir
            def children(path):
                if path==prefix:raise FileNotFoundError('live owned prefix rename')
                return original(path)
            with patch.object(r,'OUT',out),patch.object(Path,'iterdir',children):
                self.assertEqual(r.inventory(live=True)['livePrefixDisappearances'],1)
                with self.assertRaises(FileNotFoundError):r.inventory(live=False)

    def test_recipe_only_substitutes_owned_paths(self):
        s=importlib.util.spec_from_file_location('attempt2_copy_definitions',HERE/'prepare.py')
        p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
        original=json.loads(p.ORIGINAL.read_text());current=json.loads(r.RECIPE.read_text())
        self.assertEqual(current,p.derived_recipe(original));self.assertEqual(current['inputs'],original['inputs'])
        self.assertEqual(current['reusedLibcObjects'],original['reusedLibcObjects'])
        self.assertNotEqual(current['ownedPrefix'],original['ownedPrefix'])


if __name__=='__main__':unittest.main()
