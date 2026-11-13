#!/usr/bin/env python3
"""Independent, read-only exact-head reattestation for ChaptarrNG PR #190 W700–749."""
import collections, hashlib, json, pathlib, re, subprocess, sys

WORK = pathlib.Path('/home/keith/Documents/code/task-worktrees/localization-20261102-chaptarrng')
PRIMARY = pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0700-0749-primary-20261102')
PRIOR = pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0650-0699-primary-20261102')
PRIOR_X = pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0650-0699-crossreview-independent-20261102')
OUT = pathlib.Path(__file__).parent
HEAD = '02f0d841b54c7806005fc67973973799c6960bcf'
TREE = 'eab2516e48adf4586f14cb131dc1ca6876f87e5f'
LOCALES = ['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
LOCALE_FILES = {'es':'es.json','zh-Hans':'zh_CN.json','hi':'hi.json','de':'de.json','ja':'ja.json','fr':'fr.json','pt-BR':'pt_BR.json','ar':'ar.json','ko':'ko.json','zh-Hant':'zh_TW.json','vi':'vi.json','id':'id.json'}
CATDIR = 'src/NzbDrone.Core/Localization/Core/'

def sha(b): return hashlib.sha256(b if isinstance(b, bytes) else b.encode('utf-8')).hexdigest()
def jbytes(x): return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
def jsonl(path): return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def run(args, cwd=WORK): return subprocess.check_output(args, cwd=cwd, text=True).strip()
def git(*args): return run(['git', *args])
def read_head(path): return subprocess.check_output(['git','show',f'HEAD:{path}'],cwd=WORK)
def git_blob(path): return git('rev-parse',f'HEAD:{path}')
def placeholders(s): return sorted(set(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s)))
def markup(s):
    if re.fullmatch(r'<[^<>/]+>', s): return []
    return re.findall(r'</?[A-Za-z][^>]*>', s)
def verify_sums(directory, filename, base=None):
    results=[]
    for line in (directory/filename).read_text().splitlines():
        digest, name = line.split('  ', 1)
        p=(base or directory)/name
        actual=sha(p.read_bytes()) if p.is_file() else None
        results.append({'path':name,'expectedSha256':digest,'actualSha256':actual,'matches':actual==digest})
    return results

def verify_manifest_entry(entry):
    path=entry['path']; raw=read_head(path)
    return {'path':path,'expectedBytes':entry['bytes'],'liveBytes':len(raw),'expectedSha256':entry['sha256'],'liveSha256':sha(raw),'expectedBlob':entry['blob'],'liveBlob':git_blob(path),'matches':len(raw)==entry['bytes'] and sha(raw)==entry['sha256'] and git_blob(path)==entry['blob']}

primary_sums=verify_sums(PRIMARY,'SHA256SUMS')
primary_input_sums=verify_sums(PRIMARY,'INPUT-SHA256SUMS',WORK)
prior_sums=verify_sums(PRIOR,'SHA256SUMS')
prior_x_sums=verify_sums(PRIOR_X,'SHA256SUMS')
assert all(x['matches'] for x in primary_sums+primary_input_sums+prior_sums+prior_x_sums)
manifest=json.loads((PRIMARY/'manifest.json').read_text())
inp=json.loads((PRIMARY/'input-manifest.json').read_text())
assert manifest['head']==inp['head']==HEAD and manifest['tree']==inp['tree']==TREE
assert manifest['scope']==[700,749] and manifest['sourceCount']==50 and manifest['cellCount']==600
assert inp['scope']['positions']==[700,749] and inp['scope']['cells']==600 and inp['scope']['locales']==LOCALES
assert git('rev-parse','HEAD')==HEAD and git('rev-parse','HEAD^{tree}')==TREE
assert not git('status','--porcelain')

# Independently compare every primary packet file and every declared repository input against exact HEAD.
packet_files=[]
for entry in manifest['packetFiles']:
    p=PRIMARY/entry['path']; actual=sha(p.read_bytes()) if p.is_file() else None
    packet_files.append({'path':entry['path'],'expectedBytes':entry['bytes'],'liveBytes':p.stat().st_size if p.is_file() else None,'expectedSha256':entry['sha256'],'liveSha256':actual,'matches':p.is_file() and p.stat().st_size==entry['bytes'] and actual==entry['sha256']})
assert all(x['matches'] for x in packet_files)
input_entries=[]
for k in ['sourceCatalog','sourceFollowup','serverMessageRegistry','genericCallerRegistry']:
    input_entries.append({'inputType':k,**verify_manifest_entry(inp[k])})
