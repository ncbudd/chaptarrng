#!/usr/bin/env python3
from __future__ import annotations
import argparse, collections, hashlib, json, re, subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parents[1]
DEFAULT_REPO=Path('/mnt/disks/scratch/task-worktrees/localization-20261104/chaptarrng-pr190-w0-49-apply')
HEAD='daa578eaa0d1c252e969d1f5891a364b13d50ec0'
TREE='e0b306dc20596ad7004bdfb9ac2cc0a3021726c7'
TARGET_LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
PLACEHOLDER_RE=re.compile(r'\{[^{}]+\}')
PROTECTED_RE=re.compile(r'\b(?:[A-Z][A-Z0-9]{1,}|[A-Z]+[0-9][A-Z0-9]*)\b')
PROTECTED_BRANDS={'Chaptarr','ChaptarrNG','AudioBookShelf'}
HOLD_KEYS={'AddMissing','AddRootFolderInlineIntroAllMediaType','AddRootFolderInlineIntroPrefix','AddRootFolderInlineIntroSuffix','AddRootFolderInlineRootFolderLabel'}

def sha(b):return hashlib.sha256(b).hexdigest()
def sha_text(s):return sha(s.encode('utf-8'))
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
def signature(s):return dict(sorted(collections.Counter(PLACEHOLDER_RE.findall(s)).items()))
def literals(s):return sorted(set(PROTECTED_RE.findall(s)) | (PROTECTED_BRANDS & set(re.findall(r'\b[A-Za-z][A-Za-z0-9]*\b',s))))
def jsonl(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def fail(s):raise SystemExit('FAIL: '+s)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source-worktree',type=Path,default=DEFAULT_REPO);args=ap.parse_args();repo=args.source_worktree.resolve()
    if git(repo,'rev-parse','HEAD')!=HEAD:fail('source HEAD differs')
    if git(repo,'rev-parse','HEAD^{tree}')!=TREE:fail('source tree differs')
    if git(repo,'status','--porcelain=v1'):fail('source worktree is not clean')
    subprocess.run(['python',str(HERE/'verify_candidate_free.py'),'--source-worktree',str(repo)],check=True)
    subprocess.run(['sha256sum','-c','candidate-free-SHA256SUMS.txt'],cwd=HERE,check=True,stdout=subprocess.DEVNULL)
    inp=jsonl(HERE/'candidate-free-cells.jsonl')
    source_sel=json.loads((HERE/'source-selection.json').read_text(encoding='utf-8'))
    selection_hash=sha((HERE/'source-selection.json').read_bytes())
    rows=jsonl(HERE/'primary-review/primary-review-cells.jsonl')
    proposals=jsonl(HERE/'primary-review/primary-review-proposals.jsonl')
    holds=jsonl(HERE/'primary-review/primary-review-holds.jsonl')
    summary=json.loads((HERE/'primary-review/primary-review-summary.json').read_text(encoding='utf-8'))
    if len(inp)!=600 or len(rows)!=600:fail('cell count')
    inp_map={(x['sourceKey'],x['locale']):x for x in inp}
    if len(inp_map)!=600:fail('candidate duplicate cells')
    if [r['sourceOrdinal'] for r in rows]!=[c['sourceOrdinal'] for c in inp]:fail('row order/ordinal')
    if [r['cellId'] for r in rows]!=[f"{c['sourceKey']}::{c['locale']}" for c in inp]:fail('cell order')
    if len({r['cellId'] for r in rows})!=600:fail('review duplicate cells')
    if summary['exactHead']!=HEAD or summary['exactTree']!=TREE:fail('summary source pin')
    if summary['sourceSelectionSha256']!=selection_hash:fail('summary selection hash')
    if summary['candidateFreeCellsSha256']!=sha((HERE/'candidate-free-cells.jsonl').read_bytes()):fail('summary candidate hash')
    seen_proposals=set();seen_holds=set();revision_rows=[];hold_rows=[];counts=collections.Counter();locale_counts=collections.Counter()
    hold_text_fields={'sourceText','currentTarget','finalReviewedTargetText','recommendedTargetText'}
    input_lines=[line.rstrip(b'\n') for line in (HERE/'candidate-free-cells.jsonl').read_bytes().splitlines(keepends=True) if line.strip()]
    if len(input_lines)!=600:fail('raw candidate line count')
    for i,(r,c) in enumerate(zip(rows,inp)):
        ident=(c['sourceKey'],c['locale']);cell=f'{ident[0]}::{ident[1]}'
        if r['sourceKey']!=c['sourceKey'] or r['locale']!=c['locale']:fail('candidate/review identity '+cell)
        if r['sourceSelectionSha256']!=selection_hash:fail('row source-selection link '+cell)
        if r['candidateFreeRowSha256']!=sha(input_lines[i]):fail('candidate-free row hash '+cell)
        if r['sourceTextSha256']!=c['sourceTextSha256'] or r['currentTargetSha256']!=c['currentTargetSha256']:fail('candidate hash linkage '+cell)
        if r['callerContextSha256']!=c['callerContextSha256'] or r['callerReferenceCount']!=c['callerReferenceCount']:fail('caller linkage '+cell)
        if r['exactHead']!=HEAD or r['exactTree']!=TREE:fail('row source pin '+cell)
        if r['nativeSpeakerApproval'] is not False or r['nativeSpeakerReviewOutstanding'] is not True:fail('native-speaker flags '+cell)
        d=r['primaryDisposition'];counts[d]+=1
        if d=='hold':
            if c['sourceKey'] not in HOLD_KEYS:fail('unexpected hold '+cell)
            if any(k in r and r[k] not in (None,[]) for k in hold_text_fields):fail('hold contains text '+cell)
            if r.get('semanticInterpretation') is not None:fail('hold contains text interpretation '+cell)
            if r['recommendedTarget'] is not None or r['finalReviewedTarget'] is not None:fail('hold contains target '+cell)
            if r['reviewConfidence']!='low' or r['placeholderParity'] is not None:fail('hold review state '+cell)
            hold_rows.append({k:r[k] for k in ('batch','sourceOrdinal','sourceKey','locale','cellId','sourceTextSha256','currentTargetSha256','callerContextSha256','callerReferenceCount','candidateFreeRowSha256','sourceSelectionSha256','primaryDisposition','holdRationale','reviewConfidence')})
            seen_holds.add(cell)
            continue
        if d not in {'accept-current','revise-current'}:fail('unknown disposition '+cell)
        for field in ('sourceText','currentTarget','finalReviewedTarget','finalReviewedTargetSha256','decisionRationale'):
            if not isinstance(r.get(field),str):fail('missing reviewed text field '+field+' '+cell)
        if r['sourceText']!=c['sourceText'] or r['currentTarget']!=c['currentTarget']:fail('source/current text linkage '+cell)
        if sha_text(r['finalReviewedTarget'])!=r['finalReviewedTargetSha256']:fail('final target hash '+cell)
        if signature(r['finalReviewedTarget'])!=c['sourcePlaceholders']:fail('final placeholder parity '+cell)
        if r['finalPlaceholders']!=signature(r['finalReviewedTarget']) or r['placeholderParity'] is not True:fail('placeholder metadata '+cell)
        if r['protectedLiterals']!=c['protectedLiterals'] or r['protectedLiteralDisposition']!='pass':fail('protected literal metadata '+cell)
        expected_checks=[{'literal':lit,'currentPresent':lit in c['currentTarget'],'currentExactCase':lit in c['currentTarget'],'finalPresent':lit in r['finalReviewedTarget'],'finalExactCase':lit in r['finalReviewedTarget']} for lit in c['protectedLiterals']]
        if r['protectedLiteralChecks']!=expected_checks or not all(x['finalPresent'] and x['finalExactCase'] for x in expected_checks):fail('protected literal check '+cell)
        if d=='accept-current':
            if r['finalReviewedTarget']!=c['currentTarget'] or r['recommendedTarget'] is not None or r['recommendedTargetSha256'] is not None:fail('accept-current target mismatch '+cell)
        else:
            if r['finalReviewedTarget']==c['currentTarget'] or r['recommendedTarget']!=r['finalReviewedTarget']:fail('revision target mismatch '+cell)
            if r['recommendedTargetSha256']!=r['finalReviewedTargetSha256']:fail('revision hash mismatch '+cell)
            revision_rows.append({'batch':'W50-99','sourceOrdinal':r['sourceOrdinal'],'sourceKey':r['sourceKey'],'locale':r['locale'],'cellId':cell,'currentTargetSha256':r['currentTargetSha256'],'recommendedTarget':r['recommendedTarget'],'recommendedTargetSha256':r['recommendedTargetSha256'],'callerContextSha256':r['callerContextSha256'],'candidateFreeRowSha256':r['candidateFreeRowSha256'],'sourceSelectionSha256':selection_hash,'rationale':r['decisionRationale']})
            locale_counts[r['locale']]+=1
        if r['reviewConfidence']!='moderate':fail('review confidence '+cell)
    if len(seen_holds)!=60 or len(revision_rows)!=139 or counts!={'accept-current':401,'revise-current':139,'hold':60}:fail('disposition totals')
    if set(r['sourceKey'] for r in rows if r['primaryDisposition']=='hold')!=HOLD_KEYS:fail('hold key set')
    if proposals!=revision_rows:fail('proposal file does not match review ledger')
    if holds!=hold_rows:fail('hold file does not match review ledger')
    if len({r['cellId'] for r in proposals})!=len(proposals) or len({r['cellId'] for r in holds})!=len(holds):fail('duplicate proposal or hold')
    if any(any(field in h for field in ('sourceText','currentTarget','recommendedTarget','finalReviewedTarget')) for h in holds):fail('text found in hold packet')
    if summary['counts']!={'cells':600,'sourceKeys':50,'locales':12,'acceptCurrent':401,'reviseCurrent':139,'hold':60,'callerlessCells':84,'callerlessKeys':7,'nativeSpeakerApproval':0,'nativeSpeakerReviewOutstanding':600}:fail('summary counts')
    if summary['revisionCellIds']!=[r['cellId'] for r in rows if r['primaryDisposition']=='revise-current']:fail('summary revision IDs')
    if summary['holdCellIds']!=[r['cellId'] for r in rows if r['primaryDisposition']=='hold']:fail('summary hold IDs')
    if summary['revisionCountsByLocale']!={k:locale_counts.get(k,0) for k in TARGET_LOCALES}:fail('summary locale counts')
    result={'result':'PASS','exactHead':HEAD,'exactTree':TREE,'cells':600,'sourceKeys':50,'locales':12,'acceptCurrent':401,'reviseCurrent':139,'textFreeHolds':60,'holdKeys':len(HOLD_KEYS),'placeholderParity':True,'protectedLiterals':True,'candidateFreeLinkage':True,'nativeSpeakerApproval':0,'nativeSpeakerReviewOutstanding':600,'repositoryClean':True}
    (HERE/'primary-review/primary-review-verification.json').write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))

if __name__=='__main__':main()
