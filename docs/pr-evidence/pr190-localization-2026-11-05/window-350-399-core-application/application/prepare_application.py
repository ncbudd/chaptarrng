#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent
CAND=BASE/'candidate-free/input'
PRIMARY=BASE/'primary-review'
BLIND=BASE/'blind-review'
CROSS=BASE/'cross-review'
ROOT=BASE/'root-manual-review'
OUT=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
sha_text=lambda s:sha(s.encode('utf-8'))
readjl=lambda p:[json.loads(x) for x in p.read_text().splitlines() if x.strip()]
cells=readjl(CAND/'candidate-free-cells.jsonl')
cross=readjl(CROSS/'final-cross-review.jsonl')
root=readjl(ROOT/'root-review.jsonl')
root_by={(x['sourceOrdinal'],x['locale']):x for x in root}
cand_by={(x['sourceOrdinal'],x['locale']):x for x in cells}
assert len(cells)==600 and len(cross)==600
assert len(root)==112
changes=[]
counts={'accept-current':0,'recommend-revision':0,'hold-source-copy':0}
for r in cross:
    k=(r['sourceOrdinal'],r['locale'])
    c=cand_by[k]
    assert r['sourceKey']==c['sourceKey'] and r['sourceText']==c['sourceText']
    assert r['sourceTextSha256']==c['sourceTextSha256']
    assert r['currentTarget']==c['currentTarget'] and r['currentTargetSha256']==c['currentTargetSha256']
    assert r['callerContextSha256']==c['callerContextSha256']
    d=r['crossDisposition'];counts[d]+=1
    if d=='recommend-revision':
        rr=root_by[k]
        assert rr['rootDisposition'] in ('accept-recommended','maintain-current-noop')
        assert rr['recommendedTarget']==r['recommendedTarget']
        if rr['rootDisposition']=='accept-recommended':
            assert r['recommendedTarget']!=r['currentTarget']
            assert sha_text(r['recommendedTarget'])==r['recommendedTargetSha256']
            assert r['recommendedTargetTokensVerified'] is True
            changes.append({
                'cellId':r['sourceKey']+'::'+r['locale'],'sourceOrdinal':r['sourceOrdinal'],
                'sourceKey':r['sourceKey'],'locale':r['locale'],'sourceText':r['sourceText'],
                'sourceTextSha256':r['sourceTextSha256'],'callerContextSha256':r['callerContextSha256'],
                'targetFile':c['targetFile'],'targetFileGitBlob':c['targetFileGitBlob'],
                'targetFileSha256':c['targetFileSha256'],'sourcePlaceholders':c['sourcePlaceholders'],'sourceMarkup':c['sourceMarkup'],'sourceInlineCode':c['sourceInlineCode'],'sourceNumericTokens':c['sourceNumericTokens'],'protectedLiterals':c['protectedLiterals'],'integrityChecks':c['integrityChecks'],'currentTarget':c['currentTarget'],
                'currentTargetSha256':c['currentTargetSha256'],'finalTarget':r['recommendedTarget'],
                'finalTargetSha256':r['recommendedTargetSha256'],'selectedTargetTokensVerified':r['recommendedTargetTokensVerified'],'crossDisposition':d,
                'crossRationale':r['rationale'],'rootDisposition':rr['rootDisposition'],
                'rootReviewRowSha256':sha(json.dumps(rr,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
            })
    elif d=='hold-source-copy':
        rr=root_by[k]
        assert rr['rootDisposition']=='maintain-hold' and rr['recommendedTarget'] is None
        assert r['recommendedTarget'] is None
    else:
        assert d=='accept-current' and k not in root_by
assert counts=={'accept-current':488,'recommend-revision':100,'hold-source-copy':12}
assert len(changes)==99
pins=json.loads((CAND/'catalog-pins.json').read_text())
catalogs=[]
for loc in ['en','ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']:
    p=pins[loc]
    catalogs.append({'locale':loc,'path':p['path'],'preimageSha256':p['sha256'],'gitBlob':p['gitBlob'],'keyCount':p['keyCount'],'keyOrderSha256':p['keyOrderSha256']})
files={}
for name,path in {
 'candidateFreeManifest':CAND/'candidate-free-manifest.json','candidateFreeChecksums':CAND/'SHA256SUMS.txt',
 'primaryManifest':PRIMARY/'primary-review-summary.json','primaryChecksums':PRIMARY/'SHA256SUMS.txt',
 'blindSeal':BLIND/'seal.json','blindChecksums':BLIND/'SHA256SUMS.txt',
 'crossSummary':CROSS/'cross-review-summary.json','crossChecksums':CROSS/'SHA256SUMS.txt',
 'rootSummary':ROOT/'SUMMARY.json','rootChecksums':ROOT/'SHA256SUMS.txt','rootLedger':ROOT/'root-review.jsonl'
}.items(): files[name]={'path':str(path.relative_to(BASE)),'sha256':sha(path.read_bytes())}
plan={'artifact':'ChaptarrNG PR #190 W350-W399 hash-guarded application plan','sourcePin':{'head':'dbe530c9d1a7fd2c12ce2aef76ec74c5c2188aa0','tree':'be10d71209076f753ef295038a9f3c3646a918a3'},'window':'W350-W399','localeOrder':['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant'],'candidateCellCount':600,'crossDecisionCounts':counts,'rootAcceptedChanges':99,'rootNoopRecommendations':1,'rootMaintainedSourceCopyHolds':12,'changes':sorted(changes,key=lambda x:(x['sourceOrdinal'],x['locale'])),'catalogs':catalogs,'evidenceInputs':files,'nativeSpeakerApproval':False,'workflowChanges':False,'testsBuildsScansCiRun':False}
(OUT/'apply-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
summary={k:v for k,v in plan.items() if k not in ('changes','catalogs')}
summary['changeCount']=len(changes);summary['changedLocales']=sorted({x['locale'] for x in changes})
summary['changedCatalogPaths']=sorted({x['targetFile'] for x in changes})
(OUT/'plan-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'result':'PASS','changes':len(changes),'counts':counts,'changedLocales':summary['changedLocales'],'catalogs':len(summary['changedCatalogPaths'])},ensure_ascii=False))
