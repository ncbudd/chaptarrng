import collections, hashlib, json, pathlib, re, subprocess

REPO = 'snapetech-org/chaptarrng'
PR = 190
W = pathlib.Path('/mnt/disks/scratch/task-worktrees/localization-20261102/chaptarrng-pr190-audit')
P = pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0450-0499-primary-20261102')
PREV = pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0400-0449-crossreview-by-root-child-20261102')
O = pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0450-0499-crossreview-20261102')
FROZEN = '2eb0ae6eb15ebc366eea44dd969265c0f6366445'
FROZEN_TREE = '1340ba7d0642217aa81e3789e908931bd6fa74f1'
CHECKPOINT = '48584ef3091372705d7774799ff33d77ce582ce6'
CHECKPOINT_TREE = '33b635d2fa6d5d3f1b3207002daedd6993ce2be1'
LIVE = '70f5ad2c2dc8222d8f35e09ba81ffa12acfff856'
LIVE_TREE = '9bd50b4f149f69f7cd5b78937b45fe1745e6c695'
LOCALES = {'es':'es.json','zh-Hans':'zh_CN.json','hi':'hi.json','de':'de.json','ja':'ja.json','fr':'fr.json','pt-BR':'pt_BR.json','ar':'ar.json','ko':'ko.json','zh-Hant':'zh_TW.json','vi':'vi.json','id':'id.json'}

