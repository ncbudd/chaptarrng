#!/usr/bin/env python3
"""Combine the independently sealed W450-W474 and W475-W499 cross-review parts."""
from __future__ import annotations
import datetime, hashlib, json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent; TASK=ROOT.parent
CF=TASK/'candidate-free/input'; P=TASK/'primary-review'; B=TASK/'blind-review'
PARTS=[ROOT/'part-450-474',ROOT/'part-475-499']
REPO=Path('/mnt/disks/scratch/task-worktrees/localization-20261105/chaptarrng-pr190-w400-cross-pinned')
REPO_NAME='snapetech-org/chaptarrng'; PR=190; BRANCH='codex/chaptarrng-localization-complete-20261031'
HEAD='16c809b4787d70616a1a296ab0d90cf17923ba86'; TREE='dbd8343a42476f4e830428cc59efb7f4830251d5'
BASE='025498c1a9deb999a4acd1eafc4c807a252e0c29'; BASE_TREE='3c27ce1d128d1d74d3b46bf507e2f99f9c02f4d8'
LOCS=['ar','de','es','fr','hi','id','ja','ko','pt-BR','vi','zh-Hans','zh-Hant']

def sha(x):
 if isinstance(x,str): x=x.encode('utf-8')
 return hashlib.sha256(x).hexdigest()
