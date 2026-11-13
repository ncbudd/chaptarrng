from __future__ import annotations
import collections, hashlib, json, pathlib, re
OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0950-0999-primary-20261102')
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
CONF={x:'moderate' for x in LOCALES}
def sha(b): return hashlib.sha256(b if isinstance(b,bytes) else b.encode()).hexdigest()
def readjl(n): return [json.loads(x) for x in (OUT/n).read_text().splitlines()]
def writejl(n,rows): (OUT/n).write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in rows))
def placeholders(s): return sorted(set(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s)))
def markup(s):
 if re.fullmatch(r'<[^<>/]+>',s): return []
 return re.findall(r'</?[A-Za-z][^>]*>',s)
def icu_signature(s):
 return sorted(set((name.strip(),kind.strip().lower()) for name,kind in re.findall(r'\{\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*,\s*(plural|selectordinal|select)\b',s,re.I)))
# These are native name choices for the MyAnonaMouse LanguageFilter provider option.
# Candidate changes are tied to the exact source and caller context frozen in input-cells.jsonl.
C={}
def put(o,loc,target,kind,why,refs=()):
 C[(o,loc)]={'target':target,'kind':kind,'why':why,'externalReferenceIds':list(refs)}
put(973,'ar','الأيسلندية','correction','The current spelling omits the hamza/alif form used in the standard Arabic name for Icelandic. The caller confirms this is a language name.',('ar-icelandic',))
put(957,'de','Chinesisch','correction','German treats the standalone language name as a noun; Duden gives Chinesisch, so the current lowercase adjective form is not correct as a language label.')
put(980,'de','Koreanisch','correction','German treats the standalone language name as a noun; Duden gives Koreanisch, so the current lowercase adjective form is not correct as a language label.',('de-koreanisch',))
put(992,'de','Pandschabi','correction','The current “Die Punjabi” has the wrong article and uses an English spelling. Duden records the language as neuter “das Pandschabi”; the standalone label should omit the article.',('de-pandschabi',))
put(968,'es','Griego antiguo','correction','The comma and adjective order in “Griego, Antiguo” read like a reversed database sort label, not a natural Spanish language name.')
put(986,'es','Manés','correction','The current value uses an English label with an unnecessary article. The RAE lists manés as the name of the language of the Isle of Man.',('es-manes',))
put(992,'es','Punyabí','correction','The current value retains the English spelling with an unnecessary article. FundéuRAE recommends punyabí as the Spanish language name.',('es-punyabi',))
put(995,'es','Gaélico escocés','correction','The current adjective order is unnatural for this language name; “gaélico escocés” clearly names Scottish Gaelic.')
put(968,'fr','Grec ancien','correction','French uses “grec ancien” for the historical language; the comma-separated reversed order is not a natural French label.',('fr-grec-ancien',))
put(992,'fr','Pendjabi','correction','The current value retains the English spelling with an unnecessary article. Larousse gives pendjabi as the French name of this language.',('fr-pendjabi',))
put(984,'ko','말레이어','correction','“말레이시아어” means Malaysian language; the source is specifically Malay. “말레이어” names Malay.')
put(999,'vi','Tiếng Tây Ban Nha','correction','The current wording names Spain; adding “Tiếng” makes the language explicit and matches the neighboring Vietnamese language labels.')
assert len(C)==12
cells=readjl('input-cells.jsonl')
sources=readjl('source-slice.jsonl')
callers=readjl('caller-context.jsonl')
assert len(cells)==600 and len(sources)==50 and len(callers)==50
source_by={x['sourceId']:x for x in sources}
caller_by={x['sourceId']:x for x in callers}
assert {x['sourceOrdinal'] for x in sources}==set(range(950,1000))
assert all(x['callerReferenceCount']>0 and x['callerReferenceStatus']=='pinned' for x in callers)
# Spanish formal/informal register is not applicable because every selected source is a bare language-name label.
assert all(x['locale']!='es' or (not re.search(r'\b(tú|usted|vosotros|ustedes)\b',x['currentTarget'],re.I) and not re.search(r'\b(tú|usted|vosotros|ustedes)\b',x['source'],re.I)) for x in cells)
review=[]; audit=[]
for cell in sorted(cells,key=lambda x:(x['sourceOrdinal'],LOCALES.index(x['locale']))):
 o=cell['sourceOrdinal']; loc=cell['locale']; cur=cell['currentTarget']; item=C.get((o,loc))
 if item:
  disp=item['kind']; rec=item['target']; final=rec; rationale=item['why']
 else:
  disp='accept-current'; rec=None; final=cur
  rationale='Reviewed as a canonical language-name option for the pinned MyAnonaMouse LanguageFilter enum and provider-option display pipeline; the current wording identifies the source language without a material semantic or grammatical defect.'
 assert disp in {'accept-current','correction','refinement','hold'}
 source=cell['source']
 rec_for_checks=rec if rec is not None else cur
 ph_src=placeholders(source); ph_cur=placeholders(cur); ph_rec=placeholders(rec_for_checks); ph_final=placeholders(final)
 mk_src=markup(source); mk_cur=markup(cur); mk_rec=markup(rec_for_checks); mk_final=markup(final)
 icu_src=icu_signature(source); icu_cur=icu_signature(cur); icu_rec=icu_signature(rec_for_checks); icu_final=icu_signature(final)
 protected=cell['protectedLiterals']
 def checks(value): return [{'literal':lit,'present':lit in value} for lit in protected]
 current_checks=checks(cur); recommended_checks=checks(rec_for_checks); final_checks=checks(final)
 structural={'sourcePlaceholders':ph_src,'currentPlaceholders':ph_cur,'recommendedPlaceholders':ph_rec,'finalPlaceholders':ph_final,'sourceMarkup':mk_src,'currentMarkup':mk_cur,'recommendedMarkup':mk_rec,'finalMarkup':mk_final,'sourceIcuSignature':icu_src,'currentIcuSignature':icu_cur,'recommendedIcuSignature':icu_rec,'finalIcuSignature':icu_final,'currentIcuParity':icu_src==icu_cur,'recommendedIcuParity':icu_src==icu_rec,'finalIcuParity':icu_src==icu_final,'currentPlaceholderParity':ph_src==ph_cur,'recommendedPlaceholderParity':ph_src==ph_rec,'finalPlaceholderParity':ph_src==ph_final,'currentMarkupParity':mk_src==mk_cur,'recommendedMarkupParity':mk_src==mk_rec,'finalMarkupParity':mk_src==mk_final,'currentProtectedLiteralChecks':current_checks,'recommendedProtectedLiteralChecks':recommended_checks,'finalProtectedLiteralChecks':final_checks,'currentProtectedLiteralFailures':[x['literal'] for x in current_checks if not x['present']],'recommendedProtectedLiteralFailures':[x['literal'] for x in recommended_checks if not x['present']],'finalProtectedLiteralFailures':[x['literal'] for x in final_checks if not x['present']]}
 assert structural['currentPlaceholderParity'] and structural['recommendedPlaceholderParity'] and structural['finalPlaceholderParity']
 assert structural['currentMarkupParity'] and structural['recommendedMarkupParity'] and structural['finalMarkupParity']
 assert structural['currentIcuParity'] and structural['recommendedIcuParity'] and structural['finalIcuParity']
 assert not structural['recommendedProtectedLiteralFailures'] and not structural['finalProtectedLiteralFailures']
 ctx=caller_by[cell['sourceId']]
 srcrow=source_by[cell['sourceId']]
 row={**cell,'disposition':disp,'recommendedTarget':rec,'recommendedTargetSha256':sha(rec) if rec is not None else None,'finalTarget':final,'finalTargetSha256':sha(final),'decisionRationale':rationale,'reviewConfidence':CONF[loc],'semanticInterpretation':'Bare native-language label for a numeric language-filter enum option in the MyAnonaMouse indexer; localized by the provider schema pipeline and displayed as a select option.','spanishFormalAddressApplicability':'not-applicable: this source is a language name with no addressee, imperative, or second-person form.' if loc=='es' else None,'externalReferenceIds':item['externalReferenceIds'] if item else [],'pinnedCallerReferenceCount':ctx['callerReferenceCount'],'callerRefs':ctx['directCallerReferences'],'callerContextSha256':ctx['callerContextSha256'],'callerReferenceStatus':ctx['callerReferenceStatus'],'structuralChecks':structural,'sourceRegistryContext':{'path':srcrow['sourceRegistryPath'],'category':srcrow.get('registryCategory'),'surface':srcrow.get('registrySurface'),'parameters':srcrow.get('registryParameters',[]),'patterns':srcrow.get('registryPatterns',[]),'protectedLiterals':srcrow['effectiveProtectedLiterals']}}
 review.append(row)
 audit.append({'sourceOrdinal':o,'sourceId':cell['sourceId'],'locale':loc,'languageAuditDisposition':disp,'sourceTextSha256':cell['sourceTextSha256'],'currentTarget':cur,'currentTargetSha256':cell['currentTargetSha256'],'recommendedTarget':rec,'recommendedTargetSha256':sha(rec) if rec is not None else None,'finalTarget':final,'finalTargetSha256':sha(final),'rationale':rationale,'confidence':CONF[loc],'placeholdersPreserved':structural['finalPlaceholderParity'],'markupPreserved':structural['finalMarkupParity'],'icuPreserved':structural['finalIcuParity'],'protectedLiteralsPreserved':not structural['finalProtectedLiteralFailures'],'callerContextSha256':ctx['callerContextSha256'],'spanishFormalAddressApplicability':'not-applicable: language-name label; no second-person register' if loc=='es' else None,'externalReferenceIds':item['externalReferenceIds'] if item else []})
