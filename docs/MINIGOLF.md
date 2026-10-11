# 3D MiniGolf — PPSA03647

Version **01.000.000** uses a private decrypted twelve-ELF dump. The target
remains a complete offline single-player course with touch input, sound and
save/load, without an initial FPS threshold. A rendered course and completed
stroke are not established.

## Current full upstream refresh, 2026-10-12

The complete AnyPS5 source is now pinned at **`0a8b1d32`**, including all
1,735 merged commits after `c963432d` and Apple fixes #1776/#1831/#2015.
All seventeen local patches apply and reverse exactly. Both the canonical
checkout and actual build checkout match all 2,137 source entries and eleven
initialized, clean dependency trees. Madeira main and official FEX main/
FEX-2610 were already current; the FEX iOS port and #6021 bounds repair remain.
[Exact source and scoped results](evidence/anyps5-0a8b-source-integration-20261012.json),
[technical reconciliation](UPSTREAM-REFRESH-20261012.md).

The new typed interpolation fallback repairs a concrete integration conflict:
an unsafe fixed-function replacement now reaches upstream's exact barycentric
emulator. It catches only the specific original-instruction proof failure;
wave, BDA, format, capability and resource failures remain errors. All six
fresh native shader suites pass. Their 355/538 public profiles combine direct
proof checks with full compilation of admitted profiles; they do not claim
that every negative profile compiles. The complete ShaderMemory fixture also
passes, including the new sRGB depth-comparison checks.

The full 47-library build and all 49 selected test executable targets compile.
The runtime attempt passes 28 default targets, including memory and exception
tests, before Graphics detects an incorrect thin-layout dispatch for 3D
`SW_64KB_D_X` textures. The independent Addrlib size and address fixtures remain
unchanged. Patch 0017 repairs the production dispatch; a fresh complete build
and runtime test run is in progress.
[Actual attempt](evidence/anyps5-latest16-full-hle-attempt-20261012.json).
The tests use the explicitly probed `0x7400000000` test-host arena.
That result does not prove fixed-address allocation on the iPad. Stale graphics
fixtures were corrected for real tiled MSAA backing, upstream stencil clears
and cross-block XOR coordinates. Production memory/graphics validations stay
active. No package prepared from older tools is relabelled as this update.

**Native59 remains the installed host.** Its bounded CPU diagnostic recorded
an unhandled read at address 2 with PC/LR=2 after context restoration. The
observed allocator lock was free; the causative write remains unproved.
[Actual device observation](evidence/native59-owner-sampler-observation-20261012.json).

Native60 is built and signed with an experimental EC continuation repair and
matching FEXBridge/translator/native inputs. It deliberately retains the older
HLE payload to isolate CPU behavior. Its preserving updater refused before
installation when Native59 reappeared during preflight. No accepted Native60
installation, Original50 delivery result or MiniGolf execution is claimed.
The next device steps are a preserving update, the complete original 50-delivery
probe, all CPU phases, then GPU and game testing.
[Candidate and build boundaries](../experimental/native-ec-continuation/README.md).

## Preceding package and Windows results

The preceding source was complete AnyPS5 through `c963432d` with eleven local
patches, including LDS spill, complete descriptor-array snapshots and typed
image fallback. Fresh native CPU tests pass. The new 47-library Windows runtime
passes 54 host cases under local Wine; its actual production PRX passes 538
ordered public cases, nine complete shader replays and twelve null-pixel cases.
All nine SPIR-V modules and binding layouts match the earlier qualified outputs
and pass independent validation. These results qualify CPU preparation, not
native Windows GPU or iPad gameplay.
[Apple implementation and limits](APPLE-GPU-20261011.md),
[fresh runtime evidence](evidence/apple-gpu-runtime-cpu-20261011.json).

The new private package is now **prepared, unexecuted** with those fresh tools
and libraries: twelve relinked ELFs, 47 NID-patched HLE implementations, three
compiler DLLs and all 3,186 guest NIDs are covered. An independent second pass
over all 47 raw libraries reproduces their packaged patched bytes. Preparation
uses twelve verified retained decrypted inputs and 101 unchanged assets; it
does not claim equality with every file in the original 127-file download.
Independent disk readback verifies all 180 package files and finds zero
unresolved guest NIDs, native imports or forwarders.
The earlier packages remain unchanged. Windows has now verified this package
and begun its prerequisites; the new game runtime has not yet started. It has
not been imported into the iPad library.
[Preparation record](evidence/apple-gpu-minigolf-package-prepared-20261011.json).

Windows run 10 remains the latest actual game run: its preceding driver passes
all 26 prerequisites, then aborts at a strict interpolation guard at PC 76 after
7.1236738 seconds. The later six-patch PC 76 driver and current eleven-patch
runtime have separate local CPU qualification; neither has a new native
Windows game result. The preceding Native57 installation passed protected-data
preservation, but its first Continuing50 observation does not establish the
required deliveries despite JIT activation. Native58 is now installed and closed
with accessible protected-data preservation accepted. Its first actual device
probe activates JIT and begins Continuing50, but does not complete within 120
seconds. Fresh CPU qualification still precedes import and rendering.
[Historical PC 76 qualification](evidence/minigolf-pc76-qualification-20261011.json),
[latest native Windows game result](evidence/anyps5-c963-windows-run10-20261010.json),
[accepted Native57 installation](evidence/native57-preservation-accepted-20261011.json),
[accepted Native58 installation](evidence/native58-preservation-accepted-20261011.json),
[Continuing50 observation](evidence/native57-continuing50-observation-20261011.json).

The latest Windows prerequisite attempt, on 2026-10-11, verifies all 180 game
files and 259 payload files, excluding the manifest. Its first two recorded
prerequisites pass. The next captured fixture reports 803 exception deliveries,
correct integer state and 64 checks in each of three AVX modes. The runner stops
because its inherited validator still expects 553 deliveries. The third result
row is not recorded, and neither GPU tests nor the game start in this attempt.
The correction must distinguish the explicit-AVX 803-delivery branch from the
default 701-delivery branch, where async AVX is intentionally not opted in.
[Windows prerequisite attempt](evidence/apple-gpu-windows-prerequisite-attempt-20261011.json).

The corrected runner subsequently records three passing native Windows
prerequisites, including all 803 exception deliveries, 64 checks in each AVX
mode, private executable-page delivery and the native-wait checks. Each child
exits zero with complete output and closed owned processes. Application Control
then refuses the next child, `guest_memory_tests.exe`, before its result or
output is recorded. The default 701-delivery mode, GPU checks and game are still
unexecuted. A zero outer script exit only means this failure was caught and
returned; it does not qualify the reference run.
[Corrected Windows attempt](evidence/apple-gpu-windows-three-prerequisites-20261011.json).

A further Windows run passes six prerequisites, including all 36 memory checks,
both exact exception modes (803 with explicit AVX and 701 without that opt-in),
and twelve raw-logger cases. It then stops because the runner incorrectly asks
the standalone shader suite for 538 cases; that suite emits its exact ordered
355 cases. The separate production-driver suite must still pass all 538 cases.
Its execution, GPU tests and the game are not reached. Smart App Control was
briefly disabled with explicit approval and restored; its UI and registry both
confirm the original enabled state. This is a test-runner defect, not an observed
MiniGolf rendering failure.
[Latest Windows prerequisite result](evidence/apple-gpu-windows-six-prerequisites-20261011.json).

### Native59 ownership diagnostic, 2026-10-11

Native59 is installed and closed after a preserving update. It changes only
native `server.o` and `virtual.o`; all 35 other objects in the ntdll archive,
all seven native FEX archives and the four embedded PE components retain their
Native58 bytes. Thirty-two native controls check the bounded ownership reads.
The original Native58 Continuing50 failure remains a failure.

The optional diagnostic records the RPM allocator lock owner and recursion
depth from the live FEX pool mapping, plus the sampled thread's private native
critical state. It rejects foreign, ambiguous or changing mappings and logs
after resuming the sampled thread. The former watchdog and long RIP profiler
are skipped only when this diagnostic is explicitly enabled. Equal repeated
reads are observations, not an atomic snapshot or proof of the hang's cause.
The subsequent device observation above captures a PC/LR=2 fault with free
observed ownership state; CPU qualification remains required before import.
[Signed diagnostic build](evidence/native59-host-20261011.json).

An earlier installation preflight stopped before device operations because the
externally supplied Python interpreter changed after the historical provenance
record was sealed. A complete replay identifies this as the sole mismatch among
53,993 inputs; the signed applications, runtime archives and retained protected
data still match. A separate execution-tool record declares the actual new
interpreter and preserves the historical record. The subsequent update succeeds:
complete USB reads verify 3,649 readable files and 11,227,745,899 bytes. Protected
records remain equal; eight added and nine removed ordinary system records
satisfy the exact preservation policy, with no changed file records. Native
installer, monitor and observer join, and all source identities remain stable.
Opaque contents, installed executable bytes, CPU execution and gameplay are
not independently verified by this installation result.
[Accepted Native59 installation](evidence/native59-preservation-accepted-20261011.json).

### Native58 installation and preservation, 2026-10-11

The suspension-repair candidate is now compiled, linked and signed into Native58.
Its fresh Wine archives, full ARM64EC JIT and two changed native FEX archives
are verified; unaffected archives and the signed Native57 rollback retain their
bytes. The same-bundle update is now accepted: fresh complete accessible-data
reads preserve protected data and opaque metadata under the exact ordinary-system
file policy. The app ends closed and all owned operations join. Opaque contents
and installed executable bytes were not independently read.

The first Native58 device probe activates automatic built-in JIT, allocates the
512-MiB pool and begins the original Continuing50 fixture. After 120 seconds,
the log has no captured interrupted context, completed 50-delivery result or
normal guest exit. The host is still present; a crash or the hang's cause is
not established. The collector completes in 136.244 seconds, closes its own
process, restores the original library byte for byte and preserves protected
metadata, without cleanup errors. No profiler or log query runs during the
fixture. This failed or incomplete observation does not qualify the suspension
repair, Continuing50, all 803 deliveries, the eight fresh CPU phases, GPU or
gameplay. The new game-side package remains unimported and unexecuted.
[Actual Native58 observation](evidence/native58-continuing50-observation-20261011.json).
[Accepted installation and boundaries](evidence/native58-preservation-accepted-20261011.json),
[signed host build](evidence/native58-host-20261011.json).