for loc,entry in inp['localeCatalogs'].items():
    input_entries.append({'inputType':'localeCatalog','locale':loc,**verify_manifest_entry(entry)})
for entry in inp['callerFiles']:
    input_entries.append({'inputType':'sourceCallerFile',**verify_manifest_entry(entry)})
assert all(x['matches'] for x in input_entries)

# Rebuild the ordinal slice from the pinned frozen source queue, then read sources and translations from live catalogs.
follow=json.loads(read_head(inp['sourceFollowup']['path']))
ids=follow['currentMissingIds']
assert len(ids)==inp['sourceListCount']==1210
assert sha(jbytes(ids))==follow['currentMissingIdsSha256']==inp['sourceListSha256']
selected=ids[700:750]
assert selected==inp['selectedSourceIds']
source_rows=jsonl(PRIMARY/'source-slice.jsonl')
assert [x['sourceId'] for x in source_rows]==selected
assert [x['sourceOrdinal'] for x in source_rows]==list(range(700,750))
assert sha(jbytes(selected))==inp['selectedSourceIdListSha256']==manifest['sourceIdListSha256']
source_catalog=json.loads(read_head(inp['sourceCatalog']['path']))
loc_catalogs={loc:json.loads(read_head(inp['localeCatalogs'][loc]['path'])) for loc in LOCALES}
review=jsonl(PRIMARY/'review-cells.jsonl')
ledger=jsonl(PRIMARY/'primary-review-ledger.jsonl')
candidates=jsonl(PRIMARY/'correction-candidates.jsonl')
assert len(review)==len(ledger)==600
assert [(x['sourceOrdinal'],x['locale']) for x in review]==[(x['sourceOrdinal'],x['locale']) for x in ledger]
assert len({(x['sourceId'],x['locale']) for x in review})==600
candidate_map={(x['sourceId'],x['locale']):x for x in candidates}
assert len(candidates)==197 and len(candidate_map)==197
ctxs={x['sourceId']:x for x in jsonl(PRIMARY/'caller-context.jsonl')}
assert len(ctxs)==50

# Reattest every cited source caller line, file hash/blob, and surrounding context.
source_pin_rows=[]; source_pin_count=0
for c in ctxs.values():
    refs=[]
    for ref in c['callerRefs']:
        raw=read_head(ref['file']); lines=raw.decode('utf-8').splitlines(); n=ref['line']
        ok=(1<=n<=len(lines) and lines[n-1].strip()==ref['currentLineText'] and sha(lines[n-1].strip())==ref['currentLineSha256'] and sha(raw)==ref['currentFileSha256'] and git_blob(ref['file'])==ref['currentFileBlob'])
        before=lines[max(0,n-1-len(ref.get('contextBefore',[]))):n-1]
        after=lines[n:min(len(lines),n+len(ref.get('contextAfter',[])))]
        ok=ok and [x.strip() for x in before]==ref.get('contextBefore',[]) and [x.strip() for x in after]==ref.get('contextAfter',[])
        refs.append({'sourceId':c['sourceId'],'sourceOrdinal':c['sourceOrdinal'],'file':ref['file'],'line':n,'kind':ref['kind'],'currentLineText':ref['currentLineText'],'currentLineSha256':ref['currentLineSha256'],'fileSha256':sha(raw),'fileBlob':git_blob(ref['file']),'contextBeforeMatches':[x.strip() for x in before]==ref.get('contextBefore',[]),'contextAfterMatches':[x.strip() for x in after]==ref.get('contextAfter',[]),'matches':bool(ok)})
        source_pin_count+=1
    source_pin_rows.extend(refs)
assert source_pin_count==77 and all(x['matches'] for x in source_pin_rows)

# Reattest the generic frontend server-message display pipeline line pins.
pipeline_rows=[]
for ref in jsonl(PRIMARY/'pipeline-caller-context.jsonl'):
    raw=read_head(ref['file']); lines=raw.decode('utf-8').splitlines(); n=ref['line']
    ok=(1<=n<=len(lines) and lines[n-1].strip()==ref['lineText'] and sha(lines[n-1].strip())==ref['lineSha256'] and sha(raw)==ref['fileSha256'] and git_blob(ref['file'])==ref['fileBlob'])
    before=lines[max(0,n-1-len(ref.get('contextBefore',[]))):n-1]
    after=lines[n:min(len(lines),n+len(ref.get('contextAfter',[])))]
    ok=ok and [x.strip() for x in before]==ref.get('contextBefore',[]) and [x.strip() for x in after]==ref.get('contextAfter',[])
    pipeline_rows.append({'file':ref['file'],'line':n,'lineText':ref['lineText'],'lineSha256':ref['lineSha256'],'fileSha256':sha(raw),'fileBlob':git_blob(ref['file']),'contextBeforeMatches':[x.strip() for x in before]==ref.get('contextBefore',[]),'contextAfterMatches':[x.strip() for x in after]==ref.get('contextAfter',[]),'matches':bool(ok)})
