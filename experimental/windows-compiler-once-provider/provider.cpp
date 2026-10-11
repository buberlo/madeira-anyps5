#include "compiler_once.hpp"
#include <windows.h>
#include <pthread.h>

static_assert(sizeof(pthread_once_t) == 4);
static_assert(std::is_same_v<pthread_once_t, long>);
static_assert(PTHREAD_ONCE_INIT == 0);
struct AddressWaiter {
    bool wait(long* value, long expected) noexcept {
        return WaitOnAddress(value, &expected, sizeof(expected), INFINITE) != FALSE;
    }
    void wake(long* value) noexcept { WakeByAddressAll(value); }
};
extern "C" __declspec(dllexport)
int APS5NativeCompilerOnce_nid_no_patch(long* flag, void (*initialize)()) {
    if (!initialize) return EINVAL;
    AddressWaiter waiter;
    return aps5::compiler_once::invoke(flag, initialize, waiter);
}
