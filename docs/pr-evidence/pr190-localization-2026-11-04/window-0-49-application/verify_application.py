#!/usr/bin/env python3
"""Verify W0–W49 packet integrity and the exact ChaptarrNG catalog application."""
from __future__ import annotations
import argparse,hashlib,json,re,subprocess,sys
from collections import Counter
from pathlib import Path

EVIDENCE=Path(__file__).resolve().parent
BUNDLE=EVIDENCE/'cross-audit'
BASE='7f5d99e24b054cf1437d135328c3dee565e6b318'
BASE_TREE='d39f2fe8cf91a39653679980c0832c5ca400a114'
APP='3e9ef37d39301126dfc3631a80ba09fbe46f5211'
APP_TREE='30dee7612b72adf2032a295abd25acd74db55539'
CHANGELOG_BULLET='- Apply 38 context-matched translation corrections across 11 locales, including AudioBookShelf library labels, torrent adoption prompts, and author-folder help.'
HOLD_KEYS={'AddAuthorMonitorNewAudiobooksHelpText','AddAuthorMonitorNewEbooksHelpText','AddAuthorWhichAudiobooksToMonitor','AddAuthorWhichEbooksToMonitor'}

def sha(b): return hashlib.sha256(b).hexdigest()
def shat(s): return sha(s.encode('utf-8'))
def fail(message): raise SystemExit('FAIL: '+message)
def need(condition,message):
    if not condition: fail(message)
def git(repo,*args): return subprocess.check_output(['git','-C',str(repo),*args])
def jlines(path): return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]
def k(row): return (row['sourceKey'],row['locale'])
def checked_manifest(root,filename):
    manifest=root/filename
    need(manifest.is_file(),f'missing checksum manifest: {manifest}')
    seen=set()
    for line in manifest.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        digest,rel=line.split('  ',1)
        path=(root/rel).resolve()
        need(path.is_relative_to(root.resolve()),f'checksum path escapes root: {rel}')
        need(path.is_file() and sha(path.read_bytes())==digest,f'checksum mismatch: {rel}')
        need(rel not in seen,f'duplicate checksum path: {rel}')
        seen.add(rel)
    return len(seen)
