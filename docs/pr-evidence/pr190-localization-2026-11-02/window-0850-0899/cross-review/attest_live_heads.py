from __future__ import annotations
import json,subprocess,pathlib
from datetime import datetime,timezone
OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0850-0899-crossreview-20261102')
REPOS=[('SeerrNG',418),('ChaptarrNG',190),('QuestarrNG',155),('ROMarrNG',70),('slskR',204),('slskdN',409),('TorrentNG',243)]
def run(*a): return subprocess.check_output(a,text=True).strip()
rows=[]
for repo,n in REPOS:
 pr=json.loads(run('gh','pr','view',str(n),'--repo',f'snapetech-org/{repo}','--json','number,state,isDraft,headRefName,headRefOid,baseRefName,baseRefOid,url'))
 row={'repository':f'snapetech-org/{repo}',**pr}
 try: row['headTree']=json.loads(run('gh','api',f"repos/snapetech-org/{repo}/git/commits/{pr['headRefOid']}"))['tree']['sha']
 except Exception as e: row['headTreeQueryError']=str(e)
 rows.append(row)
cha=next(x for x in rows if x['number']==190)
cha['remoteBranchOid']=run('git','ls-remote','https://github.com/snapetech-org/ChaptarrNG.git',f"refs/heads/{cha['headRefName']}").split()[0]
assert cha['state']=='OPEN' and cha['isDraft'] is True
assert cha['headRefOid']=='175cff3a50569b67def345bb82332b30e9bb378c'
assert cha['headTree']=='e682581e3c577b62215658c374b15a9d3f8f8bd0'
assert cha['remoteBranchOid']==cha['headRefOid']
(OUT/'live-seven-pr-heads.json').write_text(json.dumps({'capturedAtUtc':datetime.now(timezone.utc).isoformat(),'pullRequests':rows},ensure_ascii=False,indent=2,sort_keys=True)+'\n')
print(json.dumps([{'number':x['number'],'repository':x['repository'],'state':x['state'],'isDraft':x['isDraft'],'head':x['headRefOid'],'tree':x.get('headTree'),'remote':x.get('remoteBranchOid')} for x in rows],ensure_ascii=False,indent=2))
