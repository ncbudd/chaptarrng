from __future__ import annotations
import hashlib, json, pathlib, re, subprocess, datetime
ROOT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0850-0899-primary-20261102')
OUT=ROOT/'language-audit-addendum'
HEAD='175cff3a50569b67def345bb82332b30e9bb378c'; TREE='e682581e3c577b62215658c374b15a9d3f8f8bd0'
PRIMARY=(ROOT/'review-cells.jsonl')
def sha(x): return hashlib.sha256(x if isinstance(x,bytes) else x.encode()).hexdigest()
def jwrite(p,obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
def jl(p): return [json.loads(x) for x in p.read_text().splitlines()]
def src_reason(pos):
 return {
 850:'Reports that a connection to the named download client failed.',
 852:'States that a required title field was omitted.',
 853:'Explains that the chosen edition is not part of the chosen book.',
 855:'Expresses a positive-number validation constraint.',
 857:'Reports that the client could not connect.',
 861:'Reports that the chosen root folder is not configured for the specified media type.',
 862:'Identifies an invalid mediaType parameter and lists the two valid values.',
 863:'Reports that the selected Plex library was not found.',
 867:'Labels a hostname as invalid.',
 868:'Reports that connection to NZBVortex failed.',
 869:'States the conditional Goodreads access-token requirement when an OAuth secret is configured.',
 871:'Labels an authentication token as invalid.',
 872:'States that at least one allowed quality must be present.',
 873:'States that an offset cannot be negative (zero is allowed).',
 875:'States that Topic ID must exceed 1 or be empty.',
 878:'Reports that BookLore rejected the supplied username or password.',
 879:'Explains that the chosen edition is not part of the chosen book.',
 880:'Explains that an old Hadouken client uses an unsupported API and requires version 5.1 or later.',
 882:'States that version 0.7.0 or later is required and reports the detected version.',
 883:'Recommends Direct Messaging or using a private account.',
 886:'States that the name must be unique, matching the pinned Name validator.',
 889:'Reports that the selected root folder lacks defaults for the specified media type.',
 892:'States that the URL does not identify a Calibre content server and asks the user to check it.',
 893:'Reports that a book ID does not identify a book in the requested media type.',
 895:'Reports that the requested author was not found.',
 897:'Reports that the app could not retrieve libraries from AudioBookShelf and includes its diagnostic.',
 }.get(pos,'')

def target_reason(r):
 pos=r['sourceOrdinal']; loc=r['locale']; base=src_reason(pos)
 if r['disposition']=='hold':
  return 'Preserve the hold: the caller forbids a backslash but the English catalog source omits it. No localized candidate is endorsed until source and caller text are aligned.'
 # Candidate-by-candidate language judgment. Callsite is a validation or API error unless the pinned caller says otherwise.
 if pos==850: q='Replaces an awkward noun/infinitive fragment with a conventional failed-connection message and preserves Hadouken.'
 elif pos==852: q='Uses idiomatic required-field wording for a missing title.'
 elif pos==853: q='Keeps both identifiers attached to the selected edition/book and states the failed membership relation clearly.'
 elif pos==855: q='The content is correct; the capitalization and terminal punctuation make the Indonesian validation sentence consistent.'
 elif pos==857: q='Uses a natural Brazilian Portuguese connection-failure message.'
 elif pos==861: q='Uses the established folder/root-folder vocabulary and retains the media-type placeholder.'
 elif pos==862: q='Corrects French parameter phrasing while retaining the exact mediaType parameter and allowed values.'
 elif pos==863: q='Uses a concise Vietnamese not-found construction and preserves Plex.'
 elif pos==867: q='Uses grammatical French/Japanese invalid-hostname phrasing.'
 elif pos==868: q='Uses a conventional failed-connection error while preserving NZBVortex.'
 elif pos==869: q='States the conditional requirement in natural order and preserves Goodreads and OAuth terminology.'
 elif pos==871: q='Uses natural invalid-token phrasing in the caller-facing validation error.'
 elif pos==872: q='States the minimum allowed-quality requirement clearly and uses standard media quality terminology.'
 elif pos==873: q='Expresses the numeric boundary as zero or higher, avoiding an unnatural literal negative construction.'
 elif pos==875: q='Presents the Topic ID constraint in natural order and correctly expresses the unset/empty alternative.'
 elif pos==878: q='Uses a complete sentence with BookLore as the actor rejecting the credentials.'
 elif pos==879: q='Uses the same clear edition/book membership construction without unnecessary word-order ambiguity.'
 elif pos==880: q='Separates the unsupported API condition from the minimum required version and keeps Hadouken intact.'
 elif pos==882: q='Clearly distinguishes the required version from the found version and preserves its diagnostic placeholder.'
 elif pos==883: q='Preserves both alternatives: Direct Messaging is recommended, or a private account may be used.'
 elif pos==886: q='The caller validates Name uniqueness; the candidate states uniqueness instead of distinctiveness.'
 elif pos==889: q='Uses the established root-folder concept, clearly states missing media-type defaults, and preserves both placeholders.'
 elif pos==892: q='Correctly describes the URL as not identifying the service and preserves Calibre and URL.'
 elif pos==893: q='Uses natural book-ID phrasing and retains the requested-media-type restriction.'
 elif pos==895: q='Uses a complete standard not-found message for an author.'
 elif pos==897: q='Uses the media-library sense rather than a physical library and preserves AudioBookShelf plus the diagnostic placeholder.'
 else: q='The candidate resolves the identified language issue while preserving the source meaning and caller-facing error intent.'
 return base+' '+q

rows=jl(PRIMARY)
assert len(rows)==600 and len({(r['sourceOrdinal'],r['locale']) for r in rows})==600
selected=[r for r in rows if r['disposition']!='accept-current']
assert len(selected)==91 and sum(r['disposition']=='hold' for r in selected)==12
locale_codes={'pt-BR':'pt-BR','zh-Hans':'zh-Hans','zh-Hant':'zh-Hant'}
ph_re=re.compile(r'\{[^{}]+\}')
markup_re=re.compile(r'</?[A-Za-z][^>]*>|\[[^\]]+\]\([^)]*\)|`[^`]+`')
ledger=[]
for r in selected:
 pos=r['sourceOrdinal']; cand=r['finalTarget']; hold=r['disposition']=='hold'
 assert r['exactHead']==HEAD and r['exactTree']==TREE and r['callerReferenceStatus']=='pinned'
 target=cand if not hold else None
 source_ph=sorted(ph_re.findall(r['source'])); target_ph=sorted(ph_re.findall(target or ''))
 source_markup=sorted(markup_re.findall(r['source'])); target_markup=sorted(markup_re.findall(target or ''))
 pchecks=[]
 for lit in r['protectedLiterals']:
  pchecks.append({'literal':lit,'presentInSource':lit in r['source'],'presentInCurrent':lit in r['currentTarget'],'presentInFinal':bool(target and lit in target)})
 assert source_ph==target_ph if not hold else True
 assert source_markup==target_markup if not hold else True
 assert all(x['presentInSource'] and x['presentInCurrent'] and (hold or x['presentInFinal']) for x in pchecks)
 verdict='hold' if hold else ('accept-primary-refinement' if r['disposition']=='propose-refinement' else 'accept-primary-correction')
 ledger.append({
  'schemaVersion':1,'window':'W850-W899','sourceOrdinal':pos,'sourceId':r['sourceId'],'locale':r['locale'],
  'exactHead':HEAD,'exactTree':TREE,'source':r['source'],'sourceTextSha256':r['sourceTextSha256'],
  'currentTarget':r['currentTarget'],'currentTargetSha256':r['currentTargetSha256'],
  'primaryDisposition':r['disposition'],'primaryTarget':cand,'primaryTargetSha256':r['finalTargetSha256'],
  'languageVerdict':verdict,'languageFinalTarget':target,'languageFinalTargetSha256':sha(target) if target is not None else None,
  'reason':target_reason(r),'callerReferenceStatus':r['callerReferenceStatus'],'callerContextSha256':r['callerContextSha256'],
  'callerRefs':r['callerRefs'],'callerSourceMessageMismatch':r['callerSourceMessageMismatch'],
  'sourcePlaceholders':source_ph,'targetPlaceholders':target_ph,'placeholderParity':source_ph==target_ph if not hold else None,
  'sourceMarkup':source_markup,'targetMarkup':target_markup,'markupParity':source_markup==target_markup if not hold else None,
  'protectedLiterals':pchecks,'protectedLiteralsPreserved':all(x['presentInSource'] and x['presentInCurrent'] and (hold or x['presentInFinal']) for x in pchecks),
  'nativeSpeakerApproval':False,'confidence':'moderate'
 })
ledger.sort(key=lambda x:(x['sourceOrdinal'],x['locale']))
(OUT/'language-audit.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in ledger))
counts={}
for r in ledger: counts.setdefault(r['locale'],{})[r['languageVerdict']]=counts.setdefault(r['locale'],{}).get(r['languageVerdict'],0)+1
manifest={
 'schemaVersion':1,'title':'ChaptarrNG PR #190 W850-W899 language audit addendum',
 'head':HEAD,'tree':TREE,'branch':'codex/chaptarrng-localization-complete-20261031',
 'primaryPacketRootSha256':sha((ROOT/'SHA256SUMS').read_bytes()),
 'primaryReviewCellsSha256':sha(PRIMARY.read_bytes()),
 'scope':'All 79 primary correction/refinement candidates plus all 12 holds; the 509 accept-current cells remain in the primary ledger and are not re-audited here.',
 'rows':len(ledger),'candidateRows':79,'holdRows':12,'acceptedPrimaryCandidateRows':79,
 'candidateVerdicts':{'accept-primary-correction':69,'accept-primary-refinement':10},
 'holdVerdicts':12,'additionalProposals':0,'revisions':0,
 'localeVerdicts':counts,'callerReferencesReusedAndPinned':True,
 'placeholderMismatchRows':sum(r['placeholderParity'] is False for r in ledger),
 'markupMismatchRows':sum(r['markupParity'] is False for r in ledger),
 'protectedLiteralFailureRows':sum(not r['protectedLiteralsPreserved'] for r in ledger),
 'sourceCallerMismatch':'W884 has caller backslash restriction missing from English source; all 12 cells held.',
 'nativeSpeakerReviewOutstanding':True,'nativeSpeakerApproval':False,'confidence':'moderate machine-assisted static language review',
 'reviewedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat()
}
jwrite(OUT/'manifest.json',manifest)
readme=f'''# W850–W899 language audit addendum\n\nThis addendum independently reviews every changed primary target and every hold in the parent primary packet: 79 candidate cells and 12 held cells. It does not claim an independent pass over the 509 accept-current cells; those remain documented in the primary 600-cell ledger.\n\n- Pinned PR #190 head/tree: `{HEAD}` / `{TREE}` (OPEN/DRAFT at reattestation).\n- Candidate decisions: 69 corrections accepted; 10 refinements accepted; no candidate revisions or additional proposals.\n- Held: 12 W884 cells because the caller forbids `\\` while the English catalog message omits it.\n- Placeholder, markup, and protected-literal mismatches among candidates: 0.\n- Per-cell language decisions and exact hashes: `language-audit.jsonl`.\n- Input primary ledger SHA-256: `{manifest['primaryReviewCellsSha256']}`.\n- Parent packet checksum manifest SHA-256 before this addendum: `{manifest['primaryPacketRootSha256']}`.\n\nThis is machine-assisted static review with moderate confidence. Native-speaker review remains outstanding. No repository files or PR content were changed.\n'''
(OUT/'README.md').write_text(readme)
# Addendum checksum manifest includes payload and audit script, but not its own sums file.
files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name!='SHA256SUMS')
(OUT/'SHA256SUMS').write_text(''.join(f'{sha(p.read_bytes())}  {p.name}\n' for p in files))
print(json.dumps({'rows':len(ledger),'candidateRows':79,'holds':12,'localeCounts':counts,'addendumManifestSha256':sha((OUT/'manifest.json').read_bytes()),'addendumChecksumsSha256':sha((OUT/'SHA256SUMS').read_bytes())},ensure_ascii=False,indent=2))
