#!/usr/bin/env python3
from __future__ import annotations
import argparse, collections, hashlib, json, pathlib, re, subprocess, sys, unicodedata
ROOT=pathlib.Path(__file__).resolve().parent
HEAD='9fd23606fbb4c8928505772413e5c23e85352adc'; TREE='cba466021a9a0c9699ef171ddc6a510a69209083'
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
PH=re.compile(r'\{[^{}]+\}'); CODE=re.compile(r'`([^`]+)`'); TAG=re.compile(r'</?[A-Za-z][^>]*>')
PROT=re.compile(r'\b(?:[A-Z][A-Z0-9]{1,}|[A-Z]+[0-9][A-Z0-9]*)\b'); BRANDS={'Chaptarr','ChaptarrNG','AudioBookShelf'}
OPAQUE={'AllowedLanguagesHelpText':['eng','swe'],'ApplicationUrlHelpText':['http(s)://'],'AptUpdater':['apt'],'AudibleCatalog':['Audible'],'AudibleMarketplace':['Audible']}
HOLD_FIELDS={'sourceKey','cellId','sourceText','currentTarget','selectedTarget','primaryTarget','primaryProposalTarget','recommendedTarget','finalReviewedTarget'}
def fail(s): raise SystemExit('FAIL: '+s)
def sha(b): return hashlib.sha256(b).hexdigest()
def sht(s): return sha(s.encode('utf-8'))
def jl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def ph(s): return collections.Counter(PH.findall(s))
def code(s): return collections.Counter(CODE.findall(s))
def tags(s): return collections.Counter(TAG.findall(s))
def nums(s):
 out=[]
 for m in re.findall(r'\d+',s): out.append(''.join(str(unicodedata.digit(c)) if c.isdigit() else c for c in m))
 return collections.Counter(out)
def literals(s): return sorted(set(PROT.findall(s))|(BRANDS&set(re.findall(r'\b[A-Za-z][A-Za-z0-9]*\b',s))))
def verify_tokens(cell,target,key,loc):
 src=cell['sourceText']
 if ph(src)!=ph(target): fail(f'placeholder parity {key}/{loc}')
 if code(src)!=code(target): fail(f'inline-code parity {key}/{loc}')
 if tags(src)!=tags(target): fail(f'markup parity {key}/{loc}')
 if nums(src)!=nums(target): fail(f'numeric parity {key}/{loc}')
 required=set(literals(src))|set(OPAQUE.get(key,[]))
 if any(t not in target for t in required): fail(f'protected/opaque literal parity {key}/{loc}')
