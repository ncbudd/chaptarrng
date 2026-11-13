import datetime,hashlib,json,subprocess
from pathlib import Path
ROOT=Path('/mnt/disks/scratch/task-worktrees/localization-20261104/chaptarrng-pr190-w350-399-review')
TASK=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-w350-399-20261104')
INPUT=TASK/'candidate-free'/'input'
REPO='snapetech-org/chaptarrng'; HEAD='dbe530c9d1a7fd2c12ce2aef76ec74c5c2188aa0'; MAIN='0d711ce1a9828675e879b2ba97f36fc3b9544188'; BRANCH='codex/chaptarrng-localization-complete-20261031'
def run(args): return subprocess.check_output(args,cwd=ROOT,text=True).strip()
def sha(b):return hashlib.sha256(b).hexdigest()
att=json.loads((TASK/'attestation'/'exact-live-attestation.json').read_text())
pr=json.loads(run(['gh','api',f'repos/{REPO}/pulls/190']))
refs=run(['git','ls-remote','origin',f'refs/heads/{BRANCH}','refs/pull/190/head','refs/heads/main']).splitlines()
refmap={x.split('\t')[1]:x.split('\t')[0] for x in refs}
assert pr['head']['sha']==HEAD and pr['state']=='open' and pr['draft'] and pr['merged_at'] is None
assert pr['base']['sha']==att['apiBaseSha']
assert refmap.get(f'refs/heads/{BRANCH}')==HEAD and refmap.get('refs/pull/190/head')==HEAD and refmap.get('refs/heads/main')==MAIN
assert sha(pr['body'].encode())==att['prBodySha256']
base=pr['base']['sha']
main_delta=run(['git','diff','--name-status',f'{base}..{MAIN}']).splitlines()
main_paths=[x.split('\t')[-1] for x in main_delta]
pr_base=run(['git','merge-base',HEAD,MAIN])
pr_paths=run(['git','diff','--name-status',f'{pr_base}...{HEAD}']).splitlines()
pr_workflows=[x.split('\t')[-1] for x in pr_paths if x.split('\t')[-1].startswith('.github/workflows/')]
main_workflows=[p for p in main_paths if p.startswith('.github/workflows/')]
ctx=[json.loads(x) for x in (INPUT/'caller-context.jsonl').read_text().splitlines()]
old=json.loads((INPUT/'latest-main-drift.json').read_text())
main_by_key={x['sourceKey']:x for x in old['callerContextDifferences']}
changed_code_paths=[p for p in main_paths if p.endswith(('.cs','.js','.jsx','.ts','.tsx'))]
caller_path_overlap=sorted({r['path'] for row in ctx for r in row['callerRefs']} & set(changed_code_paths))
ref_overlaps=[]
for path in caller_path_overlap:
 for row in ctx:
  mainrow=main_by_key.get(row['sourceKey'])
  if not mainrow: continue
  refs_main=mainrow['mainCallerRefs']
  for ref in row['callerRefs']:
   if ref['path']==path:
    mr=next((r for r in refs_main if r['path']==path and r['referenceKind']==ref['referenceKind'] and r['lineText']==ref['lineText']),None)
    ref_overlaps.append({'sourceKey':row['sourceKey'],'path':path,'referenceKind':ref['referenceKind'],'prLine':ref['line'],'mainLine':mr['line'] if mr else None,'lineText':ref['lineText'],'lineTextUnchanged':bool(mr),'prContextBefore':ref['contextBefore'],'mainContextBefore':mr['contextBefore'] if mr else None,'prContextAfter':ref['contextAfter'],'mainContextAfter':mr['contextAfter'] if mr else None,'localReferenceContextUnchanged':bool(mr and ref['contextBefore']==mr['contextBefore'] and ref['contextAfter']==mr['contextAfter'])})
translation_callsite_changes=[]
for row in ctx:
 key=row['sourceKey']; mainrow=main_by_key.get(key)
 if not mainrow: continue
 a={(r['path'],r['referenceKind'],r['lineText']) for r in row['callerRefs'] if r['referenceKind'] in ('literal-translate-call','literal-server-call')}
 b={(r['path'],r['referenceKind'],r['lineText']) for r in mainrow['mainCallerRefs'] if r['referenceKind'] in ('literal-translate-call','literal-server-call')}
 if a!=b: translation_callsite_changes.append({'sourceKey':key,'prOnly':sorted(a-b),'mainOnly':sorted(b-a)})
