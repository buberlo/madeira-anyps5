# Thick D_X layout source review archive

This archive preserves the locally authored Python diagnosis/model and source
roundtrip recipe for additive AnyPS5 patch 0017. The recipes remain inert data:
each `.snapshot` starts with an unconditional exception before imports, file
access or subprocess calls. They must not be imported or run. The complete
original bodies are preserved without redaction because their root paths are
already derived at runtime. The manifest binds original bytes, parsed ASTs and
guarded snapshot bytes.

The diagnosis uses local held C++ and Addrlib sources. Its Python algebra checks
ten existing thick-layout cases and 202 unchanged address expectations; it is
not a C++ or GPU test. The roundtrip recipe records a prospective held source
candidate, preserving the real predecessor failure. Archived recipes are not
claims of successful compilation, installation, GPU execution or gameplay.
No upstream C++ copies, provider maps, logs, receipts or game assets are included.

Portable checks parse these snapshots as data and never import them:

```sh
python3 -I -B -m unittest discover -s experimental/thick-dx-layout-source-snapshot -p test_snapshot.py
```
