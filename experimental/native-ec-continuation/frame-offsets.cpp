#include <FEXCore/Core/CoreState.h>
#include <cstdio>
int main() {
 using F=FEXCore::Core::CpuStateFrame;
 std::printf("frame=%zu State=%zu Pointers=%zu LastLR=%zu",sizeof(F),offsetof(F,State),offsetof(F,Pointers),offsetof(F,IosLastCallbackLR));
#if defined(FEX_IOS_HOST) && !defined(ORIGINAL_FRAME)
 std::printf(" Target=%zu SP=%zu LR=%zu",offsetof(F,IosEnterECSuspendTarget),offsetof(F,IosEnterECSuspendSP),offsetof(F,IosEnterECSuspendLR));
#endif
 std::puts("");
}
