// Calls and registers extracted byte-for-byte from the held candidate and original emitter.
#include <FEXCore/Core/CoreState.h>
#include <CodeEmitter/Emitter.h>
#include <array>
#include <cstdio>
#include <cstdlib>
#define STATE_PTR(STATE_TYPE, FIELD) STATE.R(), offsetof(FEXCore::Core::STATE_TYPE, FIELD)
using namespace FEXCore;
constexpr auto STATE = ARMEmitter::XReg::x28;
constexpr auto TMP1 = ARMEmitter::XReg::x10;
constexpr auto TMP3 = ARMEmitter::XReg::x12;
constexpr auto EC_CALL_CHECKER_PC_REG = ARMEmitter::XReg::x9;
constexpr auto REG_PF = ARMEmitter::Reg::r9;
constexpr auto REG_AF = ARMEmitter::Reg::r24;
  constexpr std::array<ARMEmitter::Register, 18> StaticRegisters = {
    ARMEmitter::Reg::r8,
    ARMEmitter::Reg::r0,
    ARMEmitter::Reg::r1,
    ARMEmitter::Reg::r27,
    // SP's register location isn't specified by the ARM64EC ABI, we choose to use r23
    ARMEmitter::Reg::r23,
    ARMEmitter::Reg::r29,
    ARMEmitter::Reg::r25,
    ARMEmitter::Reg::r26,
    ARMEmitter::Reg::r2,
    ARMEmitter::Reg::r3,
    ARMEmitter::Reg::r4,
    ARMEmitter::Reg::r5,
    ARMEmitter::Reg::r19,
    ARMEmitter::Reg::r20,
    ARMEmitter::Reg::r21,
    ARMEmitter::Reg::r22,
    // PF/AF must be last.
    REG_PF,
    REG_AF,
  };
class Probe:public ARMEmitter::Emitter {
public:using ARMEmitter::Emitter::Emitter;
void entry(){
  str(ARMEmitter::XReg::zr, STATE_PTR(CpuStateFrame, IosEnterECSuspendTarget));
  str(ARMEmitter::XReg::x30, STATE_PTR(CpuStateFrame, IosEnterECSuspendLR));
  str(EC_CALL_CHECKER_PC_REG, STATE_PTR(CpuStateFrame, State.rip));
  str(EC_CALL_CHECKER_PC_REG, STATE_PTR(CpuStateFrame, IosLastEnterECRip));
  add(ARMEmitter::Size::i64Bit, StaticRegisters[X86State::REG_RSP], ARMEmitter::Reg::rsp, 0);
  str(StaticRegisters[X86State::REG_RSP].X(), STATE_PTR(CpuStateFrame, IosEnterECSuspendSP));
  str(EC_CALL_CHECKER_PC_REG, STATE_PTR(CpuStateFrame, IosEnterECSuspendTarget));
  add(ARMEmitter::Size::i64Bit, ARMEmitter::Reg::rsp, TMP1, 0);
}
void loop(){auto RipReg=TMP3;
  ldr(RipReg, STATE_PTR(CpuStateFrame, State.rip));
  str(ARMEmitter::XReg::zr, STATE_PTR(CpuStateFrame, IosEnterECSuspendTarget));
}
};
static unsigned checks=0;
static void check(bool value,const char* name){if(!value){std::fprintf(stderr,"FAIL: %s\n",name);std::abort();}++checks;}
static uint32_t store(unsigned rt,size_t offset){return 0xf9000000u|((offset/8)<<10)|(28<<5)|rt;}
int main(){
 using F=FEXCore::Core::CpuStateFrame;
 std::array<uint32_t,32> code{};Probe p(reinterpret_cast<uint8_t*>(code.data()),sizeof(code));p.entry();p.loop();
 check(p.GetCursorOffset()==40,"exact 8 entry calls and 2 loop calls");
 check(StaticRegisters[X86State::REG_RSP].X().Idx()==23,"actual EC SRA native stack register is23");
 check(code[0]==store(31,offsetof(F,IosEnterECSuspendTarget)),"first store invalidates record");
 check(code[1]==store(30,offsetof(F,IosEnterECSuspendLR)),"second store captures incoming LR");
 check(code[2]==store(9,offsetof(F,State.rip)),"actual x9 target writes State.rip");
 check(code[3]==store(9,offsetof(F,IosLastEnterECRip)),"existing EnterEC witness preserved");
 check(code[4]==0x910003f7u,"exact native SP copied to SRA x23 without padding");
 check(code[5]==store(23,offsetof(F,IosEnterECSuspendSP)),"native SP stored before target publication");
 check(code[6]==store(9,offsetof(F,IosEnterECSuspendTarget)),"target published last after native controls");
 check(code[7]==0x9100015fu,"existing SP switch to emulator stack x10 preserved");
 check(code[8]==(0xf9400000u|((offsetof(F,State.rip)/8)<<10)|(28<<5)|12),"exact advertised LoopTop first instruction is RIP load");
 check(code[9]==store(31,offsetof(F,IosEnterECSuspendTarget)),"record cleared immediately after exact capture point");
 for(unsigned i=0;i<10;++i)std::printf("word%u=%08x\n",i,code[i]);
 std::printf("frame=%zu Pointers=%zu LastLR=%zu Target=%zu SP=%zu LR=%zu; PASS %u emitter controls\n",sizeof(F),offsetof(F,Pointers),offsetof(F,IosLastCallbackLR),offsetof(F,IosEnterECSuspendTarget),offsetof(F,IosEnterECSuspendSP),offsetof(F,IosEnterECSuspendLR),checks);
}
