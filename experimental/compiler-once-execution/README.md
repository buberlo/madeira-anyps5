# Experimental compiler-once execution sources

This checkpoint preserves the exact authored local executor and its controls for an isolated compiler-once candidate. It does not modify the normal AnyPS5 patch series or authorize a runtime action. Candidate provider/bridge source is preserved separately; no native DLL-internal `pthread_once` or POSIX cancellation qualification is asserted here.

`snapshot/run.py` and `snapshot/test_runner.py` are exact source snapshots of the reviewed executor. They depend on a separately held local recipe, prepared plan and complete provider maps. Those bindings, generated dependency files, compiled DLL/EXE/object outputs, private inventories and actual logs are deliberately omitted. These snapshots are not a portable one-command execution recipe. Their path and digest constants document the original source contract, without including its private data.

`snapshot/lifetime/` preserves the exact finite POSIX child/group capture helper plus its tests and the existing local wrapper whose pure inventory/environment/readback primitives the executor imports into a private namespace. Import does not launch a child. No original wrapper file or global namespace is patched by the new executor.

The executor consumes sixteen exact argv/environment records: six compiles, four links, four frame-section renames and two tests. It checks each actual compiler dependency against the complete original input hashes and identities before linking; it verifies the exact original 1061 exports plus one private export and rejects native `pthread_once` imports in the owned libc/callers before tests. Success requires all eight focused case names in order, one completion marker, and the unchanged original Windows exception fixture's marker, with both zero exit and complete capture/child/group closure. The complete dependency files remain hashed outputs, with counts and admission-map digests in the bounded receipt.

Limits are 1800 seconds for the command body, exact individual command deadlines, 2 GiB initial/live free space, 64 MiB artifacts outside the own prefix, 512 MiB prefix, 16384 entries and 1 MiB per captured stream. Only disappearing entries inside the live own prefix may be tolerated; static/provider/final checks remain strict. Graceful prefix wait comes first; only its timeout permits force close, followed by a required zero-exit final wait. Cleanup and replay errors stay failures. A preflight estimate checks the complete receipt against its 512 KiB cap.

The original executor had twelve pure/injected controls. The finite lifetime helper has nine tiny POSIX controls, including a self-terminating detached pipe holder; none runs Wine or a compiler. The preservation tests here check byte completeness and source boundaries only:

```sh
python3 -I -B -m unittest discover -s experimental/compiler-once-execution -p test_checkpoint.py
```

The first actual local attempt on 2026-10-12 stopped at the libc link with exit1. All six compiles and their actual dependency admission passed; every one of the eight command captures (including graceful prefix join) closed with zero discarded bytes and no cleanup error. Original providers and prepared copies remained unchanged. Neither fixture ran. The sanitized observation records this failure without including its private input map or raw logs.

The link failure has a concrete object-level cause: retained `ApplicationHeap.cpp.obj` references the direct native `pthread_once` symbol, while the new bridge defines only `__imp_pthread_once`. The Winpthreads import member defines both names; resolving the direct function therefore introduces the duplicate import-slot definition. A separately reviewed successor is needed. The unchanged executor snapshot here remains the source used for the failed first attempt, with no success relabeling.

No full HLE, iPad CPU/GPU, installation or gameplay qualification follows from this source checkpoint. Earlier failed receipts and the first-missing-frame diagnostic remain unchanged in their own retained locations.
