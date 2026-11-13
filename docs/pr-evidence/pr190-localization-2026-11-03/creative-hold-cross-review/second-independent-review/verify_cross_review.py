#!/usr/bin/env python3
import argparse,hashlib,json,re,subprocess
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parent
HEAD="15fde999b8b8dc29d44833845aba13e1a2ad0443";TREE="79f0882d1fa904ee967fb37ad1349dc6434c9537"
BRANCH="codex/chaptarrng-localization-complete-20261031";BASE_SHA="03274100af783fdffaca4dd8436e163dc6b18795"
def need(ok,m):
 if not ok:raise SystemExit("FAIL: "+m)
def sha(b):return hashlib.sha256(b).hexdigest()
def shat(s):return sha(s.encode())
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def rj(p):return json.loads(p.read_text(encoding="utf-8"))
def rjl(p):return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
PH=re.compile(r"\{[A-Za-z][A-Za-z0-9_]*\}");TAG=re.compile(r"</?[A-Za-z][^>]*>")
NUM=re.compile(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])")
PROT=re.compile(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])")
def tokens(s):return {"placeholders":PH.findall(s),"markupTags":TAG.findall(s),"numericTokens":NUM.findall(s),"protectedLiterals":list(dict.fromkeys(m.group(0) for m in PROT.finditer(s)))}
def sums(root):
 f=root/"SHA256SUMS.txt";need(f.is_file(),"missing checksum file");entries={}
 for line in f.read_text().splitlines():
  if not line:continue
  need(len(line)>=66 and line[64:66]=="  ","bad checksum line")
  d,n=line[:64],line[66:].lstrip("*");need(n not in entries,"duplicate checksum "+n)
  p=root/n;need(p.is_file() and sha(p.read_bytes())==d,"checksum mismatch "+n);entries[n]=d
 actual={p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p.name!="SHA256SUMS.txt"}
 need(actual==set(entries),"checksum inventory coverage mismatch");return entries
def repo_check(repo,pins,cells,contexts,holds):
 repo=str(repo);h=subprocess.check_output(["git","-C",repo,"rev-parse","HEAD"],text=True).strip()
 t=subprocess.check_output(["git","-C",repo,"rev-parse","HEAD^{tree}"],text=True).strip()
 st=subprocess.check_output(["git","-C",repo,"status","--porcelain"],text=True)
 need(h==HEAD and t==TREE and not st,"repo head/tree/status mismatch")
 for pin in pins["pins"]+pins["hashOnlyExclusionEvidencePins"]:
  data=subprocess.check_output(["git","-C",repo,"show",f"HEAD:{pin['path']}"])
  blob=subprocess.check_output(["git","-C",repo,"rev-parse",f"HEAD:{pin['path']}"],text=True).strip()
  need(len(data)==pin["byteCount"] and sha(data)==pin["sha256"] and blob==pin["gitBlob"],"file pin mismatch "+pin["path"])
 catalog={p["path"]:json.loads(subprocess.check_output(["git","-C",repo,"show",f"HEAD:{p['path']}"])) for p in pins["pins"] if p["kind"]=="locale-catalog"}
 en=next(p for p in pins["pins"] if p["kind"]=="source-catalog")
 source=json.loads(subprocess.check_output(["git","-C",repo,"show",f"HEAD:{en['path']}"]))
 for c in cells:
  need(source.get(c["sourceId"])==c["source"] and catalog[c["targetFile"]].get(c["sourceId"])==c["currentTarget"],"catalog preimage mismatch "+c["locale"])
 active_pin=next(p for p in pins["hashOnlyExclusionEvidencePins"] if p["kind"]=="hash-only-hold-inventory")
 data=subprocess.check_output(["git","-C",repo,"show",f"HEAD:{active_pin['path']}"])
 active={(x["sourceOrdinal"],x["locale"]):x for x in (json.loads(line) for line in data.decode().splitlines() if line.strip())}
 status_pin=next(p for p in pins["hashOnlyExclusionEvidencePins"] if p["kind"]=="hash-only-caller-status")
 status=json.loads(subprocess.check_output(["git","-C",repo,"show",f"HEAD:{status_pin['path']}"]))
 groups={x["sourceOrdinal"]:x for x in status["groups"]}
 for x in holds:
  a=active[(x["sourceOrdinal"],x["locale"])]
  need(shat(a["sourceId"])==x["sourceIdSha256"] and a["sourceTextSha256"]==x["sourceTextSha256"]
       and a["currentTargetSha256"]==x["liveTargetSha256"]==x["recordedTargetSha256"] and a["evidenceSha256"]==x["evidenceSha256"],"callerless hash mismatch")
  g=groups[x["sourceOrdinal"]];need(g["holdRemains"] and not g["exactUserFacingCallerFound"] and g["directCallerRefs"]==[],"callerless status mismatch")
 nlines=0
 for cx in contexts:
  data=subprocess.check_output(["git","-C",repo,"show",f"HEAD:{cx['sourceFile']}"])
  need(json.loads(data).get(cx["sourceId"])==cx["source"],"source text mismatch")
  for c in cx["callerReferences"]:
   data=subprocess.check_output(["git","-C",repo,"show",f"HEAD:{c['path']}"])
   need(sha(data)==c["fileSha256"],"caller file hash mismatch")
   lines=data.decode().splitlines()
   for q in c["contextLines"]:
    need(lines[q["line"]-1]==q["text"] and shat(q["text"])==q["lineSha256"],"caller line mismatch")
    nlines+=1
 return {"pins":18,"creativeCells":len(cells),"callerLines":nlines,"callerlessHashRows":len(holds)}
