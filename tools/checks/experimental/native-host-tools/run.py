#!/usr/bin/env python3
"""Run the complete native host-tool route after external compiler coordination."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    for name in ("source", "review", "directory", "prior-inventory", "cmake", "ninja", "clang", "python"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--adoption-receipt", type=Path)
    parser.add_argument("--jobs", required=True, type=int, choices=(1, 2))
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    directory = args.directory.resolve()
    if directory.exists():
        parser.error("Use a fresh output directory; retain previous attempts")
    directory.mkdir(parents=True)
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    source = args.source.resolve()
    review = args.review.resolve()
    python = args.python.resolve()
    build = directory / "build"
    def inventory(when):
        command = [str(python), "-I", "-B", str(here / "receipt.py"), "--source", str(source),
                   "--review", str(review), "--output", str(directory / ("source-" + when + ".json"))]
        if args.adoption_receipt:
            command += ["--adoption-receipt", str(args.adoption_receipt.resolve())]
        return subprocess.run(command, env=environment).returncode
    def logged(command, filename):
        with (directory / filename).open("w") as output:
            result = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, env=environment)
        print(json.dumps({"log": filename, "exitCode": result.returncode}), flush=True)
        return result.returncode
    if inventory("before"):
        return 1
    configure = logged([str(args.cmake), "-S", str(here), "-B", str(build), "-G", "Ninja",
                        "-DANYPS5_SOURCE=" + str(source), "-DCMAKE_BUILD_TYPE=Release",
                        "-DCMAKE_CXX_COMPILER=" + str(args.clang), "-DCMAKE_MAKE_PROGRAM=" + str(args.ninja),
                        "-DCMAKE_OSX_ARCHITECTURES=arm64", "-DPython3_EXECUTABLE=" + str(python)], "configure.log")
    if configure:
        inventory("after")
        return configure
    ctest = args.cmake.resolve().parent / "ctest"
    with (directory / "test-inventory.json").open("w") as output:
        result = subprocess.run([str(ctest), "--test-dir", str(build), "--show-only=json-v1"],
                                stdout=output, env=environment)
    if result.returncode:
        inventory("after")
        return result.returncode
    built = logged([str(args.cmake), "--build", str(build), "--parallel", str(args.jobs)], "build.log")
    if built:
        inventory("after")
        return built
    tested = logged([str(ctest), "--test-dir", str(build), "--output-on-failure", "--timeout", "30",
                    "--parallel", str(args.jobs), "--output-junit", str(directory / "tests.xml")], "ctest.log")
    after = inventory("after")
    final = [str(python), "-I", "-B", str(here / "finalize.py"), "--directory", str(directory),
             "--configure-exit", str(configure), "--build-exit", str(built), "--ctest-exit", str(tested),
             "--cmake", str(args.cmake), "--ninja", str(args.ninja), "--clang", str(args.clang),
             "--python", str(python), "--harness", str(here), "--jobs", str(args.jobs),
             "--prior-inventory", str(args.prior_inventory.resolve())]
    finalized = subprocess.run(final, env=environment).returncode
    return tested or after or finalized


if __name__ == "__main__":
    raise SystemExit(main())
