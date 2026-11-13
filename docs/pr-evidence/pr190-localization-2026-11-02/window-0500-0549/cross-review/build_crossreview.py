import collections, hashlib, json, pathlib, re, subprocess

REPO='snapetech-org/chaptarrng'; PR=190
W=pathlib.Path('/mnt/disks/scratch/task-worktrees/localization-20261102/chaptarrng-pr190-audit')
P=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0500-0549-primary-20261102')
PREV=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0450-0499-primary-20261102')
PREVC=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0450-0499-crossreview-20261102')
O=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0500-0549-crossreview-20261102')
FROZEN='2eb0ae6eb15ebc366eea44dd969265c0f6366445'; FROZEN_TREE='1340ba7d0642217aa81e3789e908931bd6fa74f1'
CHECKPOINT='70f5ad2c2dc8222d8f35e09ba81ffa12acfff856'; CHECKPOINT_TREE='9bd50b4f149f69f7cd5b78937b45fe1745e6c695'
LIVE='2625ad8bda30c7070bcc84ec8e4b31906a3d2288'; LIVE_TREE='128cbbef8788d11f0978529cf31eeab3f039b680'
LOCALES={'es':'es.json','zh-Hans':'zh_CN.json','hi':'hi.json','de':'de.json','ja':'ja.json','fr':'fr.json','pt-BR':'pt_BR.json','ar':'ar.json','ko':'ko.json','zh-Hant':'zh_TW.json','vi':'vi.json','id':'id.json'}

