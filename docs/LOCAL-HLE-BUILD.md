# Local qualified HLE builds

Use `scripts/build-hle.py` on Windows, or on macOS/Linux with a local Wine capable
of running the pinned Windows compiler. It verifies the WinLibs GCC 15.2 posix-SEH
UCRT r7, FFmpeg and embedded Python download hashes. CMake, Ninja, curl and an
archive extractor must be installed locally. No GitHub Actions are used.

Apply the AnyPS5 patches before invoking this helper. An omitted target list builds
all available PRX targets; explicit targets must exist and retain libc/libkernel.
The object-manager target is named `ulobjmgr`; this exact name is accepted alongside
the existing `lib*` names. Every selected target must still have a matching source
directory. Manifest paths and shell characters are rejected before configuration.
`--from-hle` reads a prior archive's manifest to select names, without reusing old
binaries. `--source /absolute/path/to/patched/AnyPS5` selects a separate checkout
for a pin upgrade; this must be its own Git checkout, not an exported folder
inside the wrapper repository. Use its matching host tools when preparing the
package. Only this invocation's selected PRXs enter the exported archive.

The current complete-source refresh is `a11c8f7f`. After configuration, the
helper reads its owned CMake codemodel query and checks all selected PRXs are
actual shared-library targets, and all selected tools/tests are executable
targets on this platform. Bundled dependencies are selected explicitly with
`ANYPS5_USE_SYSTEM_DEPS=OFF`. The fresh 47-library runtime qualification is
separate from the older results below. [Current checks](UPSTREAM-REFRESH-20261012.md).

Use `--wine-prefix /absolute/project/build/owned-prefix` for an isolated local
Wine session. Repeat `--additional-test existing_target_tests` to select further
registered CMake test targets. The helper checks their literal names and source
definitions, builds them, then obtains their exact commands and arguments from
CTest's JSON inventory. Missing, duplicated, failed or skipped registered cases
fail qualification, including cases that run the same executable with different
arguments.
The selected commands, case results and actual runtime input hashes enter the
export provenance.

```sh
scripts/apply-patches.sh --only anyps5
python3 scripts/build-hle.py libSceJson2 libSceHttp2 libSceSsl --jobs 3
# On macOS/Linux add --wine /absolute/path/to/wine
```

The default output is `build/hle-runtime/hle-runtime.zip`. It contains selected
unpatched PRXs, the pinned compiler runtime DLLs and a manifest with hashes,
source/patch/toolchain provenance and test results. It contains no game data.

The helper runs the existing exception/runtime tests and the JSON2 RTTI/virtual allocator,
offline API, filesystem and thread tests. The upstream refresh also adds busy-thread
exception delivery, memory, uniform/wide-subgroup shader emission and AudioOut2
mix/latency/layout/timing contracts, each with a bounded execution time. These are
host contracts and do not demonstrate audible output or physical GPU rendering.
The selected test set also includes the existing HMD-without-device,
player-review-dialog and object-manager contracts. Patch0001 registers the HMD
test with the ordinary library build; it does not introduce a replacement HMD
implementation or emulate connected hardware or PSN access.
Their required libraries are built as
test dependencies; only the explicitly selected distribution targets are exported.
`--skip-tests` leaves the archive explicitly untested. Passing host tests never
marks gameplay or the iPad runtime as verified.

The historical three-patch full-main qualification passes 40 selected host
targets. The preceding six-patch combined build also includes exception-output and
unused-barycentric proof tests: all 42 selected and ten additional targets pass,
producing 53 distinct cases. One internal AVX subcase remains skipped on local
Wine; there are no CTest skips or failures. Before/after hashes cover actual test
executables, PRXs and compiler runtime DLLs; changed inputs fail qualification.
The final export seals the immutable qualification and verifies embedded/outer
provenance without circular hashes. [Historical build evidence](evidence/anyps5-combined-runtime-20261010.json).

The eleven-patch Apple graphics runtime built on 2026-10-11 contains 47 PRXs
and three compiler DLLs. Its 42 standard plus eleven additional test executables
produce 54 host cases, all passed, with no CTest skips and 119 actual runtime
inputs unchanged. Separate descriptor-policy and default/explicit snapshot
tests pass. The actual production PRX passes 538 public compiler cases, nine
complete independently validated replays and twelve null-pixel cases; all nine
SPIR-V/layout outputs match the prior qualified results. The asynchronous AVX
subcase remains unavailable on this Mac Wine host. These are local CPU results;
GPU, native Windows game and iPad acceptance remain open.
[Fresh production evidence](evidence/apple-gpu-runtime-cpu-20261011.json).

These tests include the actual C unwind personality and complete AGC graphics validator. The
personality test distinguishes SysV guest calls from Microsoft-ABI host calls;
the graphics validator exercises conditional descriptor update-after-bind,
ordinary-layout parity, pool ownership and mixed resource limits. These graphics
tests mock Vulkan calls and do not qualify execution on a physical GPU. See
[full main integration](ANYPS5-MAIN-INTEGRATION.md) and the historical
[Apple integration](APPLE-UPSTREAM-INTEGRATION.md) for separate native Metal
shader results and artifact provenance.

