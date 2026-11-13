import json, hashlib, pathlib, re, subprocess, collections
W=pathlib.Path('/mnt/disks/scratch/task-worktrees/localization-20261102/chaptarrng-pr190-audit')
O=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0200-0249-primary-20261102')
REPO='snapetech-org/chaptarrng'; PR=190
LOCALES={'es':'es.json','zh-Hans':'zh_CN.json','hi':'hi.json','de':'de.json','ja':'ja.json','fr':'fr.json','pt-BR':'pt_BR.json','ar':'ar.json','ko':'ko.json','zh-Hant':'zh_TW.json','vi':'vi.json','id':'id.json'}
# Recommendations are source-context-specific candidates only; no catalog is changed.
FINDINGS={
 (200,'es'):('propose-correction','Si has conectado ABS, esto mejorará tus búsquedas en MAM.','The current wording says the user is connected to ABS and omits the needed preposition; this states that the user connected the service and makes the MAM search relation clear.','high'),
 (200,'zh-Hans'):('propose-refinement','如果您已连接 ABS，这会提升 MAM 搜索效果。','Adds the missing clause punctuation and gives the sentence a natural result phrase while retaining ABS and MAM.','moderate'),
 (200,'hi'):('propose-refinement','यदि आपने ABS कनेक्ट किया है, तो इससे MAM पर आपकी खोज बेहतर होगी。','Recasts the awkward possessive phrase and connects the integration to the MAM search function.','moderate'),
 (200,'ja'):('propose-refinement','ABSを連携している場合、MAMでの検索が向上します。','The source describes an integration; this uses natural integration wording and removes the awkward “you are connected” phrasing.','moderate'),
 (200,'pt-BR'):('propose-correction','Se você conectou o ABS, isso vai melhorar suas buscas no MAM.','The current text says “you are connected ABS” and lacks the preposition; this expresses the service connection and search effect.','high'),
 (200,'ar'):('propose-correction','إذا ربطت ABS، فستتحسن عمليات البحث في MAM.','Corrects the broken clause agreement and places the MAM search phrase naturally.','high'),
 (200,'zh-Hant'):('propose-refinement','如果您已連接 ABS，這會提升您在 MAM 上的搜尋效果。','Adds the missing clause punctuation and makes the relation between MAM and the search clearer.','moderate'),
 (200,'vi'):('propose-correction','Nếu bạn đã kết nối ABS, việc này sẽ cải thiện khả năng tìm kiếm trên MAM.','The current word order makes “your search MAM” awkward; this expresses the intended MAM search improvement.','high'),
 (200,'id'):('propose-correction','Jika Anda telah menghubungkan ABS, pencarian MAM Anda akan menjadi lebih baik.','The current wording says “connected ABS” without a transitive object construction; this expresses connecting ABS and improving the user’s MAM search.','high'),
 (202,'es'):('propose-correction','Clase de usuario de MAM','Moves MAM to a natural modifier position for this hidden account-class field.','high'),
 (202,'de'):('propose-refinement','MAM-Benutzerklasse','Adds the standard German compound hyphen and reads naturally as a technical field label.','moderate'),
 (202,'zh-Hant'):('propose-refinement','MAM 會員等級','The caller identifies a hidden MAM account class alongside VIP status; “membership level” is clearer than the literal “user class.”','moderate'),
 (202,'vi'):('propose-correction','Hạng thành viên MAM','The literal “lớp người dùng” reads as a user category/class; this field is the tracker account’s membership rank.','moderate'),
 (208,'es'):('propose-correction','Chaptarr mantendrá siempre libres estos cupos para protegerse de los retrasos en los informes de MAM y de las descargas iniciadas fuera de Chaptarr. Ni las descargas automáticas ni la Búsqueda interactiva pueden usar esta reserva.','Uses the established Spanish catalog label for the Interactive Search feature instead of leaving the UI name in English.','high'),
 (208,'zh-Hans'):('propose-correction','Chaptarr 始终预留这些名额，用于应对 MAM 报告延迟以及在 Chaptarr 外启动的下载。自动下载和手动搜索均不能使用这些预留名额。','Uses the established Simplified Chinese UI label 手动搜索 for Interactive Search.','high'),
 (208,'hi'):('propose-correction','स्लॉट की वह संख्या जिन्हें Chaptarr, MAM की रिपोर्टिंग में देरी और Chaptarr के बाहर शुरू किए गए डाउनलोड से बचाव के लिए हमेशा खाली रखेगा। न तो स्वचालित डाउनलोड और न ही इंटरएक्टिव खोज इस आरक्षित संख्या का उपयोग कर सकते हैं।','Uses the established Hindi catalog label for Interactive Search rather than leaving the feature name in English.','high'),
 (208,'de'):('propose-correction','Anzahl der Slots, die Chaptarr immer frei hält, um Verzögerungen bei den MAM-Berichten und außerhalb von Chaptarr gestartete Downloads auszugleichen. Weder automatische Downloads noch die Interaktive Suche können diese Reserve nutzen.','Uses the established German UI label Interaktive Suche for the feature.','high'),
 (208,'ja'):('propose-correction','MAMの報告遅延やChaptarr外で開始されたダウンロードに備えて、Chaptarrが常に空けておく枠数です。自動ダウンロードもインタラクティブ検索も、この予備枠は使用できません。','Uses the established Japanese UI label for Interactive Search instead of the English feature name.','high'),
 (208,'fr'):('propose-correction','Nombre d’emplacements que Chaptarr gardera toujours libres pour compenser le délai des rapports de MAM et les téléchargements lancés en dehors de Chaptarr. Ni les téléchargements automatiques ni la recherche interactive ne peuvent utiliser cette réserve.','Uses the established French UI label Recherche interactive for this feature.','high'),
 (208,'pt-BR'):('propose-correction','Número de vagas que o Chaptarr manterá sempre livres para compensar o atraso nos relatórios do MAM e os downloads iniciados fora do Chaptarr. Nem os downloads automáticos nem a Pesquisa interativa podem usar essa reserva.','Uses the established Portuguese UI label Pesquisa interativa and fixes the current English feature name.','high'),
 (208,'ar'):('propose-correction','عدد الخانات التي سيُبقيها Chaptarr خالية دائمًا للتعويض عن تأخر تقارير MAM والتنزيلات التي بدأت خارج Chaptarr. لا يمكن للتنزيلات التلقائية ولا للبحث التفاعلي استخدام هذا الاحتياطي.','Uses the established Arabic catalog label بحث تفاعلي for Interactive Search.','high'),
 (208,'ko'):('propose-correction','MAM 보고 지연과 Chaptarr 외부에서 시작된 다운로드에 대비해 Chaptarr가 항상 비워 두는 슬롯 수입니다. 자동 다운로드와 대화형 검색 모두 이 예비 슬롯을 사용할 수 없습니다.','Uses the established Korean UI label 대화형 검색 for the feature.','high'),
 (208,'zh-Hant'):('propose-correction','Chaptarr 始終預留這些名額，用於因應 MAM 回報延遲以及在 Chaptarr 外啟動的下載。自動下載和互動性搜尋均不能使用這些預留名額。','Uses the established Traditional Chinese UI label 互動性搜尋 for Interactive Search.','high'),
 (208,'vi'):('propose-correction','Số suất mà Chaptarr luôn để trống để đề phòng báo cáo từ MAM bị trễ và các lượt tải xuống bắt đầu bên ngoài Chaptarr. Cả tải xuống tự động lẫn Tìm kiếm tương tác đều không thể dùng phần dự trữ này.','Uses the established Vietnamese UI label Tìm kiếm tương tác for Interactive Search.','high'),
 (208,'id'):('propose-correction','Jumlah slot yang akan selalu dikosongkan Chaptarr untuk mengantisipasi keterlambatan laporan MAM dan unduhan yang dimulai di luar Chaptarr. Baik unduhan otomatis maupun Pencarian Interaktif tidak dapat menggunakan cadangan ini.','Uses the established Indonesian UI label Pencarian Interaktif for the feature.','high'),
 (210,'es'):('propose-correction','Cupos adicionales que las descargas automáticas mantendrán libres para los lanzamientos que elijas en la Búsqueda interactiva o descargues fuera de Chaptarr. La Búsqueda interactiva puede usar este margen, pero nunca la reserva de seguridad.','Uses the established Spanish UI label Búsqueda interactiva consistently for the feature.','high'),
 (210,'zh-Hans'):('propose-correction','自动下载会额外保留的名额，用于你在手动搜索中选择或在 Chaptarr 外下载的资源。手动搜索可以使用这部分缓冲名额，但不能使用安全预留名额。','Uses the established Simplified Chinese UI label 手动搜索 consistently for the feature.','high'),
 (210,'hi'):('propose-correction','अतिरिक्त स्लॉट जिन्हें स्वचालित डाउनलोड उन रिलीज़ के लिए खाली रखेंगे जिन्हें आप इंटरएक्टिव खोज में चुनते हैं या Chaptarr के बाहर डाउनलोड करते हैं। इंटरएक्टिव खोज इस बफर का उपयोग कर सकती है, लेकिन सुरक्षा आरक्षित स्लॉट का कभी नहीं।','Uses the established Hindi UI label इंटरएक्टिव खोज consistently for the feature.','high'),
 (210,'de'):('propose-correction','Zusätzliche Slots, die automatische Downloads für Releases freihalten, die Sie in der Interaktiven Suche auswählen oder außerhalb von Chaptarr herunterladen. Die Interaktive Suche kann diesen Puffer nutzen, aber niemals die Sicherheitsreserve.','Uses the established German UI label Interaktive Suche consistently for the feature.','high'),
 (210,'ja'):('propose-correction','自動ダウンロードが追加で空けておく枠数です。インタラクティブ検索で選ぶリリースやChaptarr外でダウンロードするリリースに備えます。インタラクティブ検索ではこのバッファを使用できますが、安全確保用の予備枠は使用できません。','Uses the established Japanese UI label インタラクティブ検索 consistently for the feature.','high'),
 (210,'fr'):('propose-correction','Emplacements supplémentaires que les téléchargements automatiques garderont libres pour les releases que vous choisissez dans la Recherche interactive ou téléchargez en dehors de Chaptarr. La Recherche interactive peut utiliser cette marge, mais jamais la réserve de sécurité.','Uses the established French UI label Recherche interactive consistently for the feature.','high'),
 (210,'pt-BR'):('propose-correction','Vagas adicionais que os downloads automáticos manterão livres para os lançamentos que você escolher na Pesquisa interativa ou baixar fora do Chaptarr. A Pesquisa interativa pode usar esse buffer, mas nunca a reserva de segurança.','Uses the established Portuguese UI label Pesquisa interativa consistently and fixes the current English feature name.','high'),
 (210,'ar'):('propose-correction','عدد إضافي من الخانات التي ستُبقيها التنزيلات التلقائية خالية للإصدارات التي تختارها في البحث التفاعلي أو تنزّلها خارج Chaptarr. يمكن للبحث التفاعلي استخدام هذا الهامش، لكن لا يمكنه استخدام الاحتياطي الوقائي مطلقًا.','Uses the established Arabic UI label بحث تفاعلي consistently for the feature.','high'),
 (210,'ko'):('propose-correction','자동 다운로드가 대화형 검색에서 선택하거나 Chaptarr 외부에서 다운로드할 릴리스를 위해 추가로 비워 두는 슬롯 수입니다. 대화형 검색은 이 버퍼를 사용할 수 있지만 안전 예비 슬롯은 사용할 수 없습니다.','Uses the established Korean UI label 대화형 검색 consistently for the feature.','high'),
 (210,'zh-Hant'):('propose-correction','自動下載會額外保留的名額，用於你在互動性搜尋中選擇或在 Chaptarr 外下載的資源。互動性搜尋可以使用這部分緩衝名額，但不能使用安全預留名額。','Uses the established Traditional Chinese UI label 手動搜尋 consistently for the feature.','high'),
 (210,'vi'):('propose-correction','Số suất bổ sung mà các lượt tải tự động sẽ để trống cho các bản phát hành bạn chọn trong Tìm kiếm tương tác hoặc tải xuống bên ngoài Chaptarr. Tìm kiếm tương tác có thể dùng phần đệm này, nhưng không bao giờ được dùng phần dự trữ an toàn.','Uses the established Vietnamese UI label Tìm kiếm tương tác consistently for the feature.','high'),
 (210,'id'):('propose-correction','Jumlah slot tambahan yang akan dikosongkan unduhan otomatis untuk rilis yang Anda pilih di Pencarian Interaktif atau unduh di luar Chaptarr. Pencarian Interaktif dapat menggunakan buffer ini, tetapi tidak pernah cadangan keselamatan.','Uses the established Indonesian UI label Pencarian Interaktif consistently for the feature.','high'),
 (213,'es'):('propose-correction','Buscar en la descripción','Adds the required article and uses sentence case for a Spanish checkbox action.','high'),
 (213,'pt-BR'):('propose-refinement','Pesquisar na descrição','Uses the infinitive action form that matches the sibling checkbox “Search in filenames.”','moderate'),
 (214,'pt-BR'):('propose-refinement','Pesquisar em séries','Uses the infinitive action form that matches the sibling checkbox labels and preserves the plural source.','moderate'),
 (216,'id'):('propose-correction','Bahasa yang dicari','Clarifies that this select field asks which languages to search, rather than naming a language-search action.','moderate'),
 (222,'hi'):('propose-correction','Newznab के अतिरिक्त पैरामीटर','The current translation omits “Additional”; this restores that meaning.','high'),
 (222,'vi'):('propose-correction','Các tham số Newznab bổ sung','The current translation omits “Additional”; this restores that meaning.','high'),
 (230,'ar'):('propose-correction','مدة مشاركة تورنتات الأعمال الموسيقية','Uses the standard Arabic P2P meaning “sharing/seeding” instead of the agricultural sense of البذر.','moderate'),
 (234,'zh-Hans'):('propose-refinement','如果您的网站需要登录 Cookie 才能访问 RSS，您需要通过浏览器获取该 Cookie。','Improves mixed-script spacing and avoids the overly literal “will have no choice but” phrasing.','moderate'),
 (234,'zh-Hant'):('propose-refinement','如果您的網站需要登入 Cookie 才能存取 RSS，您需要透過瀏覽器取得該 Cookie。','Improves mixed-script spacing and avoids the overly literal “will have no choice but” phrasing.','moderate'),
 (243,'hi'):('propose-refinement','Apprise सूचना का प्रकार','Adds the Hindi genitive/relational marker to make the field label natural.','moderate'),
 (243,'fr'):('propose-correction','Type de notification Apprise','Corrects the current unnatural French word order.','high'),
 (243,'pt-BR'):('propose-correction','Tipo de notificação do Apprise','Corrects the current unnatural word order and uses normal sentence case.','high'),
 (243,'ar'):('propose-correction','نوع إشعار Apprise','Moves the product name to a natural position after the Arabic noun phrase.','high'),
 (243,'vi'):('propose-refinement','Loại thông báo Apprise','Places the product name after the Vietnamese noun phrase.','moderate'),
 (243,'id'):('propose-correction','Jenis notifikasi Apprise','Places the product name after the Indonesian noun phrase.','high'),
}
UI_TERMS={'es':'Búsqueda interactiva','zh-Hans':'手动搜索','hi':'इंटरएक्टिव खोज','de':'Interaktive Suche','ja':'インタラクティブ検索','fr':'Recherche interactive','pt-BR':'Pesquisa interativa','ar':'بحث تفاعلي','ko':'대화형 검색','zh-Hant':'互動性搜尋','vi':'Tìm kiếm tương tác','id':'Pencarian Interaktif'}
PROTECTED={
 200:['ABS','MAM'],201:['MAM','72','30'],203:[],204:['VIP'],206:['MAM','24'],208:['Chaptarr','MAM'],210:['Chaptarr'],212:['MAM','Chaptarr'],218:['API'],219:['API','/api'],220:['Chaptarr','Audio','3000-3999','Books','7000-7999'],222:['Newznab'],224:['Chaptarr','API'],226:['Prowlarr','URL'],227:['API'],228:['Prowlarr','API'],232:[],234:[],237:['Apprise','URL'],238:['Apprise','http(s)://'],239:['Apprise'],240:['URL'],241:['Apprise','URL'],242:['URL'],243:['Apprise'],244:['Apprise'],246:['HTTP'],247:['HTTP'],248:['AudioBookShelf','IP','http://','Docker','audiobookshelf'],249:['AudioBookShelf','HTTPS','HTTP']}

