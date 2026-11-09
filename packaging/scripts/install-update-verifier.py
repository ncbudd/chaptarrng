#!/usr/bin/env python3
"""Bundle a checksum-pinned GitHub CLI for offline Sigstore bundle verification."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import urllib.request
import zipfile


def install(rid, output):
    platforms = {
        "linux-x64": "linux_amd64", "linux-arm64": "linux_arm64",
        "linux-arm": "linux_armv6", "linux-x86": "linux_386",
        "linux-musl-x64": "linux_amd64", "linux-musl-arm64": "linux_arm64",
        "osx-x64": "macOS_amd64", "osx-arm64": "macOS_arm64",
        "win-x64": "windows_amd64", "win-x86": "windows_386",
    }
    if rid == "freebsd-x64":
        # Upstream ships no FreeBSD binary. The native port supplies gh; verification
        # fails closed if it is missing or too old. Never run a Linux binary here.
        print("FreeBSD automatic updates require the native gh package with attestation support.")
        return
    platform = platforms[rid]
    manifest = json.loads((Path(__file__).resolve().parents[2] / "security/gh-verifier-assets.json").read_text())
    suffix = "zip" if platform.startswith(("windows", "macOS")) else "tar.gz"
    asset = f"gh_{manifest['version']}_{platform}.{suffix}"
    url = f"https://github.com/cli/cli/releases/download/v{manifest['version']}/{asset}"
    # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected -- The HTTPS origin is fixed to cli/cli; the platform is allowlisted and the version/hash come from a committed manifest, not application input.
    with urllib.request.urlopen(url, timeout=60) as response:
        payload = response.read(128 * 1024 * 1024 + 1)
    if len(payload) > 128 * 1024 * 1024 or hashlib.sha256(payload).hexdigest() != manifest["sha256"][asset]:
        raise ValueError("GitHub CLI archive failed its pinned size/hash check")
    binary = "gh.exe" if platform.startswith("windows") else "gh"
    # Read only the expected regular file, never extract archive paths onto disk.
    with (zipfile.ZipFile(io.BytesIO(payload)) if suffix == "zip" else tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz")) as archive:
        names = archive.namelist() if suffix == "zip" else archive.getnames()
        matches = [name for name in names if name.endswith("/bin/" + binary) or name == "bin/" + binary]
        if len(matches) != 1:
            raise ValueError("GitHub CLI archive must contain exactly one verifier")
        if suffix == "zip":
            data = archive.read(matches[0])
        else:
            member = archive.getmember(matches[0])
            if not member.isfile():
                raise ValueError("Verifier is not a regular file")
            data = archive.extractfile(member).read()
        license_names = [name for name in names if name.rsplit("/", 1)[-1] == "LICENSE"]
        if len(license_names) != 1:
            raise ValueError("GitHub CLI license is missing")
        license_data = archive.read(license_names[0]) if suffix == "zip" else archive.extractfile(license_names[0]).read()
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / binary).write_bytes(data)
    (destination / binary).chmod(0o755)
    (destination / "GitHub-CLI-LICENSE").write_bytes(license_data)


if __name__ == "__main__":
    install(*sys.argv[1:])