REVISIONS={
 (506,'hi'):'हर लेखक की ID अद्वितीय होनी चाहिए।',
 (511,'fr'):'Aucun jeton d’API Hardcover n’est configuré (ajoutez-en un à cette liste d’importation ou dans les paramètres).',
 (511,'vi'):'Chưa cấu hình token API của Hardcover (hãy thêm token vào danh sách nhập này hoặc phần Cài đặt).',
 (513,'ko'):'프록시를 통해 {value0}에 성공적으로 연결했습니다. 응답 시간: {value1}ms.',
 (520,'ar'):'لم تعد معاملات البرامج النصية المخصصة مدعومة.',
 (536,'hi'):'{value0} से कम होने पर H&R होता है।',
 (541,'de'):'Für diesen Autor ist kein Hörbuch-Metadatenprofil eingerichtet (Hörbücher sind deaktiviert). Richten Sie ein Hörbuch-Metadatenprofil ein, um Hörbücher hinzuzufügen.',
 (541,'ar'):'لم يتم إعداد ملف تعريف البيانات الوصفية للكتب الصوتية لهذا المؤلف (الكتب الصوتية معطّلة). اضبط ملف تعريف البيانات الوصفية للكتب الصوتية لإضافة كتب صوتية.',
 (544,'ko'):'암호 문구는 {value0}자 이상이어야 하며 UTF-8 기준 최대 {value1}바이트까지 허용됩니다.',
}
NOOPS={(536,'zh-Hans'),(536,'zh-Hant')}
REASONS={
 500:'The caller compares the protocol returned by the metadata-server ping with the expected handshake protocol. The candidates fix German agreement and make actual versus expected protocol values clear.',
 501:'The failure is an aborted test and {value0} carries the exception detail. The German proposal fixes the genitive and uses idiomatic wording.',
 502:'The callers report that the uTorrent connection could not be established. The candidates are natural failure statements and preserve the product name.',
 504:'The caller returns a generic error from Deluge. “त्रुटि” is the usual technical term for an error; the recommendation corrects the awkward synonym.',
 505:'The caller rejects an empty token key in a naming-pattern operation. The Japanese proposal gives a clear, grammatical prohibition.',
 506:'The validation compares author IDs for uniqueness. The candidates express distinct IDs, with the Hindi wording revised to avoid an awkward pluralized English acronym.',
 509:'The Hardcover integration rejects its API key. The candidates make the error grammatical and preserve the service and API-key terms.',
 510:'The caller parses an external provider series ID with a provider prefix. The Arabic proposal describes an external series identifier and improves the phrase order.',
 511:'The caller says a Hardcover API token may be supplied on this import list or in Settings. The proposals turn the source parenthetical into a usable instruction.',
 512:'The HTTP import-list caller appends the exception text as {value0}. The candidates clearly say the list could not be reached and keep the detail separate.',
 513:'The caller reports a successful connection through the configured proxy URL, then response time. The candidates retain both values and the time unit.',
 516:'The Vuze caller requires version 5.0.0.0 or later with the Vuze Web Remote plugin. The recommendations preserve exact product/plugin names and clarify the instruction.',
 517:'The caller gives a proxy-test timeout. The Japanese candidate uses the standard timeout wording.',
 518:'The caller identifies a SABnzbd development version and assumes version 3.0.0 or later. The proposals correct product capitalization and keep the version condition.',
 519:'The caller rejects editing a root-folder path. The proposals use standard localized root-folder wording and retain the restriction.',
 520:'The setting concerns command-line arguments to custom scripts. French and Indonesian improve grammar; the Arabic revision replaces an ambiguous word for “arguments” with the technical term معاملات.',
 522:'The caller could not retrieve data from the Hardcover import-list library. The proposals state that failure naturally and preserve Hardcover.',
 523:'The API returns a 502 when downloading the user-selected photo fails. The candidates use complete, idiomatic failure messages.',
 524:'Multiple import-list callers require a configured root folder. The candidates express a required folder rather than a literal “root folder is required” fragment.',
 525:'The caller rejects NZBGet versions below 12.0. The candidates state the lower bound clearly and preserve the source spelling of the client name and version.',
 527:'The two Download Station callers provide the supported minimum and maximum versions. The candidates explain the unsupported API version and keep both range placeholders in order.',
 529:'The bookshelf endpoint requires at least one book ID for specific-book monitoring. The proposals state that requirement naturally across locales.',
 530:'The caller validation concerns syncing an author’s monitored state across audiobook and ebook formats and requires both root folders. The proposals make the state and both required folders explicit.',
 531:'The AudioBookShelf notification caller explains that API-key creation requires an admin and offers manual key creation as an alternative. The Arabic proposal preserves both options and the product name.',
 532:'The config validation rejects an invalid ebook conversion target format. The candidates produce direct, grammatical error sentences.',
 533:'Newznab and Torznab callers reject indexers that lack required search parameters. The revisions use the locale’s indexer term while preserving the exact technical meaning.',
 535:'The series lookup endpoint rejects a non-numeric Hardcover series ID. The Arabic proposal improves ordering while keeping Hardcover and the familiar ID marker.',
 536:'The seed-criteria setting describes the consequence of a ratio below {value0}. The candidates retain the exact H&R token; two proposals exactly duplicate the current text and are no-ops, and the Hindi revision restores the source’s direct consequence.',
 537:'The caller reports the boolean result of the metadata-server ping. The candidates keep the exact `ok=true` token and state that the ping did not return it.',
 538:'The BookOrbit caller reports rejected password login and asks users to inspect credentials and password-login policy. The proposals translate both the failure and instructions naturally.',
 540:'The shared URL validator reports an invalid URL value. The candidates keep the URL term and dynamic value; the colon clearly separates the value in these locale formats.',
 541:'The AddBookService message explains a missing audiobook metadata profile and the disabled-audiobooks state. The revisions localize German audiobook terminology and clarify in Arabic that this is a metadata profile, while preserving the instruction.',
 542:'The folder-chmod validator requires a valid octal representation of Unix permissions. The candidates make that technical requirement clear.',
 543:'The Download Station callers report that a shared folder does not exist. The proposals use natural locale grammar and, in Traditional Chinese, the common term 共用資料夾.',
 544:'The backup caller requires a passphrase with a minimum character count and maximum UTF-8 byte length. The proposals retain both numeric placeholders and UTF-8; the Korean revision removes redundant minimum/at-least wording.',
 546:'The queue endpoint reports that this item has no active conversion. The proposals identify the queue item and state the absence of an active conversion.',
 547:'The root-folder validator requires a metadata profile of the requested media type. The proposals retain {value0} and use clear profile terminology.',
 548:'The qBittorrent validator requires the username field to be empty when an API key is used. The candidates state the field constraint clearly.',
 549:'The quality-items validator prohibits duplicate quality entries. The proposals use a natural plural construction and preserve the one-use-only rule.',
}
REVISION_REASONS={
 (506,'hi'):"The caller validates multiple author IDs. The proposal mixes English pluralization into Hindi; this says that each author's ID must be unique.",
 (511,'fr'):'Use the idiomatic French construction “jeton d’API Hardcover” and translate the action as adding a token to this import list or Settings.',
 (511,'vi'):'Clarify that it is the Hardcover API token, not a generic token, and keep the two configuration locations explicit.',
 (513,'ko'):'The primary wording can read as a proxy connection followed by a value. This explicitly says the connection to {value0} succeeded through the proxy.',
 (520,'ar'):'The primary “الوسائط” can mean media. In this scripting-settings caller, the source means script arguments; use “معاملات”.',
 (536,'hi'):'The source states that falling below the threshold leads to H&R. “हो सकता है” weakens that to possibility; use a direct consequence.',
 (541,'de'):'The primary leaves “Audiobook(s)” in English throughout. “Hörbuch” is the natural German term here, including in the metadata-profile setting.',
 (541,'ar'):'The primary wording can be read as setting up a metadata file, while the caller means configuring a metadata profile. State the profile explicitly in both sentences.',
 (544,'ko'):'The primary repeats the minimum requirement with “최소 ... 이상.” This uses one minimum construction and states the maximum UTF-8 byte limit separately.',
}


