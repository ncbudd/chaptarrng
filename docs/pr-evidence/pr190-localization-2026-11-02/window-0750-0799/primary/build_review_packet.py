import collections,hashlib,json,pathlib,re,subprocess
OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0750-0799-primary-20261102')
WORK=pathlib.Path('/mnt/disks/scratch/task-worktrees/localization-20261102/chaptarrng-pr190-readonly-0750-0799-a58de8c')
PRIOR=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0700-0749-primary-20261102')
CROSS=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0700-0749-crossreview-independent-20261102')
REPO='snapetech-org/chaptarrng'; PR=190
HEAD='a58de8cd62a80babdca07a86d6b7d463b4a44773'; TREE='3baf8c11efe42c617a286cd37665e946303c6d2a'
LOCALES=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
def sha(x): return hashlib.sha256(x if isinstance(x,bytes) else x.encode()).hexdigest()
def jbytes(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def writej(name,obj): (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
def writejl(name,rows): (OUT/name).write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in rows))
def run(args,text=True,cwd=None): return subprocess.check_output(args,text=text,cwd=cwd)
def git(*args,text=True): return run(['git','-C',str(WORK),*args],text=text)
def readgit(path): return git('show',f'{HEAD}:{path}',text=False)
def live_pr():
 p=json.loads(run(['gh','pr','view',str(PR),'--repo',REPO,'--json','state,isDraft,headRefOid,headRefName,baseRefOid,url']))
 t=run(['gh','api',f'repos/{REPO}/commits/{p["headRefOid"]}','--jq','.commit.tree.sha']).strip()
 r=run(['git','ls-remote',f'https://github.com/{REPO}.git',f'refs/heads/{p["headRefName"]}']).split()[0]
 return p,t,r
def verify_checksums(path):
 for line in (path/'SHA256SUMS').read_text().splitlines():
  digest,name=line.split('  ',1); fp=path/name
  assert fp.is_file() and sha(fp.read_bytes())==digest,(path/name)
 return sha((path/'SHA256SUMS').read_bytes())
def placeholders(s): return sorted(set(re.findall(r'\{[^{}]+\}',s)))
def markup(s):
 if re.fullmatch(r'<[^<>/]+>',s): return []
 return re.findall(r'</?[A-Za-z][^>]*>',s)
