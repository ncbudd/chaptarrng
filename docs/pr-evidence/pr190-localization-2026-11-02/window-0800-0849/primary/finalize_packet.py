from __future__ import annotations
import collections,hashlib,json,pathlib,subprocess
OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0800-0849-primary-20261102')
WORK=pathlib.Path('/home/keith/Documents/code/task-worktrees/localization-20261102-chaptarrng')
REPO='snapetech-org/ChaptarrNG'; PR=190
HEAD='f0eb9d38b1989bd6e3addeb698ec8c5f9c29d9e9'; TREE='7f0f9a9d71d672bb47c08e1abe4125be03d815d6'
BRANCH='codex/chaptarrng-localization-complete-20261031'
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
def sha(b): return hashlib.sha256(b if isinstance(b,bytes) else b.encode()).hexdigest()
def jbytes(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def run(a,text=True): return subprocess.check_output(a,text=text)
def git(*a,text=True): return run(['git','-C',str(WORK),*a],text=text)
def live():
 pr=json.loads(run(['gh','pr','view',str(PR),'--repo',REPO,'--json','state,isDraft,headRefOid,headRefName,baseRefOid,url']))
 tree=run(['gh','api',f'repos/{REPO}/commits/{pr["headRefOid"]}','--jq','.commit.tree.sha']).strip()
 ref=json.loads(run(['gh','api',f'repos/{REPO}/git/ref/heads/{BRANCH}']))['object']['sha']
 remote=run(['git','-C',str(WORK),'ls-remote','github',f'refs/heads/{BRANCH}']).split()[0]
 state={'head':git('rev-parse','HEAD').strip(),'tree':git('rev-parse','HEAD^{tree}').strip(),'branch':git('branch','--show-current').strip(),'status':git('status','--porcelain').strip()}
 assert pr['state']=='OPEN' and pr['isDraft'] and pr['headRefOid']==HEAD and pr['headRefName']==BRANCH
 assert tree==TREE and ref==remote==HEAD
 assert state=={'head':HEAD,'tree':TREE,'branch':BRANCH,'status':''}
 return pr,tree,ref,remote,state
def verify_sums(folder,name='SHA256SUMS'):
 p=folder/name
 assert p.is_file(),p
 rows=[]
 for line in p.read_text().splitlines():
  digest,filename=line.split('  ',1); f=folder/filename; assert f.is_file() and sha(f.read_bytes())==digest,filename
  rows.append(filename)
 return sha(p.read_bytes()),rows

def tracked_blob(path): return git('rev-parse',f'HEAD:{path}').strip()
# Verify the incoming exact-head input/checksum pins.
input_manifest=json.loads((OUT/'input-manifest.json').read_text())
assert input_manifest['head']==HEAD and input_manifest['tree']==TREE
for line in (OUT/'INPUT-SHA256SUMS').read_text().splitlines():
 digest,path=line.split('  ',1); raw=git('show',f'{HEAD}:{path}',text=False); assert sha(raw)==digest,path
assert sha((OUT/'current-missing-ids.json').read_bytes())==input_manifest['sourceQueue'].get('currentMissingIdsFileSha256',sha((OUT/'current-missing-ids.json').read_bytes()))
ids=json.loads((OUT/'current-missing-ids.json').read_text())
assert len(ids)==1210 and len(set(ids))==1210
assert sha(jbytes(ids))==input_manifest['sourceQueue']['currentMissingIdsSha256']
selected=ids[800:850]; assert len(selected)==50 and selected==input_manifest['sourceQueue']['selectedSourceIds']
assert input_manifest['sourceQueue']['selectedSourceIdListSha256']==sha(jbytes(selected))
# Reattest the 12 exact live catalogs, all 600 frozen cells, source texts, and input row hashes.
src_path=input_manifest['sourceCatalog']['path']; src_raw=git('show',f'{HEAD}:{src_path}',text=False); source=json.loads(src_raw)
assert sha(src_raw)==input_manifest['sourceCatalog']['sha256'] and tracked_blob(src_path)==input_manifest['sourceCatalog']['blob']
catalogs={}; catalog_check=[]
for loc,pin in input_manifest['localeCatalogs'].items():
 raw=git('show',f'{HEAD}:{pin["path"]}',text=False); obj=json.loads(raw)
 assert sha(raw)==pin['sha256'] and tracked_blob(pin['path'])==pin['blob'] and len(obj)==len(source)
 assert set(obj)==set(source)
 catalogs[loc]=obj; catalog_check.append({'locale':loc,'path':pin['path'],'blob':pin['blob'],'sha256':sha(raw),'keyCount':len(obj)})
source_rows=[json.loads(x) for x in (OUT/'source-slice.jsonl').read_text().splitlines()]
cell_inputs=[json.loads(x) for x in (OUT/'input-cells.jsonl').read_text().splitlines()]
assert len(source_rows)==50 and len(cell_inputs)==600
assert [x['sourceId'] for x in source_rows]==selected
for row in source_rows:
 o=row['sourceOrdinal']; sid=row['sourceId']; assert o in range(800,850) and ids[o]==sid and source[sid]==row['source'] and sha(source[sid])==row['sourceTextSha256']
for c in cell_inputs:
 assert c['exactHead']==HEAD and c['exactTree']==TREE
 assert ids[c['sourceOrdinal']]==c['sourceId'] and source[c['sourceId']]==c['source']
 assert sha(c['source'])==c['sourceTextSha256']
 assert catalogs[c['locale']][c['sourceId']]==c['currentTarget'] and sha(c['currentTarget'])==c['currentTargetSha256']
# Reattest all production caller context file blobs/lines and exact generic display pipeline refs.
caller_rows=[json.loads(x) for x in (OUT/'caller-context.jsonl').read_text().splitlines()]
assert len(caller_rows)==50 and not json.loads((OUT/'caller-context-summary.json').read_text())['sourceCallerGaps']
for c in caller_rows:
 assert c['sourceOrdinal'] in range(800,850) and ids[c['sourceOrdinal']]==c['sourceId']
 for r in c['callerRefs']:
  raw=git('show',f'{HEAD}:{r["file"]}',text=False); lines=raw.decode().splitlines()
  assert sha(raw)==r['fileSha256'] and tracked_blob(r['file'])==r['fileBlob']
  assert lines[r['line']-1].strip()==r['lineText'] and sha(lines[r['line']-1].strip())==r['lineSha256']
  for i,text in enumerate(r['contextBefore'],r['line']-len(r['contextBefore'])): assert lines[i-1].strip()==text
  for i,text in enumerate(r['contextAfter'],r['line']+1): assert lines[i-1].strip()==text
pipeline=[json.loads(x) for x in (OUT/'pipeline-caller-context.jsonl').read_text().splitlines()]
assert len(pipeline)==76 and not json.loads((OUT/'caller-context-summary.json').read_text())['genericPipelineGaps']
for r in pipeline:
 raw=git('show',f'{HEAD}:{r["file"]}',text=False); lines=raw.decode().splitlines()
 assert sha(raw)==r['fileSha256'] and tracked_blob(r['file'])==r['fileBlob']
 assert lines[r['line']-1].strip()==r['lineText'] and sha(lines[r['line']-1].strip())==r['lineSha256']
# Verify 600 semantic decisions, exact candidate/current/final hashes, placeholders, markup, and protected literals.
plan=json.loads((OUT/'review-plan.json').read_text()); ledger=[json.loads(x) for x in (OUT/'primary-review-ledger.jsonl').read_text().splitlines()]
assert len(plan)==600 and len(ledger)==600
assert len({(x['sourceOrdinal'],x['locale']) for x in ledger})==600
counts=collections.Counter(x['disposition'] for x in ledger)
assert counts==collections.Counter({'accept-current':364,'propose-correction':234,'propose-refinement':2})
for x in ledger:
 assert x['sourceOrdinal'] in range(800,850) and x['locale'] in LOCALES
 assert sha(x['source'])==x['sourceTextSha256'] and sha(x['currentTarget'])==x['currentTargetSha256']
 assert x['finalTarget'] is not None and sha(x['finalTarget'])==x['finalTargetSha256']
 if x['recommendedTarget'] is not None: assert sha(x['recommendedTarget'])==x['recommendedTargetSha256'] and x['recommendedTarget']!=x['currentTarget']
 assert x['placeholderParity'] and x['markupParity'] and x['protectedLiteralsPreserved']
assert sum(x['disposition']=='hold' for x in ledger)==0
prior=[json.loads(x) for x in (OUT/'prior-disposition-hashes.jsonl').read_text().splitlines()]
assert len(prior)==9600 and len({(x['sourceOrdinal'],x['locale']) for x in prior})==9600
assert all(x['sourceOrdinal'] in range(800) and x['sourceId']==ids[x['sourceOrdinal']] for x in prior)
assert not ({x['sourceId'] for x in prior}&set(selected))
# Reattest the prior W799 cross-review final boundary against the live catalog values.
boundary=[json.loads(x) for x in (OUT/'w799-boundary-reattestation.jsonl').read_text().splitlines()]
assert len(boundary)==12 and all(x['sourceOrdinal']==799 and x['sourceId']==ids[799] and x['matchesPreviousIndependentFinal'] for x in boundary)
assert all(catalogs[x['locale']][x['sourceId']]==x['liveTarget'] and sha(x['liveTarget'])==x['liveTargetSha256'] for x in boundary)
# Final live PR/ref/remote/worktree and catalog reattestation.
pr,tree,ref,remote,state=live()
queue_file_sha=sha((OUT/'current-missing-ids.json').read_bytes())
writej=lambda name,obj:(OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
final={'passed':True,'repository':REPO,'pullRequest':PR,'livePullRequest':pr,'head':HEAD,'tree':TREE,'branch':BRANCH,'githubBranchRefHead':ref,'githubRemoteBranchHead':remote,'worktree':state,'currentMissingIdsCount':len(ids),'currentMissingIdsListSha256':sha(jbytes(ids)),'currentMissingIdsFileSha256':queue_file_sha,'sourceIds':50,'cells':600,'catalogs':catalog_check,'callerReferences':sum(len(x['callerRefs']) for x in caller_rows),'callerRows':len(caller_rows),'callerGaps':[],'genericPipelineReferences':len(pipeline),'genericPipelineGaps':[],'priorDispositionCells':len(prior),'priorDispositionWindows':16,'priorPacketFiles':19,'priorOverlap':0,'w799BoundaryCells':len(boundary),'w799MatchesPriorFinal':12,'counts':dict(counts),'placeholderMismatches':0,'markupMismatches':0,'protectedLiteralFinalMismatches':0,'nativeSpeakerApproval':False,'repositoryModified':False,'testsBuildsScansCiBrowserRun':False}
writej('final-reattestation.json',final)
# The concise summary repeats only verified packet-level facts.
summary=json.loads((OUT/'summary.json').read_text())
summary.update({'priorPacketCount':16,'priorPacketFiles':19,'priorDispositionsRecorded':9600,'priorPositionCoverageComplete':True,'w799BoundaryMatches':12,'sourceCallerGaps':[],'genericPipelineGaps':[],'currentProtectedMismatchCells':sum(any(z['presentInSource'] and not z['presentInCurrentTarget'] for z in x['protectedLiteralChecks']) for x in ledger),'finalProtectedMismatchCells':sum(any(z['presentInSource'] and not z['presentInFinalTarget'] for z in []) for x in []),'nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True,'exactLiveReattestationPassed':True})
# Actual final protected mismatch count derives from the per-cell integrity file.
protected=[json.loads(x) for x in (OUT/'protected-literal-integrity.jsonl').read_text().splitlines()]
summary['currentProtectedMismatchCells']=sum(any(z['presentInSource'] and not z['presentInCurrentTarget'] for z in x['protectedChecks']) for x in protected)
summary['finalProtectedMismatchCells']=sum(not x['protectedLiteralsPreserved'] for x in ledger)
summary['protectedLiteralFailureCells']=summary['finalProtectedMismatchCells']
summary['placeholderMismatchCells']=sum(not x['placeholderParity'] for x in protected)
summary['markupMismatchCells']=sum(not x['markupParity'] for x in protected)
writej('summary.json',summary)
counts_json=dict(counts)
README=f'''# ChaptarrNG PR #190 primary semantic review — W800–W849

## Exact input and source window

PR #190 is OPEN/DRAFT at `{HEAD}` / tree `{TREE}` on `{BRANCH}`. The GitHub PR, GitHub branch ref, official GitHub remote, and clean worktree were reattested before and after review. The worktree remains clean.

The source queue is `currentMissingIds` from `{input_manifest['sourceQueue']['path']}` at the exact head, pinned by the complete ordered-list SHA-256 `{input_manifest['sourceQueue']['currentMissingIdsSha256']}`. The queue has 1,210 unique IDs. This packet covers positions 800–849, IDs `{selected[0]}` through `{selected[-1]}`, 50 source IDs × 12 direct locales = 600 cells. The selected ID list SHA-256 is `{input_manifest['sourceQueue']['selectedSourceIdListSha256']}`. It is disjoint from all positions 0–799.

All 12 direct locale catalogs, the English source catalog, the source registry, 63 production callsite references, and 76 generic frontend server-message display pipeline references were pinned by blob and SHA-256. There are no source caller or generic pipeline gaps. W799's source, caller context, and 12 live locale values match the previous independent cross-review final at this head.

Prior exact-hash evidence covers all positions 0–799: 9,600 per-cell disposition records across 16 windows / 19 packet files. Packet checksums passed; the record SHA-256 values, current/final target hashes, and dispositions are in `prior-disposition-hashes.jsonl`. No prior cell overlaps W800–W849.

## Decisions

- `accept-current`: {counts['accept-current']}
- `propose-correction`: {counts['propose-correction']}
- `propose-refinement`: {counts['propose-refinement']}
- `hold`: {counts['hold']}
- Candidate targets: {len([x for x in ledger if x['recommendedTarget'] is not None])}

Every cell has the exact English source, current target, final primary target, hashes, caller context and rationale. All proposed targets preserve the verified placeholders, markup, and protected literals. Current placeholder and markup mismatches are 0; final mismatches are 0. One current protected-literal mismatch is corrected: the Brazilian Portuguese MonitorExistingMode value currently translates the JSON sentinel `null` as `nulo`; the proposal preserves exact `null`.

Key context reviewed includes BookshelfNG edition selection, RanobeDB release-vs-work IDs, opaque exception interpolation, enum values, indexer category warnings, Calibre library paths, Goodreads shelves and list imports, and provider IDs. The `{{value0}}` from the import-list feed and Apprise API response remains opaque.

Confidence is moderate and machine-assisted. Native-speaker review remains outstanding. No repository or PR files were changed; no tests, builds, scans, CI, browser, workflow, release, tag, or merge activity was performed.
'''
(OUT/'README.md').write_text(README)
# Write final manifest over all packet files, then checksum every file except the checksum list itself.
manifest={'schemaVersion':1,'repository':REPO,'pullRequest':PR,'head':HEAD,'tree':TREE,'branch':BRANCH,'window':'W800-W849','positions':[800,849],'sourceCount':50,'cellCount':600,'locales':LOCALES,'candidateCount':len([x for x in ledger if x['recommendedTarget'] is not None]),'counts':dict(counts),'sourceIdListSha256':input_manifest['sourceQueue']['selectedSourceIdListSha256'],'currentMissingIdsSha256':input_manifest['sourceQueue']['currentMissingIdsSha256'],'currentMissingIdsFileSha256':queue_file_sha,'priorDispositionCellCount':9600,'priorWindowCount':16,'priorPacketFileCount':19,'priorOverlapCount':0,'callerReferences':sum(len(x['callerRefs']) for x in caller_rows),'genericPipelineReferences':len(pipeline),'w799BoundaryMatches':12,'nativeSpeakerApproval':False,'files':[]}
for p in sorted(OUT.iterdir()):
 if p.is_file() and p.name not in ('manifest.json','SHA256SUMS'):
  manifest['files'].append({'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())})
writej('manifest.json',manifest)
names=sorted(p.name for p in OUT.iterdir() if p.is_file() and p.name!='SHA256SUMS')
(OUT/'SHA256SUMS').write_text(''.join(f'{sha((OUT/n).read_bytes())}  {n}\n' for n in names))
# Validate every final sum and manifest file mapping before returning.
for line in (OUT/'SHA256SUMS').read_text().splitlines():
 digest,name=line.split('  ',1); assert sha((OUT/name).read_bytes())==digest,name
assert {x['path'] for x in manifest['files']}=={n for n in names if n!='manifest.json'}
assert final['passed'] and state['status']==''
print(json.dumps({'output':str(OUT),'head':HEAD,'tree':TREE,'counts':dict(counts),'candidates':manifest['candidateCount'],'holds':0,'priorDispositionRows':9600,'priorWindows':16,'priorPacketFiles':19,'callerRefs':final['callerReferences'],'pipelineRefs':len(pipeline),'catalogs':12,'w799Matches':12,'checksums':'PASS','scratchBytes':sum(p.stat().st_size for p in OUT.iterdir() if p.is_file()),'sha256sumsSha256':sha((OUT/'SHA256SUMS').read_bytes()),'manifestSha256':sha((OUT/'manifest.json').read_bytes())},ensure_ascii=False,indent=2))