assert len(pipeline_rows)==76 and all(x['matches'] for x in pipeline_rows)

# Verify source and current catalog readback, every target hash, and structural tokens for all 600 cells.
source_readbacks=[]; cell_readbacks=[]; disposition_counts=collections.Counter(); token_mismatch=[]
for src in source_rows:
    sid=src['sourceId']; ordn=src['sourceOrdinal']; live_source=source_catalog.get(sid)
    assert live_source==src['source'] and sha(live_source)==src['sourceTextSha256'] and sha(sid)==src['sourceKeySha256']
    assert sid.rsplit('m',1)[-1]==src['sourceTextSha256'][:12]
    source_readbacks.append({'sourceOrdinal':ordn,'sourceId':sid,'source':live_source,'sourceTextSha256':sha(live_source),'sourceKeySha256':sha(sid),'matches':True})
for row in review:
    sid=row['sourceId']; loc=row['locale']; ordn=row['sourceOrdinal']; src=row['source']
    cur=loc_catalogs[loc].get(sid)
    assert source_catalog.get(sid)==src and cur==row['currentTarget']
    assert sha(src)==row['sourceTextSha256'] and sha(cur)==row['currentTargetSha256']
    assert row['exactHead']==HEAD and row['exactTree']==TREE
    assert row['sourceOrdinal'] in range(700,750)
    recommended=row['finalTarget']
    assert recommended==row['currentTarget'] if row['disposition']=='accept-current' else True
    assert sha(recommended)==row['finalTargetSha256']
    assert row['placeholderParity'] and placeholders(src)==placeholders(cur)==row['currentTargetPlaceholders']
    assert placeholders(src)==placeholders(recommended)==row['recommendedPlaceholders'] if row['disposition']!='accept-current' else placeholders(src)==placeholders(recommended)
    assert markup(src)==markup(cur)==row['currentTargetMarkup']
    assert markup(src)==markup(recommended)==row['recommendedTargetMarkup'] if row['disposition']!='accept-current' else markup(src)==markup(recommended)
    protected=[]
    for literal in row['protectedLiterals']:
        p={'literal':literal,'presentInSource':literal in src,'presentInCurrent':literal in cur,'presentInFinal':literal in recommended}
        if p['presentInSource'] and (not p['presentInCurrent'] or not p['presentInFinal']): token_mismatch.append({'sourceOrdinal':ordn,'sourceId':sid,'locale':loc,**p})
        protected.append(p)
    assert all(not x['presentInSource'] or (x['presentInCurrent'] and x['presentInFinal']) for x in protected)
    assert row['protectedLiteralsPreserved']
    assert row['sourceId']==selected[ordn-700]
    assert row['callerContextSha256']==ctxs[sid]['callerContextSha256']
    assert (sid,loc) in candidate_map if row['disposition']=='propose-correction' else (sid,loc) not in candidate_map
    cell_readbacks.append({'sourceOrdinal':ordn,'sourceId':sid,'locale':loc,'source':src,'sourceTextSha256':sha(src),'currentTarget':cur,'currentTargetSha256':sha(cur),'finalTarget':recommended,'finalTargetSha256':sha(recommended),'primaryDisposition':row['disposition'],'currentPlaceholders':placeholders(cur),'finalPlaceholders':placeholders(recommended),'sourceMarkup':markup(src),'currentMarkup':markup(cur),'finalMarkup':markup(recommended),'protectedLiterals':protected,'callerContextSha256':ctxs[sid]['callerContextSha256'],'allPinsAndReadbacksMatch':True})
    disposition_counts[row['disposition']]+=1
assert len(cell_readbacks)==600 and disposition_counts=={'accept-current':403,'propose-correction':197}
assert not token_mismatch

# Check previous W650 has been applied exactly as independently approved, including its W699 row.
prior_summary=json.loads((PRIOR/'summary.json').read_text())
prior_x_summary=json.loads((PRIOR_X/'summary.json').read_text())
assert prior_summary['exactHead']=='4701933a50d367406fd6749c4baaf4befee22129' and prior_summary['exactTree']=='2b22ea480c934d2dc41c6813b1296f1a3c41b027'
assert prior_x_summary['head']==prior_summary['exactHead'] and prior_x_summary['tree']==prior_summary['exactTree']
prior_review=jsonl(PRIOR_X/'cell-crossreview.jsonl')
assert len(prior_review)==600
assert not ({x['sourceId'] for x in prior_review} & set(selected))
prior_applied=0; w699_prior=[]
for row in prior_review:
    if row['sourceOrdinal']==699: w699_prior.append(row)
    if 650<=row['sourceOrdinal']<=699:
        live=loc_catalogs[row['locale']].get(row['sourceId'])
        assert live==row['independentlyPreferredTarget'] and sha(live)==row['independentlyPreferredTargetSha256']
        prior_applied+=1