# Verify PR, ref, tree, and clean exact-head worktree before finalizing the ledger.
pr,api_tree,remote=live_pr()
assert pr['state']=='OPEN' and pr['isDraft'] and pr['headRefOid']==HEAD and api_tree==TREE and remote==HEAD
assert git('rev-parse','HEAD').strip()==HEAD and git('rev-parse','HEAD^{tree}').strip()==TREE and not git('status','--porcelain').strip()
input_check=run(['sha256sum','-c',str(OUT/'INPUT-SHA256SUMS')],cwd=str(WORK))
prior_hash=verify_checksums(PRIOR); cross_hash=verify_checksums(CROSS)
ps=json.loads((PRIOR/'summary.json').read_text()); xs=json.loads((CROSS/'summary.json').read_text())
assert (ps['exactHead'],ps['exactTree'])==('02f0d841b54c7806005fc67973973799c6960bcf','eab2516e48adf4586f14cb131dc1ca6876f87e5f')
assert (xs['exactHead'],xs['exactTree'])==(ps['exactHead'],ps['exactTree'])
recon=json.loads((OUT/'prior-w700-reconciliation.json').read_text())
assert recon['primaryAndCrossReviewChecksumsVerified'] and recon['liveTargetsMatchCrossReviewFinal']==600 and recon['liveTargetDiffs']==[] and recon['sourceChangesCount']==0
input_manifest=json.loads((OUT/'input-manifest.json').read_text())
source_rows=[json.loads(x) for x in (OUT/'source-slice.jsonl').read_text().splitlines()]
cells=[json.loads(x) for x in (OUT/'input-cells.jsonl').read_text().splitlines()]
ctxs=[json.loads(x) for x in (OUT/'caller-context.jsonl').read_text().splitlines()]
pipeline=[json.loads(x) for x in (OUT/'pipeline-caller-context.jsonl').read_text().splitlines()]
plan=json.loads((OUT/'review-plan.json').read_text())
assert len(source_rows)==50 and len(cells)==600 and len(ctxs)==50 and len(pipeline)==76 and len(plan)==600
assert input_manifest['head']==HEAD and input_manifest['tree']==TREE and input_manifest['scope']['positions']==[750,799] and input_manifest['scope']['cells']==600
source_ids=json.loads(readgit('docs/localization/source-followup-20261101.json'))['currentMissingIds']
assert [x['sourceId'] for x in source_rows]==source_ids[750:800]
assert not set(x['sourceId'] for x in source_rows)&set(source_ids[:750])
source=json.loads(readgit('src/NzbDrone.Core/Localization/Core/en.json'))
loc_files={'es':'es.json','zh-Hans':'zh_CN.json','hi':'hi.json','de':'de.json','ja':'ja.json','fr':'fr.json','pt-BR':'pt_BR.json','ar':'ar.json','ko':'ko.json','zh-Hant':'zh_TW.json','vi':'vi.json','id':'id.json'}
catalogs={l:json.loads(readgit(f'src/NzbDrone.Core/Localization/Core/{f}')) for l,f in loc_files.items()}
# Reattest W749 source, current target, exact previous cross-review final, and caller pin.
w749=[json.loads(x) for x in (OUT/'w749-boundary-reattestation.jsonl').read_text().splitlines()]
assert len(w749)==12; w749_caller_refs=0
for b in w749:
 assert b['sourceOrdinal']==749 and source[b['sourceId']]==b['source'] and sha(b['source'])==b['sourceTextSha256']
 assert catalogs[b['locale']][b['sourceId']]==b['liveTarget']==b['priorCrossReviewFinalTarget']
 assert sha(b['liveTarget'])==b['liveTargetSha256']==b['priorCrossReviewFinalTargetSha256']
 for ref in b['callerContext']:
  raw=readgit(ref['file']); lines=raw.decode().splitlines(); n=ref['line']
  assert sha(raw)==ref['currentFileSha256'] and git('rev-parse',f'HEAD:{ref["file"]}').strip()==ref['currentFileBlob']
  assert 1<=n<=len(lines) and lines[n-1].strip()==ref['currentLineText'] and sha(lines[n-1].strip())==ref['currentLineSha256']
  w749_caller_refs+=1
assert len({(x['sourceId'],x['locale']) for x in cells})==600
ctxmap={x['sourceId']:x for x in ctxs}
for c in cells:
 assert source[c['sourceId']]==c['source'] and sha(c['source'])==c['sourceTextSha256']
 assert catalogs[c['locale']][c['sourceId']]==c['currentTarget'] and sha(c['currentTarget'])==c['currentTargetSha256']
 assert ctxmap[c['sourceId']]['callerContextSha256']==c['callerContextSha256']
for context in ctxs:
 for ref in context['callerRefs']:
  raw=readgit(ref['file']); lines=raw.decode().splitlines(); n=ref['line']
  assert 1<=n<=len(lines) and lines[n-1].strip()==ref['currentLineText'] and sha(lines[n-1].strip())==ref['currentLineSha256']
  assert sha(raw)==ref['currentFileSha256'] and git('rev-parse',f'HEAD:{ref["file"]}').strip()==ref['currentFileBlob']
for ref in pipeline:
 raw=readgit(ref['file']); lines=raw.decode().splitlines(); n=ref['line']
 assert 1<=n<=len(lines) and lines[n-1].strip()==ref['lineText'] and sha(lines[n-1].strip())==ref['lineSha256']
 assert sha(raw)==ref['fileSha256'] and git('rev-parse',f'HEAD:{ref["file"]}').strip()==ref['fileBlob']
