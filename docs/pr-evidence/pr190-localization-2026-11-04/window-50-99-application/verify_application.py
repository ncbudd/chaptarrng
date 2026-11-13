#!/usr/bin/env python3
"""Portable verifier for the ChaptarrNG PR #190 W50-W99 application."""
from __future__ import annotations
import argparse, collections, hashlib, json, re, subprocess, sys
from pathlib import Path
EVIDENCE=Path(__file__).resolve().parent
BUNDLE=EVIDENCE/'cross-audit'
BASE='daa578eaa0d1c252e969d1f5891a364b13d50ec0'
BASE_TREE='e0b306dc20596ad7004bdfb9ac2cc0a3021726c7'
APP='ce6460458a31035c7d3361c9e01148a5a4858ca9'
APP_TREE='17c3ce829ddd7f4ddfa7778d781daa6dec622169'
BULLET='- Apply 149 cross-reviewed translation corrections and refinements across all 12 locale catalogs (W50–W99).'
FORBIDDEN_HOLD_TEXT={'sourceText','currentTarget','primaryProposal','blindProposal','selectedTarget','finalTarget','beforeTarget','postTarget','targetText'}
def sha(b): return hashlib.sha256(b).hexdigest()
def shat(s): return sha(s.encode('utf-8'))
def require(ok,msg):
    if not ok: raise SystemExit('FAIL: '+msg)
