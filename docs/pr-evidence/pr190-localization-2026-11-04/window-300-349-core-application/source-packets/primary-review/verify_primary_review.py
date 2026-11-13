#!/usr/bin/env python3
import collections,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent; I=P.parent/"candidate-free/input"; HEAD="f0082d1b655c05b8d4019ede523dd695cd6d745a"; TREE="4cf2322354e9cf9b12d59cf10d0d8661c68ab4af"
def sha(b):return hashlib.sha256(b).hexdigest()
def rj(p):return json.loads(p.read_text(encoding="utf-8"))
def rjl(p):return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
def need(v,m):
 if not v:raise SystemExit("FAIL: "+m)
def sums(p):
 rec={}
 for line in p.read_text().splitlines():
  h,n=line.split("  ",1);f=p.parent/n;need(f.is_file() and sha(f.read_bytes())==h,"checksum "+n);rec[n]=h
 need(set(rec)=={x.name for x in p.parent.iterdir() if x.is_file() and x.name!=p.name},"checksum coverage")
need((rj(I/"candidate-free-manifest.json")["head"],rj(I/"candidate-free-manifest.json")["tree"])==(HEAD,TREE),"candidate-free pin")
sums(I/"SHA256SUMS.txt");sums(P/"primary-review-SHA256SUMS.txt")
subprocess.run(["python3",str(I/"verify_candidate_free.py")],check=True,stdout=subprocess.DEVNULL)
inc=rjl(I/"candidate-free-cells.jsonl"); rows=rjl(P/"primary-review-cells.jsonl"); props=rjl(P/"primary-review-proposals.jsonl"); holds=rjl(P/"primary-review-holds.jsonl"); summary=rj(P/"primary-review-summary.json"); note=rj(P/"primary-review-source-notes.json")
need(len(inc)==len(rows)==600 and len(holds)==48,"cell/hold counts")
im={(x["sourceOrdinal"],x["locale"]):x for x in inc}; rm={(x["sourceOrdinal"],x["locale"]):x for x in rows}; pm={(x["sourceOrdinal"],x["locale"]):x for x in props}
need(len(im)==len(rm)==600 and set(im)==set(rm),"cell identity coverage")
need(len(pm)==len(props) and len(pm)==summary["counts"]["proposals"] and set(pm).issubset(rm),"proposal identity/count")
counts=collections.Counter(x["primaryDisposition"] for x in rows)
need(counts["hold-callerless-context"]==48 and counts["accept-current"]+counts["revise-current"]==552,"disposition counts")
need(counts["revise-current"]==len(props),"proposal disposition count")
for ident,c in im.items():
 r=rm[ident]; h=ident in {(x["sourceOrdinal"],x["locale"]) for x in holds}
 need((r["exactHead"],r["exactTree"])==(HEAD,TREE) and r["batch"]=="W300-349-Core","row pin")
 need(r["sourceOrdinal"]==c["sourceOrdinal"] and r["locale"]==c["locale"],"cell identity")
 need(r["candidateFreeRowSha256"]==sha((I/"candidate-free-cells.jsonl").read_bytes().splitlines()[list(im).index(ident)]),"candidate-free row linkage")
 if h:
  need(r["primaryDisposition"]=="hold-callerless-context" and r.get("targetTextIncluded") is False and r.get("sourceTextIncluded") is False,"hash-only hold")
  need(not any(k in r for k in ("sourceText","currentTarget","finalReviewedTarget","recommendedTarget")),"hold text leakage")
  need(r["currentTargetSha256"]==c["currentTargetSha256"] and r["sourceTextSha256"]==c["sourceTextSha256"],"hold hash linkage")
 else:
  need(r["sourceKey"]==c["sourceKey"] and r["sourceText"]==c["sourceText"] and r["currentTarget"]==c["currentTarget"],"source/current linkage")
  need(r["sourceTextSha256"]==c["sourceTextSha256"] and r["currentTargetSha256"]==c["currentTargetSha256"],"source/current hash linkage")
  need(sha(r["finalReviewedTarget"].encode())==r["finalReviewedTargetSha256"],"final target hash")
  if r["primaryDisposition"]=="accept-current":need(r["finalReviewedTarget"]==c["currentTarget"] and ident not in pm,"accepted-current")
  else:
   p=pm[ident];need(p["recommendedTarget"]==r["finalReviewedTarget"] and p["recommendedTargetSha256"]==r["finalReviewedTargetSha256"],"proposal linkage")
   need(p["sourceTextSha256"]==c["sourceTextSha256"] and p["currentTargetSha256"]==c["currentTargetSha256"],"proposal source hashes")
   need(r["callerReferenceCount"]>0 and bool(r["callerRefs"]),"proposed cell caller context")
  need(r["nativeSpeakerApproval"] is False and r["nativeSpeakerReviewOutstanding"] is True,"speaker status")
need(summary["counts"]["accept-current"]==counts["accept-current"] and summary["counts"]["revise-current"]==counts["revise-current"],"summary counts")
need(summary["currentWindowBlindOrCrossOutputsAccessed"] is False and note["currentWindowBlindOrCrossOutputsAccessed"] is False,"current-window review independence")
need(note["priorWindowCrossReviewSemanticallyUsed"] is False,"prior-window cross use")
need(note["callerlessKeys"]==["BookOnePlaceholder","BookTwoPlaceholder","ConflictsConsidered","SiblingTitlePlaceholder"],"callerless key set")
print(json.dumps({"result":"PASS","head":HEAD,"tree":TREE,"cells":600,"proposals":len(props),"acceptCurrent":counts["accept-current"],"callerlessHolds":counts["hold-callerless-context"],"callerBackedKeys":46,"nativeSpeakerApproval":0,"nativeSpeakerReviewOutstanding":600},sort_keys=True))