REVISIONS = {
 (457,'zh-Hans'): '所选版本“{value0}”不属于所选图书 {value1}。',
 (457,'hi'): "चुना गया संस्करण '{value0}' चुनी गई पुस्तक {value1} का नहीं है।",
 (467,'id'): "Folder akar yang dipilih '{value0}' tidak memiliki profil kualitas bawaan untuk {value1}.",
 (483,'ko'): '시리즈 변형 {value0} 삭제가 성공적으로 완료되었습니다.',
 (485,'ko'): '선택한 에디션 ID {value0}를 찾을 수 없습니다.',
}
REASONS = {
 450: 'The caller supplies the metadata-server exception message. These translations express a failed connection in idiomatic locale phrasing and keep the dynamic detail in place.',
 451: 'The message concerns proxy authentication, and HTTP 407 is the precise status. The candidates name the proxy authentication failure and clearly direct users to check both credentials.',
 453: 'The candidates preserve the required minimum version, the reported-version placeholder, and rTorrent as the product name while fixing agreement and comparison phrasing.',
 454: 'Both candidates use the ordinary locale term for a filesystem path and express nonexistence directly; the path placeholder stays quoted.',
 455: 'The caller warns about qBittorrent removing torrents once their share-ratio limit is reached. The candidates state that conditional behavior clearly and preserve the product name.',
 457: 'The caller compares the chosen edition ID with the selected book ID: “foreign” means it belongs to another book, not that it is in a foreign language. The revised wording removes that ambiguity and preserves both values.',
 458: 'The revised French adjective agrees with “jeton” and uses the concise standard error wording.',
 461: 'The revised forms make the download-state label idiomatic and grammatically agree in German, Arabic, and Vietnamese; the unknown state remains a value.',
 463: 'The candidates state the Transmission version requirement clearly, retain the 2.40 threshold, and preserve the product name.',
 464: 'The German compound adjective and hyphenation are corrected while the SSL setting remains recognizable.',
 466: '“Label” is the plugin name. The Korean sentence treats it as a named plugin and gives a complete inactive-state message.',
 467: 'The Indonesian candidate uses the application’s root-folder and quality-profile terms. The revision restores “selected,” which is part of the source meaning; both dynamic values remain unchanged.',
 468: 'The Spanish construction correctly expresses the inclusive lower and upper bounds for page size.',
 469: 'The candidates preserve qBittorrent and DHT and state that disabling DHT prevents resolving the magnet link.',
 470: 'The caller supplies an HTTP response status code. The candidates place that code in the response to a Calibre API request; Calibre and API remain explicit.',
 472: 'The candidates express failure to send the test message in a natural, complete UI sentence.',
 473: 'The revised forms retain the error detail and use locale-appropriate failure wording and punctuation.',
 475: 'The caller displays a troubleshooting warning. The candidates repair the malformed source-level NOT construction and preserve the exact external setting labels and option names, including their casing.',
 476: 'The candidates express the failed NZBGet connection directly and preserve the product name.',
 479: 'The candidates preserve Hardcover and API token as product/configuration terms and state why the integration is unavailable.',
 480: 'The candidates clearly say that the selected result lacks the author provider ID; they retain the technical identifier concept.',
 481: 'The candidates state that the folder cannot be accessed and that the permission check failed, with the path placeholder preserved.',
 482: 'These are compact connection-error fragments. The revisions use natural noun/adjective forms in the respective locales.',
 483: 'The candidates communicate successful deletion of the named series variant. The Korean revision avoids selecting an object particle based on the dynamic value’s final sound.',
 484: 'The caller provides the accepted provider prefixes. The candidates correctly describe {value0} as prefixes and retain the alphanumeric-ID requirement.',
 485: 'The caller passes a numeric edition ID. The Korean revision names the value as an ID and uses a fixed particle after the literal “ID,” avoiding a particle error on a dynamic value.',
 486: 'The candidates use the locale’s ordinary quality-profile/configuration term and retain the at-least-one requirement.',
 487: 'The candidates state the uniqueness requirement for every group and keep ID as the technical identifier.',
 489: 'The candidates clearly identify authentication failure and give the requested username/password check.',
 490: 'The candidates preserve the rule that a specified edition and its book must use the same provider, with natural grammar.',
 491: 'The candidates make the minimum-one selection requirement and ongoing monitoring purpose clear.',
 493: 'The candidates correctly describe the MQTT broker rejecting the connection and keep the dynamic rejection detail.',
 494: 'The pinned caller concerns the container’s remote Calibre GUI. The revised German message distinguishes it from the content server and gives the port-mapping instruction directly.',
 495: 'The candidates identify the import list as the source of the empty result and make the settings check clear.',
 496: 'The candidates preserve BookLore and turn the URL, credentials, and logs into clear troubleshooting directions.',
 497: 'The candidates state the conditional requirement for an API key when username and password are absent.',
 499: 'The candidates state that this is not a valid Calibre content server and preserve the exact official manual URL.',
}
HOLD_NOTES = {
 'es': 'Meaning is understandable, but “bin de reciclaje” is awkward; a more idiomatic standalone phrasing would use “carpeta de reciclaje”. No replacement is proposed without a caller to confirm the exact UI use.',
 'ja': 'The current sentence reads as “is the setting of the recycle-bin folder,” rather than identifying a configured recycle-bin path. A standalone wording could say it is the configured trash folder, but exact context remains unpinned.',
 'ko': 'The current “재활용 빈” phrasing is awkward for a recycle bin. A standalone correction could use “휴지통,” but the missing caller prevents confirming the message role.',
 'id': 'The current text mixes English “Path” and “bin” with Malay “kitar semula.” A standalone Indonesian wording could use “Jalur” and “tempat sampah,” but no exact caller pins this message.',
}

def sha(b): return hashlib.sha256(b).hexdigest()
def compact_json(x): return json.dumps(x, ensure_ascii=False, separators=(',',':')).encode()
def git(*args): return subprocess.check_output(['git','-C',str(W),*args])
def git_bytes(commit, path): return git('show',f'{commit}:{path}')
def blob(commit, path): return git('rev-parse',f'{commit}:{path}').decode().strip()
def jlines(path): return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
def write_json(path, x): path.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def write_jsonl(path, rows): path.write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in rows))
def placeholders(s): return sorted(set(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s)))
def markup(s):
    if re.fullmatch(r'<[^<>/]+>',s): return []
    return re.findall(r'</?[A-Za-z][^>]*>',s)
def check_sums(path):
    failures=[]
    for line in path.read_text().splitlines():
        if not line.strip(): continue
        expected,name=line.split(None,1); name=name.strip().lstrip('*')
        actual=sha((path.parent/name).read_bytes())
        if actual!=expected: failures.append({'file':name,'expected':expected,'actual':actual})
    return failures

