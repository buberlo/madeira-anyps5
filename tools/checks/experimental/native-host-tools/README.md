# Native ARM64 conversion-tool qualification harness

The final AnyPS5 source snapshot is `43bc17f7edfc32c38428fd8e4e6d8cc94c8cb31b`
with twenty reconciled local patches. A fresh native ARM64 relinker/NID build
passed **all 120 actual configured CTests**, with zero failed or skipped cases.
All 2,199 source hashes/modes and eleven initialized vendor commits/clean states
matched the frozen review before and after. The build used one compiler job.
[Sanitized actual result](actual120-final43bc-20261012.json).

The inventory contains 103 relinker cases, fourteen root-tool cases, one
portable cache-file-read case and two NID-patcher cases. Every prior 110 case
remains. The ten additions are:

- `elf_reader_bounds`
- `guest_syscall_trap`
- `none_relocations`
- `param_json_utf8`
- `program_layout_ranges`
- `release_package`
- `rewrite_boundaries`
- `section_header_ranges`
- `shader_cache_file_read`
- `windows_guest_export_aliases`

The result JSON records all 120 names individually and verifies exact configured
and executed-name equality. The alias fixture uses the production ELF reader,
Windows writer and helper closure on macOS. It verifies raw symbol tuples,
relocation indices, rejection paths and the exact ordinary alias plus two owned
lifecycle exports. It does not execute the emitted x86-64 PE.

The `linux_guest_stack`, `guest_module_args` and `guest_init_fini` fixtures retain
their existing host execution guards. Their synthetic-output assertions pass;
incompatible native guest execution is not claimed. This qualifies host
conversion tools only. It is not an HLE, GPU, iPad, game-import/launch or gameplay
result, and does not qualify unresolved default MSAA policy positive cases.

## Reproduce against an explicitly supplied reviewed source

`run.py` takes `--source`, `--review`, `--directory`, `--prior-inventory`,
`--cmake`, `--ninja`, `--clang`, `--python` and `--jobs` (one or two). An optional
`--adoption-receipt` records its digest without inventing its outcome. Use a
fresh output directory, native macOS ARM64, Python 3.12 and explicit tool paths.
The review supplies `sourceTree` hash/mode records and `thirdPartyGitlinks`.
The prior inventory must be the retained 110-case qualification inventory.

The runner inventories reviewed source and actual vendors, configures a fresh
CMake/Ninja output, builds the relinker/NID tools and portable targets, captures
CTest JSON and runs the complete inventory with JUnit output. It repeats the
source/vendor inventory and writes one final receipt. Qualification requires
all prior names and the ten merged regression names, every actual configured
name executed, no failed/skipped cases and unchanged reviewed source/vendors.
There is no fixed current test-count substitution.

The harness sets `ANYPS5_RELINKER_ONLY=ON`, retains upstream tests and adds the
existing NID Mach-O/symbol-version and portable alias registrations. Its native
Mach-O unwind helper is a no-op; Windows `.eh_frame` transformation is not used.
`PYTHONDONTWRITEBYTECODE=1` keeps bytecode outside the reviewed source.
Compiler jobs must be coordinated with other local builds; configuration can
also invoke compiler checks. No build, source pin or device operation starts
by reading these files. No GitHub Actions are used.

## Retained history

The older [110-test result](../../../../docs/evidence/native-host-tools-latest17-20261012.json)
remains historical and unchanged. Its exact helper bytes are preserved as
inert `.snapshot` files under `history/0a8b-plus17/`. The five helper files used
for the actual final43b run are retained under `history/final43bc-qualified/`;
only this public README changes their explanatory prose. The snapshot suffix
prevents accidental use as a runnable build route. Earlier failures remain
failures. Maps, game data, private paths, provider inventories and pairing
material are excluded from the public result and this directory.
