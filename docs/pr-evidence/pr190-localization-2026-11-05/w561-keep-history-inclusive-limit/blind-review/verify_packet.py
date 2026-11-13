#!/usr/bin/env python3
import hashlib,json,pathlib,re,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parent; REPO=pathlib.Path(__file__).resolve().parents[5]
HEAD='c01c3974a01dfcab6a1aa09401c66d412bc88e60'; TREE='55ea7696f4981fc56a774f38be477f89e454a7a3'; CURRENT_ID='server.message.m453c42aa8de5'; PROPOSED_ID='server.message.m3a79390fb21e'; ENGLISH_CURRENT='NzbGet setting KeepHistory should be less than 25000'; ENGLISH_PROPOSED='NzbGet setting KeepHistory must not exceed 25000'; LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt_BR','vi','zh_CN','zh_TW']
def fail(s): print('FAIL:',s); sys.exit(1)
def sha(b): return hashlib.sha256(b).hexdigest()
def readj(p): return json.loads(p.read_text(encoding='utf-8'))
def git(*args): return subprocess.check_output(['git','-C',str(REPO),*args],text=True).strip()
def git_bytes(spec): return subprocess.check_output(['git','-C',str(REPO),'show',spec])
def main():
 sums={}
 for line in (ROOT/'SHA256SUMS.txt').read_text().splitlines():
  h,n=line.split('  ',1)
  if n in sums or not (ROOT/n).is_file() or sha((ROOT/n).read_bytes())!=h: fail('checksum '+n)
  sums[n]=h
 m=readj(ROOT/'manifest.json')
 if set(sums)!=set(m['files'])|{'manifest.json'} or any(sums.get(n)!=v for n,v in m['files'].items()): fail('manifest/checksum inventory')
 if git('rev-parse',f'{HEAD}^{{tree}}')!=TREE: fail('pinned review commit/tree unavailable')
 ev=readj(ROOT/'source-caller-evidence.json'); code=git_bytes(f'{HEAD}:src/NzbDrone.Core/Download/Clients/Nzbget/Nzbget.cs').decode('utf-8').splitlines(); lines=[{'line':i+1,'text':code[i]} for i in range(338,354)]; window='\n'.join(x['text'] for x in lines)
 if ev.get('head')!=HEAD or ev.get('tree')!=TREE or ev.get('currentSourceId')!=CURRENT_ID or ev.get('proposedSourceId')!=PROPOSED_ID: fail('source identity pin')
 if ev.get('caller',{}).get('lines')!=lines or ev.get('caller',{}).get('windowSha256')!=sha(window.encode()) or 'else if (value > 25000)' not in window: fail('caller evidence mismatch')
 en=json.loads(git_bytes(f'{HEAD}:src/NzbDrone.Core/Localization/Core/en.json'))
 if en.get(CURRENT_ID)!=ENGLISH_CURRENT or ev.get('currentEnglish',{}).get('value')!=ENGLISH_CURRENT or ev.get('proposedEnglish',{}).get('value')!=ENGLISH_PROPOSED: fail('English value mismatch')
 rows=[json.loads(x) for x in (ROOT/'locale-review.jsonl').read_text(encoding='utf-8').splitlines()]
 if [r['locale'] for r in rows]!=LOCALES: fail('locale order/coverage')
 for r in rows:
  loc=r['locale']; rel=f'src/NzbDrone.Core/Localization/Core/{loc}.json'; raw=git_bytes(f'{HEAD}:{rel}'); actual=json.loads(raw).get(CURRENT_ID)
  if actual!=r.get('currentTarget') or sha(raw)!=r.get('catalogFileSha256') or git('rev-parse',f'{HEAD}:{rel}')!=r.get('catalogGitBlob'): fail('current locale binding '+loc)
  if not all(r.get('currentTokensPreserved',{}).values()) or not all(r.get('proposedTokensPreserved',{}).values()): fail('protected token omission '+loc)
  if any(x not in r.get('proposedTarget','') for x in ('NzbGet','KeepHistory','25000')): fail('proposal literal mismatch '+loc)
  if r.get('action')!='propose-correction' or r.get('confidence')!='moderate' or r.get('nativeSpeakerApproval')!='not performed; these proposals are not native-speaker approved': fail('review disposition/mode '+loc)
  if 'less than' not in r.get('oldBoundaryMeaning','') or 'allows exactly 25000' not in r.get('proposedBoundaryMeaning',''): fail('boundary semantics '+loc)
 s=readj(ROOT/'summary.json')
 if s.get('decisionCounts')!={'proposal':12,'retain':0,'hold':0} or s.get('nativeSpeakerApprovalPerformed') is not False or s.get('primaryReviewRead') is not False: fail('summary')
 print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'currentSourceId':CURRENT_ID,'proposedSourceId':PROPOSED_ID,'targetLocales':len(rows),'proposalCount':12,'protectedTokens':'NzbGet, KeepHistory, 25000','machineReviewOnly':True,'nativeSpeakerApprovalPerformed':False,'primaryReviewRead':False},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
