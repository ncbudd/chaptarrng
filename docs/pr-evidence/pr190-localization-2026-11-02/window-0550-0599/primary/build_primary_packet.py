import collections, hashlib, json, pathlib, re, subprocess, sys

W = pathlib.Path('/mnt/disks/scratch/task-worktrees/localization-20261102/chaptarrng-pr190-audit')
O = pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0550-0599-primary-20261102')
REPO = 'snapetech-org/chaptarrng'
PR = 190
EXPECTED_HEAD = '015ff68d96340292b5e6a45d34496a5936ebf09c'
EXPECTED_TREE = 'bbb59a14a50a4b63bc209663c1e4b873ead4fc10'
LOCALES = {'es':'es.json','zh-Hans':'zh_CN.json','hi':'hi.json','de':'de.json','ja':'ja.json','fr':'fr.json','pt-BR':'pt_BR.json','ar':'ar.json','ko':'ko.json','zh-Hant':'zh_TW.json','vi':'vi.json','id':'id.json'}
EXPECTED_IDS = [
 'server.message.m3f41c8ff49b3','server.message.m4091c9160593','server.message.m4292967cbf4d','server.message.m42d5ddf06dd0','server.message.m42e93ada21fc',
 'server.message.m43ae665db439','server.message.m43c9baeb5bdb','server.message.m43d6f014b47d','server.message.m4410286171ba','server.message.m44eab1fb9fa7',
 'server.message.m451006253bc3','server.message.m453c42aa8de5','server.message.m45461e168bdc','server.message.m4588c1c26dfc','server.message.m45d06dda48d1',
 'server.message.m460fd8e957c3','server.message.m467034a6f197','server.message.m475d30ecce8d','server.message.m476ad43ed2ca','server.message.m47ae9dc63c7a',
 'server.message.m47cc7c36cc3a','server.message.m48c9cd18eeef','server.message.m4a0e0348191a','server.message.m4abee5a92d01','server.message.m4b31cd0afb3b',
 'server.message.m4ba2d178c305','server.message.m4bbe30648055','server.message.m4c39fed9b779','server.message.m4c93d9a5340f','server.message.m4d485e3d4216',
 'server.message.m4d53a6152d2c','server.message.m4d72bec4a155','server.message.m4e3c9ff3f17f','server.message.m4e7b049867d0','server.message.m4f132daa439b',
 'server.message.m4f860894ff1b','server.message.m50abcbe9b4b1','server.message.m50b0fb9b570d','server.message.m512fa7acd5fa','server.message.m5269a817943e',
 'server.message.m52a644e8b0f9','server.message.m532212ccb76d','server.message.m535af50a7541','server.message.m537621bd08c4','server.message.m54f76bea32a1',
 'server.message.m54fc8a254d62','server.message.m55acf0a44748','server.message.m5659b793dc5f','server.message.m57a345f27938','server.message.m580ff695754e'
]