def sha(b): return hashlib.sha256(b).hexdigest()
def jbytes(x): return json.dumps(x,ensure_ascii=False,separators=(',',':')).encode()
def git(*args): return subprocess.check_output(['git','-C',str(W),*args])
def show(commit,path): return git('show',f'{commit}:{path}')
def blob(commit,path): return git('rev-parse',f'{commit}:{path}').decode().strip()
def rows(path): return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]
def write_json(path,x): path.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def write_jsonl(path,xs): path.write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in xs))
def placeholders(s): return sorted(set(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s)))
def markup(s):
    if re.fullmatch(r'<[^<>/]+>',s): return []
    return re.findall(r'</?[A-Za-z][^>]*>',s)
def verify_checksums(path):
    bad=[]
    for line in path.read_text().splitlines():
        if not line.strip(): continue
        expected,name=line.split(None,1); name=name.strip().lstrip('*')
        actual=sha((path.parent/name).read_bytes())
        if actual!=expected: bad.append({'path':name,'expected':expected,'actual':actual})
    return bad

# Confirm input and earlier-window evidence integrity.
packet_sum_bad=verify_checksums(P/'SHA256SUMS'); packet_inputs_bad=verify_checksums(P/'INPUT-SHA256SUMS')
prev_sum_bad=verify_checksums(PREVC/'SHA256SUMS')
assert not packet_sum_bad and not packet_inputs_bad and not prev_sum_bad
prim_summary=json.loads((P/'summary.json').read_text())
assert prim_summary['exactHead']==FROZEN and prim_summary['exactTree']==FROZEN_TREE
assert prim_summary['scope']['positions']==[500,549] and prim_summary['scope']['cells']==600
prior_cross_summary=json.loads((PREVC/'summary.json').read_text())
prior_reattest=json.loads((PREVC/'final-reattestation.json').read_text())
assert prior_reattest['exactHead']==CHECKPOINT and prior_reattest['checks']=='pass'

# Exact live PR query and commit/tree verification.
pr_args=['gh','pr','view',str(PR),'--repo',REPO,'--json','state,isDraft,headRefOid,headRefName,baseRefName,url']
pr=json.loads(subprocess.check_output(pr_args,text=True))
assert pr['state']=='OPEN' and pr['isDraft'] is True and pr['headRefOid']==LIVE, json.dumps(pr)
assert git('rev-parse',f'{FROZEN}^{{tree}}').decode().strip()==FROZEN_TREE
assert git('rev-parse',f'{CHECKPOINT}^{{tree}}').decode().strip()==CHECKPOINT_TREE
assert git('rev-parse',f'{LIVE}^{{tree}}').decode().strip()==LIVE_TREE

src_path='src/NzbDrone.Core/Localization/Core/en.json'
follow_path='docs/localization/source-followup-20261101.json'
locale_paths={loc:f'src/NzbDrone.Core/Localization/Core/{fn}' for loc,fn in LOCALES.items()}
source_bytes=show(LIVE,src_path); source_catalog=json.loads(source_bytes)
follow_bytes=show(LIVE,follow_path); follow=json.loads(follow_bytes); ids=follow['currentMissingIds']
assert len(ids)==1210 and len(set(ids))==1210
source_list_sha=sha(jbytes(ids)); assert source_list_sha==prim_summary['sourceIdListSha256']
assert source_catalog==json.loads(show(FROZEN,src_path))
assert follow==json.loads(show(FROZEN,follow_path))
assert show(CHECKPOINT,src_path)==source_bytes and show(CHECKPOINT,follow_path)==follow_bytes
assert ids[500:550]==[x['sourceId'] for x in rows(P/'source-slice.jsonl')]
assert ids[499]!=ids[500]

catalogs={}; locale_file_info={}
for loc,path in locale_paths.items():
    data=show(LIVE,path); catalogs[loc]=json.loads(data)
    assert set(catalogs[loc])==set(source_catalog)
    locale_file_info[loc]={'path':path,'blobFrozen':blob(FROZEN,path),'blobLive':blob(LIVE,path),'sha256Live':sha(data),'bytesLive':len(data),'fileBlobChanged':blob(FROZEN,path)!=blob(LIVE,path)}

