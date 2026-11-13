#!/usr/bin/env python3
import hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
REPO=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/mnt/disks/scratch/task-worktrees/localization-20261105/chaptarrng-pr190-w400-cross-pinned')
BASE=sys.argv[2] if len(sys.argv)>2 else '8ce0caa5c8c456ba5b1bcfeb0352955c93f181e7'
plan=[json.loads(x) for x in (ROOT/'application/apply-plan.jsonl').read_text().splitlines() if x.strip()]
cf=[json.loads(x) for x in (ROOT/'candidate-free/input/candidate-free-cells.jsonl').read_text().splitlines() if x.strip()]
sources={(r['sourceKey'],r['locale']):r['sourceText'] for r in cf}
assert len(plan)==140 and len({r['cellId'] for r in plan})==140
changed={}
def git_json(ref,path): return json.loads(subprocess.check_output(['git','-C',str(REPO),'show',f'{ref}:{path}']))
for r in plan:
 p=r['catalogPath']; key=r['sourceKey']; locale=r['locale']
 before=git_json(BASE,p); after=git_json('HEAD',p)
 assert hashlib.sha256(before[key].encode()).hexdigest()==r['expectedCurrentTargetSha256']
 assert hashlib.sha256(after[key].encode()).hexdigest()==r['finalTargetSha256'] and after[key]==r['finalTarget']
 changed.setdefault(p,set()).add(key)
pat=re.compile(r'\{\d+\}')
for p,keys in changed.items():
 before=git_json(BASE,p); after=git_json('HEAD',p)
 assert list(before)==list(after) and set(before)==set(after) and len(after)==4165
 for key in before:
  if key not in keys: assert before[key]==after[key],(p,key)
 for r in (x for x in plan if x['catalogPath']==p):
  assert sorted(pat.findall(sources[(r['sourceKey'],r['locale'])]))==sorted(pat.findall(r['finalTarget'])),r['cellId']
# Confirm the final branch has exactly the planned target-value changes relative to the review head.
for p,keys in changed.items():
 before=git_json(BASE,p); after=git_json('HEAD',p)
 assert {k for k in before if before[k]!=after[k]}==keys
readback=[json.loads(x) for x in (ROOT/'application/application-readback.jsonl').read_text().splitlines() if x.strip()]
assert len(readback)==140 and all(r['readbackMatches'] for r in readback)
summary=json.loads((ROOT/'application/application-readback-summary.json').read_text())
head=subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD']).decode().strip()
tree=subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD^{tree}']).decode().strip()
assert summary['productCommit']==head and summary['productTree']==tree
print('PASS: 140 exact-hash target readbacks; 12 catalogs retain 4,165 keys and original order; only planned values changed; placeholders preserved; product commit/tree pins match.')
