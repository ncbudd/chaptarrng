#!/usr/bin/env python3
import hashlib,json,re,subprocess
from collections import Counter
from pathlib import Path
p=Path(__file__).resolve().parent; inp=Path("/home/keith/Documents/code/task-scratch/chaptarrng-pr190-w1187-m4b-candidate-free-20261103")
subprocess.check_call(["sha256sum","-c","SHA256SUMS.txt"],cwd=inp,stdout=subprocess.DEVNULL);subprocess.check_call(["python3","verify_packet.py"],cwd=inp,stdout=subprocess.DEVNULL)
m=json.loads((p/"manifest.json").read_text());s=json.loads((p/"summary.json").read_text());att=json.loads((p/"live-ref-attestation.json").read_text());d=json.loads((inp/"input.json").read_text())
assert m["head"]=="00d37b25ce5534135c2dacaf6a84d9d15fe0bb0b" and m["tree"]=="13e57e7826db4db86556f244fb066e4915022511"
assert hashlib.sha256((inp/"input.json").read_bytes()).hexdigest()==m["candidateFreeInputSha256"]
assert att["prBefore"]["headRefOid"]==m["head"]==att["prAfter"]["headRefOid"] and att["prBefore"]["state"]==att["prAfter"]["state"]=="OPEN" and att["prBefore"]["isDraft"] is True and att["prAfter"]["isDraft"] is True
assert att["branchRefBefore"]==att["branchRefAfter"]==m["head"] and att["pullRefBefore"]==att["pullRefAfter"]==m["head"] and att["treeBefore"]==att["treeAfter"]==m["tree"]
rows=[json.loads(x) for x in (p/"review-decisions.jsonl").read_text().splitlines() if x.strip()]; cells={x["locale"]:x for x in d["targetCells"]}
assert len(rows)==12 and set(cells)=={r["locale"] for r in rows}
ph=re.compile(r"\{[A-Za-z][A-Za-z0-9_]*\}");num=re.compile(r"(?<![A-Za-z])\d+(?:[.,]\d+)?(?![A-Za-z])")
for r in rows:
 c=cells[r["locale"]];assert r["sourceId"]==d["sourceId"] and r["currentTarget"]==c["target"] and r["currentTargetSha256"]==c["targetSha256"]==hashlib.sha256(c["target"].encode()).hexdigest()
 assert r["disposition"]=="accept-current" and r["proposedTarget"]==r["currentTarget"] and r["proposedTargetSha256"]==r["currentTargetSha256"] and r["selectedTargetSha256"]==r["currentTargetSha256"]
 assert Counter(ph.findall(d["source"]["source"]))==Counter(ph.findall(r["currentTarget"]))==Counter(["{value0}"])
 assert Counter(num.findall(d["source"]["source"]))==Counter(num.findall(r["currentTarget"])) and d["source"]["protectedLiterals"]==[] and r["protectedLiterals"]==[] and r["protectedLiteralsPreserved"] is True
 assert "M4B" not in r["currentTarget"] and "TargetQualityName" in r["dynamicCallerValueTreatment"]
assert s["dispositions"]=={"accept-current":12,"correction":0,"refinement":0,"hold":0} and s["placeholderMismatches"]==s["numericMismatches"]==s["protectedLiteralMismatches"]==0
assert m["earlierWindowReviewMaterialAccessed"]=="no" and m["priorHoldRationaleReliedOn"]=="no"
print("PASS: 12 exact-hash blind decisions; all accepted unchanged; dynamic placeholder preserved; no static M4B literal; exact live head/tree pinned")
