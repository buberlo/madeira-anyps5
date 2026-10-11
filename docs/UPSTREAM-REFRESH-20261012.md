# Complete upstream refresh, 2026-10-12

The complete AnyPS5 `main` source is pinned at
[`43bc17f7`](https://github.com/boykopovar/AnyPS5/commit/43bc17f7edfc32c38428fd8e4e6d8cc94c8cb31b):
**397 merged commits after `0a8b1d32` and 2,132 after `c963432d`**, including
Apple fixes #1776, #1831 and #2015. Twenty local patches reconcile onto the
2,199-file source map with eleven unchanged vendor gitlinks. All 80 individual
application/check/reversal commands and four combined roundtrip commands pass.
The canonical checkout and actual build source match this map, with all eleven
initialized dependency trees clean at their exact commits. The original
seventeen-patch series is archived separately. Source integration does not
establish a qualified HLE archive, installed 43bc runtime or gameplay.
[Actual source integration](evidence/anyps5-43bc-source-integration-20261012.json).

New merged conversion checks cover ELF/export aliases, instruction rewrite
boundaries, program and section ranges, NONE relocations and SDK syscall traps.
The alias fixture preserves raw symbol/index and rejection checks while naming
exactly the ordinary alias plus the two owned lifecycle exports. New thread
teardown runs key destructors before publishing completion or releasing thread
identity. Linux-ASan arena constants retain their offset; Windows arena
configuration, owned metadata handles and shared-memory dispatch stay distinct.

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
  both fragment pipeline-library keys include the selected sample group. The new
  grouped-library fixture preserves the upstream 4x counter assertions, but its
  GPU execution and sample-location setup remain unqualified. Single-sample
  depth clears use upstream semantics.
  General guest Z/HTILE import, CPU refresh and multisample depth writeback are
  not claimed where the implementation still rejects those combinations.
- **CPU and platform contracts:** protected memory, AVX/flags preservation,
  lazy allocation, save behavior, exact deferred module arguments and honest
  unsupported Audio3d errors remain. Native thread teardown unbinds its wait
  state before freeing it. Optional 60-Hz waits use TimedWait's own clock.

## Current qualification boundaries and historical results

The production safeguards remain: exact interpolation proof and typed fallback,
request/cache policy identity, reserved-register rejection, guest-memory
ownership, descriptor lifetime, grouped color/depth policy and transfer bounds.
Default-profile MSAA policy positive cases are still **unqualified**; they are
not converted into passing results by limiting the tested scope.

The fresh final-source native ARM64 relinker and NID build passes **all 120
actual configured CTests**: 103 relinker cases, 14 root-tool cases, one portable
cache-file-read case and two NID-patcher cases. All prior 110 names remain and
all ten new regression names execute. Configured and executed names match;
there are zero CTest failures or skips. All 2,199 source hashes/modes and eleven
initialized, clean vendor identities match the final review before and after.

This is a fresh build/run, not a relabelled older tool. Existing host guards
still skip incompatible native guest execution inside the Linux guest-stack,
guest-module-argument and lifecycle fixtures while validating their synthetic
output. Those tests do not establish x86-64 guest execution on this ARM64 host
or any iPad result.

The separate fresh Windows HLE route selects 47 libraries and 74 executable
targets: 42 default and 32 additional. Configuration passes, but the two-job
build stops while linking `libkernel.prx`: upstream APR now requires
`GuestArenaHighestFree_nid_no_patch`, which the local libc export list omits.
The function is implemented; a focused export repair is pending. No runtime
tests execute and no qualified archive is exported. Source hashes/modes/mtimes
and all eleven vendor trees remain unchanged; the owned Wine process joins.
[Actual HLE attempt](evidence/anyps5-43bc-full-hle-attempt-20261012.json). The first single-job attempt was
interrupted and retained when the native tools finished; a separate two-job
producer resumes the same immutable source/build without repeating adoption. Loaded production-PRX, native GPU and physical
iPad qualification remain separate.

At the preceding `0a8b1d32` seventeen-patch checkpoint, **all 110 native CTests
passed**: 95 relinker, 13 root-tool and two NID-patcher cases. Source and eleven
vendor trees matched before and after.
[Historical native tool result](evidence/native-host-tools-latest17-20261012.json),
[portable harness](../tools/checks/experimental/native-host-tools/README.md).

The **six native shader suites** and complete no-argument **ShaderMemory**
fixture also passed at that earlier source checkpoint. The 355/538 public
profiles mix direct proof rejection and compilation of admitted profiles;
they do not establish that every negative profile compiles. These are historical
CPU results, not final43b shader or GPU results.
[Retained authored qualification snapshots](../experimental/upstream-qualification-source-snapshot/README.md).

The earlier sixteen-patch runtime attempt compiled all 47 libraries and 49
selected test executables, passed the first 28 default targets and stopped on
the independent thick-volume Graphics fixture. Patch 0017 corrected production
`SW_64KB_D_X` dispatch while preserving the fixture. Subsequent fixture repairs
retain real tiled backing, upstream stencil semantics, cross-block XOR,
format capability queries and the owned lifecycle export assertions. Earlier
failed attempts retain their failure status; they do not qualify this runtime.
[Historical runtime attempt](evidence/anyps5-latest16-full-hle-attempt-20261012.json).

Older 95-case host/relinker, once-provider, 47-library and actual production-PRX
results likewise retain their recorded source identities.
[Scoped once result](../experimental/compiler-once-execution/direct-attempt-observation.json),
[historical roundtrip](evidence/anyps5-thirteen-patch-roundtrip-20261012.json).

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


A separate 45-second exception diagnostic confirms the exact per-game settings
but captures no RTCS pre/post records. It records twelve EC bounce handoffs and
an unhandled native read with PC/LR/address zero; the direct caller and cause
remain unproved. All 50 deliveries, PASS and guest zero exit are still absent.
The collector finishes in 62.731 seconds, restores library/protected metadata
and closes its own process without cleanup errors. This is an incomplete
diagnostic, not CPU acceptance.
[Actual bounded trace](evidence/native60-exception-trace-observation-20261012.json).

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
