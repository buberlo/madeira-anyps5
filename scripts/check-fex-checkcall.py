#!/usr/bin/env python3
"""Execute FEX's actual CheckCall body on Darwin ARM64 and detect both old bugs.

Only object-format symbol and relocation syntax changes for native execution.
Output is retained under ignored build/. This is not PE/iPad execution evidence.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "upstreams/FEX/Source/Windows/ARM64EC/Module.S"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract(path):
    text = path.read_text()
    match = re.search(r'^"CheckCall":\n(.*?^end:\n\s+ret)\n', text, re.M | re.S)
    if not match or text.count('"CheckCall":') != 1:
        raise ValueError("expected exactly one actual CheckCall body")
    body = match.group(1)
    if body.count("ldr w17, [x17, #:lo12:NtDllRedirectionLUTSize]") != 1 or body.count("b.hs end") != 1:
        raise ValueError("current source does not contain the qualified uint32/exclusive-bound fix")
    return body


def assembly(body, alignment):
    native = re.sub(r'adrp (x\d+), (NtDll\w+)', r'adrp \1, _\2@PAGE', body)
    native = re.sub(r'#:lo12:(NtDll\w+)', r'_\1@PAGEOFF', native)
    padding = ".long 0\n" if alignment == 4 else ""
    return f""".section __DATA,__data