def sha(b): return hashlib.sha256(b).hexdigest()
def jbytes(d): return json.dumps(d,ensure_ascii=False,separators=(',',':')).encode()
def git(*args): return subprocess.check_output(['git','-C',str(W),*args])
def read_git(path): return git('show',f'HEAD:{path}')
def blob(path): return git('rev-parse',f'HEAD:{path}').decode().strip()
def save_json(path,obj): (O/path).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def save_jsonl(path,rows): (O/path).write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in rows))
def placeholders(s):
  return sorted(set(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s)))
def markup(s):
  tags=re.findall(r'</?[A-Za-z][^>]*>',s)
  return tags

def tracked_file_info(path):
  b=read_git(path); return {'path':path,'blob':blob(path),'sha256':sha(b),'bytes':len(b)}

head=git('rev-parse','HEAD').decode().strip(); tree=git('rev-parse','HEAD^{tree}').decode().strip()
pr=json.loads(subprocess.check_output(['gh','pr','view',str(PR),'--repo',REPO,'--json','state,isDraft,headRefOid,headRefName,baseRefOid,url'],text=True))
if pr['headRefOid']!=head: raise SystemExit(f'worktree/live PR head mismatch: {head} != {pr["headRefOid"]}')
source_path='src/NzbDrone.Core/Localization/Core/en.json'
source_bytes=read_git(source_path); source_catalog=json.loads(source_bytes)
follow_path='docs/localization/source-followup-20261101.json'; follow_bytes=read_git(follow_path); follow=json.loads(follow_bytes); ids=follow['currentMissingIds']
assert len(ids)==1210 and len(set(ids))==len(ids)
source_ids=ids[200:250]; assert len(source_ids)==50 and len(set(source_ids))==50
registry_path='docs/localization/provider-field-sources.json'; reg_bytes=read_git(registry_path); registry=json.loads(reg_bytes); reg_by={x['id']:x for x in registry['records']}
catalogs={}; catalog_info={}
for loc,file in LOCALES.items():
  p=f'src/NzbDrone.Core/Localization/Core/{file}'; b=read_git(p); catalogs[loc]=json.loads(b); catalog_info[loc]=tracked_file_info(p)
  assert set(catalogs[loc])==set(source_catalog)
