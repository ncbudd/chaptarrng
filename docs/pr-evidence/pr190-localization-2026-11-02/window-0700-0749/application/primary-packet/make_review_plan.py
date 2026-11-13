import hashlib,json,pathlib
import re

OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0700-0749-primary-20261102')
LOCALES=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
def placeholders(s): return sorted(set(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s)))
def markup(s):
 if re.fullmatch(r'<[^<>/]+>',s): return []
 return re.findall(r'</?[A-Za-z][^>]*>',s)

# Manual technical literals supplement the server-message source registry.
EXTRA_PROTECTED={
 703:['https://','localhost'], 713:['ProviderId'],
 717:['Both'], 718:['.zip','.db','.xml','.enc','.zip.enc'],
 719:['a-z','0-9','-'], 721:['mam_id','MAM'],
 727:['https://manual.calibre-ebook.com/server.html'],
 731:['*','IP'], 736:['selectedMediaType'],
 740:['OpenLibrary','GoogleBooks'], 748:['author/media-move'],
}

C={
700:{
 'fr':"Impossible de se connecter à l’indexeur. Consultez le journal pour plus de détails.",
 'zh-Hans':'无法连接到索引器，请查看日志了解详情。',
 'zh-Hant':'無法連接到索引器，請查看日誌以了解詳細資訊。',
},
701:{
 'hi':'इस स्थानांतरण में विरोधाभास हैं या स्थानांतरित करने के लिए कोई फ़ाइल नहीं है।',
 'de':'Bei diesem Verschiebevorgang gibt es Konflikte oder keine verschiebbaren Dateien.',
 'zh-Hans':'此移动操作存在冲突，或没有可移动的文件。',
 'zh-Hant':'此移動作業有衝突，或沒有可移動的檔案。',
 'ko':'이 이동 작업에 충돌이 있거나 이동할 수 있는 파일이 없습니다.',
},
702:{
 'de':'Verbindung konnte nicht hergestellt werden.',
 'fr':'Connexion impossible.',
 'ja':'接続できませんでした。',
 'pt-BR':'Não foi possível estabelecer a conexão.',
},
703:{'pt-BR':'É necessário usar https://, a menos que o provedor esteja sendo executado em localhost.'},
704:{
 'ja':'ユーザー名またはパスワードが無効です。',
 'zh-Hant':'使用者名稱或密碼無效。',
},
705:{
 'de':'Auf dem AudioBookShelf-Server wurden keine Bibliotheken gefunden.',
 'hi':'AudioBookShelf सर्वर पर कोई मीडिया लाइब्रेरी नहीं मिली।',
 'zh-Hans':'未在 AudioBookShelf 服务器上找到媒体库。',
 'zh-Hant':'在 AudioBookShelf 伺服器上找不到媒體庫。',
},
706:{
 'zh-Hans':'身份验证失败，请检查 API 密钥。',
 'zh-Hant':'驗證失敗，請檢查 API 金鑰。',
 'ko':'인증에 실패했습니다. API 키를 확인하세요.',
},
707:{
 'es':'No se pudo obtener la lista de NZBs: {value0}',
 'zh-Hans':'获取 NZBs 列表失败：{value0}',
 'de':'Die Liste der NZBs konnte nicht abgerufen werden: {value0}',
 'ja':'NZBsの一覧を取得できませんでした: {value0}',
 'fr':'Impossible de récupérer la liste des NZBs : {value0}',
 'pt-BR':'Não foi possível obter a lista de NZBs: {value0}',
 'ar':'تعذّر الحصول على قائمة NZBs: {value0}',
 'ko':'NZBs 목록을 가져오지 못했습니다: {value0}',
 'zh-Hant':'無法取得 NZBs 清單：{value0}',
 'vi':'Không thể lấy danh sách NZBs: {value0}',
},
708:{
 'de':'Ein Passwort ist erforderlich, wenn kein API-Schlüssel konfiguriert ist.',
 'zh-Hans':'未配置 API 密钥时必须提供密码。',
 'zh-Hant':'未設定 API 金鑰時，必須提供密碼。',
 'pt-BR':'A senha é obrigatória quando a chave de API não está configurada.',
 'vi':'Cần có mật khẩu khi chưa cấu hình khóa API.',
},
709:{
 'es':'Actualmente, solo se admite el proveedor Hardcover para buscar series.',
 'de':'Für die Suche nach Buchreihen wird derzeit nur Hardcover als Anbieter unterstützt.',
 'ja':'シリーズ検索で現在サポートされているプロバイダーは Hardcover のみです。',
 'fr':'Seul le fournisseur Hardcover est actuellement pris en charge pour la recherche de séries.',
 'ar':'حاليًا، لا يدعم البحث عن سلاسل الكتب إلا مزوّد Hardcover.',
 'ko':'현재 시리즈 조회는 Hardcover 제공자만 지원합니다.',
 'vi':'Hiện tại, chỉ hỗ trợ nhà cung cấp Hardcover để tra cứu bộ sách.',
},
710:{'ja':'SSL証明書ファイルまたはパスワードが無効です。'},
711:{'zh-Hans':'群组不存在。','zh-Hant':'群組不存在。'},
715:{
 'es':'Es necesario actualizar NZBVortex.',
 'ja':'NZBVortex を更新する必要があります。',
 'ar':'يجب تحديث NZBVortex.',
},
716:{'vi':'Tác giả này chưa được thiết lập hồ sơ siêu dữ liệu sách điện tử (sách điện tử đang bị tắt). Hãy thiết lập hồ sơ siêu dữ liệu sách điện tử để thêm sách điện tử.'},
717:{
 'es':'El valor de «Se aplica a» debe ser Both, Audiobook o Ebook.',
 'zh-Hans':'“适用范围”的值必须是 Both、Audiobook 或 Ebook。',
 'hi':'“लागू होने का दायरा” Both, Audiobook या Ebook में से एक होना चाहिए।',
 'de':'Der Wert von „Gilt für“ muss Both, Audiobook oder Ebook sein.',
 'ja':'「適用対象」の値は Both、Audiobook、Ebook のいずれかである必要があります。',
 'fr':'La valeur de « S’applique à » doit être Both, Audiobook ou Ebook.',
 'pt-BR':'O valor de “Aplica-se a” deve ser Both, Audiobook ou Ebook.',
 'ar':'يجب أن تكون قيمة «ينطبق على» هي Both أو Audiobook أو Ebook.',
 'ko':'적용 대상 값은 Both, Audiobook 또는 Ebook이어야 합니다.',
 'zh-Hant':'「適用範圍」的值必須是 Both、Audiobook 或 Ebook。',
 'vi':'Giá trị của “Áp dụng cho” phải là Both, Audiobook hoặc Ebook.',
 'id':'Nilai “Berlaku untuk” harus Both, Audiobook, atau Ebook.',
},
718:{
 'es':'Extensión no válida. Debe ser .zip, .db, .xml, .enc o .zip.enc.',
 'zh-Hans':'文件扩展名无效，必须是 .zip、.db、.xml、.enc 或 .zip.enc。',
 'ja':'ファイル拡張子が無効です。.zip、.db、.xml、.enc、.zip.enc のいずれかを指定してください。',
 'fr':'Extension non valide : elle doit être .zip, .db, .xml, .enc ou .zip.enc.',
 'pt-BR':'Extensão inválida. Deve ser .zip, .db, .xml, .enc ou .zip.enc.',
 'ko':'파일 확장자가 올바르지 않습니다. .zip, .db, .xml, .enc, .zip.enc 중 하나여야 합니다.',
 'zh-Hant':'檔案副檔名無效，必須是 .zip、.db、.xml、.enc 或 .zip.enc。',
 'vi':'Phần mở rộng không hợp lệ; phải là .zip, .db, .xml, .enc hoặc .zip.enc.',
 'id':'Ekstensi tidak valid. Ekstensi yang diperbolehkan: .zip, .db, .xml, .enc, .zip.enc.',
},
719:{
 'hi':'अनुमत वर्ण: a-z, 0-9 और -.',
 'fr':'Caractères autorisés : a-z, 0-9 et -.',
 'pt-BR':'Os caracteres permitidos são a-z, 0-9 e -.',
 'ko':'허용되는 문자는 a-z, 0-9, -입니다.',
 'id':'Karakter yang diizinkan: a-z, 0-9, dan -.',
},
720:{
 'es':'No se pudo enviar el mensaje de prueba: {value0}',
 'de':'Die Testnachricht konnte nicht gesendet werden: {value0}',
 'ja':'テストメッセージを送信できませんでした: {value0}',
 'pt-BR':'Não foi possível enviar a mensagem de teste: {value0}',
 'ar':'تعذّر إرسال رسالة الاختبار: {value0}',
 'ko':'테스트 메시지를 보낼 수 없습니다: {value0}',
},
721:{'id':'Autentikasi gagal. Pastikan mam_id Anda benar (dapat ditemukan di Preferences > Security on MAM). Jika menggunakan proxy, pastikan proxy telah dikonfigurasi di Settings > General > Proxy.'},
722:{'zh-Hans':'组不能为空。','zh-Hant':'群組不可為空。','ja':'グループを空にすることはできません。'},
723:{
 'es':'Verificando M4B',
 'zh-Hans':'正在验证 M4B',
 'hi':'M4B की जाँच हो रही है',
 'de':'M4B wird überprüft',
 'ja':'M4Bを検証中',
 'fr':'Vérification de M4B en cours',
 'pt-BR':'Verificando M4B',
 'ar':'جارٍ التحقق من M4B',
 'ko':'M4B 확인 중',
 'zh-Hant':'正在驗證 M4B',
 'vi':'Đang xác minh M4B',
 'id':'Memverifikasi M4B',
},
724:{
 'de':'„None“ ist ein reservierter Profilname.',
 'zh-Hans':'“None”是保留的配置文件名称。',
 'zh-Hant':'「None」是保留的設定檔名稱。',
},
725:{'ar':'لا يمكن أن تقل قيمة لغة الواجهة عن 1.'},
726:{
 'ja':'混合タイプのルートフォルダーでは、少なくとも1つのメディアタイプに品質プロファイルとメタデータプロファイルを設定する必要があります。',
 'fr':'Les dossiers racine mixtes doivent configurer au moins un type de média avec des profils de qualité et de métadonnées.',
 'ar':'يجب أن يضبط المجلد الجذر من النوع المختلط نوع وسائط واحدًا على الأقل مع ملفات تعريف الجودة والبيانات الوصفية.',
 'ko':'혼합 루트 폴더는 하나 이상의 미디어 유형에 품질 및 메타데이터 프로필을 설정해야 합니다.',
},
727:{
 'zh-Hans':'这是 Calibre-Web 服务器，而不是所需的 Calibre 内容服务器。请参阅 https://manual.calibre-ebook.com/server.html。',
 'zh-Hant':'這是 Calibre-Web 伺服器，不是所需的 Calibre 內容伺服器。請參閱 https://manual.calibre-ebook.com/server.html。',
 'fr':'Il s’agit d’un serveur Calibre-Web, pas du serveur de contenu Calibre requis. Consultez https://manual.calibre-ebook.com/server.html.',
},
728:{
 'es':'authorIds debe contener entre 1 y {value0} IDs de autor.',
 'zh-Hans':'authorIds 必须包含 1 到 {value0} 个作者 ID。',
 'hi':'authorIds में 1 से {value0} तक लेखक ID होने चाहिए।',
 'de':'authorIds muss zwischen 1 und {value0} Autoren-IDs enthalten.',
 'ja':'authorIds には、著者 ID を1～{value0}件含める必要があります。',
 'fr':'authorIds doit contenir entre 1 et {value0} identifiants d’auteur.',
 'ar':'يجب أن تحتوي authorIds على ما بين 1 و{value0} من معرّفات المؤلف.',
 'ko':'authorIds에는 저자 ID가 1개에서 {value0}개까지 포함되어야 합니다.',
 'zh-Hant':'authorIds 必須包含 1 到 {value0} 個作者 ID。',
 'vi':'authorIds phải chứa từ 1 đến {value0} ID tác giả.',
 'id':'authorIds harus berisi 1 hingga {value0} ID penulis.',
},
729:{
 'fr':'Échec de l’authentification.',
 'ja':'認証に失敗しました。',
 'vi':'Xác thực thất bại.',
},
731:{
 'hi':'इसमें वाइल्डकार्ड (*) या मान्य IP पता होना चाहिए।',
 'de':'Es muss einen Platzhalter (*) oder eine gültige IP-Adresse enthalten.',
 'zh-Hans':'必须包含通配符 (*) 或有效的 IP 地址。',
 'ko':'와일드카드 (*) 또는 유효한 IP 주소를 포함해야 합니다.',
 'zh-Hant':'必須包含萬用字元 (*) 或有效的 IP 位址。',
 'id':'Harus berisi karakter pengganti (*) atau alamat IP yang valid.',
},
732:{
 'de':'API-Schlüssel erforderlich.',
 'ja':'API キーが必要です。',
 'ko':'API 키가 필요합니다.',
},
734:{'ko':'유효하지 않은 API 키입니다.'},
735:{'hi':'इंडेक्सर से कनेक्ट नहीं हो सका, शायद समय-सीमा समाप्त होने के कारण। फिर से प्रयास करें या नेटवर्क सेटिंग जाँचें। {value0}'},
737:{
 'es':'La carpeta raíz seleccionada no está configurada. Añádala en Settings → Media Management.',
 'ko':'선택한 루트 폴더가 구성되어 있지 않습니다. Settings → Media Management에서 추가하세요.',
 'id':'Folder root yang dipilih belum dikonfigurasi. Tambahkan melalui Settings → Media Management.',
},
738:{
 'hi':'लंबित आयात रद्द कर दिया गया।',
 'de':'Der ausstehende Import wurde abgebrochen.',
 'fr':'L’importation en attente a été annulée.',
 'pt-BR':'A importação pendente foi cancelada.',
 'ar':'تم إلغاء الاستيراد المعلّق.',
 'vi':'Đã hủy lần nhập đang chờ.',
 'id':'Impor tertunda dibatalkan.',
},
739:{
 'es':'Se requiere el ID de usuario de Goodreads.',
 'zh-Hans':'需要 Goodreads 用户 ID。',
 'de':'Die Goodreads-Benutzer-ID ist erforderlich.',
 'ja':'Goodreads のユーザー ID が必要です。',
 'fr':'L’identifiant utilisateur Goodreads est requis.',
 'pt-BR':'O ID de usuário do Goodreads é obrigatório.',
 'ar':'مطلوب معرّف مستخدم Goodreads.',
 'ko':'Goodreads 사용자 ID가 필요합니다.',
 'zh-Hant':'需要 Goodreads 使用者 ID。',
 'vi':'Cần có ID người dùng Goodreads.',
 'id':'ID pengguna Goodreads wajib diisi.',
},
740:{'ar':'تعذّرت إضافة الكتاب: معرّف الكتاب/العمل لدى المزوّد الأصلي مفقود (Hardcover/Goodreads/OpenLibrary/GoogleBooks).'},
741:{'zh-Hans':'未知异常：{value0}','zh-Hant':'未知例外：{value0}'},
742:{
 'es':'Ya existe una exclusión en la lista de importación para este ID de proveedor y tipo de medio.',
 'zh-Hans':'此提供方 ID 和媒体类型的导入列表排除项已存在。',
 'de':'Für diese Anbieter-ID und diesen Medientyp gibt es bereits einen Importlisten-Ausschluss.',
 'ja':'このプロバイダー ID とメディアタイプに対するインポートリストの除外項目は既に存在します。',
 'fr':'Une exclusion de liste d’importation existe déjà pour cet ID de fournisseur et ce type de média.',
 'pt-BR':'Já existe uma exclusão na lista de importação para este ID de provedor e tipo de mídia.',
 'ar':'يوجد بالفعل استثناء في قائمة الاستيراد لمعرّف المزوّد ونوع الوسائط هذا.',
 'ko':'이 공급자 ID와 미디어 유형에 대한 가져오기 목록 제외 항목이 이미 존재합니다.',
 'zh-Hant':'此供應商 ID 和媒體類型的匯入清單排除項目已存在。',
 'vi':'Đã tồn tại mục loại trừ trong danh sách nhập cho ID nhà cung cấp và loại phương tiện này.',
 'id':'Pengecualian dalam daftar impor untuk ID penyedia dan jenis media ini sudah ada.',
},
743:{
 'ar':"يجب أن يكون التنسيق 'ebook' أو 'audiobook'.",
 'ko':"형식은 'ebook' 또는 'audiobook'이어야 합니다.",
},
744:{
 'hi':'श्रृंखला नहीं मिली।',
 'zh-Hans':'未找到该系列。',
 'ja':'シリーズが見つかりません。',
 'pt-BR':'Série não encontrada.',
 'ar':'لم يتم العثور على السلسلة.',
 'ko':'시리즈를 찾을 수 없습니다.',
 'zh-Hant':'未找到該系列。',
 'vi':'Không tìm thấy bộ sách.',
},
745:{'ar':'وضع علامات الكتاب الصوتي غير صالح.'},
746:{
 'es':'No se pudo conectar a Usenet Download Station.',
 'de':'Verbindung mit Usenet Download Station nicht möglich.',
 'ja':'Usenet Download Station に接続できません。',
 'pt-BR':'Não foi possível conectar ao Usenet Download Station.',
 'ar':'تعذّر الاتصال بـ Usenet Download Station.',
 'ko':'Usenet Download Station에 연결할 수 없습니다.',
},
747:{
 'es':'No se encontró la lista {value0}.',
 'zh-Hans':'未找到列表 {value0}。',
 'ja':'{value0} のリストが見つかりません。',
 'ar':'لم يتم العثور على القائمة {value0}.',
 'ko':'{value0} 목록을 찾을 수 없습니다.',
 'zh-Hant':'未找到清單 {value0}。',
 'vi':'Không tìm thấy danh sách {value0}.',
},
749:{
 'zh-Hans':'代理已配置为供索引器使用。请确保这些设置与您的 BT 客户端代理设置一致。',
 'zh-Hant':'代理已設定供索引器使用。請確認這些設定與您的 BT 用戶端代理設定相符。',
 'ja':'プロキシはインデクサー用に設定されています。これらの設定がトレントクライアントのプロキシと一致していることを確認してください。',
},
}

