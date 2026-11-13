#!/usr/bin/env python3
"""Apply the W250-W299 cross-review with exact file and cell hash guards."""
from __future__ import annotations
import collections, hashlib, json, re, subprocess
from pathlib import Path

TASK=Path('/home/keith/Documents/code/task-scratch')
OUT=TASK/'chaptarrng-pr190-w250-299-apply-20261104'
CROSS=TASK/'chaptarrng-pr190-w250-299-cross-20261104'
INPUT=TASK/'chaptarrng-pr190-w250-299-core-20261104/candidate-free/input'
REPO=Path('/mnt/disks/scratch/task-worktrees/localization-20261104/chaptarrng-pr190-w250-299-apply')
HEAD='2a9995a2bf63f06814bd8780736305f16bd6b33a'
TREE='f6ae6530b73bf581c1fbc5a8c13eacd7342e9172'
ROOT_CELL='AutomaticUpdatesDisabledDocker::id'
ROOT_TARGET='Pemutakhiran otomatis tidak didukung secara langsung saat menggunakan mekanisme pemutakhiran Docker. Anda perlu memperbarui gambar kontainer di luar {appName} atau menggunakan skrip.'
PH=re.compile(r'\{[^{}]+\}')
INLINE=re.compile(r'`([^`]+)`')
MARKUP=re.compile(r'<[^>]+>')
NUM=re.compile(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])')