# Proposed exact target strings. Unlisted cells were independently reviewed and accepted as-is.
PROPOSALS = {
 551:{'hi':'केवल ऑडियोबुक वाले फ़ोल्डरों में ई-बुक सेटिंग नहीं हो सकतीं।','de':'Ordner, die nur Hörbücher enthalten, dürfen keine E-Book-Einstellungen haben.','ja':'オーディオブック専用フォルダーには電子書籍の設定を適用できません。','ar':'لا يمكن أن تحتوي المجلدات المخصصة للكتب الصوتية فقط على إعدادات الكتب الإلكترونية.','ko':'오디오북 전용 폴더에는 전자책 설정을 지정할 수 없습니다.'},
 552:{'es':'El proxy está configurado como ProxyEverything. Esto debería funcionar, pero se recomienda IndexerOnly para obtener un mejor rendimiento.','zh-Hans':'代理设置为 ProxyEverything。该设置应该可以正常工作，但为了获得更好的性能，建议使用 IndexerOnly。','hi':'प्रॉक्सी ProxyEverything पर सेट है। यह काम करना चाहिए, लेकिन बेहतर प्रदर्शन के लिए IndexerOnly की सिफ़ारिश की जाती है।','ja':'Proxy は ProxyEverything に設定されています。動作するはずですが、パフォーマンス向上のため IndexerOnly を推奨します。','fr':'Le proxy est configuré sur ProxyEverything. Cela devrait fonctionner, mais IndexerOnly est recommandé pour de meilleures performances.','pt-BR':'O proxy está configurado como ProxyEverything. Isso deve funcionar, mas IndexerOnly é recomendado para melhor desempenho.','zh-Hant':'Proxy 設定為 ProxyEverything。這應該可以正常運作，但為了提升效能，建議使用 IndexerOnly。','vi':'Proxy được đặt thành ProxyEverything. Cấu hình này sẽ hoạt động, nhưng nên dùng IndexerOnly để có hiệu suất tốt hơn.','id':'Proxy diatur ke ProxyEverything. Ini seharusnya berfungsi, tetapi IndexerOnly disarankan untuk kinerja yang lebih baik.'},
 554:{'es':'No se encontró la serie {value0}.','hi':'श्रृंखला {value0} नहीं मिली।','ja':'シリーズ {value0} が見つかりません。','vi':'Không tìm thấy bộ truyện {value0}.'},
 555:{'pt-BR':'Não foi possível aplicar o narrador a todos os livros da série.','vi':'Không thể áp dụng người kể chuyện cho tất cả sách trong bộ truyện.','id':'Gagal menerapkan narator ke semua buku trong seri.'},
 556:{'es':'La URL del servidor de metadatos debe comenzar con http:// o https://.','de':'Die URL des Metadatenservers muss mit http:// oder https:// beginnen.','fr':'L’URL du serveur de métadonnées doit commencer par http:// ou https://.','pt-BR':'A URL do servidor de metadados deve começar com http:// ou https://.','ar':'يجب أن يبدأ عنوان URL لخادم البيانات الوصفية بـ http:// أو https://.','ko':'메타데이터 서버 URL은 http:// 또는 https://로 시작해야 합니다.','vi':'URL của máy chủ siêu dữ liệu phải bắt đầu bằng http:// hoặc https://.','id':'URL server metadata harus diawali dengan http:// atau https://.'},
 557:{'hi':'मेटाडेटा रिफ्रेश की पूर्व-जाँच विफल होने के कारण लेखक को फिर से नहीं जोड़ा जा सकता। मौजूदा लेखक को हटाया नहीं गया।','ja':'メタデータ更新の事前チェックに失敗したため、著者を再追加できません。既存の著者は削除されていません。','vi':'Không thể thêm lại tác giả vì bước kiểm tra trước khi làm mới siêu dữ liệu thất bại. Tác giả hiện có chưa bị xóa.','id':'Penulis tidak dapat ditambahkan kembali karena pemeriksaan awal penyegaran metadata gagal. Penulis yang sudah ada tidak dihapus.'},
 559:{'es':'No se pudo conectar a la lista de importación: {value0}. Consulta las entradas del registro alrededor de este error para obtener más detalles.','zh-Hans':'无法连接到导入列表：{value0}。请查看此错误附近的日志以了解详情。','hi':'आयात सूची से कनेक्ट नहीं हो सका: {value0}। अधिक जानकारी के लिए इस त्रुटि के आसपास की लॉग प्रविष्टियाँ देखें।','de':'Verbindung zur Importliste nicht möglich: {value0}. Weitere Informationen finden Sie in den Protokolleinträgen zu diesem Fehler.','ja':'インポートリストに接続できません: {value0}。詳細は、このエラー前後のログを確認してください。','fr':'Impossible de se connecter à la liste d’importation : {value0}. Consultez les entrées du journal autour de cette erreur pour plus de détails.','pt-BR':'Não foi possível conectar à lista de importação: {value0}. Consulte os registros próximos a este erro para obter mais detalhes.','ar':'تعذّر الاتصال بقائمة الاستيراد: {value0}. راجع السجلات المحيطة بهذا الخطأ لمعرفة التفاصيل.','ko':'가져오기 목록에 연결할 수 없습니다: {value0}. 자세한 내용은 이 오류 전후의 로그를 확인하세요.','zh-Hant':'無法連線至匯入清單：{value0}。請查看此錯誤附近的日誌以瞭解詳情。','id':'Tidak dapat terhubung ke daftar impor: {value0}. Periksa entri log di sekitar kesalahan ini untuk mengetahui detailnya.'},
 560:{'es':'No se pudo obtener la lista de torrents: {value0}','zh-Hans':'未能获取种子列表：{value0}','de':'Die Torrent-Liste konnte nicht abgerufen werden: {value0}','pt-BR':'Não foi possível obter a lista de torrents: {value0}','ko':'토렌트 목록을 가져오지 못했습니다: {value0}','zh-Hant':'未能取得種子清單：{value0}','vi':'Không thể lấy danh sách torrent: {value0}'},
 561:{'es':'El valor de KeepHistory en NzbGet debe ser inferior a 25000.','zh-Hans':'NzbGet 的 KeepHistory 设置必须小于 25000。','hi':'NzbGet में KeepHistory सेटिंग 25000 से कम होनी चाहिए।','de':'Die NzbGet-Einstellung KeepHistory muss kleiner als 25000 sein.','ja':'NzbGet の KeepHistory 設定は 25000 未満である必要があります。','fr':'La valeur du paramètre KeepHistory dans NzbGet doit être inférieure à 25000.','pt-BR':'O valor da configuração KeepHistory no NzbGet deve ser menor que 25000.','ar':'يجب أن تكون قيمة إعداد KeepHistory في NzbGet أقل من 25000.','ko':'NzbGet의 KeepHistory 설정값은 25000보다 작아야 합니다.','zh-Hant':'NzbGet 的 KeepHistory 設定必須小於 25000。','vi':'Giá trị cài đặt KeepHistory trong NzbGet phải nhỏ hơn 25000.','id':'Nilai pengaturan KeepHistory di NzbGet harus kurang dari 25000.'},
 562:{'zh-Hans':'所选根文件夹仅用于电子书；请选择用于有声书或混合媒体的根文件夹。','ja':'選択したルートフォルダーは電子書籍専用です。有声書または混合メディア用のルートフォルダーを選択してください。','fr':'Le dossier racine sélectionné est réservé aux livres numériques ; choisissez un dossier racine pour livres audio ou pour les deux formats.','ar':'مجلد الجذر المحدد مخصص للكتب الإلكترونية فقط؛ اختر مجلدًا جذريًا للكتب الصوتية أو للمحتوى المختلط.','ko':'선택한 루트 폴더는 전자책 전용입니다. 오디오북 또는 혼합 미디어용 루트 폴더를 선택하세요.','zh-Hant':'所選根資料夾僅供電子書使用；請選擇供有聲書或混合媒體使用的根資料夾。','id':'Folder root yang dipilih khusus untuk e-book; pilih folder root untuk buku audio atau media campuran.'},
 563:{'zh-Hans':'无法获取 Goodreads 书架。请检查用户 ID，并确认书架已设为公开。','ja':'Goodreads の本棚を取得できません。ユーザー ID と、本棚が公開設定になっていることを確認してください。','ar':'تعذّر استرداد رفوف Goodreads. تحقّق من معرّف المستخدم (ID) ومن أن الرفوف عامة.','zh-Hant':'無法取得 Goodreads 書架。請檢查使用者 ID，並確認書架已設為公開。'},
 564:{'zh-Hans':'必须是有效的主机，且不能包含 http://','fr':'L’hôte doit être valide et ne pas inclure http://.','pt-BR':'O host deve ser válido e não pode incluir http://.','vi':'Host phải hợp lệ và không được chứa http://.'},
 565:{'zh-Hans':'似乎需要 SSL','ja':'SSL が必要なようです。','ko':'SSL이 필요한 것 같습니다.','zh-Hant':'似乎需要 SSL'},
 566:{'es':'No se pudo conectar al servidor Subsonic.','zh-Hans':'无法连接到 Subsonic 服务器。','de':'Es konnte keine Verbindung zum Subsonic-Server hergestellt werden.','ja':'Subsonic サーバーに接続できません。','pt-BR':'Não foi possível conectar ao servidor Subsonic.','ar':'تعذّر الاتصال بخادم Subsonic.','ko':'Subsonic 서버에 연결할 수 없습니다.','zh-Hant':'無法連線至 Subsonic 伺服器。','vi':'Không thể kết nối với máy chủ Subsonic.','id':'Tidak dapat terhubung ke server Subsonic.'},
 567:{'es':'Debe ser 0 para desactivar o un valor entre 10 y 120 minutos.','zh-Hans':'设为 0 可禁用，否则必须为 10 到 120 分钟。','de':'Zum Deaktivieren muss der Wert 0 sein, andernfalls zwischen 10 und 120 Minuten liegen.','fr':'La valeur doit être 0 pour désactiver, ou comprise entre 10 et 120 minutes.','pt-BR':'O valor deve ser 0 para desativar ou estar entre 10 e 120 minutos.','ar':'يجب أن تكون القيمة 0 للتعطيل، أو بين 10 و120 دقيقة.','ko':'사용하지 않으려면 0으로 설정하고, 그 외에는 10~120분으로 설정해야 합니다.','zh-Hant':'設為 0 可停用，否則必須介於 10 至 120 分鐘之間。','vi':'Giá trị phải là 0 để tắt, hoặc nằm trong khoảng từ 10 đến 120 phút.'},
 568:{'zh-Hans':'请传入 1 到 500 个正数 sourceIds。','zh-Hant':'請傳入 1 到 500 個正值 sourceIds。'},
 569:{'de':'Ein API-Token ist erforderlich.','fr':'Un jeton API est requis.','pt-BR':'É necessário informar um token de API.','vi':'Cần có token API.','id':'Token API wajib diisi.'},
 570:{'es':'El cliente de uTorrent es antiguo y no admite esta API; se requiere la versión 3.0 o posterior.','zh-Hans':'此 uTorrent 客户端版本过旧，所用 API 不受支持；需要 3.0 或更高版本。','de':'Der uTorrent-Client ist veraltet und unterstützt diese API nicht. Erforderlich ist Version 3.0 oder höher.','ja':'この uTorrent クライアントは古く、API がサポートされていません。バージョン 3.0 以降が必要です。','fr':'Le client uTorrent est trop ancien et son API n’est pas prise en charge ; la version 3.0 ou ultérieure est requise.','pt-BR':'O cliente uTorrent é antigo e a API não é compatível; é necessária a versão 3.0 ou superior.','ar':'عميل uTorrent قديم ولا يدعم واجهة API هذه؛ يلزم الإصدار 3.0 أو أحدث.','ko':'uTorrent 클라이언트가 오래되어 이 API를 지원하지 않습니다. 버전 3.0 이상이 필요합니다.','zh-Hant':'此 uTorrent 用戶端版本過舊，API 不受支援；需要 3.0 或更新版本。','vi':'Ứng dụng khách uTorrent đã cũ và không hỗ trợ API này; cần phiên bản 3.0 trở lên.','id':'Klien uTorrent sudah lama dan tidak mendukung API ini; diperlukan versi 3.0 atau lebih baru.'},
 571:{'zh-Hant':'模式為必填項。','id':'Pola wajib diisi.'},
 572:{'es':'El ID de la ruta no coincide con el ID del recurso.','zh-Hans':'路由 ID 与资源 ID 不匹配。','hi':'रूट का ID संसाधन के ID से मेल नहीं खाता।','de':'Die ID in der Route stimmt nicht mit der Ressourcen-ID überein.','ja':'ルートの ID がリソースの ID と一致しません。','pt-BR':'O ID da rota não corresponde ao ID do recurso.','ar':'لا يتطابق معرّف المسار مع معرّف المورد.','zh-Hant':'路由 ID 與資源 ID 不符。','vi':'ID trong tuyến đường không khớp với ID của tài nguyên.','id':'ID rute tidak cocok dengan ID sumber daya.'},
 573:{'es':'No se pudo conectar a Transmission.','de':'Es konnte keine Verbindung zu Transmission hergestellt werden.','pt-BR':'Não foi possível conectar ao Transmission.','ar':'تعذّر الاتصال بـ Transmission.','ko':'Transmission에 연결할 수 없습니다.'},
 574:{'zh-Hans':'文件夹“{value0}”不存在。请先创建该目录或检查路径。','hi':"फ़ोल्डर '{value0}' मौजूद नहीं है। कृपया पहले निर्देशिका बनाएँ या पथ जाँचें।",'zh-Hant':'資料夾「{value0}」不存在。請先建立該目錄或檢查路徑。','id':"Folder '{value0}' tidak ada. Silakan buat direktori terlebih dahulu atau periksa jalurnya."},
 575:{'zh-Hans':'必须是有效的绝对 URL。','pt-BR':'Deve ser uma URL absoluta válida.','ar':'يجب أن يكون عنوان URL مطلقًا وصالحًا.','ko':'유효한 절대 URL이어야 합니다.','id':'Harus berupa URL absolut yang valid.'},
 576:{'ja':'フォルダーが存在しません。','ar':'المجلد غير موجود.','ko':'폴더가 존재하지 않습니다.','zh-Hant':'資料夾不存在。'},
 577:{'es':'No se pudo importar el autor del proveedor.','zh-Hans':'未能从提供方导入作者。','de':'Der Autor konnte nicht vom Anbieter importiert werden.','fr':'L’auteur n’a pas pu être importé depuis le fournisseur.','pt-BR':'Não foi possível importar o autor do provedor.','zh-Hant':'未能從提供者匯入作者。','vi':'Không thể nhập tác giả từ nhà cung cấp.'},
 578:{'es':'No se pudieron obtener los datos de la serie.','de':'Die Seriendaten konnten nicht abgerufen werden.','fr':'Impossible d’obtenir les données de la série.','pt-BR':'Não foi possível obter os dados da série.','ar':'تعذّر الحصول على بيانات السلسلة.','id':'Tidak dapat memperoleh data seri.'},
 579:{'zh-Hans':'请求正文不能为空。','hi':'अनुरोध का मुख्य भाग खाली नहीं हो सकता।','fr':'Le corps de la requête ne peut pas être vide.','pt-BR':'O corpo da solicitação não pode ficar vazio.','zh-Hant':'請求本文不能為空。'},
 580:{'es':'Previsualiza el traslado antes de iniciarlo.','zh-Hans':'开始移动前先预览移动操作。','hi':'स्थानांतरण शुरू करने से पहले उसका पूर्वावलोकन करें।','zh-Hant':'開始移動前先預覽移動操作。','vi':'Xem trước thao tác di chuyển trước khi bắt đầu.','id':'Pratinjau proses pemindahan sebelum memulainya.'},
 581:{'es':'La clave de API es incorrecta.','hi':'API कुंजी गलत है।','de':'Der API-Schlüssel ist falsch.','ja':'API キーが正しくありません。','fr':'La clé API est incorrecte.','pt-BR':'A chave de API está incorreta.','ar':'مفتاح API غير صحيح.','ko':'API 키가 잘못되었습니다.','vi':'Khóa API không chính xác.','id':'Kunci API salah.'},
 582:{'ko':'entityType 값은 Author, AuthorMetadata, Book, Edition 또는 BookFile이어야 합니다.'},
 583:{'es':'La prueba del proxy a través de {value0} falló con el código de estado {value1}.','zh-Hans':'通过 {value0} 的代理测试失败，状态码为 {value1}。','de':'Der Proxytest über {value0} ist mit Statuscode {value1} fehlgeschlagen.','ja':'{value0} 経由のプロキシテストに失敗しました（ステータスコード: {value1}）。','fr':'Le test du proxy via {value0} a échoué avec le code d’état {value1}.','pt-BR':'O teste do proxy por {value0} falhou com o código de status {value1}.','ar':'فشل اختبار الوكيل عبر {value0} برمز الحالة {value1}.','ko':'프록시 테스트가 실패했습니다. 경유 주소: {value0}, 상태 코드: {value1}.','zh-Hant':'透過 {value0} 的代理測試失敗，狀態碼為 {value1}。','vi':'Thử nghiệm proxy qua {value0} thất bại với mã trạng thái {value1}.','id':'Tes proxy melalui {value0} gagal dengan kode status {value1}.'},
 584:{'hi':'प्रमाणीकरण विफल हुआ। API कुंजी और सर्वर का प्रकार जाँचें।','zh-Hans':'身份验证失败。请检查 API 密钥和服务器类型。','ko':'인증에 실패했습니다. API 키와 서버 유형을 확인하세요.','zh-Hant':'驗證失敗。請檢查 API 金鑰和伺服器類型。'},
 585:{'es':'La respuesta al ping del servidor de metadatos no era un JSON válido: {value0}','hi':'मेटाडेटा सर्वर के पिंग का जवाब मान्य JSON नहीं था: {value0}','de':'Die Ping-Antwort des Metadatenservers war kein gültiges JSON: {value0}','ja':'メタデータサーバーの ping 応答は有効な JSON ではありませんでした: {value0}','fr':'La réponse au ping du serveur de métadonnées n’était pas un JSON valide : {value0}','pt-BR':'A resposta ao ping do servidor de metadados não era um JSON válido: {value0}','ar':'كانت استجابة ping من خادم البيانات الوصفية بصيغة JSON غير صالحة: {value0}','ko':'메타데이터 서버의 ping 응답이 유효한 JSON이 아닙니다: {value0}','zh-Hant':'中繼資料伺服器的 ping 回應不是有效的 JSON：{value0}','vi':'Phản hồi ping của máy chủ siêu dữ liệu không phải là JSON hợp lệ: {value0}','id':'Respons ping dari server metadata bukan JSON yang valid: {value0}'},
 586:{'zh-Hans':'目前仅支持 Hardcover 系列 ID（预期格式：hc:{id}）。','ja':'現在は Hardcover シリーズ ID のみ対応しています（想定形式: hc:{id}）。','ar':'تُدعم حاليًا معرّفات سلاسل Hardcover فقط (الصيغة المتوقعة: hc:{id}).','zh-Hant':'目前僅支援 Hardcover 系列 ID（預期格式：hc:{id}）。','vi':'Hiện chỉ hỗ trợ ID sê-ri Hardcover (định dạng dự kiến: hc:{id}).','id':'Saat ini hanya ID seri Hardcover yang didukung (format yang diharapkan: hc:{id}).'},
 587:{'es':'Se requiere la URL del servidor de metadatos.','hi':'मेटाडेटा सर्वर का URL आवश्यक है।','de':'Die URL des Metadatenservers ist erforderlich.','fr':'L’URL du serveur de métadonnées est obligatoire.','pt-BR':'A URL do servidor de metadados é obrigatória.','ko':'메타데이터 서버 URL이 필요합니다.','vi':'Cần có URL của máy chủ siêu dữ liệu.','id':'URL untuk server metadata wajib diisi.'},
 588:{'es':'No se pudo conectar a Emby/Jellyfin: {value0}','de':'Es konnte keine Verbindung zu Emby/Jellyfin hergestellt werden: {value0}','pt-BR':'Não foi possível conectar a Emby/Jellyfin: {value0}','ar':'تعذّر الاتصال بـ Emby/Jellyfin: {value0}'},
 589:{'zh-Hans':'请先通过 Plex.tv 进行身份验证。','zh-Hant':'請先透過 Plex.tv 進行驗證。'},
 591:{'zh-Hans':'图片已成功下载。','hi':'छवि सफलतापूर्वक डाउनलोड हुई।','de':'Das Bild wurde erfolgreich heruntergeladen.','ja':'画像を正常にダウンロードしました。','pt-BR':'Imagem baixada com sucesso.','ar':'تم تنزيل الصورة بنجاح.','ko':'이미지가 성공적으로 다운로드되었습니다.','zh-Hant':'圖片已成功下載。'},
 592:{'es':'Debe contener chaptarr.'},
 593:{'de':'Das Bild wurde nicht in den Metadaten des Autors gefunden.','ko':'저자 메타데이터에서 이미지를 찾을 수 없습니다.','vi':'Không tìm thấy hình ảnh trong siêu dữ liệu của tác giả.','id':'Gambar tidak ditemukan dalam metadata penulis.'},
 595:{'es':'La descarga de la imagen está en curso.','zh-Hans':'正在下载图像。','hi':'छवि डाउनलोड हो रही है।','de':'Das Bild wird heruntergeladen.','ja':'画像をダウンロード中です。','ar':'جارٍ تنزيل الصورة.','ko':'이미지를 다운로드하는 중입니다.','zh-Hant':'正在下載圖像。'},
 597:{'es':'La edición seleccionada no coincide con el tipo de medio solicitado.','ar':'الإصدار المحدد لا يتطابق مع نوع الوسائط المطلوب.'},
 598:{'es':'La clave de API es incorrecta.','zh-Hans':'API 密钥不正确。','hi':'API कुंजी गलत है।','de':'Der API-Schlüssel ist falsch.','ja':'API キーが正しくありません。','fr':'La clé API est incorrecte.','pt-BR':'A chave de API está incorreta.','ar':'مفتاح API غير صحيح.','ko':'API 키가 잘못되었습니다.','zh-Hant':'API 金鑰不正確。','vi':'Khóa API không chính xác.','id':'Kunci API salah.'},
 599:{'es':'No se pudo conectar a SABnzbd.','de':'Es konnte keine Verbindung zu SABnzbd hergestellt werden.','ja':'SABnzbd に接続できません。','pt-BR':'Não foi possível conectar ao SABnzbd.','ar':'تعذّر الاتصال بـ SABnzbd.','ko':'SABnzbd에 연결할 수 없습니다.'}
}
REFINEMENTS = {(552,'es'),(552,'hi'),(552,'ja'),(552,'fr'),(552,'de'),(558,'es'),(563,'ja'),(564,'zh-Hans'),(565,'ja'),(565,'ko'),(568,'zh-Hans'),(568,'zh-Hant'),(571,'zh-Hant'),(574,'zh-Hans'),(574,'zh-Hant'),(575,'zh-Hans'),(576,'zh-Hant'),(579,'pt-BR'),(580,'zh-Hans'),(580,'zh-Hant'),(582,'ko'),(584,'zh-Hans'),(584,'zh-Hant'),(586,'zh-Hans'),(586,'zh-Hant'),(589,'zh-Hans'),(589,'zh-Hant'),(591,'zh-Hans'),(591,'zh-Hant'),(593,'ko'),(595,'zh-Hans'),(595,'zh-Hant'),(597,'es')}

