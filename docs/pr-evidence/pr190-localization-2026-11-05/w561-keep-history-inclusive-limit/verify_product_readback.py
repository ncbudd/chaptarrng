import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[4]
base=Path(__file__).parent
r=json.loads((base/'product-readback.json').read_text())
def sha(b): return hashlib.sha256(b).hexdigest()
assert r['predicateUnchanged'] and r['predicate']=='value > 25000'
code=(root/r['callerPath']).read_text()
assert 'else if (value > 25000)' in code and r['source'] in code and r['sourceId'] in code
assert r['previousSourceId'] not in code
for loc,item in r['catalogs'].items():
 d=json.loads((root/item['path']).read_text())
 assert item['sourceId'] in d and item['target']==d[item['sourceId']]
 assert item['fileSha256']==sha((root/item['path']).read_bytes())
 assert item['keyCount']==len(d) and item['keyCount']==r['catalogKeyCount']
 assert r['previousSourceId'] not in d
s=json.loads((root/'docs/localization/server-message-sources.json').read_text())
assert len([x for x in s['records'] if x['id']==r['sourceId']])==1
assert not any(x['id']==r['previousSourceId'] for x in s['records'])
assert len(s['records'])==r['sourceRecordCount']
h=json.loads((root/'docs/localization/source-message-hashes.json').read_text())['messages']
assert r['sourceId'] in h and r['previousSourceId'] not in h and len(h)==r['sourceHashRegistryCount']
print(json.dumps({'result':'PASS','localeCatalogs':len(r['catalogs']),'keyCount':r['catalogKeyCount'],'predicate':r['predicate'],'sourceId':r['sourceId']},indent=2))