WHY={
700:'This is an indexer connection failure that directs the user to the log; candidates restore natural error wording and punctuation.',
701:'The AuthorMediaMoveController returns this conflict when a media-move preview has conflicts or no files can be moved; candidates distinguish the move operation from generic motion.',
702:'This is a Calibre host validation failure; candidates express a failed connection as a natural error sentence.',
703:'The OIDC authority validator requires https:// except when the provider runs on localhost; the scheme and host exception must remain exact.',
704:'This is an Ntfy username/password validation error; the Japanese wording needs a grammatical sentence.',
705:'AudioBookShelf reports an empty server library collection; Chinese and Hindi should say media library rather than a physical library.',
706:'The AudioBookShelf connection test reports failed authentication and tells the user to check the API key; Chinese punctuation and Korean imperative are corrected.',
707:'The Download Station error reports failure to retrieve an NZB list and includes the exception in {value0}; candidates restore the failed-retrieval meaning and preserve NZBs and the placeholder.',
708:'SABnzbd requires a password only when an API key is not configured; candidates fix awkward word order and the Vietnamese literal key term.',
709:'The SeriesLookupController currently supports Hardcover for book-series lookup; candidates correct awkward or misleading “supported/search/series” wording.',
710:'This HostConfig validation rejects an invalid SSL certificate file or password; the Japanese phrase currently lacks grammatical particles.',
711:'NzbVortex reports that the selected download group/category does not exist; the Chinese targets use an unrelated group/organization word.',
715:'This is a product update notice for NZBVortex; candidates fix Spanish agreement, Japanese particles, and Arabic gender/word order.',
716:'This AddBookService error requires an ebook metadata profile before adding ebook books; the Vietnamese second sentence should retain the ebook qualifier.',
717:'This validation names the Applies to field and its three exact enum values; candidates translate the field label and preserve Both, Audiobook, and Ebook.',
718:'Backup restore rejects file extensions outside the listed set; candidates clarify that these are file extensions and preserve all five literal extensions.',
719:'Deluge category validation allows only lowercase ASCII letters, digits, and hyphen; candidates repair incomplete or awkward sentence wording without changing the allowed characters.',
720:'Signal reports a failed test-message send and interpolates the server error in {value0}; candidates make the failure a natural sentence and preserve the parameter.',
721:'This MyAnonaMouse authentication error points to mam_id and two settings paths; the Indonesian version needs sentence capitalization and spacing.',
722:'This NamingPattern validator rejects an empty group; candidates fix Chinese group terminology and the Japanese “cannot become empty” wording.',
723:'M4bConversionService reports the in-progress conversion stage at 96 percent; candidates express an ongoing verification step, not a noun or command.',
724:'Metadata profile validation reserves the exact name None; candidates correct German grammar and use the settings-profile term in Chinese.',
725:'This validation requires a positive UI language value; the Arabic current wording has incorrect agreement and word order.',
726:'Root-folder validation requires at least one media type with quality and metadata profiles; candidates fix unnatural root-folder and metadata terminology.',
727:'CalibreProxy distinguishes Calibre-Web from the required Calibre content server and supplies the manual URL; candidates repair Chinese punctuation and French word order while preserving product names and URL.',
728:'The BookController requires between 1 and {value0} author IDs; candidates correct range grammar and retain the authorIds property and formatted maximum.',
729:'This is the generic authentication failure returned by multiple providers; candidates correct French tense, Japanese sentence structure, and Vietnamese capitalization.',
731:'The IP validation rule requires a wildcard or valid IP address; candidates translate wildcard correctly and repair the German grammar.',
732:'The SABnzbd validation requires an API key; candidates complete the German, Japanese, and Korean message fragments.',
734:'This is an invalid API-key validation error; the Korean current value is an unnatural noun fragment.',
735:'This indexer network error may be a timeout and instructs retry/network checks; the Hindi current word order and punctuation are poor.',
737:'This author/root-folder error says the selected folder must be configured in Settings → Media Management; candidates correct Spanish vocabulary/spacing, Korean root-folder wording, and Indonesian capitalization.',
738:'This is a confirmation after cancelling a pending author import; candidates restore “pending” and make the status grammatical.',
739:'This Goodreads import-list validation requires a Goodreads user ID; candidates correct ungrammatical word order while preserving Goodreads.',
740:'The BookController cannot add a book without an upstream provider book/work ID; the Arabic current text redundantly says “ID identifier”.',
741:'This generic exception message appends {value0}; Chinese targets need standard terminology and punctuation spacing.',
742:'The ImportListExclusionController rejects a duplicate exclusion for a provider ID and media type; candidates repair the noun phrase and Korean import terminology.',
743:'Author-media-move validation accepts only the exact format tokens ebook or audiobook; the Arabic term means form/model and Korean grammar is incorrect.',
744:'The SeriesController returns a not-found error for a book series; candidates correct gender, sentence structure, and the Vietnamese book-series sense.',
745:'This conversion setting rejects an invalid audiobook tag mode; Arabic agreement and word order are corrected.',
746:'This Download Station connection test/error reports inability to connect; candidates turn fragments into natural error messages while preserving the product name.',
747:'Goodreads reports that a list identifier {value0} was not found; candidates fix agreement and word order while preserving the interpolation.',
749:'ProxyDebugController explains that the proxy is routed to indexers and should match the torrent/BT client proxy; candidates translate Chinese technical prose and fix Japanese tense.',
}