PROTECTED = {
 550:['authorId'],552:['ProxyEverything','IndexerOnly'],554:['{value0}'],556:['http://','https://'],559:['{value0}'],560:['{value0}'],
 561:['NzbGet','KeepHistory','25000'],563:['Goodreads','ID'],564:['http://'],565:['SSL'],566:['Subsonic'],
 567:['0','10','120'],568:['sourceIds','1','500'],569:['API'],570:['uTorrent','3.0'],
 574:['{value0}'],581:['API'],582:['entityType','Author','AuthorMetadata','Book','Edition','BookFile'],
 583:['{value0}','{value1}'],584:['API'],585:['JSON','{value0}'],586:['Hardcover','hc:{id}'],587:['URL'],
 588:['Emby','Jellyfin','{value0}'],589:['Plex.tv'],590:['selectedBooks','foreignAuthorId'],592:['chaptarr'],
 594:['http://','https://'],596:['selectedMediaType',"'audiobook'","'ebook'"],599:['SABnzbd']
}

# For rows whose message key is absent from C# the exact English source text or template is pinned.
FALLBACKS = {
 550:[('Message = "authorId is required."','source-text-exact','src/Chaptarr.Api.V1/Books/ConvertBookController.cs')],
 551:[('Audiobook-only folders cannot have ebook settings','source-text-exact','src/Chaptarr.Api.V1/RootFolders/RootFolderResource.cs')],
 552:[('Proxy is set to ProxyEverything. This should work but IndexerOnly is recommended for better performance.','source-text-exact','src/Chaptarr.Api.V1/System/ProxyDebugController.cs')],
 555:[('Failed to apply narrator to all books in series','source-text-exact','src/Chaptarr.Api.V1/Series/SeriesController.cs')],
 556:[('Metadata server URL must start with http:// or https://','source-text-exact','src/Chaptarr.Api.V1/Config/DevelopmentConfigController.cs')],
 557:[('Cannot re-add author because the metadata refresh preflight failed. The existing author was not deleted.','source-text-exact','src/Chaptarr.Api.V1/Author/AuthorController.cs')],
 558:[('qBittorrent is reporting an error','source-text-exact','src/NzbDrone.Core/Download/Clients/QBittorrent/QBittorrent.cs')],
 567:[('Must be 0 to disable or between 10 and 120 minutes','normalized-validator-template','src/Chaptarr.Http/Validation/RssSyncIntervalValidator.cs'),('.SetValidator(new RssSyncIntervalValidator())','validator-binding','src/Chaptarr.Http/Validation/RuleBuilderExtensions.cs'),('.IsValidRssSyncInterval();','validator-consumer','src/Chaptarr.Api.V1/Config/IndexerConfigController.cs')],
 568:[('Pass between 1 and 500 positive sourceIds.','source-text-exact','src/Chaptarr.Api.V1/BookShelf/BookshelfController.cs')],
 569:[('API token is required','source-text-exact','src/Chaptarr.Api.V1/Config/HardcoverConfigController.cs')],
 571:[('pattern is required','source-text-exact','src/Chaptarr.Api.V1/Config/NamingPatternController.cs')],
 572:[('Route id does not match resource id','source-text-exact','src/Chaptarr.Http/REST/RestController.cs')],
 574:[('Folder \'{path}\' does not exist. Please create the directory first or check the path.','normalized-validation-template','src/NzbDrone.Core/Validation/Paths/FolderReadableValidator.cs')],
 575:[('Must be a valid absolute URL','source-text-exact','src/Chaptarr.Api.V1/Config/HostConfigController.cs')],
 577:[('Failed to import author from provider','source-text-exact','src/Chaptarr.Api.V1/Author/AuthorController.cs')],
 579:[("Request body can't be empty",'source-text-exact','src/Chaptarr.Api.V1/ManualImport/ManualImportController.cs'),("Request body can't be empty",'source-text-exact','src/Chaptarr.Api.V1/Author/AuthorMediaMoveController.cs')],
 580:[('Preview the move before starting it.','source-text-exact','src/Chaptarr.Api.V1/Author/AuthorMediaMoveController.cs')],
 582:[('entityType must be Author, AuthorMetadata, Book, Edition, or BookFile.','source-text-exact','src/Chaptarr.Api.V1/BookShelf/BookshelfController.cs')],
 583:[('Proxy test failed via {testUrl} with status code: {response.StatusCode}','source-text-fragment','src/NzbDrone.Core/Configuration/ProxyTestService.cs')],
 585:[('Metadata server ping response was not valid JSON: {ex.Message}','source-text-fragment','src/Chaptarr.Api.V1/Config/DevelopmentConfigController.cs')],
 586:[('Only Hardcover series IDs are currently supported (expected hc:{id})','source-text-exact','src/Chaptarr.Api.V1/Series/SeriesLookupController.cs')],
 587:[('Metadata server URL is required','source-text-exact','src/Chaptarr.Api.V1/Config/DevelopmentConfigController.cs')],
 591:[('Image downloaded successfully','source-text-exact','src/Chaptarr.Api.V1/Author/AuthorController.cs')],
 592:[('Must contain chaptarr','source-text-exact','src/NzbDrone.Core/Validation/RuleBuilderExtensions.cs'),('.ContainsChaptarr()','validator-consumer','src/Chaptarr.Api.V1/Config/HostConfigController.cs')],
 593:[('Image not found in author metadata','source-text-exact','src/Chaptarr.Api.V1/Author/AuthorController.cs')],
 594:[('Metadata server URL must start with http:// or https://','source-text-fragment','src/Chaptarr.Api.V1/Config/DevelopmentConfigController.cs')],
 595:[('Image download in progress','source-text-exact','src/Chaptarr.Api.V1/Author/AuthorController.cs')],
 597:[('Selected edition does not match the requested media type.','source-text-exact','src/Chaptarr.Api.V1/ManualImport/ManualImportController.cs')]
}


