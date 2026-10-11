This experimental checkpoint preserves the exact authored opt-in Windows
DWARF lookup diagnostic and its local execution orchestration. It is separate
from the normal eleven-patch AnyPS5 stack. No exception repair or native PE
frame skipping is implemented or qualified.

`trace.patch` applies to the saved `source/Unwind.before.cpp` at the current
AnyPS5 libc path. `source/Unwind.cpp` is the exact result. The companion raw
output header is retained public source. The flag is off by default; only the
exact value `APS5_UNWIND_MISS_TRACE=1` records a lookup miss. It caps process-wide
records at eight, each with a 1,024-byte stack buffer, bounded module/section
inspection and one best-effort stderr write. LastError and normal failure
returns are preserved. RtlLookupFunctionEntry reads metadata only.

`snapshot/` holds exact repository-relative source snapshots of the authored
recipe extractor, source-copy preparation, bounded execution wrapper and nine
injected controls. They depend on an explicit private local build recipe and
its provider maps, which are deliberately excluded. These snapshots are not
a portable one-command build or a current runtime authorization. The shared
public process helper remains `tools/checks/bounded_local_process.py`.

The actual local recipe replaces only Exports.cpp.obj (libc's amalgamation
includes Unwind.cpp), reuses 45 exact current objects, links/renames a fresh
libc and observes the existing exception fixture for at most 15 seconds.
The runner retains nonzero test exits, uses own-group bounded capture and
graceful/timeout-only owned-prefix closure, and never accepts a runtime result.
Its source/control tests do not execute Wine or a compiler.

`snapshot/attempt2/` separately preserves the narrow setup-lifetime successor:
live-only FileNotFoundError tolerance under the own generated prefix, strict
static/provider and post-join inventories, fresh fourteen-copy output, and
explicit subprocess transport close while its event loop remains alive.
Capture cancellation remains a failure. Its 22 controls comprise thirteen
injected/source controls and nine tiny real POSIX helper controls, including
a self-terminating detached pipe holder; no Wine/compiler execution is claimed
by those tests. The original helper and wrapper snapshots remain unchanged.

The source preservation tests here are portable Python tests, not native
unwind, compiler, CPU, GPU, device or gameplay qualification. They verify the
exact saved bodies, diagnostic limits and unchanged exception machinery.
Run `python3 -I -B -m unittest discover -s experimental/unwind-first-miss -p
'test_checkpoint.py'` from the repository root.

The known runtime boundary remains unresolved: native Winpthreads pthread_once
can hold a mutex and a manually registered TLS cleanup entry without a Windows
unwind handler. Handler-free native frame walking alone would bypass that
cleanup. A correctness repair must preserve caller destructors, same-flag
retry after a throw, single successful completion and concurrent waiter wakeup.
This checkpoint does not assert that such a repair exists.

The second actual local diagnostic completed on 2026-10-12. Its first missing
DWARF lookup was `libwinpthread-1.dll` RVA `0x851d`, the callback-return lookup
inside the native `pthread_once` range `0x8469..0x8599` (end exclusive). The
record showed `.pdata`/`.xdata` present, `.ehfram`/`.ehmeta` absent, native unwind
RVA `0x117e4`, version 1 and flags 0. The exception fixture still terminated
with exit 3 and `through runtime frames`; this is diagnosis, not a repaired or
accepted runtime. The three isolated compile/link/section commands exited zero;
all five command captures completed without cleanup errors, the own prefix
joined gracefully with exit zero, and original providers/copied carriers were
unchanged. The earlier setup failure and its sources remain retained separately.

No private assets, requests, provider inventories, captured logs, addresses,
transport credentials, device bindings, SDK binaries or compiler products are
included. Local diagnostic execution and any later production change require
their own reviewed concrete inputs and results.
