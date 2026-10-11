# Patches

One series per upstream. `scripts/apply-patches.sh` applies every
`patches/<name>/*.patch` onto `upstreams/<matching-submodule>` in lexical
order. The series are regenerated from the submodule diffs; do not edit a
submodule by hand and forget to refresh the patch.

| Series | Files |
| --- | --- |
| `anyps5` | Eleven patches on `c963432d`: reconciled iPad/Wine runtime, strict shader/image policy, bounded logging/audio diagnostics, frame pacing, large LDS spill, complete descriptor-array snapshots, typed image fallback, macOS cache directory and restored qualified interpolation proofs. See [active series](anyps5/README.md). |
| `madeira` | Forty patches: static Vulkan/binder integration, memory repair, atomic write-fault classification and lifecycle with explicit menu activation, reported display timing, bounded diagnostics, quiet measurement, memory reporting, hardware audio period, menu-app identity and device build checkpoints. |
| `fex` | Four patches on official FEX-2610: reconciled iOS port and local CPU repairs, rpmalloc iOS adapter, opt-in invalidation diagnostics and ARM64EC lookup bounds. Diagnostic instrumentation remains opt-in. `experimental/` is excluded. See [FEX series](fex/README.md). |
| `wine` | Linux portability guards and bounded diagnostics, rebased on `257f271c`. |
| `moltenvk` | Four optional stability fixes (#2853, #2855, #2860, #2861). Default builds retain unmodified `67b26826`; set `APS5_APPLY_MOLTENVK=1` on an isolated checkout to experiment. |

Status, including what was compiled and what was not: [../docs/PATCHES.md](../docs/PATCHES.md).

Each series is a derivative work of its upstream and is distributed under that upstream's license, not under the GPL-2.0-or-later grant in the repository [LICENSE](../LICENSE). `anyps5` stays GPL-2.0-only, `madeira` and `fex` stay GPL-3.0-or-later, and `wine` stays LGPL-2.1-or-later. `moltenvk` patches retain the upstream Apache-2.0 license. See [NOTICE](../NOTICE).
