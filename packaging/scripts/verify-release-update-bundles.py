#!/usr/bin/env python3
"""Require updater-compatible signatures before standalone release publication."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


PREDICATE = "https://github.com/snapetech-org/chaptarrng/release/v1"
RIDS = ("linux-x64", "linux-arm64", "linux-musl-x64", "linux-musl-arm64",
        "osx-x64", "osx-arm64", "win-x64", "win-x86", "linux-x86", "freebsd-x64")


def matches_release(verified, version, source, name, digest):
    if not isinstance(verified, list):
        return False
    for result in verified:
        statement = result.get("verificationResult", {}).get("statement", {})
        predicate = statement.get("predicate", {})
        if (statement.get("predicateType") != PREDICATE or
                predicate.get("version") != version or predicate.get("sourceCommit") != source):
            continue
        for subject in statement.get("subject", []):
            if (Path(subject.get("name", "")).name == name and
                    subject.get("digest", {}).get("sha256", "").lower() == digest):
                return True
    return False


def verify(directory, version, source, rids):
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version) or not re.fullmatch(r"[0-9a-f]{40}", source):
        raise ValueError("An exact stable version and source commit are required")
    for rid in rids:
        name = f"ChaptarrNG-{version}-{rid}." + ("zip" if rid.startswith("win-") else "tar.gz")
        archive = directory / name
        bundle = directory / (name + ".sigstore.json")
        if not archive.is_file() or not bundle.is_file() or not 0 < bundle.stat().st_size <= 4 * 1024 * 1024:
            raise ValueError("Missing archive or bounded signature bundle: " + name)
        with archive.open("rb") as stream:
            hasher = hashlib.sha256()
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                hasher.update(chunk)
            digest = hasher.hexdigest()
        checksum = (directory / (name + ".sha256")).read_text().strip().split()
        if checksum != [digest, name]:
            raise ValueError("Archive checksum or sidecar filename mismatch: " + name)
        with tempfile.TemporaryDirectory(prefix="chaptarr-release-verifier-") as config:
            env = {key: value for key, value in os.environ.items() if key not in ("GH_TOKEN", "GITHUB_TOKEN")}
            env.update(GH_HOST="github.com", GH_PROMPT_DISABLED="1", GH_CONFIG_DIR=config)
            result = subprocess.run([
                "gh", "attestation", "verify", str(archive.resolve()), "--bundle", str(bundle.resolve()),
                "--repo", "snapetech-org/chaptarrng",
                "--cert-identity", "https://github.com/snapetech-org/chaptarrng/.github/workflows/release.yml@refs/heads/main",
                "--source-ref", "refs/heads/main", "--deny-self-hosted-runners",
                "--predicate-type", PREDICATE, "--format", "json",
            ], env=env, text=True, capture_output=True, check=True, timeout=120)
        if not matches_release(json.loads(result.stdout), version, source, name, digest):
            raise ValueError("Signature does not bind the version, source, filename and archive digest: " + name)
        print("Verified updater signature: " + name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("version")
    parser.add_argument("source")
    parser.add_argument("--runtime-id", choices=RIDS)
    args = parser.parse_args()
    verify(args.directory, args.version, args.source, [args.runtime_id] if args.runtime_id else RIDS)
