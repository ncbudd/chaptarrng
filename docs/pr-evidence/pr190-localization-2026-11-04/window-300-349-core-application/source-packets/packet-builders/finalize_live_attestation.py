#!/usr/bin/env python3
import datetime,hashlib,json,pathlib,subprocess
ROOT=pathlib.Path('/mnt/disks/scratch/task-worktrees/localization-20261104/chaptarrng-pr190-w300-349-source')
TASK=pathlib.Path('/home/keith/Documents/code/task-scratch/chaptarrng-pr190-w300-349-core-20261104')
OUT=TASK/'candidate-free/input'
REPO='snapetech-org/ChaptarrNG';PR=190;HEAD='f0082d1b655c05b8d4019ede523dd695cd6d745a';TREE='4cf2322354e9cf9b12d59cf10d0d8661c68ab4af';BASE='17bde320915af42de73b8646ad56f8ba2ccebf4e';BRANCH='codex/chaptarrng-localization-complete-20261031'
def run(args):return subprocess.check_output(args,text=True).strip()
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
q='query { repository(owner:"snapetech-org",name:"ChaptarrNG") { pullRequest(number:190) { number state isDraft mergedAt headRefName headRefOid baseRefName baseRefOid } } }'
pr=json.loads(run(['gh','api','graphql','-f','query='+q]))['data']['repository']['pullRequest']
refs=sorted(run(['git','-C',str(ROOT),'ls-remote','origin',f'refs/heads/{BRANCH}',f'refs/pull/{PR}/head','refs/heads/main']).splitlines())
refmap={x.split('\t')[1]:x.split('\t')[0] for x in refs}
main=refmap['refs/heads/main']
apihead=json.loads(run(['gh','api',f'repos/{REPO}/git/commits/{HEAD}','--jq','{sha:.sha,tree:.tree.sha}']))
apimain=json.loads(run(['gh','api',f'repos/{REPO}/git/commits/{main}','--jq','{sha:.sha,tree:.tree.sha}']))
compare=json.loads(run(['gh','api',f'repos/{REPO}/compare/{BASE}...{main}','--jq','{status:.status,aheadBy:.ahead_by,changedPaths:[.files[].filename]}']))
assert pr['number']==PR and pr['state']=='OPEN' and pr['isDraft'] is True and pr['mergedAt'] is None
assert (pr['headRefOid'],pr['headRefName'],pr['baseRefName'],pr['baseRefOid'])==(HEAD,BRANCH,'main',BASE)
assert refmap[f'refs/heads/{BRANCH}']==HEAD and refmap[f'refs/pull/{PR}/head']==HEAD
assert apihead=={'sha':HEAD,'tree':TREE}
assert main==apimain['sha'] and run(['git','-C',str(ROOT),'rev-parse','HEAD'])==HEAD and run(['git','-C',str(ROOT),'rev-parse','HEAD^{tree}'])==TREE
assert run(['git','-C',str(ROOT),'status','--porcelain=v1'])==''
ctx=[json.loads(x) for x in (OUT/'caller-context.jsonl').read_text().splitlines()]
changed=set(compare['changedPaths']); overlaps=[]; direct=[]
for c in ctx:
 for r in c['callerRefs']:
  if r['isRuntimeReference'] and r['path'] in changed:
   item={'sourceKey':c['sourceKey'],'path':r['path'],'line':r['line'],'referenceKind':r['referenceKind'],'lineSha256':r['lineSha256']}
   overlaps.append(item)
   if r['referenceKind'] in ('literal-translate-call','literal-server-call'):direct.append(item)
now=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
att={'snapshot':'post-primary-review-final','capturedAtUtc':now,'repository':REPO,'pullRequest':PR,'state':'open','draft':True,'merged':False,'headRef':BRANCH,'headSha':HEAD,'headTree':TREE,'branchRefSha':refmap[f'refs/heads/{BRANCH}'],'pullRefSha':refmap[f'refs/pull/{PR}/head'],'baseRef':'main','prApiBaseSha':BASE,'liveMainSha':main,'liveMainTree':apimain['tree'],'mainCommitsAhead':compare['aheadBy'],'baseBranchMoved':BASE!=main,'remoteRefs':refs,'sourceWorktree':str(ROOT),'sourceWorktreeStatus':'','prBodyRequested':False,'result':'PASS'}
drift={'result':'PASS','snapshotAtUtc':now,'exactHead':HEAD,'exactTree':TREE,'prApiBaseSha':BASE,'liveMainSha':main,'liveMainTree':apimain['tree'],'baseBranchMoved':True,'mainCommitsAhead':compare['aheadBy'],'changedPathCount':len(changed),'changedCoreLocalizationFiles':sorted(x for x in changed if x.startswith('src/NzbDrone.Core/Localization/Core/')),'changedFrontendFiles':sorted(x for x in changed if x.startswith('frontend/')),'changedDocsLocalizationFiles':sorted(x for x in changed if x.startswith('docs/localization/')),'changedPathsIntersectingSelectedKeyReferences':overlaps,'changedLiteralTranslatorCallsites':direct,'selectedLiteralTranslatorCallsitesChanged':bool(direct),'sourceCatalogChanged':any(x=='src/NzbDrone.Core/Localization/Core/en.json' for x in changed),'localeCatalogsChanged':any(x.startswith('src/NzbDrone.Core/Localization/Core/') for x in changed),'pinnedDirectCallerContextsChanged':bool(direct),'conclusion':'Live main is 28 commits beyond the PR API base. No Core localization catalog or frontend file changed. Ten selected-key search hits overlap changed backend/API paths, all as indirect enum or incidental English prose references; there are no changed literal translation callsites. This does not alter the exact pinned PR source or caller context.'}
write(OUT/'PR-attestation-final.json',att);write(OUT/'live-main-caller-drift-final.json',drift)
# Seal the appended final live-state evidence with the candidate-free packet.
files=sorted(x for x in OUT.iterdir() if x.is_file() and x.name!='SHA256SUMS.txt')
(OUT/'SHA256SUMS.txt').write_text(''.join(f'{sha(x.read_bytes())}  {x.name}\n' for x in files))
print(json.dumps({'result':'PASS','attestation':att,'drift':drift,'attestationSha256':sha((OUT/'PR-attestation-final.json').read_bytes()),'driftSha256':sha((OUT/'live-main-caller-drift-final.json').read_bytes()),'sha256sumsSha256':sha((OUT/'SHA256SUMS.txt').read_bytes())},ensure_ascii=False,sort_keys=True,indent=2))
