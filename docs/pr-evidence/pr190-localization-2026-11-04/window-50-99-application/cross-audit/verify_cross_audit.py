#!/usr/bin/env python3
"""Portable verifier for ChaptarrNG PR #190 W50-W99 cross-review."""
from __future__ import annotations
import argparse, collections, hashlib, json, re, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
HEAD='daa578eaa0d1c252e969d1f5891a364b13d50ec0'
TREE='e0b306dc20596ad7004bdfb9ac2cc0a3021726c7'
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
FORBIDDEN_HOLD_TEXT={'sourceText','currentTarget','primaryProposal','blindProposal','selectedTarget','finalTarget'}
def sha(x): return hashlib.sha256(x).hexdigest()
def jsonl(p): return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s.strip()]
def git(w,*args): return subprocess.check_output(['git','-C',str(w),*args],text=True).strip()
def require(ok,msg):
    if not ok: raise ValueError(msg)
def run_json(cmd):
    lines=[x for x in subprocess.check_output(cmd,text=True).splitlines() if x.strip()]
    return json.loads(lines[-1])
def check_sum_list(folder,name,expected_files=None):
    path=folder/name; entries={}
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line: continue
        digest,rel=line.split('  ',1); rp=Path(rel)
        require(not rp.is_absolute() and '..' not in rp.parts,'unsafe checksum path '+rel)
        require(rel not in entries,'duplicate checksum path '+rel)
        target=(folder/rp).resolve(); require(target.is_relative_to(folder.resolve()),'checksum escapes packet '+rel)
        require(target.is_file() and sha(target.read_bytes())==digest,'checksum mismatch '+rel)
        entries[rel]=digest
    if expected_files is not None:
        actual={p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file() and p.name!=name}
        require(set(entries)==actual,'nested checksum inventory mismatch '+str(folder))
    return entries
