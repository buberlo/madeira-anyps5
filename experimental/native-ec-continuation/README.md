# Experimental native EC continuation snapshot

This opt-in checkpoint repairs only the initial native LR snapshot at the exact
EnterEC → first LoopTop instruction. It is outside the default patch series.
The candidate is a source-supported hypothesis, not an established fault cause
or CPU, GPU, MiniGolf startup or gameplay acceptance.

Apply `candidate.patch` only to a disposable FEX checkout at
`14c92681f4d62cf84d901460e0358de09c8847a7` with the existing default FEX patches and
the two additional FEX patches from `../native59/patches/fex/` applied in order.
The manifest pins the exact three before/after source hashes; stop if any differ.
The published patch is byte-identical to the isolated candidate. No canonical
upstream, default patch list, signed application or device data is changed here.

EnterEC invalidates the old record first, captures live x30 and exact native SP,
and publishes its target last. Ordinary and EC FillSRA, the instruction after
the advertised LoopTop load, and stop entry invalidate the record. The snapshot
selector requires the private exception, exact LoopTop PC, current-frame target
and RIP equality, saved/live SP and LR equality, matching packed PC/SP, and
reverse-mapped native EC membership through `RtlIsEcCode`.

The selector changes only the initial packed LR. It does not change State.mm,
other auxiliary registers, flags, YMM packing or NtContinue. Existing Wine
converters therefore preserve a later intentional handler LR edit. FillSRA's
live link and synthetic x64 targets remain distinct from a native EC caller link.

The historical isolated ARM64 run passed 42 candidate controls and 16 non-iOS
controls. The original and four effective mutants failed their intended
assertions; all 22 compile/link/run children joined. The fixture executes a real
ARM64 RET using the resulting PC/LR/SP. It uses an adapter context layout and
stubbed EC membership/flag reconstruction, not an official Windows ABI or a
production FEX dispatcher/server. A separate probe using the real ARMEmitter
passed 12 encoding and publication-order controls. The manifest binds these
historical receipt digests without publishing local provider maps or logs.

Actual native CoreState size was 3904 before and after the candidate; the new
24-byte record fits existing tail padding. Old offsets were unchanged. This
does not establish the Windows target layout. The production rebuild's first
attempt failed the unchanged CPUID version-length assertion; the separately
reviewed attempt uses a shorter identity with the same exact patch hash.
At that historical checkpoint, ARM64EC offsets, 187 fresh PE objects, 50 native
CoreState consumers, nine retained current members and imports/exports remained
gates. The subsequent local production results are recorded below. Fresh app
consumers, signing/device execution and CPU acceptance remain pending; local
producer success does not establish runtime success.

Run the small portable source-preservation controls from the repository root:

```sh
python3 -I -B -m unittest discover -s experimental/native-ec-continuation \
  -p 'test_checkpoint.py'
```

The portable extraction/native entrypoint requires explicit caller-owned source,
compiler, SDK and exclusive output paths. It checks the published source digests
before extraction. On a macOS ARM64 host, for example:

```sh
python3 -I -B experimental/native-ec-continuation/qualify_native.py \
  --fex-source /path/to/disposable/patched/FEX \
  --wine-signal /path/to/patched/signal_arm64_ios.c \
  --wine-unwind /path/to/Wine/dlls/ntdll/unwind.h \
  --compiler /path/to/clang++ --sdk /path/to/MacOSX.sdk \
  --output /path/to/new/exclusive/native-controls
```

This explicit invocation compiles and runs only the isolated native harness.
It does not configure FEX, sign, install, connect to a device or change a lease.
Published fixture address constants are synthetic. Their substitution preserves
the tested predicates but this public adaptation has only source/extraction
checks, not a separately claimed historical native run.

`emitter-probe.cpp` and `frame-offsets.cpp` compile against the actual candidate
FEX headers with the caller's complete include/generated-header route.
`frame-offsets-coff.cpp` emits the target layout into `.fexfrm`; compile it using
the actual ARM64EC Module.cpp flags, once against the before tree with
`ORIGINAL_FRAME` and once against the candidate. Check old size/offset equality
and the target/SP/LR record offsets before combining native and PE artifacts.
All actual app consumers of CoreState must use the same header route.

`local-rebuild-source-snapshot/` preserves authored local prepare/build/recipe
and review implementations, including their historical source references.
The original review writer has its local diagnostic path and fixed compiler path
redacted; every other snapshot is byte-identical to its source, as recorded in
the manifest. These files require separately retained local proof utilities and
provider maps that are deliberately absent here. Their `.snapshot` suffix is
intentional: they are not runnable entrypoints from a fresh clone. The original
and metadata-only second-attempt code are distinguished in the manifest. No
compiled binary, SDK, private diagnostic request/log, pairing material, game
asset, current provider inventory or physical device identifier is included.

FEX patch/control licensing follows GPL-3.0-or-later. Extracted Wine converter
and register-application bodies retain LGPL-2.1-or-later; repository and upstream
notices still apply.

