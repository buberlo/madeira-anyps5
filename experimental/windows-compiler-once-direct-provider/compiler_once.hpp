#pragma once
#include <atomic>
#include <cerrno>
#include <cstdint>
#include <type_traits>

namespace aps5::compiler_once {
// Native MinGW pthread_once_t is Windows long (four bytes), not GuestOnce.
// 0 is PTHREAD_ONCE_INIT, 1 is the native completed value; 2 is ours alone.
template<class Word, class Waiter, class Callback>
int invoke(Word* storage, Callback&& callback, Waiter& waiter) {
    static_assert(sizeof(Word) == 4 && std::is_integral_v<Word>);
    static_assert(std::atomic_ref<Word>::is_always_lock_free);
    static_assert(noexcept(waiter.wake(storage)));
    if (!storage || reinterpret_cast<std::uintptr_t>(storage) %
                        std::atomic_ref<Word>::required_alignment) return EINVAL;
    std::atomic_ref<Word> state(*storage);
    for (;;) {
        Word observed = state.load(std::memory_order_acquire);
        if (observed == 1) return 0;
        if (observed == 0) {
            if (!state.compare_exchange_weak(observed, Word{2},
                    std::memory_order_acquire, std::memory_order_acquire)) continue;
            // The callback runs without a registry, global mutex or TLS node.
            try { callback(); }
            catch (...) {
                state.store(0, std::memory_order_release);
                waiter.wake(storage);
                throw;
            }
            state.store(1, std::memory_order_release);
            waiter.wake(storage);
            return 0;
        }
        if (observed != 2) return EINVAL;
        // WaitOnAddress compares again before sleeping; an early wake needs
        // another acquire load. Failure never clears a different owner's flag.
        if (!waiter.wait(storage, Word{2})) return EAGAIN;
    }
}
}