# Verify the frozen primary input before independent review.
input_sum_failures=check_sums(P/'SHA256SUMS')
input_core_failures=check_sums(P/'INPUT-SHA256SUMS')
assert not input_sum_failures and not input_core_failures, json.dumps({'sha':input_sum_failures,'input':input_core_failures})
summary_primary=json.loads((P/'summary.json').read_text())
assert summary_primary['exactHead']==FROZEN and summary_primary['exactTree']==FROZEN_TREE
assert summary_primary['scope']['positions']==[450,499] and summary_primary['scope']['cells']==600

# Exact current PR state and commit/tree objects; the 70f correction only changes evidence docs.
pr_args=['gh','pr','view',str(PR),'--repo',REPO,'--json','state,isDraft,headRefOid,headRefName,baseRefName,url']
pr=json.loads(subprocess.check_output(pr_args,text=True))
assert pr['state']=='OPEN' and pr['isDraft'] is True and pr['headRefOid']==LIVE, json.dumps(pr)
assert git('rev-parse',f'{LIVE}^{{tree}}').decode().strip()==LIVE_TREE
assert git('rev-parse',f'{CHECKPOINT}^{{tree}}').decode().strip()==CHECKPOINT_TREE
latest_parent=git('show','-s','--format=%P',LIVE).decode().strip()
assert latest_parent==CHECKPOINT
changed_paths=git('diff-tree','--no-commit-id','--name-status','-r',LIVE).decode().splitlines()
assert all(x.split('\t',1)[-1].startswith('docs/pr-evidence/pr190-localization-2026-11-02/window-0400-0449/') for x in changed_paths), changed_paths

locale_paths={loc:f'src/NzbDrone.Core/Localization/Core/{fn}' for loc,fn in LOCALES.items()}
source_path='src/NzbDrone.Core/Localization/Core/en.json'
follow_path='docs/localization/source-followup-20261101.json'
source_bytes=git_bytes(LIVE,source_path); source_catalog=json.loads(source_bytes)
follow=json.loads(git_bytes(LIVE,follow_path)); ids=follow['currentMissingIds']
assert len(ids)==1210 and len(set(ids))==1210
source_list_sha=sha(compact_json(ids))
assert source_list_sha==summary_primary['sourceIdListSha256']
assert ids[450:500]==[x['sourceId'] for x in jlines(P/'source-slice.jsonl')]
assert ids[449]!=ids[450]
source_blobs={'live':blob(LIVE,source_path),'frozen':blob(FROZEN,source_path),'sourceSha256Live':sha(source_bytes),'sourceFollowupBlobLive':blob(LIVE,follow_path),'sourceFollowupSha256Live':sha(git_bytes(LIVE,follow_path))}
assert source_catalog==json.loads(git_bytes(FROZEN,source_path))
assert follow==json.loads(git_bytes(FROZEN,follow_path))
assert git_bytes(CHECKPOINT,source_path)==source_bytes
assert git_bytes(CHECKPOINT,follow_path)==git_bytes(LIVE,follow_path)

catalogs={}; catalog_info={}; checkpoint_catalog_blobs={}; live_catalog_blobs={}
for loc,path in locale_paths.items():
    data=git_bytes(LIVE,path); catalogs[loc]=json.loads(data)
    live_catalog_blobs[loc]=blob(LIVE,path); checkpoint_catalog_blobs[loc]=blob(CHECKPOINT,path)
    assert set(catalogs[loc])==set(source_catalog)
    # Correction commit 70f must leave all locale data exactly as at 48584.
    assert git_bytes(CHECKPOINT,path)==data, {'localeCatalogChangedAfterCheckpoint':loc}
    catalog_info[loc]={'path':path,'liveBlob':live_catalog_blobs[loc],'checkpointBlob':checkpoint_catalog_blobs[loc], 'fileSha256':sha(data),'bytes':len(data)}

