#!/usr/bin/env python3
import collections, datetime as dt, hashlib, json, re, subprocess
from pathlib import Path

W=Path('/mnt/disks/scratch/task-worktrees/localization-20261102/chaptarrng-pr190-readonly-0650-0699-4701933')
P=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0650-0699-primary-20261102')
O=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0650-0699-crossreview-independent-20261102')
REPO='snapetech-org/chaptarrng'; PR=190
EXPECTED_HEAD='4701933a50d367406fd6749c4baaf4befee22129'; EXPECTED_TREE='2b22ea480c934d2dc41c6813b1296f1a3c41b027'
BRANCH='codex/chaptarrng-localization-complete-20261031'
LOCALES={'es':'es.json','zh-Hans':'zh_CN.json','hi':'hi.json','de':'de.json','ja':'ja.json','fr':'fr.json','pt-BR':'pt_BR.json','ar':'ar.json','ko':'ko.json','zh-Hant':'zh_TW.json','vi':'vi.json','id':'id.json'}
LOCALE_ORDER=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
SRC='src/NzbDrone.Core/Localization/Core/en.json'
FOLLOW='docs/localization/source-followup-20261101.json'
WINDOW=(650,699)
PROTECTED={
 650:['{value0}'],651:['Kavita'],652:['Goodreads','OAuth'],653:['M4B','CPU','{value0}'],
 654:['Check before download','SABnzbd'],655:['Chaptarr','{value0}','{value1}'],656:['API'],657:['{value0}'],
 660:['foreignBookId','foreignAuthorId'],662:['PAR'],663:['Apprise'],664:['{value0}'],
 665:['Disabled','IndexerOnly','ProxyEverything'],667:['Join'],668:['Grimmory'],671:['Hardcover'],672:['Chaptarr'],
 676:['Aria2','1.34.0','{value0}'],678:['BookOrbit','URL'],679:['Goodreads','{value0}'],
 680:['Synology','synoindex'],684:['MQTT'],686:['bookFileIds','downloadId'],688:['{value0}'],
 689:['Goodreads','RSS'],690:['{value0}'],691:['{value0}','{value1}'],692:['API'],
 693:['mediaType','all','audiobook','ebook','{value0}'],695:['Mailgun'],696:['API'],
 697:['foreignSeriesId'],698:['mediaType'],699:['Http','Socks4','Socks5']
}
OVERRIDES={
 '650|ko':("경로 '{value0}'은(는) 이미 루트 폴더로 설정되어 있습니다.",
          'The proposed translation fixes the plant-root mistranslation, but uses U+3002, which is not the usual Korean sentence stop. Retain the terminology correction and use a Korean full stop.'),
}

if O.exists() and any(O.iterdir()): raise SystemExit(f'Output directory already contains files: {O}')
if O.exists(): O.rmdir()
O.mkdir(parents=True)

def sha(b): return hashlib.sha256(b).hexdigest()
def shat(s): return sha(s.encode('utf-8'))
def jbytes(x): return json.dumps(x,ensure_ascii=False,separators=(',',':')).encode('utf-8')
def run(args,cwd=W): return subprocess.check_output(args,cwd=cwd).decode('utf-8').strip()
def git(*args): return run(['git',*args],W)
def show(path): return subprocess.check_output(['git','show',f'HEAD:{path}'],cwd=W)
def blob(path): return git('rev-parse',f'HEAD:{path}')
def readjson(path): return json.loads(path.read_text(encoding='utf-8'))
def rows(path): return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def writejson(name,obj): (O/name).write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def writejsonl(name,items): (O/name).write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in items),encoding='utf-8')
def placeholders(s): return sorted(set(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s)))
def markup(s):
    if re.fullmatch(r'<[^<>/]+>',s): return []
    return re.findall(r'</?[A-Za-z][^>]*>',s)
def protected_match(literal,text): return literal in text
def live_state():
    pr=json.loads(run(['gh','pr','view',str(PR),'--repo',REPO,'--json','state,isDraft,headRefOid,headRefName,baseRefName,url']))
    remote=run(['git','ls-remote','origin',f'refs/heads/{pr["headRefName"]}']).split()[0]
    return pr,remote

