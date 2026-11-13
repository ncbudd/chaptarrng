import collections,hashlib,json,re
from pathlib import Path
OUT=Path('.')
HEAD='6e7a5341b7ccac31d950c73db68277f9a1f18f8e'; TREE='d073e1373021bf715db37461a12654f7e993cdbf'
LOCALES={'ar','de','es','fr','hi','id'}
sha=lambda s:hashlib.sha256(s.encode('utf8')).hexdigest()
inputs=[json.loads(x) for x in open(OUT/'inputs/source-cells.jsonl',encoding='utf8')]
source_rows={json.loads(x)['sourceOrdinal']:json.loads(x) for x in open(OUT/'inputs/source-rows.jsonl',encoding='utf8')}
# (ordinal, locale): disposition, target, rationale, confidence
C={}
def c(n,l,d,t,r,conf='moderate'):
 assert l in LOCALES and d in {'correction','refinement','hold'}
 if d=='hold': assert t is None
 C[(n,l)]=(d,t,r,conf)
HOLD={1187}
# Cross-review decisions are based on the pinned source, current target, caller, and locale usage.
c(1153,'ar','refinement','جارٍ استعادة تحويل M4B المتقطع.','The source is a live recovery status; the current Arabic reads like a noun label rather than an ongoing action.')
c(1153,'es','refinement','Recuperando la conversión M4B interrumpida.','Make the interrupted conversion the object of the ongoing recovery status.')
c(1153,'fr','correction','Récupération de la conversion M4B interrompue.','The current adjective placement makes M4B appear to modify “interrupted”; move M4B beside conversion.')
c(1153,'id','correction','Memulihkan konversi M4B yang terhenti.','The current verb can mean “returning”; use the recovery verb and a natural relative clause.')
c(1156,'ar','correction','FFmpeg غير متوفر (مطلوب لـ m4b-tool).','The current parenthetical calls it a requirement from the tool; this states that m4b-tool requires FFmpeg.')
c(1156,'es','correction','FFmpeg no está disponible (necesario para m4b-tool).','Use para to express that m4b-tool requires the unavailable FFmpeg dependency.')
c(1156,'hi','refinement','FFmpeg उपलब्ध नहीं है (m4b-tool के लिए आवश्यक है)।','Make the dependency relation explicit while retaining both protected tool names.')
c(1165,'ar','correction','فشل تحويل M4B.','The current Arabic word order is malformed for a failed conversion status.','high')
c(1165,'de','correction','Die M4B-Konvertierung ist fehlgeschlagen.','Use a grammatical German result clause; the current noun stack with versagt is not idiomatic.','high')
c(1165,'es','correction','La conversión a M4B falló.','The current noun/participle sequence is ungrammatical; report the failed conversion directly.','high')
c(1165,'fr','correction','Échec de la conversion en M4B.','The current noun plus past participle is ungrammatical; use the standard failure status.','high')
c(1165,'hi','correction','M4B रूपांतरण विफल रहा।','Use a complete Hindi failure clause and the standard रूपांतरण term.')
c(1165,'id','correction','Konversi M4B gagal.','The current word order places M4B before the noun unnaturally.','high')
c(1166,'ar','refinement','جارٍ التحويل إلى M4B - {value0}%','Add the progressive aspect for the ongoing percentage status.')
c(1166,'fr','correction','Conversion en M4B - {value0}%','Use en for conversion into a file format; à is not the natural preposition here.')
c(1166,'hi','refinement','M4B में रूपांतरण जारी है - {value0}%','The current past-participle wording can read as completed; make the progress state explicit.')
c(1167,'ar','correction','ملف M4B المحوّل جاهز للاستيراد.','The source says the converted file is ready; current wording makes the conversion itself ready.')
c(1167,'de','correction','Die konvertierte M4B-Datei ist bereit für den Import.','Add the missing finite predicate and identify the file as the item ready for import.')
c(1167,'es','correction','El archivo M4B convertido está listo para importarse.','Correct the adjective order and specify that the converted file is ready.')
c(1167,'fr','correction','Le fichier M4B converti est prêt à être importé.','Correct the adjective order and specify that the converted file is ready.')
c(1167,'hi','correction','रूपांतरित M4B फ़ाइल आयात के लिए तैयार है।','Make the file the subject and complete the Hindi status sentence.')
c(1167,'id','correction','File M4B hasil konversi siap diimpor.','The current subject is the conversion process, not the converted M4B file.')
c(1169,'de','refinement','Der interne Direct-Downloadclient ist nicht verfügbar.','Translate the generic download-client category and internal modifier while preserving protected Direct.')
c(1169,'id','refinement','Klien unduhan internal Direct tidak tersedia.','Translate the generic download-client category and internal modifier while preserving protected Direct.')
c(1172,'ar','correction','ملف M4B المحوّل صغير جدًا ليكون كتابًا صوتيًا صالحًا.','The source’s subject is the converted file, not the conversion process.')
c(1172,'es','refinement','El archivo M4B convertido es demasiado pequeño para ser un audiolibro válido.','Use the standard Spanish term audiolibro for the audiobook.')
c(1172,'hi','correction','रूपांतरित M4B फ़ाइल वैध ऑडियोबुक बनने के लिए बहुत छोटी है।','Correct feminine agreement with फ़ाइल and retain the “too small to be valid” meaning.')
c(1172,'id','correction','File M4B hasil konversi terlalu kecil untuk menjadi buku audio yang valid.','Make the converted file, rather than the conversion, the subject.')
c(1173,'ar','correction','فشل تحويل M4B: {value0}','Repair the word order while preserving the dynamic failure detail.','high')
c(1173,'de','correction','Die M4B-Konvertierung ist fehlgeschlagen: {value0}','Use a grammatical completed-failure clause before the dynamic detail.')
c(1173,'es','correction','La conversión a M4B falló: {value0}','The current noun sequence and falleció (died) do not express a conversion failure.')
c(1173,'fr','correction','Échec de la conversion en M4B : {value0}','Repair the ungrammatical noun/participle order.')
c(1173,'id','correction','Konversi M4B gagal: {value0}','Repair the noun order while preserving the dynamic error detail.')
c(1174,'de','correction','m4b-tool ist mit Exitcode {value0} fehlgeschlagen.','fehlte means “was missing”; the source says the tool failed with the exit code.','high')
c(1174,'es','correction','m4b-tool falló con el código de salida {value0}.','falleció means “died”; use the failure verb.')
c(1174,'fr','correction','m4b-tool a échoué avec le code de sortie {value0}.','Use a past tense for the completed tool failure rather than present échoue.')
c(1174,'hi','refinement','m4b-tool निकास कोड {value0} के साथ विफल रहा।','Move the exit-code phrase into the natural Hindi construction.')
c(1177,'es','correction','m4b-tool falló al escribir los capítulos o las etiquetas. El audio convertido no se importará automáticamente.','The current tense pairing mixes past and present; align the writing failure and resulting import behavior.')
c(1177,'fr','correction','m4b-tool a échoué lors de l’écriture des chapitres ou des tags. L’audio converti n’est pas automatiquement importé.','Capitalize the second sentence; the rest reports the caller’s failure and import behavior accurately.')
c(1177,'hi','refinement','m4b-tool अध्यायों या टैग लिखते समय विफल रहा। रूपांतरित ऑडियो स्वचालित रूप से आयात नहीं किया जा रहा है।','Use standard Hindi sentence punctuation and a natural passive for the current import state.')
c(1177,'id','correction','m4b-tool gagal saat menulis bab atau tag. Audio hasil konversi tidak akan diimpor secara otomatis.','Capitalize the second sentence and use the standard diimpor spelling for importing the converted audio.')
c(1179,'de','correction','m4b-tool wurde beendet, hat jedoch die konvertierte M4B-Datei nicht erstellt.','The current target lacks a grammatical German clause for the missing output.')
c(1179,'es','correction','m4b-tool terminó, pero no creó el archivo M4B convertido.','The current fragment omits the finite verb that connects tool completion to output absence.')
c(1179,'hi','correction','m4b-tool समाप्त हो गया, लेकिन रूपांतरित M4B फ़ाइल नहीं बनाई गई।','Correct feminine agreement with फ़ाइल and state that the file was not created.')
c(1179,'id','correction','m4b-tool selesai, tetapi tidak membuat file M4B hasil konversi.','Clarify that the completed tool run did not create the converted file.')
c(1181,'ar','correction','فشلت مهمة تحويل M4B: {value0}','The source subject is the conversion job; repair the Arabic word order and preserve the error detail.')
c(1181,'de','correction','Der M4B-Konvertierungsauftrag ist fehlgeschlagen: {value0}','Use grammatical word order for the failed job and retain the dynamic detail.')
c(1181,'es','correction','Falló la tarea de conversión a M4B: {value0}','Use natural Spanish word order and keep the dynamic error detail.')
c(1181,'fr','correction','La tâche de conversion en M4B a échoué : {value0}','Use grammatical French word order for the failed conversion job.')
c(1181,'hi','correction','M4B रूपांतरण कार्य विफल हुआ: {value0}','Replace the literal/unidiomatic “job” translation with the natural Hindi term कार्य.')
c(1181,'id','correction','Tugas konversi M4B gagal: {value0}','Use natural Indonesian word order for the failed conversion task.')
c(1184,'ar','refinement','تعذّر العثور على الكتاب المطلوب.','Convert the current nominal fragment into a natural user-facing not-found result.')
c(1184,'hi','refinement','अनुरोधित किताब नहीं मिली।','Use a concise, natural not-found message rather than the current literal ability phrasing.')
c(1185,'de','refinement','Die Konvertierung wurde abgebrochen.','abgesagt is usually used for appointments or events; abgebrochen is more natural for a process.')
c(1187,'ar','hold',None,'Hold: both exact callers interpolate TargetQualityName ?? "M4B" as {value0}; the configured quality name can differ from M4B. The registry also requires literal M4B. Inserting or omitting a fixed M4B label cannot be judged safely from the source/caller evidence alone.','low')
c(1187,'de','hold',None,'Hold: both exact callers interpolate TargetQualityName ?? "M4B" as {value0}; the configured quality name can differ from M4B. The current fixed M4B phrase can contradict the dynamic value, and the registry requires literal M4B. Do not infer the runtime quality.','low')
c(1187,'es','hold',None,'Hold: both exact callers interpolate TargetQualityName ?? "M4B" as {value0}; the configured quality name can differ from M4B. The registry requires literal M4B, so no fixed phrase is safe to infer from these pins.','low')
c(1187,'fr','hold',None,'Hold: both exact callers interpolate TargetQualityName ?? "M4B" as {value0}; the configured quality name can differ from M4B. The registry requires literal M4B, so no fixed phrase is safe to infer from these pins.','low')
c(1187,'hi','hold',None,'Hold: both exact callers interpolate TargetQualityName ?? "M4B" as {value0}; the configured quality name can differ from M4B. The registry requires literal M4B, so no fixed phrase is safe to infer from these pins.','low')
c(1187,'id','hold',None,'Hold: both exact callers interpolate TargetQualityName ?? "M4B" as {value0}; the configured quality name can differ from M4B. The registry requires literal M4B, so no fixed phrase is safe to infer from these pins.','low')
c(1188,'ar','correction','m4b-tool لم يُعِد نتيجة العملية.','Correct the verb form after لم to say the tool did not return a process result.')
c(1188,'fr','correction','m4b-tool n’a pas renvoyé de résultat de processus.','Use a natural result-return construction for the process status.')
c(1188,'hi','correction','m4b-tool ने कोई प्रक्रिया परिणाम नहीं लौटाया।','Repair Hindi word order and the missing subject marker.')
c(1189,'ar','correction','جارٍ إنهاء M4B','Correct the spelling and express the ongoing finalization status.')
c(1189,'de','correction','M4B wird fertiggestellt.','The current noun fragment is awkward; use an ongoing process status.')
c(1189,'fr','refinement','Finalisation du M4B','Use a natural French status noun rather than the current command-like infinitive.')
c(1189,'hi','correction','M4B को अंतिम रूप दिया जा रहा है।','The current target says “in order to finish M4B”; express the ongoing finalization status.')
c(1189,'id','correction','Sedang menyelesaikan M4B.','The current verb means “ending M4B”; state that final processing is underway.')
c(1190,'de','refinement','Für {value0} ist kein Download-Client verfügbar.','Use a concise unambiguous statement that no client for the protocol is available.')
c(1190,'es','refinement','Ningún cliente de descarga para {value0} está disponible.','Avoid possible negation-scope ambiguity in “Todos ... no están disponibles.”')
c(1190,'fr','correction','Aucun client de téléchargement pour {value0} n’est disponible.','The current “Tous ... ne sont pas” can mean “not all”; state that none is available.')
c(1190,'hi','refinement','{value0} के लिए कोई भी डाउनलोड क्लाइंट उपलब्ध नहीं है।','Make the scope explicit that no client for this protocol is available.')
c(1191,'de','refinement','Die wiederhergestellte M4B-Datei wartet auf den Import.','Add a grammatical subject; the current fragment says “restored; waits” without naming the file that is pending import.')
c(1195,'ar','correction','ملف M4B المحوّل لا يحتوي على تدفق صوتي قابل للقراءة.','Make the converted M4B file, rather than the conversion, the subject.')
c(1195,'de','correction','Die konvertierte M4B-Datei enthält keinen lesbaren Audiostream.','The current target is partly English and grammatically malformed; use the file as subject.')
c(1195,'es','correction','El M4B convertido no contiene un flujo de audio legible.','The current adjective order is ungrammatical; make the converted M4B the subject.')
c(1195,'fr','correction','Le M4B converti ne contient aucun flux audio lisible.','The current target leaves “Convert M4B” untranslated and omits the stream relation.')
c(1195,'hi','refinement','रूपांतरित M4B में कोई पढ़ने योग्य ऑडियो स्ट्रीम नहीं है।','Use a direct negative instead of the current generic present construction.')
c(1195,'id','correction','File M4B hasil konversi tidak berisi aliran audio yang dapat dibaca.','The current target makes the conversion process the subject and uses an unnatural stream term.')
c(1197,'de','refinement','Es konnten weder ein passender Autor noch die zugehörigen Bücher gefunden werden.','Avoid implying a gendered possessive in the reference to the author and associated books.')
c(1198,'es','refinement','Convirtiendo a M4B - {value0} de {value1}','Use an ongoing progress form rather than the imperative Convertir.')
c(1198,'fr','refinement','Conversion en M4B - {value0} sur {value1}','Use en for the output format and sur for current step over total.')

