# Complete upstream refresh, 2026-10-12

AnyPS5 now uses the complete merged main branch at
[`a11c8f7f`](https://github.com/boykopovar/AnyPS5/commit/a11c8f7f70a0ed4e71504a89de69e8cdae687817),
including all **1,721 commits** after `c963432d`. This is a complete source
refresh, with the remaining local changes reconciled across 60 overlapping
files. The app still runs relinked Windows PE programs through Wine and FEX;
graphics follow Vulkan → MoltenVK → Metal.

Madeira main remains `48f97642`. Official FEX main and the latest monthly
release, FEX-2610, remain `14c92681`; the reconciled iOS-port baseline remains
`3bec2ac4`. These heads were queried again during this refresh. The existing
FEX ARM64EC bounds correction and local iOS integration remain applied. An
unchanged upstream head is not an omitted update. See [exact pins](UPSTREAMS.md).

## Reconciliation

The eleven active patches now describe the remaining local runtime, exception,
shader, audio, resource, pipeline and relinker behavior. The preceding eleven
patches are retained under `patches/anyps5/legacy-c963432d/` and are not applied
to the new pin. Fresh application matches all **2,130 source files**, including
the 227 files changed locally; complete reversal restores upstream bytes and
executable modes. All eleven nested dependency pins remain exact.

- The merged Apple fixes, including #1776 LDS spill, #1831 descriptor arrays
  and the now-merged #2015 image handling, come from the complete upstream
  snapshot. Local device-limit, typed-image, descriptor ownership and policy
  validation remain; duplicate implementations are removed.
- New upstream shader requests and the historical local request tails had
  overlapping version numbers. The current writer uses **request version 17**;
  disk-cache format **28** includes local policy and pipeline-layout identity.
  Historical local version 14/15 requests require the explicit
  `--legacy-ipad-v14-v15` replay mode. Old cache entries are rejected.
- Normal graphics-pipeline-library support remains available. An explicitly
  selected grouped-sample profile uses a separate device/cache/pipeline identity
  because its push layout differs. Pipe/bank XOR is retained alongside logical
  sample count; unsupported GPU transfer combinations fail rather than use
  incorrect addresses.
- Upstream single-sample depth clears are retained. Grouped depth/stencil paths
  keep their stricter guest-memory restrictions. This merge does not establish
  general guest Z/HTILE import, CPU refresh or writeback for every depth format.
- Protected memory, AVX/flags preservation, lazy allocation, save behavior and
  honest unsupported Audio3d errors remain. Deferred module initialization
  receives nonzero LoadStart arguments exactly once, including nested loads.
  Native thread teardown unbinds its wait-state pointer before releasing it.
- The HLE builder verifies the actual configured CMake target types and registered
  test inventory. It refuses an exported source folder that would inherit the
  parent repository's Git identity. Bundled dependencies are explicit; a prior
  HLE archive selects names only and supplies no old runtime binaries.

## Actual local checks

The fresh ARM64 host relinker and NID patcher build successfully. **95/95
registered relinker tests pass**, including Windows lifecycle, module identity,
direct Media discovery, malformed input and 16-KiB virtual section isolation.
Upstream's zero-tail trimming is tested without requiring an unnecessary
16-KiB raw file allocation.

Six freshly compiled native shader suites pass: placeholder policy, device
profile, request/cache identity and compatibility, unused barycentrics, LDS
CPU behavior, and extended public compilation. Graphics test source also passes
its separate syntax check. The build-helper and result-validator controls pass
**54 tests**. Failed initial attempts are recorded separately from these passes.

The fresh complete **47-library Windows HLE build compiles** with the selected
test executables. The raw-log fixture passes twelve cases; the next fixture,
`windows_exception_tests`, terminates with an unhandled `through runtime frames`
exception from `std::call_once`. The supplied compiler runtime DLLs carry native
SEH tables while our custom unwinder reads DWARF metadata; a bounded diagnostic
now identifies the first missing frame in `libwinpthread`'s `pthread_once`, at
RVA `0x851d`. Its native unwind entry has no handler flags, but the implementation
still holds a mutex and a stack cleanup-list node across the callback. Merely
walking past that frame would lose required cleanup. The isolated diagnostic
compiles and links, preserves the original providers, captures exit 3 and joins
its Wine prefix; it does not repair the failure.
[First missing-frame observation](evidence/windows-compiler-once-first-miss-20261012.json).
The fixture
and cleanup assertions remain enabled. Full linked-runtime qualification, the
new prepared game package, Windows GPU run and iPad game run remain separate
steps. The earlier 54-case runtime and 538-case
production-driver results belong to the preceding source and are not reused as
results for this update.

## MiniGolf and the physical iPad

Native59 is installed. A fresh 45-second synthetic CPU diagnostic captures an
unhandled native read fault with PC/LR equal to `2` after context restoration.
The main thread waits in Wine's server path. Both valid ownership samples show
a free allocator lock and zero native critical depth; the earlier Native57 lock
spin does not establish this failure's cause. The causative write is not yet
proved. The collector restores the original library and protected metadata,
closes its own process and releases the device. [Actual observation](evidence/native59-owner-sampler-observation-20261012.json).

MiniGolf is **not yet demonstrated playable**. Boot reports for other titles on
other CPU/OS/GPU paths do not qualify this iPad's Wine/FEX context delivery or
MiniGolf's Unity rendering. The next checks are the fresh linked runtime, native
Windows comparison, corrected iPad CPU delivery, then course rendering and a
complete offline course. No graphics or exception guard is disabled to claim
success. [MiniGolf records](MINIGOLF.md).

All builds and tests run locally. GitHub Actions remain disabled. Game data,
pairing and raw diagnostic captures stay outside Git.

The current patch stack also updates four write-tracking mappings for the new
explicit GPU argument, fixes one renamed filesystem-test variable without
changing its timestamp comparison, and moves the optional 60-Hz vblank wait to
TimedWait’s own absolute nanosecond clock. The normal rational vblank path and
stop/failure predicate stay intact. The HLE helper resolves the Wine executable
before changing directories for tests; five executable-path controls cover that
repair. [Experimental EC continuation snapshot](../experimental/native-ec-continuation/README.md) preserves the narrower FEX candidate and its
local controls; it remains outside the default patch series.

The experimental FEX continuation candidate now also completes the production
build: 187 ARM64EC objects, 50 fresh native objects and nine retained FEXCore
members. All 104 native continuation commands join successfully; the old frame
size/offsets, 30 exports, 12-DLL import symbols and native public symbol contract
remain unchanged. The original failed import postcondition and terminal capture
are retained separately. A fresh Native60 app now compiles and passes local
signature/provenance verification with its new FEXBridge object and 47 actual
FEX headers, all nine native archives, retained Native59 helpers/profiles and
matching dSYM UUID. The same-app parser successor fixes Swift's four-record
Make dependency readback without rebuilding or resigning. Independent readback
checks all 382 app files and 13 completed verifier command outputs. Native60 is
built and signed, but not installed or CPU-qualified. It retains the older
installed Native59 HLE bytes rather than substituting the new a11c runtime.
These results do not establish the cause of Native59's fault or repair
MiniGolf's startup.
[Actual native build](evidence/native-ec-continuation-native-build-20261012.json),
[signed Native60 observation](evidence/native60-local-build-signature-20261012.json).
