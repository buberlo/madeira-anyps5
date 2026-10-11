The Windows runner used one 538-case expectation for two different public shader fixtures. The standalone fixture's actual suite contains 355 cases; the separate imported-driver suite contains 538. The latest bounded Windows observation retained six passed prerequisites before the standalone count assertion failed. The imported-driver fixture, GPU fixtures and game were not reached in that observation.

`windows_public_fixture.py` checks the two named suites separately. It requires an exit-zero result, complete bounded capture, owned process closure, every exact case name in order and one exact summary. The imported fixture also requires the caller's independently bound loaded-PRX path and source-cache identity, with cache format 22. Four required imported-suite names contain `skipped`; only their exact PASS lines are excluded from the skip-word scan. They remain required at their exact ordered positions. Actual skip/unavailable/failure messages and unknown, missing, changed or duplicate names fail.

The validator reads captured strings and public case-name data only. It performs no process launch, file transfer, PRX loading, device access or security-settings change. Its returned validation result is not GPU/gameplay or overall 27-prerequisite acceptance. The caller must verify the executable, case-data file and runtime identities before calling it. This portable helper does not replace those provenance checks.

All 24 controls use synthetic output and synthetic runtime identities. They test both counts, ordering, truncation, conflicts, exit/capture/cleanup refusal, the four precise skip-name exceptions and loaded-path/cache gates. There are no private logs, provider hashes, transport tokens, asset paths or device identities in this directory.

Run from this directory:

```sh
python3 -B -m unittest discover -s . -p test_windows_public_fixture.py
```

This is a public source checkpoint of output validation. It has not caused a new Windows execution or any GPU/gameplay acceptance.