## Source and host refresh, 2026-10-10

### Native57 installation and protected-data acceptance

The preceding signed Native57 update completed successfully. Full before/after USB
reads preserve the protected accessible games, saves, Wine prefix, pairing and
settings against the accepted current baseline. The final inventory contains
**10,908,776,215 readable bytes in 3,460 files / 5,736 entries**. Whole-inventory
raw equality is false: eight ordinary system files are added and nine are
absent, with no changed file records. These differences satisfy the exact
prospective system-artifact policy; all selected before/after bytes are retained
and hashed. Every current readable file has an explicit verified provider.

The native installer exits zero, the app ends closed, and the installer,
monitor and observer all join without observation errors. Source closure is
replayed under the live observer and its final fingerprints remain unchanged.
This accepts installation and protected-data preservation; it does not verify
installed binary bytes, inaccessible SystemData contents, Keychain, Native57
JIT/CPU execution, GPU output or gameplay. The Continuing-only 50-round check,
full 803-delivery test and all eight fresh CPU phases remain required.
[Accepted installation and boundaries](evidence/native57-preservation-accepted-20261011.json).

The first fresh Continuing50 attempt observes JIT enabled, the debugger attached
and both FEX thread initializations completed. The 120-second log contains eight
suspend records and seven resume records after the first suspend, but no captured
interrupted context or normal guest exit. Wine logs the first eight operations
of each counter and every 256th afterward; these samples do not establish total
operation counts or balanced suspension. The host remains alive; a crash and its
cause are not established. The collector ends after **139.650 seconds**, restores
the original library and protected metadata, and closes its own processes without
cleanup errors. This failed or incomplete diagnostic does not qualify Continuing50,
the full 803 deliveries or any of the eight CPU phases. MiniGolf import remains
blocked on those fresh results. [Actual observation](evidence/native57-continuing50-observation-20261011.json).

A subsequent **45-second sampler diagnostic** captures both Wine threads after the fixture begins. The main is RUN at the same native PC, LR and SP in all four passes; the worker waits in `read`, with `wait_select_reply` as its link-register function. The fixture still has no normal guest exit or printed interrupted-context records; this does not establish the in-memory delivery count. The collector completes in **62.379 seconds total**, closes its exact owned process, restores the original raw library and preserves the three protected metadata files, with no cleanup errors.

The watchdog can perturb scheduling or introduce a logger wait; sampling resume return codes are unchecked, and the stack addresses are candidates. This capture alone identifies neither the original hang's cause nor a repair. Continuing50, full 803, all eight CPU phases, import and GPU/gameplay acceptance remain unqualified. [Bounded observation and limitations](evidence/native57-bounded-sampler-observation-20261011.json).

Inspection of the matching ARM64EC DLL and its COFF symbols maps the sampled main PC to `fex_ios_rpm_lock`'s nonzero-owner acquisition loop. The link register is the return from `FEXCore::Allocator::malloc`'s call to that lock. This identifies the current main waiter, independently of the worker's separate code-invalidation hold stamp. It does not read the RPM owner or depth, identify the owner, unwind the outer caller or exclude a stale owner / mismatched identity. No repair or CPU gate is accepted by this attribution. [Bound code inspection](evidence/native57-rpm-spin-source-attribution-20261011.json).

An isolated suspension repair candidate now passes 132 native signal-mask and adapted server controls, 24 FEX scope cases, 23 expected fatal cases and nine controls for unchanged non-iOS paths. Six fresh iOS Wine objects form two completed archives; all 79 retained members remain byte-identical. The full ARM64EC FEX DLL is freshly compiled and retains its export/import contracts. The candidate masks `SIGUSR1` before FEX lock acquisition and binds temporary server deferral to the exact pending capture and requester. It does not synthesize an acknowledgement or bypass hard suspension. Forty-three affected native ARM64 objects also rebuild successfully into two FEX archives with equal public symbol contracts; five unaffected archives retain their exact bytes. This candidate is now signed and installed as Native58; fresh CPU gates remain pending. The RPM owner is still unknown; local build success does not establish a repaired allocation/suspend cycle. [Local candidate evidence](evidence/native-critical-suspend-local-builds-20261011.json), [accepted Native58 preservation](evidence/native58-preservation-accepted-20261011.json).

Earlier rejected captures, the seven-file diagnostic, the fresh two-read
baseline and the update refused before installation for disk reserve remain
preserved as historical evidence. Their results are not reclassified by the
later accepted update. [Historical pre-install checks](evidence/native57-preservation-preflight-20261010.json).

### Conditional interpolation groups after the PC 76 failure

The current Windows failure contains complete interpolation groups on optional
forward branches. Some destinations have ordinary initial values on the skipped
path. An isolated proof now follows definitions through the acyclic graph:
definitions intersect at joins, while possibly interpolated values union. A
subsequent read requires a complete definition on every path. P1/P2 pairs remain
inside one block; every group must use the same unmodified original SGPR for M0.
Fresh instruction decoding and complete rebuilt-graph equality run before this
analysis, and the original raw I/J liveness and EXEC checks remain active.

The request then reaches a scalar-buffer load into VCC_HI. The ordinary
translator already supports this destination; the proof now models precisely
one word at VCC_HI or one/two words at VCC_LO, with SGPR bank bounds and existing
EXEC/M0 rejection intact. This changes validation coverage, not the instruction's
execution semantics.

Native source qualification passes **538 ordered public guards**, retaining all
484 previous names in order, and a separate **148-case subset** containing eleven
private requests. Both suites pass ASan/UBSan; five deliberately broken safety
checks are detected. The proposed production fixture also passes syntax checking.
The freshly linked production PRX now passes those 538 public cases and all nine
existing complete request replays, with identical SPIR-V and binding-layout
bytes. All 3,725 export names, ordinals and forwarders, and the imports, match the
preceding driver after excluding exactly six new compiler-private helpers.
The attempt remains failed: a registration identity negative control used an
absent alternate driver, so the filesystem comparison aborted instead of
returning its expected rejection. A separate recipe repair must rerun the full
qualification with a real different file. That retry passes the public identity
negative and all 538 shader cases, but its live output-size walk races an atomic
shader-cache rename after three full replays. This runner attempt also remains
failed; its correction must keep output and disk limits intact.
GPU output and a new game run remain
pending. The original PC 76 request contains registration metadata, not a
complete runtime resource snapshot. [Source qualification](evidence/minigolf-pc76-source-20261010.json),
[partial production attempt](evidence/minigolf-pc76-production-attempt-20261010.json),
[runner retry](evidence/minigolf-pc76-control-runner-20261011.json).

### Uniform SCC branch proof after the PC 72 failure

The complete PC 72 request contains a forward uniform SCC branch around a small
optional arithmetic block, followed by more interpolation using the original
center I/J pair. The proof now accepts only an exact three-block skip diamond
with complete P1/P2 sequences and preserved raw I/J values on both paths.
Nested branches, EXEC changes, memory effects and writes overlapping the raw
pair remain rejected. The interpolation guard remains enabled.

The isolated production driver passes **401 ordered public cases**, including
46 new branch-proof regressions, **nine complete request replays**, **twelve
null-pixel cases** and the full **53-case host suite**. All eight previous replay
outputs retain identical SPIR-V and binding-layout bytes. Its complete 3,725
export-name/ordinal/forwarder table and imports match the preceding driver.
Two newly autoexported compiler-private symbols initially broke that ABI check;
the failed build remains recorded. A fresh link excludes exactly those two
symbols and restores the original ABI, without weakening the comparison.

Cache schema remains 22 with policy `center-ij-unused-m0-trace-scc-skip-v2` and
source identity `0xa13bab0bc36edc45`. Only the AGC library is freshly linked;
46 other modules retain their verified bytes. A new Windows packet has all
47 modules freshly NID-patched and independently replayed against all 3,186
guest imports; the twelve guest ELF outputs and 181-file layout are explicitly
reused unchanged. These are local CPU/preparation results. The new native
Windows run and the iPad GPU/gameplay checks remain separate.
[Production proof evidence](evidence/minigolf-scc-skip-production-20261010.json).

### Instrumentation proof correction after the Windows run

The first complete request from the sixteen-prerequisite Windows run has five
instructions, no VINTRP and no read of the original center I/J values before
their full overwrite. The strict unused-input proof did not model a literal
write to M0 and a payload-free thread-trace operation. The existing translator
already handles both forms. The source now admits only their exact decoded
encodings and operands; M0-dependent operations, trace payloads, arbitrary EXEC
changes and invalid P1/P2 sequences remain rejected.

The unchanged original proof rejects that complete private request. Its isolated
native replacement passes 54 controls and detects three deliberately broken
guards. Another 53 public synthetic regressions preserve the previous 302
production assertions. Both old and new six-patch series apply and reverse
exactly, with the old qualified sources retained. Cache format remains 22; a
new interpolation policy tag must generate a distinct source identity and old
caches cannot establish qualification of the correction.

**The correction is rebuilt and locally qualified through the actual production
PRX:** all **355 ordered public cases**, **eight complete private request replays**
and **twelve null-pixel cases** pass. The complete serializer-15 request that
triggered the recorded Windows failure now passes preparation, resource capture
and materialization. The preceding seven replay outputs preserve both their
SPIR-V and binding-layout bytes. The loaded production-library path and both
wrong-library rejection controls are verified.

The selective build compiles only `InstructionTranslator.cpp`,
`ShaderDiskCache.cpp` and the public proof fixture. It freshly links the AGC PRX
and import library, retaining all **46 other runtime libraries** and 888 unchanged
objects by exact input/dependency identity. Export names, ordinals, forwarders
and imports remain equal. Cache schema stays **22**, with policy
`center-ij-unused-m0-trace-v1` and new source identity **`0x3483c09582e11677`**.

A separate fresh host continuation passes **53 cases: forty direct targets and
thirteen registered cases**, with no CTest skips or failures. Seven host
executables are relinked against the new shader archive; the other 45 keep their
verified bytes. The separate AVX-context subtest remains unavailable on local
Wine. The initial selective phase failed while staging the real test-only
`libSceRudp` library; its failed result and completed shader checks remain
preserved. The continuation uses that library's verified original provider,
without adding it to the game's 47-library dependency set.