def run(args, text=True):
  return subprocess.check_output(args, text=text)
def sha(b): return hashlib.sha256(b).hexdigest()
def jbytes(x): return json.dumps(x,ensure_ascii=False,separators=(',',':')).encode()
def git(*args, text=True): return run(['git','-C',str(W),*args],text=text)
def read_git(path): return git('show',f'HEAD:{path}',text=False)
def tracked_info(path):
  b=read_git(path)
  return {'path':path,'blob':git('rev-parse',f'HEAD:{path}').strip(),'sha256':sha(b),'bytes':len(b)}
def save_json(path,obj): (O/path).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def save_jsonl(path,rows): (O/path).write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in rows))
def placeholders(s): return sorted(set(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s)))
def markup(s):
  if re.fullmatch(r'<[^<>/]+>',s): return []
  return re.findall(r'</?[A-Za-z][^>]*>',s)
def live_pr():
  pr=json.loads(run(['gh','pr','view',str(PR),'--repo',REPO,'--json','state,isDraft,headRefOid,headRefName,baseRefOid,url']))
  tree=run(['gh','api',f'repos/{REPO}/commits/{pr["headRefOid"]}','--jq','.commit.tree.sha']).strip()
  return pr,tree

head=git('rev-parse','HEAD').strip(); tree=git('rev-parse','HEAD^{tree}').strip()
if head!=EXPECTED_HEAD or tree!=EXPECTED_TREE: raise SystemExit(f'expected pinned head/tree {EXPECTED_HEAD}/{EXPECTED_TREE}; found {head}/{tree}')
pr, live_tree=live_pr()
if pr['headRefOid']!=head or live_tree!=tree or pr['state']!='OPEN' or not pr['isDraft']:
  raise SystemExit('live PR preflight mismatch: '+json.dumps({'pr':pr,'tree':live_tree}))
