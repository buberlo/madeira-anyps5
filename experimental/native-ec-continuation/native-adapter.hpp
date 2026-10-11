#include <array>
#include <cstdint>
#include <cstring>
#include <cstdio>
#include <cstdlib>
#include <cstddef>
#include <type_traits>
using std::memcpy;
struct ARM64_NT_CONTEXT {
  union { uint64_t X[31]; struct { uint64_t X0,X1,X2,X3,X4,X5,X6,X7,X8,X9,X10,X11,X12,X13,X14,X15,X16,X17,X18,X19,X20,X21,X22,X23,X24,X25,X26,X27,X28,Fp,Lr; }; };
  uint64_t Sp=0, Pc=0;
  uint32_t Cpsr=0, ContextFlags=0, Fpcr=0, Fpsr=0;
  alignas(16) __uint128_t V[32]{};
};
static_assert(sizeof(ARM64_NT_CONTEXT)==800 && offsetof(ARM64_NT_CONTEXT,Sp)==248 && offsetof(ARM64_NT_CONTEXT,Pc)==256 && offsetof(ARM64_NT_CONTEXT,Cpsr)==264 && offsetof(ARM64_NT_CONTEXT,V)==288);
struct NativeCapture { ARM64_NT_CONTEXT context{}; uint64_t savedNativeSp=0; };
static_assert(offsetof(NativeCapture,savedNativeSp)==800);
extern "C" void CaptureEntryLoopTop(NativeCapture*,uint64_t*,uint64_t,const uint64_t*,const __uint128_t*,void*,void*);
extern "C" void EntryLoopTopTestPoint();
constexpr uint32_t CONTEXT_ARM64_FULL=0x400007, CONTEXT_ARM64_FEX_YMMSTATE=0x40;
constexpr uint32_t PF_AVX2_INSTRUCTIONS_AVAILABLE=40;
namespace FEXCore {
namespace X86State {
enum {REG_RAX,REG_RCX,REG_RDX,REG_RBX,REG_RSP,REG_RBP,REG_RSI,REG_RDI,REG_R8,REG_R9,REG_R10,REG_R11,REG_R12,REG_R13,REG_R14,REG_R15};
enum {RFLAG_CF_RAW_LOC=0,RFLAG_TF_RAW_LOC=8,RFLAG_ZF_RAW_LOC=6,RFLAG_SF_RAW_LOC=7,RFLAG_OF_RAW_LOC=11};
}
namespace Core {
struct State {
  uint64_t rip=0, gregs[16]{};
  struct { struct { uint64_t data[16][2]{}; } sse; } xmm;
  __uint128_t avx_high[16]{};
  uint64_t mm[8][2]{};
  uint32_t compactFlags=0;
};
struct Frame { Core::State State{}; struct { uint64_t DispatcherLoopTop=0; } Pointers; int SynchronousFaultData=0; uint64_t IosEnterECSuspendTarget=0,IosEnterECSuspendSP=0,IosEnterECSuspendLR=0; };
struct InternalThreadState { Frame* CurrentFrame; };
}
}
struct Config {
  uint16_t SRAGPRCount=16, SRAFPRCount=16;
  std::array<uint8_t,16> SRAGPRMapping{8,0,1,27,23,29,25,26,2,3,4,5,19,20,21,22};
  std::array<uint8_t,16> SRAFPRMapping{0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15};
  uint64_t DispatcherBegin=0, DispatcherEnd=0;
};
struct Delegator { Config config; const Config& GetConfig() const { return config; } } delegator;
auto* SignalDelegator=&delegator;
struct ContextAdapter {
  int restoreCalls=0, liveFlagsCalls=0, packedFlagsCalls=0;
  uint64_t lastRestorePC=0,lastPF=0,lastAF=0,lastCpsr=0;
  uint64_t RestoreRIPFromHostPC(FEXCore::Core::InternalThreadState*,uint64_t pc) { ++restoreCalls; lastRestorePC=pc; return 0x114f334000; }
  uint32_t ReconstructCompactedEFLAGS(FEXCore::Core::InternalThreadState* t,bool live,const uint64_t* x,uint64_t cpsr) {
    if(live) { ++liveFlagsCalls; lastPF=x[9]; lastAF=x[24]; lastCpsr=cpsr; return 0x8d5; }
    ++packedFlagsCalls; return t->CurrentFrame->State.compactFlags;
  }
  void SetFlagsFromCompactedEFLAGS(FEXCore::Core::InternalThreadState* t,uint32_t flags) { t->CurrentFrame->State.compactFlags=flags; }
  void ReconstructXMMRegisters(FEXCore::Core::InternalThreadState* t,__uint128_t* low,__uint128_t* high) {
    memcpy(low,t->CurrentFrame->State.xmm.sse.data,16*sizeof(__uint128_t)); memcpy(high,t->CurrentFrame->State.avx_high,16*sizeof(__uint128_t));
  }
} ctx;
auto* CTX=&ctx;
struct Features { bool avx=true; bool IsFeaturePresent(uint32_t feature) { if(feature!=PF_AVX2_INSTRUCTIONS_AVAILABLE) std::abort(); return avx; } } features;
auto* CPUFeatures=&features;
FEXCore::Core::InternalThreadState* activeThread=nullptr;
struct Area { FEXCore::Core::InternalThreadState* ThreadState() {return activeThread;} };
Area GetCPUArea() {return {};}
bool IsDispatcherAddress(uint64_t pc) {return pc>=delegator.config.DispatcherBegin && pc<delegator.config.DispatcherEnd;}
struct EXCEPTION_RECORD { uint32_t ExceptionCode=0; };
namespace LogMan::Msg { template<typename... T> void DFmt(const char*,T...) {} }


