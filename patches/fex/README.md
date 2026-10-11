# FEX-2610 on the iOS host

The gitlink names the official `FEX-2610` commit
`14c92681f4d62cf84d901460e0358de09c8847a7`. Apply this series in order with
`scripts/apply-patches.sh --only fex`.

Rechecked on 2026-10-10 through GitHub's API: the latest
official monthly release and official `main` both still name this commit.
The annotated release tag is peeled before comparing source revisions.
`scripts/check-upstream-heads.py --json` now checks both the monthly release
and `FEX-main`, so post-release changes cannot be missed by checking tags alone.
The Madeira `ios-port-2607` fork baseline is also unchanged; its other `ios-port`
branch is older and diverges from that baseline, so it is not a CPU update.

`0000-ios-port-2610.patch` reconciles the Madeira iOS fork
`3bec2ac498bf78156ab47c0c194b0e8cb2849756` with the complete monthly release.
It retains dual RW/RX JIT mappings, the iOS arena/allocator hooks, TEB/TSD
access, code-pool migration, the 32-bit guest window and Mono bridge. It also
includes all former local patches 0002–0011: resolved-config diagnostics,
opt-in guest/block capture, per-compiler capture state, allocation declaration,
detach notification gating, SysV red-zone preservation and pending upper-AVX
state at protected guest faults. Their individual history remains in Git.

New release adaptations include the shared atomic code-buffer allocator,
direct architectural-state syscall API, Apple cache-line encoding, native
Darwin directory streams and entropy, and nonblocking file-read invalidation.
The latter removes locks held across ordinary reads, but Wine delivery into an
already executed, write-protected code page remains an explicitly failed device
case. It does not qualify all executable-page or asynchronous reads.
The iOS WOW64 module is an explicit adapter in `IosModule.inc`: the pinned Wine
uses the legacy CPU-area protocol, whereas the unchanged canonical module in
the other branch uses CHPE-v2. Both modules use the new FEX core/syscall API.
Compilation of that adapter does not qualify 32-bit applications on a device.

`0001-rpmalloc-ios-port.patch` uses the release's recorded rpmalloc commit
`09142d726429416bfa7b459151515fe3ab7622dd`. It reconciles the Madeira allocator
fork `812c2b9cf4310ffacf14e6b64066e78ab0c394b5`, including its iOS VA bands,
failure diagnostics, license and POSIX logging adapter. No unpublished merge
commit or floating branch is required to reproduce either checkout.

Validate the full overlapping series with `scripts/check-patch-series.py`.
`scripts/check-fex-darwin-utils.sh` tests the actual Apple directory and entropy
implementations on macOS with ASan/UBSan. `scripts/check-async-flags-layout.py`
checks the native/PE exception bridge ABI. Device evidence is separate under
`docs/evidence/`.

`0002-opt-in-invalidation-diagnostics.patch` makes the routine section and
sampled aligned invalidation messages opt-in with exact
`MADEIRA_INVALIDATION_DIAGNOSTICS=1`, cached before initial tracker notifications.
The underlying queries, invalidation and interval removal remain active.
Rebuild all affected FEX objects together because the tracker gains a private
constant flag; a partial replacement into older allocation code is unsafe.
This reduces explicit diagnostic work, without claiming a measured speedup.

`0003-arm64ec-checkcall-lut-bounds.patch` applies the two instructions from
[FEX PR #6021](https://github.com/FEX-Emu/FEX/pull/6021), pinned to commits
`4dbb046d62c57639fd93d433bb64896df7332ff0` and
`3a2b1c0b438fed5062bebff0c5f7c8e21879fe48`. The PR was still open when checked;
it is a local backport on FEX-2610, not a newer merged release. ARM64EC
`CheckCall` now loads its `uint32_t` lookup-table size with `ldr w17` and rejects
an offset equal to that size with `b.hs`. This prevents an alignment-sensitive
64-bit load and an out-of-bounds entry read. Neither defect is an established
MiniGolf failure cause or measured FPS improvement.

Run `python3 scripts/check-fex-checkcall.py` on an ARM64 Mac. Pass
`--pe-compiler /path/to/arm64ec-w64-mingw32-clang` when llvm-mingw is not on PATH;
use a fresh `--output` directory for repeat runs. The test extracts the actual
`CheckCall` body and changes only Darwin object-format symbols and relocations.
Twenty native cases cover empty tables, first/last entries, exact-end and larger
offsets, below-base addresses, nonzero bytes after the size, and both 8-byte and
4-but-not-8-byte size alignment. Protected boundary pages detect deliberate
old-width and old-inclusive-bound mutations. A separate Windows COFF fixture
verifies that the repaired load links with 4-byte alignment while the old load
fails; Darwin linking alone does not establish this Windows relocation rule.
The receipt states explicitly when the COFF check is unavailable.

Changing only `Module.S` requires a new ARM64EC `xtajit64.dll` and app
repackaging/signing. Unchanged native FEXCore and WOW64 archives can be reused
only after checking their hashes and ABI against the signed baseline. The
production object's disassembly must contain both repaired instructions.
Native assembly tests and a PE link do not replace Wine/FEX execution or iPad
call, exception and protected-memory regression checks.