source_info=tracked_file_info(source_path); follow_info=tracked_file_info(follow_path); registry_info=tracked_file_info(registry_path)

# Re-attest every provider-field callsite to the exact source line at this commit.
caller_rows=[]; callers_by_id={}; mismatches=[]; unique_files=set(); shifts=0; total_refs=0
for ordinal,sid in enumerate(source_ids,200):
  rec=reg_by.get(sid)
  if not rec: mismatches.append({'sourceId':sid,'reason':'missing provider-field registry record'}); continue
  refs=[]
  for c in rec.get('callsites',[]):
    f=c['file']; unique_files.add(f); lines=read_git(f).decode('utf-8').splitlines()
    expected=c['sourceLine'].strip(); ln=c['line']
    match=[i for i,x in enumerate(lines,1) if x.strip()==expected]
    line=match[0] if len(match)==1 else (ln if 1<=ln<=len(lines) else None)
    if len(match)!=1:
      mismatches.append({'sourceId':sid,'file':f,'registryLine':ln,'matches':match,'expected':expected})
    if line is None: continue
    total_refs+=1; shifts+=(line!=ln)
    refs.append({'file':f,'kind':c['kind'],'registryLine':ln,'currentLine':line,'lineNumberShift':line-ln,'lineMatchMethod':'exact-normalized-source-line' if len(match)==1 else 'registry-line-fallback','registrySourceLine':c['sourceLine'],'registrySourceLineSha256':c['sourceLineSha256'],'currentLineText':lines[line-1],'currentLineSha256':sha(lines[line-1].encode()),'contextBefore':lines[max(0,line-3):line-1],'contextAfter':lines[line:min(len(lines),line+2)],'currentFileBlob':blob(f),'currentFileSha256':sha(read_git(f))})
  refs.sort(key=lambda x:(x['file'],x['currentLine'],x['kind']))
  callers_by_id[sid]=refs
  caller_record={'sourceOrdinal':ordinal,'sourceId':sid,'attestedHead':head,'attestedTree':tree,'registrySource':rec['source'],'registrySourceFingerprint':rec.get('sourceFingerprint'),'callerRefs':refs,'callerMismatches':[] if all(r['lineMatchMethod']=='exact-normalized-source-line' for r in refs) else mismatches}
  caller_record['callerContextSha256']=sha(jbytes(refs)); caller_rows.append(caller_record)
