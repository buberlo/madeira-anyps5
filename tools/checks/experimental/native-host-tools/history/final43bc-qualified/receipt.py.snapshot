#!/usr/bin/env python3
"""Read-only source/dependency inventory for an explicitly supplied tool build."""
import argparse
import hashlib
import json
import os
import platform
from pathlib import Path
import subprocess
import sys


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(argv):
    result = subprocess.run(argv, capture_output=True, text=True, check=False)
    return {"argv": argv, "exitCode": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--adoption-receipt", type=Path)
    parser.add_argument("--review", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    review = json.loads(args.review.read_text())
    actual = {}
    actual_modes = {}
    for directory, directories, filenames in os.walk(source):
        directories[:] = sorted(d for d in directories if d not in (".git", "3rdparty"))
        for filename in sorted(filenames):
            path = Path(directory) / filename
            if filename == ".git":
                continue
            relative = path.relative_to(source).as_posix()
            actual[relative] = digest(path)
            actual_modes[relative] = "100755" if path.stat().st_mode & 0o111 else "100644"
    review_records = review["sourceTree"]
    expected = {relative: record["sha256"] for relative, record in review_records.items()}
    expected_modes = {relative: record["mode"] for relative, record in review_records.items()}
    source_equal = actual == expected and actual_modes == expected_modes
    dependencies = {}
    for relative, expected_commit in sorted(review["thirdPartyGitlinks"].items()):
        path = source / relative
        identity = command(["git", "--no-optional-locks", "-C", str(path), "rev-parse", "HEAD"])
        status = command(["git", "--no-optional-locks", "-C", str(path), "status", "--porcelain", "--untracked-files=all"])
        dependencies[relative] = {
            "expectedCommit": expected_commit,
            "actualCommit": identity["stdout"].strip(),
            "identityExitCode": identity["exitCode"],
            "statusExitCode": status["exitCode"],
            "clean": not status["stdout"] and status["exitCode"] == 0,
            "status": status["stdout"],
        }
    dependency_equal = all(d["clean"] and d["identityExitCode"] == 0
                           and d["actualCommit"] == d["expectedCommit"]
                           for d in dependencies.values())
    payload = {
        "schema": 1,
        "source": str(source),
        "upstreamCommit": review["upstreamCommit"],
        "patchCount": review["patchCount"],
        "adoptionReceiptSha256": digest(args.adoption_receipt) if args.adoption_receipt else None,
        "sourceReviewSha256": digest(args.review),
        "sourceEntryCount": len(actual),
        "expectedSourceEntryCount": len(expected),
        "sourceFiles": actual,
        "sourceModes": actual_modes,
        "sourceMatchesFrozenReview": source_equal,
        "missingEntries": sorted(set(expected) - set(actual)),
        "extraEntries": sorted(set(actual) - set(expected)),
        "changedEntries": sorted(k for k in set(expected) & set(actual)
                                 if expected[k] != actual[k] or expected_modes[k] != actual_modes[k]),
        "sourceMapSha256": hashlib.sha256(json.dumps(actual, sort_keys=True,
                                                       separators=(",", ":")).encode()).hexdigest(),
        "dependencies": dependencies,
        "allElevenDependenciesCleanAtExpectedGitlinks": len(dependencies) == 11 and dependency_equal,
        "host": {"system": platform.system(), "release": platform.release(),
                 "machine": platform.machine()},
        "python": {"path": sys.executable, "sha256": digest(Path(sys.executable)),
                   "version": sys.version},
        "scope": "native conversion-tool source inventory; no runtime, GPU, device or game qualification",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: payload[k] for k in ("sourceEntryCount", "sourceMapSha256",
                                             "sourceMatchesFrozenReview",
                                             "allElevenDependenciesCleanAtExpectedGitlinks")}))
    return 0 if source_equal and dependency_equal else 1


if __name__ == "__main__":
    raise SystemExit(main())
