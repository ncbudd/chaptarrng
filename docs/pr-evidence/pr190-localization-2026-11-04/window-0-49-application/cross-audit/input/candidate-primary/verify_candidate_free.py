#!/usr/bin/env python3
import hashlib,json,subprocess
from pathlib import Path
R=Path("/home/keith/Documents/code/task-scratch/chaptarrng-pr190-creative-holds-fresh-exact-20261103/repo")
O=Path("/home/keith/Documents/code/task-scratch/chaptarrng-pr190-full-catalog-w0-49-20261104")
H="7f5d99e24b054cf1437d135328c3dee565e6b318"; T="d39f2fe8cf91a39653679980c0832c5ca400a114"
def sh(b): return hashlib.sha256(b).hexdigest()
def j(p): return json.loads(p.read_text(encoding="utf-8"))
assert subprocess.check_output(["git","-C",str(R),"rev-parse","HEAD"],text=True).strip()==H
assert subprocess.check_output(["git","-C",str(R),"rev-parse","HEAD^{tree}"],text=True).strip()==T
assert not subprocess.check_output(["git","-C",str(R),"status","--porcelain=v1"],text=True).strip()
rows=[json.loads(x) for x in (O/"candidate-free-cells.jsonl").read_text(encoding="utf-8").splitlines() if x]
assert len(rows)==600 and len({x["sourceKey"] for x in rows})==50 and len({x["locale"] for x in rows})==12
assert not any(k in r for r in rows for k in ("candidate","suggestion","recommendedTarget","finalReviewedTarget","decisionRationale"))
for r in rows:
 assert sh(r["sourceText"].encode())==r["sourceTextSha256"] and sh(r["currentTarget"].encode())==r["currentTargetSha256"]
 assert r["sourcePlaceholders"]==r["currentPlaceholders"] and r["currentProtectedLiteralsPresent"]
for x in j(O/"candidate-free-manifest.json")["catalogs"].values(): assert sh((R/x["path"]).read_bytes())==x["sha256"]
sel=j(O/"source-selection.json"); assert not sel["overlapCoreKeys"] and sel["keyCount"]==50
keys=set(sel["keys"]); direct=[]; W=R/"docs/pr-evidence/pr190-localization-2026-11-02"
window_files=[p for wd in W.glob("window-*") for p in wd.rglob("*.jsonl")]
for p in window_files:
 for line in p.read_text(encoding="utf-8").splitlines():
  if not line.strip(): continue
  try: row=json.loads(line)
  except Exception: continue
  if isinstance(row,dict) and any(isinstance(row.get(k),str) and row.get(k) in keys for k in ("sourceKey","source_key","key","sourceId","source_id","id")): direct.append(p.as_posix())
assert not direct and len(window_files)==sel["allWindowJsonlFileCountScannedForDirectRequestedKeys"]
assert sel["allWindowJsonlDirectRequestedKeyRowCount"]==0 and not sel["allWindowJsonlDirectRequestedKeyMatches"]
result={"result":"PASS","exactHead":H,"exactTree":T,"cells":len(rows),"sourceKeys":50,"locales":12,"placeholdersMatch":True,"protectedLiteralsPresent":True,"candidateFieldsAbsent":True,"priorDirectOverlap":0,"allPriorWindowJsonlFilesScanned":len(window_files),"repositoryClean":True}
(O/"candidate-free-verification.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,sort_keys=True))