def token_signature(text):
    return {
        'placeholders':collections.Counter(re.findall(r'\{[^{}]+\}',text)),
        'markupTags':collections.Counter(re.findall(r'</?([A-Za-z][A-Za-z0-9]*)\b[^>]*>',text)),
        'numericTokens':collections.Counter(re.findall(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)*(?![A-Za-z0-9])',text)),
    }
def token_checks(text,source,protected):
    a=token_signature(source); b=token_signature(text)
    return {'placeholders':a['placeholders']==b['placeholders'],'markupTags':a['markupTags']==b['markupTags'],'numericTokens':a['numericTokens']==b['numericTokens'],'protectedLiterals':all(x in text for x in protected)}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source-worktree',type=Path); args=ap.parse_args()
    top=ROOT/'SHA256SUMS.txt'; outer={}
    for line in top.read_text(encoding='utf-8').splitlines():
        digest,rel=line.split('  ',1); rp=Path(rel)
        require(not rp.is_absolute() and '..' not in rp.parts,'unsafe top-level checksum '+rel)
        target=(ROOT/rp).resolve(); require(target.is_relative_to(ROOT.resolve()),'top checksum escapes bundle '+rel)
        require(target.is_file() and sha(target.read_bytes())==digest,'top checksum mismatch '+rel)
        require(rel not in outer,'duplicate top checksum '+rel); outer[rel]=digest
    actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and p!=top}
    require(set(outer)==actual,'top checksum inventory mismatch')
    primary=ROOT/'input/candidate-primary'; blind=ROOT/'input/blind'
    check_sum_list(primary,'SHA256SUMS.txt')
    check_sum_list(primary,'candidate-free-SHA256SUMS.txt')
    check_sum_list(primary,'primary-review-SHA256SUMS.txt')
    check_sum_list(blind,'OUTPUT-SHA256SUMS.txt')
    check_sum_list(blind/'input','candidate-free-SHA256SUMS.txt')
    checks={
      'candidateFree':run_json([sys.executable,str(primary/'verify_candidate_free.py')]),
      'primary':run_json([sys.executable,str(primary/'primary-review/verify_primary_review.py')]),
      'blind':run_json([sys.executable,str(blind/'verify_blind_review.py')]),
    }
    require(all(v.get('result')=='PASS' for v in checks.values()),'one or more input verifiers failed')
    require(checks['candidateFree'].get('exactHead')==HEAD and checks['candidateFree'].get('exactTree')==TREE,'candidate-free verifier pin mismatch')
    require(checks['primary'].get('exactHead')==HEAD and checks['primary'].get('exactTree')==TREE,'primary verifier pin mismatch')
    require(checks['blind'].get('exactHead')==HEAD and checks['blind'].get('exactTree')==TREE,'blind verifier pin mismatch')
    cand=jsonl(primary/'candidate-free-cells.jsonl'); p_rows=jsonl(primary/'primary-review/primary-review-cells.jsonl'); b_rows=jsonl(blind/'blind-review-ledger.jsonl')
    pp_rows=jsonl(primary/'primary-review/primary-review-proposals.jsonl'); bp_rows=jsonl(blind/'proposals.jsonl')
    contexts={r['sourceKey']:r for r in jsonl(primary/'caller-context.jsonl')}; keys=json.loads((primary/'source-selection.json').read_text())['keys']
    current={(r['sourceKey'],r['locale']):r for r in cand}; pby={(r['sourceKey'],r['locale']):r for r in p_rows}; bby={(r['sourceKey'],r['locale']):r for r in b_rows}
    pp={(r['sourceKey'],r['locale']):r for r in pp_rows}; bp={(r['sourceKey'],r['locale']):r for r in bp_rows}
    expected={(k,l) for k in keys for l in LOCALES}
    require(len(cand)==len(p_rows)==len(b_rows)==600 and set(current)==set(pby)==set(bby)==expected,'input cell coverage mismatch')
    ledger=jsonl(ROOT/'cross-ledger.jsonl'); chosen=jsonl(ROOT/'selected-proposals.jsonl'); holds=jsonl(ROOT/'holds.jsonl'); disagreements=jsonl(ROOT/'proposal-disagreements.jsonl')
    by={(r['sourceKey'],r['locale']):r for r in ledger}; require(len(by)==600 and set(by)==expected,'cross-ledger coverage/duplicates mismatch')
    selected_by={(r['sourceKey'],r['locale']):r for r in chosen}; require(len(selected_by)==149,'selected proposal count mismatch')
    hold_by={(r['sourceKey'],r['locale']):r for r in holds}; require(len(hold_by)==84,'hold count mismatch')
    callerless={(k,l) for k,v in contexts.items() if v['callerReferenceCount']==0 for l in LOCALES}
    require(set(hold_by)==callerless,'callerless holds do not match exact input context')
    for cell,row in by.items():
        k,l=cell; c=current[cell]; pr=pby[cell]; br=bby[cell]; ctx=contexts[k]
        require(row['exactHead']==HEAD and row['exactTree']==TREE,'cross row pin mismatch '+repr(cell))
        require(row['sourceTextSha256']==c['sourceTextSha256'] and row['currentTargetSha256']==c['currentTargetSha256'] and row['callerContextSha256']==c['callerContextSha256'],'cross row hash linkage mismatch '+repr(cell))
        require(row['primaryDisposition']==pr['primaryDisposition'] and row['blindDisposition']==br['disposition'],'cross dispositions mismatch '+repr(cell))
        require(row['proposalOverlap']==(cell in set(pp)&set(bp)),'proposal overlap flag mismatch '+repr(cell))
        if cell in callerless:
            require(row['crossDisposition']=='hold','callerless cell not held '+repr(cell))
            require(not (FORBIDDEN_HOLD_TEXT & set(row)),'text leaked into cross hold '+repr(cell))
            require(row.get('callerReferenceCount')==0 and row.get('selectedTargetSha256') is None,'hold is not hash-only '+repr(cell))
            continue
        require(row['callerReferenceCount']==ctx['callerReferenceCount'] and row['callerRefs']==ctx['callerRefs'],'caller evidence mismatch '+repr(cell))
        require(row['sourceText']==c['sourceText'] and row['currentTarget']==c['currentTarget'],'source/current text linkage mismatch '+repr(cell))
        target=row['selectedTarget']; require(isinstance(target,str) and target,'empty final target '+repr(cell))
        expected_target=token_checks(target,c['sourceText'],c.get('protectedLiterals',[]))
        require(all(expected_target.values()) and row['selectedTokenChecks']==expected_target,'token/protected parity mismatch '+repr(cell))
        require(row['selectedTargetSha256']==sha(target.encode('utf-8')),'selected target hash mismatch '+repr(cell))
        if row['crossDisposition']=='accept-current':
            require(target==c['currentTarget'] and cell not in selected_by,'accepted current changed or listed selected '+repr(cell))
        else:
            require(row['crossDisposition'] in ('correction','refinement') and cell in selected_by,'changed cell missing selected ledger '+repr(cell))
            s=selected_by[cell]; require(s['selectedTarget']==target and s['selectedTargetSha256']==row['selectedTargetSha256'] and s['crossDisposition']==row['crossDisposition'],'selected proposal ledger mismatch '+repr(cell))
            origin=s['selectedFromProposal']
            if origin=='primary': require(cell in pp and target==pp[cell]['recommendedTarget'],'selected primary target mismatch '+repr(cell))
            elif origin=='blind': require(cell in bp and target==bp[cell]['selectedTarget'],'selected blind target mismatch '+repr(cell))
            else: require(origin is None,'invalid custom-selection source '+repr(cell))
    counts=collections.Counter(r['crossDisposition'] for r in ledger)
    require(counts==collections.Counter({'correction':68,'refinement':81,'accept-current':367,'hold':84}),'cross disposition counts mismatch '+repr(counts))
    union=set(pp)|set(bp); overlap=set(pp)&set(bp); same={x for x in overlap if pp[x]['recommendedTarget']==bp[x]['selectedTarget']}; diff=overlap-same
    require((len(pp),len(bp),len(union),len(overlap),len(same),len(diff))==(139,58,166,31,19,12),'proposal union metrics mismatch')
    dby={(r['sourceKey'],r['locale']):r for r in disagreements}; require(set(dby)==diff and len(dby)==12,'different-target disagreement coverage mismatch')
    require(sum(bool(x['resolved']) for x in disagreements)==11 and sum(not x['resolved'] for x in disagreements)==1,'disagreement status count mismatch')
    for cell,d in dby.items():
        if cell in callerless:
            require(d['crossDisposition']=='hold' and d['primaryTarget'] is None and d['blindTarget'] is None and d['selectedTarget'] is None,'held disagreement leaks text '+repr(cell))
        else:
            require(d['resolved'] is True and d['crossDisposition']==by[cell]['crossDisposition'],'contextual disagreement not reconciled '+repr(cell))
    summary=json.loads((ROOT/'summary.json').read_text()); attest=json.loads((ROOT/'input-attestation.json').read_text())
    require(summary['exactHead']==HEAD and summary['exactTree']==TREE and summary['crossDispositionCounts']==dict(counts),'summary pin/count mismatch')
    require(summary['proposalUnionCount']==166 and summary['textFreeHoldCount']==84 and summary['selectedProposalCount']==149,'summary metrics mismatch')
    require(attest['head']==HEAD and attest['tree']==TREE and attest['prBefore']['head']==HEAD and attest['prAfter']['head']==HEAD and attest['prBefore']['state']=='OPEN' and attest['prAfter']['state']=='OPEN' and attest['prBefore']['draft'] is True and attest['prAfter']['draft'] is True,'input PR attestation mismatch')
    optional={}
    if args.source_worktree:
        w=args.source_worktree.resolve()
        require(git(w,'rev-parse','HEAD')==HEAD and git(w,'show','-s','--format=%T','HEAD')==TREE and not git(w,'status','--porcelain'),'source worktree pin/status mismatch')
        optional['sourceWorktree']='PASS'
    print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'sourceKeys':50,'locales':12,'cells':600,'primaryProposals':139,'blindProposals':58,'proposalUnion':166,'overlap':31,'sameTarget':19,'differentTarget':12,'corrections':68,'refinements':81,'acceptedCurrent':367,'selectedChanges':149,'textFreeHolds':84,'callerlessKeys':7,'callerlessProposalCellsHeld':18,'differentTargetOverlapsResolved':11,'differentTargetOverlapsHeld':1,'tokenMismatches':0,'inputVerifiers':{k:'PASS' for k in checks},'sourceWorktree':optional.get('sourceWorktree'),'checksummedFiles':len(outer)},ensure_ascii=False,sort_keys=True))
if __name__=='__main__':
    try: main()
    except Exception as e: print('FAIL:',e,file=sys.stderr); raise SystemExit(1)