def verify_evidence_manifest():
    manifest=EVIDENCE/'EVIDENCE-SHA256SUMS.txt'
    need(manifest.is_file(),'missing EVIDENCE-SHA256SUMS.txt')
    listed={}
    for line in manifest.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        digest,rel=line.split('  ',1)
        path=(EVIDENCE/rel).resolve()
        need(path.is_relative_to(EVIDENCE.resolve()),f'evidence checksum path escapes: {rel}')
        need(path.is_file() and sha(path.read_bytes())==digest,f'evidence checksum mismatch: {rel}')
        need(rel not in listed,f'duplicate evidence checksum: {rel}')
        listed[rel]=digest
    actual={p.relative_to(EVIDENCE).as_posix() for p in EVIDENCE.rglob('*') if p.is_file() and p!=manifest}
    need(actual==set(listed),f'evidence checksum file set differs: unlisted={sorted(actual-set(listed))}, stale={sorted(set(listed)-actual)}')
    return len(listed)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('repo',nargs='?',type=Path,default=Path(__file__).resolve().parents[6],help='ChaptarrNG repository worktree containing the pinned commits')
    args=ap.parse_args(); repo=args.repo.resolve()
    need(repo.is_dir(),'repository path missing')
    evidence_count=verify_evidence_manifest()
    inner_counts={
        'candidatePrimary':checked_manifest(BUNDLE/'input/candidate-primary','SHA256SUMS'),
        'blindPacket':checked_manifest(BUNDLE/'input/blind','SHA256SUMS.txt'),
        'blindNestedInput':checked_manifest(BUNDLE/'input/blind/input','SHA256SUMS.txt'),
    }
    # Re-run the cross-bundle verifier over its copied, checksummed inputs.
    subprocess.run([sys.executable,str(BUNDLE/'verify_cross_audit.py')],check=True,stdout=subprocess.PIPE,text=True)
    post=json.loads((EVIDENCE/'application-postflight.json').read_text(encoding='utf-8'))
    need(post['baseHead']==BASE and post['baseTree']==BASE_TREE,'postflight base pin mismatch')
    need(post['applicationHead']==APP and post['applicationTree']==APP_TREE,'postflight application pin mismatch')
    need(post['applicationParent']==BASE,'application parent mismatch')
    need(post['preflightPrState']=='OPEN' and post['preflightIsDraft'] is True and post['preflightHead']==BASE,'preflight PR state/head mismatch')
    need(post['workflowPathCount']==0,'postflight reports workflow path changes')
    need(git(repo,'rev-parse',BASE).decode().strip()==BASE,'base commit is missing')
    need(git(repo,'show','-s','--format=%T',BASE).decode().strip()==BASE_TREE,'base tree mismatch')
    need(git(repo,'rev-parse',APP).decode().strip()==APP,'application commit is missing')
    need(git(repo,'show','-s','--format=%T',APP).decode().strip()==APP_TREE,'application tree mismatch')
    need(git(repo,'rev-parse',APP+'^').decode().strip()==BASE,'application commit parent mismatch')

    candidates=jlines(BUNDLE/'input/candidate-primary/candidate-free-cells.jsonl')
    cross=jlines(BUNDLE/'cross-ledger.jsonl')
    proposals=jlines(BUNDLE/'selected-proposals.jsonl')
    holds=jlines(BUNDLE/'cross-audit-holds.jsonl')
    rb=json.loads((EVIDENCE/'application-readback.json').read_text(encoding='utf-8'))
    need(len(candidates)==len(cross)==len(rb['rows'])==600,'expected 600 candidates, cross rows, and readbacks')
    need(len(proposals)==38 and len(holds)==48,'proposal/hold count mismatch')
    cm={k(x):x for x in candidates}; xm={k(x):x for x in cross}; pm={k(x):x for x in proposals}; hm={k(x):x for x in holds}; rm={k(x):x for x in rb['rows']}
    need(len(cm)==600 and set(cm)==set(xm)==set(rm),'cell-key sets differ')
    need(set(pm)=={ident for ident,x in xm.items() if x['crossDisposition']=='revise-current'},'selected set mismatch')
    need(set(hm)=={ident for ident,x in xm.items() if x['crossDisposition']=='hold'},'hold set mismatch')
    need(rb['baseHead']==BASE and rb['baseTree']==BASE_TREE and rb['applicationHead']==APP and rb['applicationTree']==APP_TREE,'readback commit pins mismatch')

    # Verify all 13 source/target catalogs and 852 expanded caller references from BASE.
    base_file_cache={}
    def base_file(path):
        if path not in base_file_cache: base_file_cache[path]=git(repo,'show',f'{BASE}:{path}')
        return base_file_cache[path]
    catalog_records={}
    for c in candidates:
        for role,path_key,sha_key,blob_key in [('source','sourceFile','sourceFileSha256','sourceFileGitBlob'),('target','targetFile','targetFileSha256','targetFileGitBlob')]:
            path=c[path_key]; raw=base_file(path)
            need(sha(raw)==c[sha_key],f'{role} catalog SHA mismatch: {path}')
            need(git(repo,'rev-parse',f'{BASE}:{path}').decode().strip()==c[blob_key],f'{role} catalog blob mismatch: {path}')
            data=catalog_records.setdefault(path,json.loads(raw))
            expected=c['sourceText'] if role=='source' else c['currentTarget']
            need(data.get(c['sourceKey'])==expected,f'{role} catalog value mismatch: {c["sourceKey"]}/{c["locale"]}')
    caller_files={}; caller_refs=0
    for c in candidates:
        need(c['callerReferenceCount']==len(c['callerRefs']),f'caller count mismatch: {k(c)}')
        for ref in c['callerRefs']:
            path=ref['path']; raw=base_file(path)
            need(sha(raw)==ref['fileSha256'],f'caller file SHA mismatch: {path}')
            need(git(repo,'rev-parse',f'{BASE}:{path}').decode().strip()==ref['fileGitBlob'],f'caller file blob mismatch: {path}')
            lines=raw.decode('utf-8').splitlines()
            need(1<=ref['line']<=len(lines),f'caller line outside file: {path}:{ref["line"]}')
            line=lines[ref['line']-1]
            need(line==ref['lineText'] and shat(line)==ref['lineSha256'],f'caller line mismatch: {path}:{ref["line"]}')
            caller_files[path]=True; caller_refs+=1

    file_rows={r['path']:r for r in rb['catalogFiles']}
    paths=sorted({c['targetFile'] for c in candidates})
    need(len(paths)==12 and set(paths)==set(file_rows),'catalog readback file set mismatch')
    changed=[]
    for rel in paths:
        before=base_file(rel)
        after=git(repo,'show',f'{APP}:{rel}')
        b=json.loads(before); a=json.loads(after)
        need(list(b)==list(a),'catalog key ordering changed: '+rel)
        need(len(b)==len(a)==4165 and set(b)==set(a),'catalog key set/count changed: '+rel)
        f=file_rows[rel]
        need(sha(before)==f['preimageSha256'] and sha(after)==f['postimageSha256'],'catalog file SHA readback mismatch: '+rel)
        need(git(repo,'rev-parse',f'{BASE}:{rel}').decode().strip()==f['preimageGitBlob'],'catalog preimage blob mismatch: '+rel)
        need(git(repo,'rev-parse',f'{APP}:{rel}').decode().strip()==f['postimageGitBlob'],'catalog postimage blob mismatch: '+rel)
        by_cell={(c['sourceKey'],c['locale']):c for c in candidates if c['targetFile']==rel}
        for key,value in b.items():
            if value!=a[key]: changed.append((rel,key))
            if key in {src for src,loc in by_cell}:
                # All 50 reviewed source keys in this locale must be re-read.
                row=next(c for c in candidates if c['targetFile']==rel and c['sourceKey']==key)
                ident=k(row); rr=rm[ident]; cc=xm[ident]
                observed_hash=shat(a[key])
                expected_hash=pm[ident]['selectedTargetSha256'] if ident in pm else row['currentTargetSha256']
                need(rr['observedFinalTargetSha256']==observed_hash==rr['expectedFinalTargetSha256']==expected_hash and rr['matches'] is True,f'readback hash mismatch: {ident}')
                need(rr['currentTargetSha256']==row['currentTargetSha256'] and rr['sourceTextSha256']==row['sourceTextSha256'],f'readback source/current hash mismatch: {ident}')
                need(rr['crossDisposition']==cc['crossDisposition'],f'readback disposition mismatch: {ident}')
                if ident in hm:
                    need(a[key]==b[key] and rr.get('proposedTarget') is None,f'held cell changed or has proposal text: {ident}')
                    need(not any(field in rr for field in ('sourceText','currentTarget','selectedTarget','targetText')),f'held readback contains text: {ident}')
                elif ident in pm:
                    need(a[key]==pm[ident]['selectedTarget'],f'selected value mismatch: {ident}')
                else:
                    need(a[key]==b[key],f'accepted-current value changed: {ident}')
    expected_changes={(p['targetFile'],p['sourceKey']) for p in proposals}
    need(set(changed)==expected_changes and len(changed)==38,'catalog changed-value set is not exactly 38 selected cells')
    need(Counter(r['crossDisposition'] for r in rb['rows'])==Counter({'accept-current':514,'revise-current':38,'hold':48}),'readback counts mismatch')

    paths_changed=git(repo,'diff-tree','--no-commit-id','--name-only','-r',BASE,APP).decode().splitlines()
    expected_paths=sorted({p['targetFile'] for p in proposals}|{'CHANGELOG.md'})
    need(sorted(paths_changed)==expected_paths,'application commit contains unexpected paths')
    workflow=[p for p in paths_changed if p.startswith('.github/workflows/')]
    need(not workflow,'workflow path changed')
    before_log=base_file('CHANGELOG.md').decode('utf-8')
    after_log=git(repo,'show',f'{APP}:CHANGELOG.md').decode('utf-8')
    need(after_log.count(CHANGELOG_BULLET)==1 and before_log.count(CHANGELOG_BULLET)==0,'changelog entry mismatch')
    need(after_log.replace(CHANGELOG_BULLET+'\n','',1)==before_log,'unexpected changelog changes')

    print(json.dumps({'result':'PASS','baseHead':BASE,'baseTree':BASE_TREE,'applicationHead':APP,'applicationTree':APP_TREE,'bundleFilesChecksummed':evidence_count,'inputManifestEntries':inner_counts,'cells':600,'selected':38,'holds':48,'acceptedCurrent':514,'changedCatalogValues':len(changed),'catalogFiles':len(paths),'catalogKeyCountPerLocale':4165,'callerFiles':len(caller_files),'expandedCallerReferences':caller_refs,'workflowPathCount':len(workflow),'repoStatusChecked':False},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
