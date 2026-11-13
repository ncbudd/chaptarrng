#!/usr/bin/env python3
"""Portable verifier for the ChaptarrNG PR #190 W450-W474 cross-review part."""
import argparse, collections, hashlib, json, re, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
DEFAULT_BASE=HERE.parents[1]
HEAD='16c809b4787d70616a1a296ab0d90cf17923ba86'
TREE='dbd8343a42476f4e830428cc59efb7f4830251d5'
BASE='025498c1a9deb999a4acd1eafc4c807a252e0c29'
BRANCH='codex/chaptarrng-localization-complete-20261031'
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
HOLDS={469,474}
TEXT_FIELDS={'source','sourceText','currentTarget','target','proposedTarget','recommendedTarget','translationProposal'}
PH=re.compile(r'\{[^{}]+\}');INLINE=re.compile(r'`([^`]+)`');MARKUP=re.compile(r'<[^>]+>');NUM=re.compile(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])')
def fail(msg):raise SystemExit('FAIL: '+msg)
def need(ok,msg):
 if not ok:fail(msg)
def sha(b):return hashlib.sha256(b).hexdigest()
def shat(s):return sha(s.encode('utf-8'))
def readj(p):return json.loads(p.read_text(encoding='utf-8'))
def parse(p):return [(raw,json.loads(raw)) for raw in p.read_bytes().splitlines() if raw.strip()]
def jsonl(p):return [r for _,r in parse(p)]
def verify_sums(root):
 expected={}
 for line in (root/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
  h,name=line.split('  ',1);need(name not in expected,'duplicate checksum '+name);expected[name]=h
 actual={p.relative_to(root).as_posix():sha(p.read_bytes()) for p in root.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'}
 need(expected==actual,'checksum inventory/content at '+str(root))
 return sha((root/'SHA256SUMS.txt').read_bytes())
def token_checks(source,target,protected):
 return {'placeholders':sorted(PH.findall(source))==sorted(PH.findall(target)),
         'inlineCode':INLINE.findall(source)==INLINE.findall(target),
         'markup':MARKUP.findall(source)==MARKUP.findall(target),
         'numeric':NUM.findall(source)==NUM.findall(target),
         'protectedLiterals':all(x in target for x in protected)}
def scrub_holds(rows):
 for r in rows:
  need(not (set(r)&TEXT_FIELDS) and 'sourceKey' not in r,'text/key field in hold rows')
  for k,v in r.items():
   if isinstance(v,dict):need(not (set(v)&TEXT_FIELDS),'nested text field in hold rows')

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--candidate-free',type=Path,default=DEFAULT_BASE/'candidate-free'/'input')
 ap.add_argument('--primary',type=Path,default=DEFAULT_BASE/'primary-review')
 ap.add_argument('--blind',type=Path,default=DEFAULT_BASE/'blind-review')
 ap.add_argument('--run-input-verifiers',action='store_true',help='also run the three source packet verifiers')
 args=ap.parse_args();CF=args.candidate_free.resolve();PR=args.primary.resolve();BL=args.blind.resolve()
 output_sum=verify_sums(HERE);cf_sum=verify_sums(CF);p_sum=verify_sums(PR);b_sum=verify_sums(BL)
 manifest=readj(HERE/'manifest.json');summary=readj(HERE/'summary.json');input_att=readj(HERE/'input-reattestation.json')
 need((manifest['exactHead'],manifest['exactTree'],manifest['apiBaseSha'])==(HEAD,TREE,BASE),'manifest PR pins')
 need((summary['exactHead'],summary['exactTree'],summary['apiBaseSha'])==(HEAD,TREE,BASE),'summary PR pins')
 files={f['path']:(f['sha256'],f['bytes']) for f in manifest['files']}
 actual={p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'}
 need(set(files)==actual-{'manifest.json'},'manifest file set')
 for name,(h,n) in files.items():need(sha((HERE/name).read_bytes())==h and (HERE/name).stat().st_size==n,'manifest file pin '+name)
 cfm=readj(CF/'candidate-free-manifest.json');pm=readj(PR/'manifest.json');bm=readj(BL/'manifest.json')
 need((cfm['head'],cfm['tree'],cfm['apiBase'])==(HEAD,TREE,BASE),'candidate-free exact pins')
 need((pm['exactHead'],pm['exactTree'])==(HEAD,TREE),'primary exact pins')
 need((bm['exactHead'],bm['exactTree'],bm['apiBaseSha'])==(HEAD,TREE,BASE),'blind exact pins')
 for key,value in [('candidateFreeManifestSha256',sha((CF/'candidate-free-manifest.json').read_bytes())),('candidateFreeChecksumsSha256',cf_sum),('primaryManifestSha256',sha((PR/'manifest.json').read_bytes())),('primaryChecksumsSha256',p_sum),('blindManifestSha256',sha((BL/'manifest.json').read_bytes())),('blindChecksumsSha256',b_sum)]:need(input_att[key]==value,'input packet pin '+key)
 need((input_att['candidateFreeRowsReattested'],input_att['primaryRowsReattested'],input_att['blindRowsReattested'],input_att['callerBoundRows'],input_att['hashOnlyHoldRows'])==(300,300,300,276,24),'input reattestation scope')
 cfraw=parse(CF/'candidate-free-cells.jsonl');cf={(r['sourceOrdinal'],r['locale']):(raw,r) for raw,r in cfraw}
 p={r['candidateFreeRowSha256']:r for r in jsonl(PR/'ledger.jsonl')};b={r['candidateFreeRowSha256']:r for r in jsonl(BL/'ledger.jsonl')}
 pp={(r['sourceOrdinal'],r['locale']):r for r in jsonl(PR/'proposals.jsonl')};bp={(r['sourceOrdinal'],r['locale']):r for r in jsonl(BL/'proposals.jsonl')}
 ph={r['candidateFreeRowSha256']:r for r in jsonl(PR/'holds.jsonl')};bh={(r['sourceOrdinal'],r['locale']):r for r in jsonl(BL/'holds.jsonl')}
 ledger=jsonl(HERE/'ledger.jsonl');holds=jsonl(HERE/'holds.jsonl');need((len(cf),len(p),len(b),len(ledger),len(holds))==(600,600,600,276,24),'row dimensions')
 need(not any(set(r)&TEXT_FIELDS for r in holds),'held source/target/proposal text leaked')
 held_by={(r['sourceOrdinal'],r['locale']):r for r in holds};need(len(held_by)==24,'hold duplicate identity')
 led_by={(r['sourceOrdinal'],r['locale']):r for r in ledger};need(len(led_by)==276,'ledger duplicate identity')
 expected_keys={(o,l) for o in range(450,475) for l in LOCALES};need(set(held_by)|set(led_by)==expected_keys and not(set(held_by)&set(led_by)),'300-cell coverage')
 need({o for o,l in held_by}==HOLDS and all(o not in HOLDS for o,l in led_by),'hash-only hold ordinals')
 cross_counts=collections.Counter();primary_counts=collections.Counter();blind_counts=collections.Counter();token_fail=collections.Counter();confidence=collections.Counter();proposal_counts=collections.Counter()
 cf_context={r['sourceKey']:r for r in jsonl(CF/'caller-context.jsonl')}
 for key in sorted(expected_keys):
  raw,c=cf[key];rh=sha(raw);pr=p[rh];bl=b[rh];ishold=key in held_by
  need(pr['candidateFreeRowSha256']==bl['candidateFreeRowSha256']==rh,'candidate-free raw row binding')
  need((pr['exactHead'],pr['exactTree'],bl['exactHead'],bl['exactTree'])==(HEAD,TREE,HEAD,TREE),'review row PR pin')
  need((pr['sourceTextSha256'],pr['currentTargetSha256'],pr['callerContextSha256'])==(c['sourceTextSha256'],c['currentTargetSha256'],c['callerContextSha256']),'primary hashes bind candidate cell')
  need((bl['sourceTextSha256'],bl['currentTargetSha256'],bl['callerContextSha256'])==(c['sourceTextSha256'],c['currentTargetSha256'],c['callerContextSha256']),'blind hashes bind candidate cell')
  need((shat(c['sourceText']),shat(c['currentTarget']))==(c['sourceTextSha256'],c['currentTargetSha256']),'candidate cell text hashes')
  primary_counts[pr['decision']]+=1;blind_counts[bl['decision']]+=1
  if ishold:
   h=held_by[key];need(c['callerReferenceCount']==0 and pr['decision']==bl['decision']=='hold-hash-only','hold state/caller count')
   need((h['candidateFreeRowSha256'],h['sourceTextSha256'],h['currentTargetSha256'],h['callerContextSha256'])==(rh,c['sourceTextSha256'],c['currentTargetSha256'],c['callerContextSha256']),'hold hash binding')
   need((h['sourceOrdinal'],h['locale'],h['cellIdSha256'])==(key[0],key[1],shat(c['sourceKey']+'::'+key[1])),'hold identity hash')
   need((h['sourceFileGitBlob'],h['targetFileGitBlob'])==(c['sourceFileGitBlob'],c['targetFileGitBlob']),'hold catalog blob pins')
   phold=ph.get(rh);bhold=bh.get(key)
   need(phold is not None and bhold is not None,'review hash-only hold record')
   need(not(set(phold)&TEXT_FIELDS) and not(set(bhold)&TEXT_FIELDS),'review hold text leak')
   need((phold['sourceTextSha256'],phold['currentTargetSha256'])==(c['sourceTextSha256'],c['currentTargetSha256']),'primary hold hashes')
   need((bhold['candidateFreeRowSha256'],bhold['sourceTextSha256'],bhold['currentTargetSha256'])==(rh,c['sourceTextSha256'],c['currentTargetSha256']),'blind hold hashes')
   cross_counts['hold-hash-only']+=1
   continue
  r=led_by[key]
  need(c['callerReferenceCount']>0,'caller-backed row has zero callers')
  need((r['sourceKey'],r['sourceKeySha256'],r['locale'])==(c['sourceKey'],shat(c['sourceKey']),c['locale']),'ledger key binding')
  need((r['candidateFreeRowSha256'],r['sourceTextSha256'],r['currentTargetSha256'],r['callerContextSha256'])==(rh,c['sourceTextSha256'],c['currentTargetSha256'],c['callerContextSha256']),'ledger row hash binding')
  need(r['currentTarget']==c['currentTarget'] and shat(r['currentTarget'])==r['currentTargetSha256'],'current target exact text/hash')
  need(r['primaryDecision']==pr['decision'] and r['blindDecision']==bl['decision'],'reviewer decision tuple')
  need(r['callerReferenceCount']==c['callerReferenceCount'] and r['sourceFileGitBlob']==c['sourceFileGitBlob'] and r['targetFileGitBlob']==c['targetFileGitBlob'],'caller/catalog pins')
  ctx=cf_context[c['sourceKey']];need(ctx['callerContextSha256']==r['callerContextSha256'],'caller context source pin')
  if (key[0],key[1]) in pp:
   expected=pp[key];got=r.get('primaryProposal');need(got is not None and (got['target'],got['sha256'],got['decision'])==(expected['proposedTarget'],expected['proposedTargetSha256'],expected['decision']),'primary proposal exact target')
   need(shat(got['target'])==got['sha256'],'primary proposal target hash')
  else:need('primaryProposal' not in r,'spurious primary proposal')
  if key in bp:
   expected=bp[key];got=r.get('blindProposal');need(got is not None and (got['target'],got['sha256'],got['decision'])==(expected['recommendedTarget'],expected['recommendedTargetSha256'],expected['decision']),'blind proposal exact target')
   need(shat(got['target'])==got['sha256'],'blind proposal target hash')
  else:need('blindProposal' not in r,'spurious blind proposal')
  need(r['recommendedTargetSha256']==shat(r['recommendedTarget']),'recommended wording hash')
  checks=token_checks(c['sourceText'],r['recommendedTarget'],c.get('protectedLiterals',[]));need(r['tokenChecks']==checks,'recommended token checks')
  for name,ok in checks.items():
   if not ok:token_fail[name]+=1
  if key[0]==471 and key[1] in ('ja','ko'):
   need(r.get('manualNumericAssessment') and not checks['numeric'],'octal lexical numeral exception missing')
  else:need('manualNumericAssessment' not in r,'unexpected manual token exception')
  need(r['crossDecision'] in ('accept-current','accept-consensus-proposal','accept-primary-proposal','accept-blind-proposal','cross-adjustment'),'cross decision enum')
  cross_counts[r['crossDecision']]+=1;confidence[r['confidence']]+=1
  if r.get('primaryProposal'):proposal_counts['primary']+=1
  if r.get('blindProposal'):proposal_counts['blind']+=1
  for k,v in r.items():
   if isinstance(v,dict) and k in ('primaryProposal','blindProposal'):need(not(set(v)&{'source','sourceText','currentTarget'}),'nested proposal contains unapproved fields')
 need(cross_counts==summary['crossDecisionCounts'],'cross decision summary')
 need(primary_counts==summary['primaryDecisionCounts'] and blind_counts==summary['blindDecisionCounts'],'review decision summaries')
 need(token_fail==summary['recommendedTokenCheckFailures'] and token_fail=={'numeric':2},'token exception summary')
 need(confidence==summary['confidenceCounts'],'confidence summary')
 need(proposal_counts=={'primary':summary['primaryProposalCellsInRange'],'blind':summary['blindProposalCellsInRange']},'proposal count summary')
 entry=readj(HERE/'entry-refs.json');exit=readj(HERE/'exit-refs.json')
 for x in (entry,exit):
  need((x['headSha'],x['headTree'],x['baseSha'],x['headRef'])==(HEAD,TREE,BASE,BRANCH),'entry/exit refs pin')
  need((x['state'],x['draft'],x['merged'])==('open',True,False),'entry/exit PR state')
  need(x['branchApiSha']==x['pullRefSha']==HEAD,'entry/exit branch and pull refs')
  need(x['remoteRefs'][f'refs/heads/{BRANCH}']==x['remoteRefs']['refs/pull/190/head']==HEAD,'entry/exit remote branch/pull refs')
 need(entry['mainApiSha']==summary['liveMainAtEntry'] and exit['mainApiSha']==summary['liveMainAtExit'],'entry/exit main summary')
 need(entry['baseSha']==exit['baseSha'] and entry['headSha']==exit['headSha'],'PR head/base moved')
 need(entry['remoteRefs'].get('refs/heads/main')==entry['mainApiSha'] and exit['remoteRefs'].get('refs/heads/main')==exit['mainApiSha'],'entry/exit main ref attestations')
 need(summary['liveMainAtCandidateFreeSeal']=='317c5b431649a69a89e1c795f9490fd4df0b682b','candidate-free main baseline')
 if args.run_input_verifiers:
  for cmd,cwd in [([sys.executable,str(CF/'verify_candidate_free.py')],CF),([sys.executable,str(PR/'verify_primary.py'),'--input',str(CF)],PR),([sys.executable,str(BL/'verify_blind_review.py'),'--candidate-free',str(CF)],BL)]:
   subprocess.run(cmd,cwd=cwd,check=True,stdout=subprocess.DEVNULL)
 print(json.dumps({'result':'PASS','verifier':'portable-cross-review','head':HEAD,'tree':TREE,'base':BASE,'cells':300,'callerBacked':276,'hashOnlyHolds':24,'crossDecisions':dict(cross_counts),'recommendedTokenCheckFailures':dict(token_fail)},indent=2))
if __name__=='__main__':main()
