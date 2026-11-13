#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime, hashlib, json, subprocess
from pathlib import Path
REPO=Path('/mnt/disks/scratch/task-worktrees/localization-20261105/chaptarrng-pr190-w400-cross-pinned')
SLUG='snapetech-org/chaptarrng'; PR=190
BRANCH='codex/chaptarrng-localization-complete-20261031'
HEAD='16c809b4787d70616a1a296ab0d90cf17923ba86'
TREE='dbd8343a42476f4e830428cc59efb7f4830251d5'
API_BASE='025498c1a9deb999a4acd1eafc4c807a252e0c29'
API_BASE_TREE='3c27ce1d128d1d74d3b46bf507e2f99f9c02f4d8'
def run(cmd): return subprocess.check_output(cmd,text=True).strip()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--label',required=True);ap.add_argument('--output',required=True,type=Path);a=ap.parse_args()
 pr=json.loads(run(['gh','pr','view',str(PR),'--repo',SLUG,'--json','number,state,isDraft,headRefName,headRefOid,baseRefName,baseRefOid,url']))
 refs_raw=run(['git','-C',str(REPO),'ls-remote','origin','refs/heads/main','refs/heads/'+BRANCH,'refs/pull/190/head'])
 refs={line.split('\t')[1]:line.split('\t')[0] for line in refs_raw.splitlines() if line.strip()}
 main=refs.get('refs/heads/main')
 def tree(rev): return run(['git','-C',str(REPO),'rev-parse',rev+'^{tree}'])
 wf_head=run(['git','-C',str(REPO),'rev-parse',HEAD+':.github/workflows'])
 wf_main=run(['git','-C',str(REPO),'rev-parse',main+':.github/workflows'])
 status=run(['git','-C',str(REPO),'status','--porcelain=v1'])
 data={'schemaVersion':1,'label':a.label,'capturedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),'repository':SLUG,'pullRequest':PR,'prApi':pr,'remoteRefs':refs,'headSha':HEAD,'headTree':tree(HEAD),'apiBaseSha':API_BASE,'apiBaseTree':tree(API_BASE),'liveMainSha':main,'liveMainTree':tree(main),'headWorkflowTree':wf_head,'liveMainWorkflowTree':wf_main,'exactWorktree':str(REPO),'exactWorktreeHead':run(['git','-C',str(REPO),'rev-parse','HEAD']),'exactWorktreeTree':run(['git','-C',str(REPO),'rev-parse','HEAD^{tree}']),'exactWorktreeClean':not bool(status),'exactWorktreeStatusSha256':hashlib.sha256(status.encode()).hexdigest()}
 if pr['state']!='OPEN' or pr['isDraft'] is not True or pr['headRefName']!=BRANCH or pr['headRefOid']!=HEAD or pr['baseRefName']!='main' or pr['baseRefOid']!=API_BASE: raise SystemExit('PR API does not match expected live state/pins')
 if refs!={'refs/heads/main':main,'refs/heads/'+BRANCH:HEAD,'refs/pull/190/head':HEAD}: raise SystemExit('remote refs do not match expected branch/PR state')
 if data['headTree']!=TREE or data['apiBaseTree']!=API_BASE_TREE: raise SystemExit('Git tree pin mismatch')
 if data['exactWorktreeHead']!=HEAD or data['exactWorktreeTree']!=TREE or not data['exactWorktreeClean']: raise SystemExit('exact worktree is not clean at expected head')
 a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
 print(json.dumps(data,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
