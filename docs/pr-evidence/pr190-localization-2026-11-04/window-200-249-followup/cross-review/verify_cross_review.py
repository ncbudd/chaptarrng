#!/usr/bin/env python3
"""Verify the ChaptarrNG PR #190 W200-W249 cross-review packet and its sealed inputs."""
from __future__ import annotations
import argparse, collections, hashlib, json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parent
PRIMARY_ROOT = TASK / "chaptarrng-pr190-w200-249-primary-20261104"
BLIND_ROOT = TASK / "chaptarrng-pr190-w200-249-blind-20261104"
CANDIDATE = PRIMARY_ROOT / "candidate-free/input"
PRIMARY = PRIMARY_ROOT / "primary-review"
BLIND = BLIND_ROOT
HEAD = "dc91bdcdf60ba422bb176cc7c58b9b1cab27facd"
TREE = "ffae435c871360ba958098bc0398a1f251f8b1e8"
LOCALES = {"ar","de","es","fr","hi","id","ja","ko","pt-BR","vi","zh-Hans","zh-Hant"}
FORBIDDEN_HOLD_FIELDS = {"cellId","sourceKey","sourceText","currentTarget","primaryCandidate","blindCandidate","recommendedTarget","finalReviewedTarget"}
PH = re.compile(r"\{[^{}]+\}")
INLINE = re.compile(r"`([^`]+)`")
MARKUP = re.compile(r"<[^>]+>")
NUMBER = re.compile(r"(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])")

def fail(msg): raise SystemExit("FAIL: " + msg)
def need(ok, msg):
    if not ok: fail(msg)