inputs=jlines(P/'input-cells.jsonl')
reviews=jlines(P/'review-cells.jsonl')
candidates=jlines(P/'correction-candidates.jsonl')
callers=jlines(P/'caller-context.jsonl')
literal_rows=jlines(P/'protected-literal-integrity.jsonl')
prior_rows=jlines(P/'prior-context-dispositions.jsonl')
assert len(inputs)==600 and len(reviews)==600 and len(candidates)==168 and len(callers)==50 and len(prior_rows)==12
review_by={(x['sourceOrdinal'],x['locale']):x for x in reviews}
literal_by={(x['sourceOrdinal'],x['locale']):x for x in literal_rows}
candidate_by={(x['sourceOrdinal'],x['locale']):x for x in candidates}
proposal_keys={k for k,v in review_by.items() if v['disposition'] in ('propose-correction','propose-refinement')}
hold_keys={k for k,v in review_by.items() if v['disposition']=='hold'}
assert set(candidate_by)==proposal_keys|hold_keys and len(proposal_keys)==156 and len(hold_keys)==12

# Independently reattest all 600 current cells against the latest live tree. Catalog blobs may
# change from the frozen packet when preceding windows are applied; cell values must still match.
cell_reattests=[]; cell_mismatches=[]; locale_blob_changed=collections.Counter()
for row in inputs:
    n, sid, loc = row['sourceOrdinal'], row['sourceId'], row['locale']
    source_now=source_catalog.get(sid); target_now=catalogs[loc].get(sid)
    source_sha=sha(source_now.encode()) if isinstance(source_now,str) else None
    target_sha=sha(target_now.encode()) if isinstance(target_now,str) else None
    src_ok=(source_now==row['source'] and source_sha==row['sourceTextSha256'])
    tgt_ok=(target_now==row['target'] and target_sha==row['targetSha256'])
    target_blob_live=live_catalog_blobs[loc]
    frozen_target_blob=row['targetFileBlob']
    if target_blob_live!=frozen_target_blob: locale_blob_changed[loc]+=1
    rec={'sourceOrdinal':n,'sourceId':sid,'locale':loc,'sourceTextSha256Frozen':row['sourceTextSha256'],'sourceTextSha256Live':source_sha,'currentTargetSha256Frozen':row['targetSha256'],'currentTargetSha256Live':target_sha,'sourceValueMatchesFrozen':src_ok,'targetValueMatchesFrozen':tgt_ok,'targetCatalogBlobFrozen':frozen_target_blob,'targetCatalogBlobLive':target_blob_live,'catalogBlobChangedSinceFrozen':target_blob_live!=frozen_target_blob}
    cell_reattests.append(rec)
    if not (src_ok and tgt_ok): cell_mismatches.append(rec)
assert not cell_mismatches, json.dumps(cell_mismatches[:10],ensure_ascii=False)

# Reattest each pinned caller reference by exact file blob, SHA-256, line number and line hash.
caller_reattests=[]; caller_mismatches=[]; unique_caller_files=set()
for row in callers:
    sid=row['sourceId']; refs=row['callerRefs']
    for ref in refs:
        path=ref['file']; unique_caller_files.add(path)
        data=git_bytes(LIVE,path); lines=data.decode('utf-8').splitlines(); line=ref['currentLine']
        line_now=lines[line-1] if 1<=line<=len(lines) else None
        ok=(blob(LIVE,path)==ref['currentFileBlob'] and sha(data)==ref['currentFileSha256'] and line_now==ref['currentLineText'] and sha(line_now.encode())==ref['currentLineSha256'])
        info={'sourceOrdinal':row['sourceOrdinal'],'sourceId':sid,'file':path,'line':line,'kind':ref['kind'],'lineMatchMethod':ref['lineMatchMethod'],'fileBlobFrozen':ref['currentFileBlob'],'fileBlobLive':blob(LIVE,path),'currentLineSha256Frozen':ref['currentLineSha256'],'currentLineSha256Live':sha(line_now.encode()) if line_now is not None else None,'matchesFrozen':ok}
        caller_reattests.append(info)
        if not ok: caller_mismatches.append(info)
assert not caller_mismatches, json.dumps(caller_mismatches[:5],ensure_ascii=False)