def git(repo,*args): return subprocess.check_output(['git','-C',str(repo),*args])
def jsonl(path): return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]
def ident(row): return row['sourceKey'],row['locale']
def token_signature(text):
    return {
      'placeholders':collections.Counter(re.findall(r'\{[^{}]+\}',text)),
      'markupTags':collections.Counter(re.findall(r'</?([A-Za-z][A-Za-z0-9]*)\b[^>]*>',text)),
      'numericTokens':collections.Counter(re.findall(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)*(?![A-Za-z0-9])',text)),
    }
def token_checks(target,source,protected):
    a,b=token_signature(source),token_signature(target)
    return {'placeholders':a['placeholders']==b['placeholders'],'markupTags':a['markupTags']==b['markupTags'],'numericTokens':a['numericTokens']==b['numericTokens'],'protectedLiterals':all(x in target for x in protected)}
def verify_manifest(root,name,exclude_self=False):
    path=root/name; entries={}
    require(path.is_file(),'missing checksum manifest '+str(path))
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        digest,rel=line.split('  ',1); rp=Path(rel)
        require(not rp.is_absolute() and '..' not in rp.parts,'unsafe manifest path '+rel)
        target=(root/rp).resolve()
        require(target.is_relative_to(root.resolve()),'manifest path escapes root '+rel)
        require(rel not in entries,'duplicate manifest entry '+rel)
        require(target.is_file() and sha(target.read_bytes())==digest,'manifest checksum mismatch '+rel)
        entries[rel]=digest
    if exclude_self:
        actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p!=path}
        require(actual==set(entries),'evidence inventory mismatch')
    return len(entries)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',type=Path,default=EVIDENCE.parents[3]); args=ap.parse_args(); repo=args.repo.resolve()
    require(repo.is_dir(),'repo path missing')
    evidence_files=verify_manifest(EVIDENCE,'EVIDENCE-SHA256SUMS.txt',exclude_self=True)
    check=json.loads(subprocess.check_output([sys.executable,str(BUNDLE/'verify_cross_audit.py')],text=True).strip())
    att=json.loads((EVIDENCE/'source-pin-reattestation.json').read_text(encoding='utf-8'))
    summary=json.loads((BUNDLE/'summary.json').read_text(encoding='utf-8'))
    require(check['result']=='PASS' and check['cells']==600 and check['selectedChanges']==149,'cross verifier result mismatch')
    require(att['result']=='PASS' and att['sourceWorktree']=='PASS' and att['head']==BASE and att['tree']==BASE_TREE,'exact-source reattestation mismatch')
    require(summary['exactHead']==BASE and summary['exactTree']==BASE_TREE and summary['inputVerifiers']=={'candidateFree':'PASS','primary':'PASS','blind':'PASS'},'cross summary pin/input mismatch')
    cross=jsonl(BUNDLE/'cross-ledger.jsonl'); selected=jsonl(BUNDLE/'selected-proposals.jsonl'); holds=jsonl(BUNDLE/'holds.jsonl')
    candidates=jsonl(BUNDLE/'input/candidate-primary/candidate-free-cells.jsonl')
    readback=json.loads((EVIDENCE/'application-readback.json').read_text(encoding='utf-8'))
    post=json.loads((EVIDENCE/'application-postflight.json').read_text(encoding='utf-8'))
    keyset={ident(x) for x in cross}; cm={ident(x):x for x in candidates}; xm={ident(x):x for x in cross}; sm={ident(x):x for x in selected}; hm={ident(x):x for x in holds}; rm={ident(x):x for x in readback['rows']}
    require(len(cross)==len(candidates)==len(readback['rows'])==600,'600-cell coverage mismatch')
    require(keyset==set(cm)==set(xm)==set(rm),'cell key sets differ')
    require(len(selected)==149 and len(holds)==84,'selected/hold cardinality mismatch')
    require(set(sm)=={x for x,r in xm.items() if r['crossDisposition'] in ('correction','refinement')},'selected set mismatch')
    require(set(hm)=={x for x,r in xm.items() if r['crossDisposition']=='hold'},'hold set mismatch')
    require(collections.Counter(x['crossDisposition'] for x in cross)==collections.Counter({'correction':68,'refinement':81,'accept-current':367,'hold':84}),'cross disposition counts mismatch')
    require(readback['baseHead']==BASE and readback['baseTree']==BASE_TREE and readback['applicationHead']==APP and readback['applicationTree']==APP_TREE,'readback commit pins mismatch')
    require(post['preflightPrState']=='OPEN' and post['preflightIsDraft'] is True and post['preflightHead']==BASE and post['preflightTree']==BASE_TREE,'PR preflight pin/state mismatch')
    require(post['applicationHead']==APP and post['applicationTree']==APP_TREE and post['applicationParent']==BASE,'postflight catalog commit pin mismatch')
    require(post['testsBuildsScansCiDispatched'] is False and post['nativeSpeakerApproval'] is False and post['browserReview'] is False,'validation-limit assertion mismatch')
    require(git(repo,'rev-parse',BASE).decode().strip()==BASE and git(repo,'show','-s','--format=%T',BASE).decode().strip()==BASE_TREE,'base commit/tree missing')
    require(git(repo,'rev-parse',APP).decode().strip()==APP and git(repo,'show','-s','--format=%T',APP).decode().strip()==APP_TREE,'catalog commit/tree missing')
    require(git(repo,'rev-parse',APP+'^').decode().strip()==BASE,'catalog commit is not direct child of base')
    target_paths=sorted({x['targetFile'] for x in cross}); source_paths={x['sourceFile'] for x in cross}
    require(len(target_paths)==12 and len(source_paths)==1,'catalog inventory mismatch')
    source_path=next(iter(source_paths)); source=json.loads(git(repo,'show',f'{BASE}:{source_path}'))
    files={}; changed=[]; file_rows={x['path']:x for x in readback['catalogFiles']}
    require(set(file_rows)==set(target_paths) and len(file_rows)==12,'readback file set mismatch')
    for rel in target_paths:
        before_raw=git(repo,'show',f'{BASE}:{rel}'); after_raw=git(repo,'show',f'{APP}:{rel}')
        before=json.loads(before_raw); after=json.loads(after_raw)
        require(len(before)==len(after)==4165 and set(before)==set(after),'catalog key count/set mismatch '+rel)
        require(list(before)==list(after),'catalog key order changed '+rel)
        rec=file_rows[rel]
        require(sha(before_raw)==rec['preimageSha256'] and sha(after_raw)==rec['postimageSha256'],'catalog file hash mismatch '+rel)
        require(git(repo,'rev-parse',f'{BASE}:{rel}').decode().strip()==rec['preimageGitBlob'],'catalog preimage blob mismatch '+rel)
        require(git(repo,'rev-parse',f'{APP}:{rel}').decode().strip()==rec['postimageGitBlob'],'catalog postimage blob mismatch '+rel)
        require(rec['keyCount']==4165 and rec['orderedKeysSha256']==shat('\n'.join(before)),'readback catalog shape hash mismatch '+rel)
        files[rel]=(before,after)
        changed.extend((rel,k) for k in before if before[k]!=after[k])
    for cell,row in xm.items():
        c=cm[cell]; rr=rm[cell]; rel=row['targetFile']; sk=row['sourceKey']; before,after=files[rel]
        require(c['targetFile']==rel and c['sourceFile']==row['sourceFile'],'candidate file mismatch '+repr(cell))
        require(shat(source[sk])==row['sourceTextSha256']==c['sourceTextSha256'],'source hash mismatch '+repr(cell))
        require(shat(before[sk])==row['currentTargetSha256']==c['currentTargetSha256'],'preimage target hash mismatch '+repr(cell))
        require(rr['targetFile']==rel and rr['sourceOrdinal']==row['sourceOrdinal'] and rr['crossDisposition']==row['crossDisposition'],'readback row metadata mismatch '+repr(cell))
        require(rr['sourceTextSha256']==row['sourceTextSha256'] and rr['expectedCurrentTargetSha256']==row['currentTargetSha256'] and rr['observedPreTargetSha256']==row['currentTargetSha256'],'readback preimage hash mismatch '+repr(cell))
        if row['crossDisposition']=='hold':
            require(row.get('callerReferenceCount')==0 and cell in hm,'held cell has caller or missing hold record '+repr(cell))
            require(not (FORBIDDEN_HOLD_TEXT & set(row)) and not (FORBIDDEN_HOLD_TEXT & set(rr)),'held cell text leakage '+repr(cell))
            require(hm[cell]['currentTargetSha256']==row['currentTargetSha256'] and hm[cell]['sourceTextSha256']==row['sourceTextSha256'],'hash-only hold record mismatch '+repr(cell))
            require(rr['expectedFinalTargetSha256']==row['currentTargetSha256']==rr['observedPostTargetSha256'] and rr['matches'] is True,'hold postimage mismatch '+repr(cell))
            require(before[sk]==after[sk],'held catalog cell changed '+repr(cell))
            continue
        require(row.get('sourceText')==source[sk] and row.get('currentTarget')==before[sk],'cross source/preimage text mismatch '+repr(cell))
        require(rr.get('currentTarget')==before[sk],'readback missing/exact preimage text mismatch '+repr(cell))
        expected=row['selectedTarget'] if row['crossDisposition'] in ('correction','refinement') else row['currentTarget']
        require(after[sk]==expected and rr.get('finalTarget')==expected,'final target mismatch '+repr(cell))
        require(rr['expectedFinalTargetSha256']==rr['observedPostTargetSha256']==shat(expected) and rr['matches'] is True,'readback postimage hash mismatch '+repr(cell))
        checks=token_checks(expected,source[sk],c.get('protectedLiterals',[]))
        require(all(checks.values()) and checks==row['selectedTokenChecks']==rr['selectedTokenChecks'],'placeholder/markup/numeric/protected literal parity mismatch '+repr(cell))
    expected_changed={(xm[cell]['targetFile'],cell[0]) for cell in sm}
    require(set(changed)==expected_changed and len(changed)==149,'catalog delta is not exactly the selected 149 cells')
    paths=git(repo,'diff-tree','--no-commit-id','--name-only','-r',BASE,APP).decode().splitlines()
    require(sorted(paths)==sorted(target_paths+['CHANGELOG.md']),'catalog commit changed unexpected paths')
    workflow=[p for p in paths if p.startswith('.github/workflows/')]
    require(not workflow and post['workflowPathCount']==0,'workflow path changed')
    before_log=git(repo,'show',f'{BASE}:CHANGELOG.md').decode('utf-8'); after_log=git(repo,'show',f'{APP}:CHANGELOG.md').decode('utf-8')
    require(after_log.count(BULLET)==1 and before_log.count(BULLET)==0 and after_log.replace(BULLET+'\n','',1)==before_log,'changelog diff mismatch')
    print(json.dumps({'result':'PASS','baseHead':BASE,'baseTree':BASE_TREE,'catalogCommit':APP,'catalogTree':APP_TREE,'evidenceFilesChecksummed':evidence_files,'crossBundleChecks':check.get('checksummedFiles'),'sourcePinReattestation':att['result'],'inputVerifiers':check.get('inputVerifiers'),'cells':600,'selected':149,'corrections':68,'refinements':81,'acceptedCurrent':367,'hashOnlyHolds':84,'callerlessKeys':7,'catalogFiles':len(target_paths),'catalogKeysPerLocale':4165,'changedCatalogValues':len(changed),'workflowPathCount':len(workflow),'nativeSpeakerApproval':False,'browserReview':False},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
