These files are byte-identical snapshots of the held compiler-once candidate.
The original source review was 099251aacbf51b4e05a687bfbce2bb0db68f330c29e1ca8d8566757545dca4b7.
Private input maps, prepared recipes, actual runtime outputs and tokens are omitted.

The C++ sources and focused behavior fixtures are reusable source. recipe.py and
test_recipe.py preserve the exact local recipe implementation; their relative
workspace calculations assume the original ignored build directory and are not
a portable qualification runner from this checkpoint directory. Use the held
local source for preparation. No candidate runtime pass or full-HLE qualification
is asserted here. A separate prospective CMake patch remains unpromoted pending
actual runtime checks.
