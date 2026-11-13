#!/usr/bin/env python3
import hashlib, json, pathlib, re, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parent
REPO=pathlib.Path('/home/keith/Documents/code/.task-worktrees/localization-20261105/chaptarrng-w500')
BASE=REPO/'src/NzbDrone.Core/Localization/Core'
CODE=REPO/'src/NzbDrone.Core/Download/Clients/Nzbget/Nzbget.cs'
HEAD='c01c3974a01dfcab6a1aa09401c66d412bc88e60'
TREE='55ea7696f4981fc56a774f38be477f89e454a7a3'
CURRENT_ID='server.message.m453c42aa8de5'
PROPOSED_ID='server.message.m3a79390fb21e'
ENGLISH_CURRENT='NzbGet setting KeepHistory should be less than 25000'
ENGLISH_PROPOSED='NzbGet setting KeepHistory must not exceed 25000'
TARGETS={
 'ar':('يجب ألا يتجاوز إعداد KeepHistory في NzbGet القيمة 25000.','Current Arabic says the setting must be less than 25000, which rejects the allowed boundary. This wording says it must not exceed 25000.'),
 'de':('Die KeepHistory-Einstellung von NzbGet darf 25000 nicht überschreiten.','Current German says the setting must be below 25000, which rejects the allowed boundary. This wording sets 25000 as an inclusive maximum.'),
 'es':('La opción KeepHistory de NzbGet no debe superar 25000.','Current Spanish says the option must be below 25000, which rejects the allowed boundary. This wording says it must not exceed 25000.'),
 'fr':('La valeur du paramètre KeepHistory de NzbGet ne doit pas dépasser 25000.','Current French says the parameter must be below 25000, which rejects the allowed boundary. This wording sets 25000 as an inclusive maximum.'),
 'hi':('NzbGet की KeepHistory सेटिंग 25000 से अधिक नहीं होनी चाहिए।','Current Hindi says the setting must be less than 25000, which rejects the allowed boundary. This wording says it must not be greater than 25000.'),
 'id':('Pengaturan KeepHistory di NzbGet tidak boleh melebihi 25000.','Current Indonesian says the setting must be less than 25000, which rejects the allowed boundary. This wording says it may not exceed 25000.'),
 'ja':('NzbGet の KeepHistory 設定は 25000 以下である必要があります。','Current Japanese says the setting must be below 25000, which rejects the allowed boundary. “25000 以下” explicitly includes 25000.'),
 'ko':('NzbGet의 KeepHistory 설정은 25000을 초과하면 안 됩니다.','Current Korean says the setting must be less than 25000, which rejects the allowed boundary. This wording says it must not exceed 25000.'),
 'pt_BR':('O valor de KeepHistory no NzbGet não deve exceder 25000.','Current Brazilian Portuguese says the setting must be below 25000, which rejects the allowed boundary. This wording says it must not exceed 25000.'),
 'vi':('Giá trị KeepHistory trong NzbGet không được vượt quá 25000.','Current Vietnamese says the setting must be less than 25000, which rejects the allowed boundary. This wording says it must not exceed 25000.'),
 'zh_CN':('NzbGet 的 KeepHistory 设置不得超过 25000。','Current Simplified Chinese says the setting should be below 25000, which rejects the allowed boundary. This wording says it may not exceed 25000.'),
 'zh_TW':('NzbGet 的 KeepHistory 設定不得超過 25000。','Current Traditional Chinese says the setting should be below 25000, which rejects the allowed boundary. This wording says it may not exceed 25000.'),
}
def sha(b): return hashlib.sha256(b).hexdigest()
def readj(p): return json.loads(p.read_text(encoding='utf-8'))
def canon(o): return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def git(*args): return subprocess.check_output(['git','-C',str(REPO),*args],text=True).strip()
def main():
 if git('rev-parse','HEAD')!=HEAD or git('rev-parse','HEAD^{tree}')!=TREE or git('status','--porcelain=v1'):
  raise SystemExit('worktree exact pin/clean status mismatch')
 if len(TARGETS)!=12: raise SystemExit('expected 12 target locales')
 code=CODE.read_text(encoding='utf-8').splitlines()
 if len(code)<354 or code[347].strip()!='else if (value > 25000)' or CURRENT_ID not in code[349]: raise SystemExit('caller logic/key mismatch')
 lines=[{'line':i+1,'text':code[i]} for i in range(338,354)]
 caller_window='\n'.join(x['text'] for x in lines)
 if 'int.TryParse(keepHistory, NumberStyles.None, CultureInfo.InvariantCulture, out var value) || value == 0' not in caller_window or 'else if (value > 25000)' not in caller_window: raise SystemExit('expected validation predicates missing')
 en_file=BASE/'en.json'; en_doc=readj(en_file)
 if en_doc.get(CURRENT_ID)!=ENGLISH_CURRENT: raise SystemExit('current English value mismatch')
 source_evidence={
  'artifact':'ChaptarrNG W561 independent blind source/caller evidence',
  'repository':'ChaptarrNG','worktree':str(REPO),'head':HEAD,'tree':TREE,
  'currentSourceId':CURRENT_ID,'proposedSourceId':PROPOSED_ID,
  'sourceTransition':'The current validation caller uses the old message key; the correction is prospective and would use the proposed new key.',
  'currentEnglish':{'path':str(en_file.relative_to(REPO)),'fileSha256':sha(en_file.read_bytes()),'gitBlob':git('hash-object',str(en_file.relative_to(REPO))),'value':ENGLISH_CURRENT,'valueSha256':sha(ENGLISH_CURRENT.encode())},
  'proposedEnglish':{'value':ENGLISH_PROPOSED,'valueSha256':sha(ENGLISH_PROPOSED.encode()),'meaning':'Maximum is inclusive: 25000 is allowed; only values greater than 25000 are rejected.'},
  'caller':{'path':str(CODE.relative_to(REPO)),'fileSha256':sha(CODE.read_bytes()),'gitBlob':git('hash-object',str(CODE.relative_to(REPO))),'lineRange':[339,354],'lines':lines,'windowSha256':sha(caller_window.encode()),'predicateLine':348,'validationKeyLine':350,'branchPredicate':'value > 25000','behavior':'The branch rejects values strictly greater than 25000. A parsed value of exactly 25000 does not enter this error branch.'},
  'sourceReview':'The proposed English copy corrects the strict-boundary implication in the current wording while preserving NzbGet, KeepHistory, and 25000.',
  'primaryReviewRead':False}
 (ROOT/'source-caller-evidence.json').write_text(json.dumps(source_evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 rows=[]
 for loc,(proposal,rationale) in TARGETS.items():
  path=BASE/f'{loc}.json'; doc=readj(path); old=doc.get(CURRENT_ID)
  if not isinstance(old,str): raise SystemExit('missing current locale value '+loc)
  def token_check(s): return {'NzbGetPreserved':'NzbGet' in s,'KeepHistoryPreserved':'KeepHistory' in s,'25000Preserved':'25000' in s}
  current_tokens=token_check(old); proposal_tokens=token_check(proposal)
  if not all(current_tokens.values()) or not all(proposal_tokens.values()): raise SystemExit('protected literal missing '+loc)
  if proposal==old: raise SystemExit('proposal does not correct '+loc)
  rows.append({
   'locale':loc,'catalogPath':str(path.relative_to(REPO)),'catalogFileSha256':sha(path.read_bytes()),'catalogGitBlob':git('hash-object',str(path.relative_to(REPO))),
   'currentSourceId':CURRENT_ID,'proposedSourceId':PROPOSED_ID,'currentTarget':old,'currentTargetSha256':sha(old.encode()),
   'currentTokensPreserved':current_tokens,'proposedTarget':proposal,'proposedTargetSha256':sha(proposal.encode()),'proposedTokensPreserved':proposal_tokens,
   'oldBoundaryMeaning':'strictly less than 25000; wrongly excludes exactly 25000','proposedBoundaryMeaning':'must not exceed 25000; allows exactly 25000 and rejects only larger values',
   'action':'propose-correction','rationale':rationale,'confidence':'moderate','reviewMode':'machine semantic and token review',
   'nativeSpeakerApproval':'not performed; these proposals are not native-speaker approved','englishAnchor':ENGLISH_PROPOSED,'englishAnchorSha256':sha(ENGLISH_PROPOSED.encode()),
   'sourceCallerEvidenceSha256':sha(canon(source_evidence)),
  })
 (ROOT/'locale-review.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for r in rows),encoding='utf-8')
 summary={'artifact':'ChaptarrNG W561 independent blind semantic/token review','head':HEAD,'tree':TREE,'currentSourceId':CURRENT_ID,'proposedSourceId':PROPOSED_ID,'sourceIdTransitionRecorded':True,'currentEnglish':ENGLISH_CURRENT,'proposedEnglish':ENGLISH_PROPOSED,'targetLocaleCount':12,'decisionCounts':{'proposal':12,'retain':0,'hold':0},'allCurrentTargetsHaveStrictBoundaryError':True,'allProposalsPreserveNzbGetKeepHistoryAnd25000':True,'machineReviewOnly':True,'nativeSpeakerApprovalPerformed':False,'primaryReviewRead':False,'reposEdited':False,'testsBuildsScansCiRun':False,'sourceCallerHeadPinned':HEAD,'sourceCallerTreePinned':TREE,'worktreeClean':True}
 (ROOT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 readme='''# ChaptarrNG W561 independent blind review\n\nPinned source/caller review at head `c01c3974a01dfcab6a1aa09401c66d412bc88e60` / tree `55ea7696f4981fc56a774f38be477f89e454a7a3`. The current key is `server.message.m453c42aa8de5`; the prospective corrected message uses `server.message.m3a79390fb21e`. The review records both IDs and binds caller evidence to the current pinned code.\n\nThe caller rejects only `value > 25000`; exactly 25000 is permitted. Current English and all 12 target values say “less than 25000,” which excludes that allowed boundary. The ledger proposes inclusive-maximum wording in all 12 target locales and verifies exact preservation of `NzbGet`, `KeepHistory`, and `25000`.\n\nThis is machine semantic/token review with moderate confidence. No native-speaker review or approval was performed. The primary packet was not opened or used. No repository files were edited; no tests, builds, scans, or CI were run.\n\nRun `python3 -B verify_packet.py` from this directory to validate the source pin, caller evidence, locale inputs, proposals, and checksums.\n'''
 (ROOT/'README.md').write_text(readme,encoding='utf-8')
 verifier=r'''#!/usr/bin/env python3
import hashlib,json,pathlib,re,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parent; REPO=pathlib.Path('/home/keith/Documents/code/.task-worktrees/localization-20261105/chaptarrng-w500'); BASE=REPO/'src/NzbDrone.Core/Localization/Core'; CODE=REPO/'src/NzbDrone.Core/Download/Clients/Nzbget/Nzbget.cs'
HEAD='c01c3974a01dfcab6a1aa09401c66d412bc88e60'; TREE='55ea7696f4981fc56a774f38be477f89e454a7a3'; CURRENT_ID='server.message.m453c42aa8de5'; PROPOSED_ID='server.message.m3a79390fb21e'; ENGLISH_CURRENT='NzbGet setting KeepHistory should be less than 25000'; ENGLISH_PROPOSED='NzbGet setting KeepHistory must not exceed 25000'; LOCALES=['ar','de','es','fr','hi','id','ja','ko','pt_BR','vi','zh_CN','zh_TW']
def fail(s): print('FAIL:',s); sys.exit(1)
def sha(b): return hashlib.sha256(b).hexdigest()
def readj(p): return json.loads(p.read_text(encoding='utf-8'))
def git(*args): return subprocess.check_output(['git','-C',str(REPO),*args],text=True).strip()
def main():
 sums={}
 for line in (ROOT/'SHA256SUMS.txt').read_text().splitlines():
  h,n=line.split('  ',1)
  if n in sums or not (ROOT/n).is_file() or sha((ROOT/n).read_bytes())!=h: fail('checksum '+n)
  sums[n]=h
 m=readj(ROOT/'manifest.json')
 if set(sums)!=set(m['files'])|{'manifest.json'} or any(sums.get(n)!=v for n,v in m['files'].items()): fail('manifest/checksum inventory')
 if git('rev-parse','HEAD')!=HEAD or git('rev-parse','HEAD^{tree}')!=TREE or git('status','--porcelain=v1'): fail('worktree pin/clean status')
 ev=readj(ROOT/'source-caller-evidence.json'); code=CODE.read_text(encoding='utf-8').splitlines(); lines=[{'line':i+1,'text':code[i]} for i in range(338,354)]; window='\n'.join(x['text'] for x in lines)
 if ev.get('head')!=HEAD or ev.get('tree')!=TREE or ev.get('currentSourceId')!=CURRENT_ID or ev.get('proposedSourceId')!=PROPOSED_ID: fail('source identity pin')
 if ev.get('caller',{}).get('lines')!=lines or ev.get('caller',{}).get('windowSha256')!=sha(window.encode()) or 'else if (value > 25000)' not in window: fail('caller evidence mismatch')
 en=readj(BASE/'en.json')
 if en.get(CURRENT_ID)!=ENGLISH_CURRENT or ev.get('currentEnglish',{}).get('value')!=ENGLISH_CURRENT or ev.get('proposedEnglish',{}).get('value')!=ENGLISH_PROPOSED: fail('English value mismatch')
 rows=[json.loads(x) for x in (ROOT/'locale-review.jsonl').read_text(encoding='utf-8').splitlines()]
 if [r['locale'] for r in rows]!=LOCALES: fail('locale order/coverage')
 for r in rows:
  loc=r['locale']; path=BASE/f'{loc}.json'; actual=readj(path).get(CURRENT_ID)
  if actual!=r.get('currentTarget') or sha(path.read_bytes())!=r.get('catalogFileSha256') or git('hash-object',str(path.relative_to(REPO)))!=r.get('catalogGitBlob'): fail('current locale binding '+loc)
  if not all(r.get('currentTokensPreserved',{}).values()) or not all(r.get('proposedTokensPreserved',{}).values()): fail('protected token omission '+loc)
  if any(x not in r.get('proposedTarget','') for x in ('NzbGet','KeepHistory','25000')): fail('proposal literal mismatch '+loc)
  if r.get('action')!='propose-correction' or r.get('confidence')!='moderate' or r.get('nativeSpeakerApproval')!='not performed; these proposals are not native-speaker approved': fail('review disposition/mode '+loc)
  if 'less than' not in r.get('oldBoundaryMeaning','') or 'allows exactly 25000' not in r.get('proposedBoundaryMeaning',''): fail('boundary semantics '+loc)
 s=readj(ROOT/'summary.json')
 if s.get('decisionCounts')!={'proposal':12,'retain':0,'hold':0} or s.get('nativeSpeakerApprovalPerformed') is not False or s.get('primaryReviewRead') is not False: fail('summary')
 print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'currentSourceId':CURRENT_ID,'proposedSourceId':PROPOSED_ID,'targetLocales':len(rows),'proposalCount':12,'protectedTokens':'NzbGet, KeepHistory, 25000','machineReviewOnly':True,'nativeSpeakerApprovalPerformed':False,'primaryReviewRead':False},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
'''
 (ROOT/'verify_packet.py').write_text(verifier,encoding='utf-8')
 files=sorted(p for p in ROOT.iterdir() if p.is_file() and p.name not in ('manifest.json','SHA256SUMS.txt'))
 manifest={'artifact':'ChaptarrNG W561 independent blind review','head':HEAD,'tree':TREE,'currentSourceId':CURRENT_ID,'proposedSourceId':PROPOSED_ID,'targetLocaleCount':12,'decisionCounts':{'proposal':12,'retain':0,'hold':0},'files':{p.name:sha(p.read_bytes()) for p in files}}
 (ROOT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 sumsfiles=sorted(p for p in ROOT.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt')
 (ROOT/'SHA256SUMS.txt').write_text(''.join(f'{sha(p.read_bytes())}  {p.name}\n' for p in sumsfiles),encoding='utf-8')
 print(json.dumps({'result':'BUILT','localeCount':len(TARGETS),'files':len(sumsfiles)},indent=2))
if __name__=='__main__': main()
