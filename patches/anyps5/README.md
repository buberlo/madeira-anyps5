# AnyPS5 main reconciliation

Apply all **sixteen** adjacent `.patch` files in lexical order to
`0a8b1d32b12a6d6a3acd462787750b482bf78884`. They form one reconciled series;
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

All 64 apply/check/reverse commands pass; all 2,137 candidate entries and modes
match, reversal restores 2,055 base entries, and eleven gitlinks remain exact.
The actual canonical/build trees and initialized dependencies are independently
compared. Six fresh native shader suites and complete ShaderMemory pass.
The 355/538 public totals combine direct proof checks and admitted compiler
profiles; full linked-runtime, loaded-PRX, native Windows GPU and physical-iPad
qualification remain separate.
[Current source and scoped results](../../docs/evidence/anyps5-0a8b-source-integration-20261012.json),
[technical details and limits](../../docs/UPSTREAM-REFRESH-20261012.md).

No GitHub Actions are used. Private shader requests, provider maps and game
assets are excluded from this series.