input_rows={(x['sourceOrdinal'],x['locale']):x for x in cells}
ledger=[]; candidates=[]; literals=[]; counts=collections.Counter(); per=collections.defaultdict(collections.Counter)
for key,entry in plan.items():
 o=int(key.split('|')[0]); loc=key.split('|')[1]; c=input_rows[(o,loc)]
 assert (entry['sourceId'],entry['sourceTextSha256'],entry['currentTargetSha256'])==(c['sourceId'],c['sourceTextSha256'],c['currentTargetSha256'])
 final=entry['finalTarget']; assert final is None or sha(final)==entry['finalTargetSha256']
 assert entry['callerContextSha256']==c['callerContextSha256'] and entry['placeholderParity'] and entry['markupParity']
 if final is not None:
  for lit in entry['protectedLiterals']:
   if lit in c['source']: assert lit in final,(o,loc,lit)
 row={**c,**entry,'exactHead':HEAD,'exactTree':TREE,'sourceCatalogBlob':source_rows[o-750]['sourceCatalogBlob'],'sourceCatalogSha256':source_rows[o-750]['sourceCatalogSha256'],'sourceRegistryCallerContext':ctxmap[c['sourceId']]}
 ledger.append(row); counts[entry['disposition']]+=1; per[loc][entry['disposition']]+=1
 literals.append({'exactHead':HEAD,'exactTree':TREE,'sourceOrdinal':o,'sourceId':c['sourceId'],'locale':loc,'source':c['source'],'sourceTextSha256':c['sourceTextSha256'],'currentTarget':c['currentTarget'],'currentTargetSha256':c['currentTargetSha256'],'finalTarget':final,'finalTargetSha256':entry['finalTargetSha256'],'protectedChecks':entry['protectedLiteralChecks'],'currentMismatches':[x['literal'] for x in entry['protectedLiteralChecks'] if x['presentInSource'] and not x['presentInCurrentTarget']],'finalMismatches':[x['literal'] for x in entry['protectedLiteralChecks'] if x['presentInSource'] and final is not None and x['literal'] not in final],'placeholderParity':entry['placeholderParity'],'markupParity':entry['markupParity']})
 if entry['disposition']=='propose-correction': candidates.append(row)
