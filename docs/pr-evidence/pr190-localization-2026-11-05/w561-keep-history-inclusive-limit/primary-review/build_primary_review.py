#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,pathlib,subprocess
OUT=pathlib.Path('/mnt/disks/scratch/task-scratch/chaptarrng-w561-nzbget-keep-history-primary-review-20261105')
REPO=pathlib.Path('/home/keith/Documents/code/.task-worktrees/localization-20261105/chaptarrng-w500')
HEAD='c01c3974a01dfcab6a1aa09401c66d412bc88e60'; TREE='55ea7696f4981fc56a774f38be477f89e454a7a3'; BRANCH='codex/chaptarrng-localization-complete-20261031'
CODE='src/NzbDrone.Core/Download/Clients/Nzbget/Nzbget.cs'; LOCDIR='src/NzbDrone.Core/Localization/Core'
OLD_ID='server.message.m453c42aa8de5'; OLD_EN='NzbGet setting KeepHistory should be less than 25000'
NEW_EN='NzbGet setting KeepHistory must not exceed 25000'; NEW_SHA='3a79390fb21e5a7e7e4ea479d3d5f2643862a645f76312b3f107817fde29c5b4'; NEW_ID='server.message.m3a79390fb21e'
LOCALES=[
 ('es','es','El ajuste KeepHistory de NzbGet no debe superar 25000.','Uses “no debe superar” to preserve the inclusive maximum; 25000 is allowed.'),
 ('zh-CN','zh_CN','NzbGet 的 KeepHistory 设置不得超过 25000。','“不得超过” expresses an inclusive upper limit while preserving the setting name and exact cap.'),
 ('hi','hi','NzbGet की KeepHistory सेटिंग 25000 से अधिक नहीं होनी चाहिए।','“से अधिक नहीं” means the value cannot be greater than the cap, so equality remains allowed.'),
 ('de','de','Die Einstellung KeepHistory in NzbGet darf 25000 nicht überschreiten.','“Darf … nicht überschreiten” states an inclusive maximum and keeps KeepHistory separate and exact.'),
 ('ja','ja','NzbGet の KeepHistory 設定は 25000 を超えてはいけません。','“超えてはいけません” means must not exceed, rather than strictly less than.'),
 ('fr','fr','Le réglage KeepHistory de NzbGet ne doit pas dépasser 25000.','“Ne doit pas dépasser” keeps the accepted boundary inclusive.'),
 ('pt-BR','pt_BR','A configuração KeepHistory do NzbGet não deve exceder 25000.','“Não deve exceder” states that only values above 25000 are invalid.'),
 ('ar','ar','يجب ألا يتجاوز إعداد KeepHistory في NzbGet 25000.','The Arabic wording says the setting must not exceed the stated inclusive maximum.'),
 ('ko','ko','NzbGet의 KeepHistory 설정은 25000을 초과하면 안 됩니다.','“초과하면 안 됩니다” means the value must not go over 25000.'),
 ('zh-TW','zh_TW','NzbGet 的 KeepHistory 設定不得超過 25000。','“不得超過” expresses an inclusive upper limit and preserves the literal setting name.'),
 ('vi','vi','Cài đặt KeepHistory trong NzbGet không được vượt quá 25000.','“Không được vượt quá” means the value cannot exceed the inclusive cap.'),
 ('id','id','Pengaturan KeepHistory di NzbGet tidak boleh melebihi 25000.','“Tidak boleh melebihi” states a maximum that permits the value 25000.'),
]
def sha(v):
 if isinstance(v,str):v=v.encode('utf-8')
 return hashlib.sha256(v).hexdigest()