inputs=rows(P/'input-cells.jsonl'); review_rows=rows(P/'review-cells.jsonl'); candidate_rows=rows(P/'correction-candidates.jsonl')
caller_rows=rows(P/'caller-context.jsonl'); literal_rows=rows(P/'protected-literal-integrity.jsonl'); prior_rows=rows(P/'prior-context-dispositions.jsonl')
assert len(inputs)==600 and len(review_rows)==600 and len(candidate_rows)==174 and len(caller_rows)==50 and len(prior_rows)==12
review_by={(x['sourceOrdinal'],x['locale']):x for x in review_rows}
input_by={(x['sourceOrdinal'],x['locale']):x for x in inputs}
lit_by={(x['sourceOrdinal'],x['locale']):x for x in literal_rows}
cand_by={(x['sourceOrdinal'],x['locale']):x for x in candidate_rows}
assert len(cand_by)==174 and not [x for x in candidate_rows if x['disposition']=='hold']
assert set(cand_by)=={k for k,v in review_by.items() if v['disposition'] in ('propose-correction','propose-refinement')}
assert all(key in cand_by for key in REVISIONS) and NOOPS.issubset(cand_by)
primary_literal_mismatch_keys={(r['sourceOrdinal'],r['locale']) for r in prim_summary['protectedLiterals']['currentMismatchCells']}
assert primary_literal_mismatch_keys.issubset(cand_by)
candidate_hash_mismatches=[]
for key,cand in cand_by.items():
    cell=input_by[key]
    if cand['sourceTextSha256']!=cell['sourceTextSha256'] or cand['currentTargetSha256']!=cell['targetSha256'] or sha(cand['recommendedTarget'].encode())!=cand['recommendedTargetSha256']:
        candidate_hash_mismatches.append({'sourceOrdinal':key[0],'locale':key[1]})
assert not candidate_hash_mismatches

# Reattest exact source and current target values/hashes for all 600 cells at live PR head.
cell_attest=[]; cell_mismatch=[]; changed_catalog_cell_records=collections.Counter()
for x in inputs:
    n,sid,loc=x['sourceOrdinal'],x['sourceId'],x['locale']
    src=source_catalog.get(sid); tgt=catalogs[loc].get(sid)
    src_hash=sha(src.encode()) if isinstance(src,str) else None
    tgt_hash=sha(tgt.encode()) if isinstance(tgt,str) else None
    ok_src=(src==x['source'] and src_hash==x['sourceTextSha256'])
    ok_tgt=(tgt==x['target'] and tgt_hash==x['targetSha256'])
    target_blob=locale_file_info[loc]['blobLive']
    if target_blob!=x['targetFileBlob']: changed_catalog_cell_records[loc]+=1
    row={'sourceOrdinal':n,'sourceId':sid,'locale':loc,'sourceTextSha256Frozen':x['sourceTextSha256'],'sourceTextSha256Live':src_hash,'currentTargetSha256Frozen':x['targetSha256'],'currentTargetSha256Live':tgt_hash,'sourceValueMatchesFrozen':ok_src,'targetValueMatchesFrozen':ok_tgt,'targetCatalogBlobFrozen':x['targetFileBlob'],'targetCatalogBlobLive':target_blob,'targetCatalogBlobChanged':target_blob!=x['targetFileBlob']}
    cell_attest.append(row)
    if not (ok_src and ok_tgt): cell_mismatch.append(row)
assert not cell_mismatch, json.dumps(cell_mismatch[:5],ensure_ascii=False)

# Reattest every production source/caller pin from the primary packet against live source.
caller_attest=[]; caller_mismatch=[]; caller_files=set()
for source_row in caller_rows:
    for ref in source_row['callerRefs']:
        path=ref['file']; caller_files.add(path); data=show(LIVE,path); lines=data.decode('utf-8').splitlines(); line=ref['currentLine']
        current=lines[line-1] if 1<=line<=len(lines) else None
        file_blob=blob(LIVE,path); file_hash=sha(data)
        ok=(file_blob==ref['currentFileBlob'] and file_hash==ref['currentFileSha256'] and current==ref['currentLineText'] and current is not None and sha(current.encode())==ref['currentLineSha256'])
        info={'sourceOrdinal':source_row['sourceOrdinal'],'sourceId':source_row['sourceId'],'file':path,'line':line,'kind':ref['kind'],'matchMethod':ref['lineMatchMethod'],'fileBlobFrozen':ref['currentFileBlob'],'fileBlobLive':file_blob,'currentLineSha256Frozen':ref['currentLineSha256'],'currentLineSha256Live':sha(current.encode()) if current is not None else None,'matchesFrozen':ok}
        caller_attest.append(info)
        if not ok: caller_mismatch.append(info)
assert len(caller_attest)==prim_summary['callerEvidence']['currentCallerRefs'] and not caller_mismatch