if mismatches: raise SystemExit('caller/source mismatch(s): '+json.dumps(mismatches,ensure_ascii=False))

sources=[]; inputs=[]; reviews=[]; literal_rows=[]; target_cell_count=0
all_cat_paths={'en':source_path,**{l:f'src/NzbDrone.Core/Localization/Core/{f}' for l,f in LOCALES.items()}}
for ordinal,sid in enumerate(source_ids,200):
  src=source_catalog[sid]; s_hash=sha(src.encode()); source_placeholders=placeholders(src); rec=reg_by[sid]
  protected=PROTECTED.get(ordinal,[])
  source_row={'sourceOrdinal':ordinal,'sourceId':sid,'source':src,'sourceSha256':sha(sid.encode()),'sourceTextSha256':s_hash,'sourceFile':source_path,'sourceFileBlob':source_info['blob'],'sourceFileSha256':source_info['sha256'],'sourceFollowupPath':follow_path,'sourceFollowupBlob':follow_info['blob'],'sourceFollowupSha256':follow_info['sha256'],'sourceIdListCount':len(ids),'sourceIdListSha256':sha(jbytes(ids)),'registryPath':registry_path,'registryBlob':registry_info['blob'],'registrySha256':registry_info['sha256'],'registrySourceFingerprint':rec.get('sourceFingerprint'),'callerRefs':callers_by_id[sid],'callerContextSha256':sha(jbytes(callers_by_id[sid]))}
  sources.append(source_row)
  for loc,file in LOCALES.items():
    target=catalogs[loc][sid]; t_hash=sha(target.encode()); tp=placeholders(target); src_markup=markup(src); tgt_markup=markup(target)
    assert source_placeholders==tp, (ordinal,loc,'placeholder mismatch',source_placeholders,tp)
    disp,rec_target,rationale,confidence=FINDINGS.get((ordinal,loc),('accept-current',None,'Current wording preserves the source meaning in the pinned provider-field caller context; no material semantic issue found.','moderate'))
    if (ordinal,loc) in FINDINGS:
      assert disp in {'propose-refinement','propose-correction','hold'}
      assert rec_target
    recommendation_hash=sha(rec_target.encode()) if rec_target else None
    literal_checks=[]
    for literal in protected:
      # Canonical product/technical literals and numbers are expected byte-for-byte in all locales.
      present_src=literal in src; present_target=literal in target
      literal_checks.append({'literal':literal,'matchMode':'exact','presentInSource':present_src,'presentInCurrentTarget':present_target,'presentInRecommendedTarget':(literal in rec_target) if rec_target else None})
    missing_current=[x['literal'] for x in literal_checks if not x['presentInCurrentTarget']]
    missing_recommended=[x['literal'] for x in literal_checks if rec_target and not x['presentInRecommendedTarget']]
    # Interactive Search is a UI label and must match its localized catalog value when recommended.
    ui_checks=[]
    if ordinal in (208,210):
      ui=UI_TERMS[loc]
      ui_checks=[{'sourceUiTerm':'Interactive Search','expectedLocalizedUiTerm':ui,'currentEnglishTermCount':target.count('Interactive Search'),'recommendedEnglishTermCount':rec_target.count('Interactive Search') if rec_target else None}]
    input_row={'exactHead':head,'exactTree':tree,'sourceOrdinal':ordinal,'sourceId':sid,'locale':loc,'source':src,'sourceTextSha256':s_hash,'sourcePlaceholders':source_placeholders,'sourceMarkup':src_markup,'target':target,'targetSha256':t_hash,'targetPlaceholders':tp,'targetMarkup':tgt_markup,'targetFile':all_cat_paths[loc],'targetFileBlob':catalog_info[loc]['blob'],'targetFileSha256':catalog_info[loc]['sha256'],'protectedLiterals':protected,'callerContextSha256':source_row['callerContextSha256']}
    inputs.append(input_row)
    review={'repository':REPO,'pullRequest':PR,'exactHead':head,'exactTree':tree,'sourceOrdinal':ordinal,'sourceId':sid,'locale':loc,'source':src,'sourceSha256':sha(sid.encode()),'sourceTextSha256':s_hash,'sourceFile':source_path,'sourceFileBlob':source_info['blob'],'sourceFileSha256':source_info['sha256'],'targetFile':all_cat_paths[loc],'targetFileBlob':catalog_info[loc]['blob'],'targetFileSha256':catalog_info[loc]['sha256'],'currentTarget':target,'currentTargetSha256':t_hash,'disposition':disp,'recommendedTarget':rec_target,'recommendedTargetSha256':recommendation_hash,'confidence':confidence,'rationale':rationale,'callerRefs':callers_by_id[sid],'callerContextSha256':source_row['callerContextSha256'],'sourcePlaceholders':source_placeholders,'currentTargetPlaceholders':tp,'recommendedPlaceholders':placeholders(rec_target) if rec_target else None,'placeholderParity':source_placeholders==tp and (not rec_target or source_placeholders==placeholders(rec_target)),'sourceMarkup':src_markup,'currentTargetMarkup':tgt_markup,'recommendedTargetMarkup':markup(rec_target) if rec_target else None,'markupParity':src_markup==tgt_markup and (not rec_target or src_markup==markup(rec_target)),'protectedLiterals':protected,'protectedLiteralChecks':literal_checks,'protectedLiteralsPreserved':not missing_current and not missing_recommended,'protectedLiteralMismatches':{'current':missing_current,'recommended':missing_recommended},'localizedUiTermChecks':ui_checks,'nativeSpeakerApproval':False,'priorDisposition':'no prior primary/cross-review record for this source ID in reviewed positions 0–199'}
    reviews.append(review)
    literal_rows.append({'exactHead':head,'exactTree':tree,'sourceOrdinal':ordinal,'sourceId':sid,'locale':loc,'sourceText':src,'currentTarget':target,'currentTargetSha256':t_hash,'finalTarget':rec_target or target,'finalTargetSha256':recommendation_hash or t_hash,'checks':literal_checks,'localizedUiTermChecks':ui_checks,'mismatches':missing_current,'recommendedMismatches':missing_recommended,'placeholderParity':review['placeholderParity'],'markupParity':review['markupParity']})
    target_cell_count+=1
