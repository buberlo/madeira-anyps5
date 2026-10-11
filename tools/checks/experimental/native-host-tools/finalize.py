#!/usr/bin/env python3
"""Finalize local receipts after a native host-tool build and CTest run."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tool(path, version_args):
    result = subprocess.run([str(path), *version_args], capture_output=True, text=True)
    return {"path": str(path), "resolvedPath": str(path.resolve()),
            "sha256": digest(path), "versionExitCode": result.returncode,
            "version": result.stdout + result.stderr}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--configure-exit", required=True, type=int)
    parser.add_argument("--build-exit", required=True, type=int)
    parser.add_argument("--ctest-exit", required=True, type=int)
    parser.add_argument("--cmake", required=True, type=Path)
    parser.add_argument("--ninja", required=True, type=Path)
    parser.add_argument("--clang", required=True, type=Path)
    parser.add_argument("--python", required=True, type=Path)
    parser.add_argument("--harness", required=True, type=Path)
    args = parser.parse_args()
    effective_clang_result = subprocess.run(["xcrun", "--find", "clang++"],
                                             capture_output=True, text=True, check=True)
    effective_clang = Path(effective_clang_result.stdout.strip())
    directory = args.directory.resolve()
    before = json.loads((directory / "source-before.json").read_text())
    after = json.loads((directory / "source-after.json").read_text())
    inventory = json.loads((directory / "test-inventory.json").read_text())
    root_tools = [test["name"] for test in inventory["tests"]
                  if any("/tools/" in argument for argument in test.get("command", []))]
    nid_tests = [test["name"] for test in inventory["tests"]
                 if test["name"].startswith("nid_patcher_")]
    junit = ET.parse(directory / "tests.xml").getroot()
    cases = list(junit.iter("testcase"))
    test_results = []
    for case in cases:
        failed = case.find("failure") is not None or case.find("error") is not None
        skipped = case.find("skipped") is not None
        output = case.findtext("system-out", "")
        test_results.append({"name": case.attrib["name"],
                             "failed": failed, "skipped": skipped,
                             "time": case.attrib.get("time"),
                             "hostExecutionScopeNotes": [line for line in output.splitlines()
                                                         if "execution skipped" in line.lower()
                                                         or "not executed" in line.lower()]})
    binaries = {}
    for name, relative in (("relinker", "build/anyps5/core/relinker/relinker"),
                           ("nid_patcher", "build/nid_patcher")):
        path = directory / relative
        image_info = subprocess.run(["file", str(path)], capture_output=True, text=True)
        binaries[name] = {"path": str(path), "sha256": digest(path),
                          "bytes": path.stat().st_size, "format": image_info.stdout.strip()}
    receipt = {
        "schema": 1,
        "upstreamCommit": before["upstreamCommit"],
        "patchCount": before["patchCount"],
        "sourceEntryCount": before["sourceEntryCount"],
        "sourceMapSha256": before["sourceMapSha256"],
        "sourceBeforeAfterUnchanged": before["sourceFiles"] == after["sourceFiles"],
        "sourceMatchesPreparationAndReviewBeforeAfter":
            before["sourceMatchesPreparationAndReview"] and after["sourceMatchesPreparationAndReview"],
        "allElevenDependenciesCleanAtExpectedGitlinksBeforeAfter":
            before["allElevenDependenciesCleanAtExpectedGitlinks"]
            and after["allElevenDependenciesCleanAtExpectedGitlinks"],
        "preparationSha256": before["preparationSha256"],
        "sourceReviewSha256": before["sourceReviewSha256"],
        "configureExitCode": args.configure_exit,
        "buildExitCode": args.build_exit,
        "ctestExitCode": args.ctest_exit,
        "maxBuildJobs": 2,
        "resolvedEquivalentCommands": {
            "configure": [str(args.cmake), "-S", str(args.harness), "-B",
                          str(directory / "build"), "-G", "Ninja",
                          "-DANYPS5_SOURCE=" + before["source"],
                          "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_CXX_COMPILER=" + str(args.clang),
                          "-DCMAKE_OSX_ARCHITECTURES=arm64", "-DPython3_EXECUTABLE=" + str(args.python)],
            "build": [str(args.cmake), "--build", str(directory / "build"), "--parallel", "2"],
            "ctest": [str(args.cmake.parent / "ctest"), "--test-dir", str(directory / "build"),
                      "--output-on-failure", "--timeout", "30", "--parallel", "2",
                      "--output-junit", str(directory / "tests.xml")],
            "environment": {"PYTHONDONTWRITEBYTECODE": "1"},
        },
        "registeredTestCount": len(inventory["tests"]),
        "registeredRootToolTestCount": len(root_tools),
        "registeredNidPatcherTestCount": len(nid_tests),
        "registeredRelinkerTestCount": len(inventory["tests"]) - len(root_tools) - len(nid_tests),
        "executedCTestCaseCount": len(cases),
        "passedCTestCaseCount": sum(not t["failed"] and not t["skipped"] for t in test_results),
        "failedCTestCaseCount": sum(t["failed"] for t in test_results),
        "skippedCTestCaseCount": sum(t["skipped"] for t in test_results),
        "registeredAndExecutedTestNamesMatch":
            sorted(t["name"] for t in inventory["tests"]) == sorted(t["name"] for t in test_results),
        "testResults": test_results,
        "binaries": binaries,
        "toolchain": {"cmake": tool(args.cmake, ["--version"]),
                      "ninja": tool(args.ninja, ["--version"]),
                      "clang": tool(args.clang, ["--version"]),
                      "effectiveClangSelectedByXcrun": tool(effective_clang, ["--version"]),
                      "python": tool(args.python, ["--version"])},
        "evidence": {name: digest(directory / name) for name in
                     ("configure.log", "build.log", "ctest.log", "tests.xml",
                      "test-inventory.json", "source-before.json", "source-after.json",
                      "build/CMakeCache.txt", "build/build.ninja", "build/Testing/Temporary/LastTest.log")},
        "helperFiles": {path.name: digest(path) for path in sorted(Path(__file__).parent.iterdir())
                        if path.is_file()},
        "scope": "Fresh native arm64 host conversion-tool qualification. Existing host conditions "
                 "inspect emitted x86-64 PE/ELF without incompatible execution. "
                 "No HLE, GPU, game import/launch, device or gameplay qualification.",
    }
    path = directory / "receipt.json"
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"receipt": str(path), "receiptSha256": digest(path),
                      "passed": receipt["passedCTestCaseCount"],
                      "failed": receipt["failedCTestCaseCount"],
                      "skipped": receipt["skippedCTestCaseCount"]}))


if __name__ == "__main__":
    main()