# Independently review every proposed cell. No-op recommendations become accept-current.
ledger=[]; candidate_dispositions=collections.Counter(); final_rows=[]; revisions=[]; noops=[]
for key in sorted(cand_by):
    cand=cand_by[key]; base=review_by[key]; n,loc=key
    final_target=cand['recommendedTarget']; final_disp=base['disposition']; verdict='accept-primary-candidate'
    if key in NOOPS:
        final_target=base['currentTarget']; final_disp='accept-current'; verdict='no-op-accept-current'
        rationale='The proposed target is byte-for-byte identical to the current target, so it makes no localization change. Keep the current translation and record this as accept-current.'
        noops.append(key)
    elif key in REVISIONS:
        final_target=REVISIONS[key]; verdict='revise-primary-candidate'
        rationale=REVISION_REASONS[key]
        revisions.append(key)
    else:
        rationale=REASONS.get(n)
        assert rationale, f'No independent source-context rationale for {key}'
    checks=lit_by[key].get('checks',[]); literal_missing=[]
    for check in checks:
        if check.get('presentInSource') and check['literal'] not in final_target:
            literal_missing.append(check['literal'])
    src_ph=placeholders(base['source']); current_ph=placeholders(base['currentTarget']); final_ph=placeholders(final_target)
    src_markup=markup(base['source']); current_markup=markup(base['currentTarget']); final_markup=markup(final_target)
    structural={'sourcePlaceholders':src_ph,'currentPlaceholders':current_ph,'finalPlaceholders':final_ph,'placeholderParity':src_ph==current_ph==final_ph,'sourceMarkup':src_markup,'currentMarkup':current_markup,'finalMarkup':final_markup,'markupParity':src_markup==current_markup==final_markup,'protectedLiteralChecks':checks,'finalProtectedLiteralMismatches':literal_missing}
    assert structural['placeholderParity'] and structural['markupParity'] and not literal_missing, (key,structural)
    refs=base['callerRefs']
    row={
      'sourceOrdinal':n,'sourceId':base['sourceId'],'locale':loc,'source':base['source'],'sourceTextSha256':base['sourceTextSha256'],
      'currentTarget':base['currentTarget'],'currentTargetSha256':base['currentTargetSha256'],'primaryDisposition':base['disposition'],
      'primaryTarget':cand['recommendedTarget'],'primaryTargetSha256':cand['recommendedTargetSha256'],
      'crossReviewVerdict':verdict,'finalDisposition':final_disp,'finalTarget':final_target,'finalTargetSha256':sha(final_target.encode()),
      'confidence':'moderate','independentRationale':rationale,'callerRefs':refs,'callerContextSha256':base['callerContextSha256'],
      'placeholderMarkupProtectedLiteralChecks':structural,'nativeSpeakerApproval':False
    }
    ledger.append(row); candidate_dispositions[verdict]+=1
    if key in NOOPS: row['noOp']=True
    # add all cells separately below, including previously accepted cells

assert len(ledger)==174
assert candidate_dispositions['accept-primary-candidate']==163
assert candidate_dispositions['revise-primary-candidate']==9
assert candidate_dispositions['no-op-accept-current']==2

# Record final disposition and target for every locale cell in the 50-source window.
ledger_by={(x['sourceOrdinal'],x['locale']):x for x in ledger}
final_counts=collections.Counter()
for key in sorted(review_by):
    base=review_by[key]; candidate=ledger_by.get(key)
    if candidate:
        final_disp=candidate['finalDisposition']; final_target=candidate['finalTarget']; verdict=candidate['crossReviewVerdict']
        rationale=candidate['independentRationale']
    else:
        final_disp=base['disposition']; final_target=base['currentTarget']; verdict='retain-primary-accept-current'
        rationale='Primary review accepted the current cell; cross-review scope targeted proposed cells, and exact live source/current target hashes are reattested in the accompanying ledger.'
    assert final_target is not None
    final_counts[final_disp]+=1
    final_rows.append({'sourceOrdinal':base['sourceOrdinal'],'sourceId':base['sourceId'],'locale':base['locale'],'source':base['source'],'sourceTextSha256':base['sourceTextSha256'],'currentTarget':base['currentTarget'],'currentTargetSha256':base['currentTargetSha256'],'primaryDisposition':base['disposition'],'crossReviewVerdict':verdict,'finalDisposition':final_disp,'finalTarget':final_target,'finalTargetSha256':sha(final_target.encode()),'rationale':rationale,'callerRefs':base['callerRefs'],'callerContextSha256':base['callerContextSha256']})
assert len(final_rows)==600 and final_counts['accept-current']==428 and final_counts['hold']==0
assert final_counts['propose-correction']+final_counts['propose-refinement']==172

