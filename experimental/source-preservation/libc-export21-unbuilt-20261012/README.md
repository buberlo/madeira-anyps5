# Unbuilt libc export repair source preservation

This archive preserves authored patch 21 and the corrected portable PE export checker after development was stopped for storage cleanup. Patch 21 has not been applied to the canonical or private 20-patch source and has not been compiled. It is held here for review, outside the active patch series.

The patch appends twelve implemented upstream C exports at ordinals 1063–1074. It retains all original 1062 export rows, ordinals, 149 `DATA` entries, and the compiler-once provider. The inline C++ path helper is excluded. Its source-only 21-patch replay passed 88 check/apply/reverse operations before the stop; the prior raw binary had exactly the original 1062 exports and lacked those twelve names. A repaired binary, import/NID closure, and runtime acceptance remain unverified. The known MSAA policy conflict remains unresolved.

All Python snapshots raise before imports or original logic. They preserve the preparation, job-change closure, remaining CPU contract recipe, checker, and archive saver as data. The manifest records exact original hashes and declares local path redactions. Three supplemental helpers predate the source checkpoint but were not in its archive. No binary, raw provider payload, game data, runtime log, private source map, device data, or credential is included.

Run the portable preservation checks only: `python3 -I -B -m unittest discover -s experimental/source-preservation/libc-export21-unbuilt-20261012 -p test_preservation.py`. These validate source, ordinal preservation, and synthetic PE parsing without compilers, Wine, devices, or development/adoption actions. Preservation does not authorize resuming work. No GitHub Actions.
