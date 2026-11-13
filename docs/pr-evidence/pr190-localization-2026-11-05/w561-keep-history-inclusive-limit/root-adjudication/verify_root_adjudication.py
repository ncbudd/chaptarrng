import hashlib,json,subprocess
from pathlib import Path
p=Path(__file__).parent
rows=[json.loads(s) for s in (p/'root-adjudication.jsonl').read_text().splitlines() if s]
s=json.loads((p/'summary.json').read_text())
def sha(x): return hashlib.sha256(x.encode()).hexdigest()
assert len(rows)==12 and len({r['locale'] for r in rows})==12
assert {r['finalDecision'] for r in rows}=={'correction'}
assert all(r['exactHead']==s['exactHead'] and r['exactTree']==s['exactTree'] for r in rows)
assert all(r['proposedSourceId']==s['proposedSourceId'] for r in rows)
assert all(r['proposedSourceFingerprint']==sha(r['proposedSourceId']+'\0'+r['proposedEnglishSource']) for r in rows)
assert all(r['finalTargetSha256']==sha(r['finalTarget']) for r in rows)
assert all(all(lit in r['finalTarget'] for lit in r['requiredLiterals']) for r in rows)
assert all(r['callerPredicate']=='value > 25000' and r['nativeSpeakerApproval'] is False for r in rows)
assert s['predicateUnchanged'] and s['predicateValue25000Accepted'] and s['finalDispositionCounts']['correction']==12
print(json.dumps({'result':'PASS','rows':len(rows),'locales':len({r['locale'] for r in rows}),'corrections':12,'sourceId':s['proposedSourceId'],'head':s['exactHead'],'tree':s['exactTree'],'nativeSpeakerApproval':False},indent=2))