**These local results are CPU/compiler contracts.** The subsequent native Windows
reference passes the freshly relinked GPU fixtures and starts MiniGolf with these
runtime bytes. The earlier PC 0 request is no longer the first failure: the latest
run reaches a different strict proof guard at PC 72. No game image, course or iPad
execution is qualified. The original source-only checkpoint is retained.
[Rebuilt production qualification](evidence/minigolf-instrumentation-proof-production-20261010.json),
[source correction and bounded validation](evidence/minigolf-instrumentation-proof-source-20261010.json).

All 424 merged commits after `d70b8998` are included. Six-patch application reproduces 216 reviewed files exactly and reverses to the new upstream contents/modes. The original patched source and historical results remain preserved. Schema 22 retains local policy metadata, rejects older cache formats and uses the current source-derived identity; the refreshed package uses a new cache directory. Exception delivery retains the native AVX/flags/protected-store bridge alongside the bounded NtContinue/winpthread retry. Audio3d continues to report unsupported PCM/render behavior honestly. [Source qualification](evidence/anyps5-c963-source-20261010.json).

The matching native relinker and NID patcher pass all 43 tool tests without skips. Their actual execution belongs to the earlier tool qualification; subsequent runtime-only changes preserve the checked tool/source closure and do not count as another execution. The old module-import expectation now includes the two existing module-init argument/result helpers while retaining malformed-note and bounds checks.

**The preceding complete 47-library build passes all 53 host cases:** forty directly executed targets and thirteen registered CTest cases, with no CTest skips or failures. The separate AVX-context subtest remains explicitly unavailable on local Wine; native Windows and iPad/FEX execution are still required. The fresh production AGC PRX passes all **302 public compiler cases** and **seven complete private request replays** through preparation, resource capture and materialization. Generated cache schema 22 and the actual loaded-library identity are bound to this runtime. All **181 prepared game-package files**, twelve relinked ELFs, 3,186 guest NIDs and 47 independent library-patching replays are verified. This qualifies local preparation and CPU contracts, not game rendering. [Complete runtime qualification](evidence/anyps5-c963-full-runtime-20261010.json).

The targeted #1902/#2022 fixes register and prepare a consistent null pixel program and treat unwritten address registers as unset. A separate synthetic fixture now passes **twelve actual-production-library preparation/capture/materialization cases**, including absent/zero/partial addresses at wave32/64, stale input/SGPR removal, late variant preparation and reuse, enabled-color-write rejection and missing nonbuiltin variants. Its wrong-loaded-library identity control fails as required. An invalid color format with a nonzero mask remains a legitimate depth-only state; rejection cases explicitly enable the color target. This fixture creates no Vulkan device and does not execute device shader registration. [Reusable fixture and local build instructions](LOCAL-HLE-BUILD.md#production-null-pixel-materialization-check).

The exact `0x22eea66a` sample pattern passes the production decoder with three strict rejection controls. Existing depth format/sample queries and guest-memory coherence remain intact. General multisample depth and HTILE transfer remain guarded. Real local Wine/MoltenVK execution on **Apple M3 Pro** passes prepared graphics and the expected registration-failure control; **four prepared-shader modes fail because storage-image multisampling is unavailable**. Those failures remain recorded and are not counted as passing GPU tests. All six modes now pass the separate native AMD reference described below; the refreshed iPad GPU path remains unqualified. [Focused local CPU/GPU contracts](evidence/anyps5-c963-local-contracts-20261010.json).

### Repairs required by the refreshed host tests

The first focused execution exposed an omitted feature bit in an upstream positive update-after-bind mock fixture and a lost exception delivery during the new `NtContinue` stress test. The graphics fixture now enables the feature explicitly for its positive case and retains false-feature and limit rejection checks. The depth-reuse fixture supplies both required capability queries, retains all original reuse assertions and adds eleven strict negative controls. These mock checks do not prove physical GPU execution.

Exception diagnostics identified the lost delivery inside Wine's native dispatcher return. A bounded retry uses validated dispatcher export cells safely read before suspension; private executable memory outside that interval remains eligible. Current local execution passes **601 ordinary deliveries, twenty native wait cases and one separate private-RX delivery**, with correct thread/RIP, observed return, join and release. Local AVX remains unavailable. Native Windows separately passes the **803-delivery explicit-AVX mode and 701-delivery default mode**, including private-RX and native-wait checks; iPad/FEX execution remains required.

The Audio3d port fixture now tests the actual reset-state attribute and strict unsupported PCM behavior. Both it and the object-attribute contracts pass without changing the production Audio3d implementation. A Windows-only adapter also reconciles the local handle-based `fchmod` path with upstream's errno mapper and restores the captured Win32 error for its access-denied retry.

The descriptor-timestamp failure after rename is reproduced with 132 synthetic Win32 checks under local Wine. Updating the existing handle preserves precise timestamps after rename and unlink. `ReOpenFile` instead fails after rename or resolves a different inode when the old pathname is reused. The repair uses the original handle first, captures the error before translation and permits a permission retry only after comparing the current volume and full 128-bit identity of both handles. Eighteen production-body controls and two failing mutations cover that fallback and its errors. Local Wine permits the genuine data-only handle directly, so a real permission-denied retry is not claimed as executed.

A separate access-time failure is reproduced in the actual kernel PRX: Wine's `GetFileType` probes regular-file contents for device placeholders, and `_fstat64` calls it as well. Each isolated call changes the requested access timestamp while native metadata queries preserve it. The repair uses `FileBasicInfo` and `FileStandardInfo` on borrowed regular-file handles and the already obtained CRT classification for path metadata. Unsupported metadata may fall back to the CRT only for confirmed pipe or character descriptors; other errors remain errors. Thirty production-body controls and five failing mutations pass. The complete rebuilt filesystem regression now passes with its original precise timestamp assertions and additional path-access, pipe and invalid-descriptor checks.

Focused gate attempt 5 timed out after 90 seconds in the unchanged shader-cache executable. A separate instrumented diagnostic completed its child-process return, invocation-isolation stages and final flush; it remains diagnostic evidence. Later unchanged, uninstrumented gates pass, including **final gate 7 against the completed runtime's actual bytes**, with cache schema 22. The earlier timeout remains preserved and its cause is unresolved; no production cache repair or timeout increase is claimed. The complete host suite and production qualification described above subsequently pass.

### Native Windows prerequisites and game startup

The current private Windows packet verifies **256 payload files and 181 game files**,
including the newly linked AGC PRX, 46 verified reused libraries and twelve converted
ELFs. **All sixteen prerequisites pass on the physical AMD Radeon 780M**: native
CPU/AVX/exception checks, twelve raw-logger cases, two ordered **401-case** compiler
fixtures, BDA/8-bit/BC1 offscreen readbacks, all six prepared-GPU modes and twelve
null-pixel cases against the actual production PRX. Five prepared-GPU positives
exit zero; the deliberate registration-failure control exits one with its expected
diagnostic. Every GPU selection matches the physical device. Owned processes are
joined without discarded output.

Native exception execution includes **803 deliveries with explicit AVX and 701 in
default mode**, plus one separate private-RX delivery and twenty native-wait cases
in each mode. The null-pixel fixture creates no GPU device. Native synthetic GPU
fixtures use the queried AMD interpolation support; **MiniGolf's fixed-function
interpolation profile is restored before launch**. These tests do not qualify the
M2 fixed-function path.

**Run 9 uses the qualified SCC-skip runtime and starts MiniGolf**, then exits
after **6.223519 seconds** with **`0xC0000409`**. The first shader exception now
comes from a different program at **PC 112**:

```text
ShaderRecompiler::Recompile: fixed-function interpolation requires unmodified center I/J pairs and complete P1/P2 sequences on a proven entry/discard path (pc=112)
```

The strict proof guard remains enabled. The actual game cache is format **22**,
source identity **`0xa13bab0bc36edc45`**, with policy
`center-ij-unused-m0-trace-scc-skip-v2`. The requested window is **1920 × 1080**;
the actual swapchain is **837 × 471**, with **three images**. These measurements
do not establish the game render-target resolution. The capture helper exits
zero but reports `not_captured` because the owned game exits during capture;
no PNG is returned. **No screenshot, rendered course, completed stroke,
120-second run or gameplay acceptance is established.** The new request remains
private for local diagnosis. [Run 9 evidence](evidence/anyps5-c963-windows-run9-20261010.json).

The first complete run with the preceding 302-case runtime exited after
**6.5862776 seconds** at PC 0. Its retained request led to the narrow M0/trace proof
correction described above. [Historical startup evidence](evidence/anyps5-c963-windows-sixteen-prerequisites-game-start-20261010.json).

Run 7 passes its sixteen prerequisites but module loading fails for
`libSceImeDialog.prx` with Win32 error **4551** and process exit **`0xC0000135`**.
The dependency audit has no missing imports. This is an Application Control loader
rejection, not a shader or gameplay result. [Run 7 evidence](evidence/anyps5-c963-windows-run7-20261010.json).

The preceding **run 8 loads the modules, initializes Vulkan and starts MiniGolf**, then exits
after **6.701467 seconds** with **`0xC0000409`**. Its first shader exception is:

```text
ShaderRecompiler::Recompile: fixed-function interpolation requires unmodified center I/J pairs and complete P1/P2 sequences on a proven entry/discard path (pc=72)
```

The new complete serializer-15 request remains private for local diagnosis. The
strict proof guard stays enabled. The requested window is **1920 × 1080**; the
actual swapchain is **837 × 471**, with **three images**. This does not establish
the game render-target resolution. The capture helper exits zero but reports
`not_captured` because the own game exits during capture; no PNG is returned.
**No screenshot, rendered course, completed stroke, 120-second run or gameplay
acceptance is established.** [Run 8 evidence](evidence/anyps5-c963-windows-run8-20261010.json).

Smart App Control was temporarily disabled with explicit permission for the
reference runs. After run 9, Windows Security shows it enabled at Windows clock
minute **14:32**, and an independent read-only registry check confirms value **1** at
**14:33**. Exact action UTC seconds are not established. Own reference/game trees
are joined and the listener is closed; other security and network settings are
unchanged. All builds and tests remain local, without GitHub Actions.

The initial Application Control rejection and the [nine-prerequisite](evidence/anyps5-c963-windows-nine-prerequisites-20261010.json)
and [fourteen-prerequisite](evidence/anyps5-c963-windows-fourteen-prerequisites-20261010.json)
checkpoints remain preserved. Their reader limitations were corrected without
changing the game profile or strict shader guard. Earlier Windows comparisons
below retain their exact historical package scopes.