if git('status','--porcelain').strip(): raise SystemExit('worktree is not clean; refusing scratch packet build')

source_path='src/NzbDrone.Core/Localization/Core/en.json'
source_bytes=read_git(source_path); source_catalog=json.loads(source_bytes)
follow_path='docs/localization/source-followup-20261101.json'; follow_bytes=read_git(follow_path); follow=json.loads(follow_bytes); ids=follow['currentMissingIds']
if len(ids)!=1210 or len(set(ids))!=1210: raise SystemExit('source follow-up inventory drift')
source_ids=ids[550:600]
if source_ids!=EXPECTED_IDS: raise SystemExit('W550–599 source ID boundary drift: '+json.dumps(source_ids))
registry_path='docs/localization/provider-field-sources.json'; registry_bytes=read_git(registry_path); registry=json.loads(registry_bytes); reg_by={x['id']:x for x in registry['records']}
catalogs={}; catalog_info={}
for loc,file in LOCALES.items():
  path=f'src/NzbDrone.Core/Localization/Core/{file}'; b=read_git(path); catalogs[loc]=json.loads(b); catalog_info[loc]=tracked_info(path)
  if set(catalogs[loc])!=set(source_catalog): raise SystemExit(f'catalog key inventory drift for {loc}')
source_info=tracked_info(source_path); follow_info=tracked_info(follow_path); registry_info=tracked_info(registry_path)

# Search only production C# trees. Key-based matches are exact; absent-key rows use reviewed literal/template pins.
roots=[str(W/'src/NzbDrone.Core'),str(W/'src/Chaptarr.Api.V1'),str(W/'src/Chaptarr.Http')]
def find_needle(needle, path=None):
  paths=[str(W/path)] if path else roots
  cmd=['rg','--no-heading','--color','never','--with-filename','-n','-F','-e',needle,'--glob','*.cs',*paths]
  p=subprocess.run(cmd,text=True,capture_output=True)
  if p.returncode not in (0,1): raise SystemExit('caller search failed: '+p.stderr)
  out=[]
  for row in p.stdout.splitlines():
    try: fp,lineno,line=row.split(':',2); n=int(lineno)
    except ValueError: continue
    rel=str(pathlib.Path(fp).resolve().relative_to(W.resolve()))
    out.append((rel,n,line))
  return out

raw=collections.defaultdict(list)
for ordinal,sid in enumerate(source_ids,550):
  for fp,n,line in find_needle(sid): raw[sid].append((fp,n,line,'exact-source-id'))
for ordinal,rules in FALLBACKS.items():
  sid=source_ids[ordinal-550]
  for needle,mode,expected_path in rules:
    hits=find_needle(needle,expected_path)
    if not hits: raise SystemExit(f'caller pin missing for {ordinal} {sid}: {needle}')
    for fp,n,line in hits:
      if fp!=expected_path: raise SystemExit(f'caller pin path drift for {ordinal}: {fp} != {expected_path}')
      raw[sid].append((fp,n,line,mode))
# The generic RSS interval and Chaptarr instance-name rows have their validation consumers pinned above.

caller_rows=[]; callers_by_id={}; caller_gaps=[]; caller_mismatches=[]; unique_files=set(); total_refs=0
for ordinal,sid in enumerate(source_ids,550):
  refs=[]; seen=set()
  for fp,n,line,mode in sorted(raw.get(sid,[]),key=lambda x:(x[0],x[1],x[3])):
    if (fp,n) in seen: continue
    seen.add((fp,n)); content=read_git(fp); lines=content.decode('utf-8').splitlines()
    if not 1<=n<=len(lines) or lines[n-1]!=line:
      caller_mismatches.append({'sourceOrdinal':ordinal,'sourceId':sid,'file':fp,'line':n,'reason':'lookup line differs from pinned HEAD content'}); continue
    unique_files.add(fp); total_refs+=1
    refs.append({'file':fp,'kind':mode,'currentLine':n,'lineMatchMethod':mode,'matchedSourceId':sid if mode=='exact-source-id' else None,'matchedSourceText':source_catalog[sid] if mode!='exact-source-id' else None,'currentLineText':line,'currentLineSha256':sha(line.encode()),'contextBefore':lines[max(0,n-3):n-1],'contextAfter':lines[n:min(len(lines),n+2)],'currentFileBlob':git('rev-parse',f'HEAD:{fp}').strip(),'currentFileSha256':sha(content)})
  if not refs: caller_gaps.append({'sourceOrdinal':ordinal,'sourceId':sid,'reason':'no production source key or approved literal/template caller pin'})
  callers_by_id[sid]=refs
  rec=reg_by.get(sid)
  row={'sourceOrdinal':ordinal,'sourceId':sid,'attestedHead':head,'attestedTree':tree,'sourceText':source_catalog[sid],'sourceFile':source_path,'sourceFileBlob':source_info['blob'],'sourceFileSha256':source_info['sha256'],'sourceFingerprint':rec.get('sourceFingerprint') if rec else None,'callerReferenceStatus':'pinned' if refs else 'gap','callerRefs':refs,'callerContextSha256':sha(jbytes(refs))}
  caller_rows.append(row)
