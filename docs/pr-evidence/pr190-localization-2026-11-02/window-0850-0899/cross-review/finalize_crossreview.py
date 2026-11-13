from __future__ import annotations
import json, hashlib, pathlib, subprocess, re, collections, os
from datetime import datetime, timezone
OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0850-0899-crossreview-20261102')
PRIMARY=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0850-0899-primary-20261102')
AUDIT=PRIMARY/'language-audit-addendum'
WORK=pathlib.Path('/home/keith/Documents/code/task-worktrees/localization-20261102-chaptarrng')
HEAD='175cff3a50569b67def345bb82332b30e9bb378c'; TREE='e682581e3c577b62215658c374b15a9d3f8f8bd0'
REPOS=[('SeerrNG',418),('ChaptarrNG',190),('QuestarrNG',155),('ROMarrNG',70),('slskR',204),('slskdN',409),('TorrentNG',243)]
LOCALES={'ar':'ar.json','de':'de.json','es':'es.json','fr':'fr.json','hi':'hi.json','id':'id.json','ja':'ja.json','ko':'ko.json','pt-BR':'pt_BR.json','vi':'vi.json','zh-Hans':'zh_CN.json','zh-Hant':'zh_TW.json'}
SRC='src/NzbDrone.Core/Localization/Core/en.json'
def sha(x): return hashlib.sha256(x if isinstance(x,bytes) else x.encode()).hexdigest()
def git(*args): return subprocess.check_output(['git','-C',str(WORK),*args])
def jbytes(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def placeholders(s): return sorted(set(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s)))
def markup(s):
    if re.fullmatch(r'<[^<>/]+>',s): return []
    return re.findall(r'</?[A-Za-z][^>]*>',s)
def readjl(path): return [json.loads(x) for x in pathlib.Path(path).read_text().splitlines()]
def check_manifest(path):
    p=subprocess.run(['sha256sum','-c','SHA256SUMS'],cwd=path,text=True,capture_output=True)
    assert p.returncode==0,p.stdout+p.stderr
    return len(p.stdout.splitlines())
# Freshly query all seven open localization PRs, including their commit trees.
prs=[]
for repo,n in REPOS:
    pr=json.loads(subprocess.check_output(['gh','pr','view',str(n),'--repo',f'snapetech-org/{repo}','--json','number,state,isDraft,headRefName,headRefOid,baseRefName,baseRefOid,url'],text=True))
    tree=json.loads(subprocess.check_output(['gh','api',f"repos/snapetech-org/{repo}/git/commits/{pr['headRefOid']}"],text=True))['tree']['sha']
    row={'repository':f'snapetech-org/{repo}',**pr,'headTree':tree}
    if n==190:
        remote=subprocess.check_output(['git','ls-remote','https://github.com/snapetech-org/ChaptarrNG.git',f"refs/heads/{pr['headRefName']}"],text=True).split()[0]
        row['remoteBranchOid']=remote
    prs.append(row)
cha=next(x for x in prs if x['number']==190)
assert cha['state']=='OPEN' and cha['isDraft'] is True and cha['headRefOid']==HEAD and cha['headTree']==TREE and cha['remoteBranchOid']==HEAD
assert git('rev-parse','HEAD').decode().strip()==HEAD and git('rev-parse','HEAD^{tree}').decode().strip()==TREE
assert git('status','--porcelain').decode().strip()==''
assert git('branch','--show-current').decode().strip()=='codex/chaptarrng-localization-complete-20261031'
# Re-check all primary and independent language-audit packet checksums.
primary_manifest_sha=sha((PRIMARY/'SHA256SUMS').read_bytes())
assert primary_manifest_sha=='c74bc2a0eda46571510b64e7560e925337447ad2da17d6f51946f631ed68c848'
primary_sum_rows=check_manifest(PRIMARY); audit_sum_rows=check_manifest(AUDIT)
input_sum=subprocess.run(['sha256sum','-c',str(PRIMARY/'INPUT-SHA256SUMS')],cwd=WORK,text=True,capture_output=True)
assert input_sum.returncode==0,input_sum.stdout+input_sum.stderr
# Load pinned catalogs directly from the exact tree and verify every ledger row.
source_raw=git('show',f'{HEAD}:{SRC}'); source=json.loads(source_raw)
source_blob=git('rev-parse',f'{HEAD}:{SRC}').decode().strip()
ids=json.loads((PRIMARY/'current-missing-ids.json').read_text())
assert len(ids)==1210 and len(set(ids))==1210
source_slice=readjl(PRIMARY/'source-slice.jsonl')
assert len(source_slice)==50
for i,row in enumerate(source_slice,850):
    assert row['sourceOrdinal']==i and row['sourceId']==ids[i] and source[row['sourceId']]==row['source']
    assert row['sourceTextSha256']==sha(row['source']) and row['sourceKeySha256']==sha(row['sourceId'])
    assert row['sourceCatalogBlob']==source_blob and row['sourceCatalogSha256']==sha(source_raw)
