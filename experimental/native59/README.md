# Experimental Native59 source checkpoint

This preserves authored public source outside the default patch series. It is
an opt-in experimental checkpoint, not an accepted CPU repair. Native58's
Original50 observation did not pass; Native59 is an ownership diagnostic.
Neither source checks, native controls, signing nor installation establish CPU,
GPU, MiniGolf startup or gameplay acceptance. Consult the dated public evidence
for actual runtime outcomes.

The existing default series still reproduce their canonical source trees. The
Wine checkout's 374 added lines are already covered by default patches 0001–0004;
the new critical-suspend implementation was built from separate isolated source.

Apply the following additions only to a disposable checkout with all existing
default patches applied, and apply all three project series together:

| Repository | Additional patches, in order |
| --- | --- |
| FEX, `14c92681` | `patches/fex/0004-ios-loop-top-register-reconstruction.patch`, then `0005-ios-native-critical-suspend.patch` |
| Wine, `257f271c` | `patches/wine/0005-ios-native-critical-suspend.patch` |
| Madeira, `48f97642` | `patches/madeira/0052-ios-native-critical-suspend.patch`, then `0053-bounded-critical-owner-sampler.patch` |

The first four patches are byte-identical to the reviewed Native58 proposal. The
fifth is a repository-relative diff of the exact four Native59 diagnostic source
files. Full upstream IDs, source hashes and original source derivation are in
`source-manifest.json`; no private input inventories or assets are included.

The private self-only query is class `0x7fff4152`, 40 bytes, magic `0x41504353`,
version 1. Wine owns native TEB identity, balanced depth/token state and the full
previous SIGUSR1 mask. The outer mask/registration precede protected locks;
unregistration and exact mask restoration follow release. The server appends
`ios_fex_critical_scope` and protocol 931 without changing earlier opcodes or
the maximum request union. Effective wait deferral is restricted to an exact
same-process, unacknowledged private pending context and its current generation;
logical suspension counts remain. ACK, cancellation, debugger/process/foreign
origin and startup waits retain precedence. The FEX callback table preserves
the guard across paired callbacks and retires rows on own thread teardown.
Abnormal exit while holding the earlier Unmap lock is not established repaired.

Rebuild generated protocol consumers together: `thread.c`, `request_ios.c`,
`trace.c`, native `server_ios.c` and `thread_ios.c` embed the changed protocol or
tables. The generated request, trace and handler headers are included in the
patch. Rebuild the complete affected FEX graph; an older Module-only archive
reuse proof is insufficient. Native ARM64 guard activation remains disabled by
design; the active query is the ARM64EC bridge. No lock is disabled.

Native59's extra flag `MADEIRA_CRITICAL_OWNER_SAMPLER=1` augments the existing
bounded sampler. It checks native critical bytes and RPM owner/depth against an
exact own image/mapping, with at most 200 loader nodes, 512 map entries and 256
printed ownership rows. It logs after attempted Mach resume and refuses a failed
resume. With the flag on, earlier paused watchdog logging and the RIP profiler
are skipped. The observer perturbs scheduling; double reads are not a global
atomic snapshot, and ownership consistency alone is not a proved wait cycle.
No arbitrary resume, timeout, context/PC rewrite or exception bypass is added.

Source-only roundtrip and extraction, from the repository root:

```sh
python3 -I -B experimental/native59/check-sources.py --source-root . \
  --extract-to build/native59-public-control-sources
python3 -I -B -m unittest discover -s experimental/native59 -p 'test_checkpoint.py'
python3 -I -B -m unittest discover -s experimental/native59/own-window \
  -p 'test_*locks.py'
python3 -I -B -m unittest discover -s experimental/native59/own-window \
  -p 'test_swift_modulecache.py'
```

The source check uses a disposable tree, never edits canonical upstreams and
does not compile. Extraction imports the actual hashed production helper,
handler, ACK/origin/pending bodies and FEX bridge/templates/callbacks into thin
test adapters. It also retains the exact intermediate LoopTop Module source.

Explicit local native controls, after extraction, can be compiled by a caller
that owns its process/output budget. These commands are examples, not run on
import or by the source checker:

```sh
cc -std=c11 -pthread -Wall -Wextra \
  build/native59-public-control-sources/wine/native-harness.c \
  -o build/native59-public-control-sources/wine/native-harness
build/native59-public-control-sources/wine/native-harness
clang++ -std=c++20 -DFEX_IOS_HOST -DARCHITECTURE_arm64ec \
  -I build/native59-public-control-sources/fex/include \
  build/native59-public-control-sources/fex/test-native-critical.cpp \
  -o build/native59-public-control-sources/fex/test-native-critical
build/native59-public-control-sources/fex/test-native-critical
cc -std=c11 -Wall -Wextra \
  build/native59-public-control-sources/owner/native-harness.c \
  -o build/native59-public-control-sources/owner/native-harness
build/native59-public-control-sources/owner/native-harness
```

The retained Wine suite has 132 real pthread-mask/production-server helper
checks. The FEX suite has 24 normal cases, 23 deliberate fatal modes and three
non-iOS variants with three cases each. The owner harness has 32 cases. These
are local helper/adapter tests; they do not run an end-to-end server queue,
cross-thread protected lock cycle or device context capture. LoopTop native
14+14 and seven mutation controls are retained under `controls/loop-top`; pass
its checker explicit intermediate source and patch paths. The header fixture
is from the public FEX PE image, not a game or captured private context.

`own-window/` preserves the authored Swift XCTest source, project, bounded child,
live compiler-cache helper, direct compile/link recipe and linked-method/SDK
assembly inspection code. Only the physical device literal is redacted. The
own-element test requires foreground state immediately before and after one
still; it never activates the app and does not prove its internal PID, scene or
GPU progress. The corrected linked-method contract checks a defined method,
own-class selector, ObjC thunk and its ARM64 branch to that method. The previous
raw-symbol spelling check remains visibly present in the historical direct
recipe; successful compile/link was qualified separately, not relabeled.

Historical recipe/test sources under `own-window/archive-tests`,
`linked_artifact.py` and `assemble_retained.py` reference separately retained
local source-review and artifact receipts. Those receipts, SDK binaries,
signed apps and outputs are not published here. These are source preservation,
not ready build or capture entrypoints from a fresh clone. The portable helper
tests omit only historical sibling-tree comparisons; their derivations are
recorded. There is no included signed/installed runner or owned remote XCTest
lifecycle adapter, so this checkpoint is not capture ready.

This directory does not alter default application behavior, shared-device
leases, network settings or GitHub Actions. Private game assets, raw diagnostic
requests/logs, pairing material, accepted provider maps and transport tokens
remain outside Git. Patch licensing follows the corresponding upstream; the
Wine native harness is LGPL-2.1-or-later, FEX controls GPL-3.0-or-later and Madeira
diagnostics retain GPL-3.0-or-later. Existing repository notices still apply.
