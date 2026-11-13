import json,pathlib,subprocess,hashlib
O=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0650-0699-primary-20261102')
R='/mnt/disks/scratch/task-worktrees/localization-20261102/chaptarrng-pr190-readonly-0650-0699-4701933'
LOCS=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
C={
650:{
'ja':"パス '{value0}' は、すでにルートフォルダーとして設定されています。",
'ko':"경로 '{value0}'은(는) 이미 루트 폴더로 설정되어 있습니다。"},
651:{
'de':'Verbindung zum Kavita-Server nicht möglich.',
'ja':'Kavita サーバーに接続できません。',
'pt-BR':'Não foi possível conectar ao servidor Kavita.',
'ar':'تعذّر الاتصال بخادم Kavita.'},
652:{
'es':'Se requiere un ID de usuario de Goodreads o unas credenciales OAuth existentes.',
'zh-Hans':'需要 Goodreads 用户 ID 或现有 OAuth 凭据。',
'zh-Hant':'需要 Goodreads 使用者 ID 或現有 OAuth 認證資料。',
'pt-BR':'É necessário informar o ID de usuário do Goodreads ou credenciais OAuth existentes.',
'ar':'يلزم إدخال معرّف مستخدم Goodreads أو بيانات اعتماد OAuth موجودة.'},
654:{
'es':"Desactiva la opción 'Check before download' en SABnzbd.",
'zh-Hans':'在 SABnzbd 中禁用“Check before download”选项。',
'hi':"SABnzbd में 'Check before download' विकल्प को अक्षम करें।",
'de':'Deaktivieren Sie die Option \"Check before download\" in SABnzbd.',
'ja':"SABnzbd で 'Check before download' オプションを無効にしてください。",
'fr':'Désactivez l’option « Check before download » dans SABnzbd.',
'pt-BR':"Desative a opção 'Check before download' no SABnzbd.",
'ar':"عطّل خيار 'Check before download' في SABnzbd.",
'ko':"SABnzbd에서 'Check before download' 옵션을 비활성화하세요.",
'zh-Hant':'在 SABnzbd 中停用「Check before download」選項。',
'vi':"Tắt tùy chọn 'Check before download' trong SABnzbd.",
'id':"Nonaktifkan opsi 'Check before download' di SABnzbd."},
659:{
'ja':'電子書籍を監視する場合は、電子書籍のルートフォルダーが必要です。',
'ko':'전자책을 모니터링하려면 전자책 루트 폴더가 필요합니다.'},
671:{
'fr':'Impossible de récupérer l’utilisateur Hardcover actuel.'},
672:{
'de':'Chaptarr wird gestartet. Bitte versuchen Sie es später erneut.',
'ja':'Chaptarr は起動中です。後でもう一度お試しください。',
'fr':'Chaptarr démarre. Veuillez réessayer plus tard.',
'ko':'Chaptarr가 시작 중입니다. 나중에 다시 시도하세요.',
'zh-Hans':'Chaptarr 正在启动，请稍后再试。',
'zh-Hant':'Chaptarr 正在啟動，請稍後再試。',
'vi':'Chaptarr đang khởi động, vui lòng thử lại sau.',
'ar':'Chaptarr قيد بدء التشغيل، يُرجى المحاولة مرة أخرى لاحقًا.'},
677:{
'es':'Formatos de salida no válidos.',
'zh-Hans':'输出格式无效。',
'zh-Hant':'輸出格式無效。',
'ja':'出力形式が無効です。'},
678:{
'es':'No se pudo conectar a BookOrbit. Comprueba la URL, las credenciales y los registros.',
'zh-Hans':'无法连接到 BookOrbit。请检查 URL、凭据和日志。',
'zh-Hant':'無法連接到 BookOrbit。請檢查 URL、認證資料和日誌。',
'ja':'BookOrbitに接続できません。URL、認証情報、ログを確認してください。',
'fr':'Impossible de se connecter à BookOrbit. Vérifiez l’URL, les identifiants et les journaux.',
'pt-BR':'Não foi possível conectar ao BookOrbit. Verifique a URL, as credenciais e os logs.'},
680:{
'es':'No es un dispositivo Synology o synoindex no está disponible.',
'zh-Hans':'这不是 Synology 设备，或者 synoindex 不可用。',
'hi':'यह Synology डिवाइस नहीं है या synoindex उपलब्ध नहीं है।',
'de':'Dies ist kein Synology-Gerät oder synoindex ist nicht verfügbar.',
'ja':'Synology製デバイスではないか、synoindexを利用できません。',
'fr':'Ce n’est pas un appareil Synology, ou synoindex n’est pas disponible.',
'pt-BR':'Não é um dispositivo Synology ou o synoindex não está disponível.',
'ar':'هذا ليس جهاز Synology أو أن synoindex غير متاح.',
'ko':'Synology 장치가 아니거나 synoindex를 사용할 수 없습니다.',
'zh-Hant':'這不是 Synology 裝置，或 synoindex 無法使用。',
'vi':'Không phải thiết bị Synology hoặc synoindex không khả dụng.',
'id':'Bukan perangkat Synology atau synoindex tidak tersedia.'},
683:{
'es':'No se encontró la edición seleccionada {value0}: {value1}',
'zh-Hant':'找不到所選版本 {value0}：{value1}',
'hi':'चयनित संस्करण {value0} नहीं मिला: {value1}',
'fr':'L’édition sélectionnée {value0} est introuvable : {value1}',
'pt-BR':'A edição selecionada {value0} não foi encontrada: {value1}',
'ar':'تعذّر العثور على الإصدار المحدد {value0}: {value1}',
'ko':'선택한 에디션 {value0}을(를) 찾을 수 없습니다: {value1}'},
687:{
'ar':'يجب ألا تكون كلمة المرور فارغة.',
'ko':'비밀번호는 비어 있으면 안 됩니다.',
'vi':'Mật khẩu không được để trống.'},
688:{
'hi':"मेटाडेटा सर्वर में आवश्यक क्षमता '{value0}' उपलब्ध नहीं है।",
'ko':"메타데이터 서버에 필요한 기능 '{value0}'가 없습니다.",
'vi':"Máy chủ siêu dữ liệu thiếu tính năng bắt buộc '{value0}'."},
691:{
'vi':"Dịch vụ máy chủ siêu dữ liệu '{value0}' không như mong đợi (giá trị mong đợi là '{value1}')."},
692:{
'fr':'La clé API n’est pas valide.',
'id':'Kunci API tidak valid.'}
}
WHY={
650:"This is a path-validation error for a duplicate root folder; Japanese/Korean current wording uses a literal plant-root term rather than the filesystem root-folder term.",
651:"This connection failure identifies the Kavita server; German is ungrammatical and Japanese/Portuguese/Arabic use awkward literal structures.",
652:"The validation accepts either a Goodreads user ID or already existing OAuth credentials; candidates repair word order and missing required semantics.",
654:"The production caller is Sabnzbd.cs and the setting is SABnzbd's exact “Check before download” option. The English source misspells the product as Sabnbzd; candidates use the product's verified spelling while preserving the option label.",
659:"This configuration validation requires an ebook root folder for ebook monitoring; Japanese and Korean currently leave the core UI term in English.",
671:"This is a Hardcover connection/user lookup failure; French current text lacks a grammatical subject.",
672:"This middleware status says Chaptarr is currently starting and asks the user to retry later; several current translations say it is only about to start or are fragments.",
677:"This validation rejects output-format values; the Chinese targets use “unqualified” rather than “invalid”, and Spanish/Japanese current phrasing is awkward.",
678:"This BookOrbit connection message instructs the user to check the URL, credentials, and logs; Japanese current text is missing a sentence break and imperative.",
680:"The Synology indexer requires a Synology system or an available synoindex utility; current translations preserve an English double-negative construction that is hard to understand.",
683:"This manual-import error reports that a selected edition could not be found and appends the underlying reason; candidates correct missing articles and broken phrasing while preserving both values.",
687:"This validation requires a nonempty password; current Arabic/Korean/Vietnamese wording is grammatically weak or overly literal.",
688:"The metadata server lacks a required capability; candidates restore the missing-feature sense and preserve the capability value.",
691:"This reports an unexpected metadata-service name and the expected name; the current Vietnamese translation mistranslates “expected”.",
692:"This API-key validation says the key is invalid; current French/Indonesian word order is unnatural."
}
# Additional obvious grammar, terminology, and API-validation fixes found while reviewing all 600 current cells.
EXTRA_TARGETS={
663:{'ar':"تعذّر الاتصال بواجهة Apprise API. فشل الاتصال بالخادم: ({value0}) {value1}",'vi':"Không thể kết nối với Apprise API. Kết nối máy chủ thất bại: ({value0}) {value1}",'id':"Tidak dapat terhubung ke Apprise API. Koneksi server gagal: ({value0}) {value1}"},
664:{'hi':'स्क्रिप्ट कोड {value0} के साथ समाप्त हुई।','ar':'انتهى البرنامج النصي برمز الخروج: {value0}.'},
667:{'fr':'Impossible de se connecter à l’API Join. Veuillez réessayer plus tard.','vi':'Không thể kết nối với Join API. Vui lòng thử lại sau.','id':'Tidak dapat terhubung ke Join API. Silakan coba lagi nanti.'},
668:{'es':'No se encontró en Grimmory la biblioteca de libros electrónicos seleccionada.'},
670:{'ar':'لا يمكن أن تحتوي المجلدات المخصصة للكتب الإلكترونية فقط على إعدادات الكتب الصوتية.'},
673:{'zh-Hans':'至少需要一个媒体库。','zh-Hant':'至少需要一個媒體庫。'},
675:{'ja':'ファイルが存在しません。','ko':'파일이 존재하지 않습니다.'},
676:{'id':'Versi Aria2 harus minimal 1.34.0. Versi yang dilaporkan adalah {value0}.'},
682:{'de':'Es muss entweder authorId oder bookId angegeben werden.','fr':'L’un des champs authorId ou bookId doit être renseigné.','ar':'يجب تحديد authorId أو bookId.'},
688:{'es':"Al servidor de metadatos le falta la capacidad requerida '{value0}'.",'fr':"Le serveur de métadonnées ne dispose pas de la fonctionnalité requise '{value0}'.",'pt-BR':"O servidor de metadados não tem o recurso obrigatório '{value0}'.",'ar':"يفتقر خادم البيانات الوصفية إلى الإمكانية المطلوبة '{value0}'."},
690:{'pt-BR':"'{value0}' foi adicionado à biblioteca com sucesso.",'vi':"Đã thêm thành công '{value0}' vào thư viện."},
696:{'ja':'APIキーを使用する場合、パスワードは空欄にしてください。','ar':'عند استخدام مفتاح API، يجب أن تكون كلمة المرور فارغة.','ko':'API 키를 사용할 때 암호는 비워 두어야 합니다.'}
}
EXTRA_RATIONALE={
663:'The source contains a two-part Apprise API/server connection error; these revisions repair missing articles, sentence casing, and awkward failure wording while preserving both diagnostic placeholders.',
664:'The source reports a script exit code; these revisions restore idiomatic status wording and keep the exit-code placeholder intact.',
667:'The source is a Join API connection failure with a retry instruction; these revisions correct incomplete or unidiomatic target phrasing.',
668:'The message is specifically about an ebook library in Grimmory; the Spanish target omitted the ebook qualifier.',
670:'This validation prohibits audiobook settings on folders reserved for ebooks; the Arabic target had awkward agreement and word order.',
673:'The caller requires a Chaptarr media library; Chinese targets used a word that can mean a physical library, so these name the software media library directly.',
675:'This is a file-existence error; the Japanese and Korean targets used unnatural or blunt negative forms.',
676:'The Indonesian target had a lowercase second sentence and an unnatural version phrase; the revision preserves aria2, minimum version, and reported-version placeholder.',
682:'The API validation requires either authorId or bookId; these revisions correct agreement/coordination while preserving field names.',
688:'The server lacks a required capability; these revisions fix awkward “missing capability” syntax while preserving the capability placeholder.',
690:'This is a success notification for adding a named item to the library; these revisions use natural subject/verb order.',
696:'The validation requires the password field to remain empty when API-key auth is used; these revisions improve sentence structure and agreement.'
}

# Exact-locale review plan; candidate strings are later validated against live sources and target inventories.
plan={}
for pos,by in C.items():
 for loc,target in by.items():
  assert loc in LOCS
  plan[f'{pos}|{loc}']={'disposition':'propose-correction','recommendedTarget':target,'rationale':WHY[pos],'confidence':'high' if pos not in (654,680,683) else 'moderate'}
for pos,by in EXTRA_TARGETS.items():
 for loc,target in by.items():
  plan[f'{pos}|{loc}']={'disposition':'propose-correction','recommendedTarget':target,'rationale':EXTRA_RATIONALE[pos],'confidence':'moderate'}
(O/'review-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
print('candidate cells',len(plan),'source positions',len(C),'out',O/'review-plan.json')