# Independent assessment of every correction/refinement and every existing hold.
reviewed=[]; disposition_counts=collections.Counter(); revision_rows=[]
for key in sorted(set(candidate_by)|{k for k,v in review_by.items() if v['disposition']=='hold'}):
    base=review_by[key]; n,loc=key; candidate=candidate_by.get(key) if base['disposition'] in ('propose-correction','propose-refinement') else None
    final_target=candidate['recommendedTarget'] if candidate else None
    final_disposition=base['disposition']
    verdict='retain-primary-candidate' if candidate else 'retain-hold'
    reason=REASONS.get(n)
    if candidate:
        if key in REVISIONS:
            final_target=REVISIONS[key]; verdict='revise-primary-candidate'
            if key==(457,'zh-Hans'): reason='In the pinned validator, this ID is “foreign” because it belongs to another selected book; “外文版” implies a foreign-language edition. Use a neutral “selected edition” so the relationship is precise.'
            elif key==(457,'hi'): reason='The caller uses “foreign” for an edition belonging to another selected book, not a foreign-language edition. Remove “विदेशी” and state the book-membership mismatch directly.'
            elif key==(467,'id'): reason='The primary proposal omitted “selected.” Keep the source’s selected-root-folder detail while improving “default” to “bawaan.”'
            elif key==(483,'ko'): reason='The value is arbitrary display text. The primary particle “을” may be wrong depending on the value’s final sound; recast the sentence so the particle is fixed.'
            elif key==(485,'ko'): reason='The caller passes a numeric edition ID. The primary “을” attaches to the dynamic value and can be wrong; identify the value as ID and attach “를” after the fixed literal.'
        assert reason
        assert sha(final_target.encode())==sha(final_target.encode())
    else:
        assert n==498 and not base['callerRefs']
        verdict='retain-hold'
        reason='No direct caller or exact UI role is pinned for this sentence. The source can be read standalone as identifying a configured recycle-bin folder, but whether it labels a path, warns about a configured folder, or appears as supporting validation text is unknown. Retain the hold rather than invent caller-specific wording.'
    source_ph=placeholders(base['source']); current_ph=placeholders(base['currentTarget'])
    final_ph=placeholders(final_target) if final_target is not None else None
    source_markup=markup(base['source']); current_markup=markup(base['currentTarget'])
    final_markup=markup(final_target) if final_target is not None else None
    lit=literal_by[key]
    final_literal_mismatches=[]
    if final_target is not None:
        for check in lit.get('checks',[]):
            literal=check['literal']
            if check.get('presentInSource') and literal not in final_target:
                final_literal_mismatches.append(literal)
    parity={'sourcePlaceholders':source_ph,'currentTargetPlaceholders':current_ph,'finalTargetPlaceholders':final_ph,'placeholderParity':source_ph==current_ph and (final_ph is None or source_ph==final_ph),'sourceMarkup':source_markup,'currentMarkup':current_markup,'finalMarkup':final_markup,'markupParity':source_markup==current_markup and (final_markup is None or source_markup==final_markup),'protectedLiteralChecks':lit.get('checks',[]),'finalProtectedLiteralMismatches':final_literal_mismatches}
    assert parity['placeholderParity'] and parity['markupParity'] and not final_literal_mismatches, (key,parity)
    refs=[{'file':x['file'],'line':x['currentLine'],'kind':x['kind'],'matchMethod':x['lineMatchMethod'],'matchedSourceId':x.get('matchedSourceId'),'matchedSourceText':x.get('matchedSourceText')} for x in base['callerRefs']]
    rec={
      'sourceOrdinal':n,'sourceId':base['sourceId'],'locale':loc,'source':base['source'],'sourceTextSha256':base['sourceTextSha256'],
      'currentTarget':base['currentTarget'],'currentTargetSha256':base['currentTargetSha256'],'primaryDisposition':base['disposition'],
      'primaryTarget':candidate['recommendedTarget'] if candidate else None,'primaryTargetSha256':candidate['recommendedTargetSha256'] if candidate else None,
      'crossReviewVerdict':verdict,'finalDisposition':final_disposition,'finalTarget':final_target,'finalTargetSha256':sha(final_target.encode()) if final_target is not None else None,
      'confidence':'moderate' if candidate else 'high for retaining the hold; locale phrasing remains a native-review question',
      'independentRationale':reason,'callerRefs':refs,'callerContextSha256':base['callerContextSha256'],'exactPlaceholdersMarkupLiterals':parity,
      'callerGap':not bool(base['callerRefs']),'nativeSpeakerApproval':False,
      'standaloneNote':HOLD_NOTES.get(loc) if not candidate else None
    }
    reviewed.append(rec)
    disposition_counts[verdict]+=1
    if candidate and key in REVISIONS: revision_rows.append(rec)
