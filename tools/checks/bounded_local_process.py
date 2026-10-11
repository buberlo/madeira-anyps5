"""Bounded POSIX local child capture with an owned process-group lifetime.

No command is launched on import. Callers supply exact argv, cwd, environment,
fresh stream paths and their own live resource guard. No Wine/device policy or
private fixture inventory belongs in this reusable helper.
"""
import asyncio
import os
from pathlib import Path
import signal
import time


class CommandFailure(RuntimeError):
    def __init__(self, message, result):
        super().__init__(message)
        self.result = result


def group_exists(pgid):
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False


async def _run(argv, *, cwd, env, stdout, stderr, timeout, stream_maximum,
               guard, cleanup_seconds):
    if os.name != 'posix' or not argv or not Path(argv[0]).is_absolute():
        raise ValueError('Absolute executable and POSIX owned process group required')
    if timeout <= 0 or cleanup_seconds <= 0 or stream_maximum <= 0:
        raise ValueError('Positive timeout, cleanup and stream bounds required')
    streams = [Path(stdout), Path(stderr)]
    if streams[0] == streams[1] or any(p.exists() or p.is_symlink() for p in streams):
        raise ValueError('Two distinct fresh capture files required')
    result = {'argv': list(map(str, argv)), 'exitCode': None, 'timedOut': False,
              'stdoutBytes': 0, 'stderrBytes': 0, 'stdoutDiscarded': 0,
              'stderrDiscarded': 0, 'directChildJoined': False,
              'groupAbsent': False, 'streamsJoined': False, 'captureComplete': False,
              'cleanupErrors': []}
    child = None
    tasks = []
    handles = []
    error = None
    started = time.monotonic()
    try:
        guard()
        handles = [p.open('xb') for p in streams]
        child = await asyncio.create_subprocess_exec(*map(str, argv), cwd=cwd, env=env,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                    start_new_session=True)
        # start_new_session establishes this exact PGID. Keep it after leader exit.
        pgid = child.pid
        result.update(pid=child.pid, processGroup=pgid)

        async def drain(pipe, handle, name):
            while True:
                data = await pipe.read(65536)
                if not data:
                    return
                left = max(0, stream_maximum - result[name + 'Bytes'])
                handle.write(data[:left])
                handle.flush()
                result[name + 'Bytes'] += min(left, len(data))
                result[name + 'Discarded'] += max(0, len(data) - left)
                if len(data) > left:
                    raise RuntimeError(name + ' exceeds live capture quota')

        tasks = [asyncio.create_task(drain(child.stdout, handles[0], 'stdout')),
                 asyncio.create_task(drain(child.stderr, handles[1], 'stderr'))]
        deadline = started + timeout
        while child.returncode is None or not all(t.done() for t in tasks):
            for task in tasks:
                if task.done() and not task.cancelled() and task.exception():
                    raise task.exception()
            if time.monotonic() >= deadline:
                result['timedOut'] = True
                raise TimeoutError('Owned command deadline exceeded')
            guard()
            await asyncio.sleep(0.05)
        guard()
    except BaseException as caught:
        error = caught
    finally:
        if child is not None:
            # Descendants may outlive the direct leader and retain capture pipes.
            # Terminate only the session/group created above, never a global tool.
            for sig in (signal.SIGTERM, signal.SIGKILL):
                try:
                    if group_exists(pgid):
                        os.killpg(pgid, sig)
                except OSError as caught:
                    result['cleanupErrors'].append('group signal: ' + repr(caught))
                if sig == signal.SIGTERM:
                    await asyncio.sleep(0.05)
            try:
                await asyncio.wait_for(child.wait(), cleanup_seconds)
                result['directChildJoined'] = True
                result['exitCode'] = child.returncode
            except BaseException as caught:
                result['cleanupErrors'].append('direct child join: ' + repr(caught))
            if tasks:
                try:
                    await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), cleanup_seconds)
                except BaseException as caught:
                    result['cleanupErrors'].append('stream join: ' + repr(caught))
                finally:
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                    await asyncio.gather(*tasks, return_exceptions=True)
                    result['streamsJoined'] = all(t.done() for t in tasks)
            until = time.monotonic() + cleanup_seconds
            while group_exists(pgid) and time.monotonic() < until:
                await asyncio.sleep(0.05)
            result['groupAbsent'] = not group_exists(pgid)
            if not result['groupAbsent']:
                result['cleanupErrors'].append('owned process group still exists')
        for handle in handles:
            handle.close()
        result['elapsedSeconds'] = time.monotonic() - started
        result['captureComplete'] = bool(error is None and result['directChildJoined']
            and result['groupAbsent'] and result['streamsJoined']
            and not result['cleanupErrors'] and not result['stdoutDiscarded']
            and not result['stderrDiscarded'])
    if error is not None or not result['captureComplete']:
        result['error'] = type(error).__name__ + ': ' + str(error) if error else 'Incomplete owned command closure'
        raise CommandFailure(result['error'], result) from error
    return result


def run(argv, *, cwd, env, stdout, stderr, timeout, stream_maximum,
        guard=lambda: None, cleanup_seconds=3):
    """Capture both streams live, kill/join own descendants, return truthful row.

    A nonzero ordinary exit is returned for the caller's exact exit predicate.
    Timeout/quota/resource/capture/cleanup failure raises CommandFailure carrying
    the terminal observation. Discarded data never becomes a successful result.
    """
    return asyncio.run(_run(argv, cwd=cwd, env=env, stdout=stdout, stderr=stderr,
                           timeout=timeout, stream_maximum=stream_maximum,
                           guard=guard, cleanup_seconds=cleanup_seconds))
