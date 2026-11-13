#!/usr/bin/env python3
"""Verify the ChaptarrNG PR #190 W250-W299 cross-review packet and its pinned inputs."""
from __future__ import annotations
import collections, hashlib, json, re, subprocess, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
TASK=HERE.parent
CANDIDATE=TASK/'chaptarrng-pr190-w250-299-core-20261104/candidate-free/input'
PRIMARY=TASK/'chaptarrng-pr190-w250-299-core-20261104/primary-review'
BLIND=TASK/'chaptarrng-pr190-w250-299-independent-blind-20261104'
REPO=Path('/mnt/disks/scratch/task-worktrees/localization-20261104/chaptarrng-pr190-next-window')
HEAD='2a9995a2bf63f06814bd8780736305f16bd6b33a'
TREE='f6ae6530b73bf581c1fbc5a8c13eacd7342e9172'
BRANCH='codex/chaptarrng-localization-complete-20261031'
LOCALES={'ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant'}
PH=re.compile(r'\{[^{}]+\}')
INLINE=re.compile(r'`([^`]+)`')
MARKUP=re.compile(r'<[^>]+>')
NUMBER=re.compile(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])')

def need(ok,msg):
    if not ok: raise SystemExit('FAIL: '+msg)
def sha(data:bytes)->str: return hashlib.sha256(data).hexdigest()
def sha_text(s:str)->str: return sha(s.encode('utf-8'))
def row_sha(r)->str: return sha(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8'))
def readj(p): return json.loads(p.read_text(encoding='utf-8'))
def readjl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def sig(rx,s): return collections.Counter(rx.findall(s))
def nums(s): return sig(NUMBER,PH.sub('',s))
def verify_sums(path):
    entries={}
    for line in path.read_text(encoding='utf-8').splitlines():
        digest,name=line.split('  ',1)
        target=(path.parent/name).resolve()
        need(target.is_relative_to(path.parent.resolve()) and target.is_file(),'unsafe/missing checksum path '+name)
        need(sha(target.read_bytes())==digest,'checksum mismatch '+name)
        entries[name]=digest
    actual={p.name for p in path.parent.iterdir() if p.is_file() and p.name!=path.name}
    need(set(entries)==actual,'checksum coverage mismatch '+str(path))
    return entries

def main():
    # Output and sealed input packet checksums.
    verify_sums(HERE/'SHA256SUMS.txt')
    verify_sums(CANDIDATE/'SHA256SUMS.txt')
    verify_sums(PRIMARY/'primary-review-SHA256SUMS.txt')
    verify_sums(BLIND/'SHA256SUMS.txt')
    # Re-run only the supplied packet integrity verifiers; these are not product tests/builds.
    for label,argv in [
        ('candidate-free',[sys.executable,str(CANDIDATE/'verify_candidate_free.py'),'--source-worktree',str(REPO)]),
        ('primary',[sys.executable,str(PRIMARY/'verify_primary_review.py'),'--source-worktree',str(REPO)]),
        ('blind',[sys.executable,str(BLIND/'verify_blind_review.py'),'--candidate-free-input',str(CANDIDATE)])]:
        p=subprocess.run(argv,capture_output=True,text=True)
        need(p.returncode==0,label+' input verifier failed: '+p.stdout+p.stderr)
    need(subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip()==HEAD,'source worktree HEAD mismatch')
    need(subprocess.check_output(['git','-C',str(REPO),'show','-s','--format=%T',HEAD],text=True).strip()==TREE,'source worktree tree mismatch')
    need(not subprocess.check_output(['git','-C',str(REPO),'status','--porcelain=v1'],text=True).strip(),'source worktree dirty')

    c=readjl(CANDIDATE/'candidate-free-cells.jsonl')
    p=readjl(PRIMARY/'primary-review-cells.jsonl')
    b=readjl(BLIND/'blind-cell-review.jsonl')
    pp=readjl(PRIMARY/'primary-review-proposals.jsonl')
    findings=readj(BLIND/'findings.json')
    rows=readjl(HERE/'cross-review-cells.jsonl')
    changes=readjl(HERE/'selected-changes.jsonl')
    summary=readj(HERE/'cross-review-summary.json')
    manifest=readj(HERE/'manifest.json')
    att=readj(HERE/'live-pr-attestation.json')
    drift=readj(HERE/'base-drift-comparison.json')
    decisions=readj(HERE/'decision-reconciliation.json')
    selections=readj(HERE/'review-selections.json')
    caller=readj(HERE/'caller-evidence.json')

    need(len(c)==len(p)==len(b)==len(rows)==600,'600-row coverage')
    cm={(r['sourceOrdinal'],r['locale']):r for r in c}
    pm={(r['sourceOrdinal'],r['locale']):r for r in p}
    bm={(r['sourceOrdinal'],r['locale']):r for r in b}
    rm={(r['sourceOrdinal'],r['locale']):r for r in rows}
    pmap={r['cellId']:r for r in pp}
    need(len(cm)==len(pm)==len(bm)==len(rm)==600,'duplicate row identity')
    need(sorted({o for o,l in cm})==list(range(250,300)),'ordinal gap/overlap')
    need({l for o,l in cm}==LOCALES,'locale coverage')
    need(len({cm[(o,l)]['sourceKey'] for o in range(250,300) for l in LOCALES})==50,'source key count')
    need(len(pmap)==33 and len(changes)==42,'proposal count')
    need(summary['dispositions']=={'accept-current':558,'propose-change':42},'cross disposition counts')
    need(summary['primaryBlindOverlap']==9 and summary['blindHoldCells']==30,'primary/blind overlap counts')
    need(len(selections['customTargets'])==13,'custom target count')
    need(summary['nativeSpeakerReviewOutstanding']==600 and summary['nativeSpeakerApproval']==0,'speaker review status')
    need(summary['head']==HEAD and summary['tree']==TREE and summary['repositoryOrPRChanged'] is False,'summary pin/scope')
    need(summary['testsBuildsCIWorkflowsRun'] is False and summary['recommendationsOnly'] is True,'scope declarations')
    need(att['pr']['state']=='OPEN' and att['pr']['draft'] is True and att['fullPullRequestBodyRetrieved'] is False,'filtered PR attestation')
    need(att['pr']['headSha']==att['branchApi']['sha']==att['pullRef']['sha']==HEAD,'live head refs')
    need(att['pr']['headRefName']==att['branchApi']['ref']==BRANCH and att['pullRef']['ref']=='refs/pull/190/head','live ref names')
    need(att['sourceWorktree']['head']==HEAD and att['sourceWorktree']['tree']==TREE and att['sourceWorktree']['clean'] is True,'attested worktree')
    need(drift['apiBase']==att['pr']['baseSha'] and drift['currentMain']==att['currentMain'] and drift['aheadBy']==26,'base drift refs/count')
    need(drift['containsCoreLocalizationSourceOrCatalogChanges'] is False,'base drift localization assessment')
    need(manifest['head']==HEAD and manifest['tree']==TREE and manifest['scopeControls']['PRBodyRead'] is False,'manifest pin/scope')
    need(manifest['artifacts']=={x.name:sha(x.read_bytes()) for x in sorted(HERE.iterdir()) if x.is_file() and x.name not in {'manifest.json','SHA256SUMS.txt'}},'manifest artifact hashes')

    by_finding=collections.defaultdict(list)
    for f in findings:
        for cell in f['affectedCells']:
            _,key,locale=cell.split(':',2)
            by_finding[key+'::'+locale].append(f['findingId'])
    change_map={r['cellId']:r for r in changes}
    need(len(change_map)==42,'change identity count')
    for ident,crow in cm.items():
        pr=pm[ident]; br=bm[ident]; rr=rm[ident]
        cid=crow['sourceKey']+'::'+crow['locale']
        need(rr['cellId']==cid and rr['sourceOrdinal']==crow['sourceOrdinal'],'cell identity')
        need(rr['exactHead']==HEAD and rr['exactTree']==TREE,'row exact pin')
        need(rr['candidateFreeRowSha256']==row_sha(crow),'cross candidate-free linkage')
        need(rr['primaryReviewRowSha256']==row_sha(pr),'cross primary linkage')
        need(rr['blindReviewRowSha256']==row_sha(br),'cross blind linkage')
        need(pr['candidateFreeRowSha256']==row_sha(crow),'primary candidate-free linkage')
        need(br['sourceKey']==crow['sourceKey'] and br['locale']==crow['locale'],'blind source identity')
        need(br['sourceTextSha256']==crow['sourceTextSha256'] and br['currentTargetSha256']==crow['currentTargetSha256'],'blind source/current hashes')
        need(br['callerBacked'] is True and br['callerReferenceCount']==crow['callerReferenceCount']>0,'blind caller evidence')
        need(rr['callerContextSha256']==crow['callerContextSha256'] and rr['callerReferenceCount']==crow['callerReferenceCount'],'cross caller linkage')
        need(rr['sourceTextSha256']==sha_text(rr['sourceText'])==crow['sourceTextSha256'],'source text hash')
        need(rr['currentTargetSha256']==sha_text(rr['currentTarget'])==crow['currentTargetSha256'],'current target hash')
        target=rr['recommendedTarget']
        need(rr['recommendedTargetSha256']==sha_text(target),'recommended target hash')
        need(sig(PH,target)==sig(PH,crow['sourceText']),'placeholder parity '+cid)
        need(sig(INLINE,target)==sig(INLINE,crow['sourceText']),'inline code parity '+cid)
        need(sig(MARKUP,target)==sig(MARKUP,crow['sourceText']),'markup parity '+cid)
        need(nums(target)==nums(crow['sourceText']),'numeric token parity '+cid)
        missing=[x for x in crow.get('protectedLiterals',[]) if x not in target]
        exceptions=rr['protectedLiteralExceptions']
        if missing:
            expected=(crow['sourceKey']=='BackupIntervalHelpText' and crow['locale'] in {'ar','es','fr','pt-BR','zh-Hans','zh-Hant'} and missing==['DB'] and target==crow['currentTarget'])
            need(expected and len(exceptions)==1 and exceptions[0]['literal']=='DB','unapproved protected-literal mismatch '+cid)
        else:
            need(not exceptions,'spurious protected-literal exception '+cid)
        need(rr['findingIds']==sorted(by_finding.get(cid,[])),'finding linkage '+cid)
        if rr['crossDisposition']=='propose-change':
            need(target!=crow['currentTarget'] and cid in change_map,'proposed change missing')
            ch=change_map[cid]
            for field in ['sourceTextSha256','currentTargetSha256','recommendedTarget','recommendedTargetSha256','selectedFrom','crossRationale','callerContextSha256','candidateFreeRowSha256','primaryReviewRowSha256','blindReviewRowSha256','exactHead','exactTree']:
                need(ch.get(field)==rr.get(field),'change linkage '+cid+' '+field)
        else:
            need(rr['crossDisposition']=='accept-current' and target==crow['currentTarget'] and cid not in change_map,'accepted current target mismatch '+cid)

    need(set(change_map)=={r['cellId'] for r in rows if r['crossDisposition']=='propose-change'},'selected change coverage')
    book=[r for r in rows if r['sourceKey']=='Book']
    need(len(book)==12 and all(r['crossDisposition']=='accept-current' and 'F011' in r['findingIds'] for r in book),'F011 rejected-cell coverage')
    need(any(x.get('path')=='frontend/src/Author/History/AuthorHistoryTableContent.js' and x.get('line')==22 for x in caller['Book']['directRuntimeTranslationCallsites']),'Book caller evidence')
    need(decisions['primaryBlindProposalHoldOverlap']['count']==9 and len(decisions['rejectedF011FalsePositiveCells'])==12,'finding reconciliation coverage')
    need(len(decisions['protectedLiteralScannerExceptions']['cells'])==6,'protected-literal exception count')
    need(manifest['inputHashes']==summary['inputHashes'],'summary/manifest input hashes')
    print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'cells':600,'acceptCurrent':558,'selectedChanges':42,'primaryProposals':33,'blindHolds':30,'overlap':9,'falsePositiveF011Cells':12,'protectedLiteralExpansions':6,'sealedInputs':'PASS'},sort_keys=True))

if __name__=='__main__': main()