def sha(b): return hashlib.sha256(b).hexdigest()
def sha_text(s): return sha(s.encode('utf-8'))
def row_sha(r): return sha(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8'))
def readj(p): return json.loads(p.read_text(encoding='utf-8'))
def readjl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def git(*args): return subprocess.check_output(['git','-C',str(REPO),*args],text=True).strip()
def token(rx,text): return collections.Counter(rx.findall(text))
def num(text): return token(NUM,PH.sub('',text))

def main():
    plan=readj(OUT/'apply-plan.json')
    adj=readj(OUT/'root-adjudication.json')
    cross=readjl(CROSS/'cross-review-cells.jsonl')
    cells=readjl(INPUT/'candidate-free-cells.jsonl')
    if len(cross)!=600 or len(cells)!=600 or len(plan['changes'])!=42:
        raise SystemExit('expected 600 cross/candidate rows and 42 changes')
    if sha((CROSS/'manifest.json').read_bytes())!=plan['crossReviewManifestSha256']:
        raise SystemExit('sealed cross manifest changed')
    if sha((CROSS/'SHA256SUMS.txt').read_bytes())!=plan['crossReviewSHA256SUMSFileSha256']:
        raise SystemExit('sealed cross checksum file changed')
    if sha((OUT/'root-adjudication.json').read_bytes())!=plan['rootAdjudicationSha256']:
        raise SystemExit('root adjudication changed after plan creation')
    if adj['cellId']!=ROOT_CELL or adj['correctedTarget']!=ROOT_TARGET or adj['sealedCrossPacketModified'] is not False:
        raise SystemExit('root adjudication mismatch')
    if git('rev-parse','HEAD')!=HEAD or git('show','-s','--format=%T',HEAD)!=TREE or git('status','--porcelain=v1'):
        raise SystemExit('apply worktree is not clean at the exact pinned head')

    # Verify all whole-file pins and build the exact set of key-level replacements.
    fileguards=plan['fileGuards']
    for rel,guard in fileguards.items():
        path=REPO/rel
        raw=path.read_bytes()
        if sha(raw)!=guard['sha256'] or git('hash-object',rel)!=guard['gitBlob']:
            raise SystemExit(f'catalog file hash/blob mismatch: {rel}')
    replacements=collections.defaultdict(dict)
    for change in plan['changes']:
        cid=change['cellId']
        old=change['currentTarget']
        if sha_text(old)!=change['currentTargetSha256']:
            raise SystemExit('current-target hash mismatch in plan: '+cid)
        if sha_text(change['recommendedTarget'])!=change['recommendedTargetSha256']:
            raise SystemExit('new-target hash mismatch in plan: '+cid)
        if change['cellId']=='AutomaticUpdatesDisabledDocker::id' and change['recommendedTarget']!=ROOT_TARGET:
            raise SystemExit('root correction target mismatch')
        if change['sourceKey'] in replacements[change['targetFile']]:
            raise SystemExit('duplicate replacement key')
        replacements[change['targetFile']][change['sourceKey']]=change

    # Validate every current target before editing.
    source_by_cell={(r['sourceKey']+'::'+r['locale']):r for r in cells}
    for change in plan['changes']:
        source=source_by_cell[change['cellId']]
        if source['targetFile']!=change['targetFile'] or source['targetFileSha256']!=change['targetFileSha256'] or source['targetFileGitBlob']!=change['targetFileGitBlob']:
            raise SystemExit('candidate-free file pin mismatch: '+change['cellId'])
        catalog=json.loads((REPO/change['targetFile']).read_text(encoding='utf-8'))
        value=catalog.get(change['sourceKey'])
        if value!=change['currentTarget'] or sha_text(value)!=change['currentTargetSha256']:
            raise SystemExit('exact current target guard failed: '+change['cellId'])

    # Replace only the JSON string on the exact key line, preserving all other bytes and layout.
    for rel,keychanges in replacements.items():
        path=REPO/rel
        text=path.read_text(encoding='utf-8')
        lines=text.splitlines(keepends=True)
        for key,change in keychanges.items():
            literal=json.dumps(key,ensure_ascii=False)
            pattern=re.compile(r'^(\s*'+re.escape(literal)+r'\s*:\s*)("(?:\\.|[^"\\])*")(,?)(\s*)$')
            hits=[]
            for i,line in enumerate(lines):
                body=line.rstrip('\r\n')
                ending=line[len(body):]
                m=pattern.fullmatch(body)
                if m:
                    hits.append((i,m,ending))
            if len(hits)!=1:
                raise SystemExit(f'expected one JSON line for {rel}:{key}, got {len(hits)}')
            i,m,ending=hits[0]
            old=json.loads(m.group(2))
            if old!=change['currentTarget'] or sha_text(old)!=change['currentTargetSha256']:
                raise SystemExit(f'line-level exact hash guard failed: {rel}:{key}')
            lines[i]=m.group(1)+json.dumps(change['recommendedTarget'],ensure_ascii=False)+m.group(3)+m.group(4)+ending
        path.write_text(''.join(lines),encoding='utf-8',newline='')

    # Read back every reviewed cell; all 558 accepted values must remain exact.
    live_catalogs={rel:json.loads((REPO/rel).read_text(encoding='utf-8')) for rel in fileguards}
    change_by_id={c['cellId']:c for c in plan['changes']}
    readback=[]
    changed_ids=set()
    for cell in cross:
        cid=cell['cellId']
        source=source_by_cell[cid]
        rel=source['targetFile']
        actual=live_catalogs[rel][cell['sourceKey']]
        change=change_by_id.get(cid)
        expected=change['recommendedTarget'] if change else cell['currentTarget']
        expected_sha=change['recommendedTargetSha256'] if change else cell['currentTargetSha256']
        if actual!=expected or sha_text(actual)!=expected_sha:
            raise SystemExit(f'600-cell readback failed: {cid}')
        if change:
            changed_ids.add(cid)
        if token(PH,actual)!=token(PH,cell['sourceText']) or token(INLINE,actual)!=token(INLINE,cell['sourceText']) or token(MARKUP,actual)!=token(MARKUP,cell['sourceText']) or num(actual)!=num(cell['sourceText']):
            raise SystemExit(f'token/placeholder readback failed: {cid}')
        readback.append({
            'cellId':cid,'sourceOrdinal':cell['sourceOrdinal'],'sourceKey':cell['sourceKey'],'locale':cell['locale'],
            'crossDisposition':cell['crossDisposition'],'applied':bool(change),
            'currentTargetSha256':cell['currentTargetSha256'],'finalTargetSha256':sha_text(actual),
            'finalTarget':actual if change else None,
            'candidateFreeRowSha256':cell['candidateFreeRowSha256'],'crossReviewRowSha256':row_sha(cell),
            'targetFile':rel
        })
    if len(changed_ids)!=42 or sum(not x['applied'] for x in readback)!=558:
        raise SystemExit('readback counts mismatch')
    if changed_ids!=set(change_by_id):
        raise SystemExit('applied change set mismatch')

    # Confirm the product diff contains only these 42 keys in the 12 pinned target catalogs.
    changed_paths=git('diff','--name-only').splitlines()
    expected_paths=set(replacements)
    if set(changed_paths)!=expected_paths:
        raise SystemExit(f'catalog file diff mismatch: {changed_paths}')
    diff=git('diff','--unified=0','--',*sorted(expected_paths)).splitlines()
    removed=[]; added=[]
    keyline=re.compile(r'^[-+]\s*"((?:\\.|[^"\\])*)"\s*:\s*"(?:\\.|[^"\\])*"')
    for line in diff:
        if line.startswith(('---','+++')): continue
        m=keyline.match(line)
        if m:
            key=json.loads('"'+m.group(1)+'"')
            (removed if line.startswith('-') else added).append(key)
    expected_keys=[x['sourceKey'] for x in plan['changes']]
    if collections.Counter(removed)!=collections.Counter(expected_keys) or collections.Counter(added)!=collections.Counter(expected_keys):
        raise SystemExit('diff key set is not exactly the 42 planned catalog values')

    after_files={rel:{'sha256':hashlib.sha256((REPO/rel).read_bytes()).hexdigest(),'gitBlob':git('hash-object',rel)} for rel in sorted(fileguards)}
    (OUT/'apply-readback.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for x in readback),encoding='utf-8')
    result={
        'result':'PASS','appliedChanges':42,'acceptedCurrentPreserved':558,'allReviewedCellsReadBack':600,
        'changedCatalogFiles':sorted(fileguards),'exactDiffKeysVerified':42,
        'sourceHead':HEAD,'sourceTree':TREE,'workingTreeOnly':True,'rootCorrectedCell':ROOT_CELL,
        'rootCorrectedTarget':ROOT_TARGET,'rootCorrectedTargetSha256':sha_text(ROOT_TARGET),
        'rootAdjudicationSha256':sha((OUT/'root-adjudication.json').read_bytes()),
        'catalogFileHashesAfter':after_files,'testsBuildsCIWorkflowsRun':False
    }
    (OUT/'apply-result.json').write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'result':'PASS','appliedChanges':42,'acceptedCurrentPreserved':558,'readbackCells':600,'files':len(fileguards),'rootCell':ROOT_CELL},sort_keys=True))

if __name__=='__main__': main()
