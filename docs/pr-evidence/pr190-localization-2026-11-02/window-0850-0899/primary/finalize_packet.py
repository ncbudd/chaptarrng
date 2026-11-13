from __future__ import annotations
import collections,datetime,hashlib,json,pathlib,re,subprocess
OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0850-0899-primary-20261102')
WORK=pathlib.Path('/home/keith/Documents/code/task-worktrees/localization-20261102-chaptarrng')
REPO='snapetech-org/ChaptarrNG'; PR=190; BRANCH='codex/chaptarrng-localization-complete-20261031'
HEAD='175cff3a50569b67def345bb82332b30e9bb378c'; TREE='e682581e3c577b62215658c374b15a9d3f8f8bd0'
LOCALE_PATHS={'ar':'src/NzbDrone.Core/Localization/Core/ar.json','de':'src/NzbDrone.Core/Localization/Core/de.json','es':'src/NzbDrone.Core/Localization/Core/es.json','fr':'src/NzbDrone.Core/Localization/Core/fr.json','hi':'src/NzbDrone.Core/Localization/Core/hi.json','id':'src/NzbDrone.Core/Localization/Core/id.json','ja':'src/NzbDrone.Core/Localization/Core/ja.json','ko':'src/NzbDrone.Core/Localization/Core/ko.json','pt-BR':'src/NzbDrone.Core/Localization/Core/pt_BR.json','vi':'src/NzbDrone.Core/Localization/Core/vi.json','zh-Hans':'src/NzbDrone.Core/Localization/Core/zh_CN.json','zh-Hant':'src/NzbDrone.Core/Localization/Core/zh_TW.json'}
ALL=[('snapetech-org/ChaptarrNG',190),('snapetech-org/SeerrNG',418),('snapetech-org/slskR',204),('snapetech-org/QuestarrNG',155),('snapetech-org/TorrentNG',243),('snapetech-org/slskdN',409),('snapetech-org/ROMarrNG',70)]
MANUAL={'850':['Hadouken'],'858':['unmappedFiles.scope'],'880':['Hadouken','5.1'],'882':['0.7.0+'],'885':['RanobeDB'],'890':['all','future','missing','existing','first','latest','none','specificBook'],'891':[';download'],'896':['ast']}
SYNTAX={'884':{'sourceMarkers':["''",'//',"'/'"],'callerMarker':"'\\'",'note':'Empty/sentinel punctuation is preserved in translations; the caller additionally forbids a backslash but the English source catalog omits it.'}}
def sha(b): return hashlib.sha256(b if isinstance(b,bytes) else b.encode()).hexdigest()
def jbytes(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def run(a,text=True): return subprocess.check_output(a,text=text)
def git(*a,text=True): return run(['git','-C',str(WORK),*a],text=text)
def gitshow(path): return git('show',f'{HEAD}:{path}',text=False)
def readj(name): return json.loads((OUT/name).read_text())
def readjl(name): return [json.loads(x) for x in (OUT/name).read_text().splitlines()]
def writej(name,obj): (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
def writejl(name,rows): (OUT/name).write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in rows))
def placeholders(s): return sorted(set(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s)))
def markup(s):
 if re.fullmatch(r'<[^<>/]+>',s): return []
 return re.findall(r'</?[A-Za-z][^>]*>',s)