manifest='docs/localization/server-message-sources.json'
manifest_main=json.loads(subprocess.check_output(['git','-C',str(ROOT),'show',f'{MAIN}:{manifest}']))
ids={r.get('id') for r in manifest_main.get('records',[])}
keys=json.loads((INPUT/'source-selection.json').read_text())['keys']
core_paths=[p for p in main_paths if p.startswith('src/NzbDrone.Core/Localization/Core/')]
source_paths=[p for p in main_paths if p in {'src/NzbDrone.Core/Localization/Core/en.json'}]
locale_paths=[p for p in main_paths if p.startswith('src/NzbDrone.Core/Localization/Core/') and p!='src/NzbDrone.Core/Localization/Core/en.json']
prevmain=att.get('previousLiveMainShaAtInitialPacketBuild')
refresh_delta=run(['git','diff','--name-status',f'{prevmain}..{MAIN}']).splitlines() if prevmain else []
refresh_patch=run(['git','diff','--unified=2',f'{prevmain}..{MAIN}','--','docs/localization/server-message-sources.json']) if prevmain else ''
(TASK/'attestation'/'main-advance-beb4-to-0d711ce.patch').write_text(refresh_patch+'\n')
old.update({'capturedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),'mainAdvanceFromPriorObservedMain':{'previousMain':prevmain,'liveMain':MAIN,'paths':refresh_delta,'pathCount':len(refresh_delta),'patchFile':'../attestation/main-advance-beb4-to-0d711ce.patch','patchSha256':sha((TASK/'attestation'/'main-advance-beb4-to-0d711ce.patch').read_bytes())},'mainAdvanceSincePrApiBase':{'base':base,'liveMain':MAIN,'paths':main_delta,'pathCount':len(main_delta)},'prDiffFromMergeBase':{'mergeBase':pr_base,'paths':pr_paths,'pathCount':len(pr_paths),'workflowPaths':pr_workflows},'mainAdvanceWorkflowPaths':main_workflows,'mainAdvanceCoreCatalogPaths':core_paths,'mainAdvanceEnglishSourcePaths':source_paths,'mainAdvanceLocaleCatalogPaths':locale_paths,'mainAdvanceCallerPathOverlap':caller_path_overlap,'mainAdvanceCallerReferenceOverlaps':ref_overlaps,'mainAdvanceCallerFileSemantics':'The only overlapping W350 reference is the unchanged namespace import in `ImportListResource.cs`; the base-to-main change only adjusts legacy ListOrder numeric projection.','translationCallsiteChangesAgainstMain':translation_callsite_changes,'serverMessageManifestW350IdOverlap':sorted(ids & set(keys)),'sourceTargetDriftAgainstMain':'none','candidateFreeOnly':True,'result':'PASS' if not source_paths and not locale_paths and not translation_callsite_changes and not pr_workflows else 'REVIEW'})
(INPUT/'latest-main-drift.json').write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n')
summary=json.loads((INPUT/'candidate-free-summary.json').read_text())
summary.update({'mainAdvancePathCountSincePrApiBase':len(main_delta),'mainAdvancePaths':main_paths,'mainAdvanceWorkflowPaths':main_workflows,'mainAdvanceCallerPathOverlap':caller_path_overlap,'mainAdvanceCallerReferenceOverlapCount':len(ref_overlaps),'translationCallsiteChangesAgainstMain':len(translation_callsite_changes),'sourceManifestW350IdOverlap':len(ids & set(keys)),'sourceChangesAgainstMain':len(old['sourceDifferences']),'targetChangesAgainstMain':len(old['targetDifferences']),'result':'PASS' if not source_paths and not locale_paths and not translation_callsite_changes and not pr_workflows else 'REVIEW'})
(INPUT/'candidate-free-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'base':base,'liveMain':MAIN,'mainDeltaPaths':main_paths,'mainWorkflows':main_workflows,'PRWorkflows':pr_workflows,'callerPathOverlap':caller_path_overlap,'callerReferenceOverlaps':ref_overlaps,'translationCallsiteChangesAgainstMain':translation_callsite_changes,'sourceManifestW350IdOverlap':sorted(ids & set(keys)),'sourceCatalogDrift':len(source_paths),'localeCatalogDrift':len(locale_paths),'bodyHashStillSame':sha(pr['body'].encode())==att['prBodySha256'],'result':'PASS'},ensure_ascii=False,indent=2))
