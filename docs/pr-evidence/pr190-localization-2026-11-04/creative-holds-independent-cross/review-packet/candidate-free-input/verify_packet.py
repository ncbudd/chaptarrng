#!/usr/bin/env python3
import hashlib,json,re,sys
from pathlib import Path
root=Path(__file__).resolve().parent

def sha(b): return hashlib.sha256(b).hexdigest()
def readj(name): return json.loads((root/name).read_text(encoding='utf-8'))
def readjl(name): return [json.loads(x) for x in (root/name).read_text(encoding='utf-8').splitlines() if x.strip()]
errors=[]
manifest=readj('manifest.json'); att=readj('PR-attestation.json'); pins=readj('file-pins.json'); boundary=readj('selection-boundary.json')
cells=readjl('current-target-cells.jsonl'); sources=readjl('source-and-caller-context.jsonl'); prior=readjl('prior-hold-reattestation-hashes-only.jsonl')
expected={('vi','provider.option.o7285d46b982d'),*((x,'ui.loading.newEbookSmell') for x in ('ar','hi','id','ja','ko','vi','zh-Hans','zh-Hant')),*((x,'ui.loading.dodgeBooks') for x in ('ar','de','es','fr','hi','ja','ko','pt-BR','vi','zh-Hans','zh-Hant'))}
if manifest.get('candidateFree') is not True or manifest.get('translationCandidatesIncluded') is not False or manifest.get('priorReviewVerdictsIncluded') is not False: errors.append('candidate-free flags')
if manifest.get('head')!='28cdae837118a426ac867fb468a5e5a6937cbb9b' or manifest.get('tree')!='e6e7f1344d08eddbc421d339f91594847a625c10': errors.append('head/tree pin')
if att.get('state')!='OPEN' or att.get('draft') is not True or att.get('head')!=manifest.get('head') or att.get('tree')!=manifest.get('tree') or att.get('remoteBranchHead')!=manifest.get('head') or att.get('remotePullRefHead')!=manifest.get('head') or att.get('deploymentsObservedBefore')!=0: errors.append('PR attestation')
if len(cells)!=20 or {(x['locale'],x['sourceId']) for x in cells}!=expected: errors.append('20-cell scope')
if len(sources)!=3 or {x['sourceId'] for x in sources}!={'provider.option.o7285d46b982d','ui.loading.dodgeBooks','ui.loading.newEbookSmell'}: errors.append('source context scope')
source_map={x['sourceId']:x for x in sources}
for row in cells:
    if any(k.lower() in {'candidate','proposal','verdict','recommendation','decision'} for k in row): errors.append('proposal field in cell row')
    if sha(row['source'].encode())!=row['sourceSha256'] or sha(row['currentTarget'].encode())!=row['currentTargetSha256']: errors.append('cell text hash '+row['locale']+'/'+row['sourceId'])
    src=source_map.get(row['sourceId'])
    if not src or src['sourceSha256']!=row['sourceSha256'] or src['source']!=row['source']: errors.append('cell/source mismatch')
    tokens=re.findall(r'<[^>]+>|%[A-Za-z][A-Za-z0-9_]*%|\{\{[^{}]*\}\}|\{[0-9]+\}|%\d*\$?[sdif]',row['source'])
    targettokens=re.findall(r'<[^>]+>|%[A-Za-z][A-Za-z0-9_]*%|\{\{[^{}]*\}\}|\{[0-9]+\}|%\d*\$?[sdif]',row['currentTarget'])
    if tokens!=row['sourcePlaceholderSequence'] or targettokens!=row['currentTargetPlaceholderSequence'] or (tokens==targettokens)!=row['placeholderSequenceMatchesSource']: errors.append('placeholder sequence '+row['locale']+'/'+row['sourceId'])
    tags=re.findall(r'<\s*/?\s*[A-Za-z][^>]*>',row['source']); targettags=re.findall(r'<\s*/?\s*[A-Za-z][^>]*>',row['currentTarget'])
    if tags!=row['sourceMarkupTagSequence'] or targettags!=row['currentTargetMarkupTagSequence'] or (tags==targettags)!=row['markupTagSequenceMatchesSource']: errors.append('markup sequence '+row['locale']+'/'+row['sourceId'])
    for check in row['protectedLiteralChecks']:
        lit=check['literal']; present=row['currentTarget'].count(lit)
        if present!=check['presentInCurrentTarget'] or check['presentInSource']!=row['source'].count(lit) or check['exactPreservationPass']!=(present>=check['presentInSource']): errors.append('protected literal '+row['locale']+'/'+row['sourceId'])
if any(x.get('status')!='hash-match' or not x.get('sourceMatch') or not x.get('targetMatch') for x in prior): errors.append('prior hold hash-only reattestation')
if len(prior)!=24: errors.append('prior hold row count')
for row in prior:
    if any(k.lower() in {'source','target','currenttarget','proposal','candidate'} for k in row): errors.append('text field in prior hold row')
for pin in pins['files']:
    if not pin.get('path') or len(pin.get('sha256',''))!=64 or len(pin.get('gitBlob',''))!=40: errors.append('file pin schema')
if manifest.get('selectedCellCount')!=20 or manifest.get('sourceCount')!=3 or manifest.get('priorHoldHashDrifts')!=0: errors.append('manifest counts')
print(json.dumps({'result':'FAIL' if errors else 'PASS','cells':len(cells),'sources':len(sources),'priorHashRows':len(prior),'priorHashMatches':sum(x.get('status')=='hash-match' for x in prior),'errors':errors},sort_keys=True))
sys.exit(bool(errors))
