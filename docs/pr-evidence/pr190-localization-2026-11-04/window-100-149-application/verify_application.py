#!/usr/bin/env python3
"""Portable exact-hash verifier for ChaptarrNG PR #190 W100-W149 application evidence."""
from __future__ import annotations
import argparse, collections, hashlib, json, pathlib, re, subprocess, sys, unicodedata
EVIDENCE=pathlib.Path(__file__).resolve().parent
CROSS=EVIDENCE/'cross-audit'
BASE='9fd23606fbb4c8928505772413e5c23e85352adc'
BASE_TREE='cba466021a9a0c9699ef171ddc6a510a69209083'
APP='a5b6d99061f1193af5d8de9b3d04d9df7296b043'
APP_TREE='cab243f181d5d5e9490130e5d6229df7219848af'
BULLET='- Apply 42 cross-reviewed translation corrections and refinements across all 12 locale catalogs (W100–W149).'
HOLD_TEXT_FIELDS={'sourceKey','cellId','sourceText','currentTarget','selectedTarget','primaryTarget','primaryProposalTarget','recommendedTarget','finalReviewedTarget','finalTarget','targetText','beforeTarget','postTarget'}
OPAQUE={'AllowedLanguagesHelpText':['eng','swe'],'ApplicationUrlHelpText':['http(s)://'],'AptUpdater':['apt'],'AudibleCatalog':['Audible'],'AudibleMarketplace':['Audible']}
BRANDS={'Chaptarr','ChaptarrNG','AudioBookShelf'}
PROTECTED=re.compile(r'\b(?:[A-Z][A-Z0-9]{1,}|[A-Z]+[0-9][A-Z0-9]*)\b')
PH=re.compile(r'\{[^{}]+\}')
CODE=re.compile(r'`([^`]+)`')
TAG=re.compile(r'</?[A-Za-z][^>]*>')
def sha(b): return hashlib.sha256(b).hexdigest()
def shat(s): return sha(s.encode('utf-8'))
def require(ok,msg):
    if not ok: raise SystemExit('FAIL: '+msg)
def git(repo,*args): return subprocess.check_output(['git','-C',str(repo),*args])
def jsonl(path): return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]
def ph(s): return collections.Counter(PH.findall(s))
def code(s): return collections.Counter(CODE.findall(s))
def tags(s): return collections.Counter(TAG.findall(s))
def nums(s):
    return collections.Counter(''.join(str(unicodedata.digit(c)) if c.isdigit() else c for c in x) for x in re.findall(r'\d+',s))
def required_literals(source):
    brands=BRANDS & set(re.findall(r'\b[A-Za-z][A-Za-z0-9]*\b',source))
    return set(PROTECTED.findall(source)) | brands

