import unittest
import windows_public_fixture as m

# Synthetic public output, not a recorded device/Windows execution.
PRX = r'C:\fixture\libSceAgcDriver.prx'
SOURCE = '0123456789abcdef'

def row(fixture):
    return dict(name=fixture, status='passed', exit_code=0, own_tree_stopped=True,
                timed_out=False, stdout_discarded=0, stderr_discarded=0)

def output(fixture, newline='\n'):
    text = newline.join('PASS ' + name for name in m.case_names(fixture)) + newline
    text += 'TOTAL_PASS ' + str(m.COUNTS[fixture]) + newline
    return text

IMPORTED_MARKERS = ('ACTUAL_DRIVER_PATH ' + PRX + '\n'
                    'ACTUAL_DRIVER_CACHE_SOURCE_VERSION ' + SOURCE + '\n'
                    'ACTUAL_DRIVER_CACHE_FORMAT 22\n')

class Controls(unittest.TestCase):
    def check(self, fixture=m.STANDALONE, stdout=None, stderr=None, result=None, **pins):
        if stdout is None: stdout = output(fixture)
        if stderr is None: stderr = IMPORTED_MARKERS if fixture == m.IMPORTED else ''
        if result is None: result = row(fixture)
        if fixture == m.IMPORTED:
            pins.setdefault('expected_prx_path', PRX)
            pins.setdefault('expected_cache_source', SOURCE)
        return m.validate_public_fixture(fixture, result, stdout, stderr, **pins)
    def test_standalone355_exact_names(self):
        self.assertEqual(self.check()['caseCount'], 355)
    def test_imported538_exact_names_path_and_cache(self):
        self.assertTrue(self.check(m.IMPORTED)['importedPathAndCacheVerified'])
    def test_crlf_output_is_valid(self): self.check(stdout=output(m.STANDALONE, '\r\n'))
    def test_stream_swap_preserves_complete_markers(self):
        self.check(m.IMPORTED, stdout=IMPORTED_MARKERS, stderr=output(m.IMPORTED))
    def test_standalone355_cannot_satisfy_imported538(self):
        with self.assertRaises(ValueError): self.check(m.IMPORTED, stdout=output(m.STANDALONE))
    def test_imported538_cannot_satisfy_standalone355(self):
        with self.assertRaises(ValueError): self.check(stdout=output(m.IMPORTED))
    def test_missing_case_refused(self):
        name = m.case_names(m.STANDALONE)[0]
        with self.assertRaises(ValueError): self.check(stdout=output(m.STANDALONE).replace('PASS '+name+'\n', '', 1))
    def test_duplicate_case_cannot_replace_missing_case(self):
        names = m.case_names(m.STANDALONE)
        with self.assertRaises(ValueError): self.check(stdout=output(m.STANDALONE).replace('PASS '+names[1], 'PASS '+names[0], 1))
    def test_changed_order_refused(self):
        names = m.case_names(m.STANDALONE)
        text = output(m.STANDALONE).replace(names[0], '__temp__', 1).replace(names[1], names[0], 1).replace('__temp__', names[1], 1)
        with self.assertRaises(ValueError): self.check(stdout=text)
    def test_unknown_or_case_changed_name_refused(self):
        name = m.case_names(m.STANDALONE)[0]
        for replacement in (name+'_unknown', name.upper()):
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                self.check(stdout=output(m.STANDALONE).replace(name, replacement, 1))
    def test_missing_or_truncated_summary_refused(self):
        for replacement in ('', 'TOTAL_PASS 35', 'TOTAL_PASS 538'):
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                self.check(stdout=output(m.STANDALONE).replace('TOTAL_PASS 355', replacement))
    def test_duplicate_or_conflicting_summary_refused(self):
        for extra in ('TOTAL_PASS 355\n', 'TOTAL_PASS 538\n', 'TOTAL_PASS invalid\n'):
            with self.subTest(extra=extra), self.assertRaises(ValueError): self.check(stderr=extra)
    def test_marker_cannot_be_spliced_between_streams(self):
        text = output(m.STANDALONE); at = text.index('TOTAL_PASS 355') + len('TOTAL_PASS ')
        with self.assertRaises(ValueError): self.check(stdout=text[:at], stderr=text[at:])
    def test_nonzero_exit_and_invalid_exit_type_refused(self):
        for value in (1, -1, True, '0', None):
            with self.subTest(value=value), self.assertRaises(ValueError): self.check(result=dict(row(m.STANDALONE), exit_code=value))
    def test_timeout_ownership_or_discard_refused(self):
        for key, value in [('timed_out',True),('own_tree_stopped',False),('stdout_discarded',1),('stderr_discarded',1),('status','failed')]:
            with self.subTest(key=key), self.assertRaises(ValueError): self.check(result=dict(row(m.STANDALONE), **{key:value}))
    def test_missing_row_fields_refused(self):
        for key in row(m.STANDALONE):
            result = row(m.STANDALONE); del result[key]
            with self.subTest(key=key), self.assertRaises(ValueError): self.check(result=result)
    def test_unknown_or_wrong_fixture_name_refused(self):
        with self.assertRaises(ValueError): self.check(fixture='unknown')
        with self.assertRaises(ValueError): self.check(result=dict(row(m.STANDALONE), name=m.IMPORTED))
    def test_byte_stream_cap_refused(self):
        for text in ('x'*(m.STREAM_MAXIMUM+1), '\u20ac'*(m.STREAM_MAXIMUM//3+1)):
            with self.subTest(length=len(text)), self.assertRaises(ValueError): self.check(stderr=text)
    def test_four_known_skipped_names_are_exact_required_passes(self):
        self.assertEqual(len(m.KNOWN_SKIPPED_CASE_NAMES), 4)
        self.check(m.IMPORTED)
        for name in m.KNOWN_SKIPPED_CASE_NAMES:
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.check(m.IMPORTED, stdout=output(m.IMPORTED).replace('PASS '+name+'\n', '', 1))
    def test_unknown_skipped_unavailable_or_fail_refused(self):
        for extra in ('stage skipped\n', 'unavailable\n', 'FAIL bad\n', '[FAIL] bad\n', 'PASS unexpected_skipped_case\n'):
            with self.subTest(extra=extra), self.assertRaises(ValueError): self.check(m.IMPORTED, stderr=IMPORTED_MARKERS+extra)
    def test_duplicate_or_mutated_known_skip_case_refused(self):
        name = m.KNOWN_SKIPPED_CASE_NAMES[0]
        for extra in ('PASS '+name+'\n', 'PASS '+name+'_forged\n'):
            with self.subTest(extra=extra), self.assertRaises(ValueError): self.check(m.IMPORTED, stderr=IMPORTED_MARKERS+extra)
    def test_wrong_missing_duplicate_or_invalid_prx_path_refused(self):
        for markers in (IMPORTED_MARKERS.replace(PRX,r'C:\other\libSceAgcDriver.prx'), IMPORTED_MARKERS.replace('ACTUAL_DRIVER_PATH '+PRX+'\n',''), IMPORTED_MARKERS+'ACTUAL_DRIVER_PATH '+PRX+'\n', IMPORTED_MARKERS.replace(PRX,'relative.prx')):
            with self.subTest(markers=markers), self.assertRaises(ValueError): self.check(m.IMPORTED, stderr=markers)
        with self.assertRaises(ValueError): self.check(m.IMPORTED, expected_prx_path=None)
    def test_wrong_missing_duplicate_or_unpinned_cache_source_refused(self):
        line = 'ACTUAL_DRIVER_CACHE_SOURCE_VERSION '+SOURCE+'\n'
        for markers in (IMPORTED_MARKERS.replace(SOURCE,'fedcba9876543210'), IMPORTED_MARKERS.replace(line,''), IMPORTED_MARKERS+line):
            with self.subTest(markers=markers), self.assertRaises(ValueError): self.check(m.IMPORTED, stderr=markers)
        with self.assertRaises(ValueError): self.check(m.IMPORTED, expected_cache_source=None)
    def test_wrong_missing_duplicate_cache_format_refused(self):
        line = 'ACTUAL_DRIVER_CACHE_FORMAT 22\n'
        for markers in (IMPORTED_MARKERS.replace(line,'ACTUAL_DRIVER_CACHE_FORMAT 21\n'), IMPORTED_MARKERS.replace(line,''), IMPORTED_MARKERS+line):
            with self.subTest(markers=markers), self.assertRaises(ValueError): self.check(m.IMPORTED, stderr=markers)

if __name__ == '__main__': unittest.main()
