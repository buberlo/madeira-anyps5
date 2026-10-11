# Local upstream qualification source archive

This directory preserves small, locally authored qualification and promotion
recipes that otherwise live in ignored build directories. It is archival source,
not product tooling or a runnable build/test command. Each `.py.snapshot` begins
with an unconditional module-level exception before any original imports, file
access or subprocess call. It fails whether run directly or loaded as a module.
The absolute local project root is replaced with `__LOCAL_PROJECT_ROOT__`.
All other authored logic is preserved, including historical assertions, hashes,
cleanup paths, command budgets, error handling and failed-attempt recipes.

`source-manifest.json` records the original and normalized source hashes,
normalized AST hashes, exact snapshot hashes and the only declared changes.
Private originals remain in their original ignored locations. No logs, execution
receipts, source/provider maps, pairing material, game assets or copied upstream
source trees are included. Existing public patches preserve the implementation.
The ColorTargetLayout test file is therefore not copied here.

The archive contains two promotion recipes, fixture adoption, two native-suite
recipes, a full ShaderMemory recipe, the latest16 complete HLE recipe and four
successive targeted Graphics recipes. Failed earlier attempts are deliberately
preserved. In particular, the first latest16 promotion stopped when its SDL
checkout was missing four tracked test files; the later restoration and full
identity check have separate evidence. This saved original script is not a claim
that its initial execution passed. Likewise, old Graphics runs and the initial
latest15 native suites had real failures; later corrections do not rewrite them.
The latest16 HLE recipe's presence does not establish an exported qualified
archive, Windows/iPad execution, GPU output or playable MiniGolf.

The small ColorXOR source-control recipe is also preserved. Its original checks
read the held upstream equation header and candidate C++ fixture, so the archived
recipe is not a standalone portable C++ or GPU test. The public patch contains the
fixture correction; this archive retains the authored Python control logic only.

Portable verification parses source as data and checks hashes, transformations,
inert module guards, inventory and privacy. It never imports a snapshot:

```sh
python3 -I -B -m unittest discover -s experimental/upstream-qualification-source-snapshot -p test_snapshot.py
```

No GitHub Actions are used.
