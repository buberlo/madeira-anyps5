#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <wchar.h>

typedef void *(WINAPI *Allocate2)(HANDLE, void *, SIZE_T, ULONG, ULONG,
                                 MEM_EXTENDED_PARAMETER *, ULONG);
typedef const char *(__cdecl *WineVersion)(void);

static uintptr_t base;
static const SIZE_T size = UINT64_C(0x10000000);

static int census(const char *label) {
    uintptr_t cursor = base;
    unsigned regions = 0, nonfree = 0;
    while (cursor < base + size) {
        MEMORY_BASIC_INFORMATION m = {0};
        SetLastError(0);
        SIZE_T got = VirtualQuery((const void *)cursor, &m, sizeof(m));
        DWORD error = GetLastError();
        printf("QUERY label=%s cursor=0x%llx got=%llu error=%lu base=0x%llx allocation=0x%llx size=0x%llx state=0x%lx type=0x%lx protect=0x%lx\n",
               label, (unsigned long long)cursor, (unsigned long long)got,
               (unsigned long)error, (unsigned long long)(uintptr_t)m.BaseAddress,
               (unsigned long long)(uintptr_t)m.AllocationBase,
               (unsigned long long)m.RegionSize, (unsigned long)m.State,
               (unsigned long)m.Type, (unsigned long)m.Protect);
        uintptr_t start = (uintptr_t)m.BaseAddress;
        if (got != sizeof(m) || !m.RegionSize || start > cursor ||
            m.RegionSize > UINTPTR_MAX - start || start + m.RegionSize <= cursor ||
            ++regions > 256) return -1;
        nonfree += m.State != MEM_FREE;
        cursor = start + m.RegionSize;
    }
    printf("CENSUS label=%s regions=%u nonfree=%u\n", label, regions, nonfree);
    return (int)nonfree;
}

static int allocation(const char *label, Allocate2 function, int plain, int fixed) {
    if (census(label) < 0) return 0;
    if (!plain && !function) {
        printf("ALLOC label=%s missing=1\n", label);
        return 1;
    }
    void *wanted = fixed ? (void *)base : NULL;
    DWORD flags = MEM_RESERVE | (plain ? 0 : MEM_RESERVE_PLACEHOLDER);
    SetLastError(0);
    void *p = plain ? VirtualAlloc(wanted, size, flags, PAGE_NOACCESS) :
                     function(GetCurrentProcess(), wanted, size, flags,
                              PAGE_NOACCESS, NULL, 0);
    DWORD error = GetLastError();
    printf("ALLOC label=%s requested=0x%llx size=0x%llx flags=0x%lx protection=0x%lx result=0x%llx error=%lu\n",
           label, (unsigned long long)(uintptr_t)wanted, (unsigned long long)size,
           (unsigned long)flags, (unsigned long)PAGE_NOACCESS,
           (unsigned long long)(uintptr_t)p, (unsigned long)error);
    if (p) {
        SetLastError(0);
        BOOL released = VirtualFree(p, 0, MEM_RELEASE);
        error = GetLastError();
        printf("RELEASE label=%s pointer=0x%llx success=%d error=%lu\n", label,
               (unsigned long long)(uintptr_t)p, !!released, (unsigned long)error);
        if (!released) return 0;
    }
    return census("after-release") >= 0;
}

int wmain(int argc, wchar_t **argv) {
    setvbuf(stdout, NULL, _IONBF, 0);
    if (argc != 3 && argc != 5) {
        fprintf(stderr, "Usage: placeholder_probe.exe alloc2|fromapp|plain|any BASE [ABSOLUTE_LIBC ABSOLUTE_LIBKERNEL]\n");
        return 2;
    }
    int mode = !wcscmp(argv[1], L"alloc2") ? 0 :
               !wcscmp(argv[1], L"fromapp") ? 1 :
               !wcscmp(argv[1], L"plain") ? 2 :
               !wcscmp(argv[1], L"any") ? 3 : -1;
    if (mode < 0) return 2;
    base = !wcscmp(argv[2], L"0x200000000") ? UINT64_C(0x200000000) :
           !wcscmp(argv[2], L"0xc00000000") ? UINT64_C(0xc00000000) :
           !wcscmp(argv[2], L"0x2000000000") ? UINT64_C(0x2000000000) :
           !wcscmp(argv[2], L"0x7400000000") ? UINT64_C(0x7400000000) : 0;
    if (!base) return 2;
    HMODULE libc = NULL, kernel = NULL;
    if (argc == 5) {
        SetLastError(0);
        libc = LoadLibraryExW(argv[3], NULL, LOAD_WITH_ALTERED_SEARCH_PATH);
        DWORD error = GetLastError();
        printf("HLE_LOAD role=libc path=%ls loaded=%d error=%lu\n", argv[3], !!libc, (unsigned long)error);
        if (!libc) return 3;
        SetLastError(0);
        kernel = LoadLibraryExW(argv[4], NULL, LOAD_WITH_ALTERED_SEARCH_PATH);
        error = GetLastError();
        printf("HLE_LOAD role=kernel path=%ls loaded=%d error=%lu\n", argv[4], !!kernel, (unsigned long)error);
        if (!kernel) { FreeLibrary(libc); return 3; }
    }
    HMODULE kb = GetModuleHandleW(L"kernelbase.dll");
    HMODULE nt = GetModuleHandleW(L"ntdll.dll");
    Allocate2 a = (Allocate2)GetProcAddress(kb, "VirtualAlloc2");
    Allocate2 b = (Allocate2)GetProcAddress(kb, "VirtualAlloc2FromApp");
    WineVersion version = (WineVersion)GetProcAddress(nt, "wine_get_version");
    printf("HOST wine=%s alloc2=%d alloc2fromapp=%d hleLoaded=%d\n",
           version ? version() : "not-exported", !!a, !!b, argc == 5);
    SYSTEM_INFO info = {0}; GetSystemInfo(&info);
    printf("HOST page=0x%lx granularity=0x%lx\n", (unsigned long)info.dwPageSize,
           (unsigned long)info.dwAllocationGranularity);
    int ok = mode == 0 ? allocation("VirtualAlloc2-fixed-placeholder", a, 0, 1) :
             mode == 1 ? allocation("VirtualAlloc2FromApp-fixed-placeholder", b, 0, 1) :
             mode == 2 ? allocation("VirtualAlloc-fixed-reserve", NULL, 1, 1) :
                         allocation("VirtualAlloc2-any-placeholder", a, 0, 0);
    if (kernel && !FreeLibrary(kernel)) ok = 0;
    if (libc && !FreeLibrary(libc)) ok = 0;
    printf("DIAGNOSTIC_COMPLETE structurallyComplete=%d qualification=0\n", ok);
    return ok ? 0 : 4;
}
