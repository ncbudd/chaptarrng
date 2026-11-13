#!/usr/bin/env python3
"""Three-way merge the source inventory without discarding either branch's records."""
import argparse
import copy
import hashlib
import json
import subprocess
from pathlib import Path

PATH = "docs/localization/server-message-sources.json"
MISSING = object()

def sha(data):
    return hashlib.sha256(data).hexdigest()

def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])

def fail(message):
    raise SystemExit("FAIL: " + message)

def need(value, message):
    if not value:
        fail(message)

def records_by_id(data):
    result = {}
    for row in data["records"]:
        ident = row["id"]
        need(ident not in result, "duplicate source record " + ident)
        result[ident] = row
    return result

def changed_fields(before, after):
    return {key for key in set(before) | set(after) if before.get(key, MISSING) != after.get(key, MISSING)}

def callsite_signature(row):
    return sorted(
        (
            item.get("file"),
            item.get("sourceLine"),
            item.get("sourceLineSha256"),
            item.get("category"),
            item.get("surface"),
        )
        for item in row
    )

def load_commit_json(repo, revision):
    return json.loads(git(repo, "show", revision + ":" + PATH))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--pr-head", required=True)
    parser.add_argument("--main-head", required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    repo = args.repo.resolve()
    base = load_commit_json(repo, args.base)
    pr = load_commit_json(repo, args.pr_head)
    main = load_commit_json(repo, args.main_head)
    bmap, pmap, mmap = (records_by_id(x) for x in (base, pr, main))
    need(set(bmap) <= set(pmap), "PR branch removed source inventory records")
    need(set(bmap) == set(mmap), "latest main added or removed source IDs; manual review required")
    need(len(pmap) == 618 and len(mmap) == 554, "source record totals changed from attested branch/base")

    merged = copy.deepcopy(pr)
    merged_records = []
    conflict_records = []
    main_only_record_updates = []
    pr_only_record_updates = []
    for ident in [row["id"] for row in pr["records"]]:
        p = pmap[ident]
        m = mmap.get(ident)
        b = bmap.get(ident)
        if b is None:
            need(m is None or m == p, "new PR record collides with main record " + ident)
            merged_records.append(copy.deepcopy(p))
            continue
        if m is None:
            fail("main removed source record " + ident)
        result = copy.deepcopy(p)
        pf = changed_fields(b, p)
        mf = changed_fields(b, m)
        if pf and not mf:
            pr_only_record_updates.append(ident)
        if mf and not pf:
            main_only_record_updates.append(ident)
        for field in set(b) | set(p) | set(m):
            p_changed = p.get(field, MISSING) != b.get(field, MISSING)
            m_changed = m.get(field, MISSING) != b.get(field, MISSING)
            if not p_changed and m_changed:
                result[field] = copy.deepcopy(m[field])
            elif p_changed and not m_changed:
                pass
            elif p_changed and m_changed:
                if p.get(field, MISSING) == m.get(field, MISSING):
                    if field in p:
                        result[field] = copy.deepcopy(p[field])
                    else:
                        result.pop(field, None)
                elif field == "callsites" and callsite_signature(p[field]) == callsite_signature(m[field]):
                    result[field] = copy.deepcopy(m[field])
                    conflict_records.append({
                        "id": ident,
                        "field": field,
                        "resolution": "use latest-main callsite locations; file, source line, source-line hash, category, and surface match the PR side",
                        "prCallsiteLines": sorted(x["line"] for x in p[field]),
                        "mainCallsiteLines": sorted(x["line"] for x in m[field]),
                    })
                else:
                    fail("unreviewed same-field conflict in " + ident + ":" + field)
        merged_records.append(result)
    merged["records"] = merged_records

    # Merge remaining top-level fields with ordinary three-way semantics.
    for field in set(base) | set(pr) | set(main):
        if field == "records":
            continue
        b = base.get(field, MISSING)
        p = pr.get(field, MISSING)
        m = main.get(field, MISSING)
        p_changed = p != b
        m_changed = m != b
        if not p_changed and m_changed:
            merged[field] = copy.deepcopy(m)
        elif p_changed and not m_changed:
            pass
        elif p_changed and m_changed:
            if p == m:
                if p is MISSING:
                    merged.pop(field, None)
                else:
                    merged[field] = copy.deepcopy(p)
            elif field == "sourceExtensions" and isinstance(p, list) and isinstance(m, list):
                merged[field] = copy.deepcopy(p)
                for value in m:
                    if value not in merged[field]:
                        merged[field].append(copy.deepcopy(value))
            else:
                fail("unreviewed top-level conflict: " + field)

    need(len(merged["records"]) == 618 and len(merged["sourceExtensions"]) == 4,
         "merged inventory lost PR extensions/records")
    merged_raw = (json.dumps(merged, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    parsed = json.loads(merged_raw)
    need(len(records_by_id(parsed)) == 618, "merged record uniqueness")
    # The four simultaneous callsite edits only renumbered unchanged source lines.
    source_line_checks = []
    for conflict in conflict_records:
        row = pmap[conflict["id"]]
        for callsite in mmap[conflict["id"]]["callsites"]:
            source_raw = git(repo, "show", args.main_head + ":" + callsite["file"])
            lines = source_raw.decode("utf-8").splitlines()
            actual_source_line = lines[callsite["line"] - 1].strip() if 1 <= callsite["line"] <= len(lines) else ""
            need(actual_source_line == callsite["sourceLine"] and sha(actual_source_line.encode("utf-8")) == callsite["sourceLineSha256"],
                 "latest-main source line pin is stale for " + conflict["id"])
            source_line_checks.append({"id": conflict["id"], "file": callsite["file"], "line": callsite["line"], "sourceLineSha256": callsite["sourceLineSha256"], "matches": True})

    if not args.dry_run:
        path = repo / PATH
        path.write_bytes(merged_raw)

    report = {
        "result": "PASS",
        "path": PATH,
        "base": args.base,
        "prHead": args.pr_head,
        "latestMain": args.main_head,
        "baseRecords": len(bmap),
        "prRecords": len(pmap),
        "mainRecords": len(mmap),
        "mergedRecords": len(merged_records),
        "prOnlyAddedRecordCount": len(set(pmap) - set(bmap)),
        "mainOnlyAddedRecordCount": len(set(mmap) - set(bmap)),
        "prOnlyChangedExistingRecordCount": len(pr_only_record_updates),
        "mainOnlyChangedExistingRecordCount": len(main_only_record_updates),
        "sameFieldConflicts": conflict_records,
        "resolvedByKeepingMainCallsites": len(conflict_records),
        "sourceExtensions": len(merged["sourceExtensions"]),
        "sourceLineChecks": source_line_checks,
        "mergedBytes": len(merged_raw),
        "mergedSha256": sha(merged_raw),
        "policy": "Preserve PR-only server source records and extensions; adopt main-only updates to existing records; for four overlapping callsite-only updates, preserve the latest-main file/line while checking its exact source line and hash. Any other same-field conflict fails closed.",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("result", "baseRecords", "prRecords", "mainRecords", "mergedRecords", "prOnlyAddedRecordCount", "mainOnlyChangedExistingRecordCount", "resolvedByKeepingMainCallsites", "mergedSha256")}, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    main()

