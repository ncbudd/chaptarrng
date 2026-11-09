#!/usr/bin/env python3
"""Materialize reviewed rule IDs privately; third-party rules are not redistributed.

The manifest pins both upstream Git commits and archive SHA-256 values. Downloads
are separate from parsing so untrusted PR scanning can run completely offline.
Parsing uses ruamel.yaml supplied by the pinned Semgrep installation/container.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import tarfile
import urllib.request


def prepare(output, download_only=False):
    manifest_path = Path(__file__).resolve().parents[1] / "security/semgrep-rules-source.json"
    manifest = json.loads(manifest_path.read_text())
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    rules = []
    if not download_only:
        from ruamel.yaml import YAML
        yaml = YAML(typ="safe")
    for source in manifest["sources"]:
        archive = output / (source["name"] + ".tar.gz")
        if not archive.exists() or hashlib.sha256(archive.read_bytes()).hexdigest() != source["sha256"]:
            if not download_only:
                raise ValueError("Pinned rule archive is missing or corrupt; fetch it before offline preparation")
            # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected -- Only immutable GitHub archive URLs from the trusted-base policy manifest are read; every archive is checked against its committed SHA-256.
            with urllib.request.urlopen(source["url"], timeout=60) as response:
                data = response.read(32 * 1024 * 1024 + 1)
            if len(data) > 32 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != source["sha256"]:
                raise ValueError("Upstream rule archive does not match the reviewed SHA-256")
            archive.write_bytes(data)
        if download_only:
            continue
        with tarfile.open(archive, "r:gz") as content:
            files = {
                str(PurePosixPath(*PurePosixPath(member.name).parts[1:])): member
                for member in content.getmembers() if member.isfile()
            }
            parsed = {}
            for canonical, selected in source["rules"].items():
                path = selected["file"]
                if path not in parsed:
                    parsed[path] = yaml.load(content.extractfile(files[path]))["rules"]
                matches = [rule for rule in parsed[path] if rule["id"] == selected["id"]]
                if len(matches) != 1:
                    raise ValueError("Pinned source must contain exactly one selected rule: " + canonical)
                rule = dict(matches[0])
                rule["id"] = canonical
                rule["metadata"] = dict(rule.get("metadata", {}), chaptarr_modification_notice="Rule ID normalized to its reviewed registry ID for local scanning; rule logic unchanged.")
                rules.append(rule)
            for name, member in files.items():
                if PurePosixPath(name).name.upper().startswith(("LICENSE", "COPYING")):
                    target = output / (source["name"] + "-" + name.replace("/", "-"))
                    target.write_bytes(content.extractfile(member).read())
    if not download_only:
        if len(rules) != manifest["rules"]:
            raise ValueError("Pinned rule selection is incomplete")
        (output / "rules.json").write_text(json.dumps({"rules": rules}, default=str))
        print(f"Prepared {len(rules)} pinned rules for internal scanning")


if __name__ == "__main__":
    prepare(sys.argv[1], "--download-only" in sys.argv[2:])
