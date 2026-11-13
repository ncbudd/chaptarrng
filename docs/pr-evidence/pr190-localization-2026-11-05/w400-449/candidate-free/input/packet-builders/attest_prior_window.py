#!/usr/bin/env python3
import hashlib, json, subprocess
from pathlib import Path
TASK=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-w400-449-20261105')
REPO=Path('/mnt/disks/scratch/task-worktrees/localization-20261105/chaptarrng-pr190-w400-pinned')
OUT=TASK/'candidate-free'/'input'
PREV=REPO/'docs/pr-evidence/pr190-localization-2026-11-05/window-350-399-core-application'
PREV_CF=PREV/'candidate-free'/'input'
def sha(b):return hashlib.sha256(b).hexdigest()
def st(s):return sha(s.encode())
def jl(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def blob(path):return subprocess.check_output(['git','-C',str(REPO),'show',f'HEAD:{path}'])
def jblob(path):return json.loads(blob(path))
prevsel=json.loads((PREV_CF/'source-selection.json').read_text())
prevcells=jl(PREV_CF/'candidate-free-cells.jsonl')
prevctx={r['sourceKey']:r for r in jl(PREV_CF/'caller-context.jsonl')}
readback=jl(PREV/'application'/'all-cell-readback.jsonl')
rootrows=jl(PREV/'root-manual-review'/'root-review.jsonl')
prevholds=[r for r in rootrows if r.get('rootDisposition')=='maintain-hold']
assert prevsel['head']=='dbe530c9d1a7fd2c12ce2aef76ec74c5c2188aa0'
assert prevsel['firstPosition']==350 and prevsel['lastPosition']==399 and len(prevcells)==600
assert len(readback)==600 and len(prevholds)==12
source=json.loads(blob('src/NzbDrone.Core/Localization/Core/en.json'))
files={x['locale']:x['targetFile'] for x in prevcells[:12]}
locfiles={loc:prev for loc,prev in files.items()}
curcatalog={loc:json.loads(blob(path)) for loc,path in locfiles.items()}
readmap={(r['sourceKey'],r['locale']):r for r in readback}
prevmap={(r['sourceKey'],r['locale']):r for r in prevcells}
rows=[]
for r in readback:
 ident=(r['sourceKey'],r['locale']); c=prevmap[ident]
 current=curcatalog[r['locale']][r['sourceKey']]
 current_sha=st(current)
 assert st(source[r['sourceKey']])==r['sourceTextSha256']==c['sourceTextSha256']
 assert c['callerContextSha256']==r['callerContextSha256']
 assert current_sha==r['expectedAfterSha256']==r['observedAfterSha256']
 rows.append({'priorWindow':'W350-399-Core','sourceOrdinal':r['sourceOrdinal'],'sourceKey':r['sourceKey'],'locale':r['locale'],'sourceTextSha256':r['sourceTextSha256'],'callerContextSha256':r['callerContextSha256'],'priorBeforeTargetSha256':r['beforeTargetSha256'],'priorExpectedAfterSha256':r['expectedAfterSha256'],'currentTargetSha256':current_sha,'priorReadbackObservedSha256':r['observedAfterSha256'],'priorDisposition':r['rootDisposition'],'reattested':True})
# Recheck the full prior caller-scan file set, not only lines used by the held key.
prev_scan=json.loads((PREV_CF/'caller-scan-file-pins.json').read_text())
current_pins=[]
for f in prev_scan['files']:
 raw=blob(f['path']); oid=subprocess.check_output(['git','-C',str(REPO),'rev-parse',f'HEAD:{f["path"]}'],text=True).strip()
 assert oid==f['gitBlob'] and sha(raw)==f['sha256']
 current_pins.append(f['path'])
assert len(current_pins)==prev_scan['gitBlobFileCount']
prev_code_paths={x['path'] for x in prev_scan['files']}
head_code=subprocess.check_output(['git','-C',str(REPO),'ls-tree','-r','--name-only','HEAD','--','frontend/src','src'],text=True).splitlines()
code_paths=set()
for p in head_code:
 pp=Path(p); parts=pp.parts; basename=pp.name.lower()
 if pp.suffix not in {'.js','.jsx','.ts','.tsx','.cs'}: continue
 test_project=any(x.lower() in ('test','tests','__tests__') or x.lower().endswith(('.test','.tests','-test','-tests')) for x in parts[:-1])
 test_file=basename.endswith(('.test.js','.test.jsx','.test.ts','.test.tsx','.spec.js','.spec.jsx','.spec.ts','.spec.tsx','.test.cs','.tests.cs'))
 if not test_project and not test_file: code_paths.add(p)
assert code_paths==prev_code_paths
prior_hold_rows=[]
for r in prevholds:
 ident=(r['sourceKey'],r['locale']); cf=prevmap[ident]; current=curcatalog[r['locale']][r['sourceKey']]
 assert r['sourceTextSha256']==cf['sourceTextSha256']
 assert r['currentTargetSha256']==st(current)==readmap[ident]['expectedAfterSha256']
 assert r['callerContextSha256']==cf['callerContextSha256']==readmap[ident]['callerContextSha256']
 prior_hold_rows.append({'priorWindow':'W350-399-Core','sourceOrdinal':r['sourceOrdinal'],'sourceKey':r['sourceKey'],'locale':r['locale'],'sourceTextSha256':r['sourceTextSha256'],'currentTargetSha256':st(current),'callerContextSha256':r['callerContextSha256'],'priorDisposition':'maintain-hold','holdReasonClass':'source-copy/context mismatch','textIncluded':False,'reattested':True})
assert len(rows)==600 and len(prior_hold_rows)==12
(OUT/'prior-window-reattestation.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for r in rows))
(OUT/'prior-hold-reattestation.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for r in prior_hold_rows))
summary={'schemaVersion':1,'exactHead':'8ce0caa5c8c456ba5b1bcfeb0352955c93f181e7','exactTree':'018e46cd14424204a01be46e13e5b50f9f26ce07','priorWindow':'W350-399-Core','priorWindowSourceHead':prevsel['head'],'priorWindowSourceTree':prevsel['tree'],'priorSourceSelectionSha256':sha((PREV_CF/'source-selection.json').read_bytes()),'priorCandidateFreeCellsSha256':sha((PREV_CF/'candidate-free-cells.jsonl').read_bytes()),'priorReadbackSha256':sha((PREV/'application'/'all-cell-readback.jsonl').read_bytes()),'priorRootReviewSha256':sha((PREV/'root-manual-review'/'root-review.jsonl').read_bytes()),'priorWindowCells':len(rows),'priorWindowCellsReattested':sum(r['reattested'] for r in rows),'priorHoldCount':len(prior_hold_rows),'priorHoldsReattested':sum(r['reattested'] for r in prior_hold_rows),'priorCallerScanFileCount':len(prev_code_paths),'priorCallerScanFilesUnchanged':len(current_pins),'sourceOrTargetHashMismatches':0,'callerHashMismatches':0,'result':'PASS'}
(OUT/'prior-window-reattestation.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