assert prior_applied==600 and len(w699_prior)==12

# Independently reattest W699's current source, 12 locale targets, previous independent targets, and 48 caller references.
w699_rows=jsonl(PRIMARY/'w699-boundary-reattestation.jsonl')
assert len(w699_rows)==12
boundary_refs=[]
for b in w699_rows:
    assert b['sourceOrdinal']==699 and source_catalog.get(b['sourceId'])==b['source']
    assert sha(b['source'])==b['sourceTextSha256'] and b['sourceId']==ids[699]
    live=loc_catalogs[b['locale']].get(b['sourceId'])
    prior=next(x for x in w699_prior if x['locale']==b['locale'])
    assert live==b['liveTarget']==b['priorCrossReviewFinalTarget']==prior['independentlyPreferredTarget']
    assert sha(live)==b['liveTargetSha256']==b['priorCrossReviewFinalTargetSha256']==prior['independentlyPreferredTargetSha256']
    assert sha(jbytes(b['callerContext']))==b['callerContextSha256']
    for ref in b['callerContext']:
        raw=read_head(ref['file']); lines=raw.decode('utf-8').splitlines(); n=ref['line']
        ok=(1<=n<=len(lines) and lines[n-1].strip()==ref['currentLineText'] and sha(lines[n-1].strip())==ref['currentLineSha256'] and sha(raw)==ref['currentFileSha256'] and git_blob(ref['file'])==ref['currentFileBlob'])
        before=lines[max(0,n-1-len(ref.get('contextBefore',[]))):n-1]
        after=lines[n:min(len(lines),n+len(ref.get('contextAfter',[])))]
        ok=ok and [x.strip() for x in before]==ref.get('contextBefore',[]) and [x.strip() for x in after]==ref.get('contextAfter',[])
        assert ok
        boundary_refs.append({'locale':b['locale'],'sourceId':b['sourceId'],'file':ref['file'],'line':n,'kind':ref['kind'],'currentLineSha256':sha(lines[n-1].strip()),'fileSha256':sha(raw),'fileBlob':git_blob(ref['file']),'contextMatches':True})
assert len(boundary_refs)==48

integrity={
 'schemaVersion':1,'readOnly':True,'repository':'snapetech-org/chaptarrng','pullRequest':190,
 'exactHead':HEAD,'exactTree':TREE,'worktreeHead':git('rev-parse','HEAD'),'worktreeTree':git('rev-parse','HEAD^{tree}'),
 'branch':git('branch','--show-current'),'worktreeClean':not bool(git('status','--porcelain')),
 'primaryPacketChecksumCount':len(primary_sums),'primaryInputChecksumCount':len(primary_input_sums),
 'priorPrimaryChecksumCount':len(prior_sums),'priorCrossReviewChecksumCount':len(prior_x_sums),
 'primaryPacketFiles':len(packet_files),'repositoryInputFiles':len(input_entries),
 'allPacketAndInputHashesVerified':all(x['matches'] for x in primary_sums+primary_input_sums+prior_sums+prior_x_sums+packet_files+input_entries),
 'sourceFollowupPath':inp['sourceFollowup']['path'],'sourceFollowupSha256':sha(read_head(inp['sourceFollowup']['path'])),
 'sourceQueueLength':len(ids),'selectedSlice':[700,749],'selectedSourceIds':50,
 'selectedIdsMatchFrozenQueue':True,'sourceIdListSha256':inp['selectedSourceIdListSha256'],
 'sourceCatalogReadbacks':len(source_readbacks),'localeCatalogReadbacks':len(cell_readbacks),
 'cellReadbackCount':len(cell_readbacks),'primaryDispositionCounts':dict(disposition_counts),
 'candidateCount':len(candidates),'candidateHashesReattested':len(candidates),
 'sourceCallerRows':len(ctxs),'sourceCallerReferences':source_pin_count,'sourceCallerFiles':len({x['file'] for x in source_pin_rows}),
 'sourceCallerPinsVerified':all(x['matches'] for x in source_pin_rows),
 'genericPipelineReferences':len(pipeline_rows),'genericPipelineFiles':len({x['file'] for x in pipeline_rows}),
 'genericPipelinePinsVerified':all(x['matches'] for x in pipeline_rows),
 'currentPlaceholderMismatchCells':0,'finalPlaceholderMismatchCells':0,'currentMarkupMismatchCells':0,'finalMarkupMismatchCells':0,
 'currentProtectedLiteralMismatchCells':0,'finalProtectedLiteralMismatchCells':0,
 'priorW650CellsMatchingCrossReviewFinal':prior_applied,'w699BoundaryRows':len(w699_rows),'w699BoundaryCallerReferences':len(boundary_refs),
 'w699BoundaryTargetsMatchLiveAndPriorCrossReview':True,'allW699CallerPinsVerified':True,
 'exceptions':[]}
