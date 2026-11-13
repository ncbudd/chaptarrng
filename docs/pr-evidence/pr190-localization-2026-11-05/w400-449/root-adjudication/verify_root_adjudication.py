#!/usr/bin/env python3
import hashlib, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
rows=[json.loads(x) for x in (HERE/"root-adjudication-ledger.jsonl").read_text().splitlines() if x.strip()]
second=[json.loads(x) for x in (ROOT/"second-opinion/second-opinion-ledger.jsonl").read_text().splitlines() if x.strip()]
assert len(rows)==len(second)==140
assert len({r["cellId"] for r in rows})==140
by={r["cellId"]:r for r in rows}
for s in second:
 r=by[s["cellId"]]
 assert r["exactHead"]==s["exactHead"] and r["exactTree"]==s["exactTree"]
 assert r["sourceTextSha256"]==s["sourceTextSha256"] and r["currentTargetSha256"]==s["currentTargetSha256"]
 assert r["candidateFreeRowSha256"]==s["candidateFreeRowSha256"] and r["crossReviewRowSha256"]==s["crossReviewRowSha256"]
 assert r["finalTarget"]==s["finalTarget"] and r["finalTargetSha256"]==s["finalTargetSha256"]
 if s["decision"]=="accept-recommendation":
  assert r["rootDecision"]=="accept-cross-recommendation" and s["finalTarget"]==s["crossRecommendationTarget"]
 else:
  assert s["decision"]=="adjust" and r["rootDecision"]=="accept-adjusted-target"
assert sum(r["rootDecision"]=="accept-cross-recommendation" for r in rows)==134
assert sum(r["rootDecision"]=="accept-adjusted-target" for r in rows)==6
summary=json.loads((HERE/"summary.json").read_text())
assert summary["exactHead"]=="8ce0caa5c8c456ba5b1bcfeb0352955c93f181e7"
assert summary["exactTree"]=="018e46cd14424204a01be46e13e5b50f9f26ce07"
assert summary["callerlessHashOnlyHolds"]==12 and not summary["nativeSpeakerApproval"]
print("PASS: 140 root dispositions match exact candidate-free, cross-review, and second-opinion rows; 134 cross recommendations accepted, 6 adjusted; 12 callerless holds remain hash-only.")
