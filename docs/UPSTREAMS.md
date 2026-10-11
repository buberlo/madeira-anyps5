# Pinned upstreams

Rechecked 2026-10-12. `git submodule status` checks local checkouts. The table
records fixed source inputs; subsequent upstream movement needs a new review.

| Path | Remote | Commit | Branch |
| --- | --- | --- | --- |
| `upstreams/AnyPS5` | https://github.com/boykopovar/AnyPS5.git | `0a8b1d32b12a6d6a3acd462787750b482bf78884` | `main` |
| `upstreams/Madeira` | https://github.com/willfaust/Madeira.git | `48f976429c189f8396e23d251d8a82f43c705922` | `main` |
| `upstreams/FEX` | https://github.com/FEX-Emu/FEX.git | `14c92681f4d62cf84d901460e0358de09c8847a7` | `FEX-2610` tag |
| `upstreams/wine` | https://github.com/willfaust/wine.git | `257f271cfffed9f22f7987cac53bc00095d092fe` | `madeira-lgpl` |
| `upstreams/MoltenVK` | https://github.com/KhronosGroup/MoltenVK.git | `67b2682699d7903606b97a0392061d85d27d49e6` | `main` |

Madeira's tree also gitlinks, at its pinned commit:

| Gitlink | Commit | Vendored here? |
| --- | --- | --- |
| `FEX` | `3bec2ac498bf78156ab47c0c194b0e8cb2849756` | overridden by official FEX-2610 + local iOS port |
| `wine` | `257f271cfffed9f22f7987cac53bc00095d092fe` | yes, `upstreams/wine` |
| `dxmt` | `db546ee466ad50ec6463edb5fa183de11db43761` | no |
| `madeira-dock` | `72558e416a390f3669457930f09a389e54f49556` | no |

`scripts/link-madeira-siblings.sh` points `upstreams/Madeira/FEX` and
`upstreams/Madeira/wine` at the sibling checkouts when those directories are
empty. DXMT stays out until a build needs the D3D path.

AnyPS5's own nested submodules (SDL, Vulkan-Headers, glslang, SPIRV-Tools,
VulkanMemoryAllocator, FreeType, FFmpeg, stb, LibAtrac9) are not pinned in
the parent. `scripts/m0-build-anyps5.sh` runs
`git submodule update --init --depth 1` inside AnyPS5, which fetches the
commits AnyPS5 itself recorded. Vulkan-Headers inside that pin is
`2fa203425eb4af9dfc6b03f97ef72b0b5bcb8350`.

Clones are shallow (`--depth 1`) except where a submodule add had already
fetched a branch tip. The gitlink is the full commit id either way.

The [2026-10-08 refresh report](UPSTREAM-REFRESH.md) preserves the earlier
AnyPS5 update and reconciliation of the local patch series. The current table
records the 2026-10-12 check, retaining the official monthly FEX release.
Madeira main, official FEX main/release and the Madeira FEX iOS-port baseline
required no additional pin change. Later upstream movement is separate.
Installed game packages have separate provenance and do not change when this
source pin is updated.

## Complete main refresh, 2026-10-12

AnyPS5 includes all **1,735 merged commits** after `c963432d`, including
Apple fixes #1776, #1831 and #2015. Sixteen reconciled patches retain the
iPad runtime and strict shader/resource contracts. Fresh application and
reversal pass all 64 commands. Both actual source checkouts match all 2,137
files and modes; eleven dependency trees are initialized at their exact
recorded commits and clean.

Current shader requests use version 17 and disk caches use format 28; old
cache entries are rejected. All six freshly built native shader suites and
the full new ShaderMemory fixture pass. Complete linked-runtime, native
Windows GPU and iPad qualification remain separate. Earlier 95 host/relinker
passes belong to the preceding complete refresh; they are retained as
historical evidence. [Current reconciliation and test boundaries](UPSTREAM-REFRESH-20261012.md),
[actual source/scoped results](evidence/anyps5-0a8b-source-integration-20261012.json).

Madeira `main`, official FEX `main`/FEX-2610 and Madeira's FEX `ios-port-2607`
baseline all matched the checked heads. The FEX #6021 backport remains
included. Unmerged Madeira experiments are not treated as required updates.
These are fixed checked inputs; later upstream movement is a separate refresh.

## Historical targeted Apple GPU additions, 2026-10-11

At this checkpoint the AnyPS5 pin was `c963432d`. Its existing macOS/Apple changes #927, #1565,
#1571 and #1580 are retained. Three later changes are explicit local backports:
merged #1776 (`b7502114`) spills oversized compute LDS to a per-workgroup storage
buffer; merged #1831 (`b23bd732`) preserves complete descriptor-array ranges
during draw snapshots; open #2015 (`b288aa84` head) supplies typed placeholder
images with stricter local feature, ownership and policy checks. A separate
macOS cache-path correction was required by the unchanged native cache test.
The active series now contains eleven patches and reverses cleanly.

