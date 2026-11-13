import collections, hashlib, json, pathlib, re, shutil, subprocess

ROOT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0400-0449-crossreview-by-root-child-20261102')
PRIMARY=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0400-0449-primary-20261102')
W=pathlib.Path('/mnt/disks/scratch/task-worktrees/localization-20261102/chaptarrng-pr190-audit')
REPO='snapetech-org/chaptarrng'; PR=190
HEAD='2eb0ae6eb15ebc366eea44dd969265c0f6366445'; TREE='1340ba7d0642217aa81e3789e908931bd6fa74f1'
LOCALES=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
LOCALE_PATHS={'es':'src/NzbDrone.Core/Localization/Core/es.json','zh-Hans':'src/NzbDrone.Core/Localization/Core/zh_CN.json','hi':'src/NzbDrone.Core/Localization/Core/hi.json','de':'src/NzbDrone.Core/Localization/Core/de.json','ja':'src/NzbDrone.Core/Localization/Core/ja.json','fr':'src/NzbDrone.Core/Localization/Core/fr.json','pt-BR':'src/NzbDrone.Core/Localization/Core/pt_BR.json','ar':'src/NzbDrone.Core/Localization/Core/ar.json','ko':'src/NzbDrone.Core/Localization/Core/ko.json','zh-Hant':'src/NzbDrone.Core/Localization/Core/zh_TW.json','vi':'src/NzbDrone.Core/Localization/Core/vi.json','id':'src/NzbDrone.Core/Localization/Core/id.json'}

# Final targets where independent review changes or adds to the primary suggestion.
REVISE={
 (407,'pt-BR'):('Falha na verificação de saúde','propose-correction','The source is an application health-check failure. Integridade usually describes data integrity, so preserve the health-check meaning while fixing the title grammar.'),
 (414,'pt-BR'):('Sucesso! Você configurou corretamente as notificações por e-mail.','propose-refinement','The primary candidate still repeats the configured/configurações construction. This says the email notification settings were configured correctly without the repetition.'),
 (449,'zh-Hant'):('至少需要一個音樂媒體庫','propose-correction','The caller is Plex media-library validation. 資料庫 ordinarily means database; 媒體庫 expresses the required music media library.')
}
ADDITIONAL={
 (413,'es'):('Mensaje de prueba de Chaptarr publicado el {timestamp}','propose-refinement','The current Spanish target begins with lowercase mensaje as a standalone notification sentence. Capitalize it and use the natural date/time preposition.'),
 (413,'vi'):('Tin nhắn thử nghiệm từ Chaptarr được đăng lúc {timestamp}','propose-refinement','The current phrase uses trên (“on top/on”) with a timestamp. lúc is the natural “at” construction for the posting time.'),
 (414,'hi'):('सफलता! आपने ईमेल सूचनाओं की सेटिंग्स सही ढंग से कॉन्फ़िगर की हैं।','propose-correction','The current Hindi uses अपने with feminine plural सेटिंग्स and an awkward setup verb. This version uses correct agreement and the email-notification relationship.'),
 (421,'hi'):('आने वाली पुस्तकें','propose-correction','The current Hindi phrase आने वाले रिलीज has a gender/agreement problem and leaves the book-release domain implicit. This short heading names the forthcoming books.'),
 (434,'es'):('Chaptarr actualizado de {previous} a {current}','propose-correction','The current Spanish pairs desde with a; the standard version-transition construction is de X a Y.'),
 (436,'ko'):('저자 추가: {message}','propose-correction','This is a literary-author notification, matching W401/W403. 저자 is the correct book-author term; 작성자 means a generic writer/creator.'),
 (445,'es'):('No se pueden usar la categoría y el directorio a la vez','propose-correction','The exact validation condition prohibits using Category and Directory together, not either setting individually.'),
 (445,'zh-Hans'):('类别和目录不能同时使用','propose-correction','The source validation forbids the two settings together; the current target omits that relationship and reads as a general prohibition.'),
 (445,'ja'):('カテゴリーとディレクトリは併用できません','propose-correction','The source validation forbids using these settings together. 併用できません expresses that condition directly.'),
 (445,'ko'):('카테고리와 디렉토리를 함께 사용할 수 없습니다.','propose-correction','The source validation forbids the settings together. The current Korean can read as a general ban on either setting.'),
 (445,'zh-Hant'):('類別和目錄不能同時使用','propose-correction','The source validation forbids the two settings together; the current target does not say they are incompatible only when combined.'),
 (445,'id'):('Kategori dan direktori tidak dapat digunakan bersamaan','propose-correction','The source validation forbids using Category and Directory together; the current target leaves that relationship implicit.')
}
CONTEXT={
 400:'completed software import notification prefixes',401:'literary author-added notification heading',402:'book-added notification heading',403:'literary author-deleted notification heading',404:'book-deleted notification heading',405:'file-deleted notification body',406:'book-file-deleted notification heading',407:'application health-check failure heading',408:'book-file tag-update notification prefix',409:'download failure notification prefix',410:'software import-failure notification prefix',411:'previous-version notification field',412:'new-version notification field',413:'timestamped test-message notification',414:'email notification configuration test result',415:'test-message notification body',416:'Kavita configuration test result',417:'Mailgun test-message notification body',418:'total-books MQTT sensor',419:'total-audiobooks MQTT sensor',420:'wanted-books MQTT sensor',421:'upcoming book releases MQTT sensor',422:'library data-size sensor measured in bytes',423:'last-import timestamp sensor',424:'book-selected-for-download notification heading',425:'book-downloaded notification heading',426:'download-failure notification heading',427:'software import-failure notification heading',428:'book-file tag-update notification heading',429:'application-update notification heading',430:'counted imported-files notification body',431:'failed book-file import notification body',432:'localized missing-value display token',433:'unknown-download notification phrase',434:'application version-transition notification body',435:'Subsonic configuration test result',436:'literary author-added notification prefix',437:'book-added notification prefix',438:'deleted-item notification prefix',439:'health issue notification prefix',440:'application-updated notification prefix',441:'manually failed download status',442:'failed-download detection status',443:'encrypted-download detection status',444:'quality-profile validation reason for download failure',445:'Download Station and Transmission validation forbidding Category and Directory together',446:'HTTP authentication credential validation',447:'unmapped author-import validation message with dynamic value0',448:'uTorrent download-client error status',449:'Plex music media-library requirement validation'
}