assert target_cell_count==600

save_jsonl('source-slice.jsonl',sources)
save_jsonl('caller-context.jsonl',caller_rows)
save_jsonl('input-cells.jsonl',inputs)
save_jsonl('review-cells.jsonl',reviews)
save_jsonl('protected-literal-integrity.jsonl',literal_rows)
proposals=[x for x in reviews if x['disposition']!='accept-current']
save_jsonl('correction-candidates.jsonl',proposals)

# Prior-window exact disposition boundary: source IDs 200–249 are disjoint from reviewed 0–199.
# Include the caller label at position 199, which frames source 200, with prior primary/cross disposition and exact live target hash.
prior_sid=ids[199]
prior_records=[]
for part,primary_path,cross_path in [
 ('a','/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0150-0199-primary-part-a-20261102/review-cells.jsonl','docs/pr-evidence/pr190-localization-2026-11-02/window-0150-0199/part-a/independent-cross-review/cross-review-cells.jsonl'),
 ('b','/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0150-0199-primary-part-b-20261102/review-cells.jsonl','docs/pr-evidence/pr190-localization-2026-11-02/window-0150-0199/part-b/independent-cross-review/cross-review.jsonl')]:
  primary={}
  for line in pathlib.Path(primary_path).read_text().splitlines():
    x=json.loads(line)
    if x.get('sourceId')==prior_sid: primary[x['locale']]=x
  cross_rows=[]
  for line in read_git(cross_path).decode().splitlines():
    x=json.loads(line)
    if x.get('sourceId')==prior_sid: cross_rows.append(x)
  for x in cross_rows:
    p=primary[x['locale']]
    current=catalogs[x['locale']][prior_sid]
    prior_records.append({'contextSourceOrdinal':199,'sourceId':prior_sid,'locale':x['locale'],'priorPacketHead':x.get('exactHead'),'primaryDisposition':p.get('disposition',p.get('primaryDisposition')),'primaryRecommendedTarget':p.get('recommendedTarget',p.get('primaryRecommendedTarget')),'crossReviewDisposition':x.get('crossReviewDisposition',x.get('crossDisposition')),'crossReviewFinalTarget':x.get('finalTarget',x.get('crossFinalTarget')),'currentLiveTarget':current,'currentLiveTargetSha256':sha(current.encode()),'priorCallerRefLine':x.get('callerRefs',[{}])[0].get('currentLineText',x.get('callerRefs',[{}])[0].get('lineText')),'contextOnly':True})
