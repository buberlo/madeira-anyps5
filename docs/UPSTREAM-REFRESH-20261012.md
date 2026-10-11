# Complete upstream refresh, 2026-10-12

The project now includes the complete checked AnyPS5 `main` snapshot at
[`0a8b1d32`](https://github.com/boykopovar/AnyPS5/commit/0a8b1d32b12a6d6a3acd462787750b482bf78884):
**1,735 merged commits after `c963432d`**, including Apple fixes #1776,
#1831 and #2015. Both the canonical checkout and actual build checkout match
all **2,137 source files and modes**. Eleven nested dependencies are initialized
at their recorded commits and clean. All seventeen local patches pass the full
68-command application/check/reversal roundtrip.
[Actual source and scoped-test record](evidence/anyps5-0a8b-source-integration-20261012.json).
[Additive 3D layout repair](evidence/anyps5-latest17-source-integration-20261012.json).

Madeira main remains `48f97642`. Official FEX main and FEX-2610 remain
`14c92681`; Madeira's FEX iOS-port baseline remains `3bec2ac4`. These match
the queried heads. The FEX #6021 ARM64EC table-bounds correction and the
reconciled iOS integration remain included. Open Madeira experiments are
separate from a complete merged-source update. [Exact pins](UPSTREAMS.md).

## Runtime and shader integration

The first eleven reconciled patches preserve the remaining local runtime,
exception, audio, resource-lifetime, pipeline and relinker behavior. Existing
upstream Apple implementations are used instead of duplicate local versions.
The preceding series and its actual test results remain archived separately.

- **Compiler exceptions:** patch 0012 routes owned MinGW direct calls and IAT
  slots through one four-byte Windows once provider with DWARF cleanup.
  An exceptional callback resets the once state and wakes waiters before
  rethrowing; successful callbacks publish writes. Native compiler DLL internals
  and guest once objects are unchanged. The existing 1,061 libc exports are
  preserved and one private NID-exempt provider is appended. Reconciliation
  retains the original destructor/retry regression alongside upstream's new
  guest-frame exception checks.
- **Exact interpolation:** patch 0015 gives the original-instruction guard a
  specific error type. Only that error in a pixel shader without native
  barycentrics selects upstream's exact emulation. Original I/J reads and
  P1/P2 operations are translated rather than replaced by an unproved shortcut.
  Other failures propagate. Geometry, device capability, BDA and resource
  validation remain in force. Raw-I address calculations retain the checked
  interlock fault exits in both emulated and native paths.
- **Requests and caches:** request version 17 and cache format 28 include local
  placeholder/sample policy and pipeline identity. Old cache entries are
  rejected. Historical private version 14/15 requests require the explicit
  `--legacy-ipad-v14-v15` replay mode and are never silently rewritten.
- **Graphics resources:** pipe/bank XOR, logical sample count, descriptor
  ownership and real transfer restrictions remain. Grouped-sample profiles use
  separate device/cache/pipeline identity and disable GPL before construction;
  normal profiles retain GPL. Single-sample depth clears use upstream semantics.
  General guest Z/HTILE import, CPU refresh and multisample depth writeback are
  not claimed where the implementation still rejects those combinations.
- **CPU and platform contracts:** protected memory, AVX/flags preservation,
  lazy allocation, save behavior, exact deferred module arguments and honest
  unsupported Audio3d errors remain. Native thread teardown unbinds its wait
  state before freeing it. Optional 60-Hz waits use TimedWait's own clock.

## Test corrections and actual results

Patch 0013 tests ENOENT and an unchanged directory timestamp without writing
the current directory's timestamp. Patch 0014 supplies real R64KB_X backing
for multisampled color fixtures, tests upstream stencil-clear semantics, and
retains reserved-register rejection. Patch 0016 corrects a test oracle that
masked global X coordinates in 4-KiB XOR layouts. Explicit X32/Y32 assertions
now retain the cross-block bit contributions. These changes do not relax
production tiling, MSAA, depth or reserved-register validation.

All **six freshly compiled native shader suites pass**: placeholder images,
device profiles, cache/request identity, unused barycentrics, LDS CPU behavior
and extended public profiles. The latter suites retain their ordered **355
and 538** cases. Unsafe fixed-function profiles test the original-instruction
proof directly with the typed rejection; admitted profiles still execute
Prepare/Capture/Materialize/Recompile and compare final SPIR-V and bindings.
Forged metadata and nonstandard raw-register controls retain their direct proof
assertions. These totals are mixed proof/compiler coverage, not a claim that
all negative profiles compile through exact emulation.

The complete no-argument **ShaderMemory** fixture also passes, including the
new sRGB depth-comparison checks. GPU execution on the iPad is separate.
Earlier failed attempts and their logs remain unchanged locally.
[Authored qualification source snapshots](../experimental/upstream-qualification-source-snapshot/README.md).

The complete **47-library Windows HLE rebuild and all 49 selected test
executables compile**. The runtime attempt passes the first 28 default targets
and stops in Graphics: a 3D `SW_64KB_D_X` texture is incorrectly dispatched to
the thin layout, producing 1,048,576 bytes where the independent Addrlib fixture
requires 262,144. Patch 0017 routes this format to the existing thick-volume
layout; all 202 independent address expectations and rejection guards remain
unchanged. A fresh complete seventeen-patch build and test run is underway.
The remaining default targets and seven additional targets,
including all four registered ShaderMemory cases, still require the full run.
No qualified archive was exported from this failed attempt.
[Actual build and failure](evidence/anyps5-latest16-full-hle-attempt-20261012.json).
The local test host
uses the independently probed lazy arena at `0x7400000000`, 4 GiB reserved in
256-MiB chunks. Earlier complete-refresh memory and exception tests passed with
this arena; that result does not establish allocation on the iPad.
[Actual test-host observations](../experimental/windows-placeholder-host-probe/actual-observation.json),
[preceding runtime attempt](evidence/anyps5-latest-memory-host-run-20261012.json).

The native ARM64 conversion tools have also been freshly rebuilt for this
seventeen-patch source. **All 110 registered CTest cases pass**: 95 relinker,
13 root tooling and two NID-patcher regressions. Source and all eleven vendor
trees match before and after the run. Existing host guards inspect emitted
x86-64 images without attempting incompatible guest execution; this result
qualifies the conversion tools, not the game or HLE runtime.
[Actual native tool results](evidence/native-host-tools-latest17-20261012.json),
[portable build harness](../tools/checks/experimental/native-host-tools/README.md).

The earlier **95 host/relinker passes**, scoped once-provider execution and
older 47-library/production-PRX results retain their source identities. They
are not automatically results of the current seventeen-patch runtime.
[Scoped once execution](../experimental/compiler-once-execution/direct-attempt-observation.json),
[historical thirteen-patch roundtrip](evidence/anyps5-thirteen-patch-roundtrip-20261012.json).

## Physical iPad and MiniGolf

**The preceding Native59 diagnostic** captured an unhandled
native read with PC/LR equal to 2 after context restoration. The sampled
allocator lock was free and native critical depth was zero; neither observation
proves the cause. The collector restores its library and protected metadata,
closes its own process and releases the device.
[Actual observation](evidence/native59-owner-sampler-observation-20261012.json).

**Native60 is installed, but its Original50 CPU attempt remains incomplete.** Its experimental
EC continuation candidate compiles 187 ARM64EC objects, 50 fresh native objects
and nine retained FEXCore members. The app uses matching FEXBridge headers and
archives, verified translator bytes, signature, entitlements and dSYM identity.
It retains the older HLE payload to isolate CPU behavior. The completed update
preserves protected accessible data, verifies opaque metadata and accepts only
the exact system-artifact policy. The installer and both observers join with
no error. Opaque file contents and independent installed-binary readback are
not claimed; no CPU-delivery or gameplay result follows from installation.
Earlier preflight refusals remain preserved.
[Actual preserving installation](evidence/native60-preserving-installation-20261012.json),
[actual native build](evidence/native-ec-continuation-native-build-20261012.json),
[signed app](evidence/native60-local-build-signature-20261012.json),
[candidate source](../experimental/native-ec-continuation/README.md).

The subsequent unchanged Original50 fixture begins after automatic JIT, but
does not produce all 50 deliveries, PASS or a guest zero exit during the
120-second observation. The collector finishes in 137.148 seconds, restores
the library and protected metadata and closes only its own process, with no
cleanup error. The quiet log does not prove a fault cause or recurrence of
Native59's PC/LR=2 failure. Further CPU phases and game execution stay gated.
[Actual CPU observation](evidence/native60-original50-observation-20261012.json).

MiniGolf is **not yet demonstrated playable**. Next are complete linked-runtime
and loaded-PRX qualification, fresh twelve-ELF preparation, the preserving host
update and full CPU probes, then course rendering and a complete offline course.
Boots on another CPU/OS/GPU path do not qualify this iPad's Wine/FEX context
handling or Unity rendering. [MiniGolf records](MINIGOLF.md).

All builds and tests run locally. **GitHub Actions remain disabled.** Dumps,
pairing and raw diagnostics stay outside Git. The storage cleanup freed
68,189,360,128 allocated bytes; required MiniGolf inputs, authored source,
toolchains and active preservation providers remain.
[Cleanup record](evidence/local-storage-cleanup-20261012.json).