registry=json.loads(git('show',f'{HEAD}:docs/localization/server-message-sources.json'))
reg={x['id']:x for x in registry['records']}
for row in source_slice: assert row['source']==reg[row['sourceId']]['source']
catalogs={}; pins={}
for loc,file in LOCALES.items():
    path=f'src/NzbDrone.Core/Localization/Core/{file}'
    raw=git('show',f'{HEAD}:{path}'); obj=json.loads(raw)
    assert set(obj)==set(source),(loc,'keyset parity')
    catalogs[loc]=obj; pins[loc]={'path':path,'blob':git('rev-parse',f'{HEAD}:{path}').decode().strip(),'sha256':sha(raw)}
ledger=readjl(OUT/'cross-review-ledger.jsonl')
primary=readjl(PRIMARY/'review-cells.jsonl')
current=readjl(PRIMARY/'input-cells.jsonl')
assert len(ledger)==len(primary)==len(current)==600
pmap={(x['sourceOrdinal'],x['locale']):x for x in primary}; cmap={(x['sourceOrdinal'],x['locale']):x for x in current}
caller_rows=readjl(PRIMARY/'caller-context.jsonl'); callermap={x['sourceId']:x for x in caller_rows}
assert len(pmap)==len(cmap)==600 and len(callermap)==50
counts=collections.Counter(); failures=[]
for row in ledger:
    key=(row['sourceOrdinal'],row['locale']); p=pmap[key]; c=cmap[key]; loc=row['locale']; sid=row['sourceId']
    src=source[sid]; target=catalogs[loc][sid]
    checks={
      'head_tree':row['exactHead']==HEAD and row['exactTree']==TREE and p['exactHead']==HEAD and p['exactTree']==TREE,
      'source_order':850<=row['sourceOrdinal']<900 and ids[row['sourceOrdinal']]==sid and src==row['source']==p['source']==c['source'],
      'source_hash':sha(src)==row['sourceTextSha256']==p['sourceTextSha256']==c['sourceTextSha256'],
      'source_key_hash':sha(sid)==row['sourceKeySha256']==p['sourceKeySha256'],
      'current_text_hash':target==row['currentTarget']==p['currentTarget']==c['currentTarget'],
      'current_target_hash':sha(target)==row['currentTargetSha256']==p['currentTargetSha256']==c['currentTargetSha256'],
      'catalog_pin':row['targetFile']==pins[loc]['path'] and row['targetFileBlob']==pins[loc]['blob'] and row['targetFileSha256']==pins[loc]['sha256'],
      'source_pin':row['sourceFile']==SRC and row['sourceFileBlob']==source_blob and row['sourceFileSha256']==sha(source_raw),
      'caller_pin':row['callerContextSha256']==p['callerContextSha256']==c['callerContextSha256']==callermap[sid]['callerContextSha256'] and row['callerRefs']==p['callerRefs']==callermap[sid]['callerRefs'],
      'placeholders_source_current':placeholders(src)==row['sourcePlaceholders']==placeholders(target)==row['currentTargetPlaceholders'],
      'markup_source_current':markup(src)==row['sourceMarkup']==markup(target)==row['currentTargetMarkup'],
      'protected_current':all(x in target for x in row['protectedLiterals']),
    }
    disp=row['crossReviewDisposition']; final=row['crossReviewFinalTarget']
    if disp=='accept-current': checks['final_is_current']=final==target and row['crossReviewFinalTargetSha256']==sha(target)
    elif disp in ('accept-primary-correction','accept-primary-refinement'):
        checks['primary_disposition']=(p['disposition']=='propose-correction' if disp=='accept-primary-correction' else p['disposition']=='propose-refinement')
        checks['final_is_primary']=final==p['finalTarget'] and row['crossReviewFinalTargetSha256']==p['finalTargetSha256'] and sha(final)==p['finalTargetSha256']
    elif disp=='propose-additional-correction':
        checks['additional_differs']=final!=target
        checks['additional_hash']=final is not None and row['crossReviewFinalTargetSha256']==sha(final)
        checks['additional_disposition']=p['disposition']=='accept-current'
    elif disp=='retain-hold':
        checks['hold_exact']=final is None and row['crossReviewFinalTargetSha256'] is None and p['disposition']=='hold'
    else: checks['known_disposition']=False
    if final is not None:
        checks['final_placeholders']=placeholders(final)==row['crossReviewFinalPlaceholders']==placeholders(src)
        checks['final_markup']=markup(final)==row['crossReviewFinalMarkup']==markup(src)
        checks['protected_final']=all(x in final for x in row['protectedLiterals'])
    else:
        checks['hold_source_caller']=row['callerSourceMessageMismatch'] is True and row['sourceOrdinal']==884
    bad=[k for k,v in checks.items() if not v]
    if bad: failures.append({'ordinal':row['sourceOrdinal'],'id':sid,'locale':loc,'failed':bad})
    counts[disp]+=1