(OUT/'structural-reattestation.json').write_text(json.dumps(integrity,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
(OUT/'source-readbacks.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in source_readbacks))
(OUT/'cell-readbacks.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in cell_readbacks))
(OUT/'caller-pin-reattestation.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in source_pin_rows))
(OUT/'pipeline-pin-reattestation.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in pipeline_rows))
(OUT/'w699-boundary-reattestation.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in boundary_refs))
print(json.dumps(integrity,ensure_ascii=False,indent=2))

# Independently adjudicate every proposal and record the eight missed current-cell corrections.
proposal_rows=[]; missed=[]; cross_cells=[]
revisions={
 (742,'ar'):('يوجد بالفعل استبعاد في قائمة الاستيراد لمعرّف هذا المزوّد ونوع الوسائط.','The primary wording uses استثناء (exception), which does not clearly name the existing import-list exclusion item. Use استبعاد (exclusion); the pinned caller is the validation for an existing ImportListExclusion resource.'),
 (745,'ar'):('نمط وسم الكتاب الصوتي غير صالح.','The primary wording reads as invalid audiobook tag placement, not an invalid tag mode. Preserve the mode concept; the pinned caller validates ConversionConfig.TagMode.'),
}
missed_targets={
 (724,'ar'):("الاسم 'None' محجوز لملف تعريف.",'The current target says “saved profile name,” not “reserved profile name.” The caller rejects the literal None with MetadataProfileController.NotEqual("None").'),
 (729,'ar'):('فشلت المصادقة.','The current target says verification failed, conflating verification with authentication. Callers return this message for authentication failures, including client credential checks.'),
 (705,'ja'):('AudioBookShelfサーバーでライブラリが見つかりません。','図書館 means a physical library; the pinned AudioBookShelf caller checks the server’s media-library collection.'),
 (705,'ko'):('AudioBookShelf 서버에서 라이브러리를 찾을 수 없습니다.','도서관 means a physical library; the pinned AudioBookShelf caller checks the server’s media-library collection.'),
 (710,'pt-BR'):('O arquivo do certificado SSL é inválido ou a senha é inválida.','The current inválido conflicts in gender with the nearer feminine noun senha. The caller validates an SSL certificate file or password.'),
 (716,'ja'):('電子書籍のメタデータプロファイルはこの著者には設定されていません（電子書籍は無効です）。電子書籍を追加するには、電子書籍のメタデータプロファイルを設定してください。','The last clause is declarative (“sets … and adds”) rather than an instruction to the user. The pinned AddBookService caller returns this as a validation failure.'),
 (721,'ko'):('인증에 실패했습니다. mam_id가 올바른지 확인하세요(Preferences > Security on MAM에서 찾을 수 있습니다). 프록시를 사용하는 경우 Settings > General > Proxy에서 설정되어 있는지 확인하세요.','The current final clause is declarative (“I check”) rather than an instruction. The pinned MyAnonaMouse caller is an authentication failure and names the exact menu path.'),
 (727,'pt-BR'):('Este é um servidor Calibre-Web, não o servidor de conteúdo do Calibre exigido. Consulte https://manual.calibre-ebook.com/server.html.','The current phrase “servidor de conteúdo necessário Calibre” has unnatural word order and obscures the product distinction. The CalibreProxy caller distinguishes Calibre-Web from the required Calibre content server.'),
}
primary_by_key={(x['sourceOrdinal'],x['locale']):x for x in review}
for key,row in primary_by_key.items():
    (ordinal,loc)=key; source=row['source']; current=row['currentTarget']; primary_final=row['finalTarget']
    if key in missed_targets:
        target,rationale=missed_targets[key]; disposition='propose-correction'
        missed.append({'sourceOrdinal':ordinal,'sourceId':row['sourceId'],'locale':loc,'source':source,'sourceTextSha256':sha(source),'currentTarget':current,'currentTargetSha256':sha(current),'recommendedTarget':target,'recommendedTargetSha256':sha(target),'callerRefs':ctxs[row['sourceId']]['callerRefs'],'rationale':rationale,'confidence':'moderate','primaryDisposition':row['disposition']})
    elif key in revisions:
        target,rationale=revisions[key]; disposition='revise-proposal'
    elif row['disposition']=='propose-correction':
        target=primary_final; disposition='accept-proposal'
        rationale={
          700:'Restores a natural indexer connection failure and log instruction.',701:'Names the move operation and preserves both conflict/no-movable-file alternatives.',702:'Turns the terse fragment into a complete connection failure.',703:'Preserves the exact HTTPS requirement and localhost exception.',704:'Clearly identifies invalid credentials.',705:'Uses software/media-library terminology for AudioBookShelf.',706:'States authentication failure and asks the user to check the API key.',707:'Naturally describes the failed NZB-list retrieval and preserves {value0}.',708:'Makes the password requirement conditional on the API key being unconfigured.',709:'States the sole currently supported Hardcover provider for series lookup.',710:'Clearly identifies an invalid SSL certificate file or password.',711:'Uses a group-specific missing-item expression.',715:'Preserves the product name and update action.',716:'Preserves the ebook metadata-profile type in the instruction.',717:'Localizes the Applies to label while retaining the exact enum values.',718:'Clarifies the invalid file-extension error while preserving every allowed extension.',719:'Presents the allowed-character constraint and preserves the literal set.',720:'States failure to send a test message and preserves {value0}.',721:'Makes the authentication failure and corrective menu instructions natural while preserving product/menu literals.',722:'States that the group cannot be empty.',723:'Uses in-progress wording for the M4B verification status.',724:'Preserves the reserved-name meaning and the literal None.',725:'States the minimum UI-language value clearly.',726:'Clarifies the mixed-root-folder configuration requirement.',727:'Distinguishes Calibre-Web from the required Calibre content server and preserves the documentation URL.',728:'Preserves authorIds and the inclusive numeric range with {value0}.',729:'Uses a natural authentication-failure message.',731:'States the wildcard/IP alternatives and retains the asterisk/IP concept.',732:'Clearly says an API key is required.',734:'Clearly identifies an invalid API key.',735:'Preserves the indexer timeout/network guidance and {value0}.',737:'States that the selected root folder is missing from configuration and preserves the Settings path.',738:'States that the pending import was cancelled.',739:'Uses natural Goodreads user-ID wording.',740:'Preserves the missing upstream book/work ID and all provider names.',741:'States an unknown exception and preserves {value0}.',742:'Names the existing import-list exclusion for the provider ID and media type.',743:'Preserves the exact ebook/audiobook format values.',744:'States that the requested series was not found.',745:'Names an invalid audiobook tag mode.',746:'Clearly states inability to connect to Usenet Download Station.',747:'Uses natural not-found wording and preserves {value0}.',749:'States that the indexer proxy is configured and those settings must match the torrent client proxy.'
        }.get(ordinal,'Candidate preserves the source meaning, caller-specific technical terms, and required literals while improving target-language phrasing.')
    else:
        target=current; disposition='accept-current'
        rationale='Current target preserves the source meaning and relevant technical names/values in the pinned caller context; no material semantic defect was found.'
    assert target is not None and sha(target)
    if row['disposition']=='propose-correction':
        candidate= candidate_map[(row['sourceId'],loc)]
        assert candidate['sourceOrdinal']==ordinal and candidate['source']==source and candidate['sourceTextSha256']==sha(source)
        assert candidate['currentTarget']==current and candidate['currentTargetSha256']==sha(current)
        assert candidate['finalTarget']==primary_final and candidate['finalTargetSha256']==sha(primary_final)
        assert candidate['recommendedTarget']==primary_final and candidate['recommendedTargetSha256']==sha(primary_final)
        assert candidate['exactHead']==HEAD and candidate['exactTree']==TREE
        proposal_rows.append({'sourceOrdinal':ordinal,'sourceId':row['sourceId'],'locale':loc,'source':source,'sourceTextSha256':sha(source),'currentTarget':current,'currentTargetSha256':sha(current),'primaryProposedTarget':primary_final,'primaryProposedTargetSha256':sha(primary_final),'independentDisposition':disposition,'independentTarget':target,'independentTargetSha256':sha(target),'rationale':rationale,'callerRefs':ctxs[row['sourceId']]['callerRefs'],'callerContextSha256':ctxs[row['sourceId']]['callerContextSha256'],'placeholderParity':placeholders(source)==placeholders(target),'markupParity':markup(source)==markup(target),'protectedLiteralsPreserved':all((lit not in source) or (lit in target) for lit in row['protectedLiterals']),'confidence':'moderate'})
    cross_cells.append({'schemaVersion':1,'exactHead':HEAD,'exactTree':TREE,'sourceOrdinal':ordinal,'sourceId':row['sourceId'],'source':source,'sourceTextSha256':sha(source),'locale':loc,'currentTarget':current,'currentTargetSha256':sha(current),'primaryDisposition':row['disposition'],'primaryTarget':primary_final,'primaryTargetSha256':sha(primary_final),'independentDisposition':disposition,'independentTarget':target,'independentTargetSha256':sha(target),'rationale':rationale,'callerContextSha256':ctxs[row['sourceId']]['callerContextSha256'],'callerRefsCount':len(ctxs[row['sourceId']]['callerRefs']),'placeholderParity':placeholders(source)==placeholders(target),'markupParity':markup(source)==markup(target),'protectedLiterals':row['protectedLiterals'],'protectedLiteralsPreserved':all((lit not in source) or (lit in target) for lit in row['protectedLiterals']),'confidence':'moderate'})

assert len(cross_cells)==600 and len(proposal_rows)==197 and len(missed)==8
assert len([x for x in proposal_rows if x['independentDisposition']=='accept-proposal'])==195
assert len([x for x in proposal_rows if x['independentDisposition']=='revise-proposal'])==2
assert len([x for x in cross_cells if x['independentDisposition']=='accept-current'])==395
assert len([x for x in cross_cells if x['independentDisposition']=='propose-correction'])==8
assert not [x for x in cross_cells if x['independentDisposition'] in ('hold','reject-proposal')]
assert sum(x['independentTarget']!=x['currentTarget'] for x in cross_cells)==205
(OUT/'cell-crossreview.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in cross_cells))
(OUT/'candidate-adjudication.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in proposal_rows))
(OUT/'missed-corrections.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in missed))

# Requery PR, branch, API tree, and detached worktree at completion.
pr=json.loads(run(['gh','pr','view','190','--repo','snapetech-org/chaptarrng','--json','state,isDraft,headRefName,headRefOid,baseRefName,url']))
remote_line=run(['git','ls-remote','github',f"refs/heads/{pr['headRefName']}"]).split()
api_tree=run(['gh','api',f"repos/snapetech-org/chaptarrng/commits/{HEAD}",'--jq','.commit.tree.sha'])
assert pr['state']=='OPEN' and pr['isDraft'] and pr['headRefOid']==HEAD and api_tree==TREE and remote_line[0]==HEAD
assert git('rev-parse','HEAD')==HEAD and git('rev-parse','HEAD^{tree}')==TREE and not git('status','--porcelain')
(OUT/'live-pin-reattestation.json').write_text(json.dumps({'repository':'snapetech-org/chaptarrng','pullRequest':190,'state':pr['state'],'isDraft':pr['isDraft'],'branch':pr['headRefName'],'head':pr['headRefOid'],'treeFromGitHubApi':api_tree,'remoteBranchHead':remote_line[0],'worktreeHead':git('rev-parse','HEAD'),'worktreeTree':git('rev-parse','HEAD^{tree}'),'worktreeClean':not bool(git('status','--porcelain')),'matchesExpected':True},ensure_ascii=False,sort_keys=True,indent=2)+'\n')

cross_counts=collections.Counter(x['independentDisposition'] for x in cross_cells)
summary={'schemaVersion':1,'repository':'snapetech-org/chaptarrng','pullRequest':190,'exactHead':HEAD,'exactTree':TREE,'livePullRequest':pr,'remoteBranchHead':remote_line[0],'scope':{'sourceOrdinals':[700,749],'sourceIds':50,'locales':LOCALES,'cells':600},'structuralChecks':'structural-reattestation.json','primaryDispositionCounts':dict(disposition_counts),'independentDispositionCounts':dict(cross_counts),'candidateProposals':197,'acceptedPrimaryProposals':195,'revisedPrimaryProposals':2,'rejectedPrimaryProposals':0,'heldPrimaryProposals':0,'missedCurrentCorrections':8,'changedTargetCellsFromLiveCurrent':205,'crossReviewTargetChangesBeyondPrimary':10,'sourceCallerReferences':77,'genericPipelineReferences':76,'w699BoundaryRows':12,'w699BoundaryCallerReferences':48,'w650PriorAppliedTargetsMatchCrossReview':600,'sourceRegistryPinsRefreshedAndReattested':[711,746],'runtimeCoverageObservation':{'sourceOrdinal':749,'sourceId':'server.message.m9f3baf4b7d39','surface':'Recommendation text in system/proxy/debug API response; no frontend caller found','catalogMeaningReviewed':True,'runtimeDisplayVerified':False,'holdOnCatalogTarget':False},'nativeSpeakerApprovalOutstanding':True,'noRepositoryOrPRWrites':True,'testsBuildsScansCIOrBrowserActions':False,'workflowFilesTouched':False,'releasesTagsMerges':False,'worktreeClean':True,'packetChecksumsVerified':True,'notes':['All 600 source/current/final hashes were recomputed from exact-head catalogs and packet values.','All 77 source callers, 76 generic frontend translation lines, and 48 W699 boundary caller references match pinned exact-head files, lines, and context.','All placeholders, markup, and protected literals match in current and recommended targets.','The primary supplied 197 correction proposals: 195 are accepted and 2 Arabic proposals are revised. Eight additional corrections were found in cells the primary accepted as current; thus 205 cells differ from live current targets, with 10 recommendation changes beyond the primary ledger.','W749 has no direct frontend caller in the pinned caller registry; the catalog translation is semantically reviewed, but this packet does not claim a verified runtime display path.']}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2)+'\n')

# README and machine-readable packet manifest.
readme=f'''# ChaptarrNG PR #190 W700–W749 independent cross-review

**Exact live pin:** PR #190 is OPEN/DRAFT at `{HEAD}` / tree `{TREE}`, branch `{pr['headRefName']}`. The GitHub API tree, remote branch ref, and local detached worktree agree; the worktree is clean.

## Reattestation

- Verified primary packet: {len(primary_sums)} file hashes plus {len(primary_input_sums)} input hashes.
- Recomputed all 50 source rows and 600 current/final target hashes from the pinned source and locale catalogs.
- Reattested all 77 source caller references across 50 files, 76 generic frontend translation pins across 35 files, and all 48 W699 boundary caller references.
- All 600 current/proposed targets preserve placeholders, markup, and listed protected literals.
- The previous W650 packet and independent cross-review checksums verify; all 600 W650 live values match the previous independent final targets. W699's source, caller lines, and all 12 live targets match the prior cross-review.

## Independent dispositions

- {cross_counts['accept-current']} current values accepted unchanged.
- {cross_counts['accept-proposal']} primary proposals accepted.
- {cross_counts['revise-proposal']} primary proposals revised.
- {cross_counts['propose-correction']} missed current-value corrections identified.
- 0 rejected and 0 held; 205 cells differ from current catalogs (197 primary correction proposals, including 2 revisions, plus 8 missed corrections). The cross-review changes 10 targets from the primary recommendations.

The revised/missed target wording, exact current/proposal hashes, caller references, and rationale are in `candidate-adjudication.jsonl` and `missed-corrections.jsonl`; all cell-level values are in `cell-crossreview.jsonl`.

**Caller coverage observation:** W749 (`Proxy is configured for indexers…`) comes from the system/proxy/debug API response and has no direct frontend caller in the pinned registry. Its candidate meaning is reviewed, but the runtime display path remains unverified. This is not a hold on its catalog wording.

Native-speaker approval remains outstanding. This is a scratch-only read-only review: no repository or PR changes, tests, builds, scans, CI, browser actions, workflow changes, releases, tags, or merges.
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')
files=sorted(x for x in OUT.iterdir() if x.is_file() and x.name not in ('SHA256SUMS','manifest.json'))
manifest={'schemaVersion':1,'repository':'snapetech-org/chaptarrng','pullRequest':190,'exactHead':HEAD,'exactTree':TREE,'sourcePrimaryPacket':str(PRIMARY),'sourcePrimaryChecksumManifestSha256':sha((PRIMARY/'SHA256SUMS').read_bytes()),'files':[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in files]}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
checksum_files=sorted(x for x in OUT.iterdir() if x.is_file() and x.name!='SHA256SUMS')
(OUT/'SHA256SUMS').write_text(''.join(f'{sha(p.read_bytes())}  {p.name}\n' for p in checksum_files))
print(json.dumps({'independentDispositionCounts':dict(cross_counts),'candidateRows':len(proposal_rows),'missedCorrections':len(missed),'changedTargetCellsFromCurrent':205,'changesBeyondPrimary':10,'packetFiles':len(checksum_files),'sha256Manifest':sha((OUT/'SHA256SUMS').read_bytes()),'packetBytes':sum(p.stat().st_size for p in OUT.iterdir() if p.is_file())},ensure_ascii=False,indent=2))
