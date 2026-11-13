#!/usr/bin/env python3
import json,re,sys
from pathlib import Path
root=Path(__file__).resolve().parent
input_dir=root.parent/'input'/'candidate-free-input'
ledger=[json.loads(x) for x in (root/'reviewer-ledger.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
cells=[json.loads(x) for x in (input_dir/'current-target-cells.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
source_map={r['sourceId']:r for r in [json.loads(x) for x in (input_dir/'source-and-caller-context.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]}
errors=[]
expected={(r['locale'],r['sourceId']):r for r in cells}
actual={(r['locale'],r['sourceId']):r for r in ledger}
if len(ledger)!=20 or set(actual)!=set(expected): errors.append('20-cell scope')
allowed={'accept-current','correction','refinement','hold'}
ph=re.compile(r'<[^>]+>|%[A-Za-z][A-Za-z0-9_]*%|\{\{[^{}]*\}\}|\{[0-9]+\}|%\d*\$?[sdif]')
mt=re.compile(r'<\s*/?\s*[A-Za-z][^>]*>')
for key,r in actual.items():
  c=expected[key]; src=source_map[c['sourceId']]
  if r.get('head')!='28cdae837118a426ac867fb468a5e5a6937cbb9b' or r.get('tree')!='e6e7f1344d08eddbc421d339f91594847a625c10': errors.append('pin '+str(key))
  if r.get('sourceSha256')!=c['sourceSha256'] or r.get('currentTargetSha256')!=c['currentTargetSha256']: errors.append('text hash '+str(key))
  if r.get('disposition') not in allowed or r.get('confidence') not in {'high','moderate','low','unknown'} or not r.get('rationale'): errors.append('review fields '+str(key))
  checks=r.get('currentTargetChecks',{})
  if checks.get('protectedLiterals')!=c['protectedLiteralChecks']: errors.append('protected literal current '+str(key))
  if checks.get('sourcePlaceholderSequence')!=c['sourcePlaceholderSequence'] or checks.get('currentTargetPlaceholderSequence')!=c['currentTargetPlaceholderSequence'] or checks.get('placeholderSequenceMatchesSource') is not True: errors.append('placeholder current '+str(key))
  if checks.get('sourceMarkupTagSequence')!=c['sourceMarkupTagSequence'] or checks.get('currentTargetMarkupTagSequence')!=c['currentTargetMarkupTagSequence'] or checks.get('markupTagSequenceMatchesSource') is not True: errors.append('markup current '+str(key))
  has_text='recommendedTargetText' in r
  if r['disposition'] in {'hold','accept-current'} and has_text: errors.append('unneeded target text '+str(key))
  if r['disposition'] in {'correction','refinement'} and not has_text: errors.append('missing recommended target '+str(key))
  if r['sourceId']=='ui.loading.dodgeBooks':
    if r['disposition']!='hold' or has_text: errors.append('Dodge must remain text-free hold '+str(key))
    if not checks.get('protectedLiterals') or any(not x.get('exactPreservationPass') for x in checks['protectedLiterals']): errors.append('Dodge protected literal '+str(key))
  if has_text:
    target=r['recommendedTargetText']; tc=r['recommendedTargetChecks']
    if ph.findall(target)!=src.get('sourcePlaceholderSequence',[]): errors.append('placeholder recommendation '+str(key))
    if mt.findall(target)!=src.get('sourceMarkupTagSequence',[]): errors.append('markup recommendation '+str(key))
    if tc.get('placeholderSequence')!=ph.findall(target) or tc.get('placeholderSequenceMatchesSource') is not True: errors.append('placeholder record '+str(key))
    if tc.get('markupTagSequence')!=mt.findall(target) or tc.get('markupTagSequenceMatchesSource') is not True: errors.append('markup record '+str(key))
    for x in tc.get('protectedLiterals',[]):
      if x.get('recommendedTargetCount',0)<x.get('sourceCount',0) or not x.get('exactPreservationPass'): errors.append('protected recommendation '+str(key))
  if any(k in r for k in ('currentTarget','currentTargetText')): errors.append('current target copied into ledger '+str(key))
print(json.dumps({'result':'FAIL' if errors else 'PASS','cells':len(ledger),'holds':sum(x['disposition']=='hold' for x in ledger),'errors':errors},sort_keys=True))
sys.exit(bool(errors))