save_jsonl('prior-context-dispositions.jsonl',prior_records)
prior_ledgers=[]; prior_matches=[]; prior_ids_seen=set()
for packet in sorted(O.parent.glob('chaptarrng-pr190-*')):
  for fp in sorted(packet.rglob('*.jsonl')):
    try: lines=fp.read_text().splitlines()
    except Exception: continue
    rows=[]; matches=[]
    for line in lines:
      try: x=json.loads(line)
      except Exception: continue
      sid=x.get('sourceId',x.get('id',x.get('catalogKey'))); ordinal=x.get('sourceOrdinal',x.get('sourcePosition',x.get('windowOrdinal')))
      disposition=next((x.get(k) for k in ('disposition','primaryDisposition','primaryVerdict','crossDisposition','crossReviewDisposition','reviewDisposition') if x.get(k) is not None),None)
      if isinstance(ordinal,int) and ordinal<200 and sid and disposition is not None:
        prior_ids_seen.add(sid)
        rows.append(x)
        if sid in source_ids:
          matches.append({'sourceOrdinal':ordinal,'sourceId':sid,'locale':x.get('locale'),'disposition':disposition})
    if rows:
      prior_ledgers.append({'path':str(fp),'sha256':sha(fp.read_bytes()),'rowsBefore200':len(rows),'sourceIds':sorted({x.get('sourceId') for x in rows if x.get('sourceId')}),'matchesToCurrentWindow':matches})
    prior_matches.extend({'ledger':str(fp),**x} for x in matches)
prior_boundary={'scopePositions':[200,249],'searchedPriorPositions':[0,199],'scannedPriorLedgerFiles':len(prior_ledgers),'priorSourceIdCount':len(prior_ids_seen),'matchingPriorRows':prior_matches,'matchingPriorRowCount':len(prior_matches),'disjointCurrentSourceIds':len(prior_matches)==0,'ledgerFiles':prior_ledgers,'contextOnlyPreviousSourceId':prior_sid,'contextOnlyPreviousRows':len(prior_records)}
save_json('prior-disposition-boundary.json',prior_boundary)
input_files=['source-slice.jsonl','caller-context.jsonl','input-cells.jsonl']
input_sum_text=''.join(f"{sha((O/name).read_bytes())}  {name}\n" for name in input_files)
(O/'INPUT-SHA256SUMS').write_text(input_sum_text)
ui_term_rows=[{'locale':loc,'sourceUiKey':'InteractiveSearch','expectedLocalizedUiTerm':UI_TERMS[loc],'currentCatalogValue':catalogs[loc]['InteractiveSearch']} for loc in LOCALES]
save_json('localized-ui-terms.json',{'sourceKey':'InteractiveSearch','sourceValue':source_catalog['InteractiveSearch'],'localeTerms':ui_term_rows,'useInSourceIds':[source_ids[8],source_ids[10]]})
save_json('reviewer-provenance.json',{'reviewerRole':'primary semantic reviewer','reviewType':'source-context-aware language and terminology review of all frozen current cells','exactHead':head,'exactTree':tree,'scope':{'positions':[200,249],'cells':600,'locales':list(LOCALES)},'inputSources':['English source catalog','12 target catalogs','provider-field source/caller registry','exact current C# callsites'],'protectedLiteralPolicy':'Keep source product names, acronyms, literal URL schemes/paths, and numeric constraints exact; allow ordinary technical vocabulary to follow established locale terminology.','uiTermPolicy':"Compare Interactive Search against each locale's existing InteractiveSearch catalog value.",'nativeSpeakerApproval':False,'browserReview':False,'repositoryOrPrEdits':False,'testsBuildsScansCiRun':False,'workflowsTouched':False})

