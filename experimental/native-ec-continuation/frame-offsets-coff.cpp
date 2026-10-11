#include <FEXCore/Core/CoreState.h>
using F=FEXCore::Core::CpuStateFrame;
extern "C" __attribute__((section(".fexfrm"),used)) const unsigned long long fex_ec_frame_offsets[] = {sizeof(F),offsetof(F,State),offsetof(F,Pointers),offsetof(F,IosLastCallbackLR)
#if defined(FEX_IOS_HOST) && !defined(ORIGINAL_FRAME)
,offsetof(F,IosEnterECSuspendTarget),offsetof(F,IosEnterECSuspendSP),offsetof(F,IosEnterECSuspendLR)
#endif
};