# Reattest the previous source boundary at position 499 and its exact caller context.
prev_input_attest=rows(PREVC/'live-cell-hash-reattestation.jsonl')
prev_input_by={(x['sourceOrdinal'],x['locale']):x for x in prev_input_attest}
prev_candidate_rows=rows(PREVC/'cross-review-candidates-and-holds.jsonl')
prev_cross_by={(x['sourceOrdinal'],x['locale']):x for x in prev_candidate_rows}
assert len(prior_rows)==12 and set(x['contextSourceOrdinal'] for x in prior_rows)=={499} and set(x['sourceId'] for x in prior_rows)=={ids[499]}
assert all((499,loc) in prev_input_by for loc in LOCALES)
prev_source_id=ids[499]; boundary_source=source_catalog[prev_source_id]; boundary_source_hash=sha(boundary_source.encode())
boundary=[]; boundary_mismatch=[]; boundary_caller_refs=[]
for old in prior_rows:
    loc=old['locale']; sid=old['sourceId']; current=catalogs[loc].get(sid); current_hash=sha(current.encode()) if isinstance(current,str) else None
    prev_cell=prev_input_by[(499,loc)]
    cross=prev_cross_by.get((499,loc))
    expected_final=cross['finalTarget'] if cross else old['priorPrimaryCurrentTarget']
    expected_final_hash=cross['finalTargetSha256'] if cross else old['priorPrimaryCurrentTargetSha256']
    cross_final_match=(current==expected_final and current_hash==expected_final_hash)
    primary_snapshot_match=(current==old['priorPrimaryCurrentTarget'] and current_hash==old['priorPrimaryCurrentTargetSha256'])
    item={'sourceOrdinal':499,'sourceId':sid,'locale':loc,'sourceTextSha256Frozen':old['sourceTextSha256'],'sourceTextSha256Live':boundary_source_hash,'sourceTextMatchesFrozen':boundary_source==old['source'],'primaryCurrentTargetSha256':old['priorPrimaryCurrentTargetSha256'],'liveCurrentTargetSha256':current_hash,'liveTargetMatchesPrimarySnapshot':primary_snapshot_match,'previousCrossReviewVerdict':cross['crossReviewVerdict'] if cross else 'primary-accept-current','previousCrossReviewFinalDisposition':cross['finalDisposition'] if cross else 'accept-current','previousCrossReviewFinalTarget':expected_final,'previousCrossReviewFinalTargetSha256':expected_final_hash,'liveTargetMatchesPreviousCrossReviewFinal':cross_final_match,'previousCrossReviewRecommendationAppliedAtLiveHead':cross_final_match,'callerContextSha256':old['callerContextSha256'],'callerRefCount':len(old['currentCallerRefs'])}
    boundary.append(item)
    if not (item['sourceTextMatchesFrozen'] and cross_final_match): boundary_mismatch.append(item)
    # The immediately preceding checkpoint 70f still held the primary W499 current targets.
    assert prev_cell['sourceTextSha256Live']==boundary_source_hash and prev_cell['currentTargetSha256Live']==old['priorPrimaryCurrentTargetSha256']
    for ref in old['currentCallerRefs']:
        path=ref['file']; data=show(LIVE,path); lines=data.decode('utf-8').splitlines(); ln=ref['currentLine']; text=lines[ln-1] if 1<=ln<=len(lines) else None
        ok=(blob(LIVE,path)==ref['currentFileBlob'] and sha(data)==ref['currentFileSha256'] and text==ref['currentLineText'] and text is not None and sha(text.encode())==ref['currentLineSha256'])
        cr={'sourceId':sid,'locale':loc,'file':path,'line':ln,'fileBlobFrozen':ref['currentFileBlob'],'fileBlobLive':blob(LIVE,path),'currentLineSha256Frozen':ref['currentLineSha256'],'currentLineSha256Live':sha(text.encode()) if text is not None else None,'matchesFrozen':ok}
        boundary_caller_refs.append(cr)
        if not ok: boundary_mismatch.append({'sourceId':sid,'locale':loc,'callerMismatch':cr})
assert not boundary_mismatch, json.dumps(boundary_mismatch,ensure_ascii=False)
assert boundary_source_hash==prior_rows[0]['sourceTextSha256'] and len(boundary)==12
assert ids[499]!=ids[500]

# Final exact-head check before writing final reattestation evidence.
final_pr=json.loads(subprocess.check_output(pr_args,text=True))
assert final_pr['headRefOid']==LIVE and final_pr['state']=='OPEN' and final_pr['isDraft'] is True
assert git('rev-parse',f'{LIVE}^{{tree}}').decode().strip()==LIVE_TREE

