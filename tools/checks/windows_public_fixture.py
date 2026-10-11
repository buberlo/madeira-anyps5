"""Validate bounded public shader-fixture output; performs no runtime operation."""
import json
import ntpath
from pathlib import Path
import re

STANDALONE = 'agc_unused_barycentric_tests'
IMPORTED = 'agc_actual_driver_public_tests'
COUNTS = {STANDALONE: 355, IMPORTED: 538}
STREAM_MAXIMUM = 1048576
CACHE_FORMAT = 28
KNOWN_SKIPPED_CASE_NAMES = (
    'optional_groups_skipped_complete_pair_retains_initialized_output',
    'optional_groups_skipped_complete_pair_output_not_consumed',
    'optional_groups_skipped_uninitialized_result_unconsumed_on_that_path',
    'optional_groups_skipped_uninitialized_result_consumed_after_join',
)
PASS = r'(?m)^PASS ([^\r\n]+)\r?$'

def require(value, message):
    if not value:
        raise ValueError(message)

def case_names(fixture):
    require(fixture in COUNTS, 'Exact public fixture name required')
    value = json.loads(Path(__file__).with_name('public_shader_cases.json').read_text())
    names = value[fixture]
    require(isinstance(names, list) and len(names) == len(set(names)) == COUNTS[fixture]
            and all(isinstance(n, str) and re.fullmatch('[A-Za-z0-9_]+', n) for n in names),
            'Complete unique public case contract required')
    return names

def windows_path(value):
    require(isinstance(value, str) and re.match(r'^[A-Za-z]:[\\/]', value)
            and not any(c in value for c in ('\r', '\n', '\x00')), 'Absolute local Windows path required')
    return ntpath.normcase(ntpath.normpath(value))

def validate_public_fixture(fixture, row, stdout, stderr, *,
                            expected_prx_path=None, expected_cache_source=None):
    """Check captured results; the caller must bind the executable and case file.

    For the imported fixture, the caller supplies its independently verified PRX
    path and source-cache identity. This helper does not inspect or load a PRX.
    """
    expected = case_names(fixture)
    require(isinstance(row, dict) and row.get('name') == fixture and row.get('status') == 'passed'
            and type(row.get('exit_code')) is int and row['exit_code'] == 0
            and row.get('own_tree_stopped') is True and row.get('timed_out') is False
            and type(row.get('stdout_discarded')) is int and row['stdout_discarded'] == 0
            and type(row.get('stderr_discarded')) is int and row['stderr_discarded'] == 0,
            'Successful exit, complete capture and owned process closure required')
    require(isinstance(stdout, str) and isinstance(stderr, str)
            and len(stdout.encode('utf-8')) <= STREAM_MAXIMUM
            and len(stderr.encode('utf-8')) <= STREAM_MAXIMUM,
            'Captured stream outside one MiB bound')
    text = stdout + '\n' + stderr
    failure_text = text
    if fixture == IMPORTED:
        for name in KNOWN_SKIPPED_CASE_NAMES:
            require(name in expected, 'Required named optional-group case missing')
            failure_text = re.sub(r'(?m)^PASS ' + re.escape(name) + r'\r?$', '', failure_text)
    require(not re.search(r'(?im)^FAIL |\[FAIL\]|skipped|unavailable', failure_text),
            'Failure or unexpected skip/unavailable result')
    require(re.findall(PASS, text) == expected, 'Ordered public case names differ')
    require(len(re.findall(r'(?m)^TOTAL_PASS [^\r\n]*\r?$', text)) == 1
            and len(re.findall(r'(?m)^TOTAL_PASS ' + str(COUNTS[fixture]) + r'\r?$', text)) == 1,
            'One exact public-case summary required')
    if fixture == IMPORTED:
        expected_path = windows_path(expected_prx_path)
        require(isinstance(expected_cache_source, str) and re.fullmatch('[0-9a-f]{16}', expected_cache_source),
                'Pinned source-cache identity required')
        paths = re.findall(r'(?m)^ACTUAL_DRIVER_PATH ([^\r\n]+)\r?$', text)
        require(len(paths) == 1 and windows_path(paths[0]) == expected_path, 'Loaded PRX path differs')
        for marker, value in [('ACTUAL_DRIVER_CACHE_SOURCE_VERSION', expected_cache_source),
                              ('ACTUAL_DRIVER_CACHE_FORMAT', str(CACHE_FORMAT))]:
            rows = re.findall(r'(?m)^' + marker + r' [^\r\n]*\r?$', text)
            require(len(rows) == 1 and len(re.findall(r'(?m)^' + marker + ' ' + re.escape(value) + r'\r?$', text)) == 1,
                    'Imported driver cache identity differs')
    return {'fixture': fixture, 'caseCount': COUNTS[fixture], 'orderedNamesVerified': True,
            'importedPathAndCacheVerified': fixture == IMPORTED}