def dump(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def j(path): return json.loads(path.read_text(encoding='utf-8'))
def jl(path): return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def jsonl(path,rows): path.write_text(''.join(canon(x)+'\n' for x in rows),encoding='utf-8')
def packet_files(path,exclude_self=False):
 return {p.relative_to(path).as_posix():sha(p.read_bytes()) for p in path.rglob('*') if p.is_file() and not (exclude_self and p==path/'SHA256SUMS.txt')}
def verify_sums(path):
 expected={}
 for line in (path/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
  if line.strip():
   h,n=line.split('  ',1); expected[n]=h
 actual=packet_files(path,exclude_self=True)
 if expected!=actual: raise RuntimeError('checksum mismatch '+str(path))
 return actual
def api(endpoint): return json.loads(subprocess.check_output(['gh','api',endpoint],text=True))
def git(*args): return subprocess.check_output(['git','-C',str(REPO),*args],text=True).strip()
def capture_exit():
 pr=json.loads(subprocess.check_output(['gh','pr','view',str(PR),'--repo',REPO_NAME,'--json','number,state,isDraft,headRefName,headRefOid,baseRefName,baseRefOid,url'],text=True))
 ht=api(f'repos/{REPO_NAME}/commits/{pr["headRefOid"]}')['commit']['tree']['sha']
 bt=api(f'repos/{REPO_NAME}/commits/{pr["baseRefOid"]}')['commit']['tree']['sha']
 main=api(f'repos/{REPO_NAME}/git/ref/heads/main')['object']['sha']; mt=api(f'repos/{REPO_NAME}/commits/{main}')['commit']['tree']['sha']
 refs_text=subprocess.check_output(['git','ls-remote',f'https://github.com/{REPO_NAME}.git',f'refs/heads/{BRANCH}',f'refs/pull/{PR}/head','refs/heads/main'],text=True)
 refs={l.split('\t')[1]:l.split('\t')[0] for l in refs_text.splitlines() if l.strip()}
 lh=git('rev-parse','HEAD'); lt=git('rev-parse','HEAD^{tree}'); clean=not git('status','--porcelain=v1')
 pin=(pr['state'],pr['isDraft'],pr['headRefName'],pr['headRefOid'],ht,pr['baseRefName'],pr['baseRefOid'],bt,refs.get(f'refs/heads/{BRANCH}'),refs.get(f'refs/pull/{PR}/head'),lh,lt,clean)
 exp=('OPEN',True,BRANCH,HEAD,TREE,'main',BASE,BASE_TREE,HEAD,HEAD,HEAD,TREE,True)
 if pin!=exp: raise RuntimeError(f'live PR/head/base/worktree changed at final seal: {pin!r}')
 snap={'capturedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),'pr':pr,'headTree':ht,'baseTree':bt,'mainRef':main,'mainTree':mt,'branchRef':refs.get(f'refs/heads/{BRANCH}'),'pullRef':refs.get(f'refs/pull/{PR}/head'),'localHead':lh,'localTree':lt,'localClean':clean,'pinTuple':list(pin)}
 dump(ROOT/'exit-attestation.json',snap); (ROOT/'exit-remote-refs.txt').write_text(refs_text,encoding='utf-8')
 return snap

def main():
 if any((ROOT/n).exists() for n in ['ledger.jsonl','holds.jsonl','proposals.jsonl','manifest.json']): raise RuntimeError('refusing to overwrite an existing combined packet')
 if not (ROOT/'entry-attestation.json').exists() or not (ROOT/'entry-remote-refs.txt').exists(): raise RuntimeError('missing global entry attestation')
 entry=json.loads((ROOT/'entry-attestation.json').read_text())
 # Revalidate all three source packets before combining parts.
 input_hashes={name:verify_sums(path) for name,path in [('candidate-free',CF),('primary',P),('blind',B)]}
 part_hashes={p.name:verify_sums(p) for p in PARTS}
 part_manifests={p.name:json.loads((p/'manifest.json').read_text()) for p in PARTS}
 part_summaries={p.name:json.loads((p/'summary.json').read_text()) for p in PARTS}
 ledgers=[]; holds=[]; raw_proposals=[]
 for part in PARTS:
  ledgers.extend(jl(part/'ledger.jsonl'))
  for hold in jl(part/'holds.jsonl'):
   hold=dict(hold); hold.setdefault('crossDecision','hold-hash-only'); holds.append(hold)
  if (part/'proposals.jsonl').exists(): raw_proposals.extend(jl(part/'proposals.jsonl'))
 locale_index={l:i for i,l in enumerate(LOCS)}
 ledgers.sort(key=lambda x:(x['sourceOrdinal'],locale_index[x['locale']]))
 holds.sort(key=lambda x:(x['sourceOrdinal'],locale_index[x['locale']]))
 if len(ledgers)!=552 or len(holds)!=48: raise RuntimeError(f'combined row count mismatch {len(ledgers)}/{len(holds)}')
 lmap={(x['sourceOrdinal'],x['locale']):x for x in ledgers}; hmap={(x['sourceOrdinal'],x['locale']):x for x in holds}
 if len(lmap)!=552 or len(hmap)!=48 or set(lmap)&set(hmap): raise RuntimeError('duplicate or overlapping combined cells')
 # Create one uniform, current-head proposal list from each part's final ledger values.
 proposals=[]
 for x in ledgers:
  if x['recommendedTarget']==x['currentTarget']: continue
  proposals.append({'sourceOrdinal':x['sourceOrdinal'],'sourceKey':x['sourceKey'],'sourceKeySha256':x['sourceKeySha256'],'sourceTextSha256':x['sourceTextSha256'],'locale':x['locale'],'candidateFreeRowSha256':x['candidateFreeRowSha256'],'callerContextSha256':x['callerContextSha256'],'currentTarget':x['currentTarget'],'currentTargetSha256':x['currentTargetSha256'],'recommendedTarget':x['recommendedTarget'],'recommendedTargetSha256':x['recommendedTargetSha256'],'crossDecision':x['crossDecision'],'primaryDecision':x['primaryDecision'],'blindDecision':x['blindDecision'],'rationale':x['rationale'],'finalTokenChecks':x.get('tokenChecks',x.get('finalTokenChecks')),'exactHead':HEAD,'exactTree':TREE})
 proposals.sort(key=lambda x:(x['sourceOrdinal'],locale_index[x['locale']]))
 if len(proposals)!=111: raise RuntimeError(f'expected 111 current-head changed cells, got {len(proposals)}')
 jsonl(ROOT/'ledger.jsonl',ledgers); jsonl(ROOT/'holds.jsonl',holds); jsonl(ROOT/'proposals.jsonl',proposals)
 exit_at=capture_exit()
 require_tuple=entry.get('pinTuple')==exit_at.get('pinTuple')
 if not require_tuple: raise RuntimeError('global entry/exit PR/base/worktree pins differ')
 decision_counts={}
 for row in ledgers:
  d=row['crossDecision']; decision_counts[d]=decision_counts.get(d,0)+1
 hold_decisions={}
 for row in holds:
  d=row['crossDecision']; hold_decisions[d]=hold_decisions.get(d,0)+1
 if hold_decisions!={'hold-hash-only':48}: raise RuntimeError('hold decision coverage '+repr(hold_decisions))
 cf=j(CF/'candidate-free-manifest.json'); primary=j(P/'manifest.json'); blind=j(B/'manifest.json')
 # Pair all source-proposal cells from the sealed inputs without exposing hold text.
 pkeys={(x.get('sourceOrdinal'),x.get('locale')) for x in jl(P/'proposals.jsonl')}
 bkeys={(x.get('sourceOrdinal'),x.get('locale')) for x in jl(B/'proposals.jsonl')}
 union=pkeys|bkeys
 summary={'artifact':'ChaptarrNG PR #190 W450-W499 independent semantic cross-review','repository':REPO_NAME,'pullRequest':PR,'stateAtEntry':'OPEN/draft','stateAtExit':'OPEN/draft','branch':BRANCH,'exactHead':HEAD,'exactTree':TREE,'baseSha':BASE,'baseTree':BASE_TREE,'sourceOrdinalRange':[450,499],'sourceCount':50,'localeCount':12,'cellCount':600,'callerBoundCells':552,'hashOnlyHolds':48,'heldSourceOrdinals':[469,474,481,482],'changedCellCount':len(proposals),'retainedCurrentCount':552-len(proposals),'crossDecisionCounts':decision_counts,'holdDecisionCounts':hold_decisions,'proposalInputs':{'primary':len(pkeys),'blind':len(bkeys),'uniqueCells':len(union)},'reviewerAgreement':{'sameDecision':sum(x['primaryDecision']==x['blindDecision'] for x in ledgers),'differentDecision':sum(x['primaryDecision']!=x['blindDecision'] for x in ledgers)},'recommendedTokenCheckFailures':{'numeric':2},'manualLexicalizedOctalExceptions':[{'sourceOrdinal':471,'locale':'ja','target':'8進数','reason':'standard Japanese lexicalized octal term, not a separate source value'},{'sourceOrdinal':471,'locale':'ko','target':'8진수','reason':'standard Korean lexicalized octal term, not a separate source value'}],'inputMainAtSeal':cf['liveMain'],'mainAtEntry':entry['mainRef'],'mainAtExit':exit_at['mainRef'],'mainAdvancedSinceCandidateFreeSeal':entry['mainRef']!=cf['liveMain'],'entryExitHeadTreeBaseStable':True,'nativeSpeakerSignoff':False,'worktreeClean':True,'partSummaries':part_summaries}
 dump(ROOT/'summary.json',summary)
 input_pins={}
 for name,path,files,manifest_file in [('candidate-free',CF,input_hashes['candidate-free'],'candidate-free-manifest.json'),('primary',P,input_hashes['primary'],'manifest.json'),('blind',B,input_hashes['blind'],'manifest.json')]:
  input_pins[name]={'relativePath':path.relative_to(TASK).as_posix(),'filesSha256':files,'checksumListSha256':sha((path/'SHA256SUMS.txt').read_bytes()),'manifestSha256':sha((path/manifest_file).read_bytes()),'fileCount':len(files)}
 part_pins={}
 for part in PARTS:
  part_pins[part.name]={'sha256SumsFileSha256':sha((part/'SHA256SUMS.txt').read_bytes()),'manifestSha256':sha((part/'manifest.json').read_bytes()),'ledgerSha256':sha((part/'ledger.jsonl').read_bytes()),'holdSha256':sha((part/'holds.jsonl').read_bytes()),'fileCount':len(part_hashes[part.name])}
 manifest={'artifact':'ChaptarrNG PR #190 W450-W499 combined cross-review','schemaVersion':1,'repository':REPO_NAME,'pullRequest':PR,'branch':BRANCH,'baseRef':'main','baseSha':BASE,'baseTree':BASE_TREE,'exactHead':HEAD,'exactTree':TREE,'sourceOrdinalRange':[450,499],'cellCount':600,'callerBoundCells':552,'hashOnlyHoldCells':48,'changedCells':111,'inputPackets':input_pins,'crossReviewParts':part_pins,'portableVerifier':'verify_cross_review.py','exactWorktreeVerifierCommand':'python3 verify_cross_review.py --repo /mnt/disks/scratch/task-worktrees/localization-20261105/chaptarrng-pr190-w400-cross-pinned','checksums':'SHA256SUMS.txt','holdPolicy':'holds.jsonl contains only hashes, locale/ordinal metadata, and review disposition; no source or target text.'}
 dump(ROOT/'manifest.json',manifest)
 readme=f'''# ChaptarrNG PR #190 W450–W499 cross-review\n\nThis packet combines the independently sealed W450–W474 and W475–W499 cross-review parts. It covers 50 Core source ordinals × 12 locales = 600 cells at PR head `{HEAD}` / tree `{TREE}`, base `{BASE}` / tree `{BASE_TREE}`, branch `{BRANCH}`.\n\nThere are 552 caller-backed decisions and 48 callerless hash-only holds (source ordinals 469, 474, 481, and 482). Held rows in `holds.jsonl` contain no source or current/recommended target text. The combined `ledger.jsonl` includes all caller-backed cross decisions, and `proposals.jsonl` has the 111 exact target changes selected by the cross reviewers.\n\n## Decisions\n\n- 441 caller-backed cells retain current values. 111 receive a reviewed target recommendation.\n- The 17 primary/blind disagreements in W450–W474 were adjudicated with explicit wording and rationale.\n- Two numeric-token heuristic exceptions are the standard lexicalized octal terms `8進数` (Japanese) and `8진수` (Korean). They do not represent added numeric values; the source word is “Octal.”\n- Live main advanced after candidate-free sealing. Global entry/exit PR head, tree, base, branch, pull-ref, and exact worktree pins remained stable; main at each snapshot is recorded separately.\n- Confidence is moderate overall; native-speaker signoff was not available.\n\n## Verification\n\nPortable verification checks input and part seals, full 600-cell coverage, primary/blind reconciliation, exact target hashes, hold-text exclusion, and token/number exception records:\n\n```sh\npython3 verify_cross_review.py\n```\n\nExact worktree verification also reads the pinned catalogs and Git objects:\n\n```sh\npython3 verify_cross_review.py --repo /mnt/disks/scratch/task-worktrees/localization-20261105/chaptarrng-pr190-w400-cross-pinned\n```\n\nNo repository or PR files were edited. No tests, builds, scans, or CI were run. `SHA256SUMS.txt` seals the combined packet and both review parts.\n'''
 (ROOT/'README.md').write_text(readme,encoding='utf-8')
 files=packet_files(ROOT,exclude_self=True); (ROOT/'SHA256SUMS.txt').write_text(''.join(f'{files[n]}  {n}\n' for n in sorted(files)),encoding='utf-8')
 print(json.dumps({'result':'BUILT','output':str(ROOT),'cells':600,'callerBound':552,'holds':48,'changed':len(proposals),'retainedCurrent':552-len(proposals),'crossDecisions':decision_counts,'inputProposals':{'primary':len(pkeys),'blind':len(bkeys),'unique':len(union)},'mainEntry':entry['mainRef'],'mainExit':exit_at['mainRef']},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
