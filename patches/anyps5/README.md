# AnyPS5 runtime patches

The active files in this directory are applied in lexical order to the pinned
AnyPS5 submodule. The current source stack contains eleven patches:

1. `0001-ipad-runtime-compatibility.patch`: reconciled iPad/Wine compatibility,
   title-facing runtime repairs, guarded graphics paths and regression tests.
   It now owns the unused-barycentric proof and its public fixtures. The exact
   literal-to-M0 write and payload-free thread-trace instruction have bounded
   effects; M0 reads, other encodings and modified interpolation inputs remain
   rejected. A local policy tag changes the source-derived cache identity while
   retaining disk schema 22.
2. `0002-bounded-exception-logging.patch`: direct stderr exception output in
   bounded chunks, preserving complete shader requests up to one MiB and marking
   larger messages explicitly. Includes short-write, failure, allocation and
   guard-page tests. Guest exception ABI and custom terminate handlers are unchanged.
3. `0003-valid-image-descriptor-policy.patch`: use native null image descriptors
   only when enabled by the actual device. Otherwise require valid guest image
   addresses and Vulkan image views before initial or replayed descriptor writes.
   Request version 15 and cache keys preserve the policy; versions 1–14 default
   conservatively to valid images. This does not emulate null images.
4. `0004-no-vintrp-exec-aware-input-liveness.patch`: for shaders without VINTRP,
   prove that declared barycentric inputs are overwritten before every use.
   The bounded must-analysis models admitted register widths, EXEC changes,
   saved masks, predecessors and loops in the original guest CFG. Unknown
   effects fail closed. Scalar-buffer x4/x8, full packed conversions, plain MAD
   and 2D/3D implicit-LOD samples retain read-before-write and saved-mask guards.
   Plain scalar-buffer x2, array/MSAA image loads, admitted lane arithmetic and
   MRT0–7 color exports model exact source/destination widths and metadata.
   WQM requires a single straight-line block, whole-quad definitions and
   same-epoch helper coordinates. Exact internal MinGW export exclusions preserve
   the existing DLL interface. Existing P1/P2 validation remains unchanged.
   Its proof/header/test hunks were consolidated into patch0001; the remaining
   integration and export hunks stay in this patch.
5. `0062-bounded-legacy-audioout-ingress-trace.patch`: default-off
   bounded input/enqueue diagnostics.
6. `0065-audioout-frame-pacing.patch`: opt-in legacy AudioOut cadence, using
   upstream's precise wait and releasing the port lock while sleeping.
7. `0066-compute-lds-device-memory.patch`: backport merged upstream #1776.
   Compute LDS that would exceed the actual device's shared-memory limit uses
   a coherent storage-buffer slice per workgroup. It retains bounds, barriers,
   atomics, indirect-dispatch sizing and recorder ownership. The upstream GPU
   regression is included; it has not yet been executed for this stack.
8. `0067-descriptor-array-snapshots.patch`: backport merged upstream #1831.
   A draw snapshot rewrites the complete affected storage-buffer descriptor
   array from element zero, preserving every untouched buffer, offset and range.
   This avoids MoltenVK's partial-array update path. Both the existing descriptor
   copy and `APS5_EXPLICIT_DRAW_DESCRIPTORS=1` replay paths remain available.
9. `0068-typed-null-image-placeholders.patch`: local integration of unmerged
   upstream #2015, with a distinct `TypedPlaceholders=2` policy. Supported missing
   image descriptors use real, zero-initialized typed images. Native-null policy
   still requires the actual enabled device feature, and valid-image policy
   still rejects missing images. Exact format/sample/feature checks, initialization
   completion, cleanup and request15/cache22 policy identity are retained.
   The fallback has explicit semantic limits; it does not emulate Vulkan null
   descriptors.
10. `0069-macos-shader-cache-directory.patch`: use macOS's executable-path API
    for the native compiler's default cache directory. The existing cache test
    exposed an empty result from Linux's `/proc/self/exe` on macOS. Windows and
    Linux paths, explicit overrides and cache-disable precedence are unchanged.
11. `0070-restore-qualified-interpolation-proofs.patch`: restores the previously
    qualified SCC skip, mandatory forward-DAG and optional interpolation-group
    proofs. The two headers match the historical actual-PRX-qualified inputs.
    Fresh decoding, complete P1/P2 pairs, unchanged I/J, path-safe definitions
    and immutable M0 remain required. The cache policy tag distinguishes this
    source. The new native 538-case regression exposed the omitted restoration;
    its expectations and the canonical 355 cases are unchanged.

The full upstream `main` snapshot is `c963432db05f8b35c62e212b3a36494501522fe2`,
including all 424 commits after the previous `d70b8998` pin.
Its new prepared shaders, typed descriptor heaps, runtime ABI checks and complete
instruction inventory are retained. The local patch changes are not a rollback
to the old shader architecture.

Upstream #927, #1565, #1571 and #1580 are already ancestors of this pin. The three
2026-10-11 additions above are targeted backports; they do not change the pin or
claim to incorporate all later upstream main commits. The exact eleven-patch
application, source comparison and reversal passed. The fresh 47-library runtime
passes 54 local host cases, and its actual production PRX passes 538 public
compiler cases, nine complete replays and twelve null-pixel cases. All nine
SPIR-V/layout outputs match the previous qualified results. GPU and gameplay
qualification remains pending. See
[Apple GPU integration and limits](../../docs/APPLE-GPU-20261011.md).

The 2026-10-10 reconciliation retains shader-cache schema 22 with the local
descriptor/interpolation policy fields; prior formats are rejected. The new
NtContinue/winpthread exception retry is reconciled with wait reservations,
AVX/flags and protected-store delivery. Audio3d retains explicit unsupported
PCM/render errors rather than reporting successful rendering without output.

Patch0001 additionally includes the #1902/#2022 null-pixel registration and
unset-address corrections, plus ABI/preparation regressions. Depth-only draws
can use the null program; color output without a pixel program remains rejected.
The production sample decoder tests MiniGolf's exact `0x22eea66a` pattern and
retains its strict rejection controls. Existing depth-format/sample queries and
guest coherence are preserved. Separate actual materialization and GPU tests
remain necessary.

`legacy-6e037e98/` preserves the original 75-patch series and its hashes for
historical evidence. Build/apply scripts use `*.patch` directly in this directory
and never recurse into that archive. Do not apply the historical stack to the
new pin.

[Integration and qualification](../../docs/ANYPS5-MAIN-INTEGRATION.md) explains
source coverage, retained runtime behavior and the separate device acceptance.
The earlier six-patch qualified `c963432d` runtime passes 53 host cases, 302 public cases through
the actual PRX and seven complete MiniGolf requests. Native Windows passes all
sixteen prerequisites but the game stops at an additional strict proof failure.
The subsequently promoted instrumentation correction passes isolated native
controls; its new 355-case production fixture, eighth complete request and
fresh game execution remain separate qualification steps. See
[MiniGolf](../../docs/MINIGOLF.md).

The later six-patch PC 76 qualification records 538 ordered public compiler
cases and nine complete shader replays, with separate registration/null-pixel
and host checks. Those historical results are preserved in
[its qualification record](../../docs/evidence/minigolf-pc76-qualification-20261011.json).
They do not qualify the new eleven-patch runtime or establish a rendered MiniGolf
course. All builds and tests remain local, without GitHub Actions.
