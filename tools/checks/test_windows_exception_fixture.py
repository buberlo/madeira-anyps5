import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('new_exception_fixture', Path(__file__).with_name('windows_exception_fixture.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def output(preserve=True, avx=True):
    count = m.COUNTS[preserve][avx]
    lines = [f'Native AVX feature available: {int(avx)}', *m.PHASES]
    lines += [f'Native wait verified mode={mode} round={round} result={result}'
              for mode, result in (('timeout', 258), ('signaled', 0)) for round in range(10)]
    lines += [f'Async vector checks=64 mode={mode} errors=0' for mode in m.MODES] if preserve else [m.SKIP]
    for flags, mutation in [(f, 0) for f in m.GPR_FLAGS] + [(0xed7, 0xcd5), (0x202, 0xcd5)]:
        lines.append(f'GPR checks=15 errors=0 flags expected={flags & 0xcd5:x} context={flags & 0xcd5:x} restored={(flags ^ mutation) & 0xcd5:x} stack=1234/1234')
    lines += [m.RX, f'All {count} exception deliveries verified; AVX={"verified" if preserve else "skipped"}; integer state verified.']
    return '\n'.join(lines) + '\n'


class Fixture(unittest.TestCase):
    def setUp(self):
        self.row = dict(status='passed', exit_code=0, own_tree_stopped=True, timed_out=False, stdout_discarded=0, stderr_discarded=0)
        self.text = output()

    def reject(self, text=None, row=None, preserve=True):
        with self.assertRaises(ValueError):
            m.validate(row or self.row, '', self.text if text is None else text, preserve_async=preserve)

    def test_explicit_884_stderr(self):
        self.assertEqual(m.validate(self.row, '', self.text, preserve_async=True)['deliveries'], 884)
    def test_default_native_avx_782(self):
        self.assertEqual(m.validate(self.row, output(False), '', preserve_async=False)['deliveries'], 782)
    def test_default_non_avx_682(self):
        self.assertEqual(m.validate(self.row, '', output(False, False), preserve_async=False)['deliveries'], 682)
    def test_split_streams_crlf(self):
        lines = self.text.splitlines()
        self.assertEqual(m.validate(self.row, '\r\n'.join(lines[:6]), '\r\n'.join(lines[6:]), preserve_async=True)['deliveries'], 884)
    def test_old_803_cannot_pass_new_fixture(self): self.reject(self.text.replace('884 exception', '803 exception'))
    def test_old_default_701_rejected(self): self.reject(output(False).replace('782 exception', '701 exception'), preserve=False)
    def test_nonzero_exit(self): self.reject(row={**self.row, 'exit_code': 1})
    def test_boolean_exit(self): self.reject(row={**self.row, 'exit_code': False})
    def test_timeout(self): self.reject(row={**self.row, 'timed_out': True})
    def test_unjoined(self): self.reject(row={**self.row, 'own_tree_stopped': False})
    def test_discarded_stderr(self): self.reject(row={**self.row, 'stderr_discarded': 1})
    def test_stream_byte_bound(self): self.reject('é' * 524289)
    def test_duplicate_summary(self): self.reject(self.text + self.text.splitlines()[-1] + '\n')
    def test_truncated_summary(self): self.reject(self.text[:-10])
    def test_missing_lock_mode(self): self.reject(self.text.replace(m.PHASES[-1] + '\n', ''))
    def test_wrong_startup_count(self): self.reject(self.text.replace('deliveries=50 joined=50', 'deliveries=49 joined=49'))
    def test_missing_context(self): self.reject(self.text.replace(m.PHASES[0] + '\n', ''))
    def test_wrong_wait_result(self): self.reject(self.text.replace('round=0 result=258', 'round=0 result=0'))
    def test_duplicate_wait(self): self.reject(self.text.replace('round=1 result=258', 'round=0 result=258'))
    def test_vector_error(self): self.reject(self.text.replace('mode=mutate errors=0', 'mode=mutate errors=1'))
    def test_unknown_vector(self): self.reject(self.text.replace('mode=reset-avx', 'mode=other'))
    def test_cross_profile(self): self.reject(output(False))
    def test_gpr_stack_and_flags(self):
        for text in (self.text.replace('stack=1234/1234', 'stack=1234/5678'), self.text.replace('context=0', 'context=1')): self.reject(text)
    def test_rx_and_unexpected_skip(self):
        self.reject(self.text.replace('freed=1', 'freed=0'))
        self.reject(self.text + 'Unexpected checks skipped\n')


if __name__ == '__main__': unittest.main()