if caller_gaps or caller_mismatches: raise SystemExit('caller coverage problem: '+json.dumps({'gaps':caller_gaps,'mismatches':caller_mismatches},ensure_ascii=False))

source_rows=[]; input_rows=[]; review_rows=[]; literal_rows=[]
source_id_hash=sha(jbytes(ids)); cat_paths={'en':source_path,**{loc:f'src/NzbDrone.Core/Localization/Core/{file}' for loc,file in LOCALES.items()}}
for ordinal,sid in enumerate(source_ids,550):
  src=source_catalog[sid]; source_ph=placeholders(src); source_markup=markup(src); protected=PROTECTED.get(ordinal,[])
  srow={'sourceOrdinal':ordinal,'sourceId':sid,'source':src,'sourceKeySha256':sha(sid.encode()),'sourceTextSha256':sha(src.encode()),'sourceFile':source_path,'sourceFileBlob':source_info['blob'],'sourceFileSha256':source_info['sha256'],'sourceFollowupPath':follow_path,'sourceFollowupBlob':follow_info['blob'],'sourceFollowupSha256':follow_info['sha256'],'sourceIdListCount':len(ids),'sourceIdListSha256':source_id_hash,'registryPath':registry_path if sid in reg_by else None,'registryBlob':registry_info['blob'] if sid in reg_by else None,'registrySha256':registry_info['sha256'] if sid in reg_by else None,'sourceFingerprint':reg_by[sid].get('sourceFingerprint') if sid in reg_by else None,'callerRefs':callers_by_id[sid],'callerContextSha256':sha(jbytes(callers_by_id[sid]))}
  source_rows.append(srow)
  for loc in LOCALES:
    current=catalogs[loc][sid]; current_hash=sha(current.encode()); current_ph=placeholders(current); current_markup=markup(current)
    proposed=PROPOSALS.get(ordinal,{}).get(loc)
    if proposed is not None:
      disposition='propose-refinement' if (ordinal,loc) in REFINEMENTS else 'propose-correction'
      confidence='moderate'
      rationale=f"This target is revised for natural {loc} phrasing and exact source meaning in the pinned caller context. The wording preserves the source placeholders and protected technical literals."
    else:
      disposition='accept-current'; proposed=None; confidence='moderate'
      rationale=f"The current {loc} target preserves the source meaning in the pinned caller context and has no material semantic or terminology issue."
    proposed_hash=sha(proposed.encode()) if proposed else None
    checks=[]
    for literal in protected:
      checks.append({'literal':literal,'matchMode':'exact','presentInSource':literal in src,'presentInCurrentTarget':literal in current,'presentInRecommendedTarget':(literal in proposed) if proposed is not None else None})
    current_missing=[x['literal'] for x in checks if not x['presentInCurrentTarget']]
    proposed_missing=[x['literal'] for x in checks if proposed is not None and not x['presentInRecommendedTarget']]
    if proposed is not None and placeholders(proposed)!=source_ph:
      raise SystemExit(f'placeholder mismatch in proposed {ordinal}|{loc}: source={source_ph}, proposed={placeholders(proposed)}')
    if proposed is not None and markup(proposed)!=source_markup:
      raise SystemExit(f'markup mismatch in proposed {ordinal}|{loc}')
    if proposed_missing: raise SystemExit(f'protected literal missing from proposal {ordinal}|{loc}: {proposed_missing}')
    input_rows.append({'exactHead':head,'exactTree':tree,'sourceOrdinal':ordinal,'sourceId':sid,'locale':loc,'source':src,'sourceTextSha256':sha(src.encode()),'sourcePlaceholders':source_ph,'sourceMarkup':source_markup,'currentTarget':current,'currentTargetSha256':current_hash,'currentTargetPlaceholders':current_ph,'currentTargetMarkup':current_markup,'targetFile':cat_paths[loc],'targetFileBlob':catalog_info[loc]['blob'],'targetFileSha256':catalog_info[loc]['sha256'],'protectedLiterals':protected,'callerContextSha256':srow['callerContextSha256']})
    review={'repository':REPO,'pullRequest':PR,'exactHead':head,'exactTree':tree,'sourceOrdinal':ordinal,'sourceId':sid,'locale':loc,'source':src,'sourceKeySha256':sha(sid.encode()),'sourceTextSha256':sha(src.encode()),'sourceFile':source_path,'sourceFileBlob':source_info['blob'],'sourceFileSha256':source_info['sha256'],'targetFile':cat_paths[loc],'targetFileBlob':catalog_info[loc]['blob'],'targetFileSha256':catalog_info[loc]['sha256'],'currentTarget':current,'currentTargetSha256':current_hash,'disposition':disposition,'recommendedTarget':proposed,'recommendedTargetSha256':proposed_hash,'confidence':confidence,'rationale':rationale,'callerRefs':callers_by_id[sid],'callerContextSha256':srow['callerContextSha256'],'sourcePlaceholders':source_ph,'currentTargetPlaceholders':current_ph,'recommendedPlaceholders':placeholders(proposed) if proposed is not None else None,'placeholderParity':source_ph==current_ph and (proposed is None or source_ph==placeholders(proposed)),'sourceMarkup':source_markup,'currentTargetMarkup':current_markup,'recommendedTargetMarkup':markup(proposed) if proposed is not None else None,'markupParity':source_markup==current_markup and (proposed is None or source_markup==markup(proposed)),'protectedLiterals':protected,'protectedLiteralChecks':checks,'protectedLiteralsPreserved':not current_missing and not proposed_missing,'protectedLiteralMismatches':{'current':current_missing,'recommended':proposed_missing},'nativeSpeakerApproval':False,'priorDisposition':'no prior source ID window disposition; non-overlap scan is recorded in prior-disposition-boundary.json'}
    review_rows.append(review)
    literal_rows.append({'exactHead':head,'exactTree':tree,'sourceOrdinal':ordinal,'sourceId':sid,'locale':loc,'sourceText':src,'currentTarget':current,'currentTargetSha256':current_hash,'finalTarget':proposed or current,'finalTargetSha256':proposed_hash or current_hash,'checks':checks,'currentMismatches':current_missing,'recommendedMismatches':proposed_missing,'placeholderParity':review['placeholderParity'],'markupParity':review['markupParity']})
if len(review_rows)!=600: raise SystemExit('expected exactly 600 review cells')

# Adjacent W549 is context only. Re-attest its previous primary ledger and current target/caller hashes.
prior_packet=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0500-0549-primary-20261102')
prior_sid=ids[549]; prior_by_locale={}
for fp,n,line in find_needle('Qualities can only be used once','src/Chaptarr.Api.V1/Profiles/Quality/QualityItemsValidator.cs'):
  raw[prior_sid].append((fp,n,line,'adjacent-source-text-exact'))
for line in (prior_packet/'review-cells.jsonl').read_text().splitlines():
  x=json.loads(line)
  if x.get('sourceOrdinal')==549 and x.get('sourceId')==prior_sid: prior_by_locale[x['locale']]=x
if set(prior_by_locale)!=set(LOCALES): raise SystemExit('W549 prior primary boundary coverage incomplete')
prior_refs=[]
for fp,n,line,mode in sorted(raw.get(prior_sid,[]),key=lambda x:(x[0],x[1],x[3])):
  content=read_git(fp); lines=content.decode('utf-8').splitlines()
  if lines[n-1]!=line: raise SystemExit(f'W549 caller drift at {fp}:{n}')
  prior_refs.append({'file':fp,'kind':mode,'currentLine':n,'lineMatchMethod':mode,'matchedSourceId':prior_sid if mode=='exact-source-id' else None,'currentLineText':line,'currentLineSha256':sha(line.encode()),'contextBefore':lines[max(0,n-3):n-1],'contextAfter':lines[n:min(len(lines),n+2)],'currentFileBlob':git('rev-parse',f'HEAD:{fp}').strip(),'currentFileSha256':sha(content)})