### Native56 installation and data-equality gate

FEX #6021 corrects the 32-bit lookup-table size load and rejects `index == size`. Twenty extracted native assembly cases, two guard-page mutations, a COFF alignment control and production-object disassembly pass. The fresh full ARM64EC DLL is built and packaged in signed Native56. There is no established connection to MiniGolf's previous failure or FPS. The host retains the existing app identity, helper, memory permissions and profiles; unchanged native archives and three PE modules retain their original hash-verified provenance. [FEX qualification](evidence/fex-arm64ec-checkcall-20261010.json).

The original strict update recipe stopped at its 8-GiB backup bound. AFC denies root `SystemData` contents and an independent exact CoreDevice listing also fails, so a full-container backup is not established. A separately authorized accessible-only procedure preserves every readable game/save/settings/pairing/Wine file and records opaque system metadata without claiming inaccessible contents or Keychain bytes backed up or restorable. An earlier second comparison stopped at an own-app process appearance. The bounded own-app system log identified **DAS Prewarm launch** followed by suspension; Apple's [launch-sequence documentation](https://developer.apple.com/documentation/uikit/about-the-app-launch-sequence) describes this prewarm behavior. Failed captures and their evidence remain preserved.

The subsequent recapture accepted an accessible backup of **9,648,347,044 bytes across 2,699 files**, verified by local replay and two fresh complete USB reads with the app closed. The observer closed one proven suspended OS-prewarm process using exact PID/path/build checks. This backup remains retained.

**Same-bundle Native56 installation was observed as build 56, but its post-install userdata equality check failed.** The automatic fallback installed and closed the signed Native55 app; its strict comparison also differs from the accepted backup. Those failed gates remain recorded. [Native56 host and update evidence](evidence/native56-host-20261010.json).

A subsequent complete read-only USB inventory establishes the exact differences: eight newly named system snapshots have byte-identical old providers, nine old snapshot paths are absent, and one 78,904-byte dyld cache changed. All 4,745 entries below Documents, preferences, application support, 510 symlinks and opaque system-root metadata remain equal. This confirms preservation of the readable games, saves, Wine prefix, pairing and settings. The full readable backup remains intact. It does not establish a rename operation or which install event changed the caches, restore inaccessible contents, or retrospectively pass the strict update gates. A fresh backup basis and a narrowly scoped install comparison are required before the next Native56 attempt. Native56 JIT, GPU and gameplay remain unqualified. [Complete data comparison](evidence/native55-readonly-data-comparison-20261010.json).

### Later Native56 installation and current readback

A later native installation command completed successfully and reported build 56. Its enclosing update stopped on an iPadOS status-observation error, so that historical result remains failed. The subsequent independent read-only phase confirms the current Native56 identity and hashes all **9,647,839,116 readable bytes in 2,698 files / 4,789 entries**. Protected game/save/Wine/pairing/settings data matches the retained composite; only the prospective ordinary-system-file policy differences are present, with their bytes retained.

The final closed-state query found another exact own app process. It did not exit within the fixed 130-second wait, and the log does not establish its start cause or a fresh DAS prewarm. All three owned read/monitor/observer tasks joined. **That first reconciliation remains unaccepted.** Its complete evidence is retained and has not been relabelled. No reinstall, launch or userdata write occurred in this read-only phase. Protected `SystemData` contents and Keychain remain outside the backup claim. [Current readback and failure boundary](evidence/native56-readonly-reconciliation-20261010.json).

A second execution of the same reviewed helper completed successfully in **398.974 seconds**. It ordinarily closed the previously observed own main process, observed and closed one fully proven suspended/NotVisible DAS prewarm, streamed another complete **2,698-file / 9,647,839,116-byte** inventory, retained the allowed system-file bytes, and verified the full local source/provider bytes and a fresh final closed state. All read, monitor and observer tasks joined. This independently accepts the current Native56 protected-data state without reclassifying the earlier failed installer or readback. It performed no installation, launch or userdata write. Native56 JIT, CPU execution, GPU and gameplay still require their separate tests. [Accepted current-state evidence](evidence/native56-readonly-reconciliation-accepted-20261010.json).

### First Native56 CPU execution and library recovery

A fresh CPU launch automatically enables built-in JIT, obtains the separate RX/RW
512-MiB pool and runs the x86-64 AVX2 fixture. All six numerical cases match their
independent references, followed by a zero guest exit and clean Wine-thread
completion before collector termination. This establishes execution of those
cases; the complete phase remains failed.

The collector's broad word filter rejects benign host diagnostics containing
`skipped` or `unavailable`. Its cleanup then refuses two metadata scan timestamps
on existing library entries and default fields saved on the temporary CPU card.
A separate closed-app USB read verifies the exact differences and both protected
title manifests plus global settings. Recovery atomically restores the original
library and reads it back byte-for-byte, ending with the own app closed. No game
saves or pairing files are written by the collector or recovery. The failed
attempt is preserved; the remaining CPU phases, GPU and gameplay are open.
[CPU attempt and separate recovery](evidence/native56-avx2-attempt-and-recovery-20261010.json).

The corrected collector retains every numerical, count, target and terminal
check, scopes unavailable/skip detection to fixture results and permits only the
observed default fields and bounded forward metadata-scan timestamps. All 180
offline controls pass before plan creation. A **fresh actual AVX2 phase passes
in 78.591 seconds**: automatic JIT, all six reference cases, zero guest exit
before any collector termination, one final log read, original-library byte
restoration, protected metadata equality and own-process closure. The historical
failed attempt remains failed. This passes one CPU phase; allocator, mapping,
protected-state, exception, GPU and game qualification remain open.
[Passed fresh AVX2 phase](evidence/native56-avx2-passed-20261010.json).

Seven of the eight initial Native56 CPU phases now pass in independent fresh
launches. The additional phases verify standalone allocator collisions, 4-GiB
virtual mappings, protected store state, pending AVX with and without protection,
and relinked guest exceptions. Every passed phase records zero guest exit before
collector termination, one final log read, original-library restoration, protected
metadata equality and clean own-process closure. The remaining
`guest-raise-exception` execution fails in its Continuing worker while resuming
through the Wine/ARM64EC exception path; no normal guest exit is observed. The
expected synthetic suspension exceptions are not themselves the failure. Cleanup
restores the original library and protected metadata and closes the launched own
process. This is a CPU continuation blocker, not a GPU or gameplay result.
[Current CPU phases and failed continuation](evidence/native56-cpu-phases-20261010.json).

A separate 120-second Continuing-only diagnostic also fails to complete. Automatic
JIT succeeds, but the test records no interrupted-context rows and no normal
guest exit. The observed native ARM64EC exit thunk resumes with an unaligned
stack after a synthetic suspension; this narrows the investigation without
establishing a production repair. One final log read, original-library byte
restoration, protected metadata equality and own-app closure succeed. The
original 803-delivery gate remains failed and the initial CPU acceptance stays
at seven of eight phases. [Bounded diagnostic](evidence/native56-continuing-diagnostic-20261010.json).

## Preceding package baseline

Version **01.000.000** had a freshly prepared six-patch combined runtime
package against complete AnyPS5 main `d70b8998`. All twelve decrypted ELFs relink,
the dependency audit passes and all 170 package files are verified. **Native
Windows execution passes all eight isolated array-load prerequisites and stops
at another fragment-shader rejection; iPad execution of
this package remains unqualified.** The earlier Native55
package attempt reports the new runtime's unsupported `nullDescriptor`
requirement; its history and the preceding Native54 JSON allocator failure are
preserved below. Rendering and gameplay remain unqualified.
The target is a complete offline single-player course with touch input, sound
and save/load; there is no initial FPS acceptance threshold.

## MRT color-export candidate, 2026-10-10

The seventh request now passes the unchanged EXEC/CFG/whole-quad proof. The
new footprint models compressed and plain color exports to MRT0–7, including
enabled packed source pairs, final-export and valid-mask metadata. Raw encoding
and decoded operands must agree; depth-export restrictions remain intact.
No translator, interpolation or transfer semantics are weakened.

All 234 retained public test bodies are unchanged. Another 68 cases cover 28
accepted and 40 rejected forms. The actual graphics PRX passes all 302 public
cases and materializes all seven complete requests; the previous six SPIR-V
and binding-layout pairs remain byte-identical. Exports, native imports and
3,186 guest NIDs still close. Optimized and ASan/UBSan native checks pass 239
distinct namespace cases; three deliberate missing-read/metadata mutations
are detected. The actual-library experiment completes 37 commands and 17
result scopes, with both owned Wine prefixes closed.

The seventh SPIR-V translates to MSL with and without argument buffers. Both
variants create Metal 2.4 source libraries on Apple M3 Pro with fast math
disabled. This does not qualify a GPU pipeline, iPhoneOS compilation, game
rendering or iPad execution. The qualified repairs are saved in the canonical
source and cumulative patch0004. Their execution evidence belongs to the
isolated driver; the next native Windows game comparison and a fresh production
rebuild remain pending.
[MRT-export qualification](evidence/minigolf-mrt-export-candidate-20261010.json).

## Scalar-pair and array-load Windows comparison, 2026-10-10

The isolated driver passes all eight prerequisites on native Windows, including
234 public cases through the actual PRX. The retained tests pass 45 baseline
cases, 12 logging cases, 553 AVX-verified exception deliveries and 36 memory
checks. The Radeon 780M passes BDA/8-bit and BC1 texture readbacks. All 217
manifest files and 170 game-package files are verified; 168 game files remain
unchanged, with only the graphics PRX and manifest replaced.

MiniGolf exits after 7.180 seconds with `0xc0000409` at the interpolation guard
(`pc=0`). Its seventh distinct complete shader request is 1,999 bytes. Native
decoding reproduces the rejection: 14 instructions in one CFG block, with
eight unknown register footprints for compressed color exports to MRT7 through
MRT0. The other six instruction effects are known. The shader overwrites the
raw center inputs before exporting and uses no interpolation, implicit sampling
or whole-quad instructions. The existing translator supports these exports;
the missing proof concerns enabled source reads and valid-mask/done variants.
The swapchain
remains 837 × 471 with three images. A transient black window is observed, but
the process exits before a bounded frame capture; game rendering remains
unqualified. The owned game/reference processes and transfer service are closed.
This result does not qualify iPad execution or gameplay.
[Native Windows comparison](evidence/minigolf-array-load-candidate-20261010.json).
[Exact MRT-export diagnostic](evidence/minigolf-mrt-export-diagnostic-20261010.json).

