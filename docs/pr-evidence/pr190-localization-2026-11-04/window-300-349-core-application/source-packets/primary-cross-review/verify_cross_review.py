#!/usr/bin/env python3
import collections, hashlib, json, pathlib, re, subprocess, sys

OUT = pathlib.Path(__file__).resolve().parent
INPUT = pathlib.Path("/home/keith/Documents/code/task-scratch/chaptarrng-pr190-w300-349-core-20261104/candidate-free/input")
PROPOSALS = pathlib.Path("/home/keith/Documents/code/task-scratch/chaptarrng-pr190-w300-349-core-20261104/primary-review/primary-review-proposals.jsonl")
REPO = pathlib.Path("/mnt/disks/scratch/task-worktrees/localization-20261104/chaptarrng-pr190-w300-349-source")
EXPECTED_HEAD = "f0082d1b655c05b8d4019ede523dd695cd6d745a"
EXPECTED_TREE = "4cf2322354e9cf9b12d59cf10d0d8661c68ab4af"

def sha(data): return hashlib.sha256(data).hexdigest()
def fail(msg): raise SystemExit("FAIL: " + msg)
def read_jsonl(path): return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
def parse_sums(path):
    values={}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        digest, name = line.split(None,1)
        values[name.strip()] = digest
    return values

def verify_sums(root, sums_path, expected_names=None):
    values=parse_sums(sums_path)
    if expected_names is not None and set(values) != set(expected_names): fail(f"checksum file set mismatch: {sums_path}")
    for name, expected in values.items():
        path=root/name
        if not path.is_file() or sha(path.read_bytes()) != expected: fail(f"checksum mismatch: {path}")
    return values

