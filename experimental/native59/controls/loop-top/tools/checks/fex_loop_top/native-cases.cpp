// Appended to byte-extracted production helpers/gate/packer by qualify.py.
static unsigned controls=0;
static void Check(bool value,const char* name) {
  if(!value) { std::fprintf(stderr,"ASSERT: %s\n",name); std::exit(1); }
}
static FEXCore::Core::Frame OldFrame(uint64_t loop) {
  FEXCore::Core::Frame f{};f.Pointers.DispatcherLoopTop=loop;
  f.State.rip=0x14816e55c;
  for(unsigned i=0;i<16;++i) {f.State.gregs[i]=0xface000000+i; f.State.xmm.sse.data[i][0]=0xdead000000+i; f.State.xmm.sse.data[i][1]=0xbad0000000+i; f.State.avx_high[i]=(__uint128_t{0x33445566+i}<<64)|(0x778899aa+i);}
  f.State.gregs[4]=0x70219ae9c8; f.State.compactFlags=0x202;
  for(unsigned i=0;i<8;++i) {f.State.mm[i][0]=0x112230000+i;f.State.mm[i][1]=0xa100+i;}
  return f;
}
static void Start(FEXCore::Core::Frame& f,FEXCore::Core::InternalThreadState& thread,uint64_t loop) {
  thread.CurrentFrame=&f;activeThread=&thread;ctx=ContextAdapter{};
  delegator.config.DispatcherBegin=loop-0x130;delegator.config.DispatcherEnd=loop+0x1000;
}
static ARM64_NT_CONTEXT Execute(FEXCore::Core::Frame& f,const ARM64_NT_CONTEXT& captured,uint32_t code) {
  auto input=captured;EXCEPTION_RECORD rec{code};ReconstructBeforePacking(rec,input);
  return StoreStateToPackedECContext(activeThread,0x0123,0x0456);
}
static std::array<uint64_t,16> PackedGprs(const ARM64_NT_CONTEXT& c) {
  return {c.X8,c.X0,c.X1,c.X27,c.Sp,c.Fp,c.X25,c.X26,c.X2,c.X3,c.X4,c.X5,c.X19,c.X20,c.X21,c.X22};
}
static void ValidateLive(const FEXCore::Core::Frame& original,const FEXCore::Core::Frame& after,const ARM64_NT_CONTEXT& capture,const ARM64_NT_CONTEXT& packed,bool preserveRip) {
  const auto mapped=PackedGprs(packed);
  Check(mapped[4]==capture.X[23],"live SRA RSP replaces stale frame RSP");
  Check(mapped[4]!=capture.Sp,"guest RSP is not emulator stack SP");
  for(unsigned i=0;i<16;++i) {
    Check(mapped[i]==capture.X[delegator.config.SRAGPRMapping[i]],"all sixteen live GPRs packed");
    Check(after.State.gregs[i]==mapped[i],"stored GPRs now match the live bank");
    Check(packed.V[i]==capture.V[delegator.config.SRAFPRMapping[i]],"all sixteen live vectors packed");
    Check(packed.V[16+i]==original.State.avx_high[i],"memory YMM upper bank unchanged");
  }
  Check(std::memcmp(after.State.mm,original.State.mm,sizeof(original.State.mm))==0,"memory MM/native auxiliary bank unchanged");
  Check(std::memcmp(after.State.avx_high,original.State.avx_high,sizeof(original.State.avx_high))==0,"memory AVX upper bank unchanged");
  Check(ctx.liveFlagsCalls==1 && ctx.lastPF==capture.X[9] && ctx.lastAF==capture.X[24] && ctx.lastCpsr==capture.Cpsr,"same existing live flag reconstruction inputs");
  Check(after.State.compactFlags==0x8d5 && packed.Cpsr==0xf0000000,"existing flag result packed");
  Check(packed.Fpcr==0x123 && packed.Fpsr==0x456,"FP control parameters preserved");
  Check(packed.Pc==(preserveRip?original.State.rip:0x114f334000),"current state RIP or ordinary metadata RIP preserved");
  Check(ctx.restoreCalls==(preserveRip?0:1),"dispatcher does not query translated-block RIP metadata");
  Check(packed.X13==0 && packed.X14==0 && packed.X18==0 && packed.X23==0 && packed.X24==0 && packed.X28==0,"existing packed EC reserved registers remain zero");
}
static void ValidateUnchanged(const FEXCore::Core::Frame& original,const FEXCore::Core::Frame& after,const ARM64_NT_CONTEXT& packed) {
  Check(std::memcmp(&original.State,&after.State,sizeof(original.State))==0,"unrelated dispatcher stored state remains unchanged");
  Check(ctx.restoreCalls==0 && ctx.liveFlagsCalls==0,"unrelated dispatcher not reconstructed");
  const auto mapped=PackedGprs(packed);
  for(unsigned i=0;i<16;++i) Check(mapped[i]==original.State.gregs[i],"unrelated dispatcher uses original packing");
}
int main() {
  constexpr auto suspendCode=0xe0425355u;
  const auto loop=reinterpret_cast<uint64_t>(&EntryLoopTopTestPoint);
  auto frame=OldFrame(loop);const auto old=frame;
  FEXCore::Core::InternalThreadState thread{&frame};Start(frame,thread,loop);
  alignas(16) uint64_t bank[16];alignas(16) __uint128_t vectors[16];alignas(16) std::byte emulator[16384];
  for(unsigned i=0;i<16;++i) {bank[i]=0xabcdef800000+i;vectors[i]=(static_cast<__uint128_t>(0x1010100000000000ull+i)<<64)|(0x2020200000000000+i);}
  NativeCapture captured{};
  CaptureEntryLoopTop(&captured,&frame.State.rip,old.State.rip,bank,vectors,emulator+sizeof(emulator));
  Check(captured.context.Pc==loop && captured.context.X23==captured.savedNativeSp,"actual native EntryEC-style publication captured");
  Check(captured.savedNativeSp%16==0 && captured.context.Sp%16==0 && old.State.gregs[4]%16==8,"actual native aligned stack versus stale x64 stack");
  Check(captured.context.X23!=captured.context.Sp,"real native and synthetic emulator stacks distinct");
  for(unsigned i=0;i<16;++i) {if(i!=4) Check(captured.context.X[delegator.config.SRAGPRMapping[i]]==bank[i],"actual native live GPR seed captured");Check(captured.context.V[i]==vectors[i],"actual native live vector seed captured");}
  ++controls;
  auto packed=Execute(frame,captured.context,suspendCode);
#ifdef EXPECT_IOS_FIX
  ValidateLive(old,frame,captured.context,packed,true);
  Check(packed.Sp%16==0,"native continuation receives exact aligned live SP without padding");
#else
  ValidateUnchanged(old,frame,packed);
#endif
  ++controls;
  for(auto code:{0xc0000005u,0xe0000001u,0x80000003u}) {
    frame=OldFrame(loop);Start(frame,thread,loop);const auto before=frame;
    packed=Execute(frame,captured.context,code);ValidateUnchanged(before,frame,packed);++controls;
  }
  for(auto offset:{-4ll,4ll,0x10ll,-0x20ll}) {
    frame=OldFrame(loop);Start(frame,thread,loop);const auto before=frame;auto c=captured.context;c.Pc=loop+offset;
    packed=Execute(frame,c,suspendCode);ValidateUnchanged(before,frame,packed);++controls;
  }
  frame=OldFrame(loop+0x20);Start(frame,thread,loop);const auto before=frame;
  packed=Execute(frame,captured.context,suspendCode);ValidateUnchanged(before,frame,packed);++controls;
  for(auto pc:{loop+0x2000,loop-0x1000}) {
    frame=OldFrame(loop);Start(frame,thread,loop);const auto original=frame;auto c=captured.context;c.Pc=pc;
    packed=Execute(frame,c,0xc0000005);ValidateLive(original,frame,c,packed,false);Check(ctx.lastRestorePC==pc,"ordinary translated block performs metadata lookup");++controls;
  }
  features.avx=false;frame=OldFrame(loop);Start(frame,thread,loop);const auto original=frame;
  packed=Execute(frame,captured.context,suspendCode);
#ifdef EXPECT_IOS_FIX
  ValidateLive(original,frame,captured.context,packed,true);
#else
  ValidateUnchanged(original,frame,packed);
#endif
  Check(packed.ContextFlags==CONTEXT_ARM64_FULL,"AVX-unavailable packing retains ordinary flags");++controls;
  features.avx=true;frame=OldFrame(loop);Start(frame,thread,loop);packed=Execute(frame,captured.context,suspendCode);
  Check(packed.ContextFlags==(CONTEXT_ARM64_FULL|CONTEXT_ARM64_FEX_YMMSTATE),"AVX-available packing keeps existing extension");++controls;
  std::printf("NATIVE_LOOP_TOP_CONTROLS=%u actual_arm64_snapshot=1 full_gpr=16 full_vector=16 no_padding=1 runtime_executed=0\n",controls);
  return controls==14?0:2;
}
