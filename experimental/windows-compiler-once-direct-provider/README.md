This is an isolated Windows compiler-once provider candidate. Nothing here has
been compiled, executed, installed or accepted as a full HLE runtime. Canonical
sources, the v4 patch series and the failed runtime outputs remain unchanged.

The installed GCC 15.2 headers use a four-byte Windows `long` initialized to
zero. Native winpthreads returns immediately for value one. Its callback path
owns a mutex and a stack TLS cleanup node which normal return removes. The
actual first-missing-frame trace identifies callback-return RVA 0x851d inside
that path. A native PE frame walk would bypass that cleanup. `.eh_fram` in the
native DLL is four zero bytes, so renaming it cannot supply a DWARF handler.
The libstdc++ `__once_proxy` restores its stack before a tail jump to the user
closure; it does not leave another native proxy frame around that closure.

The proposed provider runs callbacks in a fresh owned DWARF frame. State zero
is available, two is active and one is complete. An exceptional callback stores
zero, wakes waiters and rethrows. A successful callback stores one and wakes
waiters. Release/acquire ordering publishes callback writes. WaitOnAddress
rechecks the four-byte value before sleeping, and the loop handles early wakes.
The actual core is also exercised with spurious/failing waits in the C++ fixture.
No heap registration, global callback mutex or pthread TLS cleanup node is used.

The private exported entry is `APS5NativeCompilerOnce_nid_no_patch`. Its suffix
already has explicit no-patching semantics in the current NID resolver. Only
newly linked owned callers receive `caller_bridge.cpp`, defining both their direct `pthread_once` C ABI function and exact
`__imp_pthread_once` variable through the same DWARF forwarding path. The provider's
local bridge links directly; EXE/helper bridges import the private entry from
`libc.prx`. No global macro, guest symbol or guest 16-byte Once.cpp changes.
Native DLL internal IATs are unchanged. This is not a general mixed SEH/DWARF
bridge, nor a claim about POSIX asynchronous cancellation, pthread_exit in an
initializer or recursive use of the same flag. Those are outside this candidate.

The inert recipe retains all 46 actual libc objects, adds provider/local-bridge
objects, and preserves all 1,061 original export names, ordinals and code/data
classification through an explicit DEF. Only the private code export is appended
at ordinal 1,062. It freshly compiles the original WindowsExceptions.cpp without
source changes, a focused fixture and a cross-module helper, with explicit bridge
objects and the fresh import library. Synchronization imports are linked through
the installed `libsynchronization.a`. Every fresh image's `.eh_frame` is renamed
to `.ehfram`. Input/header bytes, retained objects, tools and actual dependencies
must be replayed before and after the root's bounded build.

Focused actual cases are: retry/destructors/passive return; nested distinct flags
and TLS closures; normal concurrent publication; concurrent exception/retry;
independent flag overlap; actual core spurious/wait-failure/reset behavior; exact
four-byte ABI/invalid/done states; and cross-module private IAT identity. The
fixture checks loaded libc/helper paths and compares the private resolved import
slot with GetProcAddress. Static qualification rejects any remaining native
pthread_once import in either fixture or helper. Original WindowsExceptions must
also pass in full; the eight focused cases cannot replace it.

Root-only filesystem preparation command (substitute the held source-review SHA
and a fresh output path; this mode never invokes Wine or a compiler):

```sh
/Users/konrad/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -B /Users/konrad/Documents/ChatGPT/anyps5-ipad/build/anyps5-full-main-update-20261012/windows-compiler-once-direct-provider-proposal/recipe.py --prepare --source-review-sha256 SOURCE_REVIEW_SHA --output /Users/konrad/Documents/ChatGPT/anyps5-ipad/build/anyps5-full-main-update-20261012/windows-compiler-once-provider-build-attempt2
```

Root executes the emitted exact commands with the reviewed finite child/group
helper, a fresh owned prefix and only the owned runtime/compiler directories on
Windows PATH. Enforce 2 GiB initial/live free reserve, 64 MiB command/runtime
outputs excluding the separately capped 512 MiB prefix, 1 MiB per captured
stream, actual .d dependency admission, every child/group join and graceful
wineserver wait; kill only after a bounded wait timeout and retain any failure.
After all compile/link/rename commands and before either run, use:

```sh
.../python3.12 -I -B .../recipe.py --qualify-static --output ABSOLUTE_OUTPUT --plan-sha256 EXACT_PLAN_SHA
```

Static qualification is explicitly not a runtime pass. Root must check exit zero,
all eight ordered COMPILER_ONCE_PASS names and the complete marker, original
fixture output, exact runtime binding, all final provider identities, closed
prefix and finite child/group cleanup before proposing production integration.
A later full rebuild must route every owned compiler caller deliberately and
rerun the required HLE tests. Neither this recipe nor its focused pass exports an
accepted HLE/game package.

Primary references: [installed-source-compatible winpthreads implementation](https://raw.githubusercontent.com/mingw-w64/mingw-w64/v13.0.0/mingw-w64-libraries/winpthreads/src/thread.c),
[GCC's documented pthread_once exception boundary](https://gcc.gnu.org/pipermail/libstdc++/2020-November/051346.html),
[C++ call_once requirements](https://eel.is/c++draft/thread.once.callonce),
[WaitOnAddress semantics and Synchronization library](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitonaddress).
The cited winpthreads version corroborates the installed disassembly; it is not
a claim that an unverified upstream revision produced these exact DLL bytes.

Pure admission tests (no compiler, preparation, Wine or runtime):

```sh
/Users/konrad/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -B -m unittest discover -s /Users/konrad/Documents/ChatGPT/anyps5-ipad/build/anyps5-full-main-update-20261012/windows-compiler-once-direct-provider-proposal -p test_recipe.py
```

The preceding IAT-only candidate099251 and failed attempt1 remain immutable.
Attempt1 completed all six fresh compiles and dependency admission, then libc
linking failed: retained ApplicationHeap.cpp.obj references direct pthread_once.
The native import archive's corresponding member defines both pthread_once and
__imp_pthread_once, conflicting with the old bridge's single slot definition.
This successor defines both symbols. It does not permit multiple definitions or
remove native pthread imports needed for unrelated functions. The first focused
case now forces a direct pthread_once COFF reference, verifies its pointer equals
the IAT slot, and checks direct throw/reset/destructor/retry followed by passive
IAT use of the same flag. Eight ordered case names remain unchanged. Static
qualification requires both bridge objects to define both symbols and the focused
object to have both undefined references before checking final PE imports.
The exact four-byte ABI, provider algorithm, cross-module helper, original fixture,
guest16-byteOnce, resource caps and runtime acceptance policy are unchanged.
