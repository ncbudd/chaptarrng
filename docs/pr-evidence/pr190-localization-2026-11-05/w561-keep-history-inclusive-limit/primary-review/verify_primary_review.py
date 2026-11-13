#!/usr/bin/env python3
from __future__ import annotations
import collections,hashlib,json,pathlib,subprocess
OUT=pathlib.Path(__file__).resolve().parent
REPO=pathlib.Path(__file__).resolve().parents[5]
HEAD='c01c3974a01dfcab6a1aa09401c66d412bc88e60'; TREE='55ea7696f4981fc56a774f38be477f89e454a7a3'; BRANCH='codex/chaptarrng-localization-complete-20261031'
CODE='src/NzbDrone.Core/Download/Clients/Nzbget/Nzbget.cs'; LOCDIR='src/NzbDrone.Core/Localization/Core'
OLD_ID='server.message.m453c42aa8de5'; OLD_EN='NzbGet setting KeepHistory should be less than 25000'
NEW_ID='server.message.m3a79390fb21e'; NEW_EN='NzbGet setting KeepHistory must not exceed 25000'; NEW_SHA='3a79390fb21e5a7e7e4ea479d3d5f2643862a645f76312b3f107817fde29c5b4'
EXPECTED=[('es','es'),('zh-CN','zh_CN'),('hi','hi'),('de','de'),('ja','ja'),('fr','fr'),('pt-BR','pt_BR'),('ar','ar'),('ko','ko'),('zh-TW','zh_TW'),('vi','vi'),('id','id')]
def sha(b):
 if isinstance(b,str):b=b.encode('utf-8')
 return hashlib.sha256(b).hexdigest()
def rj(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
def rjl(p):return [json.loads(x) for x in pathlib.Path(p).read_text(encoding='utf-8').splitlines() if x.strip()]
def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args],text=True).strip()
def git_bytes(spec):return subprocess.check_output(['git','-C',str(REPO),'show',spec])
def main():
 sums=OUT/'SHA256SUMS.txt'; listed={}
 for line in sums.read_text(encoding='utf-8').splitlines():
  h,n=line.split('  ',1); p=(OUT/n).resolve()
  if n in listed or not p.is_relative_to(OUT.resolve()) or not p.is_file() or sha(p.read_bytes())!=h:raise SystemExit('output checksum failure '+n)
  listed[n]=h
 actual={p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file() and p!=sums}
 if actual!=set(listed):raise SystemExit('output checksum coverage')
 if git('rev-parse',f'{HEAD}^{{tree}}')!=TREE:raise SystemExit('pinned review commit/tree unavailable')
 sr=rj(OUT/'source-review.json'); summary=rj(OUT/'summary.json'); manifest=rj(OUT/'manifest.json'); rows=rjl(OUT/'locale-translations.jsonl')
 if (sr.get('head'),sr.get('tree'),sr.get('branch'))!=(HEAD,TREE,BRANCH):raise SystemExit('source review pin')
 sk=sr.get('sourceKey',{})
 if (sk.get('currentId'),sk.get('currentText'),sk.get('proposedId'),sk.get('proposedText'),sk.get('proposedTextFullSha256'))!=(OLD_ID,OLD_EN,NEW_ID,NEW_EN,NEW_SHA):raise SystemExit('source text/key')
 if sha(NEW_EN)!=NEW_SHA or NEW_ID!='server.message.m'+NEW_SHA[:12] or sr.get('semanticDecision')!='accept-proposed-wording':raise SystemExit('proposed English id/decision')
 raw=git_bytes(f'{HEAD}:{CODE}'); lines=raw.decode('utf-8').splitlines(keepends=True); caller=sr['callerEvidence']
 snippet=''.join(lines[338:353])
 if sha(raw)!=caller.get('fileSha256') or git('rev-parse',f'{HEAD}:{CODE}')!=caller.get('gitBlob') or sha(snippet)!=caller.get('contextSha256'):raise SystemExit('caller file/context hash')
 if (caller.get('lineRange'),caller.get('conditionLine'),caller.get('messageLine'))!=([339,353],348,350):raise SystemExit('caller line pins')
 if lines[347].rstrip('\n')!='            else if (value > 25000)' or lines[349].rstrip('\n')!=caller.get('currentFailureCall'):raise SystemExit('caller validation semantics')
 if 'server.message.m453c42aa8de5' not in lines[349] or 'should be less than 25000' not in lines[349]:raise SystemExit('current failure source binding')
 if not caller.get('value25000Accepted') or not caller.get('valuesAbove25000Rejected'):raise SystemExit('boundary interpretation')
 en=json.loads(git_bytes(f'{HEAD}:{LOCDIR}/en.json'))
 if en.get(OLD_ID)!=OLD_EN or sha(OLD_EN)!=sk.get('currentTextSha256'):raise SystemExit('current English catalog binding')
 expected=set(EXPECTED); got={(r.get('locale'),pathlib.Path(r.get('catalogLocaleFile','')).stem) for r in rows}
 if got!=expected or len(rows)!=12:raise SystemExit('locale coverage')
 for r in rows:
  locale=r['locale']; rel=r['catalogLocaleFile']; catalog=git_bytes(f'{HEAD}:{rel}'); d=json.loads(catalog)
  if d.get(OLD_ID)!=r.get('oldTarget') or sha(r['oldTarget'])!=r.get('oldTargetSha256'):raise SystemExit('old target binding '+locale)
  if sha(catalog)!=r.get('catalogFileSha256') or git('rev-parse',f'{HEAD}:{rel}')!=r.get('catalogGitBlob'):raise SystemExit('locale file pin '+locale)
  if r.get('currentSourceId')!=OLD_ID or r.get('proposedSourceId')!=NEW_ID or r.get('proposedEnglishSource')!=NEW_EN or r.get('proposedEnglishSourceSha256')!=NEW_SHA:raise SystemExit('locale source binding '+locale)
  t=r.get('proposedTarget','')
  if r.get('proposedTargetSha256')!=sha(t) or any(x not in t for x in ('NzbGet','KeepHistory','25000')):raise SystemExit('proposal hash/literals '+locale)
  if not r.get('rationale') or r.get('confidence')!='moderate' or r.get('nativeSpeakerApproval') is not False:raise SystemExit('locale rationale/confidence '+locale)
  if r.get('callerFileSha256')!=sha(raw) or r.get('callerGitBlob')!=caller.get('gitBlob') or r.get('callerContextSha256')!=caller.get('contextSha256'):raise SystemExit('locale caller binding '+locale)
 if summary.get('localeCount')!=12 or summary.get('allRequiredLiteralsPreserved') is not True or summary.get('nativeSpeakerApproval') is not False:raise SystemExit('summary consistency')
 files=manifest.get('files',{}); output_files={p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file() and p.name not in ('manifest.json','SHA256SUMS.txt')}
 if output_files!=set(files):raise SystemExit('manifest coverage')
 for n,h in files.items():
  if sha((OUT/n).read_bytes())!=h:raise SystemExit('manifest file hash '+n)
 print(json.dumps({'result':'PASS','head':HEAD,'tree':TREE,'sourceId':NEW_ID,'localeCount':len(rows),'inclusiveMaximum':'25000 accepted; values above rejected','requiredLiteralsPreserved':True,'nativeSpeakerApproval':False,'outputChecksumEntries':len(listed)},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
