#!/usr/bin/env python3
import collections, hashlib, json, subprocess
from datetime import datetime, timezone
from pathlib import Path

PRIMARY=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-1050-1099-primary-20261102')
CROSS=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-1050-1099-crossreview-20261102')
OUT=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-1050-1099-metadata-reattest-20261102')
REPO=Path('/home/keith/Documents/code/task-worktrees/localization-20261102-chaptarrng')
HEAD='c0a098e4e2b23117860c6e6827c1e84485273a7a'
TREE='669c5d82ab651dc38abb2db9d35fc2f893a19fef'
EXPECTED_MANIFEST_PREFIX='9b3b0bb0'
EXPECTED_SUMS_PREFIX='ac178120'
EXPECTED_README_BYTES=3061
EXPECTED_README_SHA='897127e176748c01d02b61bb77e9faac82a83571ed33c83bf4a31752ab9efbd4'

def sha(data): return hashlib.sha256(data).hexdigest()
def blob_sha(data):
    # Match Git's object ID; the content is also pinned with SHA-256.
    return subprocess.check_output(['git','-C',str(REPO),'hash-object','--stdin'],input=data).decode().strip()
def git(*args): return subprocess.check_output(['git','-C',str(REPO),*args])
def gitfile(path): return git('show',f'{HEAD}:{path}')
def readj(path): return json.loads(path.read_text(encoding='utf-8'))
def readjl(path): return [json.loads(s) for s in path.open(encoding='utf-8') if s.strip()]
def writej(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def writejl(path,rows):
    with path.open('w',encoding='utf-8',newline='\n') as f:
        for r in rows: f.write(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')
def verify_sums_file(path):
    checks=[]
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        digest,name=line.split(None,1); name=name.strip().lstrip('*')
        actual=sha((path.parent/name).read_bytes())
        checks.append({'path':name,'expectedSha256':digest,'actualSha256':actual,'matches':digest==actual})
    return checks

assert OUT.exists() and {p.name for p in OUT.iterdir()}=={'build_attestation.py'},list(OUT.iterdir())
assert git('cat-file','-e',f'{HEAD}^{{commit}}')==b''
assert git('rev-parse',f'{HEAD}^{{tree}}').decode().strip()==TREE
observed_head=git('rev-parse','HEAD').decode().strip()
observed_tree=git('rev-parse','HEAD^{tree}').decode().strip()
assert not git('status','--short').decode().strip()

# Recheck the sealed cross-review packet before using it as the comparison baseline.
cross_checks=verify_sums_file(CROSS/'SHA256SUMS')
assert len(cross_checks)==9 and all(x['matches'] for x in cross_checks)
cross=readj(CROSS/'summary.json')
assert cross['exactHead']==HEAD and cross['exactTree']==TREE and cross['cellCount']==600
cross_cells=readjl(CROSS/'cross-review-cells.jsonl')
cross_by_key={(x['sourceId'],x['locale']):x for x in cross_cells}
assert len(cross_by_key)==600

manifest=readj(PRIMARY/'manifest.json')
assert len(manifest['artifacts'])==24
manifest_rows=[]; manifest_failures=[]
for a in manifest['artifacts']:
    data=(PRIMARY/a['path']).read_bytes()
    actual={'bytes':len(data),'sha256':sha(data)}
    expected={'bytes':a['bytes'],'sha256':a['sha256']}
    ok=actual==expected
    row={'path':a['path'],'expectedBytes':expected['bytes'],'actualBytes':actual['bytes'],'expectedSha256':expected['sha256'],'actualSha256':actual['sha256'],'matches':ok}
    manifest_rows.append(row)
    if not ok: manifest_failures.append(row)
assert not manifest_failures,manifest_failures
readme=(PRIMARY/'README.md').read_bytes()
assert len(readme)==EXPECTED_README_BYTES and sha(readme)==EXPECTED_README_SHA
readme_manifest=next(a for a in manifest['artifacts'] if a['path']=='README.md')
assert readme_manifest['bytes']==EXPECTED_README_BYTES and readme_manifest['sha256']==EXPECTED_README_SHA
manifest_sha=sha((PRIMARY/'manifest.json').read_bytes())
sums_sha=sha((PRIMARY/'SHA256SUMS').read_bytes())
assert manifest_sha.startswith(EXPECTED_MANIFEST_PREFIX),manifest_sha
assert sums_sha.startswith(EXPECTED_SUMS_PREFIX),sums_sha
primary_sums=verify_sums_file(PRIMARY/'SHA256SUMS')
assert len(primary_sums)==25 and all(x['matches'] for x in primary_sums)
expected_names={a['path'] for a in manifest['artifacts']}|{'manifest.json'}
assert {x['path'] for x in primary_sums}==expected_names

# Validate exact repository pins remained stable and verify all files listed by pinned-files.json.
assert git('status','--short').decode().strip()==''
pins=readj(PRIMARY/'pinned-files.json')
assert pins['exactHead']==HEAD and pins['exactTree']==TREE
pin_rows=[]; pin_failures=[]
for p in pins['files']:
    data=gitfile(p['path'])
    actual={'bytes':len(data),'sha256':sha(data),'gitBlob':blob_sha(data)}
    expected={'bytes':p['bytes'],'sha256':p['sha256'],'gitBlob':p['gitBlob']}
    ok=actual==expected
    pin_rows.append({'path':p['path'],'expected':expected,'actual':actual,'matches':ok})
    if not ok: pin_failures.append(p['path'])
assert not pin_failures,pin_failures

# Compare the primary source/current/review rows against the sealed independent cross-review.
review=readjl(PRIMARY/'review-cells.jsonl')
input_cells=readjl(PRIMARY/'input-cells.jsonl')
source_slice=readjl(PRIMARY/'source-slice.jsonl')
assert len(review)==600 and len(input_cells)==600 and len(source_slice)==50
input_by_key={(x['sourceId'],x['locale']):x for x in input_cells}
assert len(input_by_key)==600
content_rows=[]; content_failures=[]
for r in review:
    key=(r['sourceId'],r['locale']); c=cross_by_key.get(key); i=input_by_key.get(key)
    if c is None or i is None:
        content_failures.append({'key':key,'kind':'missing'})
        continue
    checks={
        'sourceOrdinal':r['sourceOrdinal']==c['sourceOrdinal'],
        'source':r['source']==i['source'] and sha(r['source'].encode())==c['sourceSha256'],
        'sourceHash':r['sourceTextSha256']==i['sourceTextSha256']==c['sourceSha256'],
        'currentTarget':r['currentTarget']==i['currentTarget']==c['currentTarget'],
        'currentTargetHash':r['currentTargetSha256']==i['currentTargetSha256']==c['currentTargetSha256'],
        'primaryDisposition':r['primaryDisposition']==c['primaryDisposition'],
        'primaryFinalTarget':r['finalReviewedTarget']==c['crossReviewedTarget'],
        'primaryFinalTargetHash':r['finalReviewedTargetSha256']==c['crossReviewedTargetSha256'],
        'recommendedTarget':r['recommendedTarget']==c['recommendedTarget'],
        'callerReferenceCount':r['callerReferenceCount']==c['callerReferenceCount'],
    }
    row={'sourceOrdinal':r['sourceOrdinal'],'sourceId':r['sourceId'],'locale':r['locale'],'checks':checks,'allMatch':all(checks.values())}
    content_rows.append(row)
    if not row['allMatch']: content_failures.append(row)
assert len(content_rows)==600 and not content_failures,content_failures[:5]

# Source slice retains exactly the same 50 IDs/texts/hashes, one row per position.
source_index={(x['sourceId'],x['sourceOrdinal']):x for x in source_slice}
assert len(source_index)==50
source_failures=[]
for pos in range(1050,1100):
    group=[x for x in review if x['sourceOrdinal']==pos]
    assert len(group)==12
    r=group[0]; s=source_index.get((r['sourceId'],pos))
    if not s or s['source']!=r['source'] or s['sourceTextSha256']!=r['sourceTextSha256']:
        source_failures.append({'sourceOrdinal':pos,'sourceId':r['sourceId']})
assert not source_failures,source_failures

# The history carry-forward is also unchanged relative to the cross-review ledger.
primary_history=readjl(PRIMARY/'prior-dispositions-through-W1049.jsonl')
cross_history=readjl(CROSS/'historical-drift-checks-through-W1049.jsonl')
assert len(primary_history)==12600 and len(cross_history)==12600
cross_hist={(x['sourceId'],x['locale']):x for x in cross_history}
history_failures=[]
for x in primary_history:
    c=cross_hist.get((x['sourceId'],x['locale']))
    keys={'sourceOrdinal':'sourceOrdinal','liveCurrentTargetSha256':'liveCurrentTargetSha256','priorFinalTargetSha256':'priorFinalTargetSha256','previousPacketLiveCurrentTargetSha256':'previousPacketLiveCurrentTargetSha256'}
    if c is None or any(x[k]!=c[v] for k,v in keys.items()):
        history_failures.append({'sourceId':x['sourceId'],'locale':x['locale']})
assert not history_failures,history_failures[:5]

# Caller/source code pins in the review cells match the sealed cross-review's 60 unique caller pins.
review_callers={}
for r in review:
    for ref in r['callerRefs']:
        k=(r['sourceId'],ref['file'],ref['line'],ref['lineSha256'])
        review_callers[k]=(ref['fileGitBlob'],ref['fileSha256'])
cross_callers=readjl(CROSS/'caller-pin-checks.jsonl')
cross_caller_map={(x['sourceId'],x['file'],x['line'],x['lineSha256']):(x['fileGitBlob'],x['fileSha256']) for x in cross_callers}
assert len(review_callers)==60 and len(cross_caller_map)==60
assert review_callers==cross_caller_map

# Files with mtimes after the sealed cross-review checksum were only the two requested metadata files.
cross_seal_ns=(CROSS/'SHA256SUMS').stat().st_mtime_ns
post_crossreview=[]
for p in PRIMARY.rglob('*'):
    if p.is_file() and p.stat().st_mtime_ns>cross_seal_ns:
        post_crossreview.append(str(p.relative_to(PRIMARY)))
assert set(post_crossreview)=={'manifest.json','SHA256SUMS'},post_crossreview
mtime_evidence={
    'crossReviewSealUtc':datetime.fromtimestamp(cross_seal_ns/1e9,timezone.utc).isoformat(),
    'filesModifiedAfterCrossReviewSeal':post_crossreview,
    'maxMtimeOtherPacketFilesUtc':datetime.fromtimestamp(max(p.stat().st_mtime_ns for p in PRIMARY.rglob('*') if p.is_file() and p.name not in {'manifest.json','SHA256SUMS'})/1e9,timezone.utc).isoformat(),
}

writejl(OUT/'manifest-artifact-audit.jsonl',manifest_rows)
writejl(OUT/'content-parity.jsonl',content_rows)
writejl(OUT/'checksum-audit.jsonl',primary_sums)
writej(OUT/'pin-and-history-audit.json',{
    'exactHead':HEAD,'exactTree':TREE,'pinnedCommitAvailable':True,'observedWorktreeHead':observed_head,'observedWorktreeTree':observed_tree,'worktreeClean':True,
    'pinnedFiles':len(pin_rows),'pinnedFileFailures':len(pin_failures),
    'sourceRowsCompared':50,'currentAndReviewCellsCompared':600,'cellParityFailures':0,
    'priorHistoryRowsCompared':12600,'priorHistoryParityFailures':0,
    'uniqueCallerPinsCompared':60,'callerPinSetMatchesCrossReview':True,
    'crossReviewPacketChecksumsVerified':len(cross_checks),'crossReviewChecksumFailures':0,
    'postCrossReviewMtimeEvidence':mtime_evidence,
})
attestation={
    'attestation':'ChaptarrNG PR #190 W1050-W1099 repaired primary packet metadata reattestation',
    'primaryPacket':str(PRIMARY),'sealedCrossReview':str(CROSS),'attestationPacket':str(OUT),
    'exactHead':HEAD,'exactTree':TREE,'observedWorktreeHead':observed_head,'observedWorktreeTree':observed_tree,'worktreeClean':True,
    'primarySha256Sums':{'entries':len(primary_sums),'failures':0,'fileSha256':sums_sha},
    'manifest':{'artifactEntries':len(manifest_rows),'failures':0,'fileSha256':manifest_sha},
    'README':{'bytes':len(readme),'sha256':sha(readme),'manifestEntryMatches':True},
    'crossReviewContentParity':{'sourceRows':50,'cells':600,'historyRows':12600,'uniqueCallerPins':60,'failures':0},
    'repositoryPins':{'filePins':len(pin_rows),'failures':0,'worktreeClean':True},
    'metadataOnlyEvidence':mtime_evidence,
    'result':'PASS',
    'scope':'Metadata and cross-review parity reattestation only; no new semantic decisions.',
    'nativeSpeakerSignoff':'Still outstanding from the sealed cross-review.',
}
writej(OUT/'attestation.json',attestation)
readme_text=f'''# Chaptarr W1050–W1099 repaired packet metadata reattestation

This post-review check covers `{PRIMARY}` against the sealed independent cross-review at `{CROSS}` and its exact PR head `{HEAD}` / tree `{TREE}`. The worktree has since advanced to `{observed_head}` / `{observed_tree}`; all pin checks below use the earlier commit object directly and the worktree is clean.

## Result

- All 25 primary `SHA256SUMS` entries pass; all 24 manifest artifact sizes and SHA256 values match.
- `README.md` is 3,061 bytes with SHA256 `{sha(readme)}`; its manifest entry matches.
- Current `manifest.json` SHA256 is `{manifest_sha}`. Current regenerated `SHA256SUMS` SHA256 is `{sums_sha}`.
- All 600 reviewed rows, 50 source records, 12,600 history rows, and 60 caller pins match the sealed cross-review. The 21 pinned source/catalog/caller files still match the pinned Git tree.
- The only primary packet paths with mtimes after the sealed cross-review checksum are `manifest.json` and `SHA256SUMS`; the README and all source/catalog/review data retain their earlier mtimes and match the reviewed content.
- No new semantic dispositions were made. Native-speaker signoff remains outstanding.

Evidence: `manifest-artifact-audit.jsonl`, `checksum-audit.jsonl`, `content-parity.jsonl`, `pin-and-history-audit.json`, and `attestation.json`. `build_attestation.py` reproduces the checks. This attestation packet is confined to task scratch; no repository files, tests, CI, or PR state were changed.
'''
(OUT/'README.md').write_text(readme_text,encoding='utf-8')
files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name not in {'manifest.json','SHA256SUMS'})
writej(OUT/'manifest.json',{'exactHead':HEAD,'exactTree':TREE,'files':[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in files]})
files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name!='SHA256SUMS')
with (OUT/'SHA256SUMS').open('w',encoding='utf-8',newline='\n') as f:
    for p in files: f.write(f'{sha(p.read_bytes())}  {p.name}\n')
for line in (OUT/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
    d,name=line.split(None,1); assert sha((OUT/name.strip()).read_bytes())==d,name
print(json.dumps({'out':str(OUT),'files':len(files)+1,'attestation':attestation},ensure_ascii=False,indent=2))