ph=lambda s:collections.Counter(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s))
markup=lambda s: [] if re.fullmatch(r'<[^<>/]+>',s) else re.findall(r'</?[A-Za-z][^>]*>',s)
icu=lambda s: sorted(set((a.strip(),b.lower()) for a,b in re.findall(r'\{\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*,\s*(plural|selectordinal|select)\b',s,re.I)))
rows=[]
for cell in inputs:
 n=cell['sourceOrdinal']; loc=cell['locale']
 if loc not in LOCALES:continue
 assert cell['exactHead']==HEAD and cell['exactTree']==TREE
 key=(n,loc)
 if key in C:
  disp,target,rationale,conf=C[key]
 else:
  disp='accept-current';target=None
  rationale='Independent review of the exact English source, current target, pinned production caller(s), locale grammar/register, placeholders, markup, ICU signature, and protected literals found no material defect.'
  conf='moderate'
 current=cell['currentTarget']; final=current if target is None else target
 checks={'sourcePlaceholders':dict(sorted(ph(cell['source']).items())),'currentPlaceholders':dict(sorted(ph(current).items())),'finalPlaceholders':dict(sorted(ph(final).items())),
  'placeholderParity':ph(cell['source'])==ph(current)==ph(final),'sourceMarkup':markup(cell['source']),'currentMarkup':markup(current),'finalMarkup':markup(final),
  'markupParity':markup(cell['source'])==markup(current)==markup(final),'sourceIcuSignature':icu(cell['source']),'currentIcuSignature':icu(current),'finalIcuSignature':icu(final),
  'icuParity':icu(cell['source'])==icu(current)==icu(final),
  'protectedLiteralChecks':[{'literal':lit,'inSource':lit in cell['source'],'inCurrentTarget':lit in current,'inFinalTarget':lit in final,
   'status':'hold-conflict' if disp=='hold' else ('pass' if lit in final else 'fail')} for lit in cell['protectedLiterals']],
  'currentProtectedLiteralFailures':[lit for lit in cell['protectedLiterals'] if lit not in current],
  'finalProtectedLiteralFailures':[lit for lit in cell['protectedLiterals'] if lit not in final],
  'protectedLiteralDisposition':'hold-conflict' if disp=='hold' else 'pass'}
 assert checks['placeholderParity'] and checks['markupParity'] and checks['icuParity'],(n,loc,checks)
 if disp!='hold':assert not checks['finalProtectedLiteralFailures'],(n,loc,checks)
 if disp=='hold':assert n==1187
 row={'exactHead':HEAD,'exactTree':TREE,'sourceOrdinal':n,'sourceId':cell['sourceId'],'locale':loc,'source':cell['source'],
  'sourceIdSha256':cell['sourceIdSha256'],'sourceTextSha256':cell['sourceTextSha256'],'currentTarget':current,'currentTargetSha256':cell['currentTargetSha256'],
  'targetFile':cell['targetFile'],'targetFileGitBlob':cell['targetFileGitBlob'],'targetFileSha256':cell['targetFileSha256'],
  'sourceFile':cell['sourceFile'],'sourceFileGitBlob':cell['sourceFileGitBlob'],'sourceFileSha256':cell['sourceFileSha256'],
  'callerContextSha256':cell['callerContextSha256'],'callerReferenceCount':len(cell['callerReferences']),'callerRefs':cell['callerReferences'],
  'crossReviewVerdict':disp,'independentDisposition':disp,'candidateTarget':target,'candidateTargetSha256':sha(target) if target is not None else None,
  'independentFinalTarget':final,'independentFinalTargetSha256':sha(final),'rationale':rationale,'confidence':conf,
  'sourceRegistryFingerprint':cell['sourceRegistryFingerprint'],'protectedLiterals':cell['protectedLiterals'],'sourceRegistryParameters':cell['sourceRegistryParameters'],
  'structuralChecks':checks,'nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True}
 rows.append(row)
assert len(rows)==300 and len({(r['sourceOrdinal'],r['locale']) for r in rows})==300
with open(OUT/'independent-review-ar-de-es-fr-hi-id.jsonl','w',encoding='utf8') as f:
 for r in rows:f.write(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n')
(OUT/'independent-review-ar-de-es-fr-hi-id.jsonl.sha256').write_text(sha((OUT/'independent-review-ar-de-es-fr-hi-id.jsonl').read_text(encoding='utf8'))+'  independent-review-ar-de-es-fr-hi-id.jsonl\n',encoding='utf8')
print(json.dumps({'rows':len(rows),'dispositions':dict(collections.Counter(r['independentDisposition'] for r in rows)),'confidence':dict(collections.Counter(r['confidence'] for r in rows)),
 'sha256':sha((OUT/'independent-review-ar-de-es-fr-hi-id.jsonl').read_text(encoding='utf8')),'heldOrdinals':sorted({r['sourceOrdinal'] for r in rows if r['independentDisposition']=='hold'})},ensure_ascii=False,indent=2))