cells=[json.loads(x) for x in (OUT/'input-cells.jsonl').read_text().splitlines()]
ctx={json.loads(x)['sourceId']:json.loads(x) for x in (OUT/'caller-context.jsonl').read_text().splitlines()}
source_rows={x['sourceOrdinal']:x for x in map(json.loads,(OUT/'source-slice.jsonl').read_text().splitlines())}
plan={}; candidate_count=0
for c in cells:
 o=c['sourceOrdinal']; loc=c['locale']; candidate=C.get(o,{}).get(loc)
 extra=EXTRA_PROTECTED.get(o,[]); protected=list(dict.fromkeys(c['protectedLiterals']+extra))
 checks=[{'literal':p,'presentInSource':p in c['source'],'presentInCurrentTarget':p in c['currentTarget'],'presentInRecommendedTarget':(p in candidate) if candidate is not None else None,'origin':'source-registry' if p in c['protectedLiterals'] else 'primary-review-addition'} for p in protected]
 if candidate is not None:
  assert candidate!=c['currentTarget'],(o,loc,'unchanged candidate')
  assert placeholders(candidate)==c['sourcePlaceholders'],(o,loc,'placeholder mismatch',c['sourcePlaceholders'],placeholders(candidate))
  assert markup(candidate)==c['sourceMarkup'],(o,loc,'markup mismatch')
  missing=[p for p in protected if p in c['source'] and p not in candidate]
  assert not missing,(o,loc,'protected literals missing',missing)
  disp='propose-correction'; final=candidate; rationale=WHY[o]; confidence='moderate'; candidate_count+=1
 else:
  missing=[p for p in protected if p in c['source'] and p not in c['currentTarget']]
  if not c['placeholderParity'] or not c['markupParity'] or missing:
   disp='hold'; final=None; rationale='Needs language or token review: current value has unresolved placeholder, markup, or protected-literal drift.'; confidence='low'
  else:
   disp='accept-current'; final=c['currentTarget']; rationale='Current wording preserves the source meaning and technical terms in the pinned caller context; no material semantic issue was found.'; confidence='moderate'
 entry={'sourceOrdinal':o,'sourceId':c['sourceId'],'locale':loc,'source':c['source'],'sourceTextSha256':c['sourceTextSha256'],'currentTarget':c['currentTarget'],'currentTargetSha256':c['currentTargetSha256'],'recommendedTarget':candidate,'recommendedTargetSha256':hashlib.sha256(candidate.encode()).hexdigest() if candidate is not None else None,'finalTarget':final,'finalTargetSha256':hashlib.sha256(final.encode()).hexdigest() if final is not None else None,'disposition':disp,'rationale':rationale,'confidence':confidence,'sourcePlaceholders':c['sourcePlaceholders'],'currentTargetPlaceholders':c['currentTargetPlaceholders'],'recommendedPlaceholders':placeholders(candidate) if candidate is not None else None,'placeholderParity':c['sourcePlaceholders']==c['currentTargetPlaceholders'] and (candidate is None or c['sourcePlaceholders']==placeholders(candidate)),'sourceMarkup':c['sourceMarkup'],'currentTargetMarkup':c['currentTargetMarkup'],'recommendedTargetMarkup':markup(candidate) if candidate is not None else None,'markupParity':c['sourceMarkup']==c['currentTargetMarkup'] and (candidate is None or c['sourceMarkup']==markup(candidate)),'protectedLiterals':protected,'protectedLiteralChecks':checks,'protectedLiteralsPreserved':not (missing if candidate is None else [p for p in protected if p in c['source'] and p not in candidate]),'callerRefs':ctx[c['sourceId']]['callerRefs'],'callerContextSha256':c['callerContextSha256'],'callerSurface':ctx[c['sourceId']]['sourceRegistrySurface'],'nativeSpeakerApproval':False}
 plan[f'{o}|{loc}']=entry

assert len(plan)==600 and candidate_count==sum(len(v) for v in C.values())
assert all(r['sourceOrdinal'] in WHY for r in plan.values() if r['disposition']=='propose-correction')
(OUT/'review-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
(OUT/'manual-protected-literals.json').write_text(json.dumps({'additionalProtectedLiteralsByOrdinal':EXTRA_PROTECTED,'rationalesByOrdinal':WHY},ensure_ascii=False,indent=2,sort_keys=True)+'\n')
print(json.dumps({'cells':len(plan),'candidateCount':candidate_count,'candidatePositions':sorted(C),'additionalProtectedLiteralPositions':sorted(EXTRA_PROTECTED)},ensure_ascii=False,indent=2))