prior_refs_hash=sha(jbytes(prior_refs)); prior_records=[]
for loc,x in sorted(prior_by_locale.items()):
  live_source=source_catalog[prior_sid]; live_target=catalogs[loc][prior_sid]
  prior_refs_saved=x.get('callerRefs',[])
  saved_ref_keys={(r.get('file'),r.get('currentLine'),r.get('currentLineText')) for r in prior_refs_saved}
  live_ref_keys={(r.get('file'),r.get('currentLine'),r.get('currentLineText')) for r in prior_refs}
  prior_records.append({'contextSourceOrdinal':549,'sourceId':prior_sid,'source':live_source,'sourceTextSha256':sha(live_source.encode()),'locale':loc,'priorPrimaryPacketHead':x.get('exactHead'),'priorPrimaryPacketTree':x.get('exactTree'),'priorDisposition':x.get('disposition'),'priorRecommendedTarget':x.get('recommendedTarget'),'priorRecommendedTargetSha256':x.get('recommendedTargetSha256'),'priorCurrentTarget':x.get('currentTarget'),'priorCurrentTargetSha256':x.get('currentTargetSha256'),'liveCurrentTarget':live_target,'liveCurrentTargetSha256':sha(live_target.encode()),'priorTargetMatchesLive':x.get('currentTarget')==live_target,'priorRecommendationMatchesLive':x.get('recommendedTarget')==live_target if x.get('recommendedTarget') else None,'sourceMatchesLive':x.get('source')==live_source,'priorCallerRefs':prior_refs_saved,'liveCallerRefs':prior_refs,'callerContextSha256':prior_refs_hash,'callerRefsMatchPrior':saved_ref_keys==live_ref_keys,'contextOnly':True})

# Scan earlier review ledgers for source-ID overlap; current W550–599 remains disjoint.
prior_ledgers=[]; overlap_rows=[]; prior_ids=set(); prior_disposition_rows=0
for packet in sorted(O.parent.glob('chaptarrng-pr190-*')):
  if packet.resolve()==O.resolve(): continue
  for fp in sorted(packet.rglob('*.jsonl')):
    try: lines=fp.read_text().splitlines()
    except Exception: continue
    parsed=[]
    for line in lines:
      try: x=json.loads(line)
      except Exception: continue
      sid=x.get('sourceId',x.get('id',x.get('catalogKey')))
      ordinal=x.get('sourceOrdinal',x.get('sourcePosition',x.get('windowOrdinal')))
      disposition=next((x.get(k) for k in ('disposition','primaryDisposition','primaryVerdict','crossDisposition','crossReviewDisposition','reviewDisposition','independentVerdict','finalDisposition') if x.get(k) is not None),None)
      if isinstance(ordinal,int) and ordinal<550 and sid and disposition is not None:
        parsed.append(x); prior_ids.add(sid); prior_disposition_rows+=1
        if sid in source_ids: overlap_rows.append({'ledger':str(fp),'sourceOrdinal':ordinal,'sourceId':sid,'locale':x.get('locale'),'disposition':disposition})
    if parsed: prior_ledgers.append({'path':str(fp),'sha256':sha(fp.read_bytes()),'dispositionRowsBefore550':len(parsed),'sourceIds':sorted({x.get('sourceId') for x in parsed if x.get('sourceId')})})
if overlap_rows: raise SystemExit('source ID overlap with prior window: '+json.dumps(overlap_rows,ensure_ascii=False))

save_jsonl('source-slice.jsonl',source_rows)
save_jsonl('caller-context.jsonl',caller_rows)
save_jsonl('input-cells.jsonl',input_rows)
save_jsonl('review-cells.jsonl',review_rows)
save_jsonl('protected-literal-integrity.jsonl',literal_rows)
save_jsonl('correction-candidates.jsonl',[x for x in review_rows if x['disposition']!='accept-current'])
save_jsonl('prior-context-dispositions.jsonl',prior_records)
save_json('prior-disposition-boundary.json',{'scopePositions':[550,599],'searchedPriorPositions':[0,549],'scannedPriorLedgerFiles':len(prior_ledgers),'priorSourceIdCount':len(prior_ids),'priorDispositionRows':prior_disposition_rows,'matchingPriorRows':overlap_rows,'matchingPriorRowCount':len(overlap_rows),'disjointCurrentSourceIds':not overlap_rows,'ledgerFiles':prior_ledgers,'contextOnlyPreviousSourceId':prior_sid,'contextOnlyPreviousRows':len(prior_records),'adjacentW549CallerRefs':len(prior_refs),'adjacentW549CallerContextSha256':prior_refs_hash,'adjacentW549TargetsMatchingOlderPrimary':sum(x['priorTargetMatchesLive'] for x in prior_records),'adjacentW549PrimaryRecommendationsMatchingLive':sum(bool(x['priorRecommendationMatchesLive']) for x in prior_records),'adjacentW549SourceHashesMatchLive':sum(x['sourceMatchesLive'] for x in prior_records)})

# Persist the decision summary used to construct exact-hash review rows.
findings={}
source_rationales={}
for ordinal in range(550,600):
  sid=source_ids[ordinal-550]; source_rationales[str(ordinal)]='The pinned production caller establishes the API, validation, status-toast, or media-operation context for this message; proposals preserve that meaning and its technical identifiers.'
  for loc,target in PROPOSALS.get(ordinal,{}).items():
    disposition='propose-refinement' if (ordinal,loc) in REFINEMENTS else 'propose-correction'
    findings[f'{ordinal}|{loc}']=[disposition,target,f"Revises the current {loc} wording for grammar, terminology, or source-specific meaning while preserving placeholders and protected literals.",'moderate']
save_json('review-decisions.json',{'schemaVersion':1,'reviewer':'primary semantic reviewer','scope':[550,599],'findings':findings,'sourceRationales':source_rationales,'acceptedCellRationale':'Current target preserves source meaning in the exact pinned production caller context; no material issue found.','nativeSpeakerApproval':False})
save_json('reviewer-provenance.json',{'reviewerRole':'primary semantic reviewer','reviewType':'independent caller-context-aware language and terminology review of all frozen current cells','exactHead':head,'exactTree':tree,'scope':{'positions':[550,599],'cells':600,'locales':list(LOCALES)},'evidenceSources':['English source catalog','12 locale catalogs','exact source-ID production C# references','exact English-source or validator-template production caller pins','W549 adjacent primary packet and current target reattestation'],'protectedLiteralPolicy':'Preserve exact source placeholders, product names, API field names, protocol URLs, enum tokens, version and range values, and machine-readable identifiers; localize ordinary user-facing language.','nativeSpeakerApproval':False,'browserReview':False,'repositoryOrPrEdits':False,'testsBuildsScansCiRun':False,'workflowsTouched':False})

counts=collections.Counter(x['disposition'] for x in review_rows)
for key in ('accept-current','propose-refinement','propose-correction','hold'): counts.setdefault(key,0)
per_locale={}
for loc in LOCALES:
  c=collections.Counter(x['disposition'] for x in review_rows if x['locale']==loc)
  per_locale[loc]={key:c.get(key,0) for key in ('accept-current','propose-refinement','propose-correction','hold')}
