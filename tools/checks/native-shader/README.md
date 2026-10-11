# Native ARM64 shader CPU checks

Build the current production AnyPS5 recompiler on macOS, using its existing
third-party sources and complete driver source guard for cache identity:

```sh
cmake -S tools/checks/native-shader -B build/native-shader-checks -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_OSX_ARCHITECTURES=arm64 -DANYPS5_SOURCE="$PWD/upstreams/AnyPS5"
cmake --build build/native-shader-checks --parallel 2
ctest --test-dir build/native-shader-checks --output-on-failure
```

The six CPU suites check typed heap mapping, immutable device profiles,
request/cache identity, the canonical 355 interpolation cases, the extended
538 ordered public cases and 24 LDS spill compiler profiles. The 538 cases
include the canonical 355, plus SCC, mandatory DAG and optional-group proofs.
Their expected ordered names are retained in `expected-public-case-names.json`.
Assertions remain enabled. The LDS fixture reuses the
upstream shader and compiler helpers; its GPU entrypoint is never called.
It checks emitted SPIR-V barriers, atomic locks, bounds and workgroup slices.
An optional output directory emits the 24 synthetic modules for `spirv-val`:

```sh
ANYPS5_NO_SHADER_CACHE=1 build/native-shader-checks/agc_lds_spill_cpu_tests build/native-shader-checks/lds-spirv
```

Execution through the Windows production PRX and full private request replays
require separate qualification. ShaderReplay is built but does not search for or run game
requests automatically. These checks provide no GPU-dispatch, image-allocation,
Metal, game-rendering or gameplay proof. Production placeholder initialization
and descriptor-snapshot mocks run separately under Windows/Wine; they depend on
Windows guest-memory services. No GitHub Actions are involved.