def sha(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def sha_text(s: str) -> str: return sha(s.encode("utf-8"))
def row_sha(row) -> str: return sha(json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(",",":" )).encode("utf-8"))
def read_json(path): return json.loads(path.read_text(encoding="utf-8"))
def read_jsonl(path): return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
def signature(rx, s): return collections.Counter(rx.findall(s))
def verify_sums(path):
    entries={}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest,name=line.split("  ",1)
        target=(path.parent/name).resolve()
        need(target.is_relative_to(path.parent.resolve()) and target.is_file(), "unsafe or missing checksum path: "+name)
        need(sha(target.read_bytes())==digest,"checksum mismatch: "+name)
        entries[name]=digest
    actual={p.name for p in path.parent.iterdir() if p.is_file() and p.name!=path.name}
    need(set(entries)==actual,"checksum coverage mismatch: "+str(path))
    return entries

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-worktree",type=Path,default=Path("/mnt/disks/scratch/task-worktrees/localization-20261104/chaptarrng-pr190-w200-249-source"))
    args=ap.parse_args()
    repo=args.source_worktree.resolve()
    need(repo.is_dir(),"source worktree missing")
    need(subprocess.check_output(["git","-C",str(repo),"rev-parse","HEAD"],text=True).strip()==HEAD,"source worktree head mismatch")
    need(subprocess.check_output(["git","-C",str(repo),"show","-s","--format=%T",HEAD],text=True).strip()==TREE,"source worktree tree mismatch")
    need(not subprocess.check_output(["git","-C",str(repo),"status","--porcelain=v1"],text=True).strip(),"source worktree is dirty")

    verify_sums(HERE/"SHA256SUMS.txt")
    verify_sums(CANDIDATE/"SHA256SUMS.txt")
    verify_sums(PRIMARY/"primary-review-SHA256SUMS.txt")
    verify_sums(BLIND/"SHA256SUMS.txt")
    run=lambda argv: subprocess.run(argv,capture_output=True,text=True)
    checks=[
        [sys.executable,str(CANDIDATE/"verify_candidate_free.py"),"--source-worktree",str(repo)],
        [sys.executable,str(PRIMARY/"verify_primary_review.py"),"--source-worktree",str(repo)],
        [sys.executable,str(BLIND/"verify_blind_review.py"),"--candidate-free-input",str(CANDIDATE)],
    ]
    for name,argv in zip(("candidate-free","primary","blind"),checks):
        p=run(argv); need(p.returncode==0,f"{name} verifier failed: {p.stdout}{p.stderr}")

    att=read_json(HERE/"live-pr-attestation.json")
    drift=read_json(HERE/"base-drift-comparison.json")
    need(att["repository"]=="snapetech-org/chaptarrng" and att["pullRequest"]==190,"PR identity")
    need(att["pr"]["state"]=="OPEN" and att["pr"]["draft"] is True,"PR state at recorded attestation")
    need(att["pr"]["headSha"]==att["branchApi"]["sha"]==att["pullRef"]["sha"]==HEAD,"live head refs")
    need(att["sourceWorktree"]["head"]==HEAD and att["sourceWorktree"]["tree"]==TREE and att["sourceWorktree"]["clean"] is True,"source pin attestation")
    need(att["currentMain"]==att["remoteHeads"]["refs/heads/main"],"main ref consistency")
    need(drift["apiBase"]==att["pr"]["baseSha"] and drift["currentMain"]==att["currentMain"],"base drift refs")
    need(drift["compareStatus"]=="ahead" and drift["aheadBy"]==8 and drift["containsLocalizationSourceOrCatalogChanges"] is False,"base drift reconciliation")
    need(att["pr"]["baseSha"]!=att["currentMain"] and att["apiBaseDiffersFromMain"] is True,"base drift recorded")

    candidate=read_jsonl(CANDIDATE/"candidate-free-cells.jsonl")
    primary=read_jsonl(PRIMARY/"primary-review-cells.jsonl")
    blind=read_jsonl(BLIND/"decisions.jsonl")
    pp={r["cellId"]:r for r in read_jsonl(PRIMARY/"primary-review-proposals.jsonl")}
    bp={r["sourceKey"]+"::"+r["locale"]:r for r in read_jsonl(BLIND/"proposals.jsonl")}
    rows=read_jsonl(HERE/"cross-review-cells.jsonl")
    changes=read_jsonl(HERE/"selected-changes.jsonl")
    summary=read_json(HERE/"cross-review-summary.json")
    selections=read_json(HERE/"review-selections.json")
    need(len(candidate)==len(primary)==len(blind)==len(rows)==600,"input/output row totals")
    need(len(pp)==96 and len(bp)==34 and len(changes)==99,"proposal totals")
    cmap={(r["sourceOrdinal"],r["locale"]):r for r in candidate}
    pmap={(r["sourceOrdinal"],r["locale"]):r for r in primary}
    bmap={(r["sourceOrdinal"],r["locale"]):r for r in blind}
    rmap={(r["sourceOrdinal"],r["locale"]):r for r in rows}
    xmap={r["cellId"]:r for r in changes}
    need(len(rmap)==600 and len(xmap)==99,"unique row identities")
    counts=collections.Counter(r["crossDisposition"] for r in rows)
    need(counts=={"accept-current":489,"propose-change":99,"hold-text-free":12},"cross dispositions")
    need(summary["head"]==HEAD and summary["tree"]==TREE and summary["baseDiffersFromLiveMain"] is True,"summary pin")
    need(summary["baseDriftReconciliation"]["verifiedBy"].endswith(drift["verifiedAtUTC"]),"summary drift timestamp")
    need(summary["recommendationsOnly"] is True and summary["appliedToCatalogs"] is False and summary["repositoryOrPRChanged"] is False and summary["testsBuildsCI"]=="not run","scope declaration")
    need(summary["candidateFreeManifestSha256"]==sha((CANDIDATE/"candidate-free-manifest.json").read_bytes()),"candidate-free manifest linkage")

    by_cell={}
    for c in candidate:
        ident=(c["sourceOrdinal"],c["locale"]); cid=c["sourceKey"]+"::"+c["locale"]
        p=pmap[ident]; b=bmap[ident]; r=rmap[ident]
        need(c["sourceOrdinal"] in range(200,250) and c["locale"] in LOCALES,"scope cell")
        need(r["exactHead"]==HEAD and r["exactTree"]==TREE and r["cellIdSha256"]==sha_text(cid) if r["crossDisposition"]=="hold-text-free" else r["cellId"]==cid,"cell identity/pin")
        need(r["candidateFreeRowSha256"]==row_sha(c) and r["primaryReviewRowSha256"]==row_sha(p) and r["blindReviewRowSha256"]==row_sha(b),"review lineage hashes")
        need(p["candidateFreeRowSha256"]==row_sha(c),"primary candidate-free linkage")
        if c["callerReferenceCount"]==0:
            need(c["sourceKey"]=="AuthorsLabel" and p["primaryDisposition"] in ("hold","hold-text-free") and b["decision"]=="hash-only-hold","callerless input disposition")
            need(r["crossDisposition"]=="hold-text-free" and r["callerReferenceCount"]==0 and r["nativeSpeakerReviewOutstanding"] is True,"callerless cross hold")
            need(not (FORBIDDEN_HOLD_FIELDS & set(r)),"callerless hold contains text")
            need(r["sourceOrdinal"]==227 and r["sourceTextSha256"]==c["sourceTextSha256"] and r["currentTargetSha256"]==c["currentTargetSha256"],"callerless text hashes")
            continue
        need(r["sourceKey"]==c["sourceKey"] and r["locale"]==c["locale"] and r["sourceText"]==c["sourceText"] and r["currentTarget"]==c["currentTarget"],"source/current context linkage")
        chosen=r.get("recommendedTarget",r.get("finalReviewedTarget"))
        need(isinstance(chosen,str),"missing reviewed target")
        need(r.get("recommendedTargetSha256",r.get("finalReviewedTargetSha256"))==sha_text(chosen),"selected target hash")
        need(signature(PH,chosen)==signature(PH,c["sourceText"]),"placeholder parity")
        need(signature(INLINE,chosen)==signature(INLINE,c["sourceText"]),"inline-code parity")
        need(signature(MARKUP,chosen)==signature(MARKUP,c["sourceText"]),"markup parity")
        src_numbers=collections.Counter(NUMBER.findall(c["sourceText"]))
        out_numbers=collections.Counter(NUMBER.findall(chosen))
        ja_one=(c["sourceOrdinal"],c["locale"]) in {(233,"ja"),(235,"ja")} and "one root folder" in c["sourceText"] and NUMBER.findall(chosen)==["1"]
        need(src_numbers==out_numbers or ja_one,"numeric token parity")
        for literal in c.get("protectedLiterals",[]): need(literal in chosen,"protected literal preservation")
        need(r["nativeSpeakerApproval"] is False and r["nativeSpeakerReviewOutstanding"] is True,"native-review status")
        if r["crossDisposition"]=="propose-change":
            need(chosen!=c["currentTarget"] and xmap.get(cid) is not None,"proposal result linkage")
            x=xmap[cid]
            for k in ("sourceTextSha256","currentTargetSha256","recommendedTarget","recommendedTargetSha256","selectedFrom","crossRationale","callerContextSha256","candidateFreeRowSha256","primaryReviewRowSha256","blindReviewRowSha256","exactHead","exactTree"):
                need(x.get(k)==r.get(k),"selected-change linkage: "+k)
            need(bool(r.get("primaryCandidate") or r.get("blindCandidate")),"proposal has no upstream candidate")
            by_cell[cid]=r
        else:
            need(chosen==c["currentTarget"] and cid not in xmap,"accepted-current target")
    need(set(xmap)==set(by_cell),"change rows cover all and only proposed cells")
    need(summary["dispositions"]==dict(counts) and summary["selectedChangeCells"]==99 and summary["uniqueProposalCellsCrossReviewed"]==99,"summary totals")
    need(0 < len(selections["rationalesByOrdinal"]) <= 50 and all(200 <= int(o) < 250 for o in selections["rationalesByOrdinal"]) and len(selections["customTargets"])==3,"adjudication map structure")
    print(json.dumps({"result":"PASS","head":HEAD,"tree":TREE,"cells":600,"changes":99,"acceptCurrent":489,"textFreeHolds":12,"baseDriftCommits":8,"sealedInputVerifiers":"PASS"},sort_keys=True))

if __name__=="__main__": main()