def ghj(a): return json.loads(run(a))
# Capture and freeze the complete source queue. Its order defines the exact W850-W899 source window.
H=HEAD
ids=json.loads(gitshow('docs/localization/source-followup-20261101.json'))['currentMissingIds']
queue_bytes=json.dumps(ids,ensure_ascii=False,indent=2)+'\n'
(OUT/'current-missing-ids.json').write_text(queue_bytes)
assert len(ids)==1210 and len(set(ids))==1210
assert sha(jbytes(ids))=='a16dd0001c0a36f053bf0207060c338c428dc9beb2e3d929f7d73f19ad004e8c'
selected=ids[850:900]; assert len(selected)==50 and len(set(selected))==50 and not(set(selected)&set(ids[:850]))
input_manifest=readj('input-manifest.json')
input_manifest['sourceQueue']['currentMissingIdsFileSha256']=sha((OUT/'current-missing-ids.json').read_bytes())
input_manifest['sourceQueue']['sourcePositions']=[850,899]
input_manifest['sourceQueue']['selectedSourceIdsSha256']=sha(jbytes(selected))
input_manifest['sourceQueue']['selectedSourceIds']=selected
input_manifest['sourceQueue']['currentMissingIdsSha256']='a16dd0001c0a36f053bf0207060c338c428dc9beb2e3d929f7d73f19ad004e8c'
writej('input-manifest.json',input_manifest)
# Materialize the candidate-only index for quick independent review.
review=readjl('review-cells.jsonl')
candidates=[x for x in review if x['recommendedTarget'] is not None]
writejl('correction-candidates.jsonl',candidates)
writej('manual-protected-literals.json',{'additionalProtectedLiteralsByOrdinal':MANUAL,'syntaxMarkersByOrdinal':SYNTAX,'basis':'Source registry protected literals are retained in every per-cell row. These explicit additions cover product names, request paths, API enum values, version strings, URL suffixes, and field identifiers.'})
# Query all seven open localization PRs and their named remote branches at one UTC timestamp.
heads=[]
for repo,number in ALL:
 pr=ghj(['gh','pr','view',str(number),'--repo',repo,'--json','number,state,isDraft,headRefOid,headRefName,baseRefName,url'])
 branch=pr['headRefName']; owner,name=repo.split('/',1)
 tree=run(['gh','api',f'repos/{repo}/commits/{pr["headRefOid"]}','--jq','.commit.tree.sha']).strip()
 api_ref=ghj(['gh','api',f'repos/{repo}/git/ref/heads/{branch}'])['object']['sha']
 remote_text=run(['git','ls-remote',f'https://github.com/{repo}.git',f'refs/heads/{branch}']).strip()
 remote=remote_text.split()[0] if remote_text else None
 heads.append({'repository':repo,'pullRequest':number,'state':pr['state'],'isDraft':pr['isDraft'],'headRefName':branch,'head':pr['headRefOid'],'tree':tree,'apiBranchRefHead':api_ref,'remoteBranchRef':remote_text,'remoteBranchHead':remote,'apiAndRemoteAgree':api_ref==remote==pr['headRefOid'],'url':pr['url']})
assert all(x['apiAndRemoteAgree'] for x in heads),heads
pr190=next(x for x in heads if x['pullRequest']==190)
assert pr190['state']=='OPEN' and pr190['isDraft'] and pr190['head']==HEAD and pr190['tree']==TREE
head_snapshot={'queriedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':'GitHub PR API + GitHub branch refs + HTTPS git ls-remote','pullRequests':heads}
writej('all-seven-pr-heads.json',head_snapshot)
# Reattest frozen source/cell/catalog/caller/pipeline evidence against the exact live tree.
source_info=input_manifest['sourceCatalog']; source_raw=gitshow(source_info['path']); source=json.loads(source_raw)
assert sha(source_raw)==source_info['sha256'] and git('rev-parse',f'{HEAD}:{source_info["path"]}').strip()==source_info['blob']
follow_info=input_manifest['sourceQueue']; follow_raw=gitshow(follow_info['path']); follow=json.loads(follow_raw)
assert sha(follow_raw)==follow_info['sha256'] and follow['currentMissingIds']==ids
for line in (OUT/'INPUT-SHA256SUMS').read_text().splitlines():
 expected,path=line.split('  ',1); raw=gitshow(path); assert sha(raw)==expected,path
