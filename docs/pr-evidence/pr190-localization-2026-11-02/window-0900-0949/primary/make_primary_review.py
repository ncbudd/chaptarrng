from __future__ import annotations
import collections,hashlib,json,pathlib,re
OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0900-0949-primary-20261102')
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
CONF={'ar':'moderate','de':'high','es':'high','fr':'high','hi':'moderate','id':'moderate','ja':'moderate','ko':'moderate','pt-BR':'high','vi':'moderate','zh-Hans':'moderate','zh-Hant':'moderate'}
def sha(b): return hashlib.sha256(b if isinstance(b,bytes) else b.encode()).hexdigest()
def readjl(n): return [json.loads(x) for x in (OUT/n).read_text().splitlines()]
def writejl(n,rows): (OUT/n).write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in rows))
def placeholders(s): return sorted(set(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s)))
def markup(s):
 if re.fullmatch(r'<[^<>/]+>',s): return []
 return re.findall(r'</?[A-Za-z][^>]*>',s)
# Manual adjudications. The input source/caller evidence is frozen in input-cells.jsonl and caller-context.jsonl.
C={}
def put(o,loc,target,kind,why): C[(o,loc)]={'target':target,'kind':kind,'why':why}
# 900: global delay-profile errors.
put(900,'es','No se puede eliminar el perfil de retraso global.','refinement','La forma “perfil global del retraso” es comprensible, pero suena poco natural; esta opción usa el término directo “perfil de retraso global”.')
put(900,'hi','वैश्विक विलंब प्रोफ़ाइल हटाई नहीं जा सकती।','correction','El perfil es femenino en hindi, por lo que el valor actual usa una concordancia incorrecta.')
put(900,'ja','グローバル遅延プロファイルを削除できません。','refinement','「プロフィール」は不自然な借用語です。設定項目として一般的な「プロファイル」に整えます。')
put(900,'vi','Không thể xóa hồ sơ trì hoãn toàn cầu.','refinement','Dùng “trì hoãn” para “delay” en un ajuste es más natural y conciso que “chậm trễ”.')
put(900,'zh-Hans','无法删除全局延迟配置文件。','correction','“档案”不符合此处软件设置档案的常用说法；改用“配置文件”。')
put(900,'zh-Hant','無法刪除全域延遲設定檔。','correction','軟體設定中的 profile 通常稱為「設定檔」；目前的「檔案」容易理解成一般檔案。')
# 901: numeric MetadataProfileId validation.
put(901,'fr','MetadataProfileId doit être supérieur à 0 s’il est renseigné.','refinement','La formulation actuelle est un fragment raide; cette version garde le nom exact du champ et exprime clairement la condition.')
put(901,'hi','यदि MetadataProfileId प्रदान की गई है, तो उसका मान 0 से अधिक होना चाहिए।','correction','La condition « if provided » est mal positionnée dans la valeur actuelle; la proposition conserve le champ exact et la rend grammaticale.')
put(901,'zh-Hans','如果提供了 MetadataProfileId，则其值必须大于 0。','correction','La valeur actuelle suit l’ordre anglais et paraît fragmentaire en chinois; la proposition exprime correctement la condition.')
put(901,'zh-Hant','如果有提供 MetadataProfileId，其值必須大於 0。','correction','目前語序直譯英文而不自然；此句保留欄位識別字並清楚表達條件。')
# 903: webhook local/private-network warning.
put(903,'ar','يشير Webhook URL إلى عنوان شبكة محلي أو خاص. هذا مسموح، لكن استخدمه فقط للخدمات الداخلية التي تثق بها.','refinement','يكرر النص الحالي كلمة «عنوان» حول URL؛ هذه الصياغة تزيل التكرار وتحافظ على URL كما يظهر في الواجهة.')
put(903,'es','La URL del webhook se resuelve en una dirección de red local o privada. Esto está permitido, pero úsala solo para servicios internos de confianza.','correction','El valor actual tiene concordancia y construcción defectuosas (“Esto es permitido” y “confíes” sin objeto). La propuesta mantiene URL y el aviso completo.')
put(903,'hi','Webhook URL स्थानीय या निजी नेटवर्क पते पर जाता है। यह अनुमत है, लेकिन इसका उपयोग केवल उन आंतरिक सेवाओं के लिए करें जिन पर आपको भरोसा है।','correction','El valor actual mezcla “resolve” en inglés y su concordancia resulta poco natural; esta versión mantiene el término técnico URL y toda la advertencia.')
put(903,'id','Webhook URL mengarah ke alamat jaringan lokal atau privat. Ini diizinkan, tetapi gunakan hanya untuk layanan internal yang Anda percayai.','correction','La segunda oración actual comienza con minúscula y usa una construcción verbal incorrecta; la propuesta corrige ambos puntos.')
put(903,'pt-BR','A URL do webhook resolve para um endereço de rede local ou privado. Isso é permitido, mas use-a somente em serviços internos nos quais você confia.','correction','A construção atual “A Webhook URL resolve” não é natural em português, e a segunda oração usa voz passiva inadequada; a proposta mantém URL e o sentido.')
# 904: folder-write failure.
put(904,'zh-Hans','无法写入文件夹。','correction','“写到文件夹”不自然 para el error de permisos de escritura; “写入” es el verbo de interfaz habitual.')
put(904,'zh-Hant','無法寫入資料夾。','correction','「寫到文件夾」不自然 para un error de permisos; 「寫入資料夾」 es la forma de interfaz adecuada.')
# 905: required branch name, preserve literal main.
put(905,'id',"Nama cabang wajib diisi; nilai default-nya adalah 'main'.",'refinement','Current wording uses an English default noun without a natural Indonesian construction; this keeps the branch literal exact.')
put(905,'pt-BR',"O nome do ramo é obrigatório; 'main' é o padrão.",'correction','A redação atual omite el artículo y suena traducida literalmente. Se conserva el valor exacto main.')
put(905,'vi',"Bắt buộc phải có tên nhánh; mặc định là 'main'.",'correction','“Tên nhánh được yêu cầu” es una traducción literal poco idiomática; la propuesta expresa claramente que el campo es obligatorio.')
# 906: edition selection not retained.
put(906,'ar','لم يتم الإبقاء على الطبعة المحددة لهذا الكتاب.','correction','“نسخة” puede significar una copia; “الطبعة” expresa mejor la edición bibliográfica de un libro.')
put(906,'hi','इस पुस्तक के लिए चुना गया संस्करण बरकरार नहीं रखा गया।','refinement','La redacción actual es literal y torpe; esta forma conserva el sentido de que el sistema no mantuvo la edición escogida.')
put(906,'id','Edisi yang dipilih tidak dipertahankan untuk buku ini.','correction','“Disimpan” significa guardado en almacenamiento y puede sugerir otra acción; “dipertahankan” corresponde a retained.')
put(906,'ja','選択した版はこの本に保持されませんでした。','correction','「保存」はデータを保存したという意味にも読めます。ここでは選んだ版が書籍に保持されなかったことを示します。')
put(906,'ko','선택한 판이 이 책에 유지되지 않았습니다.','refinement','책의 edition은 “판”으로 자연스럽게 표현할 수 있으며, 현재의 “에디션”보다 짧고 명확합니다.')
put(906,'vi','Ấn bản được chọn không được giữ lại cho cuốn sách này.','refinement','“Ấn bản” es el término bibliográfico más específico para la edición seleccionada de un libro.')
put(906,'zh-Hans','未为此书保留所选版本。','correction','目前的「选择的版未保留为本书」语序生硬且不完整；此句自然地表达未能保留所选版本。')
put(906,'zh-Hant','未為此書保留所選版本。','correction','目前的「選擇的版未保留為本書」語序生硬且不完整；此句自然地表達未能保留所選版本。')
# 908: rate/request limit reached.
put(908,'es','Se alcanzó el límite de solicitudes: {value0}','correction','La traducción actual carece del verbo “se”; la propuesta es una oración completa y conserva el marcador dinámico.')
put(908,'hi','अनुरोध सीमा पूरी हो गई: {value0}','correction','La redacción actual trata la limitación como si fuera el sujeto que llegó; esta frase expresa de forma natural que se agotó el límite.')
put(908,'ja','リクエスト上限に達しました: {value0}','correction','「制限が達成されました」は直訳で不自然です。上限に達したことを表す定型表現にします。')
put(908,'ko','요청 한도에 도달했습니다: {value0}','correction','“한도가 달성되었습니다”는 직역투입니다. 한도에 도달했다는 자연스러운 표현으로 고칩니다.')
put(908,'pt-BR','Limite de solicitações atingido: {value0}','refinement','“Limite de solicitação alcançado” é compreensível, mas a forma nominal “atingido” é mais idiomática neste aviso.')
put(908,'vi','Đã đạt đến giới hạn yêu cầu: {value0}','correction','“Giới hạn yêu cầu đạt” es una frase incompleta; esta versión usa una construcción vietnamita natural y conserva el marcador.')
put(908,'zh-Hans','已达到请求限制：{value0}','correction','当前语序直译英文而不自然；此处使用中文常见的“已达到……限制”表达。')
put(908,'zh-Hant','已達到請求限制：{value0}','correction','目前語序直譯英文而不自然；此處使用中文常見的「已達到……限制」表達。')
# 909: indexer connection detail; preserve ValidationFailure and placeholder.
put(909,'es','No se pudo conectar al indexador. Consulta el registro que aparece encima de ValidationFailure para obtener más detalles. {value0}','correction','La frase actual carece de artículo y suena poco natural. La propuesta mantiene el identificador ValidationFailure y separa el detalle dinámico.')
put(909,'fr','Impossible de se connecter à l’indexeur. Vérifiez le journal au-dessus de ValidationFailure pour plus de détails. {value0}','correction','“Incapable de se connecter” est peu idiomatique ici; cette formulation estándar conserva el nombre técnico y el marcador.')
put(909,'hi','इंडेक्सर से कनेक्ट नहीं हो सका। अधिक जानकारी के लिए ValidationFailure के ऊपर का लॉग देखें। {value0}','correction','La sintaxis actual es literal e incómoda; la propuesta conserva el componente ValidationFailure y separa el mensaje dinámico.')
put(909,'id','Tidak dapat terhubung ke indexer. Periksa log di atas ValidationFailure untuk informasi lebih lanjut. {value0}','correction','La traducción actual une el marcador a la palabra anterior y la frase puede fluir mejor; se conserva ValidationFailure y se añade la separación.')
put(909,'ja','インデクサーに接続できません。詳細は ValidationFailure の上にあるログを確認してください。 {value0}','refinement','例外の詳細が直前の文に連結されて読みにくいため、コード識別子と動的メッセージの間を明確に分けます。')
put(909,'ko','인덱서에 연결할 수 없습니다. 자세한 내용은 ValidationFailure 위의 로그를 확인하세요. {value0}','refinement','현재 값은 예외 세부 정보가 앞 문장에 붙어 읽기 어렵습니다. 식별자와 매개변수를 분리합니다.')
# 910: Series ID not found.
put(910,'ar','لم يتم العثور على سلسلة بالمعرّف {value0}.','correction','الترجمة الحالية مفهومة لكن ترتيب الكلمات غير طبيعي؛ الصياغة المقترحة توضح أن الرقم هو معرّف السلسلة.')
put(910,'de','Serie mit der ID {value0} nicht gefunden.','refinement','Der fehlende Artikel macht die aktuelle Kurzmeldung holprig; die vorgeschlagene Form bleibt knapp und eindeutig.')
put(910,'fr','Série avec l’ID {value0} introuvable.','refinement','La valeur actuelle manque l’article devant ID; cette formulation courte est naturelle pour une réponse 404.')
put(910,'hi','ID {value0} वाली श्रृंखला नहीं मिली।','correction','La forma actual significa “serie con {value0}” y omite el ID; la propuesta expresa la relación exacta.')
put(910,'ko','ID가 {value0}인 시리즈를 찾을 수 없습니다.','correction','현재 문장은 “ID를 가진 시리즈 {value0}”처럼 어순이 어색합니다. 제안문은 ID 값을 명확히 연결합니다.')
put(910,'zh-Hans','未找到 ID 为 {value0} 的系列。','correction','当前语序不符合中文表达；此句清楚地把 ID 值和系列关联起来。')
put(910,'zh-Hant','未找到 ID 為 {value0} 的系列。','correction','目前語序不符合中文表達；此句清楚地將 ID 值與系列連結起來。')
# 913: translate the logical connectors, preserve all exact file-name tokens.
for loc,target in {
 'ar':'يجب أن يحتوي على Book Title وPartNumber، أو Original Title.',
 'de':'Muss Book Title und PartNumber oder Original Title enthalten.',
 'es':'Debe contener Book Title y PartNumber, o bien Original Title.',
 'fr':'Doit contenir Book Title et PartNumber, ou Original Title.',
 'hi':'इसमें Book Title और PartNumber, या Original Title होना चाहिए।',
 'id':'Harus berisi Book Title dan PartNumber, atau Original Title.',
 'ja':'Book Title と PartNumber、または Original Title を含める必要があります。',
 'ko':'Book Title과 PartNumber, 또는 Original Title을 포함해야 합니다.',
 'pt-BR':'Deve conter Book Title e PartNumber, ou Original Title.',
 'vi':'Phải chứa Book Title và PartNumber, hoặc Original Title.',
 'zh-Hans':'必须包含 Book Title 和 PartNumber，或 Original Title。',
 'zh-Hant':'必須包含 Book Title 和 PartNumber，或 Original Title。'
}.items():
 put(913,loc,target,'correction','La validación describe una expresión lógica para los tokens de formato. Se traducen AND/OR para que la condición sea legible y se conservan exactamente Book Title, PartNumber y Original Title.')