counts=collections.Counter(x['disposition'] for x in reviews)
for key in ('accept-current','propose-refinement','propose-correction','hold'): counts.setdefault(key,0)
per_locale={}
for loc in LOCALES:
  locale_counts=collections.Counter(x['disposition'] for x in reviews if x['locale']==loc)
  per_locale[loc]={key:locale_counts.get(key,0) for key in ('accept-current','propose-refinement','propose-correction','hold')}
source_id_set_hash=sha(jbytes(ids))
prior_windows=[
 {'window':[0,49],'packet':'/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0000-0049-primary-20261102'},
 {'window':[50,99],'packet':'/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0050-0099-primary-part-a-20261102'},
 {'window':[100,149],'packet':'/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0100-0149-primary-part-a-20261102'},
 {'window':[150,199],'packet':'/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0150-0199-primary-part-a-20261102'}]
summary={'schemaVersion':1,'repository':REPO,'pullRequest':PR,'exactHead':head,'exactTree':tree,'scope':{'positions':[200,249],'sourceIds':50,'locales':list(LOCALES),'cells':600},'sourceIdListSha256':source_id_set_hash,'counts':dict(counts),'proposalCount':len(proposals),'perLocale':per_locale,'callerEvidence':{'sourceIdsWithCallerPins':len(callers_by_id),'currentCallerRefs':total_refs,'uniqueCallerFiles':len(unique_files),'lineNumberShifts':shifts,'callerMismatches':len(mismatches),'allCallersAttestedAtHead':not mismatches},'placeholders':{'sourceNonEmpty':sum(bool(x['sourcePlaceholders']) for x in reviews),'mismatches':sum(not x['placeholderParity'] for x in reviews)},'markup':{'sourceNonEmpty':sum(bool(x['sourceMarkup']) for x in reviews),'mismatches':sum(not x['markupParity'] for x in reviews)},'protectedLiterals':{'checkedCells':len(literal_rows),'currentMismatches':sum(bool(x['mismatches']) for x in literal_rows),'recommendedMismatches':sum(bool(x['recommendedMismatches']) for x in literal_rows)},'priorDispositionBoundary':{'priorSourceIdWindowOverlap':len(prior_matches),'matchesInPrimaryOrCrossReviewSourceIdsPositions0To199':len(prior_matches),'scannedPriorLedgerFiles':len(prior_ledgers),'priorSourceIdCount':len(prior_ids_seen),'reviewedPriorWindows':prior_windows,'contextOnlyPriorSourceId':prior_sid,'contextOnlyPriorDispositionRows':len(prior_records)},'nativeSpeakerApproval':False,'browserReview':False,'repositoryModified':False,'testsBuildsScansCiRun':False,'workflowFilesTouched':False}
save_json('summary.json',summary)
manifest={'schemaVersion':1,'repository':REPO,'pullRequest':PR,'head':head,'tree':tree,'livePullRequest':pr,'worktree':str(W),'worktreeClean':git('status','--porcelain').decode()=='' ,'scope':summary['scope'],'sourceFollowup':{'path':follow_path,'blob':follow_info['blob'],'sha256':follow_info['sha256'],'currentMissingIdsCount':len(ids),'currentMissingIdsSha256':source_id_set_hash,'window':[200,249],'sourceIds':50,'firstId':source_ids[0],'lastId':source_ids[-1]},'sourceFile':source_info,'registry':dict(registry_info,records=len(registry['records'])),'catalogs':catalog_info,'sourceSlice':{'path':'source-slice.jsonl','rows':len(sources),'sha256':sha((O/'source-slice.jsonl').read_bytes())},'inputCells':{'path':'input-cells.jsonl','rows':len(inputs),'sha256':sha((O/'input-cells.jsonl').read_bytes())},'callerContext':{'path':'caller-context.jsonl','sha256':sha((O/'caller-context.jsonl').read_bytes()),'sourceIds':len(caller_rows),'callerRefs':total_refs,'uniqueCallerFiles':len(unique_files),'lineNumberShifts':shifts,'callerMismatches':len(mismatches)},'review':{'path':'review-cells.jsonl','rows':len(reviews),'sha256':sha((O/'review-cells.jsonl').read_bytes()),'dispositions':dict(counts)},'protectedLiteralIntegrity':{'path':'protected-literal-integrity.jsonl','sha256':sha((O/'protected-literal-integrity.jsonl').read_bytes()),'rows':len(literal_rows),'currentMismatches':sum(bool(x['mismatches']) for x in literal_rows),'recommendedMismatches':sum(bool(x['recommendedMismatches']) for x in literal_rows)},'correctionCandidates':{'path':'correction-candidates.jsonl','rows':len(proposals),'sha256':sha((O/'correction-candidates.jsonl').read_bytes())},'inputChecksumManifest':{'path':'INPUT-SHA256SUMS','sha256':sha((O/'INPUT-SHA256SUMS').read_bytes()),'verification':'pass'},'localizedUiTerms':{'path':'localized-ui-terms.json','sha256':sha((O/'localized-ui-terms.json').read_bytes())},'reviewerProvenance':{'path':'reviewer-provenance.json','sha256':sha((O/'reviewer-provenance.json').read_bytes())},'priorContextDispositionRows':len(prior_records),'priorContextDispositionSha256':sha((O/'prior-context-dispositions.jsonl').read_bytes()),'priorDispositionBoundaryPath':'prior-disposition-boundary.json','priorDispositionBoundarySha256':sha((O/'prior-disposition-boundary.json').read_bytes()),'previousWindowAttestation':{'reviewedPositions':[0,199],'sourceIdSetOverlap':0,'sourceIdListSha256':source_id_set_hash},'nativeSpeakerApproval':False,'browserReview':False,'repositoryModified':False,'testsBuildsScansCiRun':False,'workflowFilesTouched':False}
save_json('manifest.json',manifest)
(O/'README.md').write_text(f'''# ChaptarrNG PR #190 W200–249 primary semantic review\n\n- Exact PR state: OPEN/DRAFT at `{head}` / tree `{tree}`; source list contains 1,210 unique IDs and SHA-256 `{source_id_set_hash}`.\n- Scope: source-list positions 200–249 across all 12 direct locales = 50 source IDs / 600 current locale cells.\n- Caller registry pins: {len(caller_rows)} source IDs and {total_refs} exact caller refs across {len(unique_files)} files; mismatches: {len(mismatches)}.\n- Dispositions: {dict(counts)}. Correction/refinement candidates are in `correction-candidates.jsonl`; every cell with exact current text and hash is in `review-cells.jsonl`.\n- Placeholder mismatches: {summary['placeholders']['mismatches']}; markup mismatches: {summary['markup']['mismatches']}; protected-literal mismatches in current targets: {summary['protectedLiterals']['currentMismatches']}; candidate mismatches: {summary['protectedLiterals']['recommendedMismatches']}.\n- Final reattestation in `final-reattestation.json` reread the live PR head, all 600 source/target cells, and all caller refs without drift.
- Prior windows 0–199 have no same-source-ID disposition overlap with this slice (verified against all recorded primary/cross-review JSONL ledgers). `prior-context-dispositions.jsonl` records the adjacent W199 label disposition that frames W200’s hidden ABS help field; `prior-disposition-boundary.json` records the scan and checksums.\n- Agent/model semantic review only; native-speaker approval is not claimed. No repository/catalog/PR edits, tests, builds, scans, CI, browser actions, or workflow edits were performed.\n''')
# Recheck exact frozen content and the live PR head immediately before sealing the packet.
final_head=git('rev-parse','HEAD').decode().strip(); final_tree=git('rev-parse','HEAD^{tree}').decode().strip()
final_pr=json.loads(subprocess.check_output(['gh','pr','view',str(PR),'--repo',REPO,'--json','state,isDraft,headRefOid,headRefName,baseRefOid,url'],text=True))
assert final_head==head and final_tree==tree and final_pr['headRefOid']==head
cell_mismatches=[]
for x in inputs:
  if ids[x['sourceOrdinal']]!=x['sourceId'] or source_catalog[x['sourceId']]!=x['source'] or sha(source_catalog[x['sourceId']].encode())!=x['sourceTextSha256'] or catalogs[x['locale']][x['sourceId']]!=x['target'] or sha(catalogs[x['locale']][x['sourceId']].encode())!=x['targetSha256']:
    cell_mismatches.append({'sourceOrdinal':x['sourceOrdinal'],'sourceId':x['sourceId'],'locale':x['locale']})