for path,info in input_manifest['localeCatalogs'].items(): pass
catalogs={}; catalog_attest=[]
for locale,path in LOCALE_PATHS.items():
 raw=gitshow(path); obj=json.loads(raw); info=input_manifest['localeCatalogs'][locale]
 assert sha(raw)==info['sha256'] and git('rev-parse',f'{HEAD}:{path}').strip()==info['blob']
 assert set(obj)==set(source)
 catalogs[locale]=obj
 catalog_attest.append({'locale':locale,'path':path,'blob':info['blob'],'sha256':sha(raw),'keyCount':len(obj)})
cell_rows=readjl('input-cells.jsonl'); caller_rows=readjl('caller-context.jsonl'); pipeline=readjl('pipeline-caller-context.jsonl')
assert len(cell_rows)==600 and len(caller_rows)==50 and len(pipeline)==76
assert [x['sourceId'] for x in readjl('source-slice.jsonl')]==selected
for c in cell_rows:
 o=c['sourceOrdinal']; sid=c['sourceId']; loc=c['locale']
 assert c['exactHead']==HEAD and c['exactTree']==TREE and o in range(850,900) and ids[o]==sid
 assert source[sid]==c['source'] and sha(c['source'])==c['sourceTextSha256']
 assert catalogs[loc][sid]==c['currentTarget'] and sha(c['currentTarget'])==c['currentTargetSha256']
 assert c['sourcePlaceholders']==placeholders(c['source']) and c['currentTargetPlaceholders']==placeholders(c['currentTarget'])
 assert c['sourceMarkup']==markup(c['source']) and c['currentTargetMarkup']==markup(c['currentTarget'])
caller_map={x['sourceId']:x for x in caller_rows}
for c in caller_rows:
 assert c['sourceOrdinal'] in range(850,900) and ids[c['sourceOrdinal']]==c['sourceId'] and c['callerRefs']
 for ref in c['callerRefs']:
  raw=gitshow(ref['file']); lines=raw.decode().splitlines(); i=ref['line']-1
  assert sha(raw)==ref['fileSha256'] and git('rev-parse',f'{HEAD}:{ref["file"]}').strip()==ref['fileBlob']
  assert 0<=i<len(lines) and lines[i].strip()==ref['lineText'] and sha(lines[i].strip())==ref['lineSha256']
  assert [v.strip() for v in lines[max(0,i-3):i]]==ref['contextBefore']
  assert [v.strip() for v in lines[i+1:i+1+len(ref['contextAfter'])]]==ref['contextAfter']
for ref in pipeline:
 raw=gitshow(ref['file']); lines=raw.decode().splitlines(); i=ref['line']-1
 assert sha(raw)==ref['fileSha256'] and git('rev-parse',f'{HEAD}:{ref["file"]}').strip()==ref['fileBlob']
 assert lines[i].strip()==ref['lineText'] and sha(lines[i].strip())==ref['lineSha256']
# Independently recheck the cross-window boundary and applied predecessor values.
boundary=readjl('w849-boundary-reattestation.jsonl'); assert len(boundary)==12 and all(x['targetMatchesPreviousFinal'] for x in boundary)
for x in boundary:
 assert x['sourceId']==ids[849] and x['source']==source[x['sourceId']]
 assert catalogs[x['locale']][x['sourceId']]==x['liveTarget'] and sha(x['liveTarget'])==x['liveTargetSha256']
assert len(readjl('w800-w849-applied-reattestation.jsonl'))==600
prior=readj('prior-disposition-boundary.json')
assert prior['priorPositionsCovered']['complete'] and prior['priorOverlapCount']==0 and prior['w849All12MatchCrossReviewFinalAndLiveCatalog']
assert len(readjl('prior-disposition-hashes.jsonl'))==10200
# Verify every generated primary decision and exact candidate target.
for row in review:
 c=next(x for x in cell_rows if x['sourceOrdinal']==row['sourceOrdinal'] and x['locale']==row['locale'])
 assert row['sourceId']==c['sourceId'] and row['sourceTextSha256']==c['sourceTextSha256'] and row['currentTargetSha256']==c['currentTargetSha256']
 if row['recommendedTarget'] is not None:
  assert sha(row['recommendedTarget'])==row['recommendedTargetSha256']
  assert placeholders(row['recommendedTarget'])==placeholders(row['source'])
  assert markup(row['recommendedTarget'])==markup(row['source'])
 if row['finalTarget'] is not None:
  assert sha(row['finalTarget'])==row['finalTargetSha256']