write_jsonl(O/'candidate-cross-review.jsonl',ledger)
write_jsonl(O/'full-cell-final-dispositions.jsonl',final_rows)
write_jsonl(O/'live-cell-hash-reattestation.jsonl',cell_attest)
write_jsonl(O/'caller-reattestation.jsonl',caller_attest)
write_jsonl(O/'W499-boundary-reattestation.jsonl',boundary)
write_jsonl(O/'W499-caller-reattestation.jsonl',boundary_caller_refs)
changed_since_checkpoint=git('diff','--name-status',CHECKPOINT,LIVE).decode().splitlines()
write_json(O/'live-pr-state.json',{'repository':REPO,'pullRequest':PR,'state':final_pr['state'],'isDraft':final_pr['isDraft'],'headRefName':final_pr['headRefName'],'baseRefName':final_pr['baseRefName'],'head':LIVE,'tree':LIVE_TREE,'assignedCheckpointHead':CHECKPOINT,'assignedCheckpointTree':CHECKPOINT_TREE,'changedPathsSinceAssignedCheckpoint':changed_since_checkpoint,'sourceIdListSha256':source_list_sha,'englishCatalogBlobLive':blob(LIVE,src_path),'englishSourceCatalogSha256':sha(source_bytes),'sourceFollowupBlobLive':blob(LIVE,follow_path),'sourceFollowupSha256':sha(follow_bytes),'localeCatalogs':locale_file_info})

