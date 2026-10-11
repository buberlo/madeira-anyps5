"""Validate the merged a11c/local Windows exception fixture's bounded streams.

The totals are derived from GuestRaiseException.cpp; no historical test result
is acceptance for this fixture. This module performs no runtime actions.
"""
import re

MODES = ('preserve', 'mutate', 'reset-avx')
COUNTS = {False: {False: 682, True: 782}, True: {True: 884}}
SKIP = 'Async AVX checks skipped: CPU feature or opt-in unavailable.'
RX = 'Private executable exception verified: deliveries=1 rip-in-owned-rx=1 joined=1 freed=1.'
PHASES = (
    'Context mutation verified: deliveries=1 joined=1 integer=1 vector=1 mxcsr=1',
    'Immediate startup exception verified: deliveries=50 joined=50',
    *(f'Lock wait exception verified: mode={mode} deliveries=10 joined=1'
      for mode in ('mutex', 'timed-mutex', 'rwlock')),
)
GPR_FLAGS = (0x202, 0x206, 0x212, 0x216, 0x602, 0xa03, 0xad7, 0xed7)


def _need(value, message):
    if not value:
        raise ValueError(message)


def validate(row, stdout, stderr, *, preserve_async):
    _need(type(preserve_async) is bool, 'Explicit fixture profile required')
    _need(row.get('status') == 'passed' and type(row.get('exit_code')) is int
          and row['exit_code'] == 0 and row.get('own_tree_stopped') is True
          and row.get('timed_out') is False
          and type(row.get('stdout_discarded')) is int and row['stdout_discarded'] == 0
          and type(row.get('stderr_discarded')) is int and row['stderr_discarded'] == 0,
          'Exit, capture or owned-child closure differs')
    _need(isinstance(stdout, str) and isinstance(stderr, str)
          and len(stdout.encode('utf-8')) <= 1048576
          and len(stderr.encode('utf-8')) <= 1048576,
          'Captured streams exceed the fixture bound')
    lines = (stdout + '\n' + stderr).replace('\r\n', '\n').splitlines()
    features = [line for line in lines if line.startswith('Native AVX feature')]
    _need(len(features) == 1 and features[0] in ('Native AVX feature available: 0', 'Native AVX feature available: 1'),
          'Exact native AVX feature row required')
    avx = features[0].endswith('1')
    _need(avx in COUNTS[preserve_async], 'Explicit AVX profile requires native AVX')
    count = COUNTS[preserve_async][avx]
    expected = f'All {count} exception deliveries verified; AVX={"verified" if preserve_async else "skipped"}; integer state verified.'
    summaries = [line for line in lines if 'exception deliveries' in line]
    _need(summaries == [expected], 'Exactly one source-derived delivery summary required')
    _need([line for line in lines if line.startswith('Private executable exception')] == [RX], 'Private RX ownership and cleanup result differs')
    for prefix, required in (('Context mutation', PHASES[:1]), ('Immediate startup exception', PHASES[1:2]), ('Lock wait exception', PHASES[2:])):
        _need([line for line in lines if line.startswith(prefix)] == list(required), 'Context/start/lock coverage differs')
    waits = [line for line in lines if line.startswith('Native wait')]
    expected_waits = [f'Native wait verified mode={mode} round={round} result={result}'
                      for mode, result in (('timeout', 258), ('signaled', 0)) for round in range(10)]
    _need(waits == expected_waits, 'Twenty ordered native wait results required')
    vectors = [line for line in lines if line.startswith('Async vector')]
    _need(vectors == ([f'Async vector checks=64 mode={mode} errors=0' for mode in MODES] if preserve_async else []),
          'Exact asynchronous vector modes required')
    _need(lines.count(SKIP) == (0 if preserve_async else 1), 'Default opt-in skip differs')
    gprs = [line for line in lines if line.startswith('GPR checks')]
    _need(len(gprs) == 10, 'Ten ordered integer state results required')
    inputs = [(flags, 0) for flags in GPR_FLAGS] + [(0xed7, 0xcd5), (0x202, 0xcd5)]
    for line, (flags, mutation) in zip(gprs, inputs):
        match = re.fullmatch(r'GPR checks=15 errors=0 flags expected=([0-9a-f]+) context=([0-9a-f]+) restored=([0-9a-f]+) stack=([0-9a-f]+)/([0-9a-f]+)', line)
        _need(match is not None, 'Integer state row invalid')
        values = [int(value, 16) for value in match.groups()]
        _need(values[:3] == [flags & 0xcd5, flags & 0xcd5, (flags ^ mutation) & 0xcd5]
              and values[3] > 0 and values[3] == values[4], 'Integer flags or restored stack differ')
    checked = '\n'.join(line for line in lines if line not in (expected, SKIP))
    _need(not re.search(r'(?i)skipped|unavailable|\[FAIL\]|Delivery count: expected=|errors=[1-9]', checked),
          'Failure or unexpected skip present')
    return {'deliveries': count, 'nativeAvx': avx, 'preserveAsync': preserve_async,
            'contextAndLockDeliveries': 81, 'runtimeExecutionProvenByValidatorAlone': False}