def jwrite(p,v):p.write_text(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def jlwrite(p,rows):p.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows),encoding='utf-8')
def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args],text=True).strip()
def main():
 if git('rev-parse','HEAD')!=HEAD or git('rev-parse','HEAD^{tree}')!=TREE or git('branch','--show-current')!=BRANCH or git('status','--porcelain=v1','--untracked-files=all'):raise SystemExit('worktree pin/clean check')
 codepath=REPO/CODE; raw=codepath.read_bytes(); lines=raw.decode('utf-8').splitlines(keepends=True)
 if not ('else if (value > 25000)' in lines[347] and OLD_EN in lines[349] and OLD_ID in lines[349]):raise SystemExit('validation caller changed')
 snippet=''.join(lines[338:353]); context_sha=sha(snippet)
 old_en_catalog=json.loads((REPO/f'{LOCDIR}/en.json').read_text(encoding='utf-8'))
 if old_en_catalog.get(OLD_ID)!=OLD_EN or NEW_ID!='server.message.m'+NEW_SHA[:12] or NEW_ID!='server.message.m3a79390fb21e':raise SystemExit('English source key/hash')
 rows=[]; files={}; locales_summary=[]
 required=('NzbGet','KeepHistory','25000')
 for locale,pathloc,target,rationale in LOCALES:
  rel=f'{LOCDIR}/{pathloc}.json'; p=REPO/rel; data=json.loads(p.read_text(encoding='utf-8'))
  old=data.get(OLD_ID)
  if not isinstance(old,str):raise SystemExit('missing old locale target '+locale)
  if any(token not in target for token in required):raise SystemExit('required literal missing '+locale)
  check={'NzbGet': 'NzbGet' in target,'KeepHistory':'KeepHistory' in target,'25000':'25000' in target}
  if not all(check.values()):raise SystemExit('literal preservation '+locale)
  row={'locale':locale,'catalogLocaleFile':rel,'catalogFileSha256':sha(p.read_bytes()),'catalogGitBlob':git('rev-parse',f'HEAD:{rel}'),'currentSourceId':OLD_ID,'currentEnglishSource':OLD_EN,'currentEnglishSourceSha256':sha(OLD_EN),'oldTarget':old,'oldTargetSha256':sha(old),'proposedSourceId':NEW_ID,'proposedEnglishSource':NEW_EN,'proposedEnglishSourceSha256':sha(NEW_EN),'proposedTarget':target,'proposedTargetSha256':sha(target),'requiredLiterals':list(required),'literalPreservation':check,'callerPath':CODE,'callerLineRange':[339,353],'callerConditionLine':348,'callerMessageLine':350,'callerFileSha256':sha(raw),'callerGitBlob':git('rev-parse',f'HEAD:{CODE}'),'callerContextSha256':context_sha,'confidence':'moderate','rationale':rationale,'nativeSpeakerApproval':False,'reviewType':'primary semantic proposal; not native-speaker approval'}
  rows.append(row);files[rel]=sha(p.read_bytes());locales_summary.append(locale)
 jwrite(OUT/'source-review.json',{'artifact':'ChaptarrNG W561 NzbGet KeepHistory maximum primary semantic review','repository':'snapetech-org/chaptarrng','worktree':str(REPO),'branch':BRANCH,'head':HEAD,'tree':TREE,'sourceKey':{'currentId':OLD_ID,'currentText':OLD_EN,'currentTextSha256':sha(OLD_EN),'proposedId':NEW_ID,'proposedText':NEW_EN,'proposedTextSha256':sha(NEW_EN),'proposedTextFullSha256':NEW_SHA},'semanticDecision':'accept-proposed-wording','semanticRationale':'The validation rejects value > 25000, so 25000 itself is accepted. “Must not exceed 25000” expresses the inclusive upper bound; the prior “should be less than 25000” incorrectly excludes the accepted boundary.','semanticConfidence':'high','callerEvidence':{'file':CODE,'fileSha256':sha(raw),'gitBlob':git('rev-parse',f'HEAD:{CODE}'),'lineRange':[339,353],'conditionLine':348,'conditionText':lines[347].rstrip('\n'),'messageLine':350,'currentFailureCall':lines[349].rstrip('\n'),'contextText':snippet,'contextSha256':context_sha,'value25000Accepted':True,'valuesAbove25000Rejected':True},'worktreeClean':True,'nativeSpeakerApproval':False,'reviewLimit':'This is a proposed message correction and semantic translation review, not native-speaker approval.','directLocales':locales_summary})
 jlwrite(OUT/'locale-translations.jsonl',rows)
 summary={'result':'PASS','artifact':'ChaptarrNG W561 NzbGet KeepHistory maximum primary semantic review','head':HEAD,'tree':TREE,'currentSourceId':OLD_ID,'proposedSourceId':NEW_ID,'proposedEnglish':NEW_EN,'sourceSemanticDecision':'accept-proposed-wording','sourceSemanticConfidence':'high','localeCount':len(rows),'locales':locales_summary,'allRequiredLiteralsPreserved':True,'allProposalsUseInclusiveMaximum':True,'nativeSpeakerApproval':False,'repoEdited':False,'testsBuildsCiRun':False}
 jwrite(OUT/'summary.json',summary)
 readme=f'''# ChaptarrNG W561 NzbGet KeepHistory message review\n\nPinned to worktree head `{HEAD}` / tree `{TREE}`. The current English key is `{OLD_ID}` (“{OLD_EN}”). The proposed text “{NEW_EN}” hashes to `{NEW_SHA}` and source key `{NEW_ID}`.\n\nThe exact validation at `{CODE}:348-350` rejects `value > 25000`; it accepts `value == 25000`. I accept the proposed “must not exceed 25000” wording because it preserves that inclusive boundary. The old “less than 25000” wording wrongly excludes 25000.\n\n`locale-translations.jsonl` contains one proposed concise translation for each direct locale, its old target and hash, the proposed target and hash, rationale, confidence, source ID, and caller-file/context pins. All targets preserve `NzbGet`, `KeepHistory`, and `25000`. Confidence is moderate for locale wording. These are proposed corrections, not native-speaker approval.\n\nVerify with `python3 -B verify_primary_review.py`. No repository or catalog files were edited; no tests, builds, or CI were run.\n'''
 (OUT/'README.md').write_text(readme,encoding='utf-8')
 file_hashes={p.relative_to(OUT).as_posix():sha(p.read_bytes()) for p in OUT.rglob('*') if p.is_file() and p.name not in ('manifest.json','SHA256SUMS.txt')}
 jwrite(OUT/'manifest.json',{'schemaVersion':1,'artifact':'ChaptarrNG W561 NzbGet KeepHistory maximum primary semantic review','repository':'snapetech-org/chaptarrng','head':HEAD,'tree':TREE,'sourceId':NEW_ID,'localeCount':len(rows),'locales':locales_summary,'files':file_hashes})
 sums=''.join(f'{sha(p.read_bytes())}  {p.relative_to(OUT).as_posix()}\n' for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.txt')
 (OUT/'SHA256SUMS.txt').write_text(sums,encoding='utf-8')
 print(json.dumps({'result':'SEALED','output':str(OUT),'head':HEAD,'tree':TREE,'sourceId':NEW_ID,'locales':len(rows),'sha256sumsSha256':sha(sums)},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