assert len(review)==len(audit)==600
assert len({(x['sourceOrdinal'],x['locale']) for x in review})==600
assert set(C)=={(x['sourceOrdinal'],x['locale']) for x in review if x['disposition']!='accept-current'}
counts=collections.Counter(x['disposition'] for x in review)
per_locale={loc:dict(collections.Counter(x['disposition'] for x in review if x['locale']==loc)) for loc in LOCALES}
summary={'exactHead':json.loads((OUT/'input-manifest.json').read_text())['head'],'exactTree':json.loads((OUT/'input-manifest.json').read_text())['tree'],'window':'W950-W999','sourcePositions':[950,999],'sourceCount':50,'localeCells':600,'locales':LOCALES,'sourceDescription':'All selected source values are language names from the MyAnonaMouse LanguageFilter enum, rendered as provider-option select labels.','dispositionCounts':dict(sorted(counts.items())),'perLocaleDispositionCounts':per_locale,'candidateCount':counts['correction']+counts['refinement'],'correctionCandidates':counts['correction'],'refinementCandidates':counts['refinement'],'holdCount':counts['hold'],'acceptedCurrent':counts['accept-current'],'placeholderMismatchCells':sum(not x['structuralChecks']['finalPlaceholderParity'] for x in review),'markupMismatchCells':sum(not x['structuralChecks']['finalMarkupParity'] for x in review),'icuMismatchCells':sum(not x['structuralChecks']['finalIcuParity'] for x in review),'icuCellCount':sum(bool(x['structuralChecks']['sourceIcuSignature']) for x in review),'currentProtectedLiteralFailureCells':sum(bool(x['structuralChecks']['currentProtectedLiteralFailures']) for x in review),'finalProtectedLiteralFailureCells':sum(bool(x['structuralChecks']['finalProtectedLiteralFailures']) for x in review),'sourceCallerRows':len(callers),'sourceCallerReferences':sum(x['callerReferenceCount'] for x in callers),'sourceCallerGaps':sum(x['callerReferenceStatus']!='pinned' for x in callers),'staleCallerPins':len(json.loads((OUT/'caller-context-summary.json').read_text())['staleRegistryPins']),'serverMessagePipelineReferences':len(readjl('server-message-pipeline-context.jsonl')),'providerOptionPipelineReferences':len(readjl('provider-option-pipeline-context.jsonl')),'spanishFormalAddressCells':sum(x['locale']=='es' for x in review),'spanishFormalAddressApplicability':'not applicable for all 50 source labels: no direct address, instructions, or second-person grammar','nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True,'machineAssistedConfidence':'moderate','scopeLimitation':'Static primary semantic pass. No native-speaker or browser/runtime approval claimed.'}
assert counts['hold']==0
assert summary['sourceCallerGaps']==0 and summary['staleCallerPins']==0
assert summary['placeholderMismatchCells']==summary['markupMismatchCells']==summary['icuMismatchCells']==summary['finalProtectedLiteralFailureCells']==0
writejl('review-cells.jsonl',review); writejl('language-audit.jsonl',audit)
writejl('correction-candidates.jsonl',[x for x in review if x['disposition']=='correction'])
writejl('refinement-candidates.jsonl',[x for x in review if x['disposition']=='refinement'])
writejl('protected-literal-integrity.jsonl',[{'sourceOrdinal':x['sourceOrdinal'],'sourceId':x['sourceId'],'locale':x['locale'],'sourceTextSha256':x['sourceTextSha256'],'currentTargetSha256':x['currentTargetSha256'],'disposition':x['disposition'],'recommendedTargetSha256':x['recommendedTargetSha256'],'finalTargetSha256':x['finalTargetSha256'],'protectedLiterals':x['protectedLiterals'],'checks':x['structuralChecks']} for x in review])
(OUT/'manual-protected-literals.json').write_text(json.dumps({'bySourceId':{},'sourceRegistryLiteralsAlsoApplied':True,'basis':'Exact source-registered protected literals; this W950–999 slice has none.'},ensure_ascii=False,indent=2,sort_keys=True)+'\n')
(OUT/'external-language-references.json').write_text(json.dumps({
 'retrievedAtUtc':'2026-11-02',
 'purpose':'Reference lookups for selected lexical corrections only; these do not substitute for native-speaker approval.',
 'references':[
  {'id':'ar-icelandic','title':'Arabic Academy of Cairo research PDF using الأيسلندية','url':'https://www.arabicacademy.gov.eg/storage/options/pdfs/154_research.pdf','supports':'Arabic spelling used for Icelandic.'},
  {'id':'de-koreanisch','title':'Duden: Koreanisch','url':'https://www.duden.de/rechtschreibung/Koreanisch','supports':'Koreanisch is the noun naming the Korean language; German capitalization.'},
  {'id':'de-pandschabi','title':'Duden: Pandschabi','url':'https://www.duden.de/rechtschreibung/Pandschabi','supports':'Pandschabi is the neuter German noun for the language.'},
  {'id':'es-manes','title':'DLE (RAE-ASALE): manés, sa','url':'https://dle.rae.es/man%C3%A9s','supports':'Manés is the name of the language spoken on the Isle of Man.'},
  {'id':'es-punyabi','title':'FundéuRAE: panyabí / punyabí','url':'https://www.fundeu.es/consulta/panyabi-1586/','supports':'Recommends punyabí in Spanish.'},
  {'id':'fr-grec-ancien','title':'Larousse English-French: Greek','url':'https://www.larousse.fr/dictionnaires/anglais-francais/Greek/584473','supports':'Uses grec ancien for ancient Greek.'},
  {'id':'fr-pendjabi','title':'Larousse French-English: pendjabi','url':'https://www.larousse.fr/dictionnaires/francais-anglais/pendjabi/1011640','supports':'Lists pendjabi as the French form for Punjabi.'}
 ]
},ensure_ascii=False,indent=2,sort_keys=True)+'\n')
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
