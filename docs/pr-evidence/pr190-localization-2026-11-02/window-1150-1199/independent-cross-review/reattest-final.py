import datetime,json,subprocess
from pathlib import Path
O=Path('.');W='/home/keith/Documents/code/task-worktrees/localization-20261102-chaptarrng'
HEAD='6e7a5341b7ccac31d950c73db68277f9a1f18f8e';TREE='d073e1373021bf715db37461a12654f7e993cdbf';BR='codex/chaptarrng-localization-complete-20261031'
def run(a):return subprocess.run(a,check=True,capture_output=True,text=True).stdout.strip()
pr=json.loads(run(['gh','api','repos/snapetech-org/ChaptarrNG/pulls/190']))
br=json.loads(run(['gh','api',f'repos/snapetech-org/ChaptarrNG/branches/{BR}']))
commit=json.loads(run(['gh','api',f'repos/snapetech-org/ChaptarrNG/commits/{HEAD}']))
local={'head':run(['git','-C',W,'rev-parse','HEAD']),'tree':run(['git','-C',W,'rev-parse','HEAD^{tree}']),
 'branch':run(['git','-C',W,'branch','--show-current']),'status':run(['git','-C',W,'status','--porcelain'])}
assert pr['state']=='open' and pr['draft'] is True and pr['head']['sha']==HEAD
assert br['commit']['sha']==HEAD and commit['commit']['tree']['sha']==TREE
assert local=={'head':HEAD,'tree':TREE,'branch':BR,'status':''},local
start=json.load(open(O/'start-reattestation.json',encoding='utf8'))
report={'passed':True,'reattestedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repository':'snapetech-org/chaptarrng','pullRequest':190,
 'state':pr['state'].upper(),'isDraft':pr['draft'],'branch':BR,'exactHead':HEAD,'exactTree':TREE,'officialRemoteBranchHead':br['commit']['sha'],
 'officialRemoteTree':commit['commit']['tree']['sha'],'localWorktree':local,'startAndFinalExactPinsMatch':start['pr']['head']==HEAD and start['officialRemoteBranch']==HEAD and start['localWorktree']==local,
 'startReattestationSha256':__import__('hashlib').sha256((O/'start-reattestation.json').read_bytes()).hexdigest()}
(O/'final-reattestation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