assert len(candidates)==79
assert all(x['sourceOrdinal']==884 and x['disposition']=='hold' and x['finalTarget'] is None for x in review if x['sourceOrdinal']==884)
assert all(x['callerSourceMessageMismatch'] for x in review if x['sourceOrdinal']==884)
# Final live pin after all reads and review generation.
pr_final=ghj(['gh','pr','view','190','--repo',REPO,'--json','number,state,isDraft,headRefOid,headRefName,baseRefOid,url'])
final_tree=run(['gh','api',f'repos/{REPO}/commits/{pr_final["headRefOid"]}','--jq','.commit.tree.sha']).strip()
final_ref=ghj(['gh','api',f'repos/{REPO}/git/ref/heads/{BRANCH}'])['object']['sha']
final_remote=run(['git','-C',str(WORK),'ls-remote','github',f'refs/heads/{BRANCH}']).split()[0]
state={'head':git('rev-parse','HEAD').strip(),'tree':git('rev-parse','HEAD^{tree}').strip(),'branch':git('branch','--show-current').strip(),'status':git('status','--porcelain').strip()}
assert pr_final['state']=='OPEN' and pr_final['isDraft'] and pr_final['headRefOid']==HEAD and final_tree==TREE and final_ref==final_remote==HEAD
assert state=={'head':HEAD,'tree':TREE,'branch':BRANCH,'status':''}
final_attest={'passed':True,'finalizedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repository':REPO,'pullRequest':PR,'livePullRequest':pr_final,'head':HEAD,'tree':TREE,'githubBranchRefHead':final_ref,'githubRemoteBranchHead':final_remote,'worktree':state,'sourceQueueCount':len(ids),'sourceQueueSha256':sha(jbytes(ids)),'selectedSourceIds':50,'selectedSourcePositions':[850,899],'localeCells':len(cell_rows),'catalogs':catalog_attest,'sourceCallerRows':len(caller_rows),'sourceCallerReferences':sum(len(x['callerRefs']) for x in caller_rows),'sourceCallerGaps':[],'genericPipelineReferences':len(pipeline),'genericPipelineGaps':[],'w849BoundaryRows':len(boundary),'w849BoundaryMatches':12,'priorDispositionRows':10200,'priorOverlapCount':0,'candidateRows':len(candidates),'decisionRows':len(review),'repositoryModified':False,'testsBuildsCiBrowserRun':False}
writej('final-reattestation.json',final_attest)
# Human-readable artifact inventory and explicit limitations.
summary=readj('summary.json')
readme=f'''# ChaptarrNG PR #190 primary semantic review — W850–W899

This scratch-only packet reviews 50 source IDs at queue positions 850–899 across all 12 direct locales (600 cells). PR #190 was OPEN/DRAFT at `{HEAD}` / tree `{TREE}` when the exact source and catalogs were frozen and again at finalization. All seven live localization PR refs were queried; the matching API, branch-ref, and HTTPS remote heads are recorded in `all-seven-pr-heads.json`.

## Review results

- Accept current: {summary['dispositionCounts']['accept-current']}
- Correction candidates: {summary['correctionCandidates']}
- Refinement candidates: {summary['refinementCandidates']}
- Holds: {summary['holdCount']}
- Candidate target hashes, source/caller pins, protected-literal checks, placeholders, and markup are in `review-cells.jsonl` and `protected-literal-integrity.jsonl`.
- Re-attested caller context: {summary['sourceCallerReferences']} references across {summary['sourceCallerRows']} source rows; gaps: 0. Generic server-message display pipeline refs: {summary['genericPipelineReferences']}; gaps: 0.
- Placeholder mismatches: {summary['placeholderMismatchCells']}; markup mismatches: {summary['markupMismatchCells']}; protected-literal failures in proposed targets: {summary['protectedLiteralFailureCells']}.
- The W849 boundary matches all 12 previously cross-reviewed final targets at the current head. All 600 W800–W849 applied targets were re-attested against the live catalogs. Prior review coverage through W849 is recorded as 10,200 exact cell dispositions, with zero overlap against this window.

## Hold and limits

All 12 W884 cells are held. The English source catalog says `Can not contain '', '//', or start/end with '/'`, but the exact qBittorrent caller also forbids `\\`. The translation source omits this instruction. Align the source and caller first, then review all 12 translations again. The exact caller text and hashes are included in the cell rows and `primary-findings.json`.

This is machine-assisted static semantic review with moderate confidence. Native-speaker review remains outstanding. No repository or PR files were changed; no tests, builds, CI, or browser work were run.

## Build and limits

`prepare_input.py` freezes the source/catalog/caller rows. `reconcile_prior.py` verifies the checksummed W800 evidence and replaces the temporary compatibility scan with the complete 10,200-cell predecessor ledger through W849. Then `make_primary_review.py` records all 600 decisions and `finalize_packet.py` reattests the head and checksums the packet.

## Exact evidence

- Source queue: `current-missing-ids.json` contains the pinned 1,210-ID list; its canonical ordered-list SHA-256 is `{sha(jbytes(ids))}`.
- Source slice and current values: `source-slice.jsonl`, `input-cells.jsonl`.
- Caller and display-pipeline context: `caller-context.jsonl`, `pipeline-caller-context.jsonl`.
- Prior dispositions and boundary readback: `prior-disposition-hashes.jsonl`, `prior-disposition-boundary.json`, `w849-boundary-reattestation.jsonl`, and `w800-w849-applied-reattestation.jsonl`.
- Final live state: `final-reattestation.json`; checksums: `SHA256SUMS`.
'''
(OUT/'README.md').write_text(readme)
# Build manifest over every artifact except manifest and checksum file, then sums over every file except sums.
files=[]
for p in sorted(OUT.iterdir()):
 if p.is_file() and p.name not in ('manifest.json','SHA256SUMS'):
  files.append({'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())})
manifest={'schemaVersion':1,'repository':REPO,'pullRequest':PR,'head':HEAD,'tree':TREE,'branch':BRANCH,'window':'W850-W899','positions':[850,899],'sourceCount':50,'localeCount':12,'cellCount':600,'candidateCount':79,'dispositionCounts':summary['dispositionCounts'],'priorDispositionRows':10200,'priorOverlapCount':0,'w849BoundaryMatches':12,'nativeSpeakerApproval':False,'machineAssistedConfidence':'moderate','files':files,'finalReattestationSha256':sha((OUT/'final-reattestation.json').read_bytes()),'sourceQueueCanonicalSha256':sha(jbytes(ids))}
writej('manifest.json',manifest)
sums=[]
for p in sorted(OUT.iterdir()):
 if p.is_file() and p.name!='SHA256SUMS': sums.append(f'{sha(p.read_bytes())}  {p.name}')
(OUT/'SHA256SUMS').write_text('\n'.join(sums)+'\n')
# Verify manifest file list and whole-directory sums.
for item in files:
 assert sha((OUT/item['path']).read_bytes())==item['sha256']
for line in (OUT/'SHA256SUMS').read_text().splitlines():
 h,name=line.split('  ',1); assert sha((OUT/name).read_bytes())==h,name
print(json.dumps({'packet':str(OUT),'files':len(files)+2,'manifestSha256':sha((OUT/'manifest.json').read_bytes()),'sha256sumsSha256':sha((OUT/'SHA256SUMS').read_bytes()),'rows':len(review),'candidates':len(candidates),'counts':summary['dispositionCounts'],'head':HEAD,'tree':TREE,'cleanWorktree':not bool(state['status'])},indent=2))
