import collections,hashlib,json,pathlib,re,sys
repo=pathlib.Path('/mnt/disks/scratch/task-worktrees/localization-20261102/chaptarrng-pr190-readonly-0750-0799-a58de8c')
out=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0750-0799-crossreview-20261102')
primary=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0750-0799-primary-20261102')
manifest=json.load(open(primary/'input-manifest.json'))
sha=lambda s:hashlib.sha256(s.encode('utf-8')).hexdigest()
loadjl=lambda p:[json.loads(x) for x in open(p,encoding='utf-8') if x.strip()]
def has_literal(text,lit):
 if re.fullmatch(r'[A-Za-z0-9_]+',lit): return re.search(r'(?<![A-Za-z0-9_])'+re.escape(lit)+r'(?![A-Za-z0-9_])',text) is not None
 return lit in text
rows=loadjl(out/'crossreview-ledger.jsonl')
errors=[]
if len(rows)!=600: errors.append(['cell-count',len(rows)])
if len({(r['locale'],r['sourceId']) for r in rows})!=600: errors.append(['duplicate-cells'])
catalogs={loc:json.load(open(repo/info['path'])) for loc,info in manifest['localeCatalogs'].items()}
source=json.load(open(repo/manifest['sourceCatalog']['path']))
manual=json.load(open(primary/'manual-protected-literals.json'))['additionalProtectedLiteralsByOrdinal']
for r in rows:
 loc,sid=r['locale'],r['sourceId']
 if r['exactHead']!=manifest['head'] or r['exactTree']!=manifest['tree']: errors.append(['pin',loc,sid])
 if source.get(sid)!=r['source'] or sha(r['source'])!=r['sourceTextSha256']: errors.append(['source-readback',loc,sid])
 if catalogs[loc].get(sid)!=r['currentTarget'] or sha(r['currentTarget'])!=r['currentTargetSha256']: errors.append(['current-readback',loc,sid])
 if sha(r['independentTarget'])!=r['independentTargetSha256']: errors.append(['independent-target-hash',loc,sid])
 ph=lambda s:sorted(set(re.findall(r'\{[^{}]+\}|%\d*\$?[sdif]|\$\{[^}]+\}',s)))
 tags=lambda s:[] if re.fullmatch(r'<[^<>/]+>',s) else re.findall(r'</?[A-Za-z][^>]*>',s)
 if ph(r['source'])!=ph(r['currentTarget']) or ph(r['source'])!=ph(r['independentTarget']): errors.append(['placeholder-parity',loc,sid])
 if tags(r['source'])!=tags(r['currentTarget']) or tags(r['source'])!=tags(r['independentTarget']): errors.append(['markup-parity',loc,sid])
 literals=set(r['protectedLiterals'])
 for lit in literals:
  if (has_literal(r['source'],lit) or lit in manual.get(str(r['sourceOrdinal']),[])) and not has_literal(r['independentTarget'],lit):
   errors.append(['protected-literal',loc,sid,lit])
labels=json.load(open(out/'ui-label-evidence.json'))
label_map={x['locale']:x for x in labels['localeLabels']}
w770=[r for r in rows if r['sourceOrdinal']==770]
if len(w770)!=12: errors.append(['w770-count',len(w770)])
for r in w770:
 l=label_map[r['locale']]
 if l['Bookshelf'] not in r['independentTarget'] or l['AuthorEditor'] not in r['independentTarget']:
  errors.append(['w770-ui-labels',r['locale'],l['Bookshelf'],l['AuthorEditor'],r['independentTarget']])
counts=collections.Counter(r['independentDisposition'] for r in rows)
summary={
 'schemaVersion':1,'cells':len(rows),'uniqueCells':len({(r['locale'],r['sourceId']) for r in rows}),
 'independentDispositionCounts':dict(counts),'missedPrimaryCurrentCells':sum(r['primaryDisposition']=='accept-current' and r['independentDisposition'] in ('propose-correction','propose-refinement') for r in rows),
 'revisedPrimaryProposals':sum(r['independentDisposition']=='revise-proposal' for r in rows),
 'independentChangedCells':sum(r['independentTarget']!=r['currentTarget'] for r in rows),
 'placeholderMismatchCells':sum(not r['placeholderParity'] for r in rows),
 'markupMismatchCells':sum(not r['markupParity'] for r in rows),
 'protectedMismatchCells':sum(not r['protectedLiteralsPreserved'] for r in rows),
 'w770LocalizedLabelCells':sum(r['sourceOrdinal']==770 and label_map[r['locale']]['Bookshelf'] in r['independentTarget'] and label_map[r['locale']]['AuthorEditor'] in r['independentTarget'] for r in rows),
 'errors':errors,'verified':not errors,'readOnly':True
}
(out/'crossreview-verification.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True))
if errors: sys.exit(1)