assert len(reviewed)==168 and len(proposal_keys)==156 and len(hold_keys)==12
assert disposition_counts['retain-primary-candidate']==151 and disposition_counts['revise-primary-candidate']==5 and disposition_counts['retain-hold']==12

# Reattest source and target cells for all prior W449 boundary rows against the live PR.
prior_cross_rows={}
for row in jlines(PREV/'cross-review-cells.jsonl'):
    if row.get('sourceOrdinal')==449: prior_cross_rows[row['locale']]=row
assert set(prior_cross_rows)==set(LOCALES)
prior_review=jlines(P/'prior-context-dispositions.jsonl')
assert len(prior_review)==12 and {r['sourceId'] for r in prior_review}=={ids[449]}
prior_id=ids[449]; prior_source=source_catalog[prior_id]
prior_source_sha=sha(prior_source.encode())
assert prior_source==prior_review[0]['source']
prior_caller_refs=prior_review[0]['currentCallerRefs']
prior_caller_reattests=[]; prior_caller_mismatches=[]
for ref in prior_caller_refs:
    path=ref['file']; data=git_bytes(LIVE,path); lines=data.decode('utf-8').splitlines(); line=ref['currentLine']
    line_now=lines[line-1] if 1<=line<=len(lines) else None
    ok=(blob(LIVE,path)==ref['currentFileBlob'] and sha(data)==ref['currentFileSha256'] and line_now==ref['currentLineText'] and sha(line_now.encode())==ref['currentLineSha256'])
    result={'sourceId':prior_id,'file':path,'line':line,'fileBlobFrozen':ref['currentFileBlob'],'fileBlobLive':blob(LIVE,path),'currentLineSha256Frozen':ref['currentLineSha256'],'currentLineSha256Live':sha(line_now.encode()) if line_now is not None else None,'matchesFrozen':ok}
    prior_caller_reattests.append(result)
    if not ok: prior_caller_mismatches.append(result)
assert not prior_caller_mismatches
boundary=[]; boundary_mismatches=[]; changed_from_primary=0
for loc in LOCALES:
    old=next(x for x in prior_review if x['locale']==loc)
    cross=prior_cross_rows[loc]
    current=catalogs[loc].get(prior_id); current_sha=sha(current.encode()) if isinstance(current,str) else None
    expected_final=cross['finalTarget']; expected_final_sha=cross['finalTargetSha256']
    prior_current_match=(current==old['priorPrimaryCurrentTarget'] and current_sha==old['priorPrimaryCurrentTargetSha256'])
    cross_final_match=(current==expected_final and current_sha==expected_final_sha)
    item={'sourceOrdinal':449,'sourceId':prior_id,'locale':loc,'sourceTextSha256':prior_source_sha,'sourceTextMatchesFrozen':prior_source_sha==old['sourceTextSha256'],'priorPrimaryCurrentTargetSha256':old['priorPrimaryCurrentTargetSha256'],'liveTargetSha256':current_sha,'priorPrimaryCurrentTargetStillLive':prior_current_match,'priorCrossReviewFinalTarget':expected_final,'priorCrossReviewFinalTargetSha256':expected_final_sha,'liveTargetMatchesPriorCrossReviewFinal':cross_final_match,'callerContextSha256':old['callerContextSha256'],'callerRefCount':len(old['currentCallerRefs'])}
    boundary.append(item)
    if not (item['sourceTextMatchesFrozen'] and cross_final_match): boundary_mismatches.append(item)
    if not prior_current_match: changed_from_primary+=1
assert not boundary_mismatches, json.dumps(boundary_mismatches,ensure_ascii=False)
assert len(prior_caller_reattests)==2

# Verify the previous boundary is ordinal 449 and this window starts at 450, and that caller pins remain valid.
assert len(set(x['sourceId'] for x in jlines(P/'source-slice.jsonl')))==50
assert len(set(x['sourceId'] for x in jlines(PREV/'cross-review-cells.jsonl') if x.get('sourceOrdinal')==449))==1
assert summary_primary['priorDispositionBoundary']['priorSourceIdWindowOverlap']==0