The subsequent actual ARM64EC build produced all 187 objects, passed both COFF
frame probes, and preserved all 30 exports and the exact 12-DLL import symbol
contract. `RtlIsEcCode` was already imported by the baseline. An overly strict
postcondition requiring an extra import stopped that attempt; its failure is
retained while a reviewed resume qualifies the unchanged imports and the
native-archive tail. This is not a signed or device-executed runtime.
[Build observation](../../docs/evidence/native-ec-continuation-build-checkpoint-20261012.json).

The additive resume snapshots preserve the exact import-contract correction and
unchanged native50+9 tail. A later narrow successor records only the known
terminal parent's stdout capture after the parent writer exited: the producer
recorded that log before its final output flushed. It retains the immutable
failed receipt/output map and rejects every other provider drift. The terminal
record, captured bytes and local filesystem identities are deliberately absent
from this public checkpoint. This does not retroactively seal the producer log.
That source-only resume observation is historical; the subsequent native
continuation result is recorded below. Application packaging remains pending.

The actual native continuation subsequently passed: 104 owned compiler/archive
commands joined; 50 fresh native CoreState consumers and nine byte-verified
current members produced the ordered Core archive, with six other archives
retained. Complete provider/freeze replay and global symbol contracts passed.
The combined local result therefore supplies the actual 187-object EC DLL,
target ABI probes and matching native Core archive. Its actual frame size is
3904 on both old/new target probes; all old offsets remain equal. This is local
producer qualification only. Application packaging/signing, installation,
Original50/full803/eight phases, causal attribution and gameplay remain pending.
[Native producer observation](../../docs/evidence/native-ec-continuation-native-build-20261012.json).

The additive `*-native60.snapshot` files preserve the isolated prepare/run/finish
packaging implementation and its 16 source/temp controls. `common60` replaces
only the local user's literal toolchain location with an explicit placeholder;
the manifest binds the original source digest. Other snapshots are exact copies.
The root subsequently prepared the complete physical signed59 layout with only
the three candidate FEX sources, Core archive and EC DLL changed. A fresh native
application build is still pending at this checkpoint; no signed, installed or
CPU-pass claim follows from these snapshots. The final packaging gate requires
the actual new FEXBridge object/dependencies and complete header byte route, all
nine archive resolutions, retained PE helpers/profiles and Native59 rollback.
No source-review maps, Apple profile inventory, device state or private data is
published. These remain preservation snapshots, not fresh-clone build commands.

The fresh Native60 Xcode build subsequently completed. Its original final
verifier stopped at the dependency parser: Swift emitted four logical Make
records, while the parser read one RHS and rejected the later separator tokens.
The additive `*-same-app-verifier-attempt2.snapshot` sources preserve the narrow
parser successor and 12 source/local-readback controls. It parses every host
dependency record and retains the actual FEXBridge membership/header/object
checks. It verifies the same completed app and emits a separate signature
appendix; it contains no rebuild or resign operation. The original compiled
recipe and failed finish remain preserved. These snapshots are source-qualified
only; final signature verification, installation and CPU acceptance are pending
at this observation. Local source/input inventories remain unpublished.

The same-app final verifier subsequently passed on the completed Native60
application. Its actual signed receipt records the fresh FEXBridge object and
47 headers, all nine native archive resolutions, unchanged retained runtime
helpers/profiles/entitlements, strict signature checks and matching dSYM UUID.
An independent filesystem readback checked all 382 app files, 264 verifier
source records and 13 completed verification command outputs. The parser
successor neither rebuilt nor resigned the app; the earlier failed finish
remains retained. Native60 is now locally built and signed, and has not been
installed or CPU-qualified at this observation. The older installed Native59
HLE bytes remain packaged; the new a11c HLE runtime is not substituted.
[Signed local build observation](../../docs/evidence/native60-local-build-signature-20261012.json).

[The additive local-device source snapshot](local-device-source-snapshot/README.md)
preserves the authored Native60 preserving updater, provider reader and pending
Original50 adapter. It retains the prior installation's source bytes through
explicit local source views, requires complete current-data readback, and keeps
signed rollback and process closure. Its 19 updater controls and 24 Original50
controls are source checks. The snapshot omits private inventories, signing,
pairing, packages and logs; it requires the unpublished local bindings and is
not an executable fresh-clone recipe. Actual device results are recorded
separately from these source snapshots.

The later Native60 preserving update completed on the physical iPad. Complete
accessible before/after inventories and protected data readback match; opaque
metadata and the exact system-artifact policy pass. The installer and both
observers join successfully. Opaque contents and independent installed-binary
bytes remain outside this acceptance. Original50, full803, all eight CPU phases,
GPU and MiniGolf gameplay remain pending.
[Actual preserving installation](../../docs/evidence/native60-preserving-installation-20261012.json).

The first subsequent Native60 Original50 test starts the unchanged fixture
through automatic JIT but does not complete all50 deliveries or guest zero exit
within120 seconds. Library/metadata restoration and own-process closure pass,
with no cleanup errors. The candidate is not CPU-qualified; the quiet log does
not establish a cause or prove recurrence of the earlier PC/LR=2 fault. Further
CPU phases and game execution remain gated.
[Actual CPU observation](../../docs/evidence/native60-original50-observation-20261012.json).