## Lane-math Windows comparison, 2026-10-10

The repaired isolated driver passes 178 public cases through the actual loaded
PRX on native Windows. All eight prerequisites pass, retaining 45 baseline cases,
12 logging cases, native AVX/exception checks and Radeon 780M synthetic offscreen
readbacks. With a fresh test directory, title saves and shader cache, MiniGolf
then exits after 6.312 seconds with `0xc0000409` at the interpolation guard.
The new complete request is 2,463 bytes and differs from all five previous
requests. Native decoding finds 45 instructions in six reducible CFG blocks;
the remaining missing effects are scalar-buffer `DWORDx2`, 2D-array image load
with three address words, and MSAA-array image load with four. Neither implicit
sampling nor WQM appears in this request. The three missing register-effect
forms now pass native qualification: 56 new cases and 115 retained namespace
cases pass optimized and with ASan/UBSan; the complete 234-case fixture passes
syntax checking. Three deliberate omissions of the second scalar write, array
layer and MSAA sample are detected. The complete sixth request passes the
unchanged proof with all 45 instruction effects recognized. The actual loaded
PRX passes all 234 public cases, six 235-case imported runs and all six complete
shader materializations. The previous five SPIR-V and binding-layout outputs
remain byte-identical; exports, native imports and 3,186 guest NIDs still close.
This isolated one-TU experiment retains historical serializer/cache identity;
a fresh production rebuild remains pending. The subsequent native Windows game
comparison with this candidate is recorded above.
Seven independent CPU witnesses also pass optimized and with ASan/UBSan,
checking observable layer/sample selection, aliased address snapshots, scalar
mask invalidation, sparse channels and inactive or subsequently restored lanes.
All three deliberate effect omissions are detected in both modes. These tests
use an integer memory oracle; they do not qualify GPU descriptors or rendering.
The sixth SPIR-V translates to MSL in both argument-buffer modes and creates
Metal 2.4 source libraries on Apple M3 Pro with fast math disabled. No GPU
pipeline, command submission or iPhoneOS compilation is qualified by that check.
The swapchain is still 837 × 471
with three images, and quality settings are unchanged. The process exits before
the first bounded window capture; no rendered game image is established.
Both the owned game/collector and peer-only transfer service are closed.
[Qualification and Windows checkpoint](evidence/minigolf-lane-math-candidate-20261010.json).
[Sixth-request native qualification](evidence/minigolf-array-load-candidate-20261010.json).

## Volume-sampler Windows comparison and next shader, 2026-10-10

The isolated volume-sampler driver passes all eight native Windows prerequisites:
144 public cases through the actual PRX, 45 retained baseline cases, 12 logging
cases, four CPU/exception targets and the Radeon 780M offscreen probe. Native
Windows verifies AVX and 553 exception deliveries; this does not erase the
separate local-Wine AVX limitation. The original package remains unchanged;
this comparison uses a fresh test directory, shader cache and title saves.

MiniGolf exits after 6.455 seconds with `0xc0000409`, before the first bounded
window capture. Its swapchain remains 837 × 471 with three images. The new
2,975-byte Serializer15 request is distinct from the preceding 3D-sampler
request. Both the imported fixture and complete-request replay reproduce its
interpolation-guard rejection locally; all 144 existing public cases still pass.
The complete request roundtrips exactly and owned Wine cleanup is confirmed.

The native decoder finds 76 instructions in twelve reducible CFG blocks with
a scalar loop and EXEC-mask branches. Twelve instruction footprints are missing:
three occurrences each of `VCmpNleF32`, `VLogF32`, `VExpF32` and `VMadakF32`.
This shader contains image loads, with no implicit `ImageSample` or `S_WQM_B64`.
The narrow repair therefore concerns register-read/write effects and VCC identity;
it does not require relaxing the whole-quad derivative or multi-block WQM guards.
The driver used in that comparison still rejects this shader; no repaired
gameplay is claimed.
[Windows comparison and exact replay](evidence/minigolf-volume-windows-next-shader-20261010.json).

An isolated candidate now admits only the exact four register-effect forms above.
Its 34 new decoder cases pass optimized and with ASan/UBSan; the retained
81-case native suite also passes with the new header. The full fixture retains
144 cases and adds 34, for 178 cases. The complete private shader
passes native decoding and the unchanged CFG proof. Seven independent CPU
witnesses check read-before-write, inactive-lane preservation and both saved
VCC identities; deliberately omitted MADAK reads and stale VCC-high identities
are detected. Existing shader arithmetic is unchanged.
The first actual PRX attempt builds successfully but stops before runtime tests
at the export-ABI gate: the compiler emits an internal unary `Footprint` lambda,
which MinGW automatically exports, adding one symbol and shifting later ordinals.
Native imports are unchanged. That failed attempt and its successful owned
cleanup remain recorded. A separate read-only review proves that none of the
package's 5,115 native import entries uses this internal helper. Excluding exactly
that automatic export restores all 3,692 names, ordinals and forwarders; native
imports remain identical. A fresh isolated link then passes 178 public cases,
five imported 179-case runs and five full Prepare/Capture/Materialize replays,
Graphics/DiskCache regressions and prior-runtime positive/negative controls.
All 3,186 guest NIDs remain resolved across 62 consumers and 50 providers;
both owned Wine prefixes are closed. The previous four SPIR-V modules and binding
layouts are byte-identical. The fifth module translates to iOS MSL 2.4 in both
argument-buffer modes. The offline Metal frontend is unavailable. A separate
bounded native helper successfully creates both fifth-request source libraries
through the macOS Metal runtime on the M3 Pro, using Metal 2.4 and
`fastMath=false`; each exposes `main0`. This creates no render pipeline or GPU
commands. Offline AIR, iPhoneOS compilation and iPad GPU behavior remain
unqualified. This isolates the CPU/PRX repair; it is not
a full production rebuild or a repaired-game rendering result.
[Isolated candidate evidence](evidence/minigolf-lane-math-candidate-20261010.json).

## Earlier 3D texture sampler diagnostic, 2026-10-10

The isolated quad-mask driver passes all eight prerequisites on native Windows,
including 121 cases through the actual loaded PRX and asynchronous AVX-context
checks. The physical Radeon 780M Vulkan probe passes device creation, buffer
device address, 8-bit storage readback and BC1 texture sampling readback. These
synthetic GPU checks do not establish correct game rendering.

The verified 170-file game package opens a black window and exits after
6.275 seconds with `0xc0000409` at the interpolation guard. Its swapchain is
837 × 471 with three requested and three actual images. The bounded collector
returns complete logs and no images; its own successful exit is distinct from
the game's failure. Resolution and interpolation settings are unchanged.

The complete new 2,111-byte Serializer15 request roundtrips exactly and
reproduces the rejection through the qualified actual driver in local Wine.
The imported public fixture passes all 121 existing cases before rejecting
that request. Its decoder identifies one missing footprint: plain implicit-LOD
`IMAGE_SAMPLE` with a 3D image and three coordinate VGPRs at byte PC 48. The
other fourteen instruction footprints are already admitted. The guard reports
shader-start PC 0; this does not identify the unsupported instruction itself.

The current no-VINTRP liveness proof admits only the two-coordinate 2D form.
The repair must validate the exact 3D encoding and all three address words,
including helper-lane reads used for implicit derivatives. Merely changing the
dimension check would leave the third coordinate outside that derivative
proof. An isolated candidate now passes 81 decoder/CPU-model cases in both
optimized and ASan/UBSan runs, a separate geometric dependency model, and a
control that deliberately omits the third helper-coordinate check. The complete
144-case fixture and all four complete private requests now pass through the
actual loaded candidate PRX, including prepare, capture and materialization.
The previous quad PRX rejects the new positive case and fourth complete request.
The original run's sole failure was its strict cleanup classification: the
compiler server was already absent. A separate immutable reconciliation verifies
both owned prefixes' unlocked server locks, absent sockets and process closure,
and retains every original input, artifact and successful test log. The failed
original receipt is preserved. The candidate has not been promoted into
production sources. Its subsequent native Windows comparison is recorded
above; correct game rendering remains unqualified.
The complete production build of the preceding quad-mask source is sealed:
47 libraries, 53 passing host cases, 121 actual-PRX cases and three full private
requests. Local Wine's internal AVX-context subcase remains explicitly skipped.
Neither work establishes visible game frames, iPad execution, audio, save/load
or playable gameplay.
[Windows and exact-driver diagnostic evidence](evidence/minigolf-3d-sampler-diagnostic-20261010.json).
[Isolated 3D sampler CPU evidence](evidence/minigolf-3d-sampler-candidate-20261010.json).
[Actual 3D PRX and cleanup reconciliation](evidence/minigolf-3d-sampler-actual-prx-20261010.json).
[Fresh quad-mask production runtime](evidence/minigolf-quad-mask-full-production-20261010.json).

The fourth actual materialized shader also translates to iOS MSL 2.4 with
Argument Buffers both disabled and enabled, retaining a `texture3d` resource.
The earlier three shaders are byte-identical, so their six verified translation
results are reused. The selected Xcode's Metal frontend remains unavailable;
no AIR, MoltenVK pipeline or GPU execution is established by these translations.
[3D MSL preflight](evidence/minigolf-3d-sampler-msl-20261010.json).

## Further textured shader, 2026-10-10

The separate repair now passes **121 public cases through an actual loaded
`libSceAgcDriver.prx`**, all three complete retained MiniGolf requests, and the
graphics and shader-cache regression programs. Prepare, capture and
materialization all run through that PRX. The previous driver rejects the new
positive case and the complete textured request, as expected.

The proof accounts for the exact eight-word scalar-buffer load, non-fused MAD,
plain 2D implicit-LOD sample and `S_WQM_B64 EXEC, EXEC`. Full writes made while
the entire quad is active can cover the original entry mask; helper-coordinate
reads additionally require definitions in the same unchanged quad epoch.
Unknown masks, partial writes, descriptor or saved-EXEC aliases and unmodelled
effects remain rejected. WQM is limited to one straight-line guest CFG block;
divergent or reconverging blocks do not inherit this proof.