write_jsonl(O/'cross-review-candidates-and-holds.jsonl',reviewed)
write_jsonl(O/'live-cell-hash-reattestation.jsonl',cell_reattests)
write_jsonl(O/'caller-reattestation.jsonl',caller_reattests)
write_jsonl(O/'W449-boundary-reattestation.jsonl',boundary)
write_json(O/'live-pr-state.json',{'repository':REPO,'pullRequest':PR,'state':pr['state'],'isDraft':pr['isDraft'],'headRefName':pr['headRefName'],'baseRefName':pr['baseRefName'],'head':LIVE,'tree':LIVE_TREE,'parent':latest_parent,'checkpoint48584':{'head':CHECKPOINT,'tree':CHECKPOINT_TREE},'latestCommitChangedPaths':changed_paths,'all12LocaleCatalogsByteIdenticalTo48584':True,'sourceCatalogByteIdenticalToFrozenPrimaryAndCheckpoint':source_bytes==git_bytes(FROZEN,source_path)==git_bytes(CHECKPOINT,source_path),'sourceFollowupByteIdenticalToFrozenPrimaryAndCheckpoint':git_bytes(LIVE,follow_path)==git_bytes(FROZEN,follow_path)==git_bytes(CHECKPOINT,follow_path)})

summary={
 'repository':REPO,'pullRequest':PR,'primaryPacketHead':FROZEN,'primaryPacketTree':FROZEN_TREE,
 'liveHead':LIVE,'liveTree':LIVE_TREE,'checkpoint48584Tree':CHECKPOINT_TREE,'prState':'OPEN','draft':True,
 'scope':{'sourceOrdinals':[450,499],'sourceIds':50,'localeCells':600,'proposalsIndependentlyReviewed':156,'holdsIndependentlyReviewed':12},
 'crossReview':{'acceptedPrimaryCandidates':disposition_counts['retain-primary-candidate'],'revisedPrimaryCandidates':disposition_counts['revise-primary-candidate'],'retainedHolds':disposition_counts['retain-hold'],'revisions':[{'sourceOrdinal':r['sourceOrdinal'],'sourceId':r['sourceId'],'locale':r['locale'],'finalTarget':r['finalTarget'],'rationale':r['independentRationale']} for r in revision_rows]},
 'technicalChecks':{'all600SourceCurrentTargetCellsReattested':len(cell_reattests),'cellValueMismatches':len(cell_mismatches),'proposalSourceAndCurrentTargetHashesReattested':len(proposal_keys),'proposalAndHoldSourceCurrentHashesReattested':len(candidate_by),'proposalMismatchCount':sum(not next(x for x in cell_reattests if x['sourceOrdinal']==r['sourceOrdinal'] and x['locale']==r['locale'])['sourceValueMatchesFrozen'] or not next(x for x in cell_reattests if x['sourceOrdinal']==r['sourceOrdinal'] and x['locale']==r['locale'])['targetValueMatchesFrozen'] for r in candidates if (r['sourceOrdinal'],r['locale']) in proposal_keys),'catalogBlobDifferencesDueToEarlierWindows':dict(locale_blob_changed),'sourceIdListSha256':source_list_sha,'callerReferencesReattested':len(caller_reattests),'uniqueCallerFiles':len(unique_caller_files),'callerMismatches':len(caller_mismatches),'priorW449SourceCellsReattested':len(boundary),'W449TargetsMatchingCrossReviewFinal':sum(x['liveTargetMatchesPriorCrossReviewFinal'] for x in boundary),'W449CellsChangedFromPrimarySnapshot':changed_from_primary,'W449CallerRefsReattested':len(prior_caller_reattests),'W449CallerMismatches':len(prior_caller_mismatches),'placeholderOrMarkupOrProtectedLiteralMismatches':0},
 'holds':{'sourceOrdinal':498,'sourceId':ids[498],'localeCount':12,'callerRefs':0,'reason':'No exact direct caller; preserve uncertainty.'},
 'caveats':{'nativeSpeakerApproval':False,'noRepoOrPrEdits':True,'noTestsBuildsScansCiBrowserOrWorkflowEdits':True,'noReleaseOrTag':True},
 'inputPacketChecksumFailures':{'SHA256SUMS':input_sum_failures,'INPUT-SHA256SUMS':input_core_failures}
}
write_json(O/'summary.json',summary)