def check_sums(directory,name):
 subprocess.run(['sha256sum','-c',name],cwd=directory,check=True,stdout=subprocess.DEVNULL)
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--candidate-free',required=True,type=pathlib.Path); ap.add_argument('--primary',required=True,type=pathlib.Path); ap.add_argument('--source-worktree',required=True,type=pathlib.Path); a=ap.parse_args()
 cf=a.candidate_free.resolve(); primary=a.primary.resolve(); repo=a.source_worktree.resolve()
 if (cf/'candidate-free-manifest.json').is_file(): cfroot=cf
 else: fail('candidate-free directory missing manifest')
 if not (primary/'primary-review-summary.json').is_file(): fail('primary directory missing summary')
 check_sums(cfroot,'candidate-free-SHA256SUMS.txt')
 check_sums(primary,'primary-review-SHA256SUMS.txt')
 subprocess.run([sys.executable,str(cfroot/'verify_candidate_free.py'),'--source-worktree',str(repo)],check=True,stdout=subprocess.DEVNULL)
 subprocess.run([sys.executable,str(primary/'verify_primary_review.py')],check=True,stdout=subprocess.DEVNULL)
 cf_lines=(cfroot/'candidate-free-cells.jsonl').read_bytes().splitlines(); p_lines=(primary/'primary-review-cells.jsonl').read_bytes().splitlines(); prop_lines=(primary/'primary-review-proposals.jsonl').read_bytes().splitlines()
 src=jl(cfroot/'candidate-free-cells.jsonl'); primary_rows=jl(primary/'primary-review-cells.jsonl'); props=jl(primary/'primary-review-proposals.jsonl')
 ledger=jl(ROOT/'cross-ledger.jsonl'); selected=jl(ROOT/'selected-changes.jsonl'); holds=jl(ROOT/'holds-hash-only.jsonl')
 if not (len(src)==len(primary_rows)==len(ledger)==600): fail('expected 600 input, primary, and cross ledger rows')
 im={(r['sourceOrdinal'],r['locale']):i for i,r in enumerate(src)}
 pm={(r['sourceOrdinal'],r['locale']):i for i,r in enumerate(primary_rows)}
 om={(r['sourceOrdinal'],r['locale']):r for r in ledger}
 if len(im)!=600 or len(pm)!=600 or len(om)!=600 or not (set(im)==set(pm)==set(om)): fail('coverage/uniqueness mismatch')
 propmap={(r['sourceKey'],r['locale']):i for i,r in enumerate(props)}
 counts=collections.Counter(); selected_rebuilt=[]; holds_rebuilt=[]; source_cell_rows=collections.defaultdict(list)
 for ident,i in im.items():
  c=src[i]; p=primary_rows[pm[ident]]; row=om[ident]; key,loc=c['sourceKey'],c['locale']
  if row.get('batch')!='W100-149' or row.get('sourceOrdinal')!=ident[0] or row.get('locale')!=loc: fail(f'row identity {ident}')
  if row.get('candidateFreeRowSha256')!=sha(cf_lines[i]): fail(f'input row hash {ident}')
  if row.get('primaryReviewRowSha256')!=sha(p_lines[pm[ident]]): fail(f'primary row hash {ident}')
  if row.get('callerContextSha256')!=c['callerContextSha256'] or row.get('callerReferenceCount')!=c['callerReferenceCount']: fail(f'caller pin {ident}')
  if c['callerReferenceCount']==0:
   counts['hold']+=1
   if p.get('primaryDisposition')!='hold' or row.get('primaryDisposition')!='hold' or row.get('crossDisposition')!='hold': fail(f'callerless hold disposition {ident}')
   if any(f in row for f in HOLD_FIELDS): fail(f'held text exposed at {ident}')
   if row.get('sourceKeySha256')!=sht(key) or row.get('cellIdSha256')!=sht(f'{key}::{loc}'): fail(f'held identity hash {ident}')
   if row.get('sourceTextSha256')!=c['sourceTextSha256'] or row.get('currentTargetSha256')!=c['currentTargetSha256']: fail(f'held source/target hash {ident}')
   if not row.get('holdReason') or row.get('confidence') not in ('high','moderate','low'): fail(f'hold rationale/confidence {ident}')
   holds_rebuilt.append(row); continue
  # Caller-backed rows contain text because they are adjudicated cells, and must match candidate-free input exactly.
  for f in ('sourceKey','sourceText','sourceTextSha256','sourceFile','sourceFileSha256','sourceFileGitBlob','targetFile','targetFileSha256','targetFileGitBlob','currentTarget','currentTargetSha256','callerRefs'):
   if row.get(f)!=c.get(f): fail(f'caller-backed input mismatch {f} at {ident}')
  expected_paths=c.get('callerPaths',sorted({ref['path'] for ref in c['callerRefs']}))
  if row.get('cellId')!=f'{key}::{loc}' or row.get('callerPaths')!=expected_paths: fail(f'caller-backed identity/path mismatch {ident}')
  if p.get('sourceKey')!=key or p.get('locale')!=loc or p.get('sourceTextSha256')!=c['sourceTextSha256'] or p.get('currentTargetSha256')!=c['currentTargetSha256']: fail(f'primary row source/current mismatch {ident}')
  if row.get('primaryDisposition')!=p.get('primaryDisposition'): fail(f'primary disposition mismatch {ident}')
  if row.get('primaryTargetSha256')!=p.get('finalReviewedTargetSha256'): fail(f'primary final-target hash mismatch {ident}')
  if not row.get('crossRationale'): fail(f'cross rationale missing {ident}')
  if row['crossDisposition']=='accept-current':
   counts['accept-current']+=1
   if p['primaryDisposition']!='accept-current' or p['finalReviewedTarget']!=c['currentTarget']: fail(f'accept disposition mismatch {ident}')
   if row.get('selectedTarget')!=c['currentTarget'] or row.get('selectedTargetSha256')!=c['currentTargetSha256'] or row.get('selectionKind')!='current-value': fail(f'accept changed value {ident}')
   if row.get('primaryProposalRowSha256') is not None or row.get('primaryProposalTarget') is not None: fail(f'proposal on accepted current cell {ident}')
  elif row['crossDisposition']=='select-primary-proposal':
   counts['select-primary-proposal']+=1
   if p['primaryDisposition']!='revise-current' or (key,loc) not in propmap: fail(f'selected proposal missing {ident}')
   pi=propmap[(key,loc)]; prop=props[pi]
   if row.get('primaryProposalRowSha256')!=sha(prop_lines[pi]): fail(f'proposal row hash mismatch {ident}')
   if row.get('primaryProposalTarget')!=prop['recommendedTarget'] or row.get('primaryProposalTargetSha256')!=prop['recommendedTargetSha256']: fail(f'proposal target mismatch {ident}')
   if row.get('selectedTarget')!=prop['recommendedTarget'] or row.get('selectedTargetSha256')!=prop['recommendedTargetSha256'] or p['finalReviewedTarget']!=prop['recommendedTarget']: fail(f'selected target differs from proposal {ident}')
   verify_tokens(c,row['selectedTarget'],key,loc)
   selected_rebuilt.append(row)
  else: fail(f'unknown cross disposition {ident}')
  verify_tokens(c,row['selectedTarget'],key,loc)
  source_cell_rows[key].append({'sourceOrdinal':ident[0],'locale':loc,'cellId':f'{key}::{loc}','selectedTargetSha256':row['selectedTargetSha256'],'crossDisposition':row['crossDisposition']})
 if counts!=collections.Counter({'accept-current':390,'select-primary-proposal':42,'hold':168}): fail(f'cross disposition counts {dict(counts)}')
 if len(selected)!=42 or len(selected_rebuilt)!=42 or selected!=selected_rebuilt: fail('selected changes extract differs from ledger')
 if len(holds)!=168 or holds!=holds_rebuilt: fail('hash-only holds extract differs from ledger')
 # The source-rewrite recommendations are caller-backed English clarifications; they do not overwrite cell decisions.
 src_notes=json.loads((primary/'primary-review-source-notes.json').read_text())
 recdoc=json.loads((ROOT/'source-rewrite-recommendations.json').read_text())
 if recdoc.get('schemaVersion')!=1 or len(recdoc.get('recommendations',[]))!=2: fail('source rewrite recommendation count')
 expected_sources={'ApplyTagsHelpTextAdd':'Add: Add the tags to the existing list of tags.','AppDataLocationHealthCheckMessage':'Updates are disabled to prevent AppData from being deleted during an update.'}
 cells_by_key=collections.defaultdict(list)
 for c in src: cells_by_key[c['sourceKey']].append(c)
 caller_map={r['sourceKey']:r for r in jl(cfroot/'caller-context.jsonl')}
 for rec in recdoc['recommendations']:
  key=rec['sourceKey']; sample=cells_by_key[key][0]; ctx=caller_map[key]
  if key not in expected_sources or rec.get('proposedSource')!=expected_sources[key] or rec.get('sourceKeySha256')!=sht(key) or rec.get('currentSourceTextSha256')!=sample['sourceTextSha256']: fail('source rewrite wording/pin '+key)
  if rec.get('callerContextSha256')!=ctx['callerContextSha256'] or rec.get('callerReferenceCount')!=ctx['callerReferenceCount'] or rec.get('callerRefs')!=ctx['callerRefs']: fail('source rewrite caller pin '+key)
  if rec.get('recommendation')!='source-wording-only; per-locale cell decisions remain in cross-ledger.jsonl': fail('source rewrite scope '+key)
  expect=[{'sourceOrdinal':c['sourceOrdinal'],'locale':c['locale'],'cellId':f'{key}::{c["locale"]}','selectedTargetSha256':om[(c['sourceOrdinal'],c['locale'])]['selectedTargetSha256'],'crossDisposition':om[(c['sourceOrdinal'],c['locale'])]['crossDisposition']} for c in cells_by_key[key]]
  expect.sort(key=lambda r:LOCALES.index(r['locale']))
  actual=rec['localeCellDispositions']; actual.sort(key=lambda r:LOCALES.index(r['locale']))
  if actual!=expect or len(actual)!=12: fail('source rewrite locale dispositions '+key)
 if {r['sourceKey'] for r in recdoc['recommendations']}!=set(expected_sources): fail('source rewrite keys')
 # Revalidate live PR state and exact refs. Attestation times may differ.
 before=json.loads((ROOT/'live-before.json').read_text()); after=json.loads((ROOT/'live-after.json').read_text())
 for x in (before,after):
  for f,v in [('repository','snapetech-org/chaptarrng'),('pullRequest',190),('state','OPEN'),('draft',True),('merged',False),('headRefName','codex/chaptarrng-localization-complete-20261031'),('headRefOid',HEAD),('branchRefOid',HEAD),('pullRefOid',HEAD),('pullMergeRefOid','d2b3607545f99e7d7e6289c49eb2d65afff4636d'),('baseRefName','main'),('baseRefOid','17bde320915af42de73b8646ad56f8ba2ccebf4e')]:
   if x.get(f)!=v: fail('live PR ref/state '+f)
 if any(before.get(k)!=after.get(k) for k in set(before)|set(after) if k!='attestedUtc'): fail('PR refs/state changed during cross review')
 summary=json.loads((ROOT/'summary.json').read_text()); prov=json.loads((ROOT/'input-provenance.json').read_text())
 if summary.get('crossDispositions')!=dict(counts): fail('summary disposition count')
 if summary.get('primaryProposalsReconciled')!=42 or summary.get('primaryProposalsSelected')!=42 or summary.get('primaryProposalsRevised')!=0 or summary.get('primaryProposalsRejected')!=0: fail('summary proposal reconciliation')
 if summary.get('candidateFreeManifestSha256')!=sha((cfroot/'candidate-free-manifest.json').read_bytes()) or summary.get('candidateFreeChecksumListSha256')!=sha((cfroot/'candidate-free-SHA256SUMS.txt').read_bytes()) or summary.get('candidateFreeCellsSha256')!=sha((cfroot/'candidate-free-cells.jsonl').read_bytes()): fail('candidate-free provenance hash')
 if summary.get('primaryChecksumListSha256')!=sha((primary/'primary-review-SHA256SUMS.txt').read_bytes()) or summary.get('primaryCellsSha256')!=sha((primary/'primary-review-cells.jsonl').read_bytes()) or summary.get('primaryProposalsSha256')!=sha((primary/'primary-review-proposals.jsonl').read_bytes()): fail('primary provenance hash')
 if prov.get('exactHead')!=HEAD or prov.get('exactTree')!=TREE: fail('input provenance pin')
 manifest=json.loads((ROOT/'manifest.json').read_text()); entries={r['path']:r for r in manifest['files']}
 if manifest.get('head')!=HEAD or manifest.get('tree')!=TREE or manifest.get('cellCount')!=600: fail('cross bundle manifest pin')
 if 'manifest.json' in entries or 'SHA256SUMS.txt' in entries: fail('recursive manifest inventory')
 for name,e in entries.items():
  p=ROOT/name
  if not p.is_file() or p.stat().st_size!=e['bytes'] or sha(p.read_bytes())!=e['sha256']: fail('manifest file hash '+name)
 sums={}
 for line in (ROOT/'SHA256SUMS.txt').read_text().splitlines():
  if line.strip(): h,n=line.split('  ',1); sums[n]=h
 if set(sums)!=set(entries)|{'manifest.json'}: fail('checksum inventory')
 for n,h in sums.items():
  if not (ROOT/n).is_file() or sha((ROOT/n).read_bytes())!=h: fail('checksum mismatch '+n)
 print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'sourceCount':50,'localeCount':12,'cellCount':600,'acceptCurrent':counts['accept-current'],'selectedPrimaryProposals':counts['select-primary-proposal'],'textFreeCallerlessHolds':counts['hold'],'callerlessKeys':14,'proposalDisagreementsUnresolved':0,'sourceRewriteRecommendations':2,'placeholderInlineMarkupNumericProtectedParity':'PASS','candidateFreeVerifier':'PASS','primaryVerifier':'PASS','livePR':'OPEN/DRAFT at exact head/tree','checksums':len(sums)},ensure_ascii=False,sort_keys=True))
if __name__=='__main__': main()