def sha(b): return hashlib.sha256(b).hexdigest()
def jbytes(x): return json.dumps(x,ensure_ascii=False,separators=(',',':')).encode()
def git(*args): return subprocess.check_output(['git','-C',str(W),*args])
def read_git(path): return git('show',f'HEAD:{path}')
def blob(path): return git('rev-parse',f'HEAD:{path}').decode().strip()
def loadjl(path): return [json.loads(line) for line in pathlib.Path(path).read_text(encoding='utf-8').splitlines() if line]
def gh_state():
    return json.loads(subprocess.check_output(['gh','pr','view',str(PR),'--repo',REPO,'--json','state,isDraft,headRefOid,headRefName,baseRefOid,url'],text=True))
def require_pin(stage):
    pr=gh_state(); h=git('rev-parse','HEAD').decode().strip(); t=git('rev-parse','HEAD^{tree}').decode().strip(); status=git('status','--porcelain').decode()
    assert h==HEAD and t==TREE,(stage,h,t)
    assert pr['headRefOid']==HEAD and pr['state']=='OPEN' and pr['isDraft'] is True,(stage,pr)
    assert status=='',(stage,'dirty worktree',status)
    return {'stage':stage,'checkedAtUtc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'livePullRequest':pr,'worktree':{'head':h,'tree':t,'status':status}}

def verify_sumfile(directory,name):
    for line in (directory/name).read_text().splitlines():
        expected,rel=line.split('  ',1)
        assert sha((directory/rel).read_bytes())==expected,(name,rel)

# Verify sealed primary inputs and reattest source/catalog/caller evidence at the exact live head.
pre=require_pin('before-cross-review')
verify_sumfile(PRIMARY,'INPUT-SHA256SUMS'); verify_sumfile(PRIMARY,'SHA256SUMS')
manifest=json.loads((PRIMARY/'manifest.json').read_text())
assert manifest['head']==HEAD and manifest['tree']==TREE
follow_path='docs/localization/source-followup-20261101.json'
follow_raw=read_git(follow_path); follow=json.loads(follow_raw); ids=follow['currentMissingIds']
assert len(ids)==1210 and sha(jbytes(ids))==manifest['sourceFollowup']['currentMissingIdsSha256']== 'a16dd0001c0a36f053bf0207060c338c428dc9beb2e3d929f7d73f19ad004e8c'
source_ids=ids[400:450]; assert len(source_ids)==50
source_path='src/NzbDrone.Core/Localization/Core/en.json'; source_raw=read_git(source_path); source_catalog=json.loads(source_raw)
assert blob(source_path)==manifest['sourceFile']['blob'] and sha(source_raw)==manifest['sourceFile']['sha256']
locale_catalogs={}; locale_pins={}
for locale,path in LOCALE_PATHS.items():
    raw=read_git(path); locale_catalogs[locale]=json.loads(raw)
    info=manifest['catalogs'][locale]
    assert blob(path)==info['blob'] and sha(raw)==info['sha256'],locale
    locale_pins[locale]={'path':path,'blob':info['blob'],'sha256':info['sha256']}

source_rows=loadjl(PRIMARY/'source-slice.jsonl'); input_rows=loadjl(PRIMARY/'input-cells.jsonl'); primary_rows=loadjl(PRIMARY/'review-cells.jsonl'); candidate_rows=loadjl(PRIMARY/'correction-candidates.jsonl')
assert len(source_rows)==50 and len(input_rows)==600 and len(primary_rows)==600 and len(candidate_rows)==100
assert [r['sourceOrdinal'] for r in source_rows]==list(range(400,450))
assert [r['sourceId'] for r in source_rows]==source_ids
assert sha(jbytes(ids))==manifest['sourceFollowup']['currentMissingIdsSha256']
source_by_id={r['sourceId']:r for r in source_rows}
input_by={(r['sourceOrdinal'],r['locale']):r for r in input_rows}
primary_by={(r['sourceOrdinal'],r['locale']):r for r in primary_rows}
candidate_by={(r['sourceOrdinal'],r['locale']):r for r in candidate_rows}
assert len(input_by)==600 and len(primary_by)==600 and len(candidate_by)==100
assert all((pos,loc) in primary_by for pos in range(400,450) for loc in LOCALES)

caller_refs=0; caller_files={}; caller_gaps=[]
for source_row in source_rows:
    pos=source_row['sourceOrdinal']; sid=source_row['sourceId']; src=source_catalog[sid]
    assert src==source_row['source'] and sha(src.encode())==source_row['sourceTextSha256']
    assert source_row['sourceFileBlob']==blob(source_path) and source_row['sourceFileSha256']==sha(source_raw)
    assert source_row['sourceFollowupBlob']==blob(follow_path) and source_row['sourceFollowupSha256']==sha(follow_raw)
    refs=source_row['callerRefs']
    if not refs: caller_gaps.append({'sourceOrdinal':pos,'sourceId':sid})
    for ref in refs:
        path=ref['file']; raw=read_git(path); lines=raw.decode('utf-8').splitlines(); line=ref['currentLine']
        assert blob(path)==ref['currentFileBlob'] and sha(raw)==ref['currentFileSha256'],(sid,path,'file pin')
        assert 1<=line<=len(lines) and lines[line-1]==ref['currentLineText'] and sha(lines[line-1].encode())==ref['currentLineSha256'],(sid,path,line,'line')
        assert lines[max(0,line-3):line-1]==ref['contextBefore'] and lines[line:min(len(lines),line+2)]==ref['contextAfter'],(sid,path,line,'context')
        caller_refs+=1; caller_files[path]=1
assert caller_refs==90 and len(caller_files)==27 and caller_gaps==[{'sourceOrdinal':447,'sourceId':'server.message.m00dbcd234174'}]

# Reattest all frozen source/current/candidate text against live JSON catalogs.
for key,c in input_by.items():
    pos,loc=key; sid=source_ids[pos-400]; src=source_catalog[sid]; target=locale_catalogs[loc][sid]; r=primary_by[key]
    assert c['sourceId']==sid and c['source']==src and c['target']==target
    assert r['source']==src and r['currentTarget']==target and r['currentTargetSha256']==sha(target.encode())
    assert c['sourceTextSha256']==sha(src.encode()) and c['targetSha256']==sha(target.encode())
    assert c['targetFile']==LOCALE_PATHS[loc]
    assert blob(c['targetFile'])==c['targetFileBlob'] and sha(read_git(c['targetFile']))==c['targetFileSha256']
    assert r['exactHead']==HEAD and r['exactTree']==TREE
    if key in candidate_by:
        candidate=candidate_by[key]
        assert candidate['currentTarget']==target
        if r['disposition']!='hold':
            assert candidate['recommendedTarget'] is not None
            assert sha(candidate['recommendedTarget'].encode())==candidate['recommendedTargetSha256']
        else: assert candidate['recommendedTarget'] is None

# Reattest W399 source, all 12 current targets, both prior dispositions and the 3 pinned caller refs.
prior_rows=loadjl(PRIMARY/'prior-context-dispositions.jsonl'); assert len(prior_rows)==12
prior_primary_dir=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0350-0399-primary-20261102')
prior_cross_dir=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0350-0399-crossreview-by-agent-20261102')
verify_sumfile(prior_primary_dir,'SHA256SUMS'); verify_sumfile(prior_cross_dir,'SHA256SUMS')
prior_primary_rows={(r['sourceOrdinal'],r['locale']):r for r in loadjl(prior_primary_dir/'review-cells.jsonl') if r.get('sourceOrdinal')==399}
prior_cross_rows={(r['sourceOrdinal'],r['locale']):r for r in loadjl(prior_cross_dir/'cross-review-cells.jsonl') if r.get('sourceOrdinal')==399}
assert len(prior_primary_rows)==12 and len(prior_cross_rows)==12
prior_caller_refs={}
for row in prior_rows:
    sid=row['sourceId']; loc=row['locale']; live=locale_catalogs[loc][sid]
    assert sid==ids[399] and source_catalog[sid]==row['source'] and sha(row['source'].encode())==row['sourceTextSha256']
    assert live==row['currentLiveTarget'] and sha(live.encode())==row['currentLiveTargetSha256']
    assert row['priorPrimaryCurrentTargetMatchesLive'] and row['priorCrossReviewInputMatchesCurrentLive'] and row['priorCrossFinalMatchesCurrentLive']
    assert row['primaryDisposition']=='accept-current' and row['crossReviewDisposition']=='accept-current'
    pprior=prior_primary_rows[(399,loc)]; xprior=prior_cross_rows[(399,loc)]
    assert pprior['disposition']=='accept-current' and pprior['recommendedTarget'] is None
    assert pprior['currentTarget']==live and pprior['currentTargetSha256']==sha(live.encode())
    assert xprior['independentVerdict']=='accept-current' and xprior['finalDisposition']=='accept-current'
    assert xprior['currentTarget']==live and xprior['finalTarget']==live and xprior['finalTargetSha256']==sha(live.encode())
    assert row['priorPrimaryInputSha256']==sha(jbytes(pprior)) and row['priorCrossReviewInputSha256']==sha(jbytes(xprior))
    assert xprior['callerContextSha256']==row['priorCrossReviewCallerContextSha256']
    cross_refs={(r['file'],r['line'],r['lineText'],r['lineSha256']) for r in xprior['callerRefs']}
    live_refs={(r['file'],r['currentLine'],r['currentLineText'],r['currentLineSha256']) for r in row['currentCallerRefs']}
    assert cross_refs==live_refs
    for ref in row['currentCallerRefs']:
        path=ref['file']; raw=read_git(path); lines=raw.decode('utf-8').splitlines(); line=ref['currentLine']
        assert blob(path)==ref['currentFileBlob'] and sha(raw)==ref['currentFileSha256']
        assert lines[line-1]==ref['currentLineText'] and sha(lines[line-1].encode())==ref['currentLineSha256']
        prior_caller_refs[(path,line)]=1
    assert row['currentCallerRefsMatchPrior']
assert len(prior_caller_refs)==3

# Recheck the closest author-import source snippet cited by the parent. It constructs a raw dynamic
# ValidationFailure and does not invoke the catalog key or localization helper.
author_path='src/Chaptarr.Api.V1/Author/AuthorController.cs'; author_raw=read_git(author_path); author_lines=author_raw.decode('utf-8').splitlines()
author_line=author_lines[944]
assert author_line.strip()=='new ValidationFailure("Import", $"Failed to import author: {ex.Message}")'
author_evidence={'file':author_path,'line':945,'lineText':author_line,'lineSha256':sha(author_line.encode()),'fileBlob':blob(author_path),'fileSha256':sha(author_raw),'isLocalizedCatalogCall':False}

# Independently reviewed per-cell decisions. The default accept-current covers every current row; explicit
# maps below capture every primary recommendation agreement, adjustment, and additional finding.
review=[]; counts=collections.Counter(); locale_counts={l:collections.Counter() for l in LOCALES}; additional=[]; revisions=[]
for pos in range(400,450):
    sid=source_ids[pos-400]; context=CONTEXT[pos]; srow=source_by_id[sid]
    for loc in LOCALES:
        key=(pos,loc); p=primary_by[key]; inp=input_by[key]; current=p['currentTarget']; cand=p['recommendedTarget']; pdisp=p['disposition']
        if pdisp=='hold':
            assert pos==447 and cand is None
            verdict='retain-hold'; final=current; final_disp='hold'
            note='Retain the hold. This source ID has no exact production caller in the pinned packet; the nearest AuthorController validation constructs a raw dynamic message from ex.Message and is not a localized-key call, so value0 remains unverified.'
            confidence='moderate'
        elif key in REVISE:
            final,final_disp,note=REVISE[key]; verdict='revise-primary-candidate'; confidence='high' if key in ((407,'pt-BR'),(449,'zh-Hant')) else 'moderate'
            revisions.append({'sourceOrdinal':pos,'sourceId':sid,'locale':loc,'primaryTarget':cand,'finalTarget':final,'finalDisposition':final_disp,'reason':note})
        elif key in ADDITIONAL:
            final,final_disp,note=ADDITIONAL[key]; verdict='add-missed-correction' if final_disp=='propose-correction' else 'add-missed-refinement'; confidence='high' if final_disp=='propose-correction' else 'moderate'
            additional.append({'sourceOrdinal':pos,'sourceId':sid,'locale':loc,'currentTarget':current,'finalTarget':final,'finalDisposition':final_disp,'reason':note})
        elif cand is not None:
            final=cand; final_disp=pdisp; verdict='accept-primary-candidate'
            # This source-specific independent note records why the target fits its meaning/context.
            note=f"Independent review agrees with the proposed wording for the {context}; the target preserves the source meaning and fits the pinned caller use."
            confidence=p['confidence']
        else:
            final=current; final_disp='accept-current'; verdict='accept-current'
            note=f"Current wording preserves the source meaning for the {context}; I found no material semantic or structural defect in this cell."
            confidence='moderate'
        # Compare source vs final ICU/format placeholders, markup, and protected literals.
        source=inp['source']; source_ph=sorted(set(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',source)))
        final_ph=sorted(set(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',final)))
        def mt(text):
            if re.fullmatch(r'<[^<>/]+>',text): return []
            return re.findall(r'</?[A-Za-z][^>]*>',text)
        source_markup=mt(source); final_markup=mt(final)
        protected=inp.get('protectedLiterals',[]); missing=[x for x in protected if x not in final]
        assert source_ph==final_ph,(pos,loc,'placeholder parity',source,final,source_ph,final_ph)
        assert source_markup==final_markup,(pos,loc,'markup parity',source,final)
        assert not missing,(pos,loc,'protected literals',missing,final)
        final_sha=sha(final.encode())
        assert p['currentTargetSha256']==sha(current.encode())
        if cand is not None: assert p['recommendedTargetSha256']==sha(cand.encode())
        caller=source_by_id[sid]['callerRefs']
        if pos==447: assert not caller
        verdict_counts=counts
        counts[verdict]+=1; locale_counts[loc][verdict]+=1
        review.append({'repository':REPO,'pullRequest':PR,'exactHead':HEAD,'exactTree':TREE,
          'sourceOrdinal':pos,'sourceId':sid,'locale':loc,'source':source,'sourceTextSha256':sha(source.encode()),
          'currentTarget':current,'currentTargetSha256':sha(current.encode()),
          'primaryDisposition':pdisp,'primaryRecommendedTarget':cand,'primaryRecommendedTargetSha256':p.get('recommendedTargetSha256'),
          'crossReviewVerdict':verdict,'finalDisposition':final_disp,'finalTarget':final,'finalTargetSha256':final_sha,
          'independentRationale':note,'confidence':confidence,'callerRefs':caller,
          'callerContextSha256':srow['callerContextSha256'],'callerClaim':'unclaimed' if pos==447 else 'pinned-caller-context-reviewed',
          'sourceFile':p['sourceFile'],'sourceFileBlob':p['sourceFileBlob'],'sourceFileSha256':p['sourceFileSha256'],
          'targetFile':p['targetFile'],'targetFileBlob':p['targetFileBlob'],'targetFileSha256':p['targetFileSha256'],
          'sourcePlaceholders':source_ph,'finalPlaceholders':final_ph,'placeholderParity':'exact',
          'sourceMarkup':source_markup,'finalMarkup':final_markup,'markupParity':'exact',
          'protectedLiteralsExpected':protected,'protectedLiteralsMissing':missing,'protectedLiteralParity':'exact',
          'nativeSpeakerApproval':False})
assert len(review)==600 and len({(x['sourceOrdinal'],x['locale']) for x in review})==600
assert counts['accept-current']==488 and counts['accept-primary-candidate']==85 and counts['revise-primary-candidate']==3 and counts['add-missed-correction']==10 and counts['add-missed-refinement']==2 and counts['retain-hold']==12
assert sum(1 for x in review if x['finalDisposition']=='propose-correction')==53
assert sum(1 for x in review if x['finalDisposition']=='propose-refinement')==47
assert sum(1 for x in review if x['finalDisposition']=='hold')==12

# Recheck exact live PR/tree after independent semantic judgments.
post=require_pin('after-cross-review')

# Copy the complete frozen primary packet into this output so source/caller/candidate evidence is local and checksummed.
copydir=ROOT/'primary-packet'
copydir.mkdir(exist_ok=True)
for source_file in PRIMARY.iterdir():
    if source_file.is_file(): shutil.copy2(source_file,copydir/source_file.name)

(ROOT/'cross-review-cells.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for r in review),encoding='utf-8')
summary={'schemaVersion':1,'repository':REPO,'pullRequest':PR,'state':'OPEN','isDraft':True,'head':HEAD,'tree':TREE,
 'sourcePositionRange':[400,449],'sourceIds':50,'locales':LOCALES,'cells':600,
 'candidateAdjudicationCounts':dict(sorted(counts.items())),
 'primaryCandidateCells':88,'primaryCandidateAgreementCount':85,'primaryCandidateRevisionCount':3,
 'additionalMissedFindings':len(additional),'additionalMissedCorrections':sum(1 for x in additional if x['finalDisposition']=='propose-correction'),'additionalMissedRefinements':sum(1 for x in additional if x['finalDisposition']=='propose-refinement'),'finalProposedCorrections':53,'finalProposedRefinements':47,'finalHolds':12,'finalAcceptCurrent':488,
 'priorContext':{'sourceOrdinal':399,'sourceId':ids[399],'cells':12,'primaryAccepted':12,'crossReviewAccepted':12,'currentLiveTargetsMatchPriorPrimaryAndCrossFinal':12,'callerRefsReattested':len(prior_caller_refs)},
 'callerEvidence':{'sourceIdsWithCallers':49,'callerReferencesReattested':caller_refs,'uniqueCallerFilesReattested':len(caller_files),'mismatches':0,'unclaimedCallerGap':{'sourceOrdinal':447,'sourceId':'server.message.m00dbcd234174','cells':12,'retainedHold':True,'nearestCaller':'src/Chaptarr.Api.V1/Author/AuthorController.cs:945','nearestCallerIsLocalizedKey':False,'nearestCallerEvidence':author_evidence}},
 'structuralChecks':{'placeholderMismatchCount':0,'markupMismatchCount':0,'protectedLiteralMismatchCount':0},
 'nativeSpeakerApproval':'outstanding','confidence':'moderate','repositoryOrPullRequestModified':False,'testsBuildsScansCiBrowserOrWorkflowWork':False,
 'beforeAfterReattestation':{'before':pre,'after':post},'primaryPacketPath':str(PRIMARY),'outputPath':str(ROOT)}
(ROOT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
(ROOT/'additional-findings.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for x in additional),encoding='utf-8')
(ROOT/'candidate-revisions.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for x in revisions),encoding='utf-8')
README=f'''# ChaptarrNG PR #190 W400–449 independent cross-review

- Exact PR pin: OPEN/DRAFT at `{HEAD}` / tree `{TREE}`, reattested before and after review.
- Scope: 50 source IDs × 12 direct locales = 600 independently judged cells.
- The complete primary packet was copied to `primary-packet/`; its input and output checksum manifests pass. All live source/catalog values and caller lines were reattested at the pinned tree.
- Reviewed all 88 primary correction/refinement candidates, retained the 12-cell hold at W447, and found 12 additional current-target issues. Full final strings, hashes, caller references, and structural checks are in `cross-review-cells.jsonl`.

## Results

- 488 cells: accept current.
- 85 primary candidate targets: accept.
- 3 primary candidates: revise (W407 pt-BR, W414 pt-BR, W449 zh-Hant).
- 12 additional corrections/refinements: W413 es/vi; W414 hi; W421 hi; W434 es; W436 ko; W445 es, zh-Hans, ja, ko, zh-Hant, id.
- W447 remains held in all 12 locales. No source-ID or approved literal-source caller is pinned for this key. `AuthorController.cs:945` interpolates raw `ex.Message` into a different ValidationFailure and is not evidence that this catalog ID renders. Keep the translations unresolved until the actual caller and `value0` meaning are mapped.
- W399 boundary: all 12 prior primary and cross-review dispositions remain `accept-current`; current values, final targets, and three caller references match live data.
- Final independent disposition: 53 correction candidates, 47 refinement candidates, 12 holds, and 488 accepted current values.
- Placeholder, markup, and protected-literal mismatches in all final targets: zero.

Confidence is moderate. Semantic review is model-based; native-speaker approval remains outstanding. No repository/PR edits, tests, builds, scans, CI, browser actions, or workflow edits were performed. The repository worktree is clean.
'''
(ROOT/'README.md').write_text(README,encoding='utf-8')
# Include the builder and all copied evidence in the checksummed deliverable; omit only the manifest itself.
files=sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
(ROOT/'SHA256SUMS').write_text(''.join(f'{sha(p.read_bytes())}  {p.relative_to(ROOT).as_posix()}\n' for p in files),encoding='utf-8')
print(json.dumps({'outputPath':str(ROOT),'summary':summary,'primaryPacketFilesCopied':len(list(copydir.iterdir())),'sha256sumManifest':sha((ROOT/'SHA256SUMS').read_bytes())},ensure_ascii=False,indent=2))
