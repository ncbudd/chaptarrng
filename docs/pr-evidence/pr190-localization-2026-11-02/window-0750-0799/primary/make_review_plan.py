import hashlib,json,pathlib,re
OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0750-0799-primary-20261102')
LOCALES=['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']
def sha(s): return hashlib.sha256(s.encode()).hexdigest()
def placeholders(s): return sorted(set(re.findall(r'\{[^{}]+\}',s)))
def markup(s):
 if re.fullmatch(r'<[^<>/]+>',s): return []
 return re.findall(r'</?[A-Za-z][^>]*>',s)
# Candidate translations are proposed only where the frozen value has a material
# meaning, grammar, locale, or technical-token defect in its pinned caller context.
C={
752:{'de':'{value0} MonitorExisting muss 0 (None), 1 (All), 2 (Selected) oder null (nicht konfiguriert) sein.','fr':'{value0} MonitorExisting doit être 0 (None), 1 (All), 2 (Selected) ou null (non configuré).','ko':'{value0} MonitorExisting는 0 (None), 1 (All), 2 (Selected) 또는 null(설정되지 않음)이어야 합니다.'},
753:{'es':'No se pudo conectar a Goodreads. Consulte el registro para obtener más detalles.','zh-Hans':'无法连接到 Goodreads，请查看日志了解详情。','de':'Verbindung zu Goodreads nicht möglich. Weitere Details finden Sie im Protokoll.','ja':'Goodreads に接続できません。詳しくはログを確認してください。','fr':'Impossible de se connecter à Goodreads. Consultez le journal pour plus de détails.','pt-BR':'Não foi possível conectar ao Goodreads. Consulte o log para mais detalhes.','zh-Hant':'無法連線到 Goodreads，請查看日誌以瞭解詳細資訊。'},
754:{'es':'No se pudo conectar a la lista de importación. Consulte el registro para obtener más detalles.','zh-Hans':'无法连接到导入列表，请查看日志了解详情。','hi':'आयात सूची से कनेक्ट नहीं हो सका। अधिक जानकारी के लिए लॉग देखें।','ja':'インポートリストに接続できません。詳しくはログを確認してください。','fr':'Impossible de se connecter à la liste d’importation. Consultez le journal pour plus de détails.','pt-BR':'Não foi possível conectar à lista de importação. Consulte o log para mais detalhes.','ko':'가져오기 목록에 연결할 수 없습니다. 자세한 내용은 로그를 확인하세요.','zh-Hant':'無法連線到匯入清單，請查看日誌以瞭解詳細資訊。'},
755:{'es':'Debe ser una URL válida que comience con http(s)://.','zh-Hans':'必须是以 http(s):// 开头的有效 URL。','hi':'यह http(s):// से शुरू होने वाला मान्य URL होना चाहिए।','de':'Muss eine gültige URL sein, die mit http(s):// beginnt.','ja':'http(s):// で始まる有効な URL を指定してください。','fr':'Doit être une URL valide commençant par http(s)://.','pt-BR':'Deve ser uma URL válida que comece com http(s)://.','ar':'يجب أن يكون عنوان URL صالحًا ويبدأ بـ http(s)://.','ko':'http(s)://로 시작하는 유효한 URL이어야 합니다.','zh-Hant':'必須是以 http(s):// 開頭的有效 URL。','vi':'Phải là URL hợp lệ bắt đầu bằng http(s)://.','id':'Harus berupa URL valid yang diawali dengan http(s)://.'},
756:{'es':'No se pudo conectar a Hardcover. Consulte los registros para obtener más detalles.','zh-Hans':'无法连接到 Hardcover。请查看日志了解详情。','hi':'Hardcover से कनेक्ट नहीं हो सका। अधिक जानकारी के लिए लॉग देखें।','de':'Verbindung zu Hardcover nicht möglich. Weitere Details finden Sie in den Protokollen.','ja':'Hardcover に接続できません。詳しくはログを確認してください。','fr':'Impossible de se connecter à Hardcover. Consultez les journaux pour plus de détails.','pt-BR':'Não foi possível conectar ao Hardcover. Consulte os logs para mais detalhes.','ar':'تعذّر الاتصال بـ Hardcover. راجع السجلات لمعرفة التفاصيل.','ko':'Hardcover에 연결할 수 없습니다. 자세한 내용은 로그를 확인하세요.','zh-Hant':'無法連線到 Hardcover。請查看日誌以瞭解詳細資訊。'},
757:{'zh-Hans':'各组都必须有名称。','zh-Hant':'每個群組都必須有名稱。','hi':'हर समूह का एक नाम होना चाहिए।'},
758:{'es':'Caracteres permitidos: a-z y -.','zh-Hans':'允许的字符：a-z 和 -。','hi':'अनुमत वर्ण: a-z और -।','de':'Zulässige Zeichen: a-z und -.','ja':'使用できる文字：a-z と -。','fr':'Caractères autorisés : a-z et -.','pt-BR':'Caracteres permitidos: a-z e -.','ar':'الأحرف المسموح بها: a-z و-.','ko':'허용되는 문자: a-z 및 -.','zh-Hant':'允許的字元：a-z 和 -。','vi':'Các ký tự được phép: a-z và dấu gạch ngang (-).','id':'Karakter yang diizinkan: a-z dan -.'},
760:{'es':"mediaType debe ser 'audiobook' o 'ebook'.",'ko':"mediaType는 'audiobook' 또는 'ebook'이어야 합니다."},
761:{'es':'No se pudo conectar a qBittorrent.','hi':'qBittorrent से कनेक्ट नहीं हो सका।','de':'Verbindung zu qBittorrent nicht möglich.','ja':'qBittorrent に接続できません。','pt-BR':'Não foi possível conectar ao qBittorrent.','ar':'تعذّر الاتصال بـ qBittorrent.','ko':'qBittorrent에 연결할 수 없습니다.'},
762:{'id':'Tidak dapat terhubung ke broker MQTT. Periksa host, port, konfigurasi TLS, dan kredensial.'},
763:{'es':'No se pudo conectar a Aria2.','hi':'Aria2 से कनेक्ट नहीं हो सका।','de':'Verbindung zu Aria2 nicht möglich.','ja':'Aria2 に接続できません。','pt-BR':'Não foi possível conectar ao Aria2.','ar':'تعذّر الاتصال بـ Aria2.','ko':'Aria2에 연결할 수 없습니다.'},
764:{'es':'Error de conexión: {value0}','zh-Hans':'连接失败：{value0}','hi':'कनेक्शन विफल हुआ: {value0}','de':'Verbindung fehlgeschlagen: {value0}','ja':'接続に失敗しました: {value0}','fr':'Échec de la connexion : {value0}','pt-BR':'Falha na conexão: {value0}','ar':'فشل الاتصال: {value0}','ko':'연결하지 못했습니다: {value0}','zh-Hant':'連線失敗：{value0}','vi':'Kết nối không thành công: {value0}'},
766:{'es':'No se encontró la biblioteca de audiolibros seleccionada en Grimmory.','zh-Hans':'在 Grimmory 中找不到所选的有声书库。','hi':'चयनित ऑडियोबुक लाइब्रेरी Grimmory में नहीं मिली।','de':'Die ausgewählte Hörbuchbibliothek wurde in Grimmory nicht gefunden.','ja':'選択したオーディオブックライブラリが Grimmory で見つかりませんでした。','fr':'La bibliothèque de livres audio sélectionnée est introuvable dans Grimmory.','pt-BR':'A biblioteca de audiolivros selecionada não foi encontrada no Grimmory.','ko':'선택한 오디오북 라이브러리를 Grimmory에서 찾을 수 없습니다.','zh-Hant':'在 Grimmory 中找不到所選的有聲書庫。','vi':'Không tìm thấy thư viện sách nói đã chọn trong Grimmory.'},
767:{'es':'No se puede añadir el libro porque los metadatos no proporcionaron ninguna edición.','de':'Das Buch kann nicht hinzugefügt werden, da die Metadaten keine Ausgabe dafür enthalten.','ja':'メタデータにこの本の版情報がないため、追加できません。','fr':'Impossible d’ajouter le livre, car les métadonnées ne fournissent aucune édition de celui-ci.','ar':'يتعذّر إضافة الكتاب لأن البيانات الوصفية لا تتضمن أي طبعات له.','vi':'Không thể thêm sách vì siêu dữ liệu không cung cấp ấn bản nào cho sách này.','id':'Buku tidak dapat ditambahkan karena metadata tidak menyediakan edisi apa pun untuknya.'},
768:{'de':"Proxy ist deaktiviert. Für MyAnonaMouse setzen Sie ProxyMode auf 'IndexerOnly' und konfigurieren Sie die Proxy-Einstellungen so, dass sie denen Ihres Torrent-Clients entsprechen."},
770:{'es':'Bookshelf solo cambia el seguimiento de libros. Use Author Editor para cambiar el seguimiento del autor o de los libros futuros.','zh-Hans':'Bookshelf 只会更改书籍监控。请使用作者编辑器更改作者或未来书籍的监控。','hi':'Bookshelf केवल पुस्तकों की निगरानी बदलता है। लेखक या भविष्य में आने वाली पुस्तकों की निगरानी बदलने के लिए Author Editor का उपयोग करें।','de':'Bookshelf ändert nur die Überwachung von Büchern. Verwenden Sie Author Editor, um die Überwachung des Autors oder zukünftiger Bücher zu ändern.','ja':'Bookshelf で変更できるのは本の監視設定だけです。著者や今後の本の監視設定を変更するには Author Editor を使用してください。','fr':'Bookshelf ne modifie que le suivi des livres. Utilisez Author Editor pour modifier le suivi de l’auteur ou des livres à venir.','pt-BR':'Bookshelf só altera o monitoramento de livros. Use o Editor de autores para alterar o monitoramento do autor ou dos próximos livros.','ko':'Bookshelf는 책 모니터링만 변경합니다. 저자 또는 앞으로 나올 책의 모니터링을 변경하려면 Author Editor를 사용하세요.','zh-Hant':'Bookshelf 只會變更書籍監控。請使用作者編輯器變更作者或未來書籍的監控。'},
771:{'es':'No se pudo vincular al autor con la carpeta.','hi':'लेखक को फ़ोल्डर से लिंक नहीं किया जा सका।','de':'Der Autor konnte nicht mit dem Ordner verknüpft werden.','ja':'著者をフォルダーに関連付けられませんでした。','pt-BR':'Não foi possível vincular o autor à pasta.','ar':'تعذّر ربط المؤلف بالمجلد.','vi':'Không thể liên kết tác giả với thư mục.','id':'Gagal menghubungkan penulis ke folder.'},
773:{'es':'Debe ser una URL válida que comience con http:// o https://.','zh-Hans':'必须是以 http:// 或 https:// 开头的有效 URL。','ja':'http:// または https:// で始まる有効な URL を指定してください。','fr':'Doit être une URL valide commençant par http:// ou https://.','zh-Hant':'必須是以 http:// 或 https:// 開頭的有效 URL。','vi':'Phải là URL hợp lệ bắt đầu bằng http:// hoặc https://.'},
774:{'es':"mediaType debe ser 'all', 'audiobook' o 'ebook'.",'zh-Hans':"mediaType 必须是 'all'、'audiobook' 或 'ebook'。",'de':"mediaType muss 'all', 'audiobook' oder 'ebook' sein.",'fr':"mediaType doit être 'all', 'audiobook' ou 'ebook'.",'pt-BR':"mediaType deve ser 'all', 'audiobook' ou 'ebook'.",'ar':"يجب أن تكون قيمة mediaType هي 'all' أو 'audiobook' أو 'ebook'.",'ko':"mediaType는 'all', 'audiobook' 또는 'ebook'이어야 합니다.",'zh-Hant':"mediaType 必須是 'all'、'audiobook' 或 'ebook'。"},
775:{'hi':'{value0} मेटाडेटा प्रोफ़ाइल आवश्यक है।','de':'Ein Metadatenprofil für {value0} ist erforderlich.','pt-BR':'É necessário um perfil de metadados para {value0}.'},
778:{'de':'Das BookOrbit-Konto benötigt die Berechtigung Book Dock Access.','id':'Akun BookOrbit harus memiliki izin Book Dock Access.'},
779:{'es':'No se pudo conectar a AudioBookShelf. Estado: {value0}','zh-Hans':'无法连接到 AudioBookShelf。状态：{value0}','hi':'AudioBookShelf से कनेक्ट नहीं हो सका। स्थिति: {value0}','de':'Verbindung zu AudioBookShelf nicht möglich. Status: {value0}','ja':'AudioBookShelf に接続できません。ステータス: {value0}','fr':'Impossible de se connecter à AudioBookShelf. Statut : {value0}','pt-BR':'Não foi possível conectar ao AudioBookShelf. Status: {value0}','ar':'تعذّر الاتصال بـ AudioBookShelf. الحالة: {value0}','ko':'AudioBookShelf에 연결할 수 없습니다. 상태: {value0}','zh-Hant':'無法連線到 AudioBookShelf。狀態：{value0}','vi':'Không thể kết nối với AudioBookShelf. Trạng thái: {value0}'},
781:{'hi':'कोई RSS फ़ीड क्वेरी उपलब्ध नहीं है। यह इंडेक्सर या उसकी श्रेणी सेटिंग में समस्या के कारण हो सकता है।','ko':'RSS 피드 쿼리를 사용할 수 없습니다. 인덱서 또는 인덱서의 카테고리 설정에 문제가 있을 수 있습니다.'},
782:{'vi':'Cần có hồ sơ chất lượng cho {value0}.'},
783:{'ar':'لم يتم العثور على الصورة.'},
784:{'ko':'테스트하기 전에 메타데이터 서버 URL을 저장해 주세요.'},
785:{'es':'Se requiere el secreto OAuth de Goodreads cuando se configura un token de acceso.','zh-Hans':'配置了访问令牌时，必须提供 Goodreads OAuth 密钥。','hi':'एक्सेस टोकन कॉन्फ़िगर होने पर Goodreads OAuth सीक्रेट आवश्यक है।','de':'Das Goodreads-OAuth-Geheimnis ist erforderlich, wenn ein Zugriffstoken konfiguriert ist.','ja':'アクセストークンが設定されている場合は、Goodreads OAuth シークレットが必要です。','fr':'Le secret OAuth Goodreads est requis lorsqu’un jeton d’accès est configuré.','pt-BR':'O segredo OAuth do Goodreads é obrigatório quando um token de acesso está configurado.','ar':'يلزم سر OAuth الخاص بـ Goodreads عند إعداد رمز وصول.','ko':'액세스 토큰이 설정된 경우 Goodreads OAuth 시크릿이 필요합니다.','zh-Hant':'設定存取權杖時，必須提供 Goodreads OAuth 密鑰。','vi':'Cần có bí mật OAuth của Goodreads khi đã cấu hình mã thông báo truy cập.','id':'Rahasia OAuth Goodreads wajib diisi jika token akses dikonfigurasi.'},
786:{'ko':"mediaType이 유효하지 않습니다. 'audiobook' 또는 'ebook'이 필요합니다.",'vi':"mediaType không hợp lệ. Giá trị mong đợi là 'audiobook' hoặc 'ebook'."},
787:{'es':'La carpeta raíz seleccionada es solo para Audiobook; elija una carpeta raíz Ebook o Mixed.'},
789:{'ko':"루트 폴더 경로 '{value0}'에 저자 폴더 '{value1}'가 포함되어 있습니다."},
790:{'es':'El sitio está protegido por CloudFlare CAPTCHA. Se requiere un token CAPTCHA válido.','hi':'साइट CloudFlare CAPTCHA से सुरक्षित है। मान्य CAPTCHA टोकन आवश्यक है।','de':'Die Website ist durch CloudFlare CAPTCHA geschützt. Ein gültiges CAPTCHA-Token ist erforderlich.','ja':'このサイトは CloudFlare CAPTCHA で保護されています。有効な CAPTCHA トークンが必要です。','ar':'الموقع محمي بواسطة CloudFlare CAPTCHA. يلزم رمز CAPTCHA صالح.','vi':'Trang web được CloudFlare CAPTCHA bảo vệ. Cần có mã thông báo CAPTCHA hợp lệ.'},
791:{'zh-Hans':'命名模式不能为空。','ja':'パターンを空にすることはできません。','ar':'لا يمكن أن يكون النمط فارغًا.','zh-Hant':'命名模式不得為空白。','vi':'Mẫu không được để trống.','id':'Pola tidak boleh kosong.'},
792:{'vi':'Bắt buộc phải có EditionId.'},
793:{'es':'Los ID de dispositivo parecen no ser válidos.','zh-Hans':'设备 ID 似乎无效。','hi':'डिवाइस ID अमान्य प्रतीत होते हैं।','de':'Die Geräte-IDs scheinen ungültig zu sein.','ja':'デバイス ID は無効のようです。','fr':'Les identifiants des appareils semblent invalides.','ko':'기기 ID가 유효하지 않은 것 같습니다.','zh-Hant':'裝置 ID 似乎無效。','vi':'ID thiết bị có vẻ không hợp lệ.'},
794:{'es':'No se pudo iniciar el proceso.','zh-Hans':'进程启动失败。','hi':'प्रक्रिया शुरू नहीं हो सकी।','de':'Der Prozess konnte nicht gestartet werden.','ja':'プロセスを開始できませんでした。','fr':'Le processus n’a pas pu démarrer.','pt-BR':'Não foi possível iniciar o processo.','ar':'تعذّر بدء العملية.','ko':'프로세스를 시작하지 못했습니다.','zh-Hant':'程序啟動失敗。','vi':'Không thể khởi động tiến trình.','id':'Proses tidak dapat dimulai.'},
795:{'zh-Hans':'必须提供 ImageUrl。','fr':'ImageUrl est obligatoire.','ko':'ImageUrl이 필요합니다.','zh-Hant':'必須提供 ImageUrl。','vi':'ImageUrl là bắt buộc.'},
796:{'hi':'Chaptarr को लिखने की अनुमति चाहिए। calibre में उपयोगकर्ता या विश्वसनीय IP कॉन्फ़िगर करें। देखें https://manual.calibre-ebook.com/server.html'},
798:{'zh-Hans':'未配置 API 密钥时，必须提供用户名。','de':'Ein Benutzername ist erforderlich, wenn kein API-Schlüssel konfiguriert ist.','ko':'API 키가 설정되지 않은 경우 사용자 이름이 필요합니다.','vi':'Cần có tên người dùng khi chưa cấu hình khóa API.'},
799:{'ja':'Emby または Jellyfin を選択してください。','ko':'Emby 또는 Jellyfin을 선택하세요.'},
}
EXTRA={
752:['null'],755:['http(s)://'],758:['-'],759:['Jackett','all'],760:['audiobook','ebook'],
762:['MQTT','TLS'],765:['unmappedFiles.scope',"'selected'"],768:['ProxyMode',"'IndexerOnly'"],
770:['Bookshelf'],774:['mediaType'],778:['Book Dock Access'],780:['0'],781:['RSS'],784:['URL'],
786:['audiobook','ebook'],787:['Audiobook','Ebook','Mixed'],790:['CloudFlare','CAPTCHA'],
792:['EditionId'],795:['ImageUrl'],796:['calibre','IP','https://manual.calibre-ebook.com/server.html']
}
WHY={
752:'RootFolderResource validates the MonitorExisting tri-state value after the media label; preserve the property name, enum labels, and null literal. The German current value corrupts Selected as ZSelected, and the Korean null wording is unnatural.',
753:'GoodreadsNotificationBase reports a connection failure and directs users to logs; candidates repair awkward literal translations while preserving Goodreads.',
754:'Multiple Goodreads and Hardcover import-list callers report a connection failure and advise checking logs; candidates correct the import-list term and ungrammatical connection phrasing.',
755:'NewznabSettings and TorznabSettings validate NarratorMetadataBaseUrl; each candidate produces a grammatical validation message and preserves the scheme and URL term.',
756:'HardcoverProxy reports a provider connection failure and refers users to logs; candidates replace incomplete translated fragments with natural error sentences while preserving Hardcover.',
757:'QualityItemsValidator rejects unnamed groups; candidates repair the group term or awkward Hindi phrasing.',
758:'DownloadStation and Transmission category validators accept only a-z and hyphen; candidates make the allowed-character label grammatical and preserve the exact character set.',
760:'API parsers accept only the exact audiobook and ebook mediaType values; candidates correct awkward Spanish/Korean grammar while preserving the field and enum tokens.',
761:'qBittorrent validation reports an inability to connect; candidates replace incomplete or ambiguous fragments with concise error sentences while preserving the product name.',
762:'MqttGateway reports a broker connection failure and directs users to check host, port, TLS, and credentials; the Indonesian target uses a Malay word for credentials.',
763:'Aria2 validation reports an inability to connect; candidates replace incomplete or ambiguous fragments with concise error sentences while preserving the product name.',
764:'ProxyTestService inserts the exception text in value0; candidates express a failed connection naturally and preserve the interpolation.',
766:'GrimmoryProxy reports a missing selected audiobook library; candidates fix literal or awkward audiobook-library wording while preserving Grimmory.',
767:'BookService cannot add a book when metadata has no edition records for it; candidates repair awkward phrasing or improve the book-edition relationship.',
768:'ProxyDebugController explains that the proxy is disabled and gives the exact MyAnonaMouse mode; the German comparison clause is ungrammatical.',
770:'Bookshelf changes only book monitoring; Author Editor handles author and future-book monitoring. Candidates clarify the distinction and the future-book sense while retaining the Bookshelf label.',
771:'RootFolderController could not link an author to a folder; candidates replace ungrammatical or wrong-preposition wording with a clear failure sentence.',
773:'RuleBuilderExtensions validates that a URL begins with one of two schemes; candidates improve validator grammar and preserve both schemes.',
774:'ImportListExclusionController restricts mediaType to exact all/audiobook/ebook values; candidates repair punctuation and grammar while preserving tokens.',
775:'RootFolderController requires a metadata profile for the dynamic media label in value0; candidates clarify the relation and complete fragmentary forms.',
778:'BookOrbit authorization requires the exact Book Dock Access permission; candidates correct German compounding and Indonesian word choice without translating the permission name.',
779:'AudioBookShelfProxy includes an HTTP status value in value0; candidates make connection failure and status labeling grammatical while preserving the product and interpolation.',
781:'HttpIndexerBase reports an absent RSS feed query and points to indexer/category configuration; the Hindi value is in Chinese, and Korean needs sentence spacing.',
782:'RootFolderController requires a quality profile for the dynamic media label; the Vietnamese candidate clarifies the required-for relationship.',
783:'AuthorController photo lookup returns not found; the Arabic candidate uses natural sentence order.',
784:'DevelopmentConfigController requires saving the metadata server URL before testing; the Korean candidate fixes the URL particle and imperative wording.',
785:'GoodreadsBookshelfImportListSettings requires the OAuth secret only when an access token is configured; candidates repair unnatural syntax while preserving Goodreads and OAuth.',
786:'AuthorController rejects mediaType values outside audiobook/ebook; candidates correct malformed Korean/Vietnamese grammar and preserve exact enum values.',
787:'Goodreads and Hardcover import-list callers require an Ebook or Mixed folder when the selected root is Audiobook-only; the Spanish target confuses folder with pasta.',
789:'AuthorFolderAsRootFolderValidator reports that the root path contains an author folder; the Korean target uses the wrong sense of root.',
790:'HttpIndexerBase requires a valid CAPTCHA token for CloudFlare-protected sites; candidates repair fragments, agreement, or punctuation while preserving CloudFlare CAPTCHA.',
791:'NamingPatternService rejects an empty naming pattern; candidates correct the Chinese/Arabic/Vietnamese term for pattern and improve naturalness.',
792:'BookController requires the EditionId field; the Vietnamese candidate is a complete required-field message and preserves the property name.',
793:'JoinProxy reports that device IDs appear invalid; candidates correct spelling, agreement, and the uncertain-appearance meaning.',
794:'ExternalToolsService reports process startup failure; candidates express failure to start rather than a process simply not beginning.',
795:'AuthorController requires ImageUrl; candidates complete the required-field message and correct Korean particle agreement.',
796:'CalibreProxy requires write access and offers configuration guidance; the Hindi target transliterates the product name, so the candidate preserves calibre exactly.',
798:'SabnzbdSettings requires a username only if no API key is configured; candidates correct the inverted/repeated Korean condition and improve the German/Vietnamese phrasing.',
799:'EmbyJellyfinSettings prompts for one of two exact provider names; candidates fix Japanese spacing and Korean object particle grammar.'
}
inputs=[json.loads(x) for x in (OUT/'input-cells.jsonl').read_text().splitlines()]
ctx={json.loads(x)['sourceId']:json.loads(x) for x in (OUT/'caller-context.jsonl').read_text().splitlines()}
plan={}
for c in inputs:
 o=c['sourceOrdinal']; loc=c['locale']; candidate=C.get(o,{}).get(loc)
 protected=list(dict.fromkeys(c['protectedLiterals']+EXTRA.get(o,[])))
 checks=[{'literal':p,'presentInSource':p in c['source'],'presentInCurrentTarget':p in c['currentTarget'],'presentInRecommendedTarget':(p in candidate) if candidate is not None else None,'origin':'source-registry' if p in c['protectedLiterals'] else 'primary-review-addition'} for p in protected]
 if candidate is not None:
  assert candidate!=c['currentTarget'],(o,loc,'unchanged candidate')
  assert placeholders(candidate)==c['sourcePlaceholders'],(o,loc,'placeholder mismatch',c['sourcePlaceholders'],placeholders(candidate))
  assert markup(candidate)==c['sourceMarkup'],(o,loc,'markup mismatch')
  missing=[p for p in protected if p in c['source'] and p not in candidate]
  assert not missing,(o,loc,'protected literals missing',missing,candidate)
  disp='propose-correction'; final=candidate; rationale=WHY[o]+' Candidate target is selected for locale '+loc+'.'; conf='moderate'
 else:
  missing=[p for p in protected if p in c['source'] and p not in c['currentTarget']]
  if not c['placeholderParity'] or not c['markupParity'] or missing:
   disp='hold'; final=None; rationale='Current target has unresolved placeholder, markup, or protected-literal drift: '+', '.join(missing); conf='low'
  else:
   disp='accept-current'; final=c['currentTarget']; rationale='Current wording preserves the source meaning and technical literals in the pinned caller context; no material semantic issue was identified.'; conf='moderate'
 entry={'sourceOrdinal':o,'sourceId':c['sourceId'],'locale':loc,'source':c['source'],'sourceTextSha256':c['sourceTextSha256'],'currentTarget':c['currentTarget'],'currentTargetSha256':c['currentTargetSha256'],'recommendedTarget':candidate,'recommendedTargetSha256':sha(candidate) if candidate is not None else None,'finalTarget':final,'finalTargetSha256':sha(final) if final is not None else None,'disposition':disp,'rationale':rationale,'confidence':conf,'sourcePlaceholders':c['sourcePlaceholders'],'currentTargetPlaceholders':c['currentTargetPlaceholders'],'recommendedPlaceholders':placeholders(candidate) if candidate is not None else None,'placeholderParity':c['sourcePlaceholders']==c['currentTargetPlaceholders'] and (candidate is None or c['sourcePlaceholders']==placeholders(candidate)),'sourceMarkup':c['sourceMarkup'],'currentTargetMarkup':c['currentTargetMarkup'],'recommendedTargetMarkup':markup(candidate) if candidate is not None else None,'markupParity':c['sourceMarkup']==c['currentTargetMarkup'] and (candidate is None or c['sourceMarkup']==markup(candidate)),'protectedLiterals':protected,'protectedLiteralChecks':checks,'protectedLiteralsPreserved':not (missing if candidate is None else [p for p in protected if p in c['source'] and p not in candidate]),'callerRefs':ctx[c['sourceId']]['callerRefs'],'callerContextSha256':c['callerContextSha256'],'callerSurface':ctx[c['sourceId']]['sourceRegistrySurface'],'nativeSpeakerApproval':False}
 plan[f'{o}|{loc}']=entry
assert len(inputs)==600 and len(plan)==600
for k,v in plan.items():
 if v['disposition']=='hold': print('HOLD',k,v['rationale'])
(OUT/'review-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
(OUT/'manual-protected-literals.json').write_text(json.dumps({'additionalProtectedLiteralsByOrdinal':EXTRA,'rationalesByOrdinal':WHY},ensure_ascii=False,indent=2,sort_keys=True)+'\n')
print(json.dumps({'cells':len(plan),'correctionCount':len(C),'candidateCells':sum(len(v) for v in C.values()),'holds':sum(v['disposition']=='hold' for v in plan.values()),'correctionsByOrdinal':{str(k):len(v) for k,v in C.items()}},ensure_ascii=False,indent=2))