summary={'schemaVersion':1,'repository':REPO,'pullRequest':PR,'exactHead':head,'exactTree':tree,'livePullRequest':pr,'scope':{'positions':[550,599],'sourceIds':50,'locales':list(LOCALES),'cells':600},'sourceIdListSha256':source_id_hash,'sourceSliceIdsSha256':sha(jbytes(source_ids)),'counts':dict(counts),'proposalCount':sum(counts[k] for k in ('propose-refinement','propose-correction')),'perLocale':per_locale,'callerEvidence':{'sourceIdsWithCallerPins':sum(bool(v) for v in callers_by_id.values()),'callerRefs':total_refs,'uniqueCallerFiles':len(unique_files),'mismatches':len(caller_mismatches),'gaps':caller_gaps,'allCallersAttestedAtExactHead':not caller_gaps and not caller_mismatches},'placeholders':{'sourcesWithPlaceholders':sum(bool(placeholders(source_catalog[sid])) for sid in source_ids),'mismatches':sum(not x['placeholderParity'] for x in review_rows)},'markup':{'sourcesWithMarkup':sum(bool(markup(source_catalog[sid])) for sid in source_ids),'mismatches':sum(not x['markupParity'] for x in review_rows)},'protectedLiterals':{'checkedCells':len(literal_rows),'currentMismatches':sum(bool(x['currentMismatches']) for x in literal_rows),'currentMismatchCells':[{'sourceOrdinal':x['sourceOrdinal'],'sourceId':x['sourceId'],'locale':x['locale'],'missing':x['currentMismatches']} for x in literal_rows if x['currentMismatches']],'recommendedMismatches':sum(bool(x['recommendedMismatches']) for x in literal_rows),'recommendedMismatchCells':[{'sourceOrdinal':x['sourceOrdinal'],'sourceId':x['sourceId'],'locale':x['locale'],'missing':x['recommendedMismatches']} for x in literal_rows if x['recommendedMismatches']]},'priorDispositionBoundary':{'priorSourceIdOverlap':len(overlap_rows),'scannedPriorLedgerFiles':len(prior_ledgers),'priorSourceIdCount':len(prior_ids),'contextOnlyW549Rows':len(prior_records),'w549SourceRowsMatchingLive':sum(x['sourceMatchesLive'] for x in prior_records),'w549TargetsMatchingOlderPrimary':sum(x['priorTargetMatchesLive'] for x in prior_records),'w549AppliedRecommendationsMatchingLive':sum(bool(x['priorRecommendationMatchesLive']) for x in prior_records),'w549CallerRefsReattested':len(prior_refs)},'nativeSpeakerApproval':False,'browserReview':False,'repositoryModified':False,'testsBuildsScansCiRun':False,'workflowFilesTouched':False}
save_json('summary.json',summary)

final_pr,final_tree=live_pr()
final_head=git('rev-parse','HEAD').strip(); final_worktree_tree=git('rev-parse','HEAD^{tree}').strip()
if final_head!=head or final_worktree_tree!=tree or final_pr['headRefOid']!=head or final_tree!=tree or final_pr['state']!='OPEN' or not final_pr['isDraft']:
  save_json('final-reattestation.json',{'passed':False,'expectedHead':head,'expectedTree':tree,'finalHead':final_head,'finalWorktreeTree':final_worktree_tree,'finalPullRequest':final_pr,'finalLiveTree':final_tree})
  raise SystemExit('live PR moved during packet construction; preserve packet and report drift')
save_json('final-reattestation.json',{'passed':True,'exactHead':head,'exactTree':tree,'pullRequestState':final_pr['state'],'isDraft':final_pr['isDraft'],'headRefName':final_pr['headRefName'],'sourceIds':50,'localeCells':len(input_rows),'sourceTextHashes':len(source_rows),'callerRefs':total_refs,'callerContextHashes':len(caller_rows),'w549ContextRows':len(prior_records),'w549SourceRowsMatchingLive':sum(x['sourceMatchesLive'] for x in prior_records),'w549LiveTargetHashesRecorded':len(prior_records),'repositoryClean':not git('status','--porcelain').strip(),'repositoryModified':False})

# Build input checksums from blobs at the frozen exact head, not working-tree paths.
input_files=[source_info,follow_info,registry_info,*catalog_info.values()]
(O/'INPUT-SHA256SUMS').write_text(''.join(f"{x['sha256']}  {x['path']}\n" for x in input_files))
(O/'README.md').write_text(f'''# ChaptarrNG PR #190 W550–599 primary semantic review\n\n- Exact PR state: OPEN/DRAFT at `{head}` / tree `{tree}`.\n- Scope: source-list positions 550–599 across 12 locales = 50 source IDs / 600 current locale cells.\n- Exact source inventory: `source-slice.jsonl`; source-list SHA-256 `{source_id_hash}`.\n- Production caller pins: {len(caller_rows)} of 50 source IDs, {total_refs} exact C# references across {len(unique_files)} files; gaps and mismatches: 0.\n- Dispositions: {dict(counts)}. Every cell has exact source/current-target hashes and caller context in `review-cells.jsonl`; recommendations are in `correction-candidates.jsonl`.\n- Placeholder mismatches: {summary['placeholders']['mismatches']}; markup mismatches: {summary['markup']['mismatches']}; current protected-literal mismatch cells: {summary['protectedLiterals']['currentMismatches']}; proposed protected-literal mismatches: {summary['protectedLiterals']['recommendedMismatches']}.\n- W549 adjacent context: source hash was reattested; {summary['priorDispositionBoundary']['w549TargetsMatchingOlderPrimary']} of 12 previous current targets still match, while {summary['priorDispositionBoundary']['w549AppliedRecommendationsMatchingLive']} prior recommendations match the live targets after the apply commit. All 12 live target hashes and caller refs are recorded.\n- Earlier ledger overlap: {len(overlap_rows)} source IDs.\n- Primary model review only; native-speaker approval is not claimed. No repository/catalog/PR edits, tests, builds, scans, CI, browser actions, or workflow edits were performed.\n\nSee `summary.json`, `manifest.json`, and `SHA256SUMS` for packet inventory and integrity.\n''')

# Record exact input manifest and every packet-file digest before the checksum manifest itself.
manifest={'schemaVersion':1,'repository':REPO,'pullRequest':PR,'head':head,'tree':tree,'livePullRequest':final_pr,'positions':[550,599],'sourceIdCount':50,'locales':list(LOCALES),'cellCount':600,'sourceFollowup':follow_info,'sourceFile':source_info,'registry':registry_info,'catalogs':catalog_info,'sourceListSha256':source_id_hash,'files':[]}
for fp in sorted(O.iterdir()):
  if fp.is_file() and fp.name not in ('manifest.json','SHA256SUMS'):
    manifest['files'].append({'path':fp.name,'bytes':fp.stat().st_size,'sha256':sha(fp.read_bytes())})
save_json('manifest.json',manifest)
all_files=sorted(fp for fp in O.iterdir() if fp.is_file() and fp.name!='SHA256SUMS')
(O/'SHA256SUMS').write_text(''.join(f'{sha(fp.read_bytes())}  {fp.name}\n' for fp in all_files))
# Re-query exact PR state after all evidence writes and verify the checksummed packet.
post_pr,post_tree=live_pr(); post_head=git('rev-parse','HEAD').strip(); post_worktree_tree=git('rev-parse','HEAD^{tree}').strip()
if (post_head,post_worktree_tree,post_pr['headRefOid'],post_tree,post_pr['state'],post_pr['isDraft'])!=(head,tree,head,tree,'OPEN',True):
  raise SystemExit('post-write live PR exact-head verification failed')
for line in (O/'SHA256SUMS').read_text().splitlines():
  digest,name=line.split('  ',1)
  if sha((O/name).read_bytes())!=digest: raise SystemExit(f'packet checksum failure: {name}')
print(json.dumps({'packet':str(O),'head':head,'tree':tree,'cells':len(review_rows),'counts':dict(counts),'callerRefs':total_refs,'callerFiles':len(unique_files),'placeholdersMismatch':summary['placeholders']['mismatches'],'markupMismatch':summary['markup']['mismatches'],'currentProtectedMismatchCells':summary['protectedLiterals']['currentMismatches'],'proposalProtectedMismatchCells':summary['protectedLiterals']['recommendedMismatches'],'w549TargetsMatchingOlderPrimary':summary['priorDispositionBoundary']['w549TargetsMatchingOlderPrimary'],'w549AppliedRecommendationsMatchingLive':summary['priorDispositionBoundary']['w549AppliedRecommendationsMatchingLive'],'priorOverlap':len(overlap_rows),'postHead':post_head,'packetFiles':len(all_files)+1,'packetBytes':sum(fp.stat().st_size for fp in O.iterdir() if fp.is_file())},ensure_ascii=False,indent=2))
