import datetime,json,subprocess
from pathlib import Path
OUT=Path('.')
WORK=Path('/home/keith/Documents/code/task-worktrees/localization-20261102-chaptarrng')
HEAD='6e7a5341b7ccac31d950c73db68277f9a1f18f8e'; TREE='d073e1373021bf715db37461a12654f7e993cdbf'
BRANCH='codex/chaptarrng-localization-complete-20261031'
prs=[('seerr','SeerrNG',418),('chaptarr','ChaptarrNG',190),('questarr','QuestarrNG',155),('romarr','ROMarrNG',70),('slskr','slskR',204),('slskdn','slskdN',409),('torrent','TorrentNG',243)]
fields='number state isDraft headRefName headRefOid baseRefName baseRefOid updatedAt url headRepository { name owner { login } } headRef { target { oid ... on Commit { tree { oid } } } }'
query='query { '+' '.join(f'{alias}: repository(owner:"snapetech-org",name:"{repo}") {{ pullRequest(number:{num}) {{ {fields} }} }}' for alias,repo,num in prs)+' }'
def run(args): return subprocess.run(args,check=True,capture_output=True,text=True).stdout.strip()
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
raw=run(['gh','api','graphql','-f',f'query={query}'])
end=datetime.datetime.now(datetime.timezone.utc).isoformat(); data=json.loads(raw)
if data.get('errors'): raise RuntimeError(data['errors'])
snapshot={'snapshotKind':'final-seal-reattestation','queryStartedUtc':start,'queryCompletedUtc':end,'query':query,'pullRequests':data['data']}
(OUT/'snapshots').mkdir(exist_ok=True)
(OUT/'snapshots/final-seal-all-pr-heads.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf8')
ch=data['data']['chaptarr']['pullRequest']; target=ch['headRef']['target']
assert ch['state']=='OPEN' and ch['isDraft'] and ch['headRefName']==BRANCH and ch['headRefOid']==HEAD and target['oid']==HEAD and target['tree']['oid']==TREE, ch
branch=json.loads(run(['gh','api',f'repos/snapetech-org/ChaptarrNG/branches/{BRANCH}']))
commit=json.loads(run(['gh','api',f'repos/snapetech-org/ChaptarrNG/commits/{HEAD}']))
assert branch['commit']['sha']==HEAD and commit['sha']==HEAD and commit['commit']['tree']['sha']==TREE
local={'head':run(['git','-C',str(WORK),'rev-parse','HEAD']),'tree':run(['git','-C',str(WORK),'rev-parse','HEAD^{tree}']),
 'branch':run(['git','-C',str(WORK),'branch','--show-current']),'status':run(['git','-C',str(WORK),'status','--porcelain'])}
assert local=={'head':HEAD,'tree':TREE,'branch':BRANCH,'status':''},local
initial=json.load(open(OUT/'snapshots/start-all-pr-heads.json',encoding='utf8'))
unchanged={}
for alias,_,_ in prs:
 a=initial['pullRequests'][alias]['pullRequest']; b=data['data'][alias]['pullRequest']
 at=a['headRef']['target'].get('tree',{}).get('oid'); bt=b['headRef']['target'].get('tree',{}).get('oid')
 unchanged[alias]={'sameHeadAndTree':a['headRefOid']==b['headRefOid'] and at==bt,'startHead':a['headRefOid'],'startTree':at,'finalHead':b['headRefOid'],'finalTree':bt}
report={'passed':True,'reattestedAtUtc':end,'repository':'snapetech-org/chaptarrng','pullRequest':190,'state':ch['state'],'isDraft':ch['isDraft'],
 'branch':BRANCH,'exactHead':HEAD,'exactTree':TREE,'prHead':ch['headRefOid'],'prTree':target['tree']['oid'],
 'officialRemoteBranchHead':branch['commit']['sha'],'officialRemoteCommitTree':commit['commit']['tree']['sha'],'localWorktree':local,
 'allSevenPrHeadTreeComparedToInputSnapshot':unchanged,'allSevenUnchangedFromInputSnapshot':all(x['sameHeadAndTree'] for x in unchanged.values()),
 'snapshotFile':'snapshots/final-seal-all-pr-heads.json'}
(OUT/'final-reattestation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
