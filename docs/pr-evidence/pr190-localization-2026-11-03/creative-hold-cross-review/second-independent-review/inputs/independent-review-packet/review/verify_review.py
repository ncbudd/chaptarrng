#!/usr/bin/env python3
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; INPUT=ROOT/"input"; REVIEW=ROOT/"review"
def sha(b): return hashlib.sha256(b).hexdigest()
def sha_text(s): return sha(s.encode("utf-8"))
def readj(p): return json.loads(p.read_text(encoding="utf-8"))
def readjl(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x]
def sums(d,n):
 f=d/n; rows=[line.split(None,1) for line in f.read_text().splitlines()]
 entries=[(x[1].lstrip("* "),x[0]) for x in rows]
 actual={p.relative_to(d).as_posix() for p in d.rglob("*") if p.is_file() and p!=f}
 assert len(entries)==len({p for p,_ in entries}) and {p for p,_ in entries}==actual
 for p,h in entries: assert sha((d/p).read_bytes())==h,p
 return len(entries)
def tokens(s):
 return {"placeholders":re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}",s),"markupTags":re.findall(r"<\/?[A-Za-z][^>]*>",s),"numericTokens":re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])",s),"protectedLiterals":[m.group(0) for m in re.finditer(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])",s)]}
root=readj(ROOT/"manifest.json"); review=readj(REVIEW/"manifest.json"); summary=readj(REVIEW/"summary.json")
assert root["head"]==review["head"]=="15fde999b8b8dc29d44833845aba13e1a2ad0443" and root["tree"]==review["tree"]=="79f0882d1fa904ee967fb37ad1349dc6434c9537"
assert root["creativeCellCount"]==review["recommendationCount"]==summary["creativeCellCount"]==20
assert root["callerlessHoldsOutOfScope"]==root["callerlessHashCount"]==summary["callerlessHoldsExcluded"]==24
root_n=sums(ROOT,"SHA256SUMS.txt"); review_n=sums(REVIEW,"SHA256SUMS.txt"); input_n=sums(INPUT,"SHA256SUMS.txt")
contexts=readjl(INPUT/"source-caller-context.jsonl"); cells=readjl(INPUT/"creative-current-cells.jsonl"); recs=readjl(REVIEW/"independent-recommendations.jsonl"); exclusions=readjl(INPUT/"callerless-hold-hashes-only.jsonl")
assert len(contexts)==3 and len(cells)==len(recs)==20 and len(exclusions)==24
byctx={x["sourceId"]:x for x in contexts}; bycell={(x["sourceId"],x["locale"]):x for x in cells}
assert len(bycell)==20
for x in contexts:
 assert x["sourceSha256"]==sha_text(x["source"]) and x["callerCount"]==len(x["callerReferences"])>0
 for c in x["callerReferences"]:
  assert c["freshContextSha256"] and all(q["lineSha256"]==sha_text(q["text"]) for q in c["contextLines"])
for c in cells:
 assert c["currentTargetSha256"]==sha_text(c["currentTarget"])
 assert c["sourceTokens"]==tokens(c["source"]) and c["currentTargetTokens"]==tokens(c["currentTarget"])
 assert c["targetUnchangedFromCandidateFreeSeed"] is True
for r in recs:
 key=(r["sourceId"],r["locale"]); c=bycell[key]; x=byctx[r["sourceId"]]
 assert r["source"]==c["source"] and r["sourceSha256"]==c["sourceSha256"]==sha_text(r["source"])
 assert r["currentTarget"]==c["currentTarget"] and r["currentTargetSha256"]==c["currentTargetSha256"]
 assert r["targetRecommendationSha256"]==sha_text(r["independentTargetRecommendation"])
 assert r["decision"]=="recommend-target" and r["confidence"] in {"high","moderate","low","unknown"}
 assert r["callerCount"]==x["callerCount"] and r["nativeSpeakerSignoff"] is False and r["applicationStatus"]=="not applied"
 assert r["sourceTokenChecks"]==tokens(r["source"]) and r["recommendedTargetTokenChecks"]==tokens(r["independentTargetRecommendation"])
 for k in r["sourceTokenChecks"]: assert r["sourceTokenChecks"][k]==r["recommendedTargetTokenChecks"][k]
assert len({(x["sourceOrdinal"],x["locale"]) for x in exclusions})==24
for x in exclusions:
 assert set(x)=={"sourceOrdinal","sourceIdSha256","locale","sourceTextSha256","recordedTargetSha256","liveTargetSha256","sourceTextHashSameAtHead","targetHashSameAtHead","evidenceSha256"}
 assert x["sourceTextHashSameAtHead"] is True and all(len(x[k])==64 for k in ["sourceIdSha256","sourceTextSha256","recordedTargetSha256","liveTargetSha256","evidenceSha256"])
pin=readj(INPUT/"file-pins.json"); live=readj(REVIEW/"live-pr-and-pin-after.json")
assert len(pin["pins"])==16 and pin["head"]=="15fde999b8b8dc29d44833845aba13e1a2ad0443" and pin["tree"]=="79f0882d1fa904ee967fb37ad1349dc6434c9537"
assert live["afterLedger"]["head"]==live["afterLedger"]["branchRef"]==live["afterLedger"]["pullRef"]==root["head"]
assert live["afterLedger"]["state"]=="OPEN" and live["afterLedger"]["draft"] is True and live["creativeTargetsReattested"] is True
assert live["callerlessHoldHashCount"]==24 and live["callerlessHoldTargetsHashOnly"] is True
print(json.dumps({"result":"PASS","head":root["head"],"tree":root["tree"],"recommendations":len(recs),"callerlessHashOnlyCells":len(exclusions),"callerlessHashMatchesAtHead":sum(x["targetHashSameAtHead"] for x in exclusions),"sourceCallerCatalogPins":len(pin["pins"]),"rootChecksumEntries":root_n,"reviewChecksumEntries":review_n,"inputChecksumEntries":input_n,"nativeSpeakerSignoff":False},ensure_ascii=False,indent=2))
