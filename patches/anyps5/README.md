# AnyPS5 main reconciliation

Apply all **twenty** adjacent `.patch` files in lexical order to
`43bc17f7edfc32c38428fd8e4e6d8cc94c8cb31b`. They form one reconciled series;
archived subdirectories describe earlier pins and are not applied to this one.
The complete merged upstream includes Apple fixes #1776/#1831/#2015.

Patches 0001–0011 preserve runtime/exception compatibility, protected guest
memory, request17/cache28 policy, exact original-instruction interpolation
proofs, audio pacing, grouped transfer restrictions, resource ownership,
device/PSO identity and deferred module lifecycle. Upstream implementations are
retained where they supersede local code. Real capability and format checks
remain required; general guest multisample depth transfer is not established.

- **0012** routes owned MinGW direct and imported `pthread_once` calls through
  a shared four-byte provider with DWARF exception cleanup. It preserves all
  1,061 existing libc exports and appends one private NID-exempt provider.
  Original destructor/retry coverage remains alongside upstream guest-frame
  tests. Guest once objects and native compiler DLL internals stay unchanged.
- **0013** checks empty-path utimes errors and unchanged timestamps without
  writing the current directory timestamp.
- **0014** corrects stale graphics fixtures for tiled MSAA storage, upstream
  single-sample stencil-clear behavior and reserved-register error diagnostics.
  Production validations and negative cases remain.
- **0015** catches only the typed fixed-function proof rejection and uses
  upstream exact barycentric emulation. Other errors propagate; original I/J
  arithmetic and interlock fault exits remain. Proof-negative fixtures test
  the guard directly; admitted profiles retain full compiler execution.
- **0016** retains global coordinate bits in the 4-KiB XOR test oracle and adds
  explicit cross-block X32/Y32 assertions. Production tiling is unchanged.
- **0017** routes 3D `SW_64KB_D_X` textures to the existing thick-volume layout,
  matching Addrlib's display-swizzle classification. The independent size and
  202 address expectations remain unchanged; 2D, Z/R and rejection paths retain
  their existing behavior. Actual complete runtime qualification is pending.
- **0018** keeps the POSIX `HostPoll` implementation inside its platform guard,
  allowing the Windows translation unit to compile without unavailable types.
- **0019** gives the depth-format fixture a real D32S8 capability response.
  Production format validation and the strict negative cases remain.
- **0020** checks the ordinary alias together with the two owned lifecycle
  exports. Names, unique ordinals, RVAs and wrapper instructions are validated;
  conflicting-symbol and relocation cases retain their original assertions.

The rebase retains Linux-ASan's arena offset, adapts structured sample state,
and includes the selected sample group in both fragment pipeline-library keys.
The new eight-sample library fixture checks distinct groups and repeat hits;
its GPU execution and sample-location capability setup remain unqualified.

All 80 individual and four combined apply/check/reverse commands pass. The
actual canonical and build trees match all 2,199 source hashes/modes; eleven
initialized dependency trees retain their exact clean commits. The freshly
built native conversion tools pass all 120 CTests, without failures or skips.
The original seventeen-patch series remains in `legacy-0a8b1d32`.

Upstream default MSAA/CMASK/FMASK positive fixtures retain their expectations.
They expose a remaining boundary with our guarded guest sample import and
writeback policy; full HLE/runtime qualification cannot be claimed before they
pass. Older six-suite shader and ShaderMemory results remain historical.
Loaded-PRX, native GPU and physical-iPad qualification are separate.
[Current source and scoped results](../../docs/evidence/anyps5-43bc-source-integration-20261012.json),
[technical details and limits](../../docs/UPSTREAM-REFRESH-20261012.md).

No GitHub Actions are used. Private shader requests, provider maps and game
assets are excluded from this series.
