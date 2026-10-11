// Link this object only into newly qualified owned MinGW callers. It supplies
// both the direct C ABI and exact dllimport variable requested by owned callers. No macro
// or guest pthread_once export is changed, and native DLL IATs are untouched.
using OnceFunction = int (*)(long*, void (*)());
#ifdef APS5_ONCE_PROVIDER_LOCAL
extern "C" int APS5NativeCompilerOnce_nid_no_patch(long*, void (*)());
#else
extern "C" __declspec(dllimport)
int APS5NativeCompilerOnce_nid_no_patch(long*, void (*)());
extern "C" OnceFunction __imp_APS5NativeCompilerOnce_nid_no_patch;
#endif
extern "C" int APS5CompilerOnceBridge(long* flag, void (*initialize)()) {
    return APS5NativeCompilerOnce_nid_no_patch(flag, initialize);
}
extern "C" int pthread_once(long* flag, void (*initialize)()) {
    return APS5CompilerOnceBridge(flag, initialize);
}
extern "C" {
OnceFunction __imp_pthread_once = &pthread_once;
}
extern "C" OnceFunction APS5CompilerOnceResolvedTarget() noexcept {
#ifdef APS5_ONCE_PROVIDER_LOCAL
    return &APS5NativeCompilerOnce_nid_no_patch;
#else
    return __imp_APS5NativeCompilerOnce_nid_no_patch;
#endif
}