These scoped additions do not claim the entire later upstream main branch.
Native ARM64 CPU tests pass. The fresh 47-library Windows HLE build also passes
54 host cases under local Wine, plus 538 actual-PRX compiler cases, nine full
replays and twelve null-pixel cases. Actual GPU/game qualification remains
separate. [Implementation, source identities and limitations](APPLE-GPU-20261011.md).

## Historical MiniGolf refresh, 2026-10-10

The complete AnyPS5 snapshot adds all 424 merged commits after `d70b8998`.
All six local patches were reconciled, preserving protected guest memory,
AVX/flags delivery, module lifecycle, save behavior, strict Audio3d errors,
descriptor policy and the EXEC-aware interpolation proof. Fresh application
matches 216 reviewed files exactly; reversal restores their upstream contents
and modes. Schema 22 rejects prior shader caches and retains local policy
metadata. A new installation uses a distinct shader-cache directory.

The local graphics patch also adopts the null-pixel fixes from
[#1902](https://github.com/boykopovar/AnyPS5/pull/1902) and
[#2022](https://github.com/boykopovar/AnyPS5/pull/2022), retaining refusal of
color-writing draws without a pixel program. The MiniGolf sample pattern
`0x22eea66a` has a production-decoder regression. Existing format/sample queries,
guest-memory import, invalidation and writeback remain required. This is source
integration; the fresh complete runtime, native Windows comparison and physical
iPad draw must be qualified separately.

Madeira, Wine, MoltenVK and official FEX main/release match the pins above.
FEX #6021 is a separate unmerged backport. Madeira #227 remains excluded;
#228 is an audio experiment requiring measured underruns, and #211 is reserved
for an observed alias fault. No optional change is treated as a MiniGolf fix
without matching runtime evidence.

## Checking for subsequent updates locally

```sh
python3 scripts/check-upstream-heads.py
python3 scripts/check-upstream-heads.py --json
```

The check compares indexed pins with live branch heads and the latest canonical
FEX monthly tag, and does not change
sources or execute builds. Exit 0 means all five matched at the reported time,
exit 1 means newer commits require integration, and exit 2 means at least one
query failed. A failed network query is never reported as current.
Run it before upstream refreshes. For updates, fetch the full merged branch
snapshot, reconcile the entire local patch series, verify clean application and
reversal, rebuild and run the affected local tests, then update the reviewed
pin. Preserve historical device evidence and qualify newly built packages
separately. Do not use floating branches as build inputs. No GitHub Actions are
used; this command does not schedule automatic runs.

## Historical checkpoints, 2026-10-08

The following records describe earlier source and installed-package states;
the current pins and qualification status are recorded above.

The same-day [follow-up snapshot](evidence/anyps5-followup-20261008.json)
adds all 200 subsequently merged AnyPS5 commits at `8388121a`. All 33 local
patches were reconciled, including the newer HTTP2 completion routing, NP
callback registration errors, UTF16 helpers, graphics fixtures and host-blocked
exception synchronization. The ARM64 host tools pass 30 tests, the production
interpolation guard passes 111 cases, and four sanitizer contract groups pass.
The new Windows HLE snapshot and actual game still require rebuilding and
qualification.

The [FEX-2610 integration record](evidence/fex-2610-integration-20261008.json)
separates source reconciliation, builds and bounded device checks. The FEX pin
now names the official release. Its [four active patches](../patches/fex/README.md)
carry the iOS port, allocator adaptations, optional diagnostics and the isolated
ARM64EC lookup correction from PR #6021. The latter passes 20 native assembly
cases, a Windows COFF alignment check and a fresh full DLL build; device execution
and any MiniGolf benefit remain separate. [CheckCall qualification](evidence/fex-arm64ec-checkcall-20261010.json).
Monthly releases are always checked;
`--fex-release` also emits that result as a separate JSON field for older consumers.
The earlier [merge audit](evidence/fex-2610-ios-port-audit-20261008.json) remains a
historical pre-integration record.

The final same-day AnyPS5 pin is `6e037e98`: the standalone native tools pass
32 tests, all 33 patches match the reviewed source and reverse cleanly, and
interpolation/sanitizer checks pass. These source changes are not yet rebuilt
into the installed game's Windows HLE package.

The subsequent [color/sample layout checkpoint](evidence/solitaire-msaa-color-layout-20261008.json)
adds AnyPS5 patch0034. All 34 patches apply from the pin, match the checked
source and reverse back to the pin. The production CPU layout passes an
independent AMD AddrLib comparison, including retained pipe XOR above
macroblock boundaries. Multisampled guest draws still require renderer
integration; this patch is not in the installed game package.

The following [renderer component checkpoint](evidence/solitaire-msaa-renderer-integration-20261008.json)
adds patches0035–0039. All 39 patches reproduce the checked source and reverse
cleanly. CPU color transfers and depth/stencil layout comparisons pass focused
tests; the actual production color image owner preserves eight sample values
on the iPad as two four-sample layers. Depth allocation and repeated-shader
eligibility have source-level tests. Full guest draws, GPU transfers and
depth/stencil rendering are still pending, and the installed game's HLE package
has not been rebuilt with these components.
