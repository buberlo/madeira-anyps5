# AnyPS5 full main reconciliation

Apply all twelve adjacent patches in lexical order to upstream
`a11c8f7f70a0ed4e71504a89de69e8cdae687817`. They replace the prior c963
local series. The merged upstream implementations of LDS device memory,
descriptor snapshots and typed placeholder images are retained; only the
remaining local policy, lifetime, compatibility and sample-group changes
are applied here. This is a complete main update, including the new
upstream runtime and shader architecture.

The patches group runtime compatibility, bounded exception/context
handling, strict request17/cache28 image policy, original-IR interpolation
proofs, bounded AudioOut tracing/pacing, grouped color transfers, grouped
depth/stencil contracts, descriptor/resource lifetime, device/PSO profiles,
guarded module lifecycle/relinker, integration/regression tests, and scoped
native compiler-once exception delivery. All twelve are required together.
The upstream gitlinks remain unchanged.

Patch 0012 routes newly linked owned MinGW callers' direct `pthread_once`
calls and import slots through a four-byte Windows once provider with DWARF
cleanup. Guest once objects and native compiler DLL internals are unchanged.
It preserves the original 1,061 libc exports and appends one private,
NID-exempt provider. The original Windows exception fixture and all eight
focused once cases pass in the isolated actual build. The fresh complete
47-library build is running; full runtime qualification is still pending.
[Actual scoped result](../../experimental/compiler-once-execution/direct-attempt-observation.json).

Native compilation and all six shader suites pass, including the 538-case
extended public guard suite. All 95 native host/relinker tests pass. The
last two Graphics.cpp API argument corrections separately pass syntax.
These checks do not prove full HLE, Windows/iOS runtime, GPU execution or
gameplay. Original historical receipts and failures remain unchanged.

Request17 and cache28 carry the local image/sample policy and fixed push
slot identity. Default decoding follows the strict upstream layout.
Retained private14/15 requests require the explicit
`--legacy-ipad-v14-v15` loader option and are not altered. Profile/cache/PSO
keys separate grouped samples, actual null-image capability, placeholder
policy, GPL choice and per-stage push offsets. Explicit sample groups
disable GPL before profile construction; other profiles retain GPL.

Single-sample depth/stencil clear semantics follow upstream. Grouped
clears retain the stricter sample-equivalence proof. General guest depth
import, CPU-dirty depth refresh and depth writeback are not established by
this source; grouped depth transfer remains rejected. Existing real
capability and format checks remain required.

The private proposal provenance records every changed file and source/receipt
digest. The first eleven patches were fully applied and reversed. The new
seven-file patch separately passes application and reversal; all 2,136 files
of the fresh twelve-patch build source match the canonical patched source.
No GitHub Actions were used.
