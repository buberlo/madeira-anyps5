// Executes the extracted FEX CheckCall assembly; no model replaces the lookup.
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <sys/mman.h>
#include <sys/resource.h>
#include <unistd.h>

extern "C" {
extern uint64_t NtDllBase;
extern uint32_t* NtDllRedirectionLUT;
extern uint32_t NtDllRedirectionLUTSize;
extern uint32_t NtDllSizePoison;
uint64_t InvokeCheckCall(uint64_t target);
}

int main(int argc, char** argv) {
  rlimit core{0, 0};
  setrlimit(RLIMIT_CORE, &core);
  const long page = sysconf(_SC_PAGESIZE);
  if (page <= 0 || argc < 2) return 2;
  const unsigned alignment = static_cast<unsigned>(argv[1][0] - '0');
  if ((reinterpret_cast<uintptr_t>(&NtDllRedirectionLUTSize) & 7) != alignment ||
      reinterpret_cast<uintptr_t>(&NtDllSizePoison) !=
          reinterpret_cast<uintptr_t>(&NtDllRedirectionLUTSize) + 4) {
    std::fprintf(stderr, "size/poison alignment contract failed\n");
    return 3;
  }
  void* allocation = mmap(nullptr, static_cast<size_t>(page) * 2,
                          PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANON, -1, 0);
  if (allocation == MAP_FAILED) return 4;
  auto* guard = static_cast<char*>(allocation) + page;
  if (mprotect(guard, static_cast<size_t>(page), PROT_NONE)) return 5;
  NtDllBase = 0x100000000ULL;
  NtDllSizePoison = 0x76543210U;
  struct Case { const char* name; uint32_t size; int64_t offset; };
  const Case cases[] = {
      {"zero-size", 0, 0},
      {"zero-size-far", 0, 4096},
      {"below-base", 8, -1},
      {"first-entry", 8, 0},
      {"last-entry", 8, 7},
      {"exact-size", 8, 8},
      {"size-plus-one", 8, 9},
      {"large-offset", 8, 0xffff0000LL},
      {"single-entry", 1, 0},
      {"single-entry-end", 1, 1},
  };
  unsigned checked = 0;
  for (const auto& test : cases) {
    if (argc > 2 && std::strcmp(argv[2], test.name)) continue;
    NtDllRedirectionLUTSize = test.size;
    NtDllRedirectionLUT = reinterpret_cast<uint32_t*>(guard) - test.size;
    for (uint32_t i = 0; i < test.size; ++i) NtDllRedirectionLUT[i] = 0x1000 + i * 3;
    const uint64_t target = NtDllBase + test.offset;
    const uint64_t expected = test.offset >= 0 && static_cast<uint64_t>(test.offset) < test.size
                                  ? NtDllBase + NtDllRedirectionLUT[test.offset]
                                  : target;
    // Flush before the call so mutation receipts identify the faulting case.
    std::printf("check %s size=%u offset=%lld alignment=%u\n", test.name,
                test.size, static_cast<long long>(test.offset), alignment);
    std::fflush(stdout);
    const uint64_t actual = InvokeCheckCall(target);
    if (actual != expected) {
      std::fprintf(stderr, "%s: expected=%llx actual=%llx\n", test.name,
                   static_cast<unsigned long long>(expected), static_cast<unsigned long long>(actual));
      return 6;
    }
    ++checked;
  }
  munmap(allocation, static_cast<size_t>(page) * 2);
  if (!checked) return 7;
  std::printf("passed %u CheckCall cases\n", checked);
}
