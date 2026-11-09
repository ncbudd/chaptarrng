#!/usr/bin/env python3
"""Keep PR-controlled ignores from weakening the trusted scanner policy."""
import hashlib
from pathlib import Path
import re
import sys


ANNOTATION = re.compile(r"nosemgrep|trivy\s*:\s*ignore|tfsec\s*:\s*ignore|checkov\s*:\s*skip", re.I)


def annotations(text):
    lines = text.splitlines()
    return {
        hashlib.sha256("\n".join(lines[max(0, i - 3):i + 5]).encode()).hexdigest()
        for i, line in enumerate(lines) if ANNOTATION.search(line)
    }


def check(policy, source):
    issues = []
    for path in Path(source).rglob("*"):
        relative = path.relative_to(source)
        if ".git" in relative.parts:
            continue
        if path.is_symlink():
            issues.append(f"Scanner source must not contain symbolic links: {relative}")
            continue
        if not path.is_file():
            continue
        baseline = Path(policy) / relative
        data = path.read_bytes()
        old = baseline.read_bytes() if baseline.is_file() and not baseline.is_symlink() else b""
        if path.name == ".semgrepignore" and data != old:
            issues.append(f"Semgrep ignore policy must be reviewed on the trusted base: {relative}")
        if annotations(data.decode("utf-8", errors="replace")) - annotations(old.decode("utf-8", errors="replace")):
            issues.append(f"New or changed scanner suppression requires trusted-base review: {relative}")
    if issues:
        raise ValueError("\n".join(issues))
    print("Scanner suppression policy matches the reviewed base")


if __name__ == "__main__":
    check(Path(sys.argv[1]), Path(sys.argv[2]))