.p2align 3
.globl _NtDllBase
_NtDllBase: .quad 0
.globl _NtDllRedirectionLUT
_NtDllRedirectionLUT: .quad 0
.p2align 3
{padding}.globl _NtDllRedirectionLUTSize
_NtDllRedirectionLUTSize: .long 0
.globl _NtDllSizePoison
_NtDllSizePoison: .long 0
.section __TEXT,__text
.p2align 2
_CheckCall:
{native}
.globl _InvokeCheckCall
.p2align 2
_InvokeCheckCall:
  stp x29, x30, [sp, #-16]!
  mov x29, sp
  mov x11, x0
  bl _CheckCall
  mov x0, x11
  ldp x29, x30, [sp], #16
  ret
"""


def coff_assembly(body):
    return """.data
.p2align 3
.globl NtDllBase
NtDllBase: .quad 0
.globl NtDllRedirectionLUT
NtDllRedirectionLUT: .quad 0
.p2align 3
.long 0
.globl NtDllRedirectionLUTSize
NtDllRedirectionLUTSize: .long 0
.globl NtDllSizePoison
NtDllSizePoison: .long 0
.text
.p2align 2
.globl CheckCall
CheckCall:
""" + body + "\n"


def run(argv, output, name, env):
    result = subprocess.run([str(x) for x in argv], env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90)
    log = output / (name + ".log")
    log.write_text(result.stdout)
    return {"argv": [str(x) for x in argv], "returncode": result.returncode,
            "log": str(log), "logSha256": digest(log)}, result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fex", type=Path, default=ROOT / "upstreams/FEX")
    parser.add_argument("--output", type=Path, default=ROOT / "build/fex-checkcall-6021-native")
    parser.add_argument("--pe-compiler", type=Path,
                        help="llvm-mingw ARM64EC clang; otherwise search PATH")
    args = parser.parse_args()
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        parser.error("requires native Darwin arm64 execution")
    output = args.output.resolve()
    if output.exists():
        parser.error("output already exists; use a new ignored build directory")
    output.mkdir(parents=True)
    source = args.fex / "Source/Windows/ARM64EC/Module.S"
    body = extract(source)
    (output / "actual-checkcall-body.S").write_text(body + "\n")
    env = dict(os.environ)
    env.setdefault("DEVELOPER_DIR", "/Applications/Xcode.app/Contents/Developer")
    tests = []
    harness = ROOT / "tools/checks/fex_checkcall_guard.cpp"
    for alignment in (0, 4):
        name = "actual-alignment-" + str(alignment)
        asm = output / (name + ".S")
        binary = output / name
        asm.write_text(assembly(body, alignment))
        build, _ = run(["xcrun", "clang++", "-arch", "arm64", "-std=c++20", "-O2", "-g",
                        harness, asm, "-o", binary], output, name + "-link", env)
        if build["returncode"]:
            raise RuntimeError("actual assembly fixture failed to link: " + build["log"])
        execution, text = run([binary, str(alignment)], output, name + "-run", env)
        if execution["returncode"] or "passed 10 CheckCall cases" not in text:
            raise RuntimeError("actual assembly guard test failed: " + execution["log"])
        tests.append({"kind": "actual_source", "alignmentModulo8": alignment,
                      "cases": 10, "assemblySha256": digest(asm), "binarySha256": digest(binary),
                      "build": build, "execution": execution})
    # The old width can link with an aligned size; its poison upper word then
    # admits a protected OOB access. The old branch independently admits ==size.
    mutants = {"old-width": body.replace("ldr w17, [x17, #:lo12:NtDllRedirectionLUTSize]",
                                         "ldr x17, [x17, #:lo12:NtDllRedirectionLUTSize]"),
               "old-inclusive-bound": body.replace("b.hs end", "b.hi end")}
    for name, mutant in mutants.items():
        asm, binary = output / (name + ".S"), output / name
        asm.write_text(assembly(mutant, 0))
        build, _ = run(["xcrun", "clang++", "-arch", "arm64", "-std=c++20", "-O2",
                        harness, asm, "-o", binary], output, name + "-link", env)
        if build["returncode"]:
            raise RuntimeError("aligned mutation must link before testing it")
        execution, text = run([binary, "0", "exact-size"], output, name + "-run", env)
        if execution["returncode"] not in (-signal.SIGBUS, -signal.SIGSEGV) or "check exact-size" not in text:
            raise RuntimeError("guard fixture failed to detect " + name)
        tests.append({"kind": "deliberate_mutation_detected", "mutation": name,
                      "build": build, "execution": execution})
    compiler = args.pe_compiler or shutil.which("arm64ec-w64-mingw32-clang")
    pe_alignment = "unavailable_no_ARM64EC_compiler"
    if compiler:
        # Windows COFF enforces the scaled low12 relocation's alignment.
        # Darwin's linker is not a substitute for this Windows link check.
        compiler = Path(compiler).absolute()
        for name, actual_body in (("actual-coff", body), ("old-width-coff", mutants["old-width"])):
            asm, obj = output / (name + ".S"), output / (name + ".obj")
            asm.write_text(coff_assembly(actual_body))
            compile_result, _ = run([compiler, "-c", asm, "-o", obj], output, name + "-compile", env)
            if compile_result["returncode"]:
                raise RuntimeError("COFF alignment fixture failed to assemble")
            link, text = run([compiler, "-shared", "-nostdlib", "-Wl,--entry,CheckCall", obj,
                              "-o", output / (name + ".dll")], output, name + "-link", env)
            if name == "actual-coff" and link["returncode"]:
                raise RuntimeError("actual 32-bit load must link with 4-byte alignment")
            if name == "old-width-coff" and (link["returncode"] == 0 or "misaligned ldr/str offset" not in text):
                raise RuntimeError("old 64-bit relocation must reject 4-byte alignment")
            tests.append({"kind": "COFF_alignment_fixture", "mutation": name == "old-width-coff",
                          "compilerSha256": digest(compiler.resolve()), "objectSha256": digest(obj),
                          "build": compile_result, "link": link})
        objdump = compiler.parent / "llvm-objdump"
        disassembly, text = run([objdump, "-d", output / "actual-coff.obj"], output, "actual-coff-disassembly", env)
        if disassembly["returncode"] or not re.search(r"ldr\s+w17,", text) or not re.search(r"b\.hs\s", text):
            raise RuntimeError("actual COFF fixture lost the repaired instructions")
        tests.append({"kind": "COFF_object_disassembly", "execution": disassembly})
        pe_alignment = "actual_load_linked_old_load_alignment_failure_detected"
    receipt = {"schema": 1, "createdUTC": datetime.now(timezone.utc).isoformat(),
               "status": "native_actual_assembly_passed_both_mutations_detected",
               "source": str(source.resolve()), "sourceSha256": digest(source),
               "bodySha256": digest(output / "actual-checkcall-body.S"),
               "driverSha256": digest(Path(__file__)), "harnessSha256": digest(harness),
               "testedCases": 20, "tests": tests, "PEAlignment": pe_alignment, "PEExecuted": False,
               "deviceTested": False, "performanceClaim": False, "githubActionsUsed": False}
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "testedCases": 20,
                      "mutationsDetected": 3 if compiler else 2,
                      "PEAlignment": pe_alignment, "receipt": str(output / "receipt.json")}))


if __name__ == "__main__":
    main()
