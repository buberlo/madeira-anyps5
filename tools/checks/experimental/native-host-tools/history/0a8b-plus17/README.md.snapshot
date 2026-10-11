# Native host-tool qualification harness

This inert macOS CMake harness builds portable relinker and NID conversion tools
from an explicitly supplied AnyPS5 tree. It includes the tree's root
`ANYPS5_RELINKER_ONLY=ON` workflow without modifying the source or test
expectations. It additionally registers the existing Mach-O and ELF
symbol-version NID-patcher synthetic tests. The unwind helper is a native
macOS no-op matching the existing host-tools wrapper.

Configure a new output directory, supply `-DANYPS5_SOURCE=/path/to/source`, build
with `cmake --build /path/to/output --parallel 2`, and run
`ctest --test-dir /path/to/output --output-on-failure`. Python bytecode may be
kept outside source with `PYTHONDONTWRITEBYTECODE=1`.

The regressions inspect synthetic output binaries and run compatible host
fixtures. They do not establish a game's imports, launch, graphics, device
execution, or playability. No game assets, maps, receipts, credentials, or
private paths belong in this directory.
