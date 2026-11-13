#!/usr/bin/env python3
import hashlib,json,re,sys
from pathlib import Path
root=Path(__file__).resolve().parent
inputroot=root.parent/'candidate-free-input'
manifest=json.loads((root/'summary.json').read_text())
prov=json.loads((root/'reviewer-provenance.json').read_text())
rows=[json.loads(x) for x in (root/'review-ledger.jsonl').read_text().splitlines() if x.strip()]
cells=[json.loads(x) for x in (inputroot/'current-target-cells.jsonl').read_text().splitlines() if x.strip()]
expected={(x['locale'],x['sourceId']):x for x in cells}
errors=[]
if len(rows)!=20 or len(expected)!=20: errors.append('cell count')
if prov.get('pass')!='primary' or prov.get('previousTaskProposalTextConsulted') is not False or prov.get('reviewerIdentityDistinctFromOtherPass') is not False: errors.append('primary provenance')
if prov.get('head')!=manifest.get('head') or prov.get('tree')!=manifest.get('tree'): errors.append('head/tree')
for r in rows:
 k=(r['locale'],r['sourceId']); c=expected.pop(k,None)
 if c is None or r.get('currentTargetSha256')!=c['currentTargetSha256'] or r.get('sourceSha256')!=c['sourceSha256']: errors.append('input hash '+str(k)); continue
 if not r.get('callerBacked'): errors.append('callerless '+str(k))
 if r.get('disposition')=='hold':
  if 'proposedTarget' in r or 'proposedTargetSha256' in r: errors.append('text-bearing hold '+str(k))
 elif r.get('disposition') not in ('accept-current','correction','refinement'): errors.append('bad disposition '+str(k))
 else:
  t=r.get('proposedTarget','')
  if not t or hashlib.sha256(t.encode()).hexdigest()!=r.get('proposedTargetSha256'): errors.append('proposal hash '+str(k))
  toks=re.findall(r'<[^>]+>|%[A-Za-z][A-Za-z0-9_]*%|\{\{[^{}]*\}\}|\{[0-9]+\}|%\d*\$?[sdif]',t)
  src=re.findall(r'<[^>]+>|%[A-Za-z][A-Za-z0-9_]*%|\{\{[^{}]*\}\}|\{[0-9]+\}|%\d*\$?[sdif]',c['source'])
  if toks!=src or not r.get('proposedPlaceholderIntegrity'): errors.append('proposal tokens '+str(k))
  if not r.get('proposedProtectedLiteralsPreserved'): errors.append('proposal literals '+str(k))
if len(expected): errors.append('missing decisions')
if manifest.get('cellCount')!=20 or manifest.get('proposedCount')!=9 or manifest.get('holds')!=11: errors.append('summary counts')
print(json.dumps({'result':'FAIL' if errors else 'PASS','cells':len(rows),'proposals':manifest.get('proposedCount'),'holds':manifest.get('holds'),'errors':errors},sort_keys=True))
sys.exit(bool(errors))
