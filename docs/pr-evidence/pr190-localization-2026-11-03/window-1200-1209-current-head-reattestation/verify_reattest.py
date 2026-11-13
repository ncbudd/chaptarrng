#!/usr/bin/env python3
import argparse,hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
HEAD="60b5df05d401994955499a837f534974b4276c22"
EVIDENCE="docs/pr-evidence/pr190-localization-2026-11-03/window-1200-1209-recheck-c66"
LOCALES={"es":"es.json","zh-Hans":"zh_CN.json","hi":"hi.json","de":"de.json","ja":"ja.json","fr":"fr.json","pt-BR":"pt_BR.json","ar":"ar.json","ko":"ko.json","zh-Hant":"zh_TW.json","vi":"vi.json","id":"id.json"}
def sha(x): return hashlib.sha256(x if isinstance(x,bytes) else x.encode("utf-8")).hexdigest()
def git(repo,*args): return subprocess.check_output(["git","-C",str(repo),*args],text=True).strip()
def blob(repo,path): return subprocess.check_output(["git","-C",str(repo),"show",f"{HEAD}:{path}"])
def j(path): return json.loads(path.read_text(encoding="utf-8"))
def jl(path): return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
def discover_repo():
 for candidate in (Path.cwd(),*Path.cwd().parents):
  if (candidate/".git").exists(): return candidate
 raise SystemExit("Run from a repository worktree or pass --repo")
def main():
 ap=argparse.ArgumentParser(description="Verify Chaptarr W1200–W1209 current-head reattestation evidence")
 ap.add_argument("--repo",type=Path,default=None,help="repository worktree; defaults to the current worktree")
 args=ap.parse_args(); repo=(args.repo or discover_repo()).resolve()
 expected_tree=git(repo,"rev-parse",f"{HEAD}^{{tree}}")
 assert expected_tree=="4c08bd5633244e1d3d07e8b4f1beddab1503a9b3"
 root_summary=j(HERE/"summary.json"); report=jl(HERE/"cell-reattestation.jsonl")
 old=repo/EVIDENCE; manifest=j(old/"manifest.json"); inputs=jl(old/"clean-input-cells.jsonl"); primary=jl(old/"primary-review-cells.jsonl"); readback=j(old/"readback.json"); plan=j(old/"apply-plan.json")
 assert root_summary["reviewedAtHead"]==HEAD and root_summary["mismatchCount"]==0 and root_summary["allReviewedTargetsReadBack"] is True
 assert len(inputs)==len(primary)==len(report)==readback["targetCells"]==120
 assert root_summary["tree"]==expected_tree and manifest["head"]==plan["inputHead"]
 primary_by={(r["sourceId"],r["locale"]):r for r in primary}
 read_by={(r["sourceId"],r["locale"]):r for r in readback["readback"]}
 plan_targets={(r["sourceId"],r["locale"]):r["finalTarget"] for r in plan["changes"]}
 report_by={(r["sourceId"],r["locale"]):r for r in report}
 assert len(primary_by)==len(read_by)==len(report_by)==120
 english=json.loads(blob(repo,"src/NzbDrone.Core/Localization/Core/en.json")); catalogs={}
 for locale,filename in LOCALES.items():
  catalogs[locale]=json.loads(blob(repo,f"src/NzbDrone.Core/Localization/Core/{filename}"))
  assert len(catalogs[locale])==4165 and set(catalogs[locale])==set(english)
 failures=[]; different_from_input=0; caller_line_count=0
 for x in inputs:
  key=(x["sourceId"],x["locale"]); p=primary_by[key]; rb=read_by[key]; rr=report_by[key]
  source=json.loads(blob(repo,x["sourceFile"])).get(x["sourceId"])
  source_ok=source==x["source"] and sha(source or "")==x["sourceSha256"]
  final=plan_targets.get(key,p["finalReviewedTarget"])
  target=catalogs[x["locale"]].get(x["sourceId"])
  target_ok=target==final and sha(target or "")==rb["finalTargetSha256"] and sha(final)==rb["finalTargetSha256"]
  caller_checks=[]
  for ref in x.get("liveCallerRefs",[]):
   lines=blob(repo,ref["file"]).decode("utf-8").splitlines()
   for line in ref.get("context",[]):
    actual=lines[line["line"]-1] if 1<=line["line"]<=len(lines) else None
    ok=actual==line["text"] and sha(actual or "")==line["sha256"]
    caller_checks.append(ok); caller_line_count+=1
  caller_ok=all(caller_checks)
  if target!=x["currentTarget"]: different_from_input+=1
  if not source_ok or not target_ok or not caller_ok or not rr["sourceUnchanged"] or not rr["targetMatchesReviewedReadback"] or not rr["callerContextUnchanged"]:
   failures.append({"sourceId":key[0],"locale":key[1],"sourceOk":source_ok,"targetOk":target_ok,"callerOk":caller_ok,"report":rr})
 assert not failures, json.dumps(failures,ensure_ascii=False)
 assert different_from_input==root_summary["targetCellValuesDifferentFromOldInput"]==8
 assert root_summary["sourceIds"]==10 and root_summary["allSourcesUnchanged"] and root_summary["allCallerContextsUnchanged"]
 checks=[]
 for line in (HERE/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
  digest,name=line.split("  ",1); data=(HERE/name).read_bytes(); assert sha(data)==digest,name; checks.append(name)
 assert set(checks)=={x.name for x in HERE.iterdir() if x.is_file() and x.name!="SHA256SUMS.txt"},checks
 print(json.dumps({"pass":True,"head":HEAD,"tree":expected_tree,"cells":120,"sourceIds":10,"locales":12,"sourceAndCallerFailures":0,"readbackFailures":0,"appliedTargetDifferences":different_from_input,"callerLinesRechecked":caller_line_count,"catalogKeysPerLocale":4165},indent=2))
if __name__=="__main__": main()
