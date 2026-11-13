import collections, hashlib, json, pathlib, re

OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0750-0799-crossreview-20261102')
PRIMARY=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0750-0799-primary-20261102')
sha=lambda s:hashlib.sha256(s.encode('utf-8')).hexdigest()
loadjl=lambda p:[json.loads(line) for line in p.open(encoding='utf-8') if line.strip()]

# Independent follow-up recommendations found while reviewing accepted-current cells.
# Keys are source ordinal and locale; targets are review suggestions only and were not applied.
missed={
 (770,'ar'):{'disposition':'propose-correction','target':'رف الكتب يغيّر مراقبة الكتب فقط. استخدم محرر المؤلف لتغيير مراقبة المؤلف أو مراقبة الكتب المستقبلية.','confidence':'moderate','rationale':'The message names two UI destinations. At this head, the sidebar label is رف الكتب and the author tab is محرر المؤلف; use the localized catalog labels instead of English Bookshelf / Author Editor.'},
 (770,'de'):{'disposition':'revise-proposal','target':'Bücherregal ändert nur die Überwachung der Bücher. Verwenden Sie Autor Editor, um die Überwachung des Autors oder zukünftiger Bücher zu ändern.','confidence':'moderate','rationale':'The message names two UI destinations. At this head, their German labels are Bücherregal and Autor Editor; the primary proposal left them in English.'},
 (770,'es'):{'disposition':'revise-proposal','target':'Estante para libros solo permite cambiar el seguimiento de los libros. Use Editor de Autor para cambiar el seguimiento del autor o de los libros futuros.','confidence':'moderate','rationale':'The message names two UI destinations. At this head, their Spanish labels are Estante para libros and Editor de Autor; the primary proposal kept the first in English and used a different English second label.'},
 (770,'fr'):{'disposition':'revise-proposal','target':"La section Bibliothèque ne modifie que le suivi des livres. Utilisez Éditeur de l'auteur pour modifier le suivi de l’auteur ou des livres à venir.",'confidence':'moderate','rationale':'The message names two UI destinations. At this head, their French labels are Bibliothèque and the localized AuthorEditor value; the primary proposal kept both in English.'},
 (770,'hi'):{'disposition':'revise-proposal','target':'पुस्तकालय केवल पुस्तकों की निगरानी बदलता है। लेखक या भविष्य में आने वाली पुस्तकों की निगरानी बदलने के लिए लेखक संपादक का उपयोग करें।','confidence':'moderate','rationale':'The message names two UI destinations. At this head, their Hindi labels are पुस्तकालय and लेखक संपादक; the primary proposal kept both in English.'},
 (770,'id'):{'disposition':'propose-correction','target':'Rak buku hanya mengubah pemantauan buku. Gunakan Penyunting Penulis untuk mengubah pemantauan penulis atau buku mendatang.','confidence':'moderate','rationale':'The message names two UI destinations. At this head, their Indonesian labels are Rak buku and Penyunting Penulis; the current target mixed English Bookshelf with a nonmatching editor label.'},
 (770,'ja'):{'disposition':'revise-proposal','target':'本棚では本の監視設定だけを変更できます。著者や今後の本の監視設定を変更するには、作者エディタを使用してください。','confidence':'moderate','rationale':'The message names two UI destinations. At this head, their Japanese labels are 本棚 and 作者エディタ; the primary proposal kept both in English.'},
 (770,'ko'):{'disposition':'revise-proposal','target':'책장에서는 책 모니터링만 변경할 수 있습니다. 저자 또는 앞으로 나올 책의 모니터링을 변경하려면 저자 편집기를 사용하세요.','confidence':'moderate','rationale':'The message names two UI destinations. At this head, their Korean labels are 책장 and 저자 편집기; the primary proposal kept both in English.'},
 (770,'pt-BR'):{'disposition':'revise-proposal','target':'Estante só altera o monitoramento de livros. Use o Editor de autor para alterar o monitoramento do autor ou dos próximos livros.','confidence':'moderate','rationale':'The message names two UI destinations. At this head, their Brazilian Portuguese labels are Estante and Editor de autor; the primary proposal used English Bookshelf and a different editor label.'},
 (770,'vi'):{'disposition':'propose-correction','target':'Giá sách chỉ thay đổi việc theo dõi sách. Dùng Trình chỉnh sửa tác giả để thay đổi việc theo dõi tác giả hoặc sách trong tương lai.','confidence':'moderate','rationale':'The message names two UI destinations. At this head, their Vietnamese labels are Giá sách and Trình chỉnh sửa tác giả; the current target left both labels in English.'},
 (770,'zh-Hans'):{'disposition':'revise-proposal','target':'书架只能更改书籍监控。要更改作者或未来书籍的监控，请使用“编辑作者”。','confidence':'moderate','rationale':'The message names two UI destinations. At this head, their Simplified Chinese labels are 书架 and 编辑作者; the primary proposal left Bookshelf in English and used a different second label.'},
 (770,'zh-Hant'):{'disposition':'revise-proposal','target':'書架只能變更書籍監控。若要變更作者或未來書籍的監控，請使用「作者編輯器」。','confidence':'moderate','rationale':'The message names two UI destinations. At this head, their Traditional Chinese labels are 書架 and 作者編輯器; the primary proposal left Bookshelf in English.'},
 (780,'de'):{'disposition':'propose-correction','target':'Das Importlimit muss mindestens 0 betragen.','confidence':'high','rationale':'The caller is GoodreadsDualMediaImportListSettings.ImportLimit, a numeric application import cap. Einfuhrgrenze normally describes customs import; use the software term Importlimit.'},
 (780,'fr'):{'disposition':'propose-correction','target':'La limite d’importation doit être supérieure ou égale à 0.','confidence':'moderate','rationale':'The current comparison “0 ou plus grande” is unidiomatic for a numeric lower bound. The replacement states the inclusive minimum directly.'},
 (780,'hi'):{'disposition':'propose-correction','target':'आयात सीमा 0 या उससे अधिक होनी चाहिए।','confidence':'moderate','rationale':'सीमा is feminine; होना चाहिए has incorrect agreement. होनी चाहिए preserves the threshold meaning.'},
 (780,'ja'):{'disposition':'propose-correction','target':'インポート上限は 0 以上である必要があります。','confidence':'moderate','rationale':'The current 輸入制限 reads as a restriction on importing goods. The caller is a software import-list count limit; インポート上限 names that setting.'},
 (780,'ko'):{'disposition':'propose-correction','target':'가져오기 한도는 0 이상이어야 합니다.','confidence':'moderate','rationale':'수입 제한 commonly means a restriction on imported goods. The Goodreads import-list setting is a software import cap; 가져오기 한도 is clearer.'},
 (780,'vi'):{'disposition':'propose-refinement','target':'Giới hạn nhập phải từ 0 trở lên.','confidence':'low','rationale':'In this app settings context, nhập khẩu can suggest importing goods. The shorter software term nhập is clearer, pending native-speaker confirmation.'},
 (780,'zh-Hans'):{'disposition':'propose-correction','target':'导入上限必须大于或等于 0。','confidence':'moderate','rationale':'进口通常 refers to importing goods; this is a Goodreads software import-list count cap. 导入上限 is the fitting application term.'},
 (780,'zh-Hant'):{'disposition':'propose-correction','target':'匯入上限必須大於或等於 0。','confidence':'moderate','rationale':'進口通常 refers to importing goods; this is a Goodreads software import-list count cap. 匯入上限 is the fitting application term.'},
 (784,'hi'):{'disposition':'propose-refinement','target':'कृपया परीक्षण करने से पहले मेटाडेटा सर्वर URL सहेजें।','confidence':'moderate','rationale':'The current syntax around इसे परीक्षण करने से पहले is awkward. This keeps the instruction and URL literal in a clearer order.'},
 (795,'es'):{'disposition':'propose-correction','target':'Se requiere ImageUrl.','confidence':'moderate','rationale':'The current ImageUrl es necesario is awkward and has gender agreement tension with URL. An impersonal required-field phrasing avoids changing the protected field name.'},
 (797,'de'):{'disposition':'propose-correction','target':'Autor wurde in die Importwarteschlange aufgenommen.','confidence':'high','rationale':'Einfuhr normally refers to importation of goods. This is an author added to the software import queue; Importwarteschlange expresses that state.'},
}