(O/'README.md').write_text(f'''# ChaptarrNG PR #190 W450–499 independent cross-review

- Cross-reviewed the 156 correction/refinement proposals and all 12 holds in the frozen primary packet at `{FROZEN}` / tree `{FROZEN_TREE}`.
- Live PR was re-queried as OPEN/DRAFT at `{LIVE}` / tree `{LIVE_TREE}`. This is a documentation-only child of `{CHECKPOINT}` / tree `{CHECKPOINT_TREE}`; all 12 locale catalog files and the English source/follow-up inputs are byte-identical to the checkpoint.
- Proposal dispositions: {disposition_counts['retain-primary-candidate']} primary targets retained, {disposition_counts['revise-primary-candidate']} revised, {disposition_counts['retain-hold']} holds retained. The five revised targets and rationales are in `cross-review-candidates-and-holds.jsonl` and `summary.json`.
- Independently reattested all 600 W450–499 source/current-target cells at the latest live head, all {len(caller_reattests)} pinned production caller references, and the 12 W449 boundary cells. The W449 caller refs were also reattested; all W449 live targets match the prior window’s cross-review final targets. Earlier-window catalog blob changes are recorded separately from unchanged W450–499 cell values.
- Placeholder, markup, and protected-literal parity passed for every proposed target and all held/current cells. The W498 message has no direct caller; standalone comments do not replace the hold.
- This is an independent model review, not native-speaker approval. No repository or PR files were changed. No tests, builds, scans, CI, browser work, workflow edits, releases, or tags were performed.

## Packet files

- `cross-review-candidates-and-holds.jsonl`: exact primary/current/final text, independent disposition and rationale, caller references, and structural/literal checks for all 156 proposal cells and 12 holds.
- `live-cell-hash-reattestation.jsonl`: all 600 W450–499 source/current-target text hashes at the live head.
- `caller-reattestation.jsonl`: all pinned W450–499 caller refs at the live head.
- `W449-boundary-reattestation.jsonl`: prior boundary source/locale values compared with the previously cross-reviewed final values.
- `live-pr-state.json`: exact PR/checkpoint state and documentation-only commit changes.
- `build_crossreview.py`: reproducible read-only packet builder.
- `SHA256SUMS`: packet checksums.
''')

# Final exact-head check immediately before sealing.
final_pr=json.loads(subprocess.check_output(pr_args,text=True))
final_tree=git('rev-parse',f'{LIVE}^{{tree}}').decode().strip()
assert final_pr['headRefOid']==LIVE and final_pr['state']=='OPEN' and final_pr['isDraft'] is True and final_tree==LIVE_TREE
write_json(O/'final-reattestation.json',{
 'repository':REPO,'pullRequest':PR,'livePullRequest':final_pr,'exactHead':LIVE,'exactTree':LIVE_TREE,
 'matchesExpectedLiveHead':True,'sourceIdListSha256':source_list_sha,'all600CellMismatches':cell_mismatches,
 'callerRefCount':len(caller_reattests),'callerMismatches':caller_mismatches,'w449SourceLocaleRows':len(boundary),
 'w449BoundaryMismatches':boundary_mismatches,'w449CallerRefCount':len(prior_caller_reattests),'w449CallerMismatches':prior_caller_mismatches,
 'primaryInputChecksumsVerified':True,'checks':'pass','recheckedAtUtc':subprocess.check_output(['date','-u','+%Y-%m-%dT%H:%M:%SZ'],text=True).strip()
})
# Checksums include all files except the checksum list itself.
files=sorted(x for x in O.iterdir() if x.is_file() and x.name!='SHA256SUMS')
(O/'SHA256SUMS').write_text(''.join(f'{sha(x.read_bytes())}  {x.name}\n' for x in files))
print(json.dumps({'output':str(O),'summary':summary,'packetFiles':len(files)+1},ensure_ascii=False,indent=2))
