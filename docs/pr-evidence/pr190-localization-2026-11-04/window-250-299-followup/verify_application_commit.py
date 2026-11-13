#!/usr/bin/env python3
"""Verify the committed W250-W299 catalog diff against the sealed cross-review and apply plan."""
import collections, hashlib, json, re, subprocess
from pathlib import Path
TASK=Path('/home/keith/Documents/code/task-scratch')
OUT=TASK/'chaptarrng-pr190-w250-299-apply-20261104'
CROSS=TASK/'chaptarrng-pr190-w250-299-cross-20261104'
REPO=Path('/mnt/disks/scratch/task-worktrees/localization-20261104/chaptarrng-pr190-w250-299-apply')
COMMIT='7bf3760ea87879304ec8deb6e4e8cf2f2b62c5b0'
PARENT='2a9995a2bf63f06814bd8780736305f16bd6b33a'
TREE='8d821e88af5c3451d608e2bdd87549249d5cf745'
ROOT='AutomaticUpdatesDisabledDocker::id'
ROOT_TARGET='Pemutakhiran otomatis tidak didukung secara langsung saat menggunakan mekanisme pemutakhiran Docker. Anda perlu memperbarui gambar kontainer di luar {appName} atau menggunakan skrip.'
PH=re.compile(r'\{[^{}]+\}')
INLINE=re.compile(r'`([^`]+)`')
MARKUP=re.compile(r'<[^>]+>')
NUM=re.compile(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])')
sha=lambda b:hashlib.sha256(b).hexdigest()
sha_text=lambda s:sha(s.encode('utf-8'))
def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args])
def sig(rx,s):return collections.Counter(rx.findall(s))
def nums(s):return sig(NUM,PH.sub('',s))
plan=json.loads((OUT/'apply-plan.json').read_text())
cross=[json.loads(x) for x in (CROSS/'cross-review-cells.jsonl').read_text().splitlines()]
readback=[json.loads(x) for x in (OUT/'apply-readback.jsonl').read_text().splitlines()]
assert git('cat-file','-t',COMMIT).decode().strip()=='commit'
assert git('rev-parse',COMMIT+'^{tree}').decode().strip()==TREE
assert git('rev-parse',COMMIT+'^').decode().strip()==PARENT
assert git('status','--porcelain=v1').decode().strip() in ('','?? docs/pr-evidence/pr190-localization-2026-11-04/window-250-299-followup/')
changes={x['cellId']:x for x in plan['changes']}
assert len(cross)==len(readback)==600 and len(changes)==42
parent_files={}
for path,guard in plan['fileGuards'].items():
    raw=git('show',PARENT+':'+path)
    assert sha(raw)==guard['sha256']
    assert git('rev-parse',PARENT+':'+path).decode().strip()==guard['gitBlob']
    parent_files[path]=json.loads(raw)
committed_files={}
for path in plan['fileGuards']:
    raw=git('show',COMMIT+':'+path)
    committed_files[path]=json.loads(raw)

seen_changes=[]
for c,r in zip(cross,readback):
    cid=c['cellId']; path=next(x['targetFile'] for x in readback if x['cellId']==cid)
    actual=committed_files[path][c['sourceKey']]
    change=changes.get(cid)
    expected=change['recommendedTarget'] if change else c['currentTarget']
    assert actual==expected and sha_text(actual)==(change['recommendedTargetSha256'] if change else c['currentTargetSha256'])
    assert r['finalTargetSha256']==sha_text(actual)
    assert sig(PH,actual)==sig(PH,c['sourceText'])
    assert sig(INLINE,actual)==sig(INLINE,c['sourceText'])
    assert sig(MARKUP,actual)==sig(MARKUP,c['sourceText'])
    assert nums(actual)==nums(c['sourceText'])
    if change: seen_changes.append(cid)
assert len(seen_changes)==42 and len(readback)-len(seen_changes)==558
assert committed_files[next(x['targetFile'] for x in plan['changes'] if x['cellId']==ROOT)][ 'AutomaticUpdatesDisabledDocker'] == ROOT_TARGET
paths=set(git('diff-tree','--no-commit-id','--name-only','-r',COMMIT).decode().splitlines())
expected_paths={x['targetFile'] for x in plan['changes']}
assert paths==expected_paths

diff=git('diff','--unified=0',PARENT,COMMIT,'--',*sorted(paths)).decode().splitlines()
rx=re.compile(r'^[-+]\s*"((?:\\.|[^"\\])*)"\s*:\s*')
minus=[];plus=[]
for line in diff:
    if line.startswith(('---','+++')):continue
    m=rx.match(line)
    if m:
        key=json.loads('"'+m.group(1)+'"')
        (minus if line.startswith('-') else plus).append(key)
expected_keys=[x['sourceKey'] for x in plan['changes']]
assert collections.Counter(minus)==collections.Counter(expected_keys)
assert collections.Counter(plus)==collections.Counter(expected_keys)

result={
 'result':'PASS','commit':COMMIT,'tree':TREE,'parent':PARENT,'reviewedCells':600,'changedCells':42,'acceptedCurrentCellsPreserved':558,
 'changedCatalogFiles':sorted(paths),'exactChangedKeyDiffVerified':42,'rootCorrectionCell':ROOT,'rootCorrectionTargetSha256':sha_text(ROOT_TARGET),
 'parentCatalogFileGuardsVerified':len(parent_files),'committedCatalogFilesReadBack':len(committed_files),'productCommitWorkingTreeUnchanged':True,'testsBuildsCIWorkflowsRun':False
}
(OUT/'commit-readback-evidence.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
