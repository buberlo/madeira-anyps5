# Current PRX qualification source snapshot

These two files are byte-identical snapshots of the reviewed local executor and its tests. The reviewed origin is `build/current-prx-runner-proposal`; its 28 controls passed independently (8 bounded child-process controls and 20 pure/injected executor controls). No Wine, compiler, GPU, device, or game qualification is claimed by this checkpoint.

The snapshot preserves the exact execution behavior. It depends on the separate local current-PRX recipe, generated current sources, Winlibs tools, completed HLE archive/provenance, and locally retained shader requests under `build/anyps5-full-main-update-20261012`. Those private inventories, requests, binaries, proof maps, and credentials are intentionally excluded. The generic bounded process helper and its tests are public at `tools/checks/bounded_local_process.py` and `tools/checks/test_bounded_local_process.py`.

This directory is a source checkpoint, not a portable qualification package. Do not invent missing recipe/review files or accepted results. Use the original held local proposal for preparation/execution. Its strict completed-HLE gate remains blocked by the actual Windows exception test failure until a genuine repaired full build passes and exports its qualified archive. A snapshot location has no source-review file and cannot prepare an execution as-is.

The preserved executor verifies current cache format 28, exact ordered standalone 355 and imported 538 cases, null 12, distinct-path rejection, and nine explicit legacy-local 14/15 to current 17 replays with complete schema-2/layout/SPIR-V equivalence. It retains bounded owned-child/prefix cleanup and source/runtime closure. Every actual plan, output, private request, and receipt remains local and ignored.

No snapshot test is advertised as self-contained: `test_runner.py` loads the held local recipe and includes a read-only check of its nine small retained requests. With those original local inputs present, the original proposal README describes the exact no-write test commands. This checkpoint makes no fresh execution claim.
