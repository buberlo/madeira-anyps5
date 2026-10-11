#include "compiler_once.hpp"
#include <windows.h>
#include <pthread.h>
#include <array>
#include <atomic>
#include <cstdio>
#include <cstring>
#include <mutex>
#include <stdexcept>
#include <thread>

using OnceFunction = int (*)(long*, void (*)());
extern "C" __declspec(dllimport)
int APS5NativeCompilerOnce_nid_no_patch(long*, void (*)());
extern "C" OnceFunction APS5CompilerOnceResolvedTarget() noexcept;
extern "C" OnceFunction __imp_pthread_once;
extern "C" int APS5CompilerOnceBridge(long*, void (*)());
static_assert(sizeof(pthread_once_t) == 4 && PTHREAD_ONCE_INIT == 0);
static_assert(sizeof(std::once_flag) == sizeof(pthread_once_t));
static void require(bool value, const char* reason) {
    if (!value) throw std::runtime_error(reason);
}
static void pass(const char* name) { std::printf("COMPILER_ONCE_PASS %s\n", name); }
struct Destruct { int& count; ~Destruct() { ++count; } };
static void retry() {
    std::once_flag flag;
    int calls=0, destroyed=0, caught=0, published=0;
    for (int n=0; n<4; ++n) {
        try { std::call_once(flag, [&] {
            Destruct guard{destroyed};
            if (++calls < 4) throw std::runtime_error("retry identity");
            published=37;
        }); }
        catch (const std::runtime_error& e) {
            require(std::strcmp(e.what(), "retry identity")==0, "exception identity"); ++caught;
        }
    }
    std::call_once(flag, [&]{ ++calls; });
    require(calls==4 && caught==3 && destroyed==4 && published==37, "retry/destructor/passive");
    pass("retry_destructors_passive");
}
static void nested() {
    std::once_flag outer, inner;
    int outside=0, inside=0, destroyed=0;
    for (int n=0; n<2; ++n) {
        try { std::call_once(outer, [&] {
            Destruct guard{destroyed}; ++outside;
            std::call_once(inner, [&] {
                Destruct second{destroyed}; if (++inside==1) throw std::runtime_error("inner");
            });
        }); }
        catch (const std::runtime_error& e) { require(!n && !std::strcmp(e.what(),"inner"), "nested identity"); }
    }
    std::call_once(outer,[&]{ ++outside; });
    std::call_once(inner,[&]{ ++inside; });
    require(outside==2 && inside==2 && destroyed==4, "nested reset and TLS closures");
    pass("nested_distinct_flags");
}
static void contention(bool failFirst) {
    std::once_flag flag;
    std::atomic<int> ready{0}, calls{0}, caught{0}, completed{0}, bad{0};
    std::atomic<bool> start{false};
    int published=0;
    std::array<std::thread,16> workers;
    for (auto& worker: workers) worker=std::thread([&] {
        ready.fetch_add(1); while (!start.load(std::memory_order_acquire)) std::this_thread::yield();
        try {
            std::call_once(flag,[&] {
                int attempt=calls.fetch_add(1);
                // Give competing callers an opportunity to enter the wait.
                Sleep(20);
                if (failFirst && !attempt) throw std::runtime_error("contended retry");
                published=91;
            });
            if (published!=91) bad.fetch_add(1);
            completed.fetch_add(1);
        } catch (const std::runtime_error& e) {
            if (std::strcmp(e.what(),"contended retry")) bad.fetch_add(1);
            caught.fetch_add(1);
        } catch (...) { bad.fetch_add(1); }
    });
    while (ready.load()!=16) std::this_thread::yield();
    start.store(true,std::memory_order_release);
    for (auto& worker: workers) worker.join();
    require(!bad.load() && calls==(failFirst?2:1) && caught==(failFirst?1:0)
        && completed==(failFirst?15:16), "waiter progress and publication");
    pass(failFirst?"concurrent_exception_retry":"concurrent_single_success");
}
static void independent() {
    std::once_flag first, second;
    std::atomic<int> entered{0}; std::atomic<bool> release{false};
    auto body=[&] { entered.fetch_add(1); while (!release.load()) std::this_thread::yield(); };
    std::thread a([&]{std::call_once(first,body);});
    std::thread b([&]{std::call_once(second,body);});
    // If a global callback lock is introduced, root's finite fixture timeout
    // fails this case rather than claiming independent progress.
    while (entered.load()!=2) std::this_thread::yield();
    release=true; a.join(); b.join(); pass("independent_flag_overlap");
}
struct ScriptedWaiter {
    int waits=0, wakes=0; bool fail=false;
    bool wait(long* value,long) noexcept {
        ++waits;
        if (fail) return false;
        if (waits==2) std::atomic_ref<long>(*value).store(0,std::memory_order_release);
        return true;
    }
    void wake(long*) noexcept { ++wakes; }
};
static void backend_contract() {
    long flag=2; int calls=0; ScriptedWaiter wait;
    int r=aps5::compiler_once::invoke(&flag,[&]{++calls;},wait);
    require(!r && calls==1 && flag==1 && wait.waits==2 && wait.wakes==1,"spurious waits");
    flag=2; wait={}; wait.fail=true;
    require(aps5::compiler_once::invoke(&flag,[&]{++calls;},wait)==EAGAIN
        && flag==2 && wait.wakes==0 && calls==1,"wait failure preserves owner");
    flag=0; wait={};
    try { aps5::compiler_once::invoke(&flag,[]{throw std::runtime_error("core");},wait); }
    catch (const std::runtime_error& e) { require(!std::strcmp(e.what(),"core"),"core rethrow"); }
    require(flag==0 && wait.wakes==1,"exception reset wake");
    require(aps5::compiler_once::invoke(&flag,[&]{++calls;},wait)==0 && flag==1 && calls==2,"core retry");
    pass("actual_core_spurious_failure_reset");
}
static void invalid() {
    long flag=0;
    require(APS5NativeCompilerOnce_nid_no_patch(nullptr,+[]{})==EINVAL,"null flag");
    require(APS5NativeCompilerOnce_nid_no_patch(&flag,nullptr)==EINVAL && flag==0,"null callback");
    alignas(long) unsigned char bytes[sizeof(long)+1]{};
    require(APS5NativeCompilerOnce_nid_no_patch(reinterpret_cast<long*>(bytes+1),+[]{})==EINVAL,"alignment");
    flag=3; require(APS5NativeCompilerOnce_nid_no_patch(&flag,+[]{})==EINVAL && flag==3,"invalid state");
    flag=1; require(!APS5NativeCompilerOnce_nid_no_patch(&flag,+[]{throw 7;}),"native done value");
    pass("four_byte_abi_invalid_done");
}
static bool exact_path(HMODULE module, const char* expected) {
    wchar_t actual[32768], input[32768], full[32768];
    DWORD length=GetModuleFileNameW(module,actual,32768);
    int converted=MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,expected,-1,input,32768);
    if (!length || length>=32768 || !converted) return false;
    DWORD expanded=GetFullPathNameW(input,32768,full,nullptr);
    return expanded && expanded<32768 &&
        CompareStringOrdinal(actual,-1,full,-1,TRUE)==CSTR_EQUAL;
}
static void binding_and_cross_module(const char* libcPath, const char* helperPath) {
    HMODULE libc=GetModuleHandleW(L"libc.prx");
    require(libc!=nullptr && exact_path(libc,libcPath),"loaded exact libc path");
    auto expected=reinterpret_cast<OnceFunction>(GetProcAddress(libc,"APS5NativeCompilerOnce_nid_no_patch"));
    require(expected && APS5CompilerOnceResolvedTarget()==expected
        && __imp_pthread_once==&APS5CompilerOnceBridge,"EXE exact private IAT route");
    wchar_t wideHelper[32768];
    require(MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,helperPath,-1,wideHelper,32768)>0,"helper path UTF8");
    HMODULE helper=LoadLibraryW(wideHelper);
    require(helper!=nullptr && exact_path(helper,helperPath),"cross helper exact path");
    using Target=OnceFunction (*)();
    using Call=void (*)(std::once_flag*,int*,bool);
    auto target=reinterpret_cast<Target>(GetProcAddress(helper,"HelperOnceTarget"));
    auto call=reinterpret_cast<Call>(GetProcAddress(helper,"HelperCallOnce"));
    require(target && call && target()==expected,"DLL same provider");
    std::once_flag flag; int calls=0, caught=0;
    try { call(&flag,&calls,true); }
    catch (const std::runtime_error& e) { require(!std::strcmp(e.what(),"cross-module once"),"cross throw"); ++caught; }
    std::call_once(flag,[&]{++calls;}); call(&flag,&calls,false);
    require(calls==2 && caught==1,"cross-module flag retry/passive");
    require(FreeLibrary(helper)!=FALSE,"cross helper close");
    pass("private_iat_cross_module_identity");
}
int main(int argc, char** argv) {
    try {
        require(argc==3,"expected exact libc and helper paths");
        binding_and_cross_module(argv[1],argv[2]); retry(); nested(); contention(false);
        contention(true); independent(); backend_contract(); invalid();
        std::puts("COMPILER_ONCE_COMPLETE cases=8 errors=0"); return 0;
    } catch (const std::exception& e) {
        std::fprintf(stderr,"COMPILER_ONCE_FAILED %s\n",e.what()); return 1;
    } catch (...) { std::fputs("COMPILER_ONCE_FAILED unknown\n",stderr); return 1; }
}
