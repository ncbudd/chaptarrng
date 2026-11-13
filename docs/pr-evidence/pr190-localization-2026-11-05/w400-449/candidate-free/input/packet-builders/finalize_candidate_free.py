#!/usr/bin/env python3
import hashlib,json,shutil
from pathlib import Path
TASK=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-w400-449-20261105')
OUT=TASK/'candidate-free'/'input'
def sha(b):return hashlib.sha256(b).hexdigest()
def j(name):return json.loads((OUT/name).read_text())
def wj(name,obj):(OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def call_sig(rows):
 return {(r['path'],r.get('referenceKind'),r['lineText']) for r in rows if r.get('isRuntimeReference') and r.get('referenceKind') in ('literal-translate-call','literal-server-call')}
def dynamic_sig(rows):
 return {(r['path'],r['callExpression'],r['argumentExpression'],r['lineText']) for r in rows}
(OUT/'packet-builders').mkdir(exist_ok=True)
shutil.copy2(TASK/'build_candidate_free.py',OUT/'packet-builders'/'build_candidate_free.py')
shutil.copy2(TASK/'attestation'/'build_reattestation.py',OUT/'packet-builders'/'attest_prior_window.py')
shutil.copy2(TASK/'attestation'/'finalize_candidate_free.py',OUT/'packet-builders'/'finalize_candidate_free.py')
att=j('PR-attestation.json'); att['headTree']=att['headTree']; att['capturedAtUtc']=att.get('capturedAtUtc'); wj('PR-attestation.json',att)
drift=j('latest-main-drift.json')
drift['prWorkflowTree']=att['headWorkflowTree'];drift['liveMainWorkflowTree']=att['liveMainWorkflowTree']
drift['mainWorkflowTreeChangedAgainstPr']=att['headWorkflowTree']!=att['liveMainWorkflowTree']
drift['mainAdvanceWorkflowPaths']=[x.split('\t')[-1] for x in drift['mainAdvanceSincePrApiBase']['paths'] if x.split('\t')[-1].startswith('.github/workflows/')]
drift['mainAdvanceCoreCatalogPaths']=[x.split('\t')[-1] for x in drift['mainAdvanceSincePrApiBase']['paths'] if '/Localization/Core/' in x.split('\t')[-1]]
drift['mainAdvanceEnglishSourcePaths']=[x.split('\t')[-1] for x in drift['mainAdvanceSincePrApiBase']['paths'] if x.split('\t')[-1]=='src/NzbDrone.Core/Localization/Core/en.json']
drift['mainAdvanceLocaleCatalogPaths']=[x.split('\t')[-1] for x in drift['mainAdvanceSincePrApiBase']['paths'] if '/Localization/Core/' in x.split('\t')[-1] and not x.split('\t')[-1].endswith('/en.json')]
callsite_diffs=[]
for item in drift['callerContextDifferences']:
 pr_direct=call_sig(item['prCallerRefs']); main_direct=call_sig(item['mainCallerRefs'])
 pr_dynamic=dynamic_sig(item['prDynamicCallsites']); main_dynamic=dynamic_sig(item['mainDynamicCallsites'])
 if pr_direct!=main_direct or pr_dynamic!=main_dynamic:
  callsite_diffs.append({'sourceKey':item['sourceKey'],'prLiteralCallsiteCount':len(pr_direct),'mainLiteralCallsiteCount':len(main_direct),'addedLiteralCallsites':sorted(main_direct-pr_direct),'removedLiteralCallsites':sorted(pr_direct-main_direct),'prDynamicCallsiteCount':len(pr_dynamic),'mainDynamicCallsiteCount':len(main_dynamic),'addedDynamicCallsites':sorted(main_dynamic-pr_dynamic),'removedDynamicCallsites':sorted(pr_dynamic-main_dynamic)})
drift['translationCallsiteChangesAgainstMain']=callsite_diffs
wj('latest-main-drift.json',drift)
summary=j('candidate-free-summary.json')
reattest=j('prior-window-reattestation.json')
prior_hold_rows=[json.loads(x) for x in (OUT/'prior-hold-reattestation.jsonl').read_text().splitlines() if x.strip()]
ctx=[json.loads(x) for x in (OUT/'caller-context.jsonl').read_text().splitlines()]
no_literal=[r['sourceKey'] for r in ctx if r['literalCallCount']==0]
summary.update({'priorWindowReattestation':reattest,'priorHoldCount':len(prior_hold_rows),'priorHoldsReattested':len(prior_hold_rows),'keysWithZeroLiteralCallers':no_literal,'candidateFreeOnly':True,'noCandidateSuggestionsIncluded':True})
wj('candidate-free-summary.json',summary)
manifest=j('candidate-free-manifest.json')
manifest.update({'liveMainTree':att['liveMainTree'],'headWorkflowTree':att['headWorkflowTree'],'liveMainWorkflowTree':att['liveMainWorkflowTree'],'latestMainDriftSha256':sha((OUT/'latest-main-drift.json').read_bytes()),'catalogPinsSha256':sha((OUT/'catalog-pins.json').read_bytes()),'priorWindowReattestation':{'path':'prior-window-reattestation.json','sha256':sha((OUT/'prior-window-reattestation.json').read_bytes()),'rows':600},'priorWindowCells':{'path':'prior-window-reattestation.jsonl','sha256':sha((OUT/'prior-window-reattestation.jsonl').read_bytes()),'rows':600},'priorHoldReattestation':{'path':'prior-hold-reattestation.jsonl','sha256':sha((OUT/'prior-hold-reattestation.jsonl').read_bytes()),'rows':len(prior_hold_rows)},'packetBuilder':{'path':'packet-builders/build_candidate_free.py','sha256':sha((OUT/'packet-builders/build_candidate_free.py').read_bytes())},'priorWindowAttestor':{'path':'packet-builders/attest_prior_window.py','sha256':sha((OUT/'packet-builders/attest_prior_window.py').read_bytes())},'packetFinalizer':{'path':'packet-builders/finalize_candidate_free.py','sha256':sha((OUT/'packet-builders/finalize_candidate_free.py').read_bytes())},'candidateFreeOnly':True,'result':'PASS' if not drift['sourceDifferences'] and not drift['targetDifferences'] and not drift['workflowPathsInPrDiff'] else 'PASS_WITH_RECORDED_DRIFT'})
wj('candidate-free-manifest.json',manifest)
(OUT/'README.md').write_text(f'''# W400–W449 Core candidate-free review packet\n\nThis packet is pinned to open draft PR #190 head `{att['headSha']}` (tree `{att['headTree']}`) and live `main` `{att['liveMainSha']}` (tree `{att['liveMainTree']}`). It contains the next 50 uncovered English Core source keys, ordinals 400–449, across 12 locale catalogs: 600 current cells.\n\n`candidate-free-cells.jsonl` contains the pinned English source, current target, exact source/catalog file hashes, placeholder/markup/numeric/protected-literal checks, and caller-context hash for each cell. `caller-context.jsonl` pins source callers and neighboring code; the full caller-scan file pins are included. `latest-main-drift.json` compares this window against live `main`: source and target values match; six caller-context fingerprints differ and are enumerated. The PR diff from its API base has no workflow paths. `main` has a newer workflow tree, including `{', '.join(drift['mainAdvanceWorkflowPaths']) or 'no workflow paths'}` since the PR API base; no workflow file is part of the PR diff.\n\n`source-selection.json` continues the verified W0–W399 selection, excluding direct identifiers in the frozen 392-file historical scan. The previous W350–W399 window is reattested against all 600 committed application readback hashes; its 12 source-copy holds are reattested as text-free hash records. Current candidate-free extraction reports zero exact literal translation calls for `{', '.join(no_literal) if no_literal else 'no selected keys'}`; the primary review must keep any such cells as hash-only holds.\n\nThis packet includes no translation proposals or primary-review decisions. It does not authorize catalog edits, cross-review, blind review, application, or CI. `verify_candidate_free.py` checks the portable packet and its checksums; `--repo` additionally checks the pinned local Git objects and current worktree.\n''')
# Rebuild checksums after all packet files are finalized.
files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt')
(OUT/'SHA256SUMS.txt').write_text(''.join(f'{sha(p.read_bytes())}  {p.relative_to(OUT).as_posix()}\n' for p in files))
print(json.dumps({'files':len(files)+1,'cells':600,'priorWindowCellsReattested':reattest['priorWindowCellsReattested'],'priorHoldsReattested':len(prior_hold_rows),'zeroLiteralCallKeys':no_literal,'mainWorkflowPathsSincePrBase':drift['mainAdvanceWorkflowPaths'],'prWorkflowPaths':drift['workflowPathsInPrDiff'],'sourceDrift':len(drift['sourceDifferences']),'targetDrift':len(drift['targetDifferences']),'callerContextDrift':len(drift['callerContextDifferences']),'result':manifest['result']},indent=2))
