// All address constants below are synthetic fixture values, never captured process addresses.

static unsigned controls=0;
static void Check(bool ok,const char* what) { if(!ok) { std::fprintf(stderr,"FAIL: %s\n",what); std::abort(); } ++controls; }
struct Fixture {
 FEXCore::Core::Frame frame{};
 FEXCore::Core::InternalThreadState thread{&frame};
 ARM64_NT_CONTEXT context{};
 EXCEPTION_RECORD rec{0xe0425355u};
 Fixture() {
  activeThread=&thread; frame.Pointers.DispatcherLoopTop=0x110008000;
  context.Pc=frame.Pointers.DispatcherLoopTop; context.Lr=0x120123450; context.X23=0x130219a000;
  frame.State.rip=0x1201485a8; frame.State.gregs[4]=context.X23;
  frame.State.mm[0][0]=2;
  frame.IosEnterECSuspendTarget=frame.State.rip; frame.IosEnterECSuspendSP=context.X23; frame.IosEnterECSuspendLR=context.Lr;
  for(unsigned i=0;i<16;++i) {
   context.X[delegator.config.SRAGPRMapping[i]]=0x70000000+i;
   context.V[i]=(static_cast<__uint128_t>(0xa0123456789abcdeULL)<<64)|i;
   frame.State.avx_high[i]=(static_cast<__uint128_t>(0xc0123456789abcdeULL)<<64)|i;
  }
  context.X23=frame.IosEnterECSuspendSP; acceptedEcTarget=frame.State.rip;
  aliasTarget=aliasPe=0; delegator.config.DispatcherBegin=context.Pc-16; delegator.config.DispatcherEnd=context.Pc+256;
 }
 ARM64_NT_CONTEXT snap() { return SnapshotBeforeDispatch(rec,context); }
};
static void Negative(Fixture& f,const char* name) {
 auto value=f.snap(); Check(value.Lr==2,name);
}
static void NativeReturnCallback(NativeContinuationCapture* capture,void*) {
 Fixture f;
 auto native=capture->context;
 f.context.Lr=native.Lr; f.context.X23=native.Sp;
 f.frame.State.rip=native.Pc; f.frame.IosEnterECSuspendTarget=native.Pc;
 f.frame.IosEnterECSuspendSP=native.Sp; f.frame.IosEnterECSuspendLR=native.Lr;
 acceptedEcTarget=native.Pc;
 auto packed=f.snap();
 Check(packed.Pc==native.Pc && packed.Sp==native.Sp,"native return PC/SP are exact, no padding");
 Check(packed.Lr==native.Lr,"captured native LR replaces stale MM before conversion");
 ARM64EC_NT_CONTEXT ec{}; ARM64_NT_CONTEXT restored{};
 context_arm_to_x64(&ec,&packed); context_x64_to_arm(&restored,&ec);
 Check(restored.Lr==native.Lr && restored.Sp==native.Sp && restored.Pc==native.Pc,"real Wine converters preserve native controls");
 selfFrame={}; selfFrame.x[18]=0x130ffd000;
 ApplySelfRegisterBlock(&restored);
 Check(selfFrame.x[18]==0x130ffd000,"real self-apply block preserves authoritative frame TEB after packed X18 zero");
 capture->context=restored;
}
int main() {
 Fixture f; auto beforeMm=f.frame.State.mm[0][0]; auto packed=f.snap();
#ifdef FEX_IOS_HOST
 Check(packed.Lr==f.context.Lr,"exact live EnterEC/native target snapshot has native LR");
#else
 Check(packed.Lr==2,"non-iOS original MM packing remains unchanged");
#endif
 Check(f.frame.State.mm[0][0]==beforeMm,"snapshot never mutates MM state");
 Check(packed.Sp==f.context.X23,"live SRA native SP remains exact");
 Check(packed.X18==0,"packed x64 forbidden-register rule remains unchanged");
 Check(std::memcmp(packed.V+16,f.frame.State.avx_high,sizeof(f.frame.State.avx_high))==0,"FEX AVX upper bank packing is unchanged");
 Check(packed.ContextFlags==(CONTEXT_ARM64_FULL|CONTEXT_ARM64_FEX_YMMSTATE),"FEX AVX extension flags remain unchanged");
#ifdef FEX_IOS_HOST
 Check(packed.Cpsr==0xf0000000u,"existing packed async condition flags are unchanged");
 Check(std::memcmp(packed.V,f.context.V,16*sizeof(__uint128_t))==0,"all live XMM vectors are preserved");
 for(unsigned i=0;i<16;++i) Check(f.frame.State.gregs[i]==f.context.X[delegator.config.SRAGPRMapping[i]],"all16 live SRA GPRs are preserved");
#else
 Check(packed.Cpsr==0,"non-iOS dispatcher snapshot keeps stored flags");
 Check(f.frame.State.gregs[0]==0,"non-iOS dispatcher snapshot keeps stored GPRs");
#endif
 Fixture ordinary; ordinary.frame.IosEnterECSuspendTarget=0; Negative(ordinary,"inactive FillSRA/JIT record rejected");
 Fixture stale; ++stale.frame.IosEnterECSuspendTarget; Negative(stale,"stale target rejected");
 Fixture sp; sp.frame.IosEnterECSuspendSP+=8; Negative(sp,"stale SP rejected, no alignment repair");
 Fixture lr; ++lr.frame.IosEnterECSuspendLR; Negative(lr,"stale LR rejected");
 Fixture adjacent; adjacent.context.Pc+=4; Negative(adjacent,"adjacent LoopTop instruction rejected");
 Fixture exception; exception.rec.ExceptionCode=0xc0000005; Negative(exception,"ordinary exception rejected");
 Fixture wrongLoop; wrongLoop.frame.Pointers.DispatcherLoopTop+=16; Negative(wrongLoop,"different advertised LoopTop rejected");
 Fixture x64; acceptedEcTarget=x64.frame.State.rip+4; Negative(x64,"synthetic x64 target keeps original MM LR");
#ifdef FEX_IOS_HOST
 Fixture emitted; NativeCapture entered{};
 alignas(16) std::array<unsigned char,8192> emulatorStack{};
 std::array<uint64_t,16> gprs{}; std::array<__uint128_t,16> vectors{};
 for(unsigned i=0;i<16;++i) { gprs[i]=0xa00000+i; vectors[i]=i+42; }
 CaptureEntryLoopTop(&entered,&emitted.frame.State.rip,emitted.frame.State.rip,gprs.data(),vectors.data(),
                     emulatorStack.data()+emulatorStack.size(),&emitted.frame.IosEnterECSuspendTarget);
 Check(emitted.frame.IosEnterECSuspendTarget==emitted.frame.State.rip &&
       emitted.frame.IosEnterECSuspendSP==entered.context.X23 &&
       emitted.frame.IosEnterECSuspendLR==entered.context.Lr,"real native entry fixture publishes captured target/SP/LR");
 emitted.context=entered.context; emitted.frame.Pointers.DispatcherLoopTop=entered.context.Pc;
 delegator.config.DispatcherBegin=entered.context.Pc-16;delegator.config.DispatcherEnd=entered.context.Pc+256;
 Check(emitted.snap().Lr==entered.context.Lr,"actual captured native link survives initial packed snapshot");
 Fixture alias; aliasTarget=alias.frame.State.rip; aliasPe=0x1400585a8; acceptedEcTarget=aliasPe;
 Check(alias.snap().Lr==alias.context.Lr,"pool alias requires exact verified PE EC target");
 Fixture intent; auto snapshot=intent.snap(); ARM64EC_NT_CONTEXT ec{}; ARM64_NT_CONTEXT restored{};
 context_arm_to_x64(&ec,&snapshot); ec.Lr=0x120112234; context_x64_to_arm(&restored,&ec);
 Check(restored.Lr==ec.Lr,"later intentional handler LR edit is honored without resume override");
 NativeContinuationCapture capture{};
 ExerciseNativeContinuation(&capture,NativeReturnCallback,nullptr);
 Check(capture.returned==1,"actual native RET reaches captured continuation");
 Check(capture.observedLr==capture.context.Lr && capture.observedSp==capture.context.Sp,"actual native RET preserves exact LR/SP");
#endif
 std::printf("PASS %u controls; isolated native fixture, not signed runtime\n",controls);
}
