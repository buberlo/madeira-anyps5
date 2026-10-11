# Fixed-address Wine host probe

The small Windows probe compares fixed reservations before and after loading
libc/libkernel. It records the actual Wine version, VirtualQuery census, returned
address, GetLastError and release. An allocation failure is an observation;
DIAGNOSTIC_COMPLETE is not a success result for that allocation.

On local Wine 11.0, both bare and HLE-loaded placeholder reservations fail at
8 and 128 GiB despite Wine reporting the range as free. They succeed at 48 GiB
and `0x7400000000`. The latter is selected explicitly for the local HLE tests,
with 4 GiB lazy arena size and 256 MiB chunks. No runtime fallback or memory
assertion is removed. These observations do not qualify iPad mappings or games.

The two runner snapshots preserve the bounded local execution source. They
require private local provider manifests and exact borrowed execution primitives;
they are archival source, not standalone entry points. Original failures are
retained separately. No game files, private manifests or raw logs are included.