summary={
 'repository':REPO,'pullRequest':PR,'primaryPacketHead':FROZEN,'primaryPacketTree':FROZEN_TREE,'assignedCheckpointHead':CHECKPOINT,'assignedCheckpointTree':CHECKPOINT_TREE,'liveHead':LIVE,'liveTree':LIVE_TREE,'prState':'OPEN','draft':True,
 'scope':{'sourceOrdinals':[500,549],'sourceIds':50,'localeCells':600,'primaryCandidates':174,'proposedCorrectionsOrRefinements':174,'primaryHolds':0},
 'crossReview':{'acceptedPrimaryCandidates':candidate_dispositions['accept-primary-candidate'],'revisedPrimaryCandidates':candidate_dispositions['revise-primary-candidate'],'noOpCandidatesAcceptedAsCurrent':candidate_dispositions['no-op-accept-current'],'retainedHolds':0,'revisions':[{'sourceOrdinal':n,'locale':loc,'sourceId':ledger_by[(n,loc)]['sourceId'],'finalTarget':ledger_by[(n,loc)]['finalTarget'],'rationale':ledger_by[(n,loc)]['independentRationale']} for n,loc in sorted(REVISIONS)],'noOpCells':[{'sourceOrdinal':n,'locale':loc,'sourceId':ledger_by[(n,loc)]['sourceId'],'currentTarget':ledger_by[(n,loc)]['currentTarget']} for n,loc in sorted(NOOPS)]},
 'finalDispositionCounts':dict(final_counts),
 'hashAndContextChecks':{'all600SourceCurrentTargetCellsReattested':len(cell_attest),'cellMismatches':len(cell_mismatch),'proposalSourceCurrentTargetHashesReattested':174,'proposalHashMismatches':len(candidate_hash_mismatches),'uniqueLocaleCatalogsWithBlobDriftFromFrozen':sum(v['fileBlobChanged'] for v in locale_file_info.values()),'catalogBlobChangedRowsByLocale':dict(changed_catalog_cell_records),'sourceIdListSha256':source_list_sha,'callerReferencesReattested':len(caller_attest),'uniqueCallerFiles':len(caller_files),'callerMismatches':len(caller_mismatch),'W499BoundaryCellsReattested':len(boundary),'W499TargetsMatchingPreviousCrossReviewFinal':sum(x['liveTargetMatchesPreviousCrossReviewFinal'] for x in boundary),'W499TargetsMatchingPrimaryCurrentSnapshot':sum(x['liveTargetMatchesPrimarySnapshot'] for x in boundary),'W499TargetsChangedFromPrimarySnapshot':sum(not x['liveTargetMatchesPrimarySnapshot'] for x in boundary),'W499CallerReferencesReattested':len(boundary_caller_refs),'W499CallerMismatches':len([x for x in boundary_caller_refs if not x['matchesFrozen']]),'candidatePlaceholderMarkupProtectedLiteralMismatches':0},
 'protectedLiteral':{'primaryWindowCurrentMismatches':prim_summary['protectedLiterals']['currentMismatches'],'allPrimaryCurrentMismatchesCoveredByCandidates':primary_literal_mismatch_keys.issubset(cand_by),'finalCandidateMismatchCount':0,'mismatchCells':prim_summary['protectedLiterals']['currentMismatchCells']},
 'evidenceChecks':{'primaryPacketSHA256SUMSFailures':packet_sum_bad,'primaryPacketInputChecksumFailures':packet_inputs_bad,'previousCrossReviewSHA256SUMSFailures':prev_sum_bad,'previousCrossReviewHead':prior_reattest['exactHead'],'previousCrossReviewTree':prior_reattest['exactTree']},
 'caveats':{'nativeSpeakerApproval':False,'noRepoOrPrEdits':True,'noTestsBuildsScansCiBrowserOrWorkflowEdits':True,'noReleasesOrTags':True}
}
write_json(O/'summary.json',summary)
(O/'README.md').write_text(f'''# ChaptarrNG PR #190 W500–549 independent cross-review

- Cross-reviewed all 174 correction/refinement candidates in the frozen primary packet at `{FROZEN}` / tree `{FROZEN_TREE}`. The primary packet contains no holds.
- Candidate decisions: {candidate_dispositions['accept-primary-candidate']} primary targets retained, {candidate_dispositions['revise-primary-candidate']} revised, and {candidate_dispositions['no-op-accept-current']} exact no-op candidates converted to `accept-current`. No new holds were needed. Exact final targets and rationales are in `candidate-cross-review.jsonl`.
- The two no-op candidates are W536 zh-Hans and zh-Hant: each recommended target exactly equals the current target. The Hindi W536 proposal was revised because it weakened the source’s direct consequence.
- Assigned checkpoint `{CHECKPOINT}` / tree `{CHECKPOINT_TREE}` advanced while this review was running. Final reattestation uses the latest OPEN/DRAFT PR head `{LIVE}` / tree `{LIVE_TREE}`. All 600 W500–549 source/current-target hashes and all 71 pinned caller references reattested without drift. At the latest head, all 12 W499 boundary values match the prior window’s independently reviewed final decisions: 11 proposals are applied and one cell remains accepted-current. The repeated caller refs still match live source.
- Candidate placeholder, markup, and protected-literal parity passes. The five primary current protected-literal mismatches (Vuze Web Remote in three W516 locales and SABnzbd in two W518 locales) are repaired by the primary candidates and remain repaired in the independent final targets.
- This is model cross-review, not native-speaker approval. No repo or PR files were edited. No tests, builds, scans, CI, browser actions, workflow edits, releases, or tags were performed.

## Packet files

- `candidate-cross-review.jsonl`: every proposed cell with current and primary targets, independent final disposition/target, rationale, exact caller context, and placeholder/markup/literal checks.
- `full-cell-final-dispositions.jsonl`: all 600 cells with final dispositions and targets.
- `live-cell-hash-reattestation.jsonl`: all 600 source/current-target values at the live head.
- `caller-reattestation.jsonl`: all 71 W500–549 production caller pins.
- `W499-boundary-reattestation.jsonl` and `W499-caller-reattestation.jsonl`: adjacent boundary source, locale values, previous review context, and caller refs.
- `live-pr-state.json`: exact PR and catalog state.
- `build_crossreview.py`: read-only packet builder.
- `SHA256SUMS`: packet checksums.
''')
write_json(O/'final-reattestation.json',{
 'repository':REPO,'pullRequest':PR,'livePullRequest':final_pr,'exactHead':LIVE,'exactTree':LIVE_TREE,'matchesExpectedLiveHead':True,
 'sourceIdListSha256':source_list_sha,'sourceIdsAttested':50,'cellCountReattested':len(cell_attest),'cellMismatches':cell_mismatch,
 'candidateCount':174,'candidateHashMismatches':len(candidate_hash_mismatches),'candidateVerdictCounts':dict(candidate_dispositions),
 'callerRefsReattested':len(caller_attest),'callerMismatches':caller_mismatch,
 'assignedCheckpointHead':CHECKPOINT,'assignedCheckpointTree':CHECKPOINT_TREE,'priorBoundaryOrdinal':499,'priorBoundaryCellsReattested':len(boundary),'priorBoundaryMismatches':boundary_mismatch,
 'priorBoundaryCallerRefsReattested':len(boundary_caller_refs),'priorBoundaryCallerMismatches':[x for x in boundary_caller_refs if not x['matchesFrozen']],
 'checks':'pass','worktreeStatus':git('status','--porcelain').decode(),'recheckedAtUtc':subprocess.check_output(['date','-u','+%Y-%m-%dT%H:%M:%SZ'],text=True).strip()
})
files=sorted(x for x in O.iterdir() if x.is_file() and x.name!='SHA256SUMS')
(O/'SHA256SUMS').write_text(''.join(f'{sha(x.read_bytes())}  {x.name}\n' for x in files))
print(json.dumps({'output':str(O),'packetFiles':len(files)+1,'summary':summary},ensure_ascii=False,indent=2))
