#!/usr/bin/env python3
"""Refresh the PR localization inventory against the merged ChaptarrNG source tree."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
INVENTORY = REPO / "docs/localization/server-message-sources.json"
RUNTIME = REPO / "frontend/src/Utilities/Localization/server-messages.json"
ENGLISH = REPO / "src/NzbDrone.Core/Localization/Core/en.json"
PR_INVENTORY = HERE / "pr-server-message-sources-before.json"
MAIN_INVENTORY = HERE / "main-server-message-sources.json"
PIN = HERE / "main-inventory-pin.json"
REPORT = HERE / "inventory-refresh-report.json"


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def source_fragments(record: dict[str, Any]) -> list[str]:
    values = [record.get("source", "")]
    values.extend(record.get("sourceTemplates", []))
    values.extend(record.get("patterns", []))
    fragments: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        for part in re.split(r"\{[^{}]*\}", value):
            part = part.strip()
            if len(part) >= 12:
                fragments.add(part)
    return sorted(fragments, key=lambda value: (-len(value), value))


def is_production_line(line: str) -> bool:
    value = line.strip()
    return bool(value) and not value.startswith(("//", "/*", "*", "///"))


def callsite_key(callsite: dict[str, Any]) -> tuple[str, int, str]:
    return callsite["file"], callsite["line"], callsite["sourceLineSha256"]


def locate_callsite(
    callsite: dict[str, Any],
    message_id: str,
    fragments: list[str],
    used_lines: set[tuple[str, int]],
) -> dict[str, Any] | None:
    relative = callsite["file"]
    source_file = REPO / relative
    if not source_file.is_file():
        return None
    lines = source_file.read_text(encoding="utf-8").splitlines()
    source_line = callsite["sourceLine"]
    exact = [
        (number, line.strip())
        for number, line in enumerate(lines, 1)
        if line.strip() == source_line and is_production_line(line)
    ]
    candidates = exact
    if not candidates:
        by_id = [
            (number, line.strip())
            for number, line in enumerate(lines, 1)
            if message_id in line and is_production_line(line)
        ]
        candidates = by_id
    if not candidates:
        matching_fragments = [
            fragment for fragment in fragments
            if any(fragment in line for line in lines)
        ]
        if matching_fragments:
            longest = max(map(len, matching_fragments))
            selected_fragments = {fragment for fragment in matching_fragments if len(fragment) == longest}
            candidates = [
                (number, line.strip())
                for number, line in enumerate(lines, 1)
                if is_production_line(line) and any(fragment in line for fragment in selected_fragments)
            ]
    if not candidates:
        return None
    unused = [candidate for candidate in candidates if (relative, candidate[0]) not in used_lines]
    pool = unused or candidates
    number, current_line = min(pool, key=lambda candidate: (abs(candidate[0] - callsite["line"]), candidate[0]))
    used_lines.add((relative, number))
    return {
        **callsite,
        "line": number,
        "sourceLine": current_line,
        "sourceLineSha256": sha(current_line),
    }


def main() -> None:
    inventory = read_json(PR_INVENTORY)
    main_inventory = read_json(MAIN_INVENTORY)
    english = read_json(ENGLISH)
    pin = read_json(PIN)
    before_records = {row["id"]: dict(row) for row in inventory["records"]}
    main_records = {row["id"]: row for row in main_inventory["records"]}
    if set(main_records) - set(before_records):
        raise SystemExit("main contains source IDs absent from the PR inventory; audit additions before proceeding")

    source_updates: list[dict[str, str]] = []
    callsite_changes: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    added_main_callsite_ids: set[str] = set()
    added_main_callsite_keys: set[tuple[str, str, int, str]] = set()
    binding_delta = 0

    for record in inventory["records"]:
        message_id = record["id"]
        if message_id in english and english[message_id] != record["source"]:
            old_source = record["source"]
            new_source = english[message_id]
            source_updates.append({"id": message_id, "before": old_source, "after": new_source})
            record["source"] = new_source
            record["patterns"] = [new_source]
            record["sourceTemplates"] = [new_source]
            record["sourceFingerprint"] = sha(f"{message_id}\0{new_source}")

        old_callsites = list(record.get("callsites", []))
        main_callsites = list(main_records.get(message_id, {}).get("callsites", []))
        fragments = source_fragments(record)
        if message_id in before_records:
            fragments = sorted(
                set(fragments + source_fragments(before_records[message_id])),
                key=lambda value: (-len(value), value),
            )
        used_lines: set[tuple[str, int]] = set()
        pr_callsites: list[dict[str, Any]] = []
        main_refreshed: list[dict[str, Any]] = []
        for callsite in old_callsites:
            updated = locate_callsite(callsite, message_id, fragments, used_lines)
            if updated is None:
                unresolved.append({
                    "id": message_id,
                    "file": callsite["file"],
                    "reason": "PR callsite no longer resolves by exact line, ID, or source text",
                    "priorLine": callsite["line"],
                    "priorSourceLine": callsite["sourceLine"],
                })
            else:
                pr_callsites.append(updated)
        for callsite in main_callsites:
            updated = locate_callsite(callsite, message_id, fragments, used_lines)
            if updated is None:
                continue
            main_refreshed.append(updated)
            if callsite_key(updated) not in {callsite_key(row) for row in pr_callsites}:
                added_main_callsite_ids.add(message_id)
                added_main_callsite_keys.add((message_id, *callsite_key(updated)))

        deduped: dict[tuple[str, int, str], dict[str, Any]] = {}
        for callsite in pr_callsites + main_refreshed:
            deduped[callsite_key(callsite)] = callsite
        new_callsites = sorted(deduped.values(), key=lambda row: (row["file"], row["line"]))
        old_keys = {callsite_key(row) for row in old_callsites}
        new_keys = {callsite_key(row) for row in new_callsites}
        binding_delta += len(new_callsites) - len(old_callsites)
        if old_callsites != new_callsites:
            callsite_changes.append({
                "id": message_id,
                "beforeBindings": len(old_callsites),
                "afterBindings": len(new_callsites),
                "addedBindings": len(new_keys - old_keys),
                "removedBindings": len(old_keys - new_keys),
            })
        record["callsites"] = new_callsites

    for excluded in inventory["excluded"]:
        refreshed = []
        for callsite in excluded.get("callsites", []):
            path = REPO / callsite["file"]
            if not path.is_file():
                unresolved.append({"id": "excluded", "file": callsite["file"], "reason": "source file missing"})
                continue
            lines = path.read_text(encoding="utf-8").splitlines()
            matches = [(n, line.strip()) for n, line in enumerate(lines, 1) if line.strip() == callsite["sourceLine"]]
            if not matches:
                unresolved.append({
                    "id": "excluded",
                    "file": callsite["file"],
                    "reason": "excluded source line no longer matches",
                    "priorLine": callsite["line"],
                    "priorSourceLine": callsite["sourceLine"],
                })
                continue
            for number, text in matches:
                refreshed.append({
                    **callsite,
                    "line": number,
                    "sourceLine": text,
                    "sourceLineSha256": sha(text),
                })
        excluded["callsites"] = refreshed

    if unresolved:
        REPORT.write_text(json.dumps({
            "status": "BLOCKED",
            "unresolved": unresolved,
            "sourceUpdates": source_updates,
            "callsiteChangeCount": len(callsite_changes),
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise SystemExit(f"unresolved source callsites: {len(unresolved)}; see {REPORT}")

    records = inventory["records"]
    excluded_count = sum(len(record.get("callsites", [])) for record in inventory["excluded"])
    unique_callsites = {
        (callsite["file"], callsite["line"], callsite["sourceLineSha256"])
        for record in records
        for callsite in record.get("callsites", [])
    }
    source_templates = {template for record in records for template in record.get("sourceTemplates", [])}
    inventory["counts"]["translatableMessages"] = len(records)
    inventory["counts"]["sourceBindings"] = sum(len(record.get("callsites", [])) for record in records)
    inventory["counts"]["sourceCallsites"] = len(unique_callsites)
    inventory["counts"]["sourceOccurrences"] = len(unique_callsites) + excluded_count
    inventory["counts"]["excludedTemplates"] = len(inventory["excluded"])
    inventory["counts"]["originalTemplates"] = len(source_templates) + len(inventory["excluded"])

    extension = {
        "id": "20261105-main-sync",
        "baseHead": pin["mainHead"],
        "newMessages": 0,
        "newSourceBindings": len(added_main_callsite_keys),
        "newUniqueCallsites": len(added_main_callsite_keys),
        "sourceIds": sorted(added_main_callsite_ids),
        "inputEvidence": {
            "file": "docs/pr-evidence/pr190-localization-2026-11-05/main-sync-2026-11-05/main-inventory-pin.json",
            "sha256": sha((HERE / "main-inventory-pin.json").read_text(encoding="utf-8").rstrip("\n")),
        },
        "method": "Reconciled PR-side source-bound localization wrappers with the merged main callsites, refreshed exact source-line hashes, and rechecked source changes against the English catalog. No new message IDs or target cells were generated.",
    }
    extensions = inventory.setdefault("sourceExtensions", [])
    if not any(item.get("id") == extension["id"] for item in extensions):
        extensions.append(extension)

    runtime = [
        {
            "id": record["id"],
            "source": record["source"],
            "parameters": record["parameters"],
            "patterns": record["patterns"],
            **({"explicitOnly": record["explicitOnly"]} if record.get("explicitOnly") else {}),
        }
        for record in records
    ]
    INVENTORY.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    RUNTIME.write_text(json.dumps(runtime, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {
        "status": "PASS",
        "repository": "snapetech-org/chaptarrng",
        "pr": 190,
        "baseHead": pin["baseHead"],
        "preMergeHead": pin["pullHeadBeforeMerge"],
        "mainHead": pin["mainHead"],
        "sourceRecords": len(records),
        "sourceUpdatesFromEnglishCatalog": source_updates,
        "updatedRecordsWithCallsiteChanges": len(callsite_changes),
        "sourceBindingDelta": binding_delta,
        "newMainCallsiteRecordIds": sorted(added_main_callsite_ids),
        "uniqueCallsites": len(unique_callsites),
        "excludedCallsites": excluded_count,
        "catalogTargetsChanged": 0,
        "runtimeRegistryRefreshed": True,
        "unresolved": [],
        "callsiteChanges": callsite_changes,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "callsiteChanges"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