def verify_pin(ordinal,sid,source_text,ref):
    path=ref['file']; raw=(W/path).read_bytes(); lines=raw.decode('utf-8',errors='replace').splitlines()
    n=ref['currentLine']; line=lines[n-1]
    before=lines[max(0,n-3):n-1]; after=lines[n:min(len(lines),n+2)]
    exact={
      'currentLineText':line==ref['currentLineText'],
      'currentLineSha256':shat(line)==ref['currentLineSha256'],
      'contextBefore':before==ref['contextBefore'],
      'contextAfter':after==ref['contextAfter'],
      'currentFileSha256':sha(raw)==ref['currentFileSha256'],
      'currentFileBlob':blob(path)==ref['currentFileBlob'],
    }
    if ref.get('matchedSourceId'):
        exact['matchedSourceId']=ref['matchedSourceId']==sid
    if ref.get('matchedSourceText'):
        mode=ref['lineMatchMethod']
        if mode in ('source-text-exact','source-text-fragment'):
            exact['matchedSourceTextKnown']=ref['matchedSourceText'] in (source_text, line) or ref['matchedSourceText'] in source_text
        else:
            exact['matchedSourceTextRecorded']=bool(ref['matchedSourceText'])
    return {**ref,'sourceOrdinal':ordinal,'sourceId':sid,'sourceTextSha256':shat(source_text),'liveFileSha256':sha(raw),'liveFileBlob':blob(path),'liveLineText':line,'liveLineSha256':shat(line),'liveContextBefore':before,'liveContextAfter':after,'fieldChecks':exact,'allPinChecksPass':all(exact.values())}

# Re-attest exact checkout, PR and remote head before reading evidence.
head=git('rev-parse','HEAD'); tree=git('rev-parse','HEAD^{tree}'); status=git('status','--porcelain')
pr_before,remote_before=live_state()
assert not status and head==EXPECTED_HEAD and tree==EXPECTED_TREE
assert pr_before['state']=='OPEN' and pr_before['isDraft'] is True and pr_before['headRefOid']==EXPECTED_HEAD and pr_before['headRefName']==BRANCH
assert remote_before==EXPECTED_HEAD

