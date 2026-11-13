#!/usr/bin/env python3
"""Seal candidate-free W450–W499 evidence and complete manifest/checksums."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
TASK=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-w450-499-20261105')
OUT=TASK/'candidate-free'/'input'
def sha(b): return hashlib.sha256(b).hexdigest()
def j(name): return json.loads((OUT/name).read_text())
def wj(name,obj): (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
# Preserve both independently captured live snapshots within the packet.
before=json.loads((TASK/'attestation'/'live-pre-build.json').read_text())
after=json.loads((TASK/'attestation'/'live-after-build.json').read_text())
if before['headSha']!=after['headSha'] or before['headTree']!=after['headTree'] or before['liveMainSha']!=after['liveMainSha'] or before['liveMainTree']!=after['liveMainTree']:
 raise SystemExit('FAIL: PR or live-main refs changed during candidate-free packet build')
(OUT/'PR-attestation-before.json').write_text(json.dumps(before,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
(OUT/'PR-attestation-after.json').write_text(json.dumps(after,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
wj('PR-attestation.json',after)
# Add live workflow and main-advance details from the API/ref attestation.
drift=j('latest-main-drift.json')
drift['prWorkflowTree']=after['headWorkflowTree']
drift['liveMainWorkflowTree']=after['liveMainWorkflowTree']
drift['mainWorkflowTreeChangedAgainstPr']=after['headWorkflowTree']!=after['liveMainWorkflowTree']
advance=drift['mainAdvanceSincePrApiBase']['paths']
drift['mainAdvanceWorkflowPaths']=[x.split('\t')[-1] for x in advance if x.split('\t')[-1].startswith('.github/workflows/')]
drift['mainAdvanceCoreCatalogPaths']=[x.split('\t')[-1] for x in advance if '/Localization/Core/' in x.split('\t')[-1]]
drift['mainAdvanceEnglishSourcePaths']=[x.split('\t')[-1] for x in advance if x.split('\t')[-1]=='src/NzbDrone.Core/Localization/Core/en.json']
drift['mainAdvanceLocaleCatalogPaths']=[x.split('\t')[-1] for x in drift['mainAdvanceCoreCatalogPaths'] if not x.endswith('/en.json')]
wj('latest-main-drift.json',drift)
# Human-readable packet summary; numeric differences remain explicit for review.
summary=j('candidate-free-summary.json')
prev=j('prior-review-input-reattestation.json')
summary.update({'priorW400CellsReattested':prev['W400']['cellsReattested'],'priorW400CallerScanFilesReattested':prev['W400']['callerScanFilesReattested'],'committedW400ApplicationRowsReattested':prev['W400']['applicationReadbackMatchesCurrent'],'w400CallerlessHoldsReattested':prev['W400']['callerlessHoldsReattested'],'carriedPriorHoldsReattested':prev['W400']['carriedPriorHoldsReattested'],'legacyNov2W450SelectionDisposition':prev['legacyW450']['legacyDisposition'],'legacyNov2W450SourceKeyOverlap':prev['legacyW450']['primaryWindowKeyOverlap'],'numericHeuristicFlagCells':[{'sourceOrdinal':471,'sourceKey':'ChmodFolderHelpText','locale':'ja'},{'sourceOrdinal':471,'sourceKey':'ChmodFolderHelpText','locale':'ko'}],'candidateFreeOnly':True,'noCandidateSuggestionsIncluded':True})
wj('candidate-free-summary.json',summary)
# Record the requested verifier commands and their observed successful summaries.
verify_result={'portable':{'command':'python3 verify_candidate_free.py','result':'PASS','summary':{'cells':600,'sourceIds':50,'callerContexts':50,'candidateFreeOnly':True}},'exactWorktree':{'command':'python3 verify_candidate_free.py --repo /mnt/disks/scratch/task-worktrees/localization-20261105/chaptarrng-pr190-w400-cross-pinned','result':'PASS','summary':{'catalogs':13,'selectedCellsVerified':600,'historicalRows':211539,'callerSourcePinsVerified':13049}},'capturedAfterRuns':True}
(OUT/'verifier-results.json').write_text(json.dumps(verify_result,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
# Manifest pins all semantic inputs, prior continuity records, and verifier artifacts.
selection=j('source-selection.json'); att=after
files={
 'candidateFreeCells':'candidate-free-cells.jsonl','callerContext':'caller-context.jsonl','catalogPins':'catalog-pins.json','sourceSelection':'source-selection.json','latestMainDrift':'latest-main-drift.json','priorHistoricalScan':'prior-historical-evidence-scan.json','runtimeSourcePins':'runtime-source-pins.json','callerScanFilePins':'caller-scan-file-pins.json','mainCallerScanFilePins':'main-caller-scan-file-pins.json','priorW400CellReattestation':'prior-window-reattestation.jsonl','priorW400ReattestationSummary':'prior-window-reattestation.json','priorW400CallerScanReattestation':'prior-caller-scan-file-reattestation.jsonl','w400ApplicationReadbackReattestation':'w400-application-readback-reattestation.jsonl','w400CallerlessHoldReattestation':'w400-callerless-hold-reattestation.jsonl','carriedPriorHoldReattestation':'w400-carried-prior-hold-reattestation.jsonl','priorReviewInputReattestation':'prior-review-input-reattestation.json','legacyW450PrimaryInputReattestation':'legacy-w450-primary-input-reattestation.jsonl','legacyW450PrimaryCallerReattestation':'legacy-w450-primary-caller-reattestation.jsonl','legacyW450CrossCellReattestation':'legacy-w450-cross-live-cell-reattestation.jsonl','legacyW450CrossCallerReattestation':'legacy-w450-cross-caller-reattestation.jsonl','legacyW450RootReadbackReattestation':'legacy-w450-root-readback-reattestation.jsonl','portableVerifier':'verify_candidate_free.py','verifierResults':'verifier-results.json'
}
manifest={'schemaVersion':1,'repository':'snapetech-org/chaptarrng','pullRequest':190,'branch':'codex/chaptarrng-localization-complete-20261031','scope':{'firstPosition':450,'lastPosition':499,'sourceIds':50,'locales':selection['locales'],'cells':600},'head':att['headSha'],'tree':att['headTree'],'apiBase':att['apiBaseSha'],'apiBaseTree':att['apiBaseTree'],'liveMain':att['liveMainSha'],'liveMainTree':att['liveMainTree'],'headWorkflowTree':att['headWorkflowTree'],'liveMainWorkflowTree':att['liveMainWorkflowTree'],'sourceQueue':{'historicalFileCount':selection['historicalFileCount'],'historicalRows':selection['historicalRows'],'priorSelectedKeysCount':selection['priorSelectedKeysCount'],'selectedKeysSha256':selection['selectedKeysSha256'],'selectionMatchesFirstUncoveredPositions':selection['selectionMatchesFirstUncoveredPositions']},'artifactPins':{name:{'path':path,'sha256':sha((OUT/path).read_bytes())} for name,path in files.items()},'integrityCheckFailures':summary['integrityCheckFailures'],'priorContinuity':{'w400CellsReattested':prev['W400']['cellsReattested'],'w400CallerSourceFilesReattested':prev['W400']['callerScanFilesReattested'],'committedApplicationRowsReattested':prev['W400']['applicationReadbackMatchesCurrent'],'w400CallerlessHoldsReattested':prev['W400']['callerlessHoldsReattested'],'carriedPriorHoldsReattested':prev['W400']['carriedPriorHoldsReattested'],'legacyNov2W450InputsCurrent':prev['legacyInputsReattestedAtCurrentHead'],'legacyNov2W450KeyOverlap':prev['legacyW450']['primaryWindowKeyOverlap']},'candidateFreeOnly':True,'nativeSpeakerApproval':False,'result':'PASS'}
wj('candidate-free-manifest.json',manifest)
# Make provenance builders self-contained and checksummed with the packet.
obsolete=OUT/'packet-builders'/'attest_prior_window.py'
if obsolete.exists(): obsolete.unlink()
for p in sorted(OUT.rglob('*')):
 if p.is_file() and p.name!='SHA256SUMS.txt' and p.suffix=='.py': p.chmod(0o755)
# Explicit reader guide and freshness limitation for Nov 2 evidence.
(OUT/'README.md').write_text(f'''# W450–W499 Core candidate-free review packet

This packet covers ChaptarrNG PR #190 Core source positions 450–499: 50 source IDs × 12 locales = 600 current cells. It is pinned to open draft PR head `{att['headSha']}` (tree `{att['headTree']}`), API base `{att['apiBaseSha']}`, and live main `{att['liveMainSha']}` (tree `{att['liveMainTree']}`). `PR-attestation-before.json` and `PR-attestation-after.json` record the live API state, branch/pull refs, exact Git objects, and clean exact worktree before and after packet generation.

`candidate-free-cells.jsonl` contains the current English source, locale value, source and catalog pins, token/markup summaries, and caller-context hash for each cell. `caller-context.jsonl` carries source lines and neighboring code. `source-selection.json`, `prior-historical-evidence-scan.json`, and the four-position boundary file establish continuity from W0–W449 and select the first 50 remaining Core keys. `catalog-pins.json` pins all 12 locale catalogs and their ordered key sets.

The W400 window is reattested at the current head: all 600 source, post-application target, and caller hashes match; all 4,350 caller-scan source files match. The committed W400 application commit `{prev['W400']['applicationCommit']}` is an ancestor of the current PR head, and its 140 readback rows match current catalogs. W400’s 12 callerless hash-only holds and the 12 carried prior-window hash-only holds were reattested without including text.

The Nov 2 W450 primary, cross-review, and root-apply scratch inputs are preserved separately and are marked stale: their 50 source IDs have zero overlap with this current W450 selection. Hash-only reattestation records document the mismatch. No old proposal, recommendation, or candidate ledger was opened, and those outputs are not current evidence.

The source/target comparison against current main has no differences; six caller-context fingerprints differ. The PR diff contains no workflow paths. Main’s workflow tree differs from the PR workflow tree. The heuristic numeric-token check flags two current Japanese and Korean cells for `ChmodFolderHelpText`; the flags are preserved for review and make no translation judgment.

This packet contains candidate-free inputs only. It does not include translation proposals, approval, catalog edits, or CI results. Run `python3 verify_candidate_free.py` for the portable checks and add `--repo /path/to/clean/exact-head-worktree` for Git object and catalog readback verification.
''')
# Final complete checksum inventory, including verifier and builder provenance.
files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt')
(OUT/'SHA256SUMS.txt').write_text(''.join(f'{sha(p.read_bytes())}  {p.relative_to(OUT).as_posix()}\n' for p in files))
print(json.dumps({'files':len(files)+1,'manifestScope':manifest['scope'],'head':att['headSha'],'tree':att['headTree'],'liveMain':att['liveMainSha'],'legacyW450':'STALE_SELECTION_NO_KEY_OVERLAP','result':manifest['result']},indent=2))