def main():
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument("--repo");args=ap.parse_args()
 root_sums=sums(ROOT);m=rj(ROOT/"manifest.json");s=rj(ROOT/"summary.json")
 need(m["head"]==HEAD and m["tree"]==TREE and m["branch"]==BRANCH and m["baseSha"]==BASE_SHA and m["recommendationCount"]==20,"manifest pin mismatch")
 need(m["fileHashes"]=={k:v for k,v in root_sums.items() if k!="manifest.json"},"manifest file hash mismatch")
 inp=ROOT/"inputs/independent-review-packet"
 subprocess.check_call(["python3",str(inp/"review/verify_review.py")],stdout=subprocess.DEVNULL)
 need(m["inputPacketRootSha256"]==sha((inp/"manifest.json").read_bytes()),"input manifest pin mismatch")
 need(m["inputPacketChecksumSha256"]==sha((inp/"SHA256SUMS.txt").read_bytes()),"input root checksum pin mismatch")
 cells=rjl(inp/"input/creative-current-cells.jsonl");ctxs=rjl(inp/"input/source-caller-context.jsonl")
 recs=rjl(inp/"review/independent-recommendations.jsonl");rows=rjl(ROOT/"cross-ledger.jsonl")
 holds=ROOT/"callerless-hold-hashes-only.jsonl";hold_in=inp/"input/callerless-hold-hashes-only.jsonl"
 need(holds.read_bytes()==hold_in.read_bytes(),"callerless hash records changed")
 hold_rows=rjl(holds);need(len(hold_rows)==24,"callerless hash row count mismatch")
 need(all(set(x)=={"sourceOrdinal","sourceIdSha256","locale","sourceTextSha256","recordedTargetSha256","liveTargetSha256","sourceTextHashSameAtHead","targetHashSameAtHead","evidenceSha256"} for x in hold_rows),"callerless file contains non-hash fields")
 cm={(x["sourceId"],x["locale"]):x for x in cells};rm={(x["sourceId"],x["locale"]):x for x in recs};xm={(x["sourceId"],x["locale"]):x for x in rows}
 need(len(cm)==len(rm)==len(xm)==20 and set(cm)==set(rm)==set(xm),"cross ledger coverage mismatch")
 cx={x["sourceId"]:x for x in ctxs};dec=Counter();conf=Counter()
 for key,c in cm.items():
  r=rm[key];x=xm[key];context=cx[c["sourceId"]]
  need(x["sourceId"]==c["sourceId"] and x["sourceIdSha256"]==shat(c["sourceId"]),"source id mismatch")
  need(x["source"]==c["source"]==r["source"] and x["sourceSha256"]==c["sourceSha256"]==r["sourceSha256"]==shat(c["source"]),"source preimage mismatch")
  need(x["currentTarget"]==c["currentTarget"]==r["currentTarget"] and x["currentTargetSha256"]==c["currentTargetSha256"]==r["currentTargetSha256"]==shat(c["currentTarget"]),"target preimage mismatch")
  need(x["targetPreimageReattested"] is True and x["locale"]==c["locale"]==r["locale"],"target attestation missing")
  need(x["independentRecommendation"]==r["independentTargetRecommendation"] and x["recommendationSha256"]==r["targetRecommendationSha256"]==shat(r["independentTargetRecommendation"]),"recommendation mismatch")
  need(x["callerContextSha256"]==context["callerContextSha256"]==r["callerContextSha256"] and x["callerCount"]==context["callerCount"]==r["callerCount"],"caller context pin mismatch")
  need(context["callerContextSha256"]==shat(canon(context["callerReferences"])),"caller context digest mismatch")
  refs=[{"path":a["path"],"fileSha256":a["fileSha256"],"gitBlob":a["gitBlob"],"startLine":a["startLine"],"endLine":a["endLine"],"freshContextSha256":a["freshContextSha256"]} for a in context["callerReferences"]]
  need(x["callerReferencePins"]==refs,"caller refs mismatch")
  st=tokens(c["source"]);ct=tokens(c["currentTarget"]);rt=tokens(r["independentTargetRecommendation"])
  need(x["sourceTokens"]==st==r["sourceTokenChecks"] and x["currentTargetTokens"]==ct and x["recommendationTokenChecks"]==rt==r["recommendedTargetTokenChecks"]==st,"token/literal checks mismatch")
  need(x["recommendationSha256"]==shat(x["independentRecommendation"]),"recommendation hash mismatch")
  need(x["crossDecision"] in ("advance-to-qualified-native-review","hold-for-qualified-native-review"),"bad cross decision")
  need(x["nativeSpeakerSignoff"] is False and x["applicationStatus"]=="not applied","native/application state mismatch")
  need(bool(x["crossRationale"]),"missing rationale")
  if x["crossDecision"]=="advance-to-qualified-native-review":
   need(x["crossTargetRecommendation"]==x["independentRecommendation"] and x["crossTargetRecommendationSha256"]==x["recommendationSha256"] and x["holdReason"] is None,"advance target mismatch")
  else:
   need(x["crossTargetRecommendation"] is None and x["crossTargetRecommendationSha256"] is None and x["holdReason"]==x["crossRationale"],"held candidate exposed as selected")
  dec[x["crossDecision"]]+=1;conf[x["crossConfidence"]]+=1
 need(dec==s["crossDecisionCounts"] and conf==s["crossConfidenceCounts"],"summary count mismatch")
 need(len(hold_rows)==s["callerlessHashCellsPreserved"]==s["callerlessSourceAndTargetHashesUnchanged"]==24,"callerless preservation summary mismatch")
 need(m["sourcePinReattestationSha256"]==sha((ROOT/"source-pin-reattestation.json").read_bytes()),"source attestation hash mismatch")
 need(m["livePrReattestationSha256"]==sha((ROOT/"live-pr-reattestation.json").read_bytes()),"live attestation hash mismatch")
 pin=rj(ROOT/"source-pin-reattestation.json");live=rj(ROOT/"live-pr-reattestation.json")
 need(pin["result"]=="PASS" and pin["head"]==HEAD and pin["tree"]==TREE and pin["sourceCallerCatalogPinCount"]==16
      and pin["creativeTargetPreimagesReattested"]==20 and pin["callerlessHashCellsReattested"]==24,"source attestation mismatch")
 for stage in ("observedBeforeWrite","observedDuringSeal"):
  z=live[stage];p=z["pr"]
  need(p["state"]=="OPEN" and p["isDraft"] and p["headRefOid"]==HEAD and p["headRefName"]==BRANCH and p["baseRefOid"]==BASE_SHA,"live PR pin mismatch")
  need(z["remoteRefs"]=={f"refs/heads/{BRANCH}":HEAD,"refs/pull/190/head":HEAD} and z["apiTree"]==TREE,"live refs mismatch")
  need(z["sourceCheckout"]["head"]==HEAD and z["sourceCheckout"]["tree"]==TREE and z["sourceCheckout"]["clean"],"checkout pin mismatch")
 need(live["observedBeforeWrite"]["pr"]==live["observedDuringSeal"]["pr"],"PR changed during seal")
 repo_result=repo_check(args.repo,rj(inp/"input/file-pins.json"),cells,ctxs,hold_rows) if args.repo else None
 print(json.dumps({"result":"PASS","head":HEAD,"tree":TREE,"recommendations":20,"advanceToNativeReview":dec["advance-to-qualified-native-review"],
  "heldForNativeReview":dec["hold-for-qualified-native-review"],"crossConfidenceCounts":dict(conf),"sourceCallerCatalogPins":16,
  "targetPreimages":20,"callerReferences":5,"callerlessHashesPreserved":24,"nativeSpeakerSignoff":False,"rootFilesChecked":len(root_sums),
  "exactRepoReattestation":repo_result},ensure_ascii=False,indent=2))
if __name__=="__main__":
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument("--repo");main()