def verify_sums(root,name,exclude_self=False):
    checksum=root/name
    require(checksum.is_file(),'missing checksum file '+str(checksum))
    sums={}
    for line in checksum.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        digest,rel=line.split('  ',1)
        rp=pathlib.Path(rel)
        require(not rp.is_absolute() and '..' not in rp.parts,'unsafe checksum path '+rel)
        target=(root/rp).resolve()
        require(target.is_relative_to(root.resolve()),'checksum path escapes root '+rel)
        require(rel not in sums,'duplicate checksum entry '+rel)
        require(target.is_file() and sha(target.read_bytes())==digest,'checksum mismatch '+rel)
        sums[rel]=digest
    if exclude_self:
        actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p!=checksum}
        require(actual==set(sums),'checksum inventory mismatch under '+str(root))
    return sums

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',type=pathlib.Path,default=EVIDENCE.parents[3])
    args=ap.parse_args(); repo=args.repo.resolve()
    require(repo.is_dir(),'repository path missing')
    evidence_sums=verify_sums(EVIDENCE,'EVIDENCE-SHA256SUMS.txt',exclude_self=True)
    local_input_sums=verify_sums(EVIDENCE,'CALLER-BACKED-INPUT-SHA256.txt')
    require(set(local_input_sums)=={'caller-backed-input.jsonl'},'caller-backed input checksum inventory')
    cross_sums=verify_sums(CROSS,'SHA256SUMS.txt')
    manifest=json.loads((CROSS/'manifest.json').read_text(encoding='utf-8'))
    cross_entries={x['path']:x for x in manifest['files']}
    require(manifest.get('head')==BASE and manifest.get('tree')==BASE_TREE and manifest.get('cellCount')==600,'cross manifest pin/count mismatch')
    require(set(cross_sums)==set(cross_entries)|{'manifest.json'},'cross manifest/checksum inventory mismatch')
    for name,item in cross_entries.items():
        p=CROSS/name
        require(p.is_file() and p.stat().st_size==item['bytes'] and sha(p.read_bytes())==item['sha256'],'cross manifest file mismatch '+name)
    summary=json.loads((CROSS/'summary.json').read_text(encoding='utf-8'))
    require(summary.get('head')==BASE and summary.get('tree')==BASE_TREE,'cross summary pin mismatch')
    require(summary.get('crossDispositions')=={'accept-current':390,'select-primary-proposal':42,'hold':168},'cross summary disposition mismatch')
    require(summary.get('unresolvedProposalDisagreements')==0 and summary.get('sourceRewriteRecommendations')==2,'cross summary proposal/source-review mismatch')
    cv=json.loads((EVIDENCE/'cross-verification-before-application.json').read_text(encoding='utf-8'))
    require(cv.get('result')=='PASS' and cv.get('head')==BASE and cv.get('tree')==BASE_TREE,'cross verifier result/pin mismatch')
    require(cv.get('candidateFreeVerifier')=='PASS' and cv.get('primaryVerifier')=='PASS','cross input verifier result mismatch')
    require(cv.get('cellCount')==600 and cv.get('selectedPrimaryProposals')==42 and cv.get('acceptCurrent')==390 and cv.get('textFreeCallerlessHolds')==168,'cross verifier counts mismatch')
    ledger=jsonl(CROSS/'cross-ledger.jsonl'); selected=jsonl(CROSS/'selected-changes.jsonl'); holds=jsonl(CROSS/'holds-hash-only.jsonl')
    require(len(ledger)==600 and len(selected)==42 and len(holds)==168,'cross packet cardinality mismatch')
    im={(r['sourceOrdinal'],r['locale']):r for r in ledger}; sm={(r['sourceOrdinal'],r['locale']):r for r in selected}; hm={(r['sourceOrdinal'],r['locale']):r for r in holds}
    require(len(im)==600 and len(sm)==42 and len(hm)==168,'cross packet duplicate identity')
    dispositions=collections.Counter(r['crossDisposition'] for r in ledger)
    require(dispositions==collections.Counter({'accept-current':390,'select-primary-proposal':42,'hold':168}),'cross cell disposition counts')
    selected_ids={ident for ident,row in im.items() if row['crossDisposition']=='select-primary-proposal'}
    hold_ids={ident for ident,row in im.items() if row['crossDisposition']=='hold'}
    current_ids={ident for ident,row in im.items() if row['crossDisposition']=='accept-current'}
    require(set(sm)==selected_ids and set(hm)==hold_ids,'selected/hold extract differs from ledger')
    for ident,row in im.items():
        if row['crossDisposition']=='hold':
            require(row.get('callerReferenceCount')==0 and not (HOLD_TEXT_FIELDS & set(row)),'cross held row leaks text '+repr(ident))
            h=hm[ident]
            require(h.get('callerReferenceCount')==0 and not (HOLD_TEXT_FIELDS & set(h)),'hash-only hold record leaks text '+repr(ident))
            require(h['sourceTextSha256']==row['sourceTextSha256'] and h['currentTargetSha256']==row['currentTargetSha256'],'hold hash mismatch '+repr(ident))
        else:
            require(row.get('callerReferenceCount',0)>0,'caller-backed cell lacks caller '+repr(ident))
    readback=json.loads((EVIDENCE/'application-readback.json').read_text(encoding='utf-8'))
    require(readback.get('baseHead')==BASE and readback.get('baseTree')==BASE_TREE and readback.get('applicationHead')==APP and readback.get('applicationTree')==APP_TREE,'readback commit pin mismatch')
    require(readback.get('counts')=={'cells':600,'selected':42,'acceptedCurrent':390,'hashOnlyCallerlessHolds':168,'callerlessKeys':14,'catalogsInspected':12,'catalogValuesChanged':42,'catalogKeysPerLocale':4165,'tokenParityChecks':{k:432 for k in ('placeholderParity','inlineCodeParity','markupParity','numericParity','protectedLiterals')}},'readback count block mismatch')
    rows=readback['rows']; rm={(r['sourceOrdinal'],r['locale']):r for r in rows}
    require(len(rows)==600 and len(rm)==600 and set(rm)==set(im),'readback row coverage/uniqueness mismatch')
    # Candidate-free input subset contains exactly 432 caller-backed source rows, preserving original row bytes.
    cf_bytes=(EVIDENCE/'caller-backed-input.jsonl').read_bytes().splitlines()
    cf_rows=[json.loads(x) for x in cf_bytes]
    cfm={(r['sourceOrdinal'],r['locale']):r for r in cf_rows}
    require(len(cf_rows)==432 and len(cfm)==432 and set(cfm)==current_ids|selected_ids,'caller-backed subset coverage mismatch')
    for ident,c in cfm.items():
        require(c['callerReferenceCount']>0,'callerless row leaked into caller-backed subset '+repr(ident))
        row=im[ident]
        require(sha(next(raw for raw,parsed in zip(cf_bytes,cf_rows) if parsed['sourceOrdinal']==ident[0] and parsed['locale']==ident[1]))==row['candidateFreeRowSha256'],'candidate-free row provenance mismatch '+repr(ident))
        require(c['sourceTextSha256']==row['sourceTextSha256'] and c['currentTargetSha256']==row['currentTargetSha256'],'candidate-free row source/current mismatch '+repr(ident))
    cf_map={(r['sourceOrdinal'],r['locale']):r for r in cf_rows}
    # Validate exact base/application Git objects, all 12 catalog shapes, and only the 42 intended changes.
    require(git(repo,'rev-parse',BASE).decode().strip()==BASE and git(repo,'show','-s','--format=%T',BASE).decode().strip()==BASE_TREE,'pinned base commit/tree missing')
    require(git(repo,'rev-parse',APP).decode().strip()==APP and git(repo,'show','-s','--format=%T',APP).decode().strip()==APP_TREE,'product commit/tree missing')
    require(git(repo,'rev-parse',APP+'^').decode().strip()==BASE,'product commit parent mismatch')
    catalog_rows={r['path']:r for r in readback['catalogFiles']}
    require(len(catalog_rows)==12 and len(catalog_rows)==len(readback['catalogFiles']),'catalog file readback inventory')
    target_paths=sorted(catalog_rows)
    source_path='src/NzbDrone.Core/Localization/Core/en.json'
    source_raw=git(repo,'show',f'{BASE}:{source_path}'); source=json.loads(source_raw)
    file_data={}; changed=[]
    for rel in target_paths:
        pre=git(repo,'show',f'{BASE}:{rel}'); post=git(repo,'show',f'{APP}:{rel}')
        before=json.loads(pre); after=json.loads(post); rec=catalog_rows[rel]
        require(len(before)==len(after)==4165 and set(before)==set(after),'catalog key set/count mismatch '+rel)
        require(list(before)==list(after),'catalog order changed '+rel)
        require(sha(pre)==rec['preimageSha256'] and sha(post)==rec['postimageSha256'],'catalog file hash mismatch '+rel)
        require(git(repo,'rev-parse',f'{BASE}:{rel}').decode().strip()==rec['preimageGitBlob'],'catalog preimage blob mismatch '+rel)
        require(git(repo,'rev-parse',f'{APP}:{rel}').decode().strip()==rec['postimageGitBlob'],'catalog postimage blob mismatch '+rel)
        require(rec['keyCount']==4165 and rec['orderedKeysSha256']==shat('\n'.join(before)),'catalog shape hash mismatch '+rel)
        file_data[rel]=(before,after)
        changed.extend((rel,k) for k in before if before[k]!=after[k])
    expected_changed=set()
    locale_file={'pt-BR':'pt_BR.json','zh-Hans':'zh_CN.json','zh-Hant':'zh_TW.json'}
    def file_for(locale): return 'src/NzbDrone.Core/Localization/Core/'+locale_file.get(locale,locale+'.json')
    # Full caller-backed semantic and exact-hash readback.
    for ident in current_ids|selected_ids:
        row=im[ident]; c=cf_map[ident]; rr=rm[ident]; key=row['sourceKey']; loc=row['locale']; rel=row['targetFile']
        before,after=file_data[rel]
        require(row['sourceFile']==source_path and row['sourceFileSha256']==sha(source_raw) and row['sourceFileGitBlob']==git(repo,'rev-parse',f'{BASE}:{source_path}').decode().strip(),'source file pin mismatch '+repr(ident))
        require(c['sourceKey']==key and c['targetFile']==rel and c['sourceText']==source[key]==row['sourceText'],'source/candidate text mismatch '+repr(ident))
        require(shat(source[key])==row['sourceTextSha256']==c['sourceTextSha256']==rr['sourceTextSha256'],'source text hash mismatch '+repr(ident))
        require(shat(before[key])==row['currentTargetSha256']==c['currentTargetSha256']==rr['expectedCurrentTargetSha256']==rr['observedPreTargetSha256'],'target preimage hash mismatch '+repr(ident))
        require(before[key]==row['currentTarget']==c['currentTarget']==rr['currentTarget'],'preimage target text mismatch '+repr(ident))
        final=row['selectedTarget'] if ident in selected_ids else row['currentTarget']
        require(rr['crossDisposition']==row['crossDisposition'] and rr['sourceKey']==key and rr['targetFile']==rel,'readback row identity mismatch '+repr(ident))
        require(rr['finalTarget']==final==after[key],'final target value mismatch '+repr(ident))
        require(rr['expectedFinalTargetSha256']==rr['observedPostTargetSha256']==row['selectedTargetSha256']==shat(final) and rr['matches'] is True,'final target hash/match mismatch '+repr(ident))
        if ident in selected_ids:
            selected_row=sm[ident]
            require(row['selectedTarget']==selected_row['selectedTarget'] and row['selectedTargetSha256']==selected_row['selectedTargetSha256'],'selected target extract mismatch '+repr(ident))
            expected_changed.add((rel,key))
        else:
            require(final==before[key],'accepted-current value changed '+repr(ident))
        source_text=source[key]; required=set(PROTECTED.findall(source_text)) | (BRANDS & set(re.findall(r'\b[A-Za-z][A-Za-z0-9]*\b',source_text))) | set(OPAQUE.get(key,[]))
        checks={'placeholderParity':ph(source_text)==ph(final),'inlineCodeParity':code(source_text)==code(final),'markupParity':tags(source_text)==tags(final),'numericParity':nums(source_text)==nums(final),'protectedLiterals':all(x in final for x in required)}
        require(all(checks.values()) and rr['selectedTokenChecks']==checks,'placeholder/markup/numeric/protected-token parity mismatch '+repr(ident))
        require(rr['callerReferenceCount']==row['callerReferenceCount'] and rr['callerContextSha256']==row['callerContextSha256'] and rr['callerPaths']==row['callerPaths'],'caller pin mismatch '+repr(ident))
    # Hash-only holds: infer keys transiently from hashes, verify source and locale values, never emit text.
    for ident in hold_ids:
        h=hm[ident]; rr=rm[ident]; loc=ident[1]; rel=file_for(loc)
        require(rel in file_data,'held locale catalog missing '+repr(ident))
        require(not (HOLD_TEXT_FIELDS & set(rr)) and rr.get('crossDisposition')=='hold' and rr.get('callerReferenceCount')==0,'application hold record leaks text '+repr(ident))
        key_matches=[k for k in source if shat(k)==h['sourceKeySha256']]
        target_matches=[k for k in file_data[rel][0] if shat(k)==h['sourceKeySha256']]
        require(len(key_matches)==len(target_matches)==1,'cannot resolve held key hash uniquely '+repr(ident))
        key=key_matches[0]; before,after=file_data[rel]
        require(shat(f'{key}::{loc}')==h['cellIdSha256'],'held cell ID hash mismatch '+repr(ident))
        require(shat(source[key])==h['sourceTextSha256'],'held source text hash mismatch '+repr(ident))
        require(shat(before[key])==h['currentTargetSha256']==rr['expectedCurrentTargetSha256']==rr['observedPreTargetSha256'],'held target preimage hash mismatch '+repr(ident))
        require(shat(after[key])==h['currentTargetSha256']==rr['expectedFinalTargetSha256']==rr['observedPostTargetSha256'],'held target changed '+repr(ident))
        require(rr['sourceTextSha256']==h['sourceTextSha256'] and rr['sourceKeySha256']==h['sourceKeySha256'] and rr['cellIdSha256']==h['cellIdSha256'] and rr['matches'] is True,'held readback hash mismatch '+repr(ident))
    require(set(changed)==expected_changed and len(changed)==42,'product catalog delta is not exactly 42 selected cells')
    paths=git(repo,'diff-tree','--no-commit-id','--name-only','-r',BASE,APP).decode().splitlines()
    expected_paths=sorted({r['targetFile'] for r in selected}|{'CHANGELOG.md'})
    require(sorted(paths)==expected_paths,'product commit path mismatch')
    require(not any(p.startswith('.github/workflows/') or p==source_path for p in paths),'workflow or English source path changed')
    before_log=git(repo,'show',f'{BASE}:CHANGELOG.md').decode('utf-8'); after_log=git(repo,'show',f'{APP}:CHANGELOG.md').decode('utf-8')
    require(after_log.count(BULLET)==1 and before_log.count(BULLET)==0 and after_log.replace(BULLET+'\n','',1)==before_log,'changelog mismatch')
    pin=json.loads((EVIDENCE/'source-pin-reattestation.json').read_text(encoding='utf-8'))
    require(pin.get('result')=='PASS' and pin.get('head')==BASE and pin.get('tree')==BASE_TREE and pin.get('crossVerifier')=='PASS','source/cross attestation mismatch')
    require(pin.get('sourceFile')==source_path and pin.get('sourceFileSha256')==sha(source_raw) and pin.get('sourceFileGitBlob')==git(repo,'rev-parse',f'{BASE}:{source_path}').decode().strip(),'source file reattestation mismatch')
    require(pin.get('crossChecksumListSha256')==sha((CROSS/'SHA256SUMS.txt').read_bytes()) and pin.get('crossManifestSha256')==sha((CROSS/'manifest.json').read_bytes()),'cross packet reattestation mismatch')
    pin_catalogs={x['path']:x for x in pin.get('targetCatalogs',[])}
    require(set(pin_catalogs)==set(catalog_rows),'source target catalog attestation inventory')
    for rel,rec in catalog_rows.items():
        preinfo=pin_catalogs[rel]
        require(preinfo['preimageSha256']==rec['preimageSha256'] and preinfo['preimageGitBlob']==rec['preimageGitBlob'],'source target catalog preimage reattestation '+rel)
    post=json.loads((EVIDENCE/'application-postflight.json').read_text(encoding='utf-8'))
    require(post.get('productCommit')==APP and post.get('productTree')==APP_TREE and post.get('productParent')==BASE and post.get('preflightPrState')=='OPEN' and post.get('preflightIsDraft') is True,'product postflight mismatch')
    require(post.get('workflowPathCount')==0 and post.get('gitDiffCheck')=='PASS' and post.get('checksReadback',{}).get('testsBuildsScansCiDispatched') is False,'validation record mismatch')
    require(post.get('browserReview') is False and post.get('nativeSpeakerApproval') is False and post.get('mergeReleaseTagPerformed') is False,'unsupported acceptance claim')
    print(json.dumps({'result':'PASS','baseHead':BASE,'baseTree':BASE_TREE,'productCommit':APP,'productTree':APP_TREE,'cells':600,'selected':42,'acceptedCurrent':390,'hashOnlyCallerlessHolds':168,'callerlessKeys':14,'catalogsInspected':12,'catalogsChanged':11,'catalogKeysPerLocale':4165,'changedCatalogValues':len(changed),'callerBackedTokenChecks':432,'tokenCategories':['placeholders','inlineCode','markup','numeric','protectedLiterals'],'crossBundleFiles':len(cross_sums),'evidenceFilesChecksummed':len(evidence_sums),'workflowPaths':0},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