assert not failures,failures[:10]
assert counts=={'accept-current':495,'accept-primary-correction':69,'accept-primary-refinement':10,'propose-additional-correction':14,'retain-hold':12},counts
assert all(r['sourceOrdinal']==884 for r in ledger if r['crossReviewDisposition']=='retain-hold')
assert len({(x['sourceOrdinal'],x['locale']) for x in ledger})==600
# Ensure additional-correction index exactly matches its 14 full ledger proposals.
adds=readjl(OUT/'additional-corrections.jsonl')
addkeys={(x['sourceOrdinal'],x['locale']):x for x in adds}
assert len(addkeys)==14
for r in ledger:
    if r['crossReviewDisposition']=='propose-additional-correction':
        a=addkeys[(r['sourceOrdinal'],r['locale'])]
        assert a['recommendedTarget']==r['crossReviewFinalTarget'] and a['recommendedTargetSha256']==r['crossReviewFinalTargetSha256']
# Confirm independent language audit exactness for all 79 proposal rows and W884 holds.
audit_manifest=json.loads((AUDIT/'manifest.json').read_text()); audits=readjl(AUDIT/'language-audit.jsonl')
assert audit_manifest['head']==HEAD and audit_manifest['tree']==TREE and audit_manifest['rows']==91 and len(audits)==91
assert audit_manifest['primaryReviewCellsSha256']==sha((PRIMARY/'review-cells.jsonl').read_bytes())
assert audit_manifest['candidateRows']==79 and audit_manifest['holdRows']==12 and audit_manifest['additionalProposals']==0
assert len((OUT/'structural-caller-reattestation.jsonl').read_text().splitlines())==600
# Save final independent snapshot and reproducibility facts.
now=datetime.now(timezone.utc).isoformat()
(OUT/'live-seven-pr-heads.json').write_text(json.dumps({'capturedAtUtc':now,'pullRequests':prs},ensure_ascii=False,indent=2,sort_keys=True)+'\n')
summary=json.loads((OUT/'cross-review-summary.json').read_text())
summary['finalReattestationUtc']=now
summary['finalReattestationPath']='final-reattestation.json'
summary['finalReadbackChecks']=600
summary['primaryChecksumRowsVerified']=primary_sum_rows
summary['languageAuditChecksumRowsVerified']=audit_sum_rows
summary['primaryInputChecksumRowsVerified']=len(input_sum.stdout.splitlines())
(OUT/'cross-review-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
final={'capturedAtUtc':now,'repository':'snapetech-org/ChaptarrNG','pullRequest':190,'state':cha['state'],'isDraft':cha['isDraft'],'branch':cha['headRefName'],'exactHead':HEAD,'exactTree':TREE,'remoteBranchOid':cha['remoteBranchOid'],'worktree':str(WORK),'worktreeBranch':git('branch','--show-current').decode().strip(),'worktreeHead':git('rev-parse','HEAD').decode().strip(),'worktreeTree':git('rev-parse','HEAD^{tree}').decode().strip(),'worktreeStatus':'clean','allSevenPullRequestCount':len(prs),'allSevenSnapshots':{str(x['number']):{'repository':x['repository'],'state':x['state'],'isDraft':x['isDraft'],'head':x['headRefOid'],'tree':x['headTree']} for x in prs},'sourcePositions':[850,899],'cellsReadBack':600,'catalogKeysetParityLocales':list(LOCALES),'dispositions':dict(counts),'primaryPacketSha256Manifest':primary_manifest_sha,'primaryChecksumRowsVerified':primary_sum_rows,'languageAuditChecksumRowsVerified':audit_sum_rows,'primaryInputChecksumRowsVerified':len(input_sum.stdout.splitlines()),'w884HeldAcross12Locales':True,'w884Reason':'English source omits backslash restriction enforced by pinned qBittorrent caller.','nativeSpeakerApproval':False,'browserReview':False,'repoModified':False,'testsBuildCiRun':False,'readbackFailures':0,'confidence':'moderate'}
(OUT/'final-reattestation.json').write_text(json.dumps(final,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
print(json.dumps({'capturedAtUtc':now,'head':HEAD,'tree':TREE,'counts':dict(counts),'readbackFailures':len(failures),'primaryInputChecksumRowsVerified':len(input_sum.stdout.splitlines()),'primaryChecksumRowsVerified':primary_sum_rows,'languageAuditChecksumRowsVerified':audit_sum_rows},ensure_ascii=False,indent=2))
