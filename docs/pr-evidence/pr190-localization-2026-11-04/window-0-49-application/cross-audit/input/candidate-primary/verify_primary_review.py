#!/usr/bin/env python3
import collections,hashlib,json,re,subprocess
from pathlib import Path
R=Path("/home/keith/Documents/code/task-scratch/chaptarrng-pr190-creative-holds-fresh-exact-20261103/repo")
O=Path("/home/keith/Documents/code/task-scratch/chaptarrng-pr190-full-catalog-w0-49-20261104")
H="7f5d99e24b054cf1437d135328c3dee565e6b318"; T="d39f2fe8cf91a39653679980c0832c5ca400a114"
def sh(b): return hashlib.sha256(b).hexdigest()
def j(name): return json.loads((O/name).read_text(encoding="utf-8"))
assert subprocess.check_output(["git","-C",str(R),"rev-parse","HEAD"],text=True).strip()==H
assert subprocess.check_output(["git","-C",str(R),"rev-parse","HEAD^{tree}"],text=True).strip()==T
assert not subprocess.check_output(["git","-C",str(R),"status","--porcelain=v1"],text=True).strip()
inp=[json.loads(x) for x in (O/"candidate-free-cells.jsonl").read_text(encoding="utf-8").splitlines() if x]
rows=[json.loads(x) for x in (O/"primary-review-cells.jsonl").read_text(encoding="utf-8").splitlines() if x]
assert len(inp)==600 and len(rows)==600
ins={(x["sourceKey"],x["locale"]):x for x in inp}; seen=set()
for x in rows:
 k=(x["sourceKey"],x["locale"]); assert k not in seen; seen.add(k); a=ins[k]
 assert x["exactHead"]==H and x["exactTree"]==T
 assert x["sourceText"]==a["sourceText"] and x["sourceTextSha256"]==a["sourceTextSha256"]
 assert x["currentTarget"]==a["currentTarget"] and x["currentTargetSha256"]==a["currentTargetSha256"]
 assert sh(x["finalReviewedTarget"].encode())==x["finalReviewedTargetSha256"]
 sig=lambda s:dict(sorted(collections.Counter(re.findall(r"\{[^{}]+\}",s)).items()))
 assert sig(x["sourceText"])==sig(x["finalReviewedTarget"])==x["finalPlaceholders"]
 assert x["protectedLiteralDisposition"]=="pass" and all(c["present"] and c["exactCase"] for c in x["protectedLiteralChecks"])
 if x["primaryDisposition"]=="accept-current": assert x["finalReviewedTarget"]==x["currentTarget"] and x["recommendedTarget"] is None
 else: assert x["primaryDisposition"]=="revise-current" and x["finalReviewedTarget"]!=x["currentTarget"] and x["recommendedTarget"]==x["finalReviewedTarget"]
assert len({x["sourceKey"] for x in rows})==50 and len({x["locale"] for x in rows})==12
selection_hash=sh((O/"source-selection.json").read_bytes()); assert all(x["sourceSelectionSha256"]==selection_hash for x in rows)
for c in j("candidate-free-manifest.json")["catalogs"].values(): assert sh((R/c["path"]).read_bytes())==c["sha256"]
changes=[x for x in rows if x["primaryDisposition"]=="revise-current"]
result={"result":"PASS","exactHead":H,"exactTree":T,"sourceKeys":50,"locales":12,"cells":600,"acceptCurrent":600-len(changes),"reviseCurrent":len(changes),"placeholderParity":True,"protectedLiteralParity":True,"candidateFreeInputLinkage":True,"nativeSpeakerReviewOutstanding":600,"repositoryClean":True}
(O/"primary-review-verification.json").write_text(json.dumps(result,sort_keys=True,indent=2)+chr(10),encoding="utf-8")
print(json.dumps(result,sort_keys=True))