The raw and NID-patched driver preserve export names, ordinals and forwarders;
all 3,692 raw exports and native imports match the baseline. Two exactly named
internal proof helpers are excluded from automatic export. Only one translator
object is replaced in the experimental archive; this is not a full production
rebuild. A synthetic test's saved-EXEC registers initially overlapped its sampler
descriptor. Both affected fixtures now use a separate register pair, with an
explicit decoder check for descriptor preservation.

All three actual materialized shaders translate to iOS MSL 2.4 with Argument
Buffers both disabled and enabled. The selected Xcode lacks the separate Metal
Toolchain, so no Metal frontend compilation occurred. This check also does not
create a MoltenVK pipeline or execute GPU work. A separate diagnostic changes
only the retained requests' host subgroup size from 64 to 32, after checking
their original serialization. All three still prepare and materialize through
the actual PRX, producing byte-identical SPIR-V and unchanged resource layouts;
their six MSL translations also pass. This is a CPU target check, not a report
of physical Apple GPU features. The subsequent Windows comparison is recorded
above; physical iPad rendering remains pending. The qualified source and exact MinGW export
exclusions have now been integrated into patch0004. The fresh complete
production runtime build is now sealed with source-derived cache identity
`0xee2929b1aa766da2`; its 121 public and three full private checks pass through
the freshly built PRX. The recorded game comparison uses the preceding isolated
PRX; neither build is the later 3D extension.
[Isolated quad-mask compiler evidence](evidence/minigolf-quad-mask-proof-20261010.json).

A separate local iPad candidate package contains all 170 checked files. Its
168 unaffected files match the combined baseline; only the qualified driver
and installation manifest differ. Fresh native-import and guest-NID checks
cover all twelve guest PE files and 3,186 NIDs without unresolved dependencies.
This package is prepared only, with no device profile update or installation.

The preceding failure that motivated this repair is retained below.

The isolated scalar-buffer/packed-conversion driver passes all eight native
Windows prerequisites, including its 63 actual-driver shader cases. With a
fresh cache, MiniGolf then exits after 9.06 seconds with `0xc0000409` at another
fixed-function interpolation guard, at byte PC 0. All 170 game files and 211
overlay payload files are checked. It exits before the first scheduled window
capture; no game picture or gameplay is established.

A local replay imports that exact `libSceAgcDriver.prx`, roundtrips the complete
2,079-byte Serializer15 request and reproduces the rejection. The pixel inputs
are perspective-center v0/v1 and position v2/v3, with no interpolators or VINTRP.
The proof lacks footprints for an eight-word scalar-buffer load, three-source
`V_MAD_F32`, plain 2D implicit-LOD sampling, and `S_WQM_B64 EXEC, EXEC`. MAD is
the decoder's non-fused operation; it must not be silently replaced with FMA.

WQM expands execution to helper lanes needed by texture derivatives. A repair
must prove that original barycentric inputs are unused in those lanes too;
an overwrite confined to the original active lanes is insufficient. The guard
remains enabled in the separately qualified CPU candidate. At that diagnostic
checkpoint, the scalar-color candidate had not been promoted. This replay performs CPU shader
preparation only. [Exact-driver diagnostic evidence](evidence/minigolf-quad-shader-diagnostic-20261010.json).

## Further scalar-color shader, 2026-10-10

The same combined package passes its native Windows CPU/AVX and physical
Radeon 780M Vulkan prerequisites. The game runs for 65.97 seconds, then exits
with `0xc0000409` at the fixed-function interpolation guard, this time at byte
PC 0. No owned foreground game window was captured; this is an execution and
diagnostic result, not a rendering or playability result.

The complete Serializer15 request contains a six-instruction constant-color
fragment shader with no VINTRP. Its four-word scalar-buffer load is followed by
two VOP3 packed F32-to-F16 conversions and a compressed color export. The current
proof does not model these two instruction forms, so it correctly rejects the
otherwise unsupported footprint.

An isolated candidate accounts for all four scalar definitions, including
saved-EXEC identity invalidation, and both packed-conversion source reads before
the full 32-bit destination write. Descriptor range/alignment, modifiers,
partial writes and inactive EXEC lanes remain guarded. It passes 63 public
compiler cases and both complete private requests through prepare, capture and
materialization. The separately named unchanged production translator rejects
the new scalar-color test as expected. This candidate is not yet promoted to
the production runtime and has no GPU or gameplay qualification.
[Isolated compiler evidence](evidence/minigolf-buffer-pack-proof-20261010.json).

The candidate also passes through an actual isolated `libSceAgcDriver.prx`,
including graphics and disk-cache regressions, all 63 public cases and both
private shaders. Its 3,692 export names and native imports match the baseline.
Only the translator object in the shader archive changes; the existing generated
cache version is retained for this experiment, so its game comparison requires
an empty, separate cache. This is not a complete production-runtime rebuild.
An independent ARM64 and ASan/UBSan model each checks 1,451,520 raw-input
comparisons, 72 descriptor snapshot cases and 15 finite-half references; seven
deliberately unsafe variants are rejected. These CPU proofs still do not
establish correct GPU output.

## Combined runtime prepared, 2026-10-10

The complete upstream plus six local patches now builds 47 HLE PRXs and passes
42 selected plus ten additional host test programs: 53 distinct cases with zero
failures or CTest skips. Local Wine cannot expose asynchronous AVX for one
internal subcase; this remains explicit. All project objects are rebuilt,
source bytes/modes and test dependencies are verified, and the 50-file HLE
payload is sealed against immutable qualification and final provenance.
[Combined runtime evidence](evidence/anyps5-combined-runtime-20261010.json).

The package combines bounded complete exception logs, `RequiresValidImages` for
drivers lacking native null-image descriptors, and the EXEC-aware no-VINTRP
proof. The latter passes 45 public staged compiler cases and the exact private
MiniGolf shader using the newly linked runtime. Enabled uncompressed MRTZ
reads and the exact ordered `S_SENDMSG 7` boundary are accounted for; unknown
side effects and actual null image entries still fail explicitly. An independent
64-lane CPU model checks 921,600 comparisons per run and detects three unsafe
mutations. These repairs do not establish execution of that shader on Metal.
[Compiler and semantic proof](evidence/anyps5-unused-barycentric-proof-20261010.json).

Fresh preparation uses matching relinker/NID tools and the sealed runtime. It
preserves the four explicit Unity lifecycle selections, relinks twelve ELFs,
resolves 3,186 unique guest NIDs and rehashes all 170 package files. There are no
missing HLE libraries, native imports or guest NIDs; all 127 original dump files
are unchanged. This new package is **prepared only**, awaiting a separately
successful import and fresh-process device run. Native55 remains the installed
host; the older imported package and launch failure below do not test this new
one. [Current preparation evidence](evidence/minigolf-combined-main-preparation-20261010.json).

The subsequent combined-package iPad import stages and reads back all 170 files,
then stops when the own app process reappears during library publication. The
receipt reports attempted publication, no successful return, and a rollback
blocked by the same closed-process guard. The staged folder is retained; this
is a failed import, with the final library state requiring a fresh readback.
The expired earlier baseline is not reused as current evidence. No gameplay
result is attributed to this attempt.

A subsequent read-only check closes the exact own-app process and reads the
library and global configuration again. Both match the original bytes, and the
older MiniGolf package remains selected. This resolves the library-state
uncertainty; it is not a fresh game-file baseline or a successful new import.
The staged combined package remains available for a separately qualified reuse.

## First full-main package and import, 2026-10-09

The [complete upstream integration](ANYPS5-MAIN-INTEGRATION.md) replaces the
earlier selective backports. All 47 real x86-64 HLE PRXs build, and 40 selected
plus ten additional host test targets pass. Their 53 positive cases run under
local Wine with CPU or mock-Vulkan checks. Wine does not expose AVX on this Mac,
so the asynchronous AVX-context subtest is explicitly unverified; native Windows
and FEX/iPad checks are tracked separately.

The matching native tools pass all 37 relinker CTest cases, including actual
emitted-PE constructor/finalizer and deferred-lifecycle fixtures. Fresh MiniGolf
preparation preserves the four explicit Unity module lifecycle selections and
checks **3,186 unique guest NIDs**, with zero missing libraries, native imports
or guest NIDs. All **170 package files**, including the manifest, are rehashed.
The original 127 dump files are unchanged; separately recorded Finder metadata
is the only added input file. None of the game files are committed.

Native55 is an existing signed host artifact. Its 382-file closure and 53 native
host input hashes are independently verified; the HLE package is qualified
separately. Native55 is installed in place with the existing bundle ID. The new
170-file game folder is imported and selected by the existing MiniGolf library
entry. Complete pre/post readbacks verify the new package and 981 files across
five protected older package directories; global configuration is unchanged.
Publication uses one same-directory AFC rename with exact library readback.
The first attempt stopped before publication after an unexpected app restart;
the recovery reused the staged files and closed one exact own-app process.
The restart's cause is unknown. The app and file-service session are closed
after publication. [iPad import evidence](evidence/minigolf-main-ipad-import-20261009.json).
The first device attempt uses the same conservative MiniGolf profile in a fresh
process, without Solitaire's optional stencil or sample-group assumptions.
[Historical preparation evidence](evidence/minigolf-main-preparation-20261009.json).

## First full-main iPad attempt, 2026-10-09

The normal library shortcut selects the exact imported package. Built-in JIT,
the JIT pool and helper detachment are observed, followed by selection of the
Apple M2 GPU. The first live log transfer fails with CoreDevice7000 and a closed
socket; the collector stops its own app/helper and obtains the final owned log.
That log contains `AGC graphics: shader runtime requires nullDescriptor`, with
no observed swapchain creation. The exact fatal-versus-cleanup chronology is
unqualified because this error is retrieved after intentional cleanup.

The new device and typed image-heap code require `nullDescriptor`; the pinned
MoltenVK source explicitly reports it as unsupported. The gate runs before guest
descriptor materialization, so this does not establish that MiniGolf accesses
null images. The subsequent patch0003 implements a `RequiresValidImages` policy:
every consumed guest image base and Vulkan image view is checked before initial
updates and cached replay. Its device-profile, descriptor, graphics and cache
suites pass locally; the device-creation code compiles. Actual null entries still
fail explicitly. This source repair has not yet been exercised on the iPad.
[Descriptor-policy evidence](evidence/anyps5-valid-image-policy-20261009.json).
No screenshots, footprint snapshots, picture, sound or gameplay are qualified
by this interrupted attempt. Global configuration, other library entries and
the Solitaire manifest remain unchanged; full protected-file inventories were
verified during import. [First-launch evidence](evidence/minigolf-main-ipad-first-launch-20261009.json).

