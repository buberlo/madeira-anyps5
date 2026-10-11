import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
import gc
import warnings

spec = importlib.util.spec_from_file_location('bounded', Path(__file__).with_name('bounded_local_process.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


@unittest.skipUnless(os.name == 'posix', 'POSIX process-group helper')
class Bounds(unittest.TestCase):
    def command(self, root, code, **changes):
        args = dict(cwd=root, env=dict(os.environ), stdout=root/'out', stderr=root/'err',
                    timeout=2, stream_maximum=1024, cleanup_seconds=2)
        args.update(changes)
        return m.run([str(Path(sys.executable).resolve()), '-I', '-B', '-c', code], **args)

    def test_complete_both_streams_and_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); r = self.command(p, 'import sys;print("out");print("err",file=sys.stderr);sys.exit(7)')
            self.assertEqual(r['exitCode'], 7)
            self.assertTrue(r['captureComplete'] and r['groupAbsent'] and r['streamsJoined'])
            self.assertEqual((p/'out').read_bytes(), b'out\n')
            self.assertEqual((p/'err').read_bytes(), b'err\n')

    def test_timeout_joins_child_and_streams(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(m.CommandFailure) as failure:
                self.command(Path(d), 'import time;time.sleep(10)', timeout=.1)
            r = failure.exception.result
            self.assertTrue(r['timedOut'] and r['directChildJoined'] and r['groupAbsent'] and r['streamsJoined'])
            self.assertFalse(r['captureComplete'])

    def test_live_stdout_quota(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            with self.assertRaises(m.CommandFailure) as failure:
                self.command(p, 'import os,time;os.write(1,b"x"*8192);time.sleep(10)', stream_maximum=128)
            self.assertEqual((p/'out').stat().st_size, 128)
            self.assertGreater(failure.exception.result['stdoutDiscarded'], 0)
            self.assertTrue(failure.exception.result['groupAbsent'])

    def test_live_stderr_quota(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            with self.assertRaises(m.CommandFailure):
                self.command(p, 'import os,time;os.write(2,b"x"*8192);time.sleep(10)', stream_maximum=128)
            self.assertEqual((p/'err').stat().st_size, 128)

    def test_live_guard_failure_still_joins(self):
        calls = 0
        def guard():
            nonlocal calls
            calls += 1
            if calls == 3: raise ValueError('resource refused')
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(m.CommandFailure) as failure:
                self.command(Path(d), 'import time;time.sleep(10)', guard=guard)
            r = failure.exception.result
            self.assertTrue(r['directChildJoined'] and r['streamsJoined'] and r['groupAbsent'])

    def test_leader_exit_with_live_descendant_uses_retained_group(self):
        # Child inherits both pipes. Its parent exits before cleanup; cached PGID
        # must still close that descendant rather than calling getpgid(dead_pid).
        code = 'import os,time;pid=os.fork();time.sleep(10) if pid==0 else None;os._exit(0)'
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(m.CommandFailure) as failure:
                self.command(Path(d), code, timeout=.1)
            self.assertTrue(failure.exception.result['directChildJoined'])
            self.assertTrue(failure.exception.result['streamsJoined'])
            self.assertTrue(failure.exception.result['groupAbsent'])

    def test_existing_capture_refused_without_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'out').write_bytes(b'keep')
            with self.assertRaises(ValueError): self.command(p, 'print("new")')
            self.assertEqual((p/'out').read_bytes(), b'keep')

    def test_spawn_failure_retains_terminal_row(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            with self.assertRaises(m.CommandFailure) as failure:
                m.run(['/missing/bounded-command'],cwd=p,env={},stdout=p/'out',stderr=p/'err',timeout=1,stream_maximum=1)
            self.assertIsNone(failure.exception.result['exitCode'])
            self.assertFalse(failure.exception.result['captureComplete'])

    def test_detached_pipe_holder_closes_transport_before_loop_exit(self):
        # The detached child is self-terminating. It models a separately owned
        # daemon's inherited pipe: helper must close its own transport, never
        # kill that other process group or accept canceled capture as complete.
        code='import os,time;pid=os.fork();(os.setsid(),time.sleep(.6),os._exit(0)) if pid==0 else time.sleep(10)'
        with tempfile.TemporaryDirectory() as d, warnings.catch_warnings(record=True) as observed:
            warnings.simplefilter('always',ResourceWarning)
            with self.assertRaises(m.CommandFailure) as failure:
                self.command(Path(d),code,timeout=.05,cleanup_seconds=.1)
            result=failure.exception.result
            self.assertTrue(result['processTransportClosed'])
            self.assertTrue(result['groupAbsent'] and result['streamsJoined'])
            self.assertFalse(result['captureComplete'])
            gc.collect()
            self.assertFalse(any('unclosed transport' in str(w.message) for w in observed))


if __name__ == '__main__': unittest.main()