# 915: save API token.
put(915,'de','API-Token konnte nicht gespeichert werden. Bitte versuchen Sie es erneut.','correction','La frase actual es un fragmento sin verbo y la oración posterior empieza en minúscula; la propuesta conserva API y completa el mensaje.')
put(915,'es','No se pudo guardar el token de API. Inténtelo de nuevo.','correction','“Salvar” es un calco poco natural para guardar una credencial; esta versión mantiene API y usa el verbo habitual.')
put(915,'hi','API टोकन सहेजने में विफल। कृपया फिर से प्रयास करें।','correction','“बचाने” significa rescatar/proteger en este contexto, no guardar; la propuesta conserva API y usa el verbo de almacenamiento.')
put(915,'id','Gagal menyimpan token API. Silakan coba lagi.','correction','La segunda oración actual comienza en minúscula y la frase mezcla orden y estilo; la propuesta mantiene API.')
put(915,'pt-BR','Falha ao salvar o token de API. Tente novamente.','correction','“Não conseguiu salvar” no identifica un sujeto natural y suena traducido literalmente; la propuesta es el mensaje estándar de fallo.')
# 916: Info notification type.
put(916,'de','Info','refinement','Bei Apprise ist dies die Benachrichtigungskategorie Info; “Informationen” klingt wie eine Mehrzahl von Informationstexten.')
put(916,'fr','Info','refinement','Il s’agit de la catégorie de notification Info d’Apprise; le pluriel « Informations » désigne plutôt plusieurs renseignements.')
put(916,'pt-BR','Informação','refinement','A opção representa o nível de notificação informativo; o singular é mais adequado que “Informações”.')
# 919–920: Deluge/qBittorrent/Transmission/uTorrent queue-position choices.
LAST={'ar':'في النهاية','de':'Zuletzt','es':'Al final','fr':'À la fin','hi':'सूची के अंत में','id':'Paling akhir','ja':'末尾','ko':'맨 뒤','pt-BR':'No fim','vi':'Cuối hàng đợi','zh-Hans':'队列末尾','zh-Hant':'佇列末尾'}
FIRST={'ar':'في البداية','de':'Zuerst','es':'Al principio','fr':'En tête','hi':'सूची की शुरुआत में','id':'Paling awal','ja':'先頭','ko':'맨 앞','pt-BR':'No início','vi':'Đầu hàng đợi','zh-Hans':'队列开头','zh-Hant':'佇列開頭'}
for loc,target in LAST.items(): put(919,loc,target,'refinement','En el enum DelugePriority/QBittorrentPriority/TransmissionPriority/uTorrentPriority, Last significa colocar el elemento al final de la cola; esta opción evita una forma adjetiva incompleta.')
for loc,target in FIRST.items(): put(920,loc,target,'refinement','En el enum DelugePriority/QBittorrentPriority/TransmissionPriority/uTorrentPriority, First significa colocar el elemento al principio de la cola; esta opción expresa la posición.')
# 924–926: priority scale forms.
put(924,'es','Baja','correction','“Prioridad” es femenino en español; el valor actual usa el masculino “bajo”.')
put(924,'ko','낮음','refinement','현재 “낮은”은 뒤에 명사가 오는 관형형입니다. 선택 항목에는 명사형 “낮음”이 자연스럽습니다.')
put(925,'ko','보통','refinement','현재 “정상적인”은 명사를 수식하는 형용사입니다. 우선순위 값에는 “보통”이 자연스럽습니다.')
put(926,'ar','مرتفعة','correction','“أعلى” تعني higher وليس high؛ هنا مستوى أولوية مرتفع.')
put(926,'de','Hoch','correction','Die aktuelle Form “hohe” braucht ein folgendes Nomen; als eigenständige Auswahlstufe lautet sie “Hoch”.')
put(926,'ko','높음','refinement','현재 “높은”은 뒤에 명사가 오는 관형형입니다. 선택 항목에는 명사형 “높음”이 자연스럽습니다.')
put(926,'pt-BR','Alta','correction','“Prioridade” é feminino em português; a forma atual usa o masculino “alto”.')
# 929: release flag counts uploaded credit twice.
put(929,'es','Subida contabilizada el doble','correction','“Dupla subida” describe dos subidas, no el crédito de upload contado en dobro.')
put(929,'pt-BR','Upload em dobro','refinement','“Duplo upload” pode parecer dois envios; esta forma curta expressa o crédito de upload duplicado.')
# 931: Scene is the proper release-group category in IndexerFlags.
put(931,'ar','إصدار من مجموعة Scene','correction','في هذا السياق Scene اسم فئة لمجموعة إصدار، وليس مشهدًا من فيلم؛ نحافظ على المصطلح ونوضح المقصود.')
put(931,'es','Lanzamiento del grupo Scene','correction','“Escena” parece referirse a una escena audiovisual; el caller define Scene como grupo de publicación y conviene conservar el nombre del término.')
put(931,'fr','Sortie du groupe Scene','correction','Le caller indique que Scene est un groupe de publication, pas une scène audiovisuelle; le nom de catégorie reste inchangé.')
put(931,'hi','Scene समूह की रिलीज़','correction','Caller में Scene torrent release-group श्रेणी है, दृश्य नहीं; सही तकनीकी नाम को जस का तस रखा गया है।')
put(931,'ko','Scene 그룹 릴리스','correction','호출부에서 Scene은 토렌트 릴리스 그룹 범주입니다. 현재 “장면”은 영상의 한 장면이라는 뜻이므로 용어를 보존합니다.')
put(931,'pt-BR','Lançamento do grupo Scene','correction','“A cena” indica uma cena audiovisual; o código define Scene como grupo de lançamento, então o termo deve ser preservado.')
# 934: VIP-exclusive flag.
put(934,'hi','केवल VIP सदस्यों के लिए','correction','El valor actual está en chino y no en hindi; la propuesta conserva exactamente VIP.')
put(934,'ja','VIP限定','refinement','「VIP 独占」は独占権の意味にも読めるため、対象が VIP のみに限定されることを短く示します。')
put(934,'ko','VIP 전용','correction','“독점”은 독점권/시장 독점의 뉘앙스가 있습니다. 이 플래그는 VIP 전용 콘텐츠라는 뜻입니다.')
put(934,'pt-BR','Exclusivo para VIP','refinement','A ordem atual soa como um adjetivo solto; esta forma diz claramente que o torrent é exclusivo para VIP.')
# 936–937: Silent and Quiet notification-priority labels (distinct enum levels).
put(936,'ko','무음','correction','현재 Silent와 Quiet가 모두 “조용한”으로 번역되어 두 우선순위 값을 구분하지 못합니다.')
put(937,'ko','조용함','correction','현재 Quiet와 Silent가 모두 “조용한”으로 같아 서로 다른 enum 옵션이 구분되지 않습니다.')
# 938: Emergency notification level.
put(938,'id','Darurat','correction','“Kecemasan” berarti kecemasan/perasaan cemas; untuk tingkat pemberitahuan Emergency, gunakan “Darurat”.')
# 942: MAM preference action.
put(942,'ar','اتبع تفضيلات MAM','refinement','الترتيب الحالي غير طبيعي؛ الصياغة المقترحة تجعل MAM مضافًا إليه للتفضيلات.')
put(942,'de','MAM-Einstellungen folgen','correction','“Folgen Sie MAM Präferenzen” lacks the required article/case in German; the compound retains MAM exactly.')
put(942,'ja','MAMの設定に従う','refinement','「好みをフォローする」は口語的な借用表現です。設定項目に従うという自然なUI表現にします。')
# 947: action when required MAM freeleech cannot be applied.
put(947,'fr','La récupération échoue si MAM ne peut pas appliquer l’avantage Freeleech personnel requis.','correction','« Échouez la récupération » est une injonction française maladroite; la proposition décrit clairement le comportement du système et garde MAM.')
put(947,'ja','MAM が必要な個人用 Freeleech 特典を適用できない場合は、取得処理を失敗として扱います。','refinement','「取得を失敗させる」は不自然な使役です。システムが取得処理を失敗扱いにする意味を明確にします。')
put(947,'pt-BR','A aquisição falhará se MAM não puder aplicar o benefício Freeleech pessoal obrigatório.','refinement','“Falhe a solicitação” é uma instrução pouco natural para uma configuração; esta frase descreve o resultado do grab e mantém MAM.')
# 949: Afrikaans language name in Simplified Chinese.
put(949,'zh-Hans','南非荷兰语','correction','“南非语”泛指南非的语言，不是 Afrikaans 的专名；“南非荷兰语”可准确指称该语言。')