## Matched native Windows reference, 2026-10-09

The exact 170-file package runs on the UM790's native Windows 11 installation
with the same conservative compatibility switches. Four CPU tests pass,
including 553 exception deliveries and 64 vectors in each of three AVX modes,
with no errors or internal skips. The physical Radeon 780M creates the Vulkan
device and passes buffer-device-address/8-bit and BC1 texture readback tests.

MiniGolf starts, initializes its 32-MiB save-memory slot and creates an
837×471 swapchain with three actual images. After 93.58 seconds it exits with
`0xc0000409`: the fixed-function interpolation validator rejects a fragment
shader at byte PC 56. It requires unmodified center I/J barycentrics and complete
P1/P2 sequences along a proven control-flow path. This is a concrete shared
shader-path blocker; the validator remains enabled while the shader is examined.
The exception logger truncates the serialized shader request at 1,023 characters,
so the retained request is an incomplete prefix, not a full replay fixture.

The game is not foreground at the two capture checks; no game-window image was
obtained. Neither those checks nor successful offscreen GPU tests establish
rendering or playability. Only the run's own child process trees are stopped,
and its private transfer service is closed. No security or network settings are
changed. [Windows reference evidence](evidence/minigolf-main-windows-reference-20261009.json).

## Complete shader diagnostic, 2026-10-09

A separate native Windows comparison replaces only `libc.prx` and provenance
manifests, retaining all 168 other game-package files. The bounded exception
writer passes twelve real Windows cases; the four CPU tests pass again with
553 exception deliveries and three sets of 64 AVX vectors. Physical GPU
prerequisites pass. The game still exits with `0xc0000409` at PC 56, after
11.13 seconds in this run. It exits before the first window capture, so this
comparison establishes no game picture or performance improvement.

The complete Serializer14 request is now captured: 3,108 base64 characters,
2,331 decoded bytes. An independent helper linked to the unchanged original
shader archive roundtrips its bytes and reproduces the same guard failure both
directly and through full recompilation. The actual pixel metadata declares
perspective-center v0/v1 and position v2/v3, with no interpolation attributes or
VINTRP instructions. Its six-block, 43-instruction loop saves, narrows and
restores the 64-bit EXEC mask. Ordinary vector writes therefore do not establish
that the original input is overwritten for every later active lane.

Patch0002 is now retained in source with the generic writer tests. Patch0004
adds the bounded EXEC-aware proof for shaders without VINTRP. Thirty public
synthetic cases and the exact private request pass actual preparation, capture
and materialization with equivalent final SPIR-V and bindings. The existing
P1/P2 guard stays unchanged, and unknown instruction effects remain rejected.
That initial 30-case compiler qualification is preserved independently of the
subsequent 45-case/current-runtime proof and completed combined 47-library build
above. Neither establishes GPU execution or game output.
[Historical proof evidence](evidence/anyps5-unused-barycentric-proof-20261009.json).
The private shader request and raw logs remain excluded
from Git. The comparison's own process trees and transfer service are closed;
existing packages, saves and system settings are unchanged.
[Complete diagnostic evidence](evidence/minigolf-complete-shader-diagnostic-20261009.json).

The following sections preserve earlier checkpoints. Their numbered patches
belong to the archived `legacy-6e037e98` series; the corresponding repairs are
reconciled in the initial three-patch integration for `d70b8998`; the subsequent
logging and shader/descriptor repairs have their separate qualifications above.

## Preparation checkpoint

The immutable input contains 127 files (1,331,695,275 bytes), uses Unity
2019.4.20f1/IL2CPP and supplies twelve decrypted ELF backups. All input hashes
still match the first inventory. Assets, converted executables, manifests and
raw diagnostics remain in ignored local storage.

- Fresh native relinker and NID-patcher tools were built from the patched source.
  The native host-tools suite passes 33 tests.
- Patch0067 handles omitted inert producer notes while retaining strict bounds
  for runtime segments, symbols, relocations and initializers. All twelve ELFs
  relink, preserving the eleven guest-module paths.
- The dump declares 46 HLE roots. `libSceKeyboard` is an additional native
  dependency of VideoOut, so the distribution contains 47 actual HLE libraries
  and three compiler DLLs. HMD, player-review and object-manager implementations
  are built; no empty replacement libraries are supplied.
- Patch0068 supplies the missing Audio3d object-attribute and flush exports.
  Object PCM/spatial rendering remains explicitly unsupported. This is not an
  audible-output result; see [patch behavior and limits](PATCHES.md).
- All 28 Windows host contracts pass through local Wine. The unchanged memory
  test failed at the host's 8-GiB base and passed at `0x7400000000`; the complete
  suite uses the latter explicitly. The failed address attempt is preserved.
- The final package audit checks 3,186 unique guest NIDs and has no missing
  libraries, native imports or guest NIDs. The immutable package manifest remains
  `prepared_unexecuted`; separate device records track installation and testing.

[Preparation and import record](evidence/minigolf-preparation-20261009.json).

## First runtime failure

The same package reproduces the SaveData startup null read in an isolated
Wine 11 macOS/Rosetta run. This is evidence of a shared startup problem rather
than an iPad-only GPU problem. The comparison was bounded and stopped its own
Wine prefix; it is not a Windows-GPU compatibility or gameplay result.

The failed package's generated bootstrap invokes every retained guest module's
initializer with zero arguments. SaveData's initializer instead parses a
module-start argument block, while that package's `sceKernelLoadStartModule` HLE
discards the caller's arguments. The null read therefore precedes gameplay and
does not establish a renderer failure.

Native54 stayed alive after the guest exited and returned to a library error
dialog. Consequently native process continuity is not counted as a successful
game start. No game FPS, render resolution, course, audio or save/load result
was obtained. The run closed only the project's own main app and JIT helper,
then released the shared device lease.

## Lifecycle repair checkpoint

Frozen patch0069 and promoted patch0070 address the startup contract in source.
The explicit candidate selection defers `Il2CppUserAssemblies.prx`,
`PSNCommon.prx`, `PSNCore.prx` and `SaveData.prx` until Unity's actual
`sceKernelLoadStartModule` call supplies its argument pointer. The recovered
producer supplies a 52-byte argument allocation containing a 16-byte interface
record and callback pointer. Il2Cpp is also linked from the main executable;
that linkage alone does not justify an earlier zero-argument module start.
Bundled libc and PS5Util retain eager initialization. All module mapping,
binding, TLS and ELF validation remain in place.

Bootstrap and kernel APIs use each image's shared versioned start/stop wrappers.
They preserve the full argument count and pointer, prevent duplicate callbacks,
and separate operational errors from the guest's exact return value. A failed
stop retains its result and prevents unload; finalizers that already ran cannot
roll back. Mutable state and executable wrappers occupy separate complete
16-KiB host pages. The default initialization policy remains unchanged for
packages without explicit lifecycle selections, and Solitaire's existing
package and settings are preserved.

The fresh native host-tools suite passes 34 tests. Five synthetic emitted-PE
Wine scenarios, retained-libc constructor/allocation ordering and three rejected
negative controls pass; kernel API contracts also pass native ASan/UBSan checks.
The matched HLE rebuild passes 29 Windows host contracts. A fresh twelve-ELF
package passes the complete dependency audit and is imported into Native54:
all 169 files match device readback. The existing MiniGolf card now points to
the new package through a single same-directory AFC rename. All 303 Solitaire
files, 169 files of the earlier MiniGolf package and global settings are unchanged.
The first corrected launch crosses the old startup failure and creates a
768×432 swapchain with three actual images. A transient device file-service
failure interrupts that collector after about fourteen seconds; it is not a
guest exit. A subsequent bounded retry remains live for 121 seconds with no
reported guest exit. Reviewed captures at 15, 60 and 120 seconds show Madeira's
startup screen rather than a game picture. Native footprint reaches a recorded
peak of 1,770 MiB; this short run does not establish stable resource use. The
collector stops only the app's own processes and releases the device lease.
Global settings, existing library fields and the Solitaire manifest remain
unchanged; the earlier import is the full Solitaire file verification.

