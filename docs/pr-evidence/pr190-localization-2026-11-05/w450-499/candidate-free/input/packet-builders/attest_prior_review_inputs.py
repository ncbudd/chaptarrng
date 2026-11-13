#!/usr/bin/env python3
"""Reattest prior W400 work and legacy W450 candidate-free inputs by hashes only."""
from __future__ import annotations
import collections, hashlib, json, subprocess
from pathlib import Path
ROOT=Path('/mnt/disks/scratch/task-worktrees/localization-20261105/chaptarrng-pr190-w400-cross-pinned')
TASK=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-w450-499-20261105')
OUT=TASK/'candidate-free'/'input'
W400=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-w400-449-20261105')
W450P=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0450-0499-primary-20261102')
W450X=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0450-0499-crossreview-20261102')
W450A=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0450-0499-root-apply-20261102')
HEAD='16c809b4787d70616a1a296ab0d90cf17923ba86'; TREE='dbd8343a42476f4e830428cc59efb7f4830251d5'
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
def sha(b): return hashlib.sha256(b).hexdigest()
def st(s): return sha(s.encode('utf-8'))
def canon(o): return (json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
def rdj(p): return json.loads(p.read_text())
def rdjl(p): return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def git(*args): return subprocess.check_output(['git','-C',str(ROOT),*args])
def blob(path): return git('show',f'{HEAD}:{path}')
def writej(name,obj): (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
def writejl(name,rows): (OUT/name).write_bytes(b''.join(canon(r) for r in rows))
def need(ok,msg):
 if not ok: raise SystemExit('FAIL: '+msg)
need(git('rev-parse','HEAD').decode().strip()==HEAD and git('rev-parse','HEAD^{tree}').decode().strip()==TREE,'exact target checkout')
# Current canonical W450 candidate-free rows and exact catalogs.
current=rdjl(OUT/'candidate-free-cells.jsonl')
ctx=rdjl(OUT/'caller-context.jsonl')
cur={(r['sourceKey'],r['locale']):r for r in current}
ctxmap={r['sourceKey']:r for r in ctx}
need(len(cur)==600 and len(ctxmap)==50,'current W450 packet dimensions')
sel=rdj(OUT/'source-selection.json')
# Capture current catalog values from exact Git blobs without writing values to attestation.
catfiles={r['locale']:r['targetFile'] for r in current[:12]}
catalogs={loc:json.loads(blob(path)) for loc,path in catfiles.items()}
source=json.loads(blob('src/NzbDrone.Core/Localization/Core/en.json'))
# W400 candidate-free cell, caller, and source queue continuity.
W400CF=W400/'candidate-free'/'input'
subprocess.run(['sha256sum','-c','SHA256SUMS.txt'],cwd=W400CF,check=True,stdout=subprocess.DEVNULL)
w400sel=rdj(W400CF/'source-selection.json')
w400cells=rdjl(W400CF/'candidate-free-cells.jsonl')
w400contexts=rdjl(W400CF/'caller-context.jsonl')
need(len(w400cells)==600 and len(w400contexts)==50,'W400 packet dimensions')
w400cur={(r['sourceKey'],r['locale']):r for r in w400cells}
w400ctx={r['sourceKey']:r for r in w400contexts}
# Pin and read the committed application hash records before checking prior cells.
app=W400/'application'/'application-readback.jsonl'; appsum=rdj(W400/'application'/'application-readback-summary.json')
need(appsum['exactSourceHead']=='8ce0caa5c8c456ba5b1bcfeb0352955c93f181e7' and appsum['exactSourceTree']=='018e46cd14424204a01be46e13e5b50f9f26ce07','W400 application source pins')
need(git('merge-base','--is-ancestor',appsum['productCommit'],HEAD) is not None,'W400 application commit ancestry')
app_rows=rdjl(app); app_by_key={(r['sourceKey'],r['locale']):r for r in app_rows}
need(len(app_by_key)==140,'W400 application readback row count')
w400rows=[]
for r in w400cells:
 key=(r['sourceKey'],r['locale']); live=source.get(r['sourceKey']); target=catalogs[r['locale']].get(r['sourceKey'])
 live_source=st(live) if live is not None else None
 live_target=st(target) if target is not None else None
 context_hash=w400ctx[r['sourceKey']]['callerContextSha256']
 applied=app_by_key.get(key)
 expected_after=applied['finalTargetSha256'] if applied else r['currentTargetSha256']
 source_ok=live_source==r['sourceTextSha256']; target_ok=live_target==expected_after
 context_ok=context_hash==r['callerContextSha256']
 w400rows.append({'priorWindow':'W400-449-Core','sourceOrdinal':r['sourceOrdinal'],'sourceKey':r['sourceKey'],'locale':r['locale'],'sourceTextSha256Expected':r['sourceTextSha256'],'sourceTextSha256Current':live_source,'preApplicationTargetSha256':r['currentTargetSha256'],'committedApplicationTargetSha256':applied['finalTargetSha256'] if applied else None,'currentTargetSha256Current':live_target,'applicationChangedCell':applied is not None,'sourceMatches':source_ok,'targetMatchesPostApplication':target_ok,'callerContextSha256Expected':r['callerContextSha256'],'callerContextSha256Current':context_hash,'callerContextMatchesFrozenInput':context_ok,'reattested':source_ok and target_ok and context_ok})
need(all(r['reattested'] for r in w400rows),'W400 cell or caller-context hash drift after accounting for committed application')
# Reattest complete W400 caller-scan source file set at current head.
scanpins=rdj(W400CF/'caller-scan-file-pins.json')['files']
pinned={r['path']:r['gitBlob'] for r in scanpins}
allpaths=git('ls-tree','-r','--name-only',HEAD,'--','frontend/src','src').decode().splitlines()
codepaths=set()
for path in allpaths:
 p=Path(path); parts=p.parts; base=p.name.lower()
 if p.suffix not in {'.js','.jsx','.ts','.tsx','.cs'}: continue
 test_project=any(x.lower() in ('test','tests','__tests__') or x.lower().endswith(('.test','.tests','-test','-tests')) for x in parts[:-1])
 test_file=base.endswith(('.test.js','.test.jsx','.test.ts','.test.tsx','.spec.js','.spec.jsx','.spec.ts','.spec.tsx','.test.cs','.tests.cs'))
 if not test_project and not test_file: codepaths.add(path)
need(codepaths==set(pinned),'W400 caller-scan path inventory changed')
callerfiles=[]
for path,oid in sorted(pinned.items()):
 raw=blob(path); live_oid=git('rev-parse',f'{HEAD}:{path}').decode().strip()
 expected=next(x for x in scanpins if x['path']==path)
 ok=live_oid==oid and sha(raw)==expected['sha256'] and len(raw)==expected['bytes']
 callerfiles.append({'path':path,'gitBlobExpected':oid,'gitBlobCurrent':live_oid,'sha256Expected':expected['sha256'],'sha256Current':sha(raw),'matches':ok})
need(all(x['matches'] for x in callerfiles),'W400 caller-scan source file changed')
writejl('prior-window-reattestation.jsonl',w400rows)
writej('prior-window-reattestation.json',{'schemaVersion':1,'window':'W400-449-Core','priorHead':w400sel['head'],'priorTree':w400sel['tree'],'currentHead':HEAD,'currentTree':TREE,'sourceIds':50,'locales':12,'cellsExpected':600,'cellsReattested':sum(x['reattested'] for x in w400rows),'sourceHashMismatches':sum(not x['sourceMatches'] for x in w400rows),'targetHashMismatchesAfterCommittedApplication':sum(not x['targetMatchesPostApplication'] for x in w400rows),'callerContextHashMismatches':sum(not x['callerContextMatchesFrozenInput'] for x in w400rows),'callerScanFilesExpected':len(scanpins),'callerScanFilesReattested':sum(x['matches'] for x in callerfiles),'callerScanPathInventoryMatches':codepaths==set(pinned),'callerScanFilePinsSha256':sha((W400CF/'caller-scan-file-pins.json').read_bytes()),'sourceSelectionSha256':sha((W400CF/'source-selection.json').read_bytes()),'candidateFreeCellsSha256':sha((W400CF/'candidate-free-cells.jsonl').read_bytes()),'callerContextSha256':sha((W400CF/'caller-context.jsonl').read_bytes()),'result':'PASS'})
writejl('prior-caller-scan-file-reattestation.jsonl',callerfiles)
# Attest the committed W400 application/readback by hashes only.
app_out=[]
for r in app_rows:
 current_val=catalogs[r['locale']].get(r['sourceKey']); current_hash=st(current_val) if current_val is not None else None
 source_hash=st(source[r['sourceKey']]) if r['sourceKey'] in source else None
 prevhash=r['finalTargetSha256']; observed=r['readbackTargetSha256']
 app_out.append({'sourceKey':r['sourceKey'],'locale':r['locale'],'sourceTextSha256':r['sourceTextSha256'],'sourceTextMatchesCurrent':source_hash==r['sourceTextSha256'],'callerContextSha256':r['callerContextSha256'],'priorFinalTargetSha256':prevhash,'priorReadbackTargetSha256':observed,'currentTargetSha256':current_hash,'readbackMatchesCurrent':prevhash==observed==current_hash,'rootDecision':r['rootDecision']})
need(len(app_out)==appsum['cellsApplied']==appsum['readbackMatches'] and all(r['readbackMatchesCurrent'] and r['sourceTextMatchesCurrent'] for r in app_out),'committed W400 application readback drift')
writejl('w400-application-readback-reattestation.jsonl',app_out)
# W400 callerless 12 holds, output hash-only (do not copy any recommended text).
hold_input=rdjl(W400/'primary-review'/'primary-review-holds.jsonl')
holdout=[]
for r in hold_input:
 k=(r['sourceKey'],r['locale']); old=w400cur[k]; now=catalogs[r['locale']].get(r['sourceKey'])
 now_hash=st(now) if now is not None else None
 holdout.append({'sourceKey':r['sourceKey'],'sourceOrdinal':r['sourceOrdinal'],'locale':r['locale'],'sourceTextSha256':r['sourceTextSha256'],'currentSourceTextSha256':st(source[r['sourceKey']]),'callerContextSha256':r['callerContextSha256'],'currentTargetSha256Expected':r['currentTargetSha256'],'currentTargetSha256':now_hash,'literalCallCount':r['literalCallCount'],'disposition':r['disposition'],'sourceTextIncluded':False,'targetTextIncluded':False,'reattested':r['sourceTextSha256']==st(source[r['sourceKey']]) and r['callerContextSha256']==old['callerContextSha256'] and r['currentTargetSha256']==now_hash})
need(len(holdout)==12 and all(x['reattested'] for x in holdout),'W400 callerless hash-only hold drift')
writejl('w400-callerless-hold-reattestation.jsonl',holdout)
# Prior W350 holds carried in the W400 candidate-free packet are hash-only too.
prior_hold_path=W400CF/'prior-hold-reattestation.jsonl'
prevholds=rdjl(prior_hold_path); prevholdout=[]
for r in prevholds:
 current_val=catalogs[r['locale']].get(r['sourceKey']); current_hash=st(current_val) if current_val is not None else None
 src_hash=st(source[r['sourceKey']]) if r['sourceKey'] in source else None
 prevholdout.append({'priorWindow':r.get('priorWindow'),'sourceKey':r['sourceKey'],'sourceOrdinal':r['sourceOrdinal'],'locale':r['locale'],'sourceTextSha256Expected':r['sourceTextSha256'],'sourceTextSha256Current':src_hash,'currentTargetSha256Expected':r['currentTargetSha256'],'currentTargetSha256':current_hash,'callerContextSha256Expected':r['callerContextSha256'],'sourceTextIncluded':False,'targetTextIncluded':False,'reattested':src_hash==r['sourceTextSha256'] and current_hash==r['currentTargetSha256']})
need(len(prevholdout)==12 and all(x['reattested'] for x in prevholdout),'W400 carried prior hold drift')
writejl('w400-carried-prior-hold-reattestation.jsonl',prevholdout)
# Legacy Nov 2 W450 candidate-free/source and caller inputs. Never open proposal ledgers.
oldman=rdj(W450P/'manifest.json')
oldcells=rdjl(W450P/'input-cells.jsonl')
oldctx=rdjl(W450P/'caller-context.jsonl')
old_out=[]
for r in oldcells:
 key=(r['sourceId'],r['locale']); now=cur.get(key)
 old_out.append({'sourceOrdinal':r['sourceOrdinal'],'sourceKey':r['sourceId'],'locale':r['locale'],'oldSourceTextSha256':r['sourceTextSha256'],'currentSourceTextSha256':now['sourceTextSha256'] if now else None,'oldTargetSha256':r['targetSha256'],'currentTargetSha256':now['currentTargetSha256'] if now else None,'oldCallerContextSha256':r['callerContextSha256'],'currentCallerContextSha256':now['callerContextSha256'] if now else None,'sourceMatches':bool(now and r['sourceTextSha256']==now['sourceTextSha256']),'targetMatches':bool(now and r['targetSha256']==now['currentTargetSha256']), 'callerContextMatches':bool(now and r['callerContextSha256']==now['callerContextSha256'])})
# Old primary caller context is one row per source ID; attest its fingerprint against present caller context.
oldctx_out=[]
for r in oldctx:
 now=ctxmap.get(r['sourceId'])
 oldctx_out.append({'sourceOrdinal':r['sourceOrdinal'],'sourceKey':r['sourceId'],'oldSourceTextSha256':st(r['sourceText']),'currentSourceTextSha256':st(source[r['sourceId']]) if r['sourceId'] in source else None,'oldCallerContextSha256':r['callerContextSha256'],'currentCallerContextSha256':now['callerContextSha256'] if now else None,'sourceMatchesCurrent':bool(r['sourceId'] in source and st(r['sourceText'])==st(source[r['sourceId']])), 'callerContextMatches':bool(now and r['callerContextSha256']==now['callerContextSha256'])})
writejl('legacy-w450-primary-input-reattestation.jsonl',old_out)
writejl('legacy-w450-primary-caller-reattestation.jsonl',oldctx_out)
# Cross-review live-cell hash attestations contain no proposed translations.
xrows=rdjl(W450X/'live-cell-hash-reattestation.jsonl'); xout=[]
for r in xrows:
 now=cur.get((r['sourceId'],r['locale']))
 xout.append({'sourceOrdinal':r['sourceOrdinal'],'sourceKey':r['sourceId'],'locale':r['locale'],'sourceTextSha256Frozen':r['sourceTextSha256Frozen'],'sourceTextSha256Current':now['sourceTextSha256'] if now else None,'targetSha256Frozen':r['currentTargetSha256Frozen'],'targetSha256Current':now['currentTargetSha256'] if now else None,'sourceMatchesCurrent':bool(now and r['sourceTextSha256Frozen']==now['sourceTextSha256']),'targetMatchesCurrent':bool(now and r['currentTargetSha256Frozen']==now['currentTargetSha256'])})
writejl('legacy-w450-cross-live-cell-reattestation.jsonl',xout)
# Cross caller hash rows are reconciled only against current caller lines in the candidate-free packet.
current_lines=collections.defaultdict(set)
for c in ctx:
 for r in c['callerRefs']:
  current_lines[(c['sourceKey'],r['path'],r['line'])].add(r['lineSha256'])
 for r in c['dynamicTranslationCallsites']:
  current_lines[(c['sourceKey'],r['path'],r['line'])].add(r['lineSha256'])
xc=rdjl(W450X/'caller-reattestation.jsonl'); xcout=[]
for r in xc:
 # Legacy id may be called sourceId, no translation text is copied.
 sid=r['sourceId']; key=(sid,r['file'],r['line']); expected=r['currentLineSha256Live']
 matches=expected in current_lines.get(key,set())
 xcout.append({'sourceOrdinal':r['sourceOrdinal'],'sourceKey':sid,'file':r['file'],'line':r['line'],'kind':r['kind'],'legacyLiveLineSha256':expected,'currentLineMatches':matches,'legacyMatchesFrozen':r['matchesFrozen']})
writejl('legacy-w450-cross-caller-reattestation.jsonl',xcout)
# Root apply readback exposes target hashes only; compare against current catalog values.
rootread=rdjl(W450A/'readback.jsonl'); rootout=[]
for r in rootread:
 now=cur.get((r['sourceId'],r['locale']))
 rootout.append({'sourceOrdinal':r['sourceOrdinal'],'sourceKey':r['sourceId'],'locale':r['locale'],'legacyReadbackTargetHash':r['targetHash'],'currentTargetSha256':now['currentTargetSha256'] if now else None,'matchesCurrent':bool(now and r['targetHash']==now['currentTargetSha256']),'finalDisposition':r['finalDisposition']})
writejl('legacy-w450-root-readback-reattestation.jsonl',rootout)
# Metadata summary, no recommendation or translation strings.
alllegacy=old_out
counts=lambda rows,field:sum(bool(r.get(field)) for r in rows)
old_key_set={r['sourceId'] for r in oldcells}; current_key_set=set(sel['keys']); key_overlap=sorted(old_key_set & current_key_set)
summary={'schemaVersion':1,'exactCurrentHead':HEAD,'exactCurrentTree':TREE,'W400':{'sourceIds':50,'cells':len(w400rows),'cellsReattested':sum(r['reattested'] for r in w400rows),'callerScanFilesReattested':sum(x['matches'] for x in callerfiles),'callerlessHolds':len(holdout),'callerlessHoldsReattested':sum(x['reattested'] for x in holdout),'carriedPriorHolds':len(prevholdout),'carriedPriorHoldsReattested':sum(x['reattested'] for x in prevholdout),'applicationCommit':appsum['productCommit'],'applicationCommitIsAncestor':True,'applicationRows':len(app_out),'applicationReadbackMatchesCurrent':sum(x['readbackMatchesCurrent'] for x in app_out),'applicationReadbackSourceMatchesCurrent':sum(x['sourceTextMatchesCurrent'] for x in app_out),'priorHead':w400sel['head'],'priorTree':w400sel['tree']},'legacyW450':{'primaryPacketHead':oldman.get('head'),'primaryPacketTree':oldman.get('tree'),'primaryManifestSha256':sha((W450P/'manifest.json').read_bytes()),'primaryInputCellsSha256':sha((W450P/'input-cells.jsonl').read_bytes()),'primaryCallerContextSha256':sha((W450P/'caller-context.jsonl').read_bytes()),'crossLiveCellInputSha256':sha((W450X/'live-cell-hash-reattestation.jsonl').read_bytes()),'crossCallerInputSha256':sha((W450X/'caller-reattestation.jsonl').read_bytes()),'rootReadbackInputSha256':sha((W450A/'readback.jsonl').read_bytes()),'primaryInputCells':len(old_out),'primaryWindowKeyOverlap':len(key_overlap),'primaryWindowKeyOverlapIds':key_overlap,'primaryInputSourceMatchesCurrent':counts(old_out,'sourceMatches'),'primaryInputTargetMatchesCurrent':counts(old_out,'targetMatches'),'primaryInputCallerMatchesCurrent':counts(old_out,'callerContextMatches'),'primaryCallerKeys':len(oldctx_out),'primaryCallerKeysMatchingCurrent':counts(oldctx_out,'callerContextMatches'),'crossLiveCellRows':len(xout),'crossLiveCellSourceMatchesCurrent':counts(xout,'sourceMatchesCurrent'),'crossLiveCellTargetsMatchCurrent':counts(xout,'targetMatchesCurrent'),'crossCallerRows':len(xcout),'crossCallerLinesMatchCurrent':counts(xcout,'currentLineMatches'),'rootReadbackRows':len(rootout),'rootReadbackTargetsMatchCurrent':counts(rootout,'matchesCurrent'),'candidateTextsRead':False,'proposalLedgersOpened':False,'legacyDisposition':'STALE_SELECTION_NO_KEY_OVERLAP' if not key_overlap else 'REQUIRES_CELL_HASH_REVIEW'},'legacyInputsReattestedAtCurrentHead':len(old_out)==600 and counts(old_out,'sourceMatches')==600 and counts(old_out,'targetMatches')==600 and counts(old_out,'callerContextMatches')==600 and counts(oldctx_out,'callerContextMatches')==50,'legacyRootReadbackMatchesCurrent':len(rootout)==600 and counts(rootout,'matchesCurrent')==600,'result':'PASS' if all(x['reattested'] for x in w400rows+holdout+prevholdout) and len(app_out)==140 and all(x['readbackMatchesCurrent'] and x['sourceTextMatchesCurrent'] for x in app_out) else 'FAIL'}
writej('prior-review-input-reattestation.json',summary)
print(json.dumps(summary,indent=2))