WHY={
 900:'The proposed wording uses natural software terminology and correct locale grammar for a global delay profile.',
 901:'The conditional numeric validation is expressed naturally while preserving the exact MetadataProfileId field name.',
 903:'The proposal corrects locale-specific grammar in the webhook warning while preserving URL and the internal-service trust condition.',
 904:'The proposal uses the standard software term for being unable to write to a folder.',
 905:'The branch-name requirement is phrased naturally and preserves the exact default branch literal main.',
 906:'The proposal uses the locale term for a book edition and clearly states that the selected edition was not retained.',
 908:'The proposal gives a natural request-limit error and preserves the dynamic value0 detail.',
 909:'The connection error is phrased naturally, keeps the ValidationFailure identifier, and separates the dynamic value0 detail.',
 910:'The proposal clearly associates value0 with the Series ID and preserves the dynamic placeholder.',
 913:'The natural-language Boolean connectors are translated while the exact format tokens Book Title, PartNumber, and Original Title remain unchanged.',
 915:'The save failure uses natural credential terminology and punctuation while preserving the exact API literal.',
 916:'The option names Apprise’s informational notification category with a natural concise label.',
 919:'The pinned download-client enums use Last for adding an item at the end of the queue; the proposal states that position directly.',
 920:'The pinned download-client enums use First for adding an item at the beginning of the queue; the proposal states that position directly.',
 924:'The priority label uses the locale form appropriate for a standalone low-priority option.',
 925:'The priority label uses a natural standalone locale term for the normal level.',
 926:'The priority label uses the locale form appropriate for a standalone high-priority option.',
 929:'The tracker flag means upload credit is counted twice; the proposal avoids wording that could mean two separate uploads.',
 931:'The caller defines Scene as a torrent release-group category, so the proposal preserves Scene instead of translating it as an audiovisual scene.',
 934:'The proposal clearly identifies VIP-only release access while preserving the exact VIP literal.',
 936:'The current Korean values for Silent and Quiet are identical; this proposal restores the distinction between the two enum options.',
 937:'The current Korean values for Quiet and Silent are identical; this proposal restores the distinction between the two enum options.',
 938:'The Indonesian proposal uses the word for an emergency notification level rather than anxiety.',
 942:'The proposal expresses following MAM account preferences naturally while preserving the exact MAM name.',
 947:'The hint describes what happens when MAM cannot apply the required personal Freeleech feature; the proposal states that behavior naturally.',
 949:'The proposal uses the name of Afrikaans rather than a generic term for a South African language.'
}
assert all(900<=o<=949 and loc in LOCALES for o,loc in C)
assert len(C)==len(set(C))
input_rows=readjl('input-cells.jsonl'); sources=readjl('source-slice.jsonl'); callers=readjl('caller-context.jsonl')
assert len(input_rows)==600 and len(sources)==50 and len(callers)==50
context={x['sourceId']:x for x in callers}
source_rows={x['sourceId']:x for x in sources}
review=[]; audit=[]
for cell in sorted(input_rows,key=lambda x:(x['sourceOrdinal'],LOCALES.index(x['locale']))):
 o=cell['sourceOrdinal']; loc=cell['locale']; src=cell['source']; cur=cell['currentTarget']; item=C.get((o,loc))
 if item:
  disp=item['kind']; rec=item['target']; rationale=WHY.get(o,item['why']); final=rec
 else:
  disp='accept-current'; rec=None; final=cur
  rationale='Current target preserves the source meaning in this locale in the pinned caller/provider-option context; no correction is needed in this static pass.'
 assert disp in {'accept-current','correction','refinement'}
 rec_ph=placeholders(rec) if rec is not None else cell['currentTargetPlaceholders']
 rec_markup=markup(rec) if rec is not None else cell['currentTargetMarkup']
 protected=cell['protectedLiterals']
 current_checks=[{'literal':lit,'present':lit in cur} for lit in protected]
 rec_checks=[{'literal':lit,'present':lit in (rec if rec is not None else cur)} for lit in protected]
 final_checks=[{'literal':lit,'present':lit in final} for lit in protected]
 structural={'sourcePlaceholders':placeholders(src),'currentPlaceholders':placeholders(cur),'recommendedPlaceholders':rec_ph,'finalPlaceholders':placeholders(final) if final is not None else None,'sourceMarkup':markup(src),'currentMarkup':markup(cur),'recommendedMarkup':rec_markup,'finalMarkup':markup(final) if final is not None else None,'currentPlaceholderParity':placeholders(src)==placeholders(cur),'recommendedPlaceholderParity':rec is None or placeholders(src)==rec_ph,'currentMarkupParity':markup(src)==markup(cur),'recommendedMarkupParity':rec is None or markup(src)==rec_markup,'currentProtectedLiteralChecks':current_checks,'recommendedProtectedLiteralChecks':rec_checks,'finalProtectedLiteralChecks':final_checks,'currentProtectedLiteralFailures':[x['literal'] for x in current_checks if not x['present']],'recommendedProtectedLiteralFailures':[x['literal'] for x in rec_checks if not x['present']],'finalProtectedLiteralFailures':[x['literal'] for x in final_checks if not x['present']]}
 assert structural['currentPlaceholderParity'] and structural['currentMarkupParity']
 assert structural['recommendedPlaceholderParity'] and structural['recommendedMarkupParity']
 assert not structural['recommendedProtectedLiteralFailures'] and not structural['finalProtectedLiteralFailures'],(o,loc,structural)
 assert not structural['currentProtectedLiteralFailures'] or rec is not None,(o,loc,structural)
 assert rec is None or rec!=cur
 ctx=context[cell['sourceId']]
 row={**cell,'disposition':disp,'recommendedTarget':rec,'recommendedTargetSha256':sha(rec) if rec is not None else None,'finalTarget':final,'finalTargetSha256':sha(final) if final is not None else None,'decisionRationale':rationale,'reviewConfidence':CONF[loc],'pinnedCallerReferenceCount':ctx['callerReferenceCount'],'callerRefs':ctx['directCallerReferences'],'callerContextSha256':ctx['callerContextSha256'],'callerReferenceStatus':ctx['callerReferenceStatus'],'structuralChecks':structural,'candidateSourceRegistryContext':source_rows[cell['sourceId']]['registrySurface'] or source_rows[cell['sourceId']]['registryCategory']}
 review.append(row)
 audit.append({'sourceOrdinal':o,'sourceId':cell['sourceId'],'locale':loc,'languageAuditDisposition':disp,'currentTargetSha256':cell['currentTargetSha256'],'reviewedCurrentTarget':cur,'recommendedTarget':rec,'recommendedTargetSha256':sha(rec) if rec is not None else None,'finalTarget':final,'finalTargetSha256':sha(final) if final is not None else None,'rationale':rationale,'confidence':CONF[loc],'placeholdersPreserved':structural['recommendedPlaceholderParity'],'markupPreserved':structural['recommendedMarkupParity'],'protectedLiteralsPreserved':not structural['finalProtectedLiteralFailures'],'callerContextSha256':ctx['callerContextSha256']})