This demonstrates progress through initialization, without verifying a complete
game start, picture, audible output or gameplay. The Solitaire card/Undo
regression remains pending. See
[lifecycle implementation and limits](PATCHES.md#explicit-guest-module-lifecycle-anyps5-00690070)
and [packaging selection](PRIVATE-GAME-PACKAGING.md).

## Historical save-memory failure

At this earlier checkpoint, the corrected guest requests a 32-MiB save-memory
slot. Native SaveData rejects that request with `0x809f0000` because its cap is 16 MiB, while the other
SaveData implementation already admits 32 MiB. Patch0071 raises the native cap
to 32 MiB and retains upper bounds, atomic writes and per-user/slot isolation.
This is a bounded compatibility change, not a claim about the platform maximum.

Five local sanitizer checks pass, covering creation, tail access, growth with
existing data, reopening, isolation and write failures. Negative controls reject
the original cap and a removed upper bound. Those native checks use a private
compatibility copy for an existing `chrono::clock_cast` expression unsupported
by the Mac's libc++; the production timestamp code is unchanged. The actual
Windows HLE rebuild now passes all 33 host test targets, including growth and
the separate read-failure case; no CTest case is skipped. A fresh 169-file package
passes the complete dependency audit. Its compiled provider matches the tested
archive, and the original dump and both earlier packages remain unchanged.
The fresh package is now imported into Native54: all 169 files match device
readback. The same library card is retained through AFC rename, with Solitaire's
303 files, the first MiniGolf folder's 169 files and the prior lifecycle folder's
170 files unchanged. The extra prior file is included in the preservation
check. Global settings are unchanged. A fresh bounded iPad launch records
`setupMemory2(size=33554432)` returning zero, followed by the same user/slot's
`getMemory2` returning zero. This qualifies setup and readiness; gameplay
save/load remains open.

## Historical JSON allocator failure

After the save-memory repair, startup reports an unhandled `std::runtime_error`:
`sce::Json::MemAllocator virtual ABI is not implemented; use AllocParamRtti`,
followed by a fatal abort. This is the explicit non-null allocator rejection in
the JSON HLE setter. A swapchain is created, but all three reviewed screenshots
still show Madeira's startup overlay. Native continuity and absence of a guest
exit report do not turn this fatal trace into a successful launch.

The virtual-table contract is now recovered from the original ELF relocations
and unchanged converted instructions. The allocation/release methods forward
to guest libc; notification aborts on the title's allocation-failure code.
Only one of the twelve selected ELFs imports these initialization interfaces.
Its parameter is accessed exclusively through imported methods; the available
stack span does not establish the original class layout.

Patch0072 implements typed guest virtual calls and keeps each block paired with
its creating release function, allocator object and context. RTTI remains a
distinct policy. The existing 24-byte HLE parameter representation is retained;
the explicit setters select its internal allocator kind. Default allocation
does not replace a custom allocation failure. Three native sanitizer suites,
three rejected mutation controls and all 34 Windows host targets pass, including
reentrant callbacks and concurrent policy changes. That 34-target runtime
checkpoint has no qualified iPad clearance of this failure; the later full-main
attempts and newly prepared combined package are recorded separately above. [Detailed contract and limits](PATCHES.md).

[REA's tested investigation route](BINARY-INVESTIGATION.md) confirms the caller
and argument-setting instructions. Its automatic Windows calling convention is
incorrect for the guest, and its first indirect-method query is rejected.
Original ELF/NID/relocation inspection supplies the missing table evidence;
neither tool output alone establishes the complete SDK class ABI.

The collector closes only the project's own processes and releases the device
lease. Global settings, other library fields and the Solitaire manifest remain
unchanged; the immediately preceding import verifies the full protected folders.

## Device profile and remaining checks

The earlier first device run uses the existing Native54 host and a separate
package/working directory, the lazy 4-GiB arena at `0x7400000000`, 256-MiB chunks and the
unchanged global 512-MiB JIT pool. The profile includes automatic built-in JIT,
18 touch controls, FPS-only HUD, fixed-function interpolation, conservative draw
transitions and three swapchain images. Solitaire's sample-group, zero-stencil
and experimental transfer gates are absent.

Unity's original `boot.config` requests 3840-pixel output width. The profile's
1280×720 virtual monitor is a separate setting. The observed swapchain is
768×432 in that Native54 run; game render targets and Metal layer size remain
unmeasured. The first Native55 full-main attempt has no observed swapchain, and
the latest prepared combined package still requires a new device measurement.
A separate private 1080p variant is permitted only if the original has excessive
resource cost; it must retain verified rendering and have its actual resolution
recorded.

The device importer verifies a fresh package before appending its library entry,
backs up and compares Solitaire's full directory, and preserves global settings
and existing entries. It uses a bounded shared-iPad lease with rollback time;
it neither reinstalls the native app nor replaces Solitaire. A fresh native
process is required at every title/profile change.

Remaining acceptance: three library starts, a complete offline course, aiming
and shot strength, ball movement and scoring, touch release, audible music and
effects, save/load after restart, background/resume, and at least 15 minutes of
stable gameplay with FPS, memory and thermal observations. Shared runtime repairs
also require a Solitaire card/Undo regression. A successful preparation, live
process or visible menu does not satisfy these checks.

All builds and tests are local. No GitHub Actions are used.


## PC 112 production attempt, 2026-10-10

The next isolated correction validates mandatory forward control-flow blocks,
active NSA address words and complete register footprints through the terminal
interpolation block. Unknown, indexed or partial accesses remain rejected while
raw center inputs are live or interpolation pairs are pending. It retains the
strict guard and existing interpolation behavior.

A real production relink preserves all **3,725 export names, ordinals and
forwarders plus every import**. Eight new compiler-private autoexports are
hidden, and one previous stateless sort alias resolves locally to the exact
**1,216-byte** relocation-free body verified in both prior and new builds.
The new cache remains schema 22 with identity `409d82e2083d0bae`.

All **484 ordered public cases** and the previous **nine complete requests**
pass through that actual PRX; their SPIR-V and binding layouts remain byte
identical. The tenth complete request passes interpolation validation but fails
subsequently in runtime resource-table evaluation at descriptor source 0, dword 0.
No tenth materialized shader, subsequent null/host suite, new Windows packet or
iPad GPU result is established. The attempt remains failed; its source and
artifacts are retained and its own Wine server closed. The candidate has not
been promoted into the canonical source or game package.
[Actual production attempt](evidence/minigolf-pc112-production-attempt-20261010.json).


The tenth request is now traced to `PrepareRegistered()`: it contains thirty
zero-initialized UserData words and only code plus header memory. This is a valid
shader-registration capture, with no live resource tables. The actual draw path
obtains those inputs later through `ShaderMemory::capture()`. Its failed offline
resource-table evaluation is therefore an expected missing-input rejection, not
a demonstrated resource-table compiler bug. A separate preparation/artifact
test and explicit negative capture test now qualify that boundary; a later live
draw capture is required for full materialization evidence.

The separate successor runs against the unchanged production PRX and preserves
the failed attempt above. Its imported registration fixture successfully runs
`PrepareShader()` and `GetArtifact()`, then confirms the exact rejection of
missing runtime resources by `CaptureResources()`. A wrong-driver control is
also rejected. All **12 null-pixelshader cases** and a fresh **53-target host
suite** pass. The 484 public cases and nine complete requests retain their
actual earlier execution proofs; they are not counted as newly rerun here.

This qualifies a bounded Windows diagnostic package with nine complete shader
replays and one registration/negative-resource gate. It does not establish a
tenth materialized shader, an iPad graphics result or a playable course. The
canonical source and existing game packages remain unchanged until that next
run supplies the required evidence.
[Registration boundary and fresh host tests](evidence/minigolf-pc112-registration-20261010.json).


## Windows run 10: prerequisites pass, next shader guard

The new packet passes **26 prerequisites** on the physical AMD Radeon 780M:
the original sixteen, nine complete resource-bound replays and one separate
registration test. Both compiler suites execute the same 484 ordered cases;
803 explicit-AVX and 701 default exception deliveries pass. The original PC 112
registration request passes preparation and artifact generation while its absent
runtime SRT correctly remains a capture error. It is not a tenth complete replay.

MiniGolf proceeds past that shader and exits after **7.1236738 seconds** with
`0xC0000409` at another interpolation guard, **PC 76**. Its inline serializer-15
request contains code and header regions with thirty zero user-data words. This
allows private registration/compiler analysis, but does not establish actual
resource capture or GPU execution. The owned-window capture reports that the
game exited during capture; no image or direct `.req` snapshot was returned.

The cache remains schema 22 with a fresh policy identity. Fixed-function
interpolation, three 837 × 471 swapchain images and the requested 1920 × 1080
window remain unchanged. All prerequisite and game processes are joined, no
stdout/stderr is discarded, the scoped transfer listener closes, and Smart App
Control is restored through Windows Security with independent registry value 1.
A course image, a first stroke and the iPad graphics path remain open.
[Actual run and independent audit](evidence/anyps5-c963-windows-run10-20261010.json).


## Native57 build: exact LoopTop suspend repair

Native57 is built and signed locally. It embeds a freshly linked ARM64EC JIT
runtime with a narrowly scoped context reconstruction change: for the private
`0xe0425355` suspend exception at exact dispatcher LoopTop on iOS, copy the live
SRA GPR/vector/flag mappings before packing, keeping the already published RIP.
Other dispatcher addresses and exceptions retain their existing behavior. The
original failing log did not print the live SRA stack pointer, so the causal
explanation remains a source-supported candidate until a new device run.

Fourteen native ARM64 captured-state controls and fourteen non-iOS controls pass;
the original source and seven omission/broader-guard mutations fail their exact
assertions. The entire changed production translation unit compiles as ARM64EC,
and the complete runtime is rebuilt from 187 objects with unchanged exports.
The prior table-size/bounds correction remains present in actual object code.
These fixtures verify mapping and packing, not native-call flag preservation or
general native auxiliary-register preservation.

The optimized host retains the bundle ID, Native54 provisioning profiles and
memory/debug entitlements, automatic JIT helper and the seven verified native
archives. The new DLL is the only changed copied layout file. Native55 and
Native56 files remain preserved. **Native57 installation and protected-data
preservation are now accepted; the 50-round Continuing diagnostic, full
803-delivery test, all eight fresh CPU phases and GPU acceptance remain
required.** [Source/native controls](evidence/fex-loop-top-native-controls-20261010.json),
[signed host build](evidence/native57-host-20261010.json),
[accepted installation](evidence/native57-preservation-accepted-20261011.json).

The fresh Native56 pre-installation baseline is now verified by two complete,
independent USB reads with identical hashed inventories. Every readable current
file has an explicit locally replayed provider: 3,461 files totaling
10,909,284,143 bytes. All 2,698 original backup providers remain verified,
including files no longer present on the device. Fourteen current files were
newly copied; other current bytes come from individually approved preserved
providers. The native operation and both observers finish successfully, and
source closure remains unchanged. This proves the accessible baseline, not
opaque SystemData or Keychain contents, Native57 installation, or gameplay.
The observed initial changes do not relax the subsequent update preservation
policy. [Preservation evidence](evidence/native57-preservation-preflight-20261010.json).

## PC76 completed local qualification

The bounded cache-inventory successor now completes the actual production
driver qualification: 538 public compiler cases, nine complete request replays
with byte-identical SPIR-V/layout outputs, two registration-only preparations,
twelve null-pixelshader cases and all 53 fresh host cases. Export names,
ordinals, forwarders and native imports match the prior qualified driver.
One exact owned cache-temp rename race triggers a complete inventory retry;
all resource caps remain active. Both wrong-driver controls and full prefix
cleanup finish with their expected results. Earlier failed runs remain failed.
These CPU results allow preparation of the next Windows package; they do not
prove native GPU rendering, a MiniGolf course, or iPad gameplay.
[Qualification evidence](evidence/minigolf-pc76-qualification-20261011.json).

The subsequent Native57 update attempt reads a full pre-installation inventory
matching the verified baseline, then stops before installation because the
Mac has less than its required 6-GiB planning reserve. The native task and both
observers join. Native56 is not replaced, and no userdata writes are performed
by the installer. [Preservation evidence](evidence/native57-preservation-preflight-20261010.json).
