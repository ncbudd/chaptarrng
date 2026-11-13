#!/usr/bin/env python3
import collections,hashlib,json,re,subprocess
from pathlib import Path
TASK=Path('/mnt/disks/scratch/task-scratch/chaptarrng-pr190-w350-399-20261104')
INPUT=TASK/'candidate-free'/'input'; HERE=TASK/'primary-review'
LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']
PH=re.compile(r'\{[^{}]+\}'); INLINE=re.compile(r'`([^`]+)`'); MARKUP=re.compile(r'<[^>]+>'); NUM=re.compile(r'(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])')
PROTECTED=re.compile(r'\b(?:[A-Z][A-Z0-9]{1,}|[A-Z]+[0-9][A-Z0-9]*)\b'); BRANDS={'Chaptarr','ChaptarrNG','AudioBookShelf'}
def sha(b):return hashlib.sha256(b).hexdigest()
def shat(s):return sha(s.encode('utf-8'))
def canon(o):return (json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
def j(name):return json.loads((HERE/name).read_text())
def jl(name):return [json.loads(x) for x in (HERE/name).read_text().splitlines() if x.strip()]
def require(ok,msg):
 if not ok:raise SystemExit('FAIL: '+msg)
def protected(s):return sorted(set(PROTECTED.findall(s)) | (BRANDS & set(re.findall(r'\b[A-Za-z][A-Za-z0-9]*\b',s))))

def main():
 sums={}
 for line in (HERE/'SHA256SUMS.txt').read_text().splitlines():
  h,n=line.split('  ',1);sums[n]=h
 actual={p.relative_to(HERE).as_posix():sha(p.read_bytes()) for p in HERE.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'}
 require(sums==actual,'primary SHA256SUMS file set/content')
 att=json.loads((INPUT/'PR-attestation.json').read_text())
 cand=[json.loads(x) for x in (INPUT/'candidate-free-cells.jsonl').read_text().splitlines()]
 require(sha((INPUT/'SHA256SUMS.txt').read_bytes())==j('primary-review-summary.json')['candidateFreeSumsSha256'],'candidate-free seal linkage')
 require(sha((INPUT/'candidate-free-cells.jsonl').read_bytes())==j('primary-review-summary.json')['candidateFreeCellsSha256'],'candidate-free cell linkage')
 rows=jl('primary-review-cells.jsonl');proposals=jl('primary-review-proposals.jsonl');holds=jl('primary-review-holds.jsonl');summary=j('primary-review-summary.json')
 require(len(cand)==len(rows)==600,'row count')
 require([(r['sourceOrdinal'],r['sourceKey'],r['locale']) for r in rows]==[(c['sourceOrdinal'],c['sourceKey'],c['locale']) for c in cand],'identity/order')
 cfm={(r['sourceKey'],r['locale']):r for r in cand};review={(r['sourceKey'],r['locale']):r for r in rows}
 require(len(review)==600,'identity uniqueness')
 for r in rows:
  c=cfm[(r['sourceKey'],r['locale'])]
  require(r['exactHead']==att['headSha'] and r['exactTree']==att['headTree'] and r['liveMainSha']==att['liveMainSha'],'head pins '+r['cellId'])
  require(r['sourceTextSha256']==c['sourceTextSha256'] and r['currentTargetSha256']==c['currentTargetSha256'],'source/target pins '+r['cellId'])
  require(r['callerContextSha256']==c['callerContextSha256'],'caller pin '+r['cellId'])
  require(r['candidateFreeRowSha256']==sha(canon(c)),'candidate-free row link '+r['cellId'])
  d=r['primaryDisposition']
  if d=='hold-text-free':
   require(r['recommendedTarget'] is None and r['recommendedTargetSha256'] is None and r['finalReviewedTarget'] is None and r['finalReviewedTargetSha256'] is None,'hold has no selected target '+r['cellId'])
  elif d in ('accept-current','revise-current'):
   target=r['currentTarget'] if d=='accept-current' else r['recommendedTarget']
   require(isinstance(target,str) and r['finalReviewedTarget']==target and r['finalReviewedTargetSha256']==shat(target),'final target/hash '+r['cellId'])
   if d=='revise-current':require(r['recommendedTargetSha256']==shat(target),'proposal hash '+r['cellId'])
   require(dict(sorted(collections.Counter(PH.findall(r['sourceText'])).items()))==dict(sorted(collections.Counter(PH.findall(target)).items())),'placeholder parity '+r['cellId'])
   require(INLINE.findall(r['sourceText'])==INLINE.findall(target),'inline-code parity '+r['cellId'])
   require(MARKUP.findall(r['sourceText'])==MARKUP.findall(target),'markup parity '+r['cellId'])
   require(collections.Counter(NUM.findall(r['sourceText']))==collections.Counter(NUM.findall(target)),'numeric token parity '+r['cellId'])
   if c['integrityChecks']['protectedLiteral']:
    require(all(x in target for x in protected(r['sourceText'])),'protected literal preservation '+r['cellId'])
  else:raise SystemExit('FAIL: unknown disposition '+str(d))
 proposal_cells={(r['sourceKey'],r['locale']):r for r in proposals}
 hold_cells={(r['sourceKey'],r['locale']):r for r in holds}
 require(set(proposal_cells)=={i for i,r in review.items() if r['primaryDisposition']=='revise-current'},'proposal ledger linkage')
 require(set(hold_cells)=={i for i,r in review.items() if r['primaryDisposition']=='hold-text-free'},'hold ledger linkage')
 for ident,r in proposal_cells.items():
  base=review[ident]
  require(r['recommendedTarget']==base['recommendedTarget'] and r['recommendedTargetSha256']==base['recommendedTargetSha256'],'proposal target link '+base['cellId'])
 for ident,r in hold_cells.items():
  require(r.get('recommendedTarget') is None and r.get('recommendedTargetSha256') is None,'text-free hold '+r['cellId'])
 require(len(hold_cells)==12 and all(k=='BookVisibilityToggleHelpText' for k,l in hold_cells),'source/context mismatch holds')
 counts=collections.Counter(r['primaryDisposition'] for r in rows)
 require(counts==collections.Counter({'accept-current':summary['counts']['accept-current'],'revise-current':summary['counts']['revise-current'],'hold-text-free':summary['counts']['hold-text-free']}),'summary counts')
 require(summary['currentWindowBlindOrCrossOutputsAccessed'] is False and summary['nativeSpeakerApproval'] is False,'review exposure')
 ex=j('review-process-exposure.json')
 require(ex['currentWindowBlindOrCrossOutputsAccessed'] is False and ex['reviewerRole']=='primary','exposure disclosure')
 manual={(r['locale'],r['recommendedTarget']) for r in proposals if r['sourceKey']=='BookshelfInputManualAddPlaceholder'}
 require(len(manual)==10,'manual shelf proposal count')
 for loc,text in manual:require('read' in text and 'currently-reading' in text,'exact Goodreads shelf labels '+loc)
 print(json.dumps({'result':'PASS','head':summary['exactHead'],'tree':summary['exactTree'],'main':summary['liveMainSha'],'cells':600,'acceptCurrent':counts['accept-current'],'proposedRevisions':counts['revise-current'],'textFreeHolds':counts['hold-text-free'],'candidateFreeSeal':summary['candidateFreeSumsSha256'],'blindOrCrossOutputsAccessed':False,'nativeSpeakerApproval':False},indent=2))
if __name__=='__main__':main()
