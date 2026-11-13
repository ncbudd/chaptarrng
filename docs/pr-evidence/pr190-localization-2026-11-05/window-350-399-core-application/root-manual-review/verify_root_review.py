#!/usr/bin/env python3
import hashlib, json
from pathlib import Path
R=Path(__file__).resolve().parent
P=R.parent
crossdir=P/'cross-review'
candidate=P/'candidate-free/input/candidate-free-manifest.json'
summary=json.loads((crossdir/'cross-review-summary.json').read_text())
manifest=json.loads((R/'SUMMARY.json').read_text())
cross=[json.loads(x) for x in (crossdir/'final-cross-review.jsonl').read_text().splitlines() if x.strip()]
review=[json.loads(x) for x in (R/'root-review.jsonl').read_text().splitlines() if x.strip()]
by={(x['sourceOrdinal'],x['locale']):x for x in cross}
assert summary['head']==manifest['head']=='dbe530c9d1a7fd2c12ce2aef76ec74c5c2188aa0'
assert summary['tree']==manifest['tree']=='be10d71209076f753ef295038a9f3c3646a918a3'
assert hashlib.sha256(candidate.read_bytes()).hexdigest()==manifest['candidateFreeManifestSha256']
assert hashlib.sha256((crossdir/'cross-review-summary.json').read_bytes()).hexdigest()==manifest['crossReviewSummarySha256']
assert hashlib.sha256((crossdir/'final-cross-review.jsonl').read_bytes()).hexdigest()==manifest['crossReviewLedgerSha256']
assert hashlib.sha256((R/'root-review.jsonl').read_bytes()).hexdigest()==manifest['rootReviewLedgerSha256']
assert len(review)==112 and len({(x['sourceOrdinal'],x['locale']) for x in review})==112
for x in review:
 c=by[(x['sourceOrdinal'],x['locale'])]
 assert x['sourceKey']==c['sourceKey'] and x['sourceText']==c['sourceText']
 assert x['sourceTextSha256']==c['sourceTextSha256'] and x['callerContextSha256']==c['callerContextSha256']
 assert x['currentTarget']==c['currentTarget'] and x['currentTargetSha256']==c['currentTargetSha256']
 if x['rootDisposition']=='accept-recommended':
  assert c['crossDisposition']=='recommend-revision' and x['recommendedTarget']!=x['currentTarget']
  assert x['recommendedTarget']==c['recommendedTarget']
  assert hashlib.sha256(x['recommendedTarget'].encode()).hexdigest()==x['recommendedTargetSha256']==c['recommendedTargetSha256']
 elif x['rootDisposition']=='maintain-current-noop':
  assert c['crossDisposition']=='recommend-revision' and x['recommendedTarget']==x['currentTarget']
 else:
  assert x['rootDisposition']=='maintain-hold' and c['crossDisposition']=='hold-source-copy'
  assert x['recommendedTarget'] is None
counts={'accept-recommended':sum(x['rootDisposition']=='accept-recommended' for x in review),
        'maintain-current-noop':sum(x['rootDisposition']=='maintain-current-noop' for x in review),
        'maintain-hold':sum(x['rootDisposition']=='maintain-hold' for x in review)}
assert counts==manifest['rootDecisionCounts']=={'accept-recommended':99,'maintain-current-noop':1,'maintain-hold':12}
assert summary['crossDecisionCounts']==manifest['crossDispositionCounts']
print('PASS: exact-head root review; 99 changes accepted, 1 no-op retained, 12 source-copy holds maintained.')
