import collections, hashlib, json, pathlib, re

PIN=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0300-0349-primary-20261102')
OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0300-0349-crossreview-by-agent-20261102')
HEAD='4b862646fbd038cfa4c16a94f7b6ac16f181751c'
TREE='d76d887609ae90c9238ffda9b192a4c0c72be227'
LOCALES=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']

# Independent cross-review findings on current cells and primary recommendations.
EXTRA={
 (302,'ja'):('propose-cross-review-refinement','Grimmory の URL（http(s):// とポートを含む。例: http://grimmory:6060）。Grimmory から Chaptarr と同じファイルにアクセスできる必要があります（ストレージを共有するか、同じパスにマウントしてください）。','The sample URL is parenthesized, so a period immediately before the closing parenthesis can be copied as part of the port/host. Keep the exact URL and put sentence punctuation after the parenthesis.'),
 (302,'zh-Hans'):('propose-cross-review-refinement','Grimmory URL（包括 http(s):// 和端口，例如 http://grimmory:6060）。Grimmory 必须能访问与 Chaptarr 相同的文件（使用共享存储，或将存储挂载到相同路径）。','The sample URL is parenthesized, so the current period before the closing parenthesis could be copied as part of the URL. Keep the exact URL and put Chinese sentence punctuation after the parenthesis.'),
 (302,'zh-Hant'):('propose-cross-review-refinement','Grimmory URL（包括 http(s):// 和連接埠，例如 http://grimmory:6060）。Grimmory 必須能存取與 Chaptarr 相同的檔案（使用共用儲存空間，或將儲存空間掛載至相同路徑）。','The sample URL is parenthesized, so the current period before the closing parenthesis could be copied as part of the URL. Keep the exact URL and put Chinese sentence punctuation after the parenthesis.'),
 (304,'zh-Hans'):('propose-cross-review-refinement','电子书库','The source is the library collection selected from Grimmory; 电子书库 is a concise natural label, while 电子书图书馆 suggests an institution.'),
 (304,'zh-Hant'):('propose-cross-review-refinement','電子書庫','The source is the library collection selected from Grimmory; 電子書庫 is a concise natural label, while 電子書圖書館 suggests an institution.'),
 (329,'de'):('propose-cross-review-correction','Optionale tokenbasierte Autorisierung. Sie hat Vorrang vor der Anmeldung mit Benutzername und Passwort.','The current German leaves the precedence sentence as a fragment. State that token authorization takes precedence over username/password authentication.'),
 (330,'de'):('propose-cross-review-correction','Optionale Autorisierung','The current adjective is misspelled; the natural German label is Optionale Autorisierung.')
}
REVISE={
 (312,'zh-Hans'):('将 Grimmory 中所做的元数据和封面编辑转发给其他接受媒体库编辑的连接。需要启用 Grimmory 旁车文件的“write on update”设置，以便编辑保存为 Chaptarr 可监视的旁车文件。Grimmory 仅在 DISK_TYPE=LOCAL 时写入旁车文件；使用网络存储时，该设置会隐藏，也不会转发任何内容。','The primary proposal restores the exact setting name, but replaces the already localized 旁车文件 terminology with English sidecar. Preserve the exact setting label and keep the surrounding technical term localized.'),
 (312,'ar'):('حوّل تعديلات البيانات الوصفية والأغلفة التي أُجريت في Grimmory إلى الاتصالات الأخرى التي تقبل تعديلات المكتبات. يتطلب ذلك تفعيل إعداد Grimmory للملفات الجانبية "write on update" حتى تظهر التعديلات كملفات جانبية يستطيع Chaptarr مراقبتها. لا يكتب Grimmory هذه الملفات إلا عند تشغيله باستخدام DISK_TYPE=LOCAL؛ أما عند استخدام التخزين الشبكي، فيكون الإعداد مخفيًا ولا يتم تحويل أي تعديلات.','The primary proposal restores the exact setting name but leaves sidecar untranslated; retain the Arabic term for sidecar files while preserving the exact setting label.'),
 (312,'zh-Hant'):('將 Grimmory 中所做的中繼資料和封面編輯轉送至其他接受媒體庫編輯的連線。需要啟用 Grimmory 側車檔案的「write on update」設定，讓編輯儲存為 Chaptarr 可監看的側車檔案。Grimmory 僅在 DISK_TYPE=LOCAL 時寫入側車檔案；使用網路儲存時，該設定會隱藏，也不會轉送任何內容。','The primary proposal restores the exact setting name but replaces the localized 側車檔案 terminology with English sidecar; preserve the exact setting label and localize the surrounding technical term.'),
 (314,'ja'):('Chaptarrのタグではなく、Grimmoryで本に設定されたタグです。例：Processed。自動送信や転送された編集では、これらのタグが付いたGrimmoryの本は変更されません。ただし、「Grimmory Push」ダイアログと「Push Chaptarr Metadata to Grimmory」操作では引き続き更新されます。','The primary proposal duplicates the example marker (例: 例:). Keep one Japanese example label and preserve the exact tag and action names.'),
 (314,'ko'):('Chaptarr 태그가 아니라 Grimmory에서 책에 설정한 태그입니다. 예: Processed. 자동 전송과 전달된 편집은 이러한 태그가 있는 Grimmory 책을 변경하지 않습니다. 단, “Grimmory Push” 대화상자와 “Push Chaptarr Metadata to Grimmory” 작업은 계속 업데이트합니다.','The primary proposal duplicates the example marker (예: 예:). Keep one Korean example label and preserve the exact tag and action names.')
}
WHY={}
def loadjl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x]
def sha(x): return hashlib.sha256(x.encode('utf-8') if isinstance(x,str) else x).hexdigest()
def ph(s): return sorted(set(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s)))
def tags(s): return re.findall(r'</?[A-Za-z][^>]*>',s)
def compact_hash(x): return sha(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')))
inputs=loadjl(PIN/'input-cells.jsonl')
reviews=loadjl(PIN/'review-cells.jsonl')
candidates=loadjl(PIN/'correction-candidates.jsonl')
sources=loadjl(PIN/'source-slice.jsonl')
ctx=loadjl(PIN/'caller-context.jsonl')
prior=loadjl(PIN/'prior-context-dispositions.jsonl')
source_rationales=json.loads((PIN/'review-decisions.json').read_text(encoding='utf-8'))['sourceRationales']
primary_lines=(PIN/'review-cells.jsonl').read_text(encoding='utf-8').splitlines()
candidate_lines=(PIN/'correction-candidates.jsonl').read_text(encoding='utf-8').splitlines()
input_lines=(PIN/'input-cells.jsonl').read_text(encoding='utf-8').splitlines()
raw_review=[json.loads(x) for x in primary_lines]
raw_candidate=[json.loads(x) for x in candidate_lines]
raw_input=[json.loads(x) for x in input_lines]
review_map={(x['sourceOrdinal'],x['locale']):x for x in reviews}
candidate_map={(x['sourceOrdinal'],x['locale']):x for x in candidates}
review_line_hash={(x['sourceOrdinal'],x['locale']):sha(line) for x,line in zip(raw_review,primary_lines)}
candidate_line_hash={(x['sourceOrdinal'],x['locale']):sha(line) for x,line in zip(raw_candidate,candidate_lines)}
input_line_hash={(x['sourceOrdinal'],x['locale']):sha(line) for x,line in zip(raw_input,input_lines)}
source_map={x['sourceOrdinal']:x for x in sources}
caller_map={x['sourceId']:x for x in ctx}
protected={
 300:['Gotify'],302:['Grimmory','http(s)://','http://grimmory:6060','Chaptarr'],303:['Grimmory'],
 305:['Grimmory','Chaptarr'],307:['Grimmory','Chaptarr'],308:['Chaptarr','Grimmory'],
 310:['Chaptarr','Grimmory'],311:['Grimmory'],312:['Grimmory','Chaptarr','write on update','DISK_TYPE=LOCAL'],
 313:['Grimmory'],314:['Grimmory','Chaptarr','Processed','Grimmory Push','Push Chaptarr Metadata to Grimmory'],
 315:['Join','API','Join API'],321:['Kavita','HTTPS','HTTP'],322:['MailGun','API'],323:['EU'],324:['EU','MailGun'],
 326:['API'],328:['https://ntfy.sh'],334:['Ntfy'],342:['device_iden','pushbullet.com'],346:['30'],348:['86400']}
ledger=[]; assessments=[]
for cell in inputs:
    key=(cell['sourceOrdinal'],cell['locale']); pos,loc=key
    primary=review_map[key]; candidate=candidate_map.get(key); source=cell['source']; current=cell['target']
    if key in REVISE:
        final,reason=REVISE[key]; verdict='revise-primary-candidate'
    elif key in EXTRA:
        verdict,final,reason=EXTRA[key]
    elif candidate:
        final=candidate['recommendedTarget']; reason='Independent cross-review accepts the proposed wording in the pinned caller context; all exact source literals, placeholders, and markup are preserved.'; verdict='accept-primary-candidate'
    else:
        final=current; reason='Independent cross-review finds the current translation semantically acceptable in the pinned caller context; no material mismatch was found.'; verdict='accept-current'
    source_ph=cell['sourcePlaceholders']; final_ph=ph(final); current_ph=cell['targetPlaceholders']
    source_markup=cell['sourceMarkup']; final_markup=tags(final)
    expect=protected.get(pos,[])
    current_missing=[x for x in expect if x not in current]
    candidate_text=candidate['recommendedTarget'] if candidate else None
    candidate_missing=[x for x in expect if candidate_text is not None and x not in candidate_text]
    final_missing=[x for x in expect if x not in final]
    cr=caller_map[cell['sourceId']]
    row={'sourceOrdinal':pos,'sourceId':cell['sourceId'],'locale':loc,'source':source,'sourceSha256':sha(cell['sourceId']),
      'sourceTextSha256':cell['sourceTextSha256'],'currentTarget':current,'currentTargetSha256':cell['targetSha256'],
      'primaryDisposition':primary['disposition'],'primaryRecommendedTarget':candidate_text,
      'primaryRecommendedTargetSha256':candidate['recommendedTargetSha256'] if candidate else None,
      'primaryReviewRowSha256':review_line_hash[key],'primaryCandidateRowSha256':candidate_line_hash.get(key),
      'inputCellRowSha256':input_line_hash[key],'targetFile':cell['targetFile'],'targetFileBlob':cell['targetFileBlob'],
      'targetFileSha256':cell['targetFileSha256'],'callerContextSha256':cell['callerContextSha256'],
      'callerRefs':cr['callerRefs'],'independentVerdict':verdict,'independentRationale':reason,
      'finalTarget':final,'finalTargetSha256':sha(final),'sourcePlaceholders':source_ph,
      'currentTargetPlaceholders':current_ph,'finalTargetPlaceholders':final_ph,
      'placeholderParity':source_ph==final_ph,'sourceMarkup':source_markup,'currentTargetMarkup':cell['targetMarkup'],
      'finalTargetMarkup':final_markup,'markupParity':source_markup==final_markup,
      'protectedLiterals':expect,'currentProtectedLiteralsMissing':current_missing,
      'primaryCandidateProtectedLiteralsMissing':candidate_missing,'finalProtectedLiteralsMissing':final_missing,
      'protectedLiteralParity':not final_missing,'callerSourceRationale':source_rationales[str(pos)]}
    ledger.append(row)
    if candidate:
        assessments.append({'sourceOrdinal':pos,'sourceId':cell['sourceId'],'locale':loc,
          'primaryDisposition':primary['disposition'],'primaryCandidate':candidate_text,
          'primaryCandidateSha256':candidate['recommendedTargetSha256'],
          'candidateRowSha256':candidate_line_hash[key],'independentVerdict':verdict,
          'finalTarget':final,'finalTargetSha256':sha(final),'independentRationale':reason,
          'protectedLiterals':expect,'primaryCandidateProtectedLiteralsMissing':candidate_missing,
          'finalProtectedLiteralsMissing':final_missing,'placeholderParity':row['placeholderParity'],
          'markupParity':row['markupParity'],'callerContextSha256':row['callerContextSha256']})
counts=collections.Counter(x['independentVerdict'] for x in ledger)
assert len(ledger)==600 and len({(x['sourceOrdinal'],x['locale']) for x in ledger})==600
assert all(x['placeholderParity'] and x['markupParity'] and x['protectedLiteralParity'] for x in ledger)
assert sum(bool(x['currentProtectedLiteralsMissing']) for x in ledger)==3
assert sum(bool(x['primaryCandidateProtectedLiteralsMissing']) for x in ledger)==0
assert sum(bool(x['finalProtectedLiteralsMissing']) for x in ledger)==0
# Independently cross-review the frozen adjacent W299 App Token outcomes.
adj=[]
for p in prior:
 live=p['currentLiveTarget']; final=p['crossReviewFinalTarget']
 assert p['priorCrossFinalMatchesCurrentLive'] and live==final
 adj.append({'contextSourceOrdinal':299,'sourceId':p['sourceId'],'locale':p['locale'],
  'source':p['source'],'sourceTextSha256':p['sourceTextSha256'],
  'priorPrimaryDisposition':p['primaryDisposition'],'priorPrimaryRecommendedTarget':p['primaryRecommendedTarget'],
  'priorCrossReviewDisposition':p['crossReviewDisposition'],'priorCrossReviewFinalTarget':final,
  'priorCrossReviewFinalTargetSha256':sha(final),'priorCrossReviewCurrentTarget':p['priorCrossReviewCurrentTarget'],
  'currentLiveTarget':live,'currentLiveTargetSha256':p['currentLiveTargetSha256'],
  'currentMatchesPriorFinal':live==final,'callerContextSha256':p['callerContextSha256'],
  'callerRefs':p['currentCallerRefs'],'independentVerdict':'preserve-adjacent-frozen-disposition',
  'independentRationale':'This is the adjacent W299 App Token entry; its prior primary/cross-review decision remains exact at the live catalog cell and the caller pin was reattested.'})
assert len(adj)==12
(OUT/'cross-review-ledger.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in ledger),encoding='utf-8')
(OUT/'candidate-assessments.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in assessments),encoding='utf-8')
(OUT/'adjacent-w299-context.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in adj),encoding='utf-8')
summary={'repository':'snapetech-org/chaptarrng','pullRequest':190,'liveState':'OPEN/DRAFT','head':HEAD,'tree':TREE,
 'sourcePositionRange':[300,349],'sourceIds':50,'locales':LOCALES,'cells':600,
 'independentDispositionCounts':dict(sorted(counts.items())),
 'primaryCandidatesIndependentlyReviewed':len(assessments),
 'primaryCandidatesAccepted':sum(x['independentVerdict']=='accept-primary-candidate' for x in assessments),
 'primaryCandidatesRevised':sum(x['independentVerdict']=='revise-primary-candidate' for x in assessments),
 'newCrossReviewFindings':sum(x['independentVerdict'].startswith('propose-cross-review-') for x in ledger),
 'newCorrectionFindings':sum(x['independentVerdict']=='propose-cross-review-correction' for x in ledger),
 'newRefinementFindings':sum(x['independentVerdict']=='propose-cross-review-refinement' for x in ledger),
 'currentProtectedLiteralMismatchCells':sum(bool(x['currentProtectedLiteralsMissing']) for x in ledger),
 'primaryCandidateProtectedLiteralMismatchCells':sum(bool(x['primaryCandidateProtectedLiteralsMissing']) for x in ledger),
 'finalProtectedLiteralMismatchCells':sum(bool(x['finalProtectedLiteralsMissing']) for x in ledger),
 'placeholderMismatchCells':sum(not x['placeholderParity'] for x in ledger),
 'markupMismatchCells':sum(not x['markupParity'] for x in ledger),
 'adjacentW299CellsCrossReviewed':len(adj),'adjacentW299CallerRefsReattested':1,
 'nativeSpeakerApproval':'outstanding','repositoryOrPrModified':False,
 'testsBuildsScansCiBrowserWorkflowsReleasesRun':False,'outputPath':str(OUT)}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
readme='''# ChaptarrNG PR #190 W300–349 independent cross-review

This packet independently cross-reviews all 600 locale cells across the 50 source IDs at positions 300–349. The primary packet’s 41 recommendations are each assessed; all current targets are independently judged. The adjacent W299 App Token entry is included as context with its 12 frozen outcomes.

## Pin and reattestation

- PR #190 remained OPEN/DRAFT at head 4b862646fbd038cfa4c16a94f7b6ac16f181751c and tree d76d887609ae90c9238ffda9b192a4c0c72be227.
- The source-ID slice, source/current values for all 600 cells, 51 caller references in 9 files, and the W299 source/cells/caller reference were independently reattested at that head.
- The primary packet checksum manifest passed verification; the repository worktree was clean.

## Findings

- The three current cells at source position 312 omit the exact Grimmory setting name “write on update”; the primary candidates restore it.
- The three primary recommendations restore that literal, but I revised the surrounding phrasing to retain the existing localized terms for sidecar files.
- Two other primary candidate strings (Japanese and Korean at position 314) duplicated the localized example marker; final strings keep one marker.
- Additional cross-review findings: the sample URL punctuation in Japanese/Simplified Chinese/Traditional Chinese at position 302 can be copied as part of the URL; German position 329 leaves a sentence fragment and position 330 misspells “optionale”; the Simplified and Traditional Chinese “Ebook Library” labels at 304 are clearer as 电子书库 / 電子書庫.
- The adjacent W299 App Token decisions still match the live locale cells, including the prior Hindi accepted candidate.

All final candidates preserve exact source protected literals, placeholder structures, and markup. The ledger includes a final exact SHA-256 for every cell. There are no holds. Native-speaker approval remains outstanding; this packet is a machine cross-review.

No repository/PR edits, tests, builds, scans, CI, browser, release, workflow, or tag actions were performed.

## Files

- cross-review-ledger.jsonl: complete independent verdict and final target for every one of the 600 cells.
- candidate-assessments.jsonl: verdicts on the 41 primary candidates.
- adjacent-w299-context.jsonl: the 12 adjacent W299 frozen decisions with exact current/final targets.
- independent-reattestation.json: live pin, source/cell/caller and W299 reattestation evidence.
- README.md, summary.json, build_crossreview.py, SHA256SUMS: method, counts, generator, and checksums.
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')
files=['independent-reattestation.json','cross-review-ledger.jsonl','candidate-assessments.jsonl','adjacent-w299-context.jsonl','summary.json','README.md','build_crossreview.py']
(OUT/'SHA256SUMS').write_text(''.join(f'{sha((OUT/f).read_bytes())}  {f}\n' for f in files),encoding='utf-8')
print(json.dumps({'summary':summary,'independentFindings':[{'pos':x['sourceOrdinal'],'locale':x['locale'],'verdict':x['independentVerdict'],'final':x['finalTarget']} for x in ledger if x['independentVerdict'] not in ('accept-current','accept-primary-candidate')],'checksumFiles':files},ensure_ascii=False,indent=2))