primary=loadjl(PRIMARY/'primary-review-ledger.jsonl')
candidates={(r['locale'],r['sourceId']):r for r in loadjl(PRIMARY/'correction-candidates.jsonl')}
source_ctx={r['sourceId']:r for r in loadjl(PRIMARY/'caller-context.jsonl')}
placeholder_re=re.compile(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}')
markup_re=re.compile(r'</?[A-Za-z][^>]*>')
def placeholders(s): return sorted(set(placeholder_re.findall(s)))
def markup(s):
    if re.fullmatch(r'<[^<>/]+>',s): return []
    return markup_re.findall(s)
def has_literal(text,lit):
    if re.fullmatch(r'[A-Za-z0-9_]+',lit):
        return re.search(r'(?<![A-Za-z0-9_])'+re.escape(lit)+r'(?![A-Za-z0-9_])',text) is not None
    return lit in text
manual=json.load(open(PRIMARY/'manual-protected-literals.json',encoding='utf-8'))['additionalProtectedLiteralsByOrdinal']
rows=[]
for row in primary:
    loc=row['locale']; sid=row['sourceId']; ordinal=row['sourceOrdinal']
    cand=candidates.get((loc,sid))
    override=missed.get((ordinal,loc))
    if override:
        ind_disp=override['disposition']; target=override['target']; rationale=override['rationale']; conf=override['confidence']
    elif cand:
        ind_disp='accept-proposal'; target=cand['recommendedTarget']; rationale='Independently reviewed against the English source and pinned server caller; the proposal corrects the current wording and preserves the required values.'; conf='moderate'
    else:
        ind_disp='accept-current'; target=row['currentTarget']; rationale='Independently reviewed against the English source and pinned server caller; the current wording preserves the message and technical identifiers.'; conf='moderate'
    context=source_ctx[sid]
    literals=set(row.get('protectedLiterals') or [])|set(manual.get(str(ordinal),[]))
    reclassified=[]
    if ordinal==770 and 'Bookshelf' in literals:
        literals.remove('Bookshelf'); reclassified=['Bookshelf']
    protected_ok=all(has_literal(target,lit) for lit in literals if has_literal(row['source'],lit) or lit in manual.get(str(ordinal),[]))
    ph_ok=placeholders(row['source'])==placeholders(row['currentTarget'])==placeholders(target)
    mk_ok=markup(row['source'])==markup(row['currentTarget'])==markup(target)
    out={
      'schemaVersion':1,'exactHead':row['exactHead'],'exactTree':row['exactTree'],
      'sourceOrdinal':ordinal,'sourceId':sid,'locale':loc,
      'source':row['source'],'sourceTextSha256':row['sourceTextSha256'],
      'currentTarget':row['currentTarget'],'currentTargetSha256':row['currentTargetSha256'],
      'primaryDisposition':row['disposition'],
      'primaryTarget':row['finalTarget'],'primaryTargetSha256':row['finalTargetSha256'],
      'independentDisposition':ind_disp,'independentTarget':target,'independentTargetSha256':sha(target),
      'callerContextSha256':row['callerContextSha256'],'callerRefsCount':len(context['callerRefs']),
      'confidence':conf,'rationale':rationale,
      'sourcePlaceholders':placeholders(row['source']),'currentPlaceholders':placeholders(row['currentTarget']),'independentPlaceholders':placeholders(target),'placeholderParity':ph_ok,
      'sourceMarkup':markup(row['source']),'currentMarkup':markup(row['currentTarget']),'independentMarkup':markup(target),'markupParity':mk_ok,
      'protectedLiterals':sorted(literals),'protectedLiteralsPreserved':protected_ok,'reclassifiedProtectedLiterals':reclassified,
      'nativeSpeakerApproval':False
    }
    rows.append(out)
