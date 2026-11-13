#!/usr/bin/env python3
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
files=[]
for p in sorted(ROOT.iterdir()):
 if p.is_file() and p.name not in {'manifest.json','SHA256SUMS.txt'}:
  b=p.read_bytes(); files.append({'path':p.name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
summary=json.loads((ROOT/'summary.json').read_text())
manifest={'artifact':'ChaptarrNG PR #190 W100-W149 independent cross review','schemaVersion':1,'repository':'snapetech-org/chaptarrng','pullRequest':190,'batch':'W100-149','head':'9fd23606fbb4c8928505772413e5c23e85352adc','tree':'cba466021a9a0c9699ef171ddc6a510a69209083','sourceCount':50,'localeCount':12,'cellCount':600,'crossDispositions':summary['crossDispositions'],'candidateFreeManifestSha256':summary['candidateFreeManifestSha256'],'candidateFreeChecksumListSha256':summary['candidateFreeChecksumListSha256'],'primaryChecksumListSha256':summary['primaryChecksumListSha256'],'files':files}
(ROOT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=[]
for p in sorted(ROOT.iterdir()):
 if p.is_file() and p.name!='SHA256SUMS.txt': lines.append(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name)
(ROOT/'SHA256SUMS.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'result':'SEALED','files':len(files),'checksums':len(lines),'manifestSha256':hashlib.sha256((ROOT/'manifest.json').read_bytes()).hexdigest(),'checksumListSha256':hashlib.sha256((ROOT/'SHA256SUMS.txt').read_bytes()).hexdigest()}))