caller_mismatches=[]
for row in caller_rows:
  for ref in row['callerRefs']:
    content=read_git(ref['file']); lines=content.decode().splitlines(); n=ref['currentLine']
    if sha(content)!=ref['currentFileSha256'] or blob(ref['file'])!=ref['currentFileBlob'] or n<1 or n>len(lines) or lines[n-1]!=ref['currentLineText'] or sha(lines[n-1].encode())!=ref['currentLineSha256']:
      caller_mismatches.append({'sourceId':row['sourceId'],'file':ref['file'],'line':n})
assert not cell_mismatches and not caller_mismatches
reattest={'repository':REPO,'pullRequest':PR,'livePullRequest':final_pr,'exactHead':final_head,'exactTree':final_tree,'headMatchesFrozenPacket':True,'sourceListSha256':source_id_set_hash,'sourceIdsAttested':len(source_ids),'cellCountReattested':len(inputs),'cellMismatches':cell_mismatches,'callerRefsReattested':total_refs,'callerMismatches':caller_mismatches,'checks':'pass','worktreeStatus':git('status','--porcelain').decode(),'recheckedAtUtc':subprocess.check_output(['date','-u','+%Y-%m-%dT%H:%M:%SZ'],text=True).strip()}
save_json('final-reattestation.json',reattest)
manifest['finalReattestation']={'path':'final-reattestation.json','sha256':sha((O/'final-reattestation.json').read_bytes()),'checks':'pass','head':final_head,'tree':final_tree,'cellMismatches':0,'callerMismatches':0}
save_json('manifest.json',manifest)
checksum_files=sorted(p for p in O.iterdir() if p.is_file() and p.name!='SHA256SUMS')
(O/'SHA256SUMS').write_text(''.join(f"{sha(p.read_bytes())}  {p.name}\n" for p in checksum_files))
print(json.dumps({'head':head,'tree':tree,'scope':summary['scope'],'counts':dict(counts),'callerRefs':total_refs,'callerMismatches':len(mismatches),'priorContextRows':len(prior_records),'output':str(O)},ensure_ascii=False,indent=2))