(OUT/'crossreview-ledger.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows),encoding='utf-8')
(OUT/'missed-corrections.jsonl').write_text(''.join(json.dumps({k:v for k,v in r.items() if k in ['sourceOrdinal','sourceId','locale','source','currentTarget','independentDisposition','independentTarget','independentTargetSha256','confidence','rationale']},ensure_ascii=False,sort_keys=True)+'\n' for r in rows if r['independentDisposition'] in ('propose-correction','propose-refinement')),encoding='utf-8')

counts=collections.Counter(r['independentDisposition'] for r in rows)
per=collections.defaultdict(collections.Counter)
for r in rows: per[r['locale']][r['independentDisposition']]+=1
summary={
 'schemaVersion':1,'repository':'snapetech-org/chaptarrng','pullRequest':190,
 'exactHead':'a58de8cd62a80babdca07a86d6b7d463b4a44773','exactTree':'3baf8c11efe42c617a286cd37665e946303c6d2a',
 'sourceIds':50,'localeCells':len(rows),'reviewedPrimaryProposals':len(candidates),
 'acceptedPrimaryProposals':sum(r['independentDisposition']=='accept-proposal' for r in rows),
 'revisedPrimaryProposals':sum(r['independentDisposition']=='revise-proposal' for r in rows),
 'primaryProposalChanges':sum(r['primaryTarget']!=r['currentTarget'] for r in rows if r['primaryDisposition']=='propose-correction'),
 'missedPrimaryCurrentCells':sum(r['primaryDisposition']=='accept-current' and (r['sourceOrdinal'],r['locale']) in missed for r in rows),
 'independentChangedCells':sum(r['independentTarget']!=r['currentTarget'] for r in rows),
 'independentDispositionCounts':dict(counts),'perLocale':{k:dict(v) for k,v in sorted(per.items())},
 'placeholderMismatchCells':sum(not r['placeholderParity'] for r in rows),
 'markupMismatchCells':sum(not r['markupParity'] for r in rows),
 'independentFinalProtectedMismatchCells':sum(not r['protectedLiteralsPreserved'] for r in rows),
 'nativeSpeakerApproval':False,'browserReview':False,'readOnly':True
}
(OUT/'crossreview-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True))