assert len(ledger)==600
for k in ('accept-current','propose-correction','propose-refinement','hold'): counts.setdefault(k,0)
current_ph_mismatch=sum(not x['placeholderParity'] for x in cells); current_markup_mismatch=sum(not x['markupParity'] for x in cells)
final_ph_mismatch=sum(not x['placeholderParity'] for x in ledger); final_markup_mismatch=sum(not x['markupParity'] for x in ledger)
current_protected=sum(bool(x['currentMismatches']) for x in literals); final_protected=sum(bool(x['finalMismatches']) for x in literals)
writejl('review-cells.jsonl',ledger); writejl('primary-review-ledger.jsonl',ledger); writejl('correction-candidates.jsonl',candidates); writejl('protected-literal-integrity.jsonl',literals)
writej('review-decisions.json',{'schemaVersion':1,'reviewerRole':'primary semantic reviewer','scope':[750,799],'candidateCount':len(candidates),'dispositionCounts':dict(counts),'sourceRationales':json.loads((OUT/'manual-protected-literals.json').read_text())['rationalesByOrdinal'],'nativeSpeakerApproval':False})
writej('reviewer-provenance.json',{'reviewerRole':'primary semantic reviewer','reviewType':'source/caller-context-aware semantic and terminology review of every frozen locale cell','exactHead':HEAD,'exactTree':TREE,'sourceIds':50,'localeCells':600,'locales':LOCALES,'evidence':['English source catalog','12 locale catalogs','exact-head server-message source registry with reattested current caller refs','exact-head frontend server-message display callsites','W749 prior cross-review final target and caller-boundary reattestation','W700 primary and independent cross-review checksum reattestation'],'protectedLiteralPolicy':'Preserve placeholders, API field names, provider/product names, protocol values, enum tokens, file extensions, URLs, and endpoint paths; translate ordinary user-facing labels and prose.','nativeSpeakerApproval':False,'browserReview':False,'repositoryModified':False,'testsBuildsCiRun':False,'workflowFilesTouched':False})
source_hash=sha(jbytes([{'sourceOrdinal':x['sourceOrdinal'],'sourceId':x['sourceId'],'source':x['source']} for x in source_rows]))
source_icu=sum(bool(re.search(r'\{[^{}]+,\s*(?:plural|select|selectordinal)\s*,',x['source'])) for x in source_rows)
summary={'schemaVersion':1,'repository':REPO,'pullRequest':PR,'exactHead':HEAD,'exactTree':TREE,'livePullRequest':pr,'remoteBranchHead':remote,'scope':{'positions':[750,799],'sourceIds':50,'locales':LOCALES,'cells':600},'sourceIdListSha256':input_manifest['selectedSourceIdListSha256'],'sourceWindowSha256':source_hash,'counts':dict(counts),'proposalCount':len(candidates),'holdCount':counts['hold'],'perLocale':{loc:dict(per[loc]) for loc in LOCALES},'confidenceCounts':dict(collections.Counter(x['confidence'] for x in ledger)),'sourceCallerRows':len(ctxs),'sourceCallerReferences':sum(len(x['callerRefs']) for x in ctxs),'sourceCallerFiles':len({r['file'] for x in ctxs for r in x['callerRefs']}),'sourceCallerGaps':json.loads((OUT/'caller-context-summary.json').read_text())['sourceCallerGaps'],'genericPipelineReferences':len(pipeline),'genericPipelineFiles':len({x['file'] for x in pipeline}),'genericPipelineGaps':json.loads((OUT/'caller-context-summary.json').read_text())['genericPipelineGaps'],'staleRegistryPinsRefreshed':json.loads((OUT/'caller-context-summary.json').read_text())['staleRegistryPinsRefreshed'],'placeholderSources':sum(bool(placeholders(x['source'])) for x in source_rows),'icuSources':source_icu,'currentPlaceholderMismatches':current_ph_mismatch,'finalPlaceholderMismatches':final_ph_mismatch,'markupSources':sum(bool(markup(x['source'])) for x in source_rows),'currentMarkupMismatches':current_markup_mismatch,'finalMarkupMismatches':final_markup_mismatch,'protectedLiteralChecks':len(literals),'currentProtectedMismatchCells':current_protected,'finalProtectedMismatchCells':final_protected,'priorW700':recon,'priorW700PrimarySha256SUMS':prior_hash,'priorW700CrossReviewSha256SUMS':cross_hash,'priorDispositionBoundary':json.loads((OUT/'prior-disposition-boundary.json').read_text()),'w749BoundaryRows':len(w749),'w749BoundaryCallerRefs':w749_caller_refs,'inputChecksumValidation':'passed','inputChecksumCommandOutputLines':len(input_check.splitlines()),'nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True,'browserReview':False,'repositoryModified':False,'testsBuildsCiRun':False,'workflowFilesTouched':False,'releasesTagsMergesPerformed':False}
writej('summary.json',summary)
# Final exact-head/ref/worktree reattestation, after all source/caller checks and ledger generation.
pr2,tree2,remote2=live_pr(); state={'head':git('rev-parse','HEAD').strip(),'tree':git('rev-parse','HEAD^{tree}').strip(),'status':git('status','--porcelain').strip()}
assert pr2['state']=='OPEN' and pr2['isDraft'] and pr2['headRefOid']==HEAD and tree2==TREE and remote2==HEAD and state=={'head':HEAD,'tree':TREE,'status':''}
writej('final-reattestation.json',{'passed':True,'head':HEAD,'tree':TREE,'livePullRequest':pr2,'remoteBranchHead':remote2,'repositoryState':state,'sourceIds':50,'localeCells':600,'candidates':len(candidates),'holds':counts['hold'],'sourceCallerRefs':summary['sourceCallerReferences'],'sourceCallerFiles':summary['sourceCallerFiles'],'genericPipelineRefs':len(pipeline),'genericPipelineFiles':summary['genericPipelineFiles'],'priorW700TargetsMatchCrossReview':600,'w749BoundaryRows':len(w749),'w749BoundaryCallerRefs':w749_caller_refs})
README=f'''# ChaptarrNG PR #190 primary semantic review: W750–799

This packet reviews 50 source IDs across 12 locales (600 current locale cells).

## Exact input pin

PR #190 remains OPEN/DRAFT at `{HEAD}` / tree `{TREE}` on `{pr2['headRefName']}`. The GitHub API, remote branch, and detached exact-head worktree were rechecked before and after ledger generation; the worktree is clean. Ordinals use `currentMissingIds` from `docs/localization/source-followup-20261101.json`.

W700 primary and independent cross-review packet checksums validate. At this head, all 600 W700 locale values match the independent cross-review final targets, with no W700 source changes. W749's source, caller pin, and 12 live locale targets match the prior cross-review boundary. W750–799 has no overlap with earlier source IDs.

## Review results

- Decisions: {dict(counts)}; {len(candidates)} proposed corrections and {counts['hold']} holds.
- Source callers: {summary['sourceCallerReferences']} exact references across {summary['sourceCallerFiles']} files for all 50 source rows, with no caller gaps. Three stale source-registry line pins were refreshed against the exact-head production sources (759, 761, 763).
- Generic frontend server-message display path: {len(pipeline)} line references across {summary['genericPipelineFiles']} files; no gaps.
- Current and final placeholder mismatches: {current_ph_mismatch}/{final_ph_mismatch}. Current and final markup mismatches: {current_markup_mismatch}/{final_markup_mismatch}.
- Protected literal mismatch cells: current {current_protected}, final {final_protected}; the candidates preserve exact placeholders, property/enum tokens, provider names, URL schemes, and other recorded literals.

`review-cells.jsonl` and `primary-review-ledger.jsonl` contain one row per locale cell with exact source/current/final strings and hashes, caller context, rationale, confidence, placeholder/markup parity, and protected-literal checks. `correction-candidates.jsonl` contains each proposed target. `prior-w700-reconciliation.json` and `w749-boundary-reattestation.jsonl` preserve prior-window and boundary evidence.

Machine review is complete for this window; native-speaker approval remains outstanding. No repository or PR files were changed; no tests, builds, scans, CI, browser actions, workflows, releases, tags, or merges were run.
'''
(OUT/'README.md').write_text(README)
# Include hashes and byte sizes in a manifest; checksums then cover the manifest and every other packet file.
manifest={'schemaVersion':1,'repository':REPO,'pullRequest':PR,'head':HEAD,'tree':TREE,'scope':[750,799],'sourceCount':50,'cellCount':600,'candidateCount':len(candidates),'holdCount':counts['hold'],'sourceIdListSha256':input_manifest['selectedSourceIdListSha256'],'sourceInputs':input_manifest,'packetFiles':[]}
for fp in sorted(OUT.iterdir()):
 if fp.is_file() and fp.name not in ('manifest.json','SHA256SUMS'):
  manifest['packetFiles'].append({'path':fp.name,'bytes':fp.stat().st_size,'sha256':sha(fp.read_bytes())})
writej('manifest.json',manifest)
names=sorted(p.name for p in OUT.iterdir() if p.is_file() and p.name!='SHA256SUMS')
(OUT/'SHA256SUMS').write_text(''.join(f'{sha((OUT/n).read_bytes())}  {n}\n' for n in names))
print(json.dumps({'head':HEAD,'tree':TREE,'counts':dict(counts),'candidates':len(candidates),'holds':counts['hold'],'sourceCallerRefs':summary['sourceCallerReferences'],'sourceCallerFiles':summary['sourceCallerFiles'],'callerGaps':summary['sourceCallerGaps'],'genericPipelineRefs':len(pipeline),'genericPipelineFiles':summary['genericPipelineFiles'],'currentPlaceholderMarkupMismatch':[current_ph_mismatch,current_markup_mismatch],'finalPlaceholderMarkupMismatch':[final_ph_mismatch,final_markup_mismatch],'currentProtectedMismatchCells':current_protected,'finalProtectedMismatchCells':final_protected,'w749BoundaryCallerRefs':w749_caller_refs,'reattestPassed':True},ensure_ascii=False,indent=2))