# Verify both supplied manifests. SHA256SUMS covers packet files; INPUT-SHA256SUMS pins repository inputs.
manifest=[]
for line in (P/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
    digest,name=line.split(None,1); name=name.strip(); actual=sha((P/name).read_bytes())
    manifest.append({'path':name,'expectedSha256':digest,'actualSha256':actual,'matches':digest==actual,'sizeBytes':(P/name).stat().st_size})
assert len(manifest)==19 and all(x['matches'] for x in manifest)
input_manifest=[]
for line in (P/'INPUT-SHA256SUMS').read_text(encoding='utf-8').splitlines():
    digest,path=line.split(None,1); path=path.strip(); raw=show(path); actual=sha(raw)
    input_manifest.append({'path':path,'expectedSha256':digest,'actualSha256':actual,'matches':digest==actual,'gitBlob':blob(path)})
assert len(input_manifest)==63 and all(x['matches'] for x in input_manifest)
primary_summary=readjson(P/'summary.json'); primary_manifest=readjson(P/'manifest.json')
assert primary_summary['exactHead']==EXPECTED_HEAD and primary_summary['exactTree']==EXPECTED_TREE
assert primary_manifest['head']==EXPECTED_HEAD and primary_manifest['tree']==EXPECTED_TREE

# Independently reconstruct source ordinal inventory and all 12 catalogs from exact HEAD.
source_raw=show(SRC); source=json.loads(source_raw)
follow_raw=show(FOLLOW); follow=json.loads(follow_raw); ids=follow['currentMissingIds']
assert len(ids)==1210 and len(set(ids))==1210
source_id_list_sha=sha(jbytes(ids))
assert source_id_list_sha==primary_summary['sourceIdListSha256']
source_ids=ids[650:700]
assert len(source_ids)==50
assert sha(jbytes(source_ids))==primary_summary['sourceSliceIdsSha256']
source_slice=rows(P/'source-slice.jsonl')
assert len(source_slice)==50
assert [r['sourceOrdinal'] for r in source_slice]==list(range(650,700))
assert [r['sourceId'] for r in source_slice]==source_ids
catalogs={}; catalog_info=[]
for locale in LOCALE_ORDER:
    rel=f'src/NzbDrone.Core/Localization/Core/{LOCALES[locale]}'
    raw=show(rel); cat=json.loads(raw); catalogs[locale]=cat
    catalog_info.append({'locale':locale,'path':rel,'fileSha256':sha(raw),'gitBlob':blob(rel),'keyCount':len(cat)})
assert all(set(c)==set(source) for c in catalogs.values())
assert all(source.get(sid) is not None for sid in source_ids)

# Re-attest 50 source rows and 600 frozen current/review cells.
input_cells=rows(P/'input-cells.jsonl'); review_cells=rows(P/'review-cells.jsonl')
candidates=rows(P/'correction-candidates.jsonl'); decisions=readjson(P/'review-decisions.json')
caller_context=rows(P/'caller-context.jsonl'); protected_primary=rows(P/'protected-literal-integrity.jsonl')
assert len(input_cells)==600 and len(review_cells)==600 and len(candidates)==99
assert len(caller_context)==50 and len(protected_primary)==600
caller_by_ord={r['sourceOrdinal']:r for r in caller_context}
source_by_ord={r['sourceOrdinal']:r for r in source_slice}
review_by={(r['sourceOrdinal'],r['locale']):r for r in review_cells}
input_by={(r['sourceOrdinal'],r['locale']):r for r in input_cells}
candidate_by={(r['sourceOrdinal'],r['locale']):r for r in candidates}
protected_by={(r['sourceOrdinal'],r['locale']):r for r in protected_primary}
assert len(review_by)==600 and len(input_by)==600 and len(candidate_by)==99 and len(protected_by)==600

pin_rows=[]; total_refs=0; caller_files=set()
for srow in source_slice:
    ordinal=srow['sourceOrdinal']; sid=srow['sourceId']; source_text=source[sid]
    assert source_text==srow['source'] and shat(source_text)==srow['sourceTextSha256']
    assert shat(sid)==srow['sourceKeySha256']
    assert srow['sourceFile']==SRC and sha(source_raw)==srow['sourceFileSha256'] and blob(SRC)==srow['sourceFileBlob']
    refs=caller_by_ord[ordinal]['callerRefs']; total_refs+=len(refs)
    assert caller_by_ord[ordinal]['sourceId']==sid and caller_by_ord[ordinal]['sourceText']==source_text
    assert caller_by_ord[ordinal]['callerContextSha256']==sha(jbytes(refs))
    assert srow['callerRefs']==refs and srow['callerContextSha256']==sha(jbytes(refs))
    for ref in refs:
        pin=verify_pin(ordinal,sid,source_text,ref); assert pin['allPinChecksPass'], (ordinal,ref['file'],ref['currentLine'],pin['fieldChecks'])
        pin_rows.append(pin); caller_files.add(ref['file'])
assert total_refs==59 and len(caller_files)==48

# Protected literal policy matches the primary source-specific list; exact source/current/proposal checks.
current_mismatch_cells=[]; candidate_mismatch_cells=[]
cell_rows=[]; candidate_rows=[]
for ordinal in range(650,700):
    sid=source_ids[ordinal-650]; src=source[sid]; srow=source_by_ord[ordinal]
    assert sid==srow['sourceId'] and src==srow['source']
    refs=caller_by_ord[ordinal]['callerRefs']
    for locale in LOCALE_ORDER:
        r=review_by[(ordinal,locale)]; inp=input_by[(ordinal,locale)]; live=catalogs[locale][sid]
        assert r['source']==src and r['sourceTextSha256']==shat(src) and r['sourceKeySha256']==shat(sid)
        assert r['currentTarget']==live and r['currentTargetSha256']==shat(live)
        assert inp['currentTarget']==live and inp['currentTargetSha256']==shat(live)
        target_rel=f'src/NzbDrone.Core/Localization/Core/{LOCALES[locale]}'
        raw=show(target_rel); assert sha(raw)==r['targetFileSha256']==inp['targetFileSha256']
        assert blob(target_rel)==r['targetFileBlob']==inp['targetFileBlob']
        assert r['targetFile']==target_rel and inp['targetFile']==target_rel
        assert r['callerRefs']==refs and r['callerContextSha256']==sha(jbytes(refs))
        assert inp['callerContextSha256']==sha(jbytes(refs))
        src_ph=placeholders(src); now_ph=placeholders(live); src_markup=markup(src); now_markup=markup(live)
        assert src_ph==now_ph and src_markup==now_markup
        candidate=candidate_by.get((ordinal,locale))
        if candidate:
            decision_record=decisions['findings'][f'{ordinal}|{locale}']
            assert decision_record[0]==r['disposition'] and decision_record[1]==r['recommendedTarget']
            proposed=candidate['recommendedTarget']
            assert r['recommendedTarget']==proposed and r['recommendedTargetSha256']==shat(proposed)==candidate['recommendedTargetSha256']
            assert candidate['currentTarget']==live and candidate['currentTargetSha256']==shat(live)
            assert placeholders(proposed)==src_ph and markup(proposed)==src_markup
        else:
            proposed=None
            assert r['recommendedTarget'] is None and r['recommendedTargetSha256'] is None
        literals=PROTECTED.get(ordinal,[])
        c_checks=[]
        for lit in literals:
            c_checks.append({'literal':lit,'sourceContains':protected_match(lit,src),'currentContains':protected_match(lit,live),'proposalContains':protected_match(lit,proposed) if proposed is not None else None})
        missing_current=[x['literal'] for x in c_checks if x['sourceContains'] and not x['currentContains']]
        missing_proposal=[x['literal'] for x in c_checks if x['sourceContains'] and proposed is not None and not x['proposalContains']]
        # SABnzbd is a caller-known protected product name misspelled in the English source; candidates deliberately use the canonical caller spelling.
        known_brand_corrected=(ordinal==654 and proposed is not None and 'SABnzbd' in proposed)
        if ordinal==654:
            missing_current=['SABnzbd'] if not protected_match('SABnzbd',live) else []
            missing_proposal=[lit for lit in literals if proposed is not None and not protected_match(lit,proposed)]
        protected_row=protected_by[(ordinal,locale)]
        assert protected_row['sourceText']==src and protected_row['currentTarget']==live and protected_row['currentTargetSha256']==shat(live)
        primary_final=proposed if proposed is not None else live
        assert protected_row['finalTarget']==primary_final and protected_row['finalTargetSha256']==shat(primary_final)
        assert protected_row['currentMismatches']==missing_current and protected_row['recommendedMismatches']==missing_proposal
        if missing_current: current_mismatch_cells.append({'sourceOrdinal':ordinal,'sourceId':sid,'locale':locale,'missing':missing_current})
        if missing_proposal: candidate_mismatch_cells.append({'sourceOrdinal':ordinal,'sourceId':sid,'locale':locale,'missing':missing_proposal})
        cross_key=f'{ordinal}|{locale}'
        if candidate:
            disposition='revise-proposal' if cross_key in OVERRIDES else 'accept-proposal'
            preferred=OVERRIDES[cross_key][0] if cross_key in OVERRIDES else proposed
        else:
            disposition='accept-current'; preferred=live
        cell_rows.append({
            'exactHead':EXPECTED_HEAD,'exactTree':EXPECTED_TREE,'sourceOrdinal':ordinal,'sourceId':sid,'locale':locale,
            'sourceText':src,'sourceKeySha256':shat(sid),'sourceTextSha256':shat(src),
            'liveCurrentTarget':live,'liveCurrentTargetSha256':shat(live),
            'primaryCurrentTargetMatchesLive':True,'primaryDisposition':r['disposition'],
            'independentDisposition':disposition,'independentlyPreferredTarget':preferred,
            'independentlyPreferredTargetSha256':shat(preferred),
            'candidateProposal':proposed,'candidateProposalSha256':shat(proposed) if proposed is not None else None,
            'candidateKnownBrandCorrection':known_brand_corrected,
            'sourcePlaceholders':src_ph,'currentPlaceholders':now_ph,'preferredPlaceholders':placeholders(preferred),
            'sourceMarkup':src_markup,'currentMarkup':now_markup,'preferredMarkup':markup(preferred),
            'protectedLiterals':literals,'protectedChecks':c_checks,
            'currentProtectedMismatch':missing_current,'proposalProtectedMismatch':missing_proposal,
            'callerRefsCount':len(refs),'callerContextSha256':sha(jbytes(refs)),
        })

# Adjudicate every proposal independently using source and the live production caller context.
reason_by_ord={
650:'Path validation rejects a duplicate filesystem root folder; the Japanese and Korean proposals use the filesystem-root term rather than a plant-root literal.',
651:'This is a server connection validation for Kavita; the proposal names the Kavita server and uses a natural connection-failure construction.',
652:'The validator accepts either a Goodreads user ID or already-existing OAuth credentials; proposal fixes the alternatives and credential ordering.',
654:'Sabnzbd.cs rejects a specific Check before download configuration. Proposal corrects the product name to SABnzbd and keeps the exact option label.',
659:'The Goodreads and Hardcover import-list validators require an ebook root only when ebook monitoring is enabled; proposal retains that condition and the root-folder meaning.',
663:'AppriseProxy reports an API connection failure, HTTP status, and exception detail. Proposals retain Apprise/API identity and both diagnostic placeholders.',
664:'CustomScript reports Process.ExitCode for a failed script run. Proposals express a script exit code and preserve {value0}.',
667:'JoinProxy returns a Join API connection error with a retry instruction. Proposals preserve the service and retry action.',
668:'GrimmoryProxy validates the selected ebook library ID; Spanish proposal restores the ebook qualifier and Grimmory name.',
670:'RootFolderResource prohibits audiobook settings on folders reserved for ebooks; the Arabic proposal preserves that exact restriction.',
671:'Hardcover import-list lookup failed to retrieve the current user; the French proposal expresses inability to retrieve the current Hardcover user.',
672:'StartingUpMiddleware returns this response while the service is starting; proposals express in-progress startup and retry later.',
673:'GrimmorySettings requires a selected library when AudiobookLibraryId is unset; the Chinese proposals replace the misleading public-library term with the media-library term.',
675:'CustomScript validation reports a missing configured file; Japanese and Korean proposals make the error natural while preserving the missing-file meaning.',
676:'The caller validates an Aria2 minimum version; Indonesian proposal improves version phrasing and keeps 1.34.0 and {value0}.',
677:'Calibre settings reject output formats that are not valid; proposals repair invalid spelling/wording in Spanish and Chinese/Japanese.',
678:'BookOrbit connection validation instructs the user to check URL, credentials, and logs; proposals retain the service and URL literal.',
680:'SynologyIndexer fails its test when the device is not Synology or synoindex is unavailable; proposals state those alternatives coherently and retain both identifiers.',
682:'RetagBookController requires authorId or bookId; proposals express an either/or requirement and retain the exact field names.',
683:'ManualImportController could not find the selected edition and supplies the exception detail; proposals preserve both placeholders and the selected-edition meaning.',
687:'Hadouken settings requires a nonempty password; proposals correct Arabic agreement and improve Korean/Vietnamese wording.',
688:'DevelopmentConfigController reports a metadata service lacking a required capability; proposals retain {value0} and express the missing feature/capability naturally.',
690:'PendingImportService confirms that an item was added to the library; Portuguese and Vietnamese proposals express successful completion naturally and preserve {value0}.',
691:'DevelopmentConfigController reports actual and expected metadata server service names; Vietnamese proposal clarifies the mismatch and preserves both values.',
692:'Chaptarr and PushBullet validation reject an invalid API key; proposals use natural key/API order and keep the API acronym.',
696:'QBittorrentSettings requires an empty password when API-key auth is used; proposals preserve the condition and distinguish the password field from the API key.',
}
for c in candidates:
    ordinal=c['sourceOrdinal']; locale=c['locale']; key=f'{ordinal}|{locale}'; src=c['source']; proposed=c['recommendedTarget']
    assert ordinal in reason_by_ord and c['sourceTextSha256']==shat(src) and c['recommendedTargetSha256']==shat(proposed)
    if key in OVERRIDES:
        preferred,why=OVERRIDES[key]; disposition='revise-proposal'
    else:
        preferred=proposed; why=reason_by_ord[ordinal]; disposition='accept-proposal'
    assert placeholders(preferred)==placeholders(src) and markup(preferred)==markup(src)
    assert all(protected_match(lit,preferred) for lit in PROTECTED.get(ordinal,[]) if ordinal!=654 or lit!='SABnzbd' or lit in preferred)
    candidate_rows.append({
        'exactHead':EXPECTED_HEAD,'exactTree':EXPECTED_TREE,'sourceOrdinal':ordinal,'sourceId':c['sourceId'],'locale':locale,
        'sourceText':src,'sourceTextSha256':shat(src),'currentTarget':c['currentTarget'],'currentTargetSha256':shat(c['currentTarget']),
        'primaryProposal':proposed,'primaryProposalSha256':shat(proposed),'primaryDisposition':c['disposition'],
        'independentDisposition':disposition,'independentRationale':why,
        'crossReviewSuggestedTarget':preferred,'crossReviewSuggestedTargetSha256':shat(preferred),
        'candidatePlaceholderParity':placeholders(preferred)==placeholders(src),
        'candidateMarkupParity':markup(preferred)==markup(src),
        'protectedLiterals':PROTECTED.get(ordinal,[]),
        'sourceProductTypoNote':'English source says Sabnbzd; caller is in Sabnzbd.cs and the option/service are SABnzbd. Correcting the canonical brand in the translated proposal is appropriate; source text should be fixed separately.' if ordinal==654 else None,
    })
assert len(candidate_rows)==99 and len(cell_rows)==600

# Verify current protected mismatch classification; it must be confined to the misspelled SABnzbd source.
assert len(current_mismatch_cells)==12 and all(x['sourceOrdinal']==654 and x['missing']==['SABnzbd'] for x in current_mismatch_cells)
assert not candidate_mismatch_cells

# Re-attest W649 previous-window cell values and W650 adjacent-boundary values against exact live catalogs.
w649_rows=rows(P/'prior-context-dispositions.jsonl'); w650_rows=rows(P/'boundary-next-source-650.jsonl')
assert len(w649_rows)==12 and len(w650_rows)==12
w649_id=ids[649]; w650_id=ids[650]
assert all(x['contextSourceOrdinal']==649 and x['sourceId']==w649_id for x in w649_rows)
assert all(x['sourceOrdinal']==650 and x['sourceId']==w650_id for x in w650_rows)
boundary_rows=[]; w649_ref_checks=[]
for old,new in zip(w649_rows,w650_rows):
    locale=old['locale']; assert new['locale']==locale
    old_source=source[w649_id]; new_source=source[w650_id]
    old_live=catalogs[locale][w649_id]; new_live=catalogs[locale][w650_id]
    assert old['source']==old_source and old['sourceTextSha256']==shat(old_source)
    assert old['liveCurrentTarget']==old_live and old['liveCurrentTargetSha256']==shat(old_live)
    assert old['priorCrossReviewFinalTarget']==old_live and old['priorCrossReviewFinalTargetSha256']==shat(old_live)
    assert old['liveTargetMatchesPriorCrossReviewFinal'] is True
    assert new['source']==new_source and new['sourceTextSha256']==shat(new_source)
    assert new['liveTarget']==new_live and new['liveTargetSha256']==shat(new_live)
    assert new['previousTarget']==new_live and new['previousTargetSha256']==shat(new_live)
    target_rel=f'src/NzbDrone.Core/Localization/Core/{LOCALES[locale]}'
    target_raw=show(target_rel)
    assert new['targetFile']==target_rel and new['targetFileSha256']==sha(target_raw) and new['targetFileBlob']==blob(target_rel)
    refs=old['liveCallerRefs']; assert old['liveCallerContextSha256']==sha(jbytes(refs))
    for ref in refs:
        pin=verify_pin(649,w649_id,old_source,ref); assert pin['allPinChecksPass']; w649_ref_checks.append(pin)
    boundary_rows.append({
        'exactHead':EXPECTED_HEAD,'exactTree':EXPECTED_TREE,'locale':locale,
        'priorWindow':{'sourceOrdinal':649,'sourceId':w649_id,'sourceText':old_source,'sourceTextSha256':shat(old_source),'previousFinalTarget':old_live,'liveTarget':old_live,'liveTargetSha256':shat(old_live),'primaryCurrentMatchesLive':old['primaryCurrentTargetMatchesLive'],'primaryRecommendationMatchesLive':old['primaryRecommendationMatchesLive']},
        'nextWindow':{'sourceOrdinal':650,'sourceId':w650_id,'sourceText':new_source,'sourceTextSha256':shat(new_source),'previousTarget':new['previousTarget'],'liveTarget':new_live,'liveTargetSha256':shat(new_live),'targetFile':target_rel,'targetFileSha256':sha(target_raw),'targetFileBlob':blob(target_rel),'catalogChangedSincePreviousBoundary':new['catalogFileChangedSinceBoundary']},
    })

prior_boundary=readjson(P/'prior-disposition-boundary.json')
assert prior_boundary['matchingPriorRowCount']==0 and prior_boundary['contextOnlyPreviousRows']==12 and prior_boundary['w650AdjacentBoundaryRows']==12
assert prior_boundary['w649CrossReviewFinalTargetsMatchLive']==12 and prior_boundary['w650SourceAndTargetsMatchPriorBoundary'] is True
assert len(w649_ref_checks)>=1
w649_unique_ref_count=len({(x['file'],x['currentLine'],x['lineMatchMethod']) for x in w649_ref_checks})

# Additional English-source issues visible in pinned caller text; no catalog/repository edits.
source_findings=[]
for ordinal,expected,recommended,reason in [
  (654,"Disable 'Check before download' option in Sabnbzd","Disable the 'Check before download' option in SABnzbd.","The source English message misspells SABnzbd as Sabnbzd; the pinned production caller is src/NzbDrone.Core/Download/Clients/Sabnzbd/Sabnzbd.cs and the protected product name is SABnzbd."),
  (695,"Unable to send test message though Mailgun.","Unable to send a test message through Mailgun.","The source English string has a clear though/through typo. The pinned caller is the Mailgun test-message failure path; all current locale targets already express the intended through-Mailgun meaning."),
]:
    sid=source_ids[ordinal-650]; assert source[sid]==expected
    ref=caller_by_ord[ordinal]['callerRefs'][0]
    pin=verify_pin(ordinal,sid,source[sid],ref); assert pin['allPinChecksPass']
    source_findings.append({'sourceOrdinal':ordinal,'sourceId':sid,'sourceText':expected,'sourceTextSha256':shat(expected),'sourceFile':SRC,'sourceFileSha256':sha(source_raw),'callerReference':pin,'recommendedEnglishSourceText':recommended,'finding':reason,'translationDisposition':'candidate/current translations reviewed against intended caller meaning; source wording follow-up required','readOnly':True})

# End-state recheck guards against branch movement during review.
pr_after,remote_after=live_state(); assert pr_after==pr_before and remote_after==EXPECTED_HEAD
assert git('rev-parse','HEAD')==EXPECTED_HEAD and git('rev-parse','HEAD^{tree}')==EXPECTED_TREE
assert not git('status','--porcelain')

# Write independently reviewed packet.
writejsonl('caller-pin-reattestation.jsonl',pin_rows)
writejsonl('w649-w650-boundary-reattestation.jsonl',boundary_rows)
writejsonl('w649-caller-reattestation.jsonl',w649_ref_checks)
writejsonl('cell-crossreview.jsonl',cell_rows)
writejsonl('candidate-adjudication.jsonl',candidate_rows)
writejsonl('source-followup-findings.jsonl',source_findings)

primary_integrity={
 'primaryPacketPath':str(P),'primarySHA256SUMSFileSha256':sha((P/'SHA256SUMS').read_bytes()),
 'primaryINPUTSHA256SUMSFileSha256':sha((P/'INPUT-SHA256SUMS').read_bytes()),
 'primaryPacketFileCount':len(manifest),'primaryPacketFilesVerified':all(x['matches'] for x in manifest),'primaryPacketFiles':manifest,
 'repositoryInputCount':len(input_manifest),'repositoryInputsVerified':all(x['matches'] for x in input_manifest),'repositoryInputs':input_manifest,
 'manifestSha256':sha((P/'SHA256SUMS').read_bytes()),'inputManifestSha256':sha((P/'INPUT-SHA256SUMS').read_bytes()),
 'exactHead':EXPECTED_HEAD,'exactTree':EXPECTED_TREE,'prBefore':pr_before,'remoteHeadBefore':remote_before,
 'englishSourceCatalog':{'path':SRC,'fileSha256':sha(source_raw),'gitBlob':blob(SRC),'keyCount':len(source)},
 'sourceFollowup':{'path':FOLLOW,'fileSha256':sha(follow_raw),'gitBlob':blob(FOLLOW),'currentMissingIds':len(ids),'sourceIdListSha256':source_id_list_sha},
 'localeCatalogs':catalog_info,'currentCellsReattested':len(cell_rows),'callerRefsReattested':total_refs,
 'callerSourceIds':len(caller_context),'callerFiles':len(caller_files),'w649BoundaryCells':len(w649_rows),'w650BoundaryCells':len(w650_rows),
 'w649CallerRefRowsReattested':len(w649_ref_checks),'w649UniqueCallerRefsReattested':w649_unique_ref_count,'w650CallerRefsIncludedInWindowPins':len(caller_by_ord[650]['callerRefs']),
}
writejson('primary-input-integrity.json',primary_integrity)

independent_counts=dict(collections.Counter(x['independentDisposition'] for x in cell_rows))
candidate_counts=dict(collections.Counter(x['independentDisposition'] for x in candidate_rows))
structural={
 'exactHead':EXPECTED_HEAD,'exactTree':EXPECTED_TREE,'windowOrdinals':[650,699],
 'sourceIdCount':len(source_ids),'localeCount':len(LOCALE_ORDER),'cellCount':len(cell_rows),'candidateCount':len(candidate_rows),
 'sourceIdListCount':len(ids),'sourceIdListSha256':source_id_list_sha,'sourceSliceSha256':sha(jbytes(source_ids)),
 'localeKeySetsMatchEnglish':all(set(c)==set(source) for c in catalogs.values()),
 'allSourceCurrentPlaceholderSetsMatch':all(placeholders(source[r['sourceId']])==placeholders(catalogs[r['locale']][r['sourceId']]) for r in review_cells),
 'allSourceCurrentMarkupMatch':all(markup(source[r['sourceId']])==markup(catalogs[r['locale']][r['sourceId']]) for r in review_cells),
 'placeholderMismatchCells':sum(not r['placeholderParity'] for r in review_cells),
 'markupMismatchCells':sum(not r['markupParity'] for r in review_cells),
 'currentProtectedMismatchCells':len(current_mismatch_cells),'currentProtectedMismatchDetails':current_mismatch_cells,
 'proposalProtectedMismatchCells':len(candidate_mismatch_cells),'allProposalPlaceholdersMatch':all(placeholders(source[c['sourceId']])==placeholders(c['recommendedTarget']) for c in candidates),
 'allProposalMarkupMatches':all(markup(source[c['sourceId']])==markup(c['recommendedTarget']) for c in candidates),
 'proposalCountByLocale':dict(collections.Counter(c['locale'] for c in candidates)),
 'callerRefs':total_refs,'callerFiles':len(caller_files),'callerReferencesVerified':all(x['allPinChecksPass'] for x in pin_rows),
 'w649CallerRefsReattested':len(w649_ref_checks),'w650BoundaryRows':len(w650_rows),
 'primaryDispositions':dict(collections.Counter(r['disposition'] for r in review_cells)),
 'independentCellDispositions':independent_counts,'independentCandidateDispositions':candidate_counts,
 'nativeSpeakerReviewStillRecommended':True,
}
assert structural['placeholderMismatchCells']==0 and structural['markupMismatchCells']==0
assert structural['allProposalPlaceholdersMatch'] and structural['allProposalMarkupMatches']
assert structural['proposalProtectedMismatchCells']==0
writejson('structural-integrity.json',structural)

summary={
 'attestedAtUtc':dt.datetime.now(dt.timezone.utc).isoformat(),'repository':REPO,'pullRequest':PR,
 'pullRequestState':pr_after,'remoteHead':remote_after,'head':EXPECTED_HEAD,'tree':EXPECTED_TREE,'branch':BRANCH,
 'window':'W650–W699','sourceIds':50,'locales':12,'cells':600,
 'primaryCallerRefs':total_refs,'primaryCallerSourceIds':len(caller_context),'primaryCallerFiles':len(caller_files),
 'w649BoundaryLocaleRows':12,'w649CallerRefRowsReattested':len(w649_ref_checks),'w649UniqueCallerRefsReattested':w649_unique_ref_count,'w650BoundaryLocaleRows':12,
 'candidateProposals':99,'candidateDispositionCounts':candidate_counts,'cellDispositionCounts':independent_counts,
 'proposalRevisions':sum(v for k,v in candidate_counts.items() if k=='revise-proposal'),
 'proposalRejections':sum(v for k,v in candidate_counts.items() if k=='reject-proposal'),
 'proposalHolds':sum(v for k,v in candidate_counts.items() if k=='hold'),
 'missedSourceFollowups':len(source_findings),'sourceFollowupOrdinals':[x['sourceOrdinal'] for x in source_findings],
 'placeholderMismatchCells':0,'markupMismatchCells':0,'currentProtectedMismatchCells':12,'proposalProtectedMismatchCells':0,
 'priorSourceIdOverlap':0,'readOnly':True,'repositoryModified':False,'testsBuildsCiBrowserRun':False,
 'notes':[
  'Primary SHA256SUMS and INPUT-SHA256SUMS both verify; all listed repository inputs match exact-head blobs and bytes.',
  'The primary packet provides 59 exact production caller refs across 50 IDs and 48 files; all pins were reattested. The W649 prior boundary adds its caller-context ref and 12 locale values; W650 has 12 boundary locale rows.',
  'The 99 proposals were independently reviewed against source meaning and pinned C# callers. 98 are accepted verbatim; W650 Korean is revised only to use a Korean full stop.',
  'Twelve current targets miss the protected SABnzbd product name because English source says “Sabnbzd”; all proposed targets use SABnzbd. The source typo itself needs correction.',
  'W695 English source says “though Mailgun”; the caller and all locale targets show intended “through Mailgun”. Source correction is a missed fix.',
  'No repository edits, tests, builds, CI, or browser actions were performed.',
 ],
 'packetFiles':['README.md','primary-input-integrity.json','structural-integrity.json','caller-pin-reattestation.jsonl','w649-w650-boundary-reattestation.jsonl','w649-caller-reattestation.jsonl','cell-crossreview.jsonl','candidate-adjudication.jsonl','source-followup-findings.jsonl','summary.json','cross_review.py','SHA256SUMS']
}
writejson('summary.json',summary)
readme=f'''# ChaptarrNG PR #190 W650–W699 independent cross-review\n\n- Live PR #{PR} remained OPEN/DRAFT at `{EXPECTED_HEAD}` / tree `{EXPECTED_TREE}` on `{BRANCH}`; configured `origin` branch head and clean detached exact-head worktree matched before and after review.\n- Both primary manifests verify: `SHA256SUMS` SHA256 `{sha((P/'SHA256SUMS').read_bytes())}` and `INPUT-SHA256SUMS` SHA256 `{sha((P/'INPUT-SHA256SUMS').read_bytes())}`.\n- Independently reattested all 600 cells, 59 exact caller references across 50 source IDs/48 files, W649 previous-window context, and W650 next-source boundary.\n- Independent cell dispositions: {independent_counts}. Candidate outcomes: {candidate_counts}. One proposal was revised for Korean punctuation; none rejected or held.\n- Placeholder and markup parity pass. All 12 current protected-literal mismatches are the W654 Sabnbzd/SABnzbd brand issue; proposed targets preserve the canonical product/setting literals.\n- Missed English-source fixes: W654 `Sabnbzd` should be `SABnzbd`; W695 `though Mailgun` should be `through Mailgun`. The caller contexts confirm both.\n- Read-only review only; no repo edits, tests, builds, CI, or browser actions.\n\nSee `summary.json`, `primary-input-integrity.json`, `structural-integrity.json`, `cell-crossreview.jsonl`, `candidate-adjudication.jsonl`, `caller-pin-reattestation.jsonl`, `w649-w650-boundary-reattestation.jsonl`, and `source-followup-findings.jsonl`.\n'''
(O/'README.md').write_text(readme,encoding='utf-8')
# Include this reproducible script in the packet, then checksum each output except the checksum file itself.
(O/'cross_review.py').write_bytes(Path(__file__).read_bytes())
manifest_out=[]
for f in sorted(x for x in O.iterdir() if x.is_file() and x.name!='SHA256SUMS'):
    manifest_out.append(f'{sha(f.read_bytes())}  {f.name}')
(O/'SHA256SUMS').write_text('\n'.join(manifest_out)+'\n',encoding='utf-8')
for line in (O/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
    digest,name=line.split(None,1); assert sha((O/name.strip()).read_bytes())==digest
print(json.dumps({'packet':str(O),'SHA256SUMS_SHA256':sha((O/'SHA256SUMS').read_bytes()),'summary':summary,'packetSizeBytes':sum(x.stat().st_size for x in O.iterdir() if x.is_file())},ensure_ascii=False,indent=2))
