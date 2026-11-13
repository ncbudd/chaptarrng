#!/usr/bin/env python3
"""Build a checksum-pinned GitHub CLI for Sigstore bundle verification."""
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile


MAX_SOURCE_ARCHIVE_SIZE = 128 * 1024 * 1024


def read_manifest():
    path = Path(__file__).resolve().parents[2] / "security/gh-verifier-assets.json"
    manifest = json.loads(path.read_text())
    required = (
        "version", "source_commit", "source_sha256", "go_version",
        "golang_x_net", "golang_x_net_sum",
    )
    if any(not manifest.get(key) for key in required):
        raise ValueError("GitHub CLI verifier source manifest is incomplete")
    return manifest


def download_source(manifest):
    commit = manifest["source_commit"]
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("GitHub CLI source commit is invalid")
    curl = shutil.which("curl")
    if not curl:
        raise RuntimeError("curl is required to download the pinned GitHub CLI source archive")
    url = f"https://codeload.github.com/cli/cli/tar.gz/{commit}"
    with tempfile.TemporaryDirectory(prefix="chaptarrng-gh-source-") as work:
        archive_path = Path(work) / "gh-source.tar.gz"
        subprocess.run(
            [
                curl,
                "--fail",
                "--silent",
                "--show-error",
                "--location",
                "--proto",
                "=https",
                "--proto-redir",
                "=https",
                "--max-redirs",
                "3",
                "--max-time",
                "60",
                "--max-filesize",
                str(MAX_SOURCE_ARCHIVE_SIZE),
                "--output",
                str(archive_path),
                url,
            ],
            check=True,
        )
        payload = archive_path.read_bytes()
    if len(payload) > MAX_SOURCE_ARCHIVE_SIZE:
        raise ValueError("GitHub CLI source archive exceeds the size limit")
    if hashlib.sha256(payload).hexdigest() != manifest["source_sha256"]:
        raise ValueError("GitHub CLI source archive failed its pinned SHA-256 check")
    return payload


def extract_source(payload, destination, commit):
    expected_root = f"cli-{commit}"
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
        members = archive.getmembers()
        if not members:
            raise ValueError("GitHub CLI source archive is empty")
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != expected_root:
                raise ValueError("GitHub CLI source archive contains an unsafe path")
            if not (member.isdir() or member.isfile()):
                raise ValueError("GitHub CLI source archive contains a non-regular entry")
        archive.extractall(destination, members=members)
    source = Path(destination) / expected_root
    if not (source / "go.mod").is_file() or not (source / "LICENSE").is_file():
        raise ValueError("GitHub CLI source archive is missing required files")
    return source


def require_go(version):
    go = shutil.which("go")
    if not go:
        raise RuntimeError(f"Go {version} is required to build the pinned update verifier")
    output = subprocess.check_output([go, "version"], text=True).strip()
    if not re.search(r"\bgo" + re.escape(version) + r"(?:\b|-)", output):
        raise RuntimeError(f"Expected Go {version}; found {output}")
    return go, output


def build(rid, output):
    targets = {
        "linux-x64": ("linux", "amd64", ""),
        "linux-arm64": ("linux", "arm64", ""),
        "linux-arm": ("linux", "arm", "6"),
        "linux-x86": ("linux", "386", ""),
        "linux-musl-x64": ("linux", "amd64", ""),
        "linux-musl-arm64": ("linux", "arm64", ""),
        "osx-x64": ("darwin", "amd64", ""),
        "osx-arm64": ("darwin", "arm64", ""),
        "win-x64": ("windows", "amd64", ""),
        "win-x86": ("windows", "386", ""),
        "win-arm64": ("windows", "arm64", ""),
    }
    if rid == "freebsd-x64":
        print("FreeBSD automatic updates require the native gh package with attestation support.")
        return
    if rid not in targets:
        raise ValueError(f"Unsupported GitHub CLI verifier RID: {rid}")

    manifest = read_manifest()
    go, go_info = require_go(manifest["go_version"])
    payload = download_source(manifest)
    goos, goarch, goarm = targets[rid]
    filename = "gh.exe" if goos == "windows" else "gh"
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="chaptarrng-gh-verifier-") as work:
        source = extract_source(payload, work, manifest["source_commit"])
        subprocess.run(
            [go, "get", f"golang.org/x/net@{manifest['golang_x_net']}"],
            cwd=source,
            check=True,
        )
        expected_sum = f"golang.org/x/net {manifest['golang_x_net']} h1:{manifest['golang_x_net_sum']}"
        if expected_sum not in (source / "go.sum").read_text(encoding="utf-8").splitlines():
            raise RuntimeError("The patched GitHub CLI dependency failed its pinned Go checksum check")
        selected = subprocess.check_output(
            [go, "list", "-m", "golang.org/x/net"], cwd=source, text=True
        ).strip().split()
        if len(selected) != 2 or selected[1] != manifest["golang_x_net"]:
            raise RuntimeError("The patched GitHub CLI dependency graph did not select the pinned golang.org/x/net")

        binary = Path(work) / filename
        env = os.environ.copy()
        env.update({"GOOS": goos, "GOARCH": goarch, "CGO_ENABLED": "0", "GOTOOLCHAIN": "local"})
        if goarm:
            env["GOARM"] = goarm
        else:
            env.pop("GOARM", None)
        version = manifest["version"]
        ldflags = (
            f"-X github.com/cli/cli/v2/internal/build.Version={version} "
            "-X github.com/cli/cli/v2/internal/build.Date=2026-10-26"
        )
        subprocess.run(
            [go, "build", "-trimpath", "-buildvcs=false", "-ldflags", ldflags, "-o", str(binary), "./cmd/gh"],
            cwd=source,
            env=env,
            check=True,
        )
        shutil.copyfile(binary, destination / filename)
        (destination / filename).chmod(0o755)
        shutil.copyfile(source / "LICENSE", destination / "GitHub-CLI-LICENSE")

    binary_hash = hashlib.sha256((destination / filename).read_bytes()).hexdigest()
    build_info = (
        f"GitHub CLI version: {manifest['version']}\n"
        f"Source commit: {manifest['source_commit']}\n"
        f"Source archive SHA-256: {manifest['source_sha256']}\n"
        f"Go toolchain: {go_info}\n"
        f"golang.org/x/net: {manifest['golang_x_net']}\n"
        f"golang.org/x/net checksum: h1:{manifest['golang_x_net_sum']}\n"
        f"Target: {goos}/{goarch}{('/v' + goarm) if goarm else ''}\n"
        f"Binary SHA-256: {binary_hash}\n"
    )
    (destination / "GitHub-CLI-BUILD-INFO.txt").write_text(build_info, encoding="utf-8")
    print(f"Built patched GitHub CLI {manifest['version']} for {rid} ({binary_hash})")


if __name__ == "__main__":
    build(*sys.argv[1:])
