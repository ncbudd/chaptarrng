from __future__ import annotations
import collections,datetime,hashlib,json,pathlib,re,subprocess,time
OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0900-0949-primary-20261102')
WORK=pathlib.Path('/home/keith/Documents/code/task-worktrees/localization-20261102-chaptarrng')
REPO='snapetech-org/ChaptarrNG'; PR=190; BRANCH='codex/chaptarrng-localization-complete-20261031'
HEAD='a9a74f6ba733e8c1f06a2d260bd802d4fde2da0e'; TREE='d9d25f309f3a7256056b4ed8deb1dabee58b64fe'
ALL=[('snapetech-org/ChaptarrNG',190),('snapetech-org/SeerrNG',418),('snapetech-org/slskR',204),('snapetech-org/QuestarrNG',155),('snapetech-org/TorrentNG',243),('snapetech-org/slskdN',409),('snapetech-org/ROMarrNG',70)]
LOCALES={'ar':'ar.json','de':'de.json','es':'es.json','fr':'fr.json','hi':'hi.json','id':'id.json','ja':'ja.json','ko':'ko.json','pt-BR':'pt_BR.json','vi':'vi.json','zh-Hans':'zh_CN.json','zh-Hant':'zh_TW.json'}
SRC='src/NzbDrone.Core/Localization/Core/en.json'; FOLLOW='docs/localization/source-followup-20261101.json'
def sha(b): return hashlib.sha256(b if isinstance(b,bytes) else b.encode()).hexdigest()
def jbytes(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def run(a,text=True):
 err=None
 for attempt in range(3):
  try: return subprocess.check_output(a,text=text,stderr=subprocess.PIPE)
  except subprocess.CalledProcessError as e:
   err=e
   if attempt<2: time.sleep(2)
 raise err
def git(*a,text=True): return run(['git','-C',str(WORK),*a],text=text)
def show(path): return git('show',f'{HEAD}:{path}',text=False)
def readj(n): return json.loads((OUT/n).read_text())
def readjl(n): return [json.loads(x) for x in (OUT/n).read_text().splitlines()]
def writej(n,x): (OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
def verify_sums(folder):
 sums=folder/'SHA256SUMS'; assert sums.is_file(),folder
 for line in sums.read_text().splitlines():
  h,n=line.split('  ',1); assert sha((folder/n).read_bytes())==h,(folder,n)
 return sha(sums.read_bytes())
def query_all():
 out=[]
 for repo,num in ALL:
  p=json.loads(run(['gh','pr','view',str(num),'--repo',repo,'--json','number,state,isDraft,headRefOid,headRefName,baseRefName,url']))
  b=p['headRefName']; tree=run(['gh','api',f'repos/{repo}/commits/{p["headRefOid"]}','--jq','.commit.tree.sha']).strip() if num==PR else None
  ref=json.loads(run(['gh','api',f'repos/{repo}/git/ref/heads/{b}']))['object']['sha']
  rt=run(['git','ls-remote',f'https://github.com/{repo}.git',f'refs/heads/{b}']).strip()
  remote=rt.split()[0] if rt else None
  out.append({'repository':repo,'pullRequest':num,'state':p['state'],'isDraft':p['isDraft'],'branch':b,'head':p['headRefOid'],'tree':tree,'apiBranchRefHead':ref,'remoteBranchRef':rt,'remoteBranchHead':remote,'apiAndRemoteAgree':ref==remote==p['headRefOid'],'url':p['url']})
 assert all(x['apiAndRemoteAgree'] for x in out),out
 pr=next(x for x in out if x['pullRequest']==PR)
 assert pr['state']=='OPEN' and pr['isDraft'] and pr['head']==HEAD and pr['tree']==TREE and pr['branch']==BRANCH,pr
 return {'queriedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'GitHub PR API, commit-tree API for #190, branch-ref API, HTTPS git ls-remote','pullRequests':out}
def state():
 return {'head':git('rev-parse','HEAD').strip(),'tree':git('rev-parse','HEAD^{tree}').strip(),'branch':git('branch','--show-current').strip(),'status':git('status','--porcelain').strip()}
def placeholders(s): return sorted(set(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s)))
def markup(s):
 if re.fullmatch(r'<[^<>/]+>',s): return []
 return re.findall(r'</?[A-Za-z][^>]*>',s)
assert state()=={'head':HEAD,'tree':TREE,'branch':BRANCH,'status':''}
# Re-query all refs after semantic review; #190 must still match the frozen input.
heads=query_all(); writej('all-seven-pr-heads-final.json',heads)
m=readj('input-manifest.json'); files=readj('pinned-files.json')['files']
assert m['head']==HEAD and m['tree']==TREE
for f in files:
 raw=show(f['path'])
 assert sha(raw)==f['sha256'] and git('rev-parse',f'{HEAD}:{f["path"]}').strip()==f['blob'],f['path']
ids=json.loads(show(FOLLOW))['currentMissingIds']
assert ids==readj('current-missing-ids.json') and len(ids)==1210
assert sha(jbytes(ids))=='a16dd0001c0a36f053bf0207060c338c428dc9beb2e3d929f7d73f19ad004e8c'
selected=ids[900:950]; source=json.loads(show(SRC))
srcrows=readjl('source-slice.jsonl'); cells=readjl('input-cells.jsonl'); callers=readjl('caller-context.jsonl')
assert len(selected)==len(srcrows)==len(callers)==50 and len(cells)==600
assert [x['sourceId'] for x in srcrows]==selected and [x['sourceOrdinal'] for x in srcrows]==list(range(900,950))
for r in srcrows: assert source[r['sourceId']]==r['source'] and sha(r['source'])==r['sourceTextSha256']
# Exact locale catalog values and cell hashes.
catalogs={}
for loc,filename in LOCALES.items():
 path=f'src/NzbDrone.Core/Localization/Core/{filename}'
 raw=show(path); obj=json.loads(raw); info=m['localeCatalogs'][loc]
 assert sha(raw)==info['sha256'] and git('rev-parse',f'{HEAD}:{path}').strip()==info['blob'] and set(obj)==set(source)
 catalogs[loc]=obj
for c in cells:
 assert c['exactHead']==HEAD and c['exactTree']==TREE and ids[c['sourceOrdinal']]==c['sourceId']
 assert source[c['sourceId']]==c['source']
 assert catalogs[c['locale']][c['sourceId']]==c['currentTarget'] and sha(c['currentTarget'])==c['currentTargetSha256']
# Direct caller line, file, and adjacent context pins.
caller_summary=readj('caller-context-summary.json')
assert sum(x['callerReferenceCount'] for x in callers)==86 and not caller_summary['callerGaps'] and not caller_summary['staleRegistryPins']
for group in callers:
 assert group['callerReferenceStatus']=='pinned' and group['callerReferenceCount']==len(group['directCallerReferences'])
 for ref in group['directCallerReferences']:
  raw=show(ref['file']); lines=raw.decode().splitlines(); i=ref['line']-1
  assert sha(raw)==ref['fileSha256'] and git('rev-parse',f'{HEAD}:{ref["file"]}').strip()==ref['fileBlob']
  assert lines[i].strip()==ref['lineText'] and sha(lines[i].strip())==ref['lineSha256']
  assert [x.strip() for x in lines[max(0,i-3):i]]==ref['contextBefore']
  assert [x.strip() for x in lines[i+1:i+1+len(ref['contextAfter'])]]==ref['contextAfter']
server_pipeline=readjl('server-message-pipeline-context.jsonl'); provider_pipeline=readjl('provider-option-pipeline-context.jsonl')
assert len(server_pipeline)==76 and len(provider_pipeline)==20
for ref in server_pipeline+provider_pipeline:
 raw=show(ref['file']); lines=raw.decode().splitlines(); i=ref['line']-1
 assert sha(raw)==ref['fileSha256'] and git('rev-parse',f'{HEAD}:{ref["file"]}').strip()==ref['fileBlob']
 assert lines[i].strip()==ref['lineText'] and sha(lines[i].strip())==ref['lineSha256']
# Prior packets and boundary.
p850=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0850-0899-primary-20261102')
x850=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0850-0899-crossreview-20261102')
p850_sum=verify_sums(p850); x850_sum=verify_sums(x850)
prior=readjl('prior-disposition-hashes.jsonl'); boundary=readjl('w899-boundary-reattestation.jsonl')
assert len(prior)==10800 and len(boundary)==12 and all(x['liveMatchesPriorCrossReviewFinal'] for x in boundary)
assert len({(x['sourceOrdinal'],x['locale']) for x in prior})==10800
for x in boundary:
 assert catalogs[x['locale']][x['sourceId']]==x['liveTarget'] and sha(x['liveTarget'])==x['liveTargetSha256']
assert sum(x['liveTargetMatchesPriorFinalHash'] for x in prior)==readj('prior-disposition-boundary.json')['priorLiveCatalogMatchesFinalCount']
# Source-884 evidence is context only, not reopened by this window.
w884=readj('source-884-followup-context.json')
assert sha(pathlib.Path(w884['path']).read_bytes())==w884['sha256'] and w884['outsideSelectedPositions']
assert source.get(w884['record']['sourceId'])==w884['currentSourceText']
# All cell decisions and proposal structure.
review=readjl('review-cells.jsonl'); audit=readjl('language-audit.jsonl')
assert len(review)==len(audit)==600
assert {(x['sourceOrdinal'],x['locale']) for x in review}=={(x['sourceOrdinal'],x['locale']) for x in cells}
for r in review:
 c=next(x for x in cells if x['sourceOrdinal']==r['sourceOrdinal'] and x['locale']==r['locale'])
 assert r['currentTargetSha256']==c['currentTargetSha256'] and sha(r['currentTarget'])==r['currentTargetSha256']
 assert r['sourceTextSha256']==c['sourceTextSha256'] and r['sourceId']==c['sourceId']
 assert r['disposition'] in {'accept-current','correction','refinement','hold'}
 if r['recommendedTarget'] is not None:
  assert r['recommendedTarget']!=r['currentTarget'] and sha(r['recommendedTarget'])==r['recommendedTargetSha256']
  assert placeholders(r['recommendedTarget'])==placeholders(r['source'])
  assert markup(r['recommendedTarget'])==markup(r['source'])
 if r['disposition']=='accept-current': assert r['finalTarget']==r['currentTarget']
 elif r['disposition']=='hold': assert r['finalTarget'] is None
 else: assert r['finalTarget']==r['recommendedTarget']
 assert r['finalTarget'] is None or sha(r['finalTarget'])==r['finalTargetSha256']
 assert not r['structuralChecks']['recommendedProtectedLiteralFailures']
 assert not r['structuralChecks']['finalProtectedLiteralFailures']
assert all(x['languageAuditDisposition']==next(r['disposition'] for r in review if r['sourceOrdinal']==x['sourceOrdinal'] and r['locale']==x['locale']) for x in audit)
summary=readj('summary.json'); counts=collections.Counter(x['disposition'] for x in review)
assert dict(sorted(counts.items()))==summary['dispositionCounts']
assert counts=={'accept-current':478,'correction':71,'refinement':51}
assert state()=={'head':HEAD,'tree':TREE,'branch':BRANCH,'status':''}
# Re-query again after verification to bound the final input state.
heads_end=query_all(); writej('all-seven-pr-heads-after-review.json',heads_end)
headmap={x['pullRequest']:x['head'] for x in heads['pullRequests']}
endmap={x['pullRequest']:x['head'] for x in heads_end['pullRequests']}
assert next(x for x in heads_end['pullRequests'] if x['pullRequest']==PR)['head']==HEAD
assert state()=={'head':HEAD,'tree':TREE,'branch':BRANCH,'status':''}
final={'passed':True,'finalizedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repository':REPO,'pullRequest':PR,'pullRequestState':'OPEN','isDraft':True,'head':HEAD,'tree':TREE,'branch':BRANCH,'finalWorktreeState':state(),'allSevenPRHeadRequeryAfterReview':heads_end,'allSevenHeadsUnchangedBetweenFinalChecks':headmap==endmap,'sourceQueueCanonicalSha256':sha(jbytes(ids)),'sourceWindowPositions':[900,949],'sourceIds':50,'directLocales':12,'reviewedCells':len(review),'decisionCounts':dict(sorted(counts.items())),'recommendationCount':counts['correction']+counts['refinement'],'sourceCallerRows':len(callers),'sourceCallerReferences':86,'sourceCallerGaps':0,'staleCallerPins':0,'serverMessagePipelineReferences':len(server_pipeline),'providerOptionPipelineReferences':len(provider_pipeline),'localeCatalogsReattested':len(catalogs),'priorDispositionRows':len(prior),'priorCatalogValuesMatchingRecordedFinalHash':sum(x['liveTargetMatchesPriorFinalHash'] for x in prior),'priorCatalogValuesNotMatchingRecordedFinalHash':sum(not x['liveTargetMatchesPriorFinalHash'] for x in prior),'priorPositionCoverage':[0,899],'priorOverlapCount':0,'w899BoundaryRows':len(boundary),'w899BoundaryMatches':12,'w884FollowupReopened':False,'placeholderMismatchCells':summary['placeholderMismatchCells'],'markupMismatchCells':summary['markupMismatchCells'],'currentProtectedLiteralFailureCells':summary['currentProtectedLiteralFailureCells'],'recommendedProtectedLiteralFailureCells':summary['recommendedProtectedLiteralFailureCells'],'repositoryOrPRModified':False,'testsBuildsScansCiBrowserRun':False,'nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True,'machineAssistedConfidence':'moderate'}
writej('final-reattestation.json',final)
readme=f'''# ChaptarrNG PR #190 primary semantic review - W900-W949

This scratch-only review covers queue positions 900-949: 50 source IDs x 12 direct locales = 600 cells. These are zero-based positions in the exact currentMissingIds list from docs/localization/source-followup-20261101.json; they are not catalog-key ordinals. PR #190 was OPEN/DRAFT at {HEAD} / tree {TREE} at input freeze and final reattestation. All seven localization PR refs were queried before and after the review; each PR API head, branch API ref, and HTTPS remote branch agreed in the recorded snapshots.

## Decisions

- Accept current: {counts['accept-current']}
- Correction candidates: {counts['correction']}
- Refinement candidates: {counts['refinement']}
- Holds: {counts['hold']}
- Placeholder and markup mismatches in final proposals: 0
- Protected-literal failures in proposals: 0
- Current values missing an explicit protected term: {summary['currentProtectedLiteralFailureCells']}; all are resolved in proposed corrections.

review-cells.jsonl is the per-cell decision ledger. correction-candidates.jsonl and refinement-candidates.jsonl contain exact proposed targets and hashes. language-audit.jsonl is the full 600-cell language-review export of this same primary pass; it is not an independent second review. protected-literal-integrity.jsonl records current, proposed, and final placeholder, markup, and literal checks.

## Source and caller evidence

All 50 exact English sources and 12 complete locale catalogs were reattested. Direct caller context covers {len(callers)} source rows and 86 exact caller references, with zero gaps or stale caller pins. Server-message display evidence covers {len(server_pipeline)} pinned references. Provider-option rendering/localization evidence covers {len(provider_pipeline)} pinned code references, including enum FieldOption, server-side SchemaBuilder/ILocalizationService localization, and the frontend select display path.

The W899 boundary matches all 12 prior cross-review final targets at the frozen head. Prior review packets cover positions 0-899 with 10,800 exact cell records and no queue-position overlap. At this head, {final['priorCatalogValuesMatchingRecordedFinalHash']} current prior-window values match their recorded prior final hashes and {final['priorCatalogValuesNotMatchingRecordedFinalHash']} do not; every comparison is retained in prior-disposition-hashes.jsonl. Those older differences are recorded, not reopened by this window.

The source-884 backslash/source correction and its specific language follow-up remain separate and outside W900-W949. This packet does not reopen any source-884 locale decision.

## Scope and limits

This is a machine-assisted static primary review with moderate confidence. Native-speaker review remains outstanding. No repository or PR files were edited, and no tests, builds, scans, CI, or browser work were run.

## Evidence files

- input-manifest.json, current-missing-ids.json, source-slice.jsonl: exact queue and source slice.
- input-cells.jsonl and pinned-files.json: exact current targets, hashes, catalog blobs, and file pins.
- caller-context.jsonl, server-message-pipeline-context.jsonl, provider-option-pipeline-context.jsonl: caller and runtime display context.
- prior-disposition-hashes.jsonl, prior-disposition-boundary.json, w899-boundary-reattestation.jsonl: prior decisions and boundary.
- source-884-followup-context.json: context-only out-of-window source correction record.
- all-seven-pr-heads-*.json and final-reattestation.json: live ref checks.
- manifest.json and SHA256SUMS: file integrity.
'''
(OUT/'README.md').write_text(readme)
manifest_files=[]
for p in sorted(OUT.iterdir()):
 if p.is_file() and p.name not in {'manifest.json','SHA256SUMS'}:
  manifest_files.append({'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())})
manifest={'schemaVersion':1,'repository':REPO,'pullRequest':PR,'state':'OPEN','isDraft':True,'head':HEAD,'tree':TREE,'branch':BRANCH,'window':'W900-W949','queuePositions':[900,949],'queueSemantics':'zero-based currentMissingIds positions, not catalog key ordinals','sourceCount':50,'localeCount':12,'cellCount':600,'decisionCounts':dict(sorted(counts.items())),'candidateCount':counts['correction']+counts['refinement'],'priorDispositionRows':len(prior),'priorOverlapCount':0,'w899BoundaryMatches':12,'directCallerReferences':86,'serverMessagePipelineReferences':len(server_pipeline),'providerOptionPipelineReferences':len(provider_pipeline),'nativeSpeakerApproval':False,'machineAssistedConfidence':'moderate','finalReattestationSha256':sha((OUT/'final-reattestation.json').read_bytes()),'sourceQueueCanonicalSha256':sha(jbytes(ids)),'files':manifest_files}
writej('manifest.json',manifest)
sums=[]
for p in sorted(OUT.iterdir()):
 if p.is_file() and p.name!='SHA256SUMS': sums.append(f'{sha(p.read_bytes())}  {p.name}')
(OUT/'SHA256SUMS').write_text('\n'.join(sums)+'\n')
for item in manifest_files: assert sha((OUT/item['path']).read_bytes())==item['sha256'],item['path']
for line in (OUT/'SHA256SUMS').read_text().splitlines():
 h,n=line.split('  ',1); assert sha((OUT/n).read_bytes())==h,n
print(json.dumps({'packet':str(OUT),'manifestSha256':sha((OUT/'manifest.json').read_bytes()),'sha256sumsSha256':sha((OUT/'SHA256SUMS').read_bytes()),'fileCount':len(manifest_files)+2,'summary':summary,'finalHead':HEAD,'finalTree':TREE,'worktreeClean':state()['status']==''},ensure_ascii=False,indent=2))