assert len(review)==len(audit)==600 and set((x['sourceOrdinal'],x['locale']) for x in review)==set((x['sourceOrdinal'],x['locale']) for x in input_rows)
counts=collections.Counter(x['disposition'] for x in review)
per_locale={loc:dict(collections.Counter(x['disposition'] for x in review if x['locale']==loc)) for loc in LOCALES}
summary={'exactHead':json.loads((OUT/'input-manifest.json').read_text())['head'],'exactTree':json.loads((OUT/'input-manifest.json').read_text())['tree'],'window':'W900-W949','sourcePositions':[900,949],'sourceCount':50,'localeCells':600,'locales':LOCALES,'dispositionCounts':dict(sorted(counts.items())),'perLocaleDispositionCounts':per_locale,'candidateCount':counts['correction']+counts['refinement'],'correctionCandidates':counts['correction'],'refinementCandidates':counts['refinement'],'holdCount':counts['hold'],'acceptedCurrent':counts['accept-current'],'placeholderMismatchCells':sum(not x['structuralChecks']['recommendedPlaceholderParity'] for x in review),'markupMismatchCells':sum(not x['structuralChecks']['recommendedMarkupParity'] for x in review),'currentProtectedLiteralFailureCells':sum(bool(x['structuralChecks']['currentProtectedLiteralFailures']) for x in review),'recommendedProtectedLiteralFailureCells':sum(bool(x['structuralChecks']['recommendedProtectedLiteralFailures']) for x in review),'finalProtectedLiteralFailureCells':sum(bool(x['structuralChecks']['finalProtectedLiteralFailures']) for x in review),'sourceCallerRows':len(callers),'sourceCallerReferences':sum(x['callerReferenceCount'] for x in callers),'sourceCallerGaps':sum(x['callerReferenceStatus']!='pinned' for x in callers),'serverMessagePipelineReferences':len(readjl('server-message-pipeline-context.jsonl')),'providerOptionPipelineReferences':len(readjl('provider-option-pipeline-context.jsonl')),'nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True,'machineAssistedConfidence':'moderate','scopeLimitation':'Static primary semantic pass. No native-speaker or browser/runtime approval claimed.'}
assert counts['hold']==0
assert summary['placeholderMismatchCells']==summary['markupMismatchCells']==summary['recommendedProtectedLiteralFailureCells']==summary['finalProtectedLiteralFailureCells']==0
writejl('review-cells.jsonl',review); writejl('language-audit.jsonl',audit)
writejl('correction-candidates.jsonl',[x for x in review if x['disposition']=='correction'])
writejl('refinement-candidates.jsonl',[x for x in review if x['disposition']=='refinement'])
(OUT/'manual-protected-literals.json').write_text(json.dumps({'bySourceId':{x['sourceId']:x['manualProtectedLiterals'] for x in sources if x['manualProtectedLiterals']},'sourceRegistryLiteralsAlsoApplied':True,'basis':'Exact identifiers, flag names, and UI tokens retained from pinned caller context.'},ensure_ascii=False,indent=2,sort_keys=True)+'\n')
writejl('protected-literal-integrity.jsonl',[{'sourceOrdinal':x['sourceOrdinal'],'sourceId':x['sourceId'],'locale':x['locale'],'sourceTextSha256':x['sourceTextSha256'],'currentTargetSha256':x['currentTargetSha256'],'disposition':x['disposition'],'recommendedTargetSha256':x['recommendedTargetSha256'],'finalTargetSha256':x['finalTargetSha256'],'protectedLiterals':x['protectedLiterals'],'checks':x['structuralChecks']} for x in review])
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
