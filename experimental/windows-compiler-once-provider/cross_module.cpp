#include <mutex>
#include <stdexcept>
using OnceFunction = int (*)(long*, void (*)());
extern "C" OnceFunction APS5CompilerOnceResolvedTarget() noexcept;
extern "C" __declspec(dllexport) OnceFunction HelperOnceTarget() noexcept {
    return APS5CompilerOnceResolvedTarget();
}
extern "C" __declspec(dllexport)
void HelperCallOnce(std::once_flag* flag, int* calls, bool fail) {
    std::call_once(*flag, [=] {
        ++*calls;
        if (fail) throw std::runtime_error("cross-module once");
    });
}