Host contracts default to a lazy 4-GiB virtual arena at 8 GiB, in 256-MiB chunks.
Explicit `APS5_GUEST_ARENA_*` settings override it and enter build provenance.
This reserves virtual addresses on demand, not 4 GiB of physical RAM. It does not
change or qualify the iPad/game arena; reservation failures still fail the tests.
If a local Wine host cannot reserve that fixed range, preserve the failure and
qualify an explicit alternative with the unchanged memory test before running
the complete suite. For the MiniGolf build, the same memory-test binary failed
at `0x200000000` and passed at `0x7400000000`, with only the base changed. This
establishes address-dependent host availability; it does not identify the
underlying Wine/Rosetta mapping or prove a device result.

The Git Bash `m0-build-anyps5-winlibs.sh` route remains available for the existing
selected closure and Windows source-build transfer. Set `APS5_HLE_TESTS=ON` to run
its focused compatibility tests, including the complete AGC graphics validator
and 20 repeated exception-delivery runs. A failure or timeout fails the build.
See [API coverage](HLE-API-COVERAGE.md) and
[runtime performance](RUNTIME-PERFORMANCE.md) for the limits of these results.

## Production null-pixel materialization check

[`anyps5_null_pixel_materialization.cpp`](../tools/checks/anyps5_null_pixel_materialization.cpp)
is a synthetic Windows fixture linked to the current raw AGC driver import library.
Its twelve cases call the loaded production decoder, graphics-stage preparer,
invocation builder, resource capture and shader materializer. They cover absent,
zero and partial pixel-program addresses at wave32/64, stale input/SGPR state,
late wave32 preparation and reuse, enabled-color-write rejection, and a missing
variant for a nonbuiltin shader. An invalid color target remains a valid
depth-only control; both rejection cases explicitly enable an RGBA8 target.

After a local HLE build containing `libSceAgcDriver`, use these PowerShell commands
from the repository root. Adjust `$build` and `$tc` if the build used other paths.
Use a fresh output directory and raw PRXs from this same build.

```powershell
$src = (Resolve-Path 'upstreams\AnyPS5').Path
$build = (Resolve-Path 'build\anyps5-winlibs-local').Path
$tc = (Resolve-Path 'build\toolchains\winlibs\mingw64').Path
$runtime = (New-Item -ItemType Directory 'build\null-pixel-check').FullName
$includes = @("$src\core\libs", "$src\core\shader\recompiler",
    "$build\core\libs\prx\libSceAgcDriver\shader_recompiler_agc_driver_generated",
    "$src\3rdparty\SPIRV-Headers\include", "$src\3rdparty\glslang",
    "$src\3rdparty\Vulkan-Headers\include")
$includes += Get-ChildItem "$src\core\shader\recompiler" -Directory |
    ForEach-Object { Join-Path $_.FullName 'include' } | Where-Object { Test-Path $_ }
$flags = @('-O3', '-DNDEBUG', '-std=c++20', '-fno-asynchronous-unwind-tables',
    '-DANYPS5_ENABLE_SPIRV_TOOLS=0', '-DAPS5_ENABLE_TIMING_LOG=0')
$flags += $includes | ForEach-Object { '-I' + $_ }
$link = @("$build\core\libs\libs\implib\liblibSceAgcDriver.dll.a",
    "$build\core\libs\libs\implib\liblibc.dll.a", '-lkernel32', '-luser32',
    '-lgdi32', '-lwinspool', '-lshell32', '-lole32', '-loleaut32', '-luuid',
    '-lcomdlg32', '-ladvapi32')
$exe = Join-Path $runtime 'null-pixel-materialization.exe'
& "$tc\bin\g++.exe" @flags 'tools\checks\anyps5_null_pixel_materialization.cpp' @link -o $exe
if ($LASTEXITCODE -ne 0) { throw 'Null-pixel fixture link failed' }
& "$tc\bin\objcopy.exe" --rename-section '.eh_frame=.ehfram' $exe
if ($LASTEXITCODE -ne 0) { throw 'Null-pixel fixture section conversion failed' }
'libc.prx', 'libkernel.prx', 'libSceAgcDriver.prx' | ForEach-Object {
    Copy-Item "$build\core\libs\libs\unpatched\$_" $runtime
}
'libgcc_s_seh-1.dll', 'libstdc++-6.dll', 'libwinpthread-1.dll' | ForEach-Object {
    Copy-Item "$tc\bin\$_" $runtime
}
& $exe (Join-Path $runtime 'libSceAgcDriver.prx')
if ($LASTEXITCODE -ne 0) { throw 'Production null-pixel check failed' }
& $exe (Join-Path $runtime 'not-the-driver.prx')
if ($LASTEXITCODE -ne 1) { throw 'Loaded-driver identity control failed' }
```

A successful run prints `ACTUAL_DRIVER_PATH`, twelve ordered `PASS` lines and
`TOTAL_PASS 12`. The wrong-path control must exit 1 with
`fixture loaded a different production PRX`. The byte-identical fixture passed
against the current full production runtime under local Wine, including that
identity control. This proves CPU preparation/capture/materialization only:
`GPU_EXECUTION 0` and `REGISTER_SHADER_DEVICE_API_EXECUTION 0` explicitly exclude
Vulkan-device registration, Metal rendering, iPad execution and gameplay.
