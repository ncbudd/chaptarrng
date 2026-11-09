#!/usr/bin/env python3
"""Validate custom-RID restores against committed NuGet dependency versions/hashes.

Custom runtime packs are installed/qualified separately. Their SDK runtime graph
differs from the standard SDK, so NuGet cannot reuse its RID-keyed lockfile. All
ordinary NuGet packages must nevertheless match the committed dependency set.
"""
import json
from pathlib import Path
import sys


def verify(source, generated):
    baselines = {}
    for lock in Path(source).rglob("packages.lock.json"):
        projects = list(lock.parent.glob("*.csproj"))
        if len(projects) == 1:
            baselines[projects[0].stem] = lock
    files = list(Path(generated).glob("*.lock.json"))
    if not files:
        raise ValueError("Custom-platform restore produced no lockfiles")
    for actual in files:
        name = actual.name.removesuffix(".lock.json")
        if name not in baselines:
            raise ValueError(f"No committed dependency baseline for {name}")
        expected = json.loads(baselines[name].read_text())["dependencies"]
        permitted = set()
        for group in expected.values():
            for package, item in group.items():
                if item["type"].lower() != "project":
                    permitted.add((package.lower(), item.get("resolved"), item.get("contentHash")))
        for group in json.loads(actual.read_text())["dependencies"].values():
            for package, item in group.items():
                if item["type"].lower() == "project":
                    continue
                resolved = (package.lower(), item.get("resolved"), item.get("contentHash"))
                if resolved not in permitted:
                    raise ValueError(f"Unlocked custom-platform dependency in {name}: {package} {item.get('resolved')}")
    print(f"Validated {len(files)} custom-platform dependency locks against committed versions and hashes")


if __name__ == "__main__":
    verify(*sys.argv[1:])