using ULONG_PTR=uint64_t;
static uint64_t acceptedEcTarget=0, aliasTarget=0, aliasPe=0;
static unsigned ecCalls=0;
static uint64_t IosJitReverseTranslate(uint64_t target) { return target==aliasTarget ? aliasPe : target; }
static bool RtlIsEcCode(ULONG_PTR target) { ++ecCalls; return target==acceptedEcTarget; }
using DWORD=uint32_t; using DWORD64=uint64_t; using UINT=uint32_t; using UINT64=uint64_t; using ULONG=uint32_t;
struct ARM64EC_NT_CONTEXT {
 uint32_t ContextFlags=0,AMD64_MxCsr=0,AMD64_MxCsr_copy=0,AMD64_EFlags=0;
 uint16_t AMD64_SegCs=0,AMD64_SegDs=0,AMD64_SegEs=0,AMD64_SegFs=0,AMD64_SegGs=0,AMD64_SegSs=0;
 uint64_t X0=0,X1=0,X2=0,X3=0,X4=0,X5=0,X6=0,X7=0,X8=0,X9=0,X10=0,X11=0,X12=0,X15=0,X19=0,X20=0,X21=0,X22=0,X25=0,X26=0,X27=0,Fp=0,Lr=0,Sp=0,Pc=0;
 uint16_t X16_0=0,X16_1=0,X16_2=0,X16_3=0,X17_0=0,X17_1=0,X17_2=0,X17_3=0;
 __uint128_t V[16]{};
};
constexpr uint32_t CONTEXT_ARM64=0x400000,CONTEXT_AMD64=0x100000;
constexpr uint32_t CONTEXT_ARM64_CONTROL=0x400001,CONTEXT_ARM64_INTEGER=0x400002,CONTEXT_ARM64_FLOATING_POINT=0x400004;
constexpr uint32_t CONTEXT_AMD64_CONTROL=0x100001,CONTEXT_AMD64_INTEGER=0x100002,CONTEXT_AMD64_FLOATING_POINT=0x100008;
constexpr uint32_t CONTEXT_CONTROL=CONTEXT_ARM64_CONTROL,CONTEXT_INTEGER=CONTEXT_ARM64_INTEGER,CONTEXT_FLOATING_POINT=CONTEXT_ARM64_FLOATING_POINT;
constexpr uint32_t CONTEXT_ARM64_X18=0x10,CONTEXT_DEBUG_REGISTERS=0x400008;
struct syscall_frame { uint64_t x[29]{},fp=0,lr=0,sp=0,pc=0; uint32_t cpsr=0,fpcr=0,fpsr=0,restore_flags=0; __uint128_t v[32]{}; } selfFrame;
using CONTEXT=ARM64_NT_CONTEXT;
static syscall_frame* get_syscall_frame() { return &selfFrame; }
struct NativeContinuationCapture { ARM64_NT_CONTEXT context{}; uint64_t unused=0,observedLr=0,observedSp=0,returned=0; };
static_assert(offsetof(NativeContinuationCapture,observedLr)==808 && offsetof(NativeContinuationCapture,observedSp)==816 && offsetof(NativeContinuationCapture,returned)==824);
extern "C" void ExerciseNativeContinuation(NativeContinuationCapture*,void(*)(NativeContinuationCapture*,void*),void*);
extern "C" void NativeSyscallRet();
