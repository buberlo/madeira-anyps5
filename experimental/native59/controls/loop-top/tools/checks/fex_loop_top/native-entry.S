// Native ARM64 fixture reproducing the two production EnterEC publications.
// It is synthetic; it never executes FEX or the signed iPad runtime.
.text
.p2align 2
.globl _CaptureEntryLoopTop
.globl _EntryLoopTopTestPoint
_CaptureEntryLoopTop:
  stp x19, x20, [sp, #-96]!
  stp x21, x22, [sp, #16]
  stp x23, x24, [sp, #32]
  stp x25, x26, [sp, #48]
  stp x27, x28, [sp, #64]
  stp x29, x30, [sp, #80]
  sub sp, sp, #128
  stp q8, q9, [sp]
  stp q10, q11, [sp, #32]
  stp q12, q13, [sp, #64]
  stp q14, q15, [sp, #96]
  mov x16, x0
  mov x12, sp
  str x12, [x16, #800]
  str x2, [x1] // State.rip published, as in actual EnterEC.
  mov x12, x3
  mov x14, x4
  mov x17, x5
  ldp q0, q1, [x14]
  ldp q2, q3, [x14, #32]
  ldp q4, q5, [x14, #64]
  ldp q6, q7, [x14, #96]
  ldp q8, q9, [x14, #128]
  ldp q10, q11, [x14, #160]
  ldp q12, q13, [x14, #192]
  ldp q14, q15, [x14, #224]
  ldr x8, [x12]
  ldr x0, [x12, #8]
  ldr x1, [x12, #16]
  ldr x27, [x12, #24]
  ldr x29, [x12, #40]
  ldr x25, [x12, #48]
  ldr x26, [x12, #56]
  ldr x2, [x12, #64]
  ldr x3, [x12, #72]
  ldr x4, [x12, #80]
  ldr x5, [x12, #88]
  ldr x19, [x12, #96]
  ldr x20, [x12, #104]
  ldr x21, [x12, #112]
  ldr x22, [x12, #120]
  mov x9, #0x46
  mov x24, #0x10
  mov x12, #0xa0000000
  msr nzcv, x12
  add x23, sp, #0 // Exact live SRA RSP publication from actual EnterEC.
  mov sp, x17 // Switch to an independent aligned synthetic emulator stack.
_EntryLoopTopTestPoint:
  stp x0, x1, [x16]
  stp x2, x3, [x16, #16]
  stp x4, x5, [x16, #32]
  stp x6, x7, [x16, #48]
  stp x8, x9, [x16, #64]
  stp x10, x11, [x16, #80]
  stp x12, x13, [x16, #96]
  stp x14, x15, [x16, #112]
  stp x16, x17, [x16, #128]
  stp x18, x19, [x16, #144]
  stp x20, x21, [x16, #160]
  stp x22, x23, [x16, #176]
  stp x24, x25, [x16, #192]
  stp x26, x27, [x16, #208]
  stp x28, x29, [x16, #224]
  str x30, [x16, #240]
  mov x17, sp
  str x17, [x16, #248]
  adr x17, _EntryLoopTopTestPoint
  str x17, [x16, #256]
  mrs x17, nzcv
  str w17, [x16, #264]
  stp q0, q1, [x16, #288]
  stp q2, q3, [x16, #320]
  stp q4, q5, [x16, #352]
  stp q6, q7, [x16, #384]
  stp q8, q9, [x16, #416]
  stp q10, q11, [x16, #448]
  stp q12, q13, [x16, #480]
  stp q14, q15, [x16, #512]
  ldr x17, [x16, #800]
  mov sp, x17
  ldp q8, q9, [sp]
  ldp q10, q11, [sp, #32]
  ldp q12, q13, [sp, #64]
  ldp q14, q15, [sp, #96]
  add sp, sp, #128
  ldp x21, x22, [sp, #16]
  ldp x23, x24, [sp, #32]
  ldp x25, x26, [sp, #48]
  ldp x27, x28, [sp, #64]
  ldp x29, x30, [sp, #80]
  ldp x19, x20, [sp], #96
  ret