manifest=json.loads((OUT/"cross-review-manifest.json").read_text(encoding="utf-8"))
if manifest["source"]["head"] != EXPECTED_HEAD or manifest["source"]["tree"] != EXPECTED_TREE: fail("manifest source pin mismatch")
head=subprocess.check_output(["git","-C",str(REPO),"rev-parse","HEAD"],text=True).strip()
tree=subprocess.check_output(["git","-C",str(REPO),"rev-parse","HEAD^{tree}"],text=True).strip()
status=subprocess.check_output(["git","-C",str(REPO),"status","--porcelain"],text=True).strip()
if (head,tree,status)!=(EXPECTED_HEAD,EXPECTED_TREE,""): fail("source worktree is not exact and clean")
input_sums_path=INPUT/"SHA256SUMS.txt"
if sha(input_sums_path.read_bytes()) != manifest["inputs"]["candidateFreePacket"]["sha256SumsFileSha256"]: fail("candidate-free checksum index changed")
input_files=parse_sums(input_sums_path)
verify_sums(INPUT,input_sums_path)
if sha((INPUT/"candidate-free-cells.jsonl").read_bytes()) != manifest["inputs"]["candidateFreePacket"]["candidateCellsSha256"]: fail("candidate-free cells hash mismatch")
if sha(PROPOSALS.read_bytes()) != manifest["inputs"]["primaryProposalsOnly"]["sha256"]: fail("primary proposals hash mismatch")
proposals=read_jsonl(PROPOSALS)
candidates=read_jsonl(INPUT/"candidate-free-cells.jsonl")
callers={r["sourceKey"]:r for r in read_jsonl(INPUT/"caller-context.jsonl")}
if len(proposals)!=87 or len(candidates)!=600: fail("input row count mismatch")
proposal_by_id={r["cellId"]:r for r in proposals}
candidate_by_cell={(r["sourceKey"],r["locale"]):r for r in candidates}
rows=read_jsonl(OUT/"cross-review-decisions.jsonl")
if len(rows)!=87 or len({r["cellId"] for r in rows})!=87: fail("cross-review ledger row count or uniqueness mismatch")
placeholder=lambda s: collections.Counter(re.findall(r"\{[^{}]+\}",s))
markup=lambda s: collections.Counter(re.findall(r"</?[A-Za-z][^>]*>",s))
inline=lambda s: collections.Counter(re.findall(r"`[^`]*`",s))
numeric=lambda s: collections.Counter(re.findall(r"(?<!\w)\d+(?:[.,]\d+)?(?!\w)",s))
for row in rows:
    p=proposal_by_id.get(row["cellId"])
    c=candidate_by_cell.get((row["sourceKey"],row["locale"]))
    if p is None or c is None: fail(f"missing proposal/candidate row: {row['cellId']}")
    if (p["sourceText"],p["currentTarget"],p["recommendedTarget"]) != (c["sourceText"],c["currentTarget"],row["proposedTarget"]): fail(f"text join mismatch: {row['cellId']}")
    if p["candidateFreeRowSha256"] != sha(json.dumps(c,ensure_ascii=False,separators=(",",":")).encode("utf-8")): fail(f"candidate-row hash mismatch: {row['cellId']}")
    if row["sourceTextSha256"] != sha(c["sourceText"].encode()) or row["currentTargetSha256"] != sha(c["currentTarget"].encode()) or row["proposedTargetSha256"] != sha(p["recommendedTarget"].encode()): fail(f"input text hash mismatch: {row['cellId']}")
    if row["callerContextSha256"] != c["callerContextSha256"] or row["callerContextSha256"] != callers[row["sourceKey"]]["callerContextSha256"]: fail(f"caller context hash mismatch: {row['cellId']}")
    target=row["reviewerTarget"]
    if sha(target.encode("utf-8")) != row["reviewerTargetSha256"]: fail(f"reviewer target hash mismatch: {row['cellId']}")
    actual={"placeholder":placeholder(c["sourceText"])==placeholder(target),"markup":markup(c["sourceText"])==markup(target),"inlineCode":inline(c["sourceText"])==inline(target),"numericToken":numeric(c["sourceText"])==numeric(target),"protectedLiteral":all(x in target for x in c.get("protectedLiterals",[]) if x)}
    if actual != row["structuralChecks"] or not all(actual.values()): fail(f"structural check mismatch: {row['cellId']}")
    if row["decision"] not in {"accept","revise","hold"}: fail(f"unknown decision: {row['cellId']}")
    if row["decision"]=="accept" and target != p["recommendedTarget"]: fail(f"accepted target differs: {row['cellId']}")
    if row["decision"]=="revise" and target == p["recommendedTarget"]: fail(f"revision did not change target: {row['cellId']}")
    expected_refs=[]
    for ref in callers[row["sourceKey"]].get("callerRefs",[]):
        if ref.get("isRuntimeReference") and ref.get("path","").startswith("frontend/"):
            expected_refs.append({"path":ref["path"],"line":ref["line"],"lineText":ref["lineText"]})
    if not expected_refs:
        expected_refs=[{"path":ref["path"],"line":ref["line"],"lineText":ref["lineText"]} for ref in callers[row["sourceKey"]].get("callerRefs",[])[:5]]
    if row["contextRefs"] != expected_refs[:5]: fail(f"caller refs mismatch: {row['cellId']}")
if len(set(r["cellId"] for r in rows)^set(proposal_by_id))!=0: fail("proposal and cross-review cell sets differ")
counts=dict(collections.Counter(r["decision"] for r in rows))
summary=json.loads((OUT/"cross-review-summary.json").read_text(encoding="utf-8"))
if summary["decisions"]!=counts or counts!={"accept":86,"revise":1}: fail(f"decision count mismatch: {counts}")
expected_output={p.name for p in OUT.iterdir() if p.is_file() and p.name!="SHA256SUMS.txt"}
verify_sums(OUT,OUT/"SHA256SUMS.txt",expected_output)
print(json.dumps({"result":"PASS","head":head,"tree":tree,"candidateFiles":len(input_files),"candidateRows":len(candidates),"primaryProposalRows":len(proposals),"crossReviewRows":len(rows),"decisions":counts,"outputFiles":len(expected_output)}))
