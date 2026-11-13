import collections
import hashlib
import json
import shutil
from pathlib import Path

REPO = Path('/home/keith/Documents/code/task-worktrees/localization-20261102-chaptarrng')
SCRATCH = Path('/mnt/disks/scratch/task-scratch')
PRIMARY = SCRATCH / 'chaptarrng-pr190-window-0850-0899-primary-20261102'
CROSS = SCRATCH / 'chaptarrng-pr190-window-0850-0899-crossreview-20261102'
ADJ = SCRATCH / 'seerr-chaptarr-new-correction-adjudication-20261102'
EVIDENCE = REPO / 'docs/pr-evidence/pr190-localization-2026-11-02/window-0850-0899'
LOCALE_ROOT = REPO / 'src/NzbDrone.Core/Localization/Core'
EXPECTED_HEAD = '175cff3a50569b67def345bb82332b30e9bb378c'
EXPECTED_TREE = 'e682581e3c577b62215658c374b15a9d3f8f8bd0'
SOURCE_ID = 'server.message.mf00d6bc38ae8'
OLD_SOURCE = "Can not contain '', '//', or start/end with '/'"
NEW_SOURCE = "Can not contain '\\', '//', or start/end with '/'"

sha_bytes = lambda value: hashlib.sha256(value).hexdigest()
sha_text = lambda value: hashlib.sha256(value.encode('utf-8')).hexdigest()

def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))

def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]

def render_json(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')

def ordered_key_hash(keys):
    return sha_text('\n'.join(keys))

assert not EVIDENCE.exists(), EVIDENCE
primary_summary = read_json(PRIMARY / 'summary.json')
cross_summary = read_json(CROSS / 'cross-review-summary.json')
adj_summary = read_json(ADJ / 'summary.json')
assert primary_summary['exactHead'] == EXPECTED_HEAD and primary_summary['exactTree'] == EXPECTED_TREE
assert cross_summary['exactHead'] == EXPECTED_HEAD and cross_summary['exactTree'] == EXPECTED_TREE
assert adj_summary['chaptarrHead'] == EXPECTED_HEAD and adj_summary['chaptarrTree'] == EXPECTED_TREE
assert adj_summary['perCohort']['ChaptarrNG'] == {'accept': 14}
assert cross_summary['crossReviewDispositionCounts'] == {
    'accept-current': 495,
    'accept-primary-correction': 69,
    'accept-primary-refinement': 10,
    'propose-additional-correction': 14,
    'retain-hold': 12,
}

primary_rows = read_jsonl(PRIMARY / 'review-cells.jsonl')
cross_rows = read_jsonl(CROSS / 'cross-review-ledger.jsonl')
additional_rows = read_jsonl(CROSS / 'additional-corrections.jsonl')
adj_rows = [row for row in read_jsonl(ADJ / 'adjudication.jsonl') if row['repository'] == 'snapetech-org/ChaptarrNG']
assert len(primary_rows) == len(cross_rows) == 600 and len(additional_rows) == len(adj_rows) == 14
pmap = {(row['sourceOrdinal'], row['locale']): row for row in primary_rows}
cmap = {(row['sourceOrdinal'], row['locale']): row for row in cross_rows}
amap = {(row['sourceOrdinal'], row['locale']): row for row in additional_rows}
adjmap = {(row['sourceId'], row['locale']): row for row in adj_rows}
assert len(pmap) == len(cmap) == 600 and len(amap) == len(adjmap) == 14

source_path = REPO / 'src/NzbDrone.Core/Localization/Core/en.json'
source_raw = source_path.read_bytes()
source_en = json.loads(source_raw)
assert source_en[SOURCE_ID] == OLD_SOURCE
assert render_json(source_en) == source_raw
source_hash_path = REPO / 'docs/localization/source-message-hashes.json'
source_hash_raw = source_hash_path.read_bytes()
source_hashes = json.loads(source_hash_raw)
assert render_json(source_hashes) == source_hash_raw
source_messages = source_hashes['messages']
old_fingerprint = sha_text(SOURCE_ID + '\0' + OLD_SOURCE)
new_fingerprint = sha_text(SOURCE_ID + '\0' + NEW_SOURCE)
assert source_messages[SOURCE_ID] == old_fingerprint == '4458d0721df2c7e25ceeeb675c3db8220d6c16b58432ab7ed1d254164887c29e'
assert sha_text(OLD_SOURCE) == 'f00d6bc38ae8d8287c51f0dd680c3be77f307a21ff98f0fe4b37a78a573dcb9d'
assert sha_text(NEW_SOURCE) == 'a49f6f46ac43b970cc69960dbd472ad87bd94245781ac3d2cb22f035cd1709ff'

registry_path = REPO / 'docs/localization/server-message-sources.json'
registry_raw = registry_path.read_bytes()
registry = json.loads(registry_raw)
assert render_json(registry) == registry_raw
record = next(row for row in registry['records'] if row['id'] == SOURCE_ID)
assert record['source'] == OLD_SOURCE and record['sourceFingerprint'] == old_fingerprint
assert record['patterns'] == [OLD_SOURCE] and record['sourceTemplates'] == [OLD_SOURCE]
runtime_path = REPO / 'frontend/src/Utilities/Localization/server-messages.json'
runtime_raw = runtime_path.read_bytes()
runtime = json.loads(runtime_raw)
assert render_json(runtime) == runtime_raw
runtime_record = next(row for row in runtime if row['id'] == SOURCE_ID)
assert runtime_record['source'] == OLD_SOURCE and runtime_record['patterns'] == [OLD_SOURCE]
followup_path = REPO / 'docs/localization/source-followup-20261102.json'
followup_raw = followup_path.read_bytes()
followup = json.loads(followup_raw)
assert render_json(followup) == followup_raw
assert len(followup['entries']) == 2

caller_path = REPO / 'src/NzbDrone.Core/Download/Clients/QBittorrent/QBittorrentSettings.cs'
caller_bytes = caller_path.read_bytes()
caller_lines = caller_bytes.decode('utf-8').splitlines()
caller_file_hash = sha_bytes(caller_bytes)
caller_rows = []
for line_number in (27, 29, 31, 33):
    line_text = caller_lines[line_number - 1].strip()
    assert NEW_SOURCE in line_text, (line_number, line_text)
    caller_rows.append({'line': line_number, 'lineText': line_text, 'lineSha256': sha_text(line_text)})

final_rows = []
locale_files = {}
for cell, primary in pmap.items():
    assert cell in cmap
    cross = cmap[cell]
    ordinal, locale = cell
    assert primary['sourceOrdinal'] == cross['sourceOrdinal']
    assert primary['sourceId'] == cross['sourceId']
    assert primary['sourceTextSha256'] == cross['sourceTextSha256']
    assert cross['exactHead'] == EXPECTED_HEAD and cross['exactTree'] == EXPECTED_TREE
    assert primary['currentTarget'] == cross['currentTarget']
    assert primary['currentTargetSha256'] == cross['currentTargetSha256'] == sha_text(cross['currentTarget'])
    target_file = cross['targetFile']
    locale_files[locale] = target_file
    disposition = cross['crossReviewDisposition']
    adjudication = None
    if disposition == 'retain-hold':
        assert primary['disposition'] == 'hold'
        final_target = cross['currentTarget']
    elif disposition in ('accept-primary-correction', 'accept-primary-refinement'):
        assert primary['disposition'] in ('propose-correction', 'propose-refinement')
        final_target = cross['crossReviewFinalTarget']
        assert final_target == primary['finalTarget']
        assert sha_text(final_target) == cross['crossReviewFinalTargetSha256']
    elif disposition == 'accept-current':
        assert primary['disposition'] == 'accept-current'
        final_target = cross['currentTarget']
    elif disposition == 'propose-additional-correction':
        assert primary['disposition'] == 'accept-current'
        adjudication = adjmap[(cross['sourceId'], locale)]
        assert adjudication['adjudication'] == 'accept'
        assert adjudication['exactHead'] == EXPECTED_HEAD and adjudication['exactTree'] == EXPECTED_TREE
        assert adjudication['currentTarget'] == cross['currentTarget']
        assert adjudication['currentTargetSha256'] == cross['currentTargetSha256']
        assert adjudication['sourceTextSha256'] == cross['sourceTextSha256']
        assert adjudication['currentCatalogValueVerified'] is True
        assert adjudication['sourceCatalogValueVerified'] is True
        assert adjudication['callerContextHashVerified'] is True
        assert adjudication['placeholderParity'] == adjudication['markupParity'] == adjudication['protectedLiteralParity'] == 'exact'
        final_target = adjudication['adjudicatedTarget']
        assert sha_text(final_target) == adjudication['adjudicatedTargetSha256']
    else:
        raise AssertionError((cell, disposition))
    if disposition != 'retain-hold':
        assert cross['crossReviewFinalPlaceholders'] == cross['sourcePlaceholders']
        assert cross['crossReviewFinalMarkup'] == cross['sourceMarkup']
    assert cross['protectedLiteralsPreserved'] is True
    final_rows.append({
        'sourceOrdinal': ordinal,
        'sourceId': cross['sourceId'],
        'locale': locale,
        'localeFile': target_file,
        'source': cross['source'],
        'sourceTextSha256': cross['sourceTextSha256'],
        'callerContextSha256': cross['callerContextSha256'],
        'currentTarget': cross['currentTarget'],
        'currentTargetHash': cross['currentTargetSha256'],
        'primaryDisposition': primary['disposition'],
        'primaryTarget': primary['finalTarget'],
        'crossReviewDisposition': disposition,
        'crossReviewTarget': cross.get('crossReviewFinalTarget'),
        'thirdPartyAdjudication': adjudication['adjudication'] if adjudication else None,
        'thirdPartyTarget': adjudication['adjudicatedTarget'] if adjudication else None,
        'finalTarget': final_target,
        'finalTargetHash': sha_text(final_target),
        'changed': final_target != cross['currentTarget'],
    })

assert len(final_rows) == 600
assert collections.Counter(row['crossReviewDisposition'] for row in final_rows) == collections.Counter(cross_summary['crossReviewDispositionCounts'])
assert sum(row['changed'] for row in final_rows) == 93
held = [row for row in final_rows if row['crossReviewDisposition'] == 'retain-hold']
assert len(held) == 12 and {row['sourceOrdinal'] for row in held} == {884}
assert {row['sourceId'] for row in held} == {SOURCE_ID}

catalogs = {}
preapply_catalogs = []
for locale, rel in sorted(locale_files.items()):
    path = REPO / rel
    raw = path.read_bytes()
    data = json.loads(raw)
    assert render_json(data) == raw, rel
    assert len(data) == 4165
    catalogs[rel] = {'path': path, 'raw': raw, 'data': data}
    keys = list(data.keys())
    preapply_catalogs.append({'locale': locale, 'file': rel, 'sha256': sha_bytes(raw), 'keyCount': len(keys), 'orderedKeySetSha256': ordered_key_hash(keys)})
key_sets = [set(entry['data'].keys()) for entry in catalogs.values()]
assert all(keys == key_sets[0] for keys in key_sets)
for row in final_rows:
    data = catalogs[row['localeFile']]['data']
    assert data[row['sourceId']] == row['currentTarget']
    assert sha_text(data[row['sourceId']]) == row['currentTargetHash']
    if row['changed']:
        data[row['sourceId']] = row['finalTarget']

# Prepare metadata edits in memory and enforce exact-source consistency before writing.
source_en[SOURCE_ID] = NEW_SOURCE
source_messages[SOURCE_ID] = new_fingerprint
record.update({'source': NEW_SOURCE, 'sourceFingerprint': new_fingerprint, 'patterns': [NEW_SOURCE], 'sourceTemplates': [NEW_SOURCE]})
runtime_record.update({'source': NEW_SOURCE, 'patterns': [NEW_SOURCE]})
new_source_hash_bytes = render_json(source_hashes)
new_source_hash_snapshot_hash = sha_bytes(new_source_hash_bytes)
followup['state'] = 'Exact-source corrections for three reviewed English typos; stable source IDs, locale keys, placeholders, and caller bindings are retained. The third correction aligns the qBittorrent category validation catalog with all four pinned callers; its 12 locale targets remain held for fresh review.'
followup['entries'].append({
    'sourceId': SOURCE_ID,
    'sourceFile': 'src/NzbDrone.Core/Localization/Core/en.json',
    'oldSourceText': OLD_SOURCE,
    'oldSourceTextSha256': sha_text(OLD_SOURCE),
    'newSourceText': NEW_SOURCE,
    'newSourceTextSha256': sha_text(NEW_SOURCE),
    'sourceFingerprintBefore': old_fingerprint,
    'sourceFingerprintAfter': new_fingerprint,
    'callerFile': 'src/NzbDrone.Core/Download/Clients/QBittorrent/QBittorrentSettings.cs',
    'callerFileSha256Before': caller_file_hash,
    'callerFileSha256After': caller_file_hash,
    'callerOccurrencesChanged': 0,
    'postEditCallerOccurrences': caller_rows,
    'translationHandling': 'W850 primary and independent cross-review held all twelve locale cells because the English catalog omitted the forbidden backslash. Corrected the English source to match the exact four existing validators under the stable ID; keep the twelve targets held until fresh exact-head review explicitly preserves backslash, //, and leading/trailing slash constraints.'
})
followup['sourceMessageHashSnapshot'] = 'docs/localization/source-message-hashes.json'
followup['sourceMessageHashSnapshotSha256'] = new_source_hash_snapshot_hash

metadata = {
    'sourceId': SOURCE_ID,
    'stableIdRetained': True,
    'oldSource': OLD_SOURCE,
    'newSource': NEW_SOURCE,
    'oldSourceTextSha256': sha_text(OLD_SOURCE),
    'newSourceTextSha256': sha_text(NEW_SOURCE),
    'oldSourceFingerprint': old_fingerprint,
    'newSourceFingerprint': new_fingerprint,
    'sourceMessageHashesSha256Before': sha_bytes(source_hash_raw),
    'sourceMessageHashesSha256After': new_source_hash_snapshot_hash,
    'callerFile': str(caller_path.relative_to(REPO)),
    'callerFileSha256BeforeAndAfter': caller_file_hash,
    'callers': caller_rows,
    'validationRule': r'^([^\\\/](\/?[^\\\/])*)?$',
    'semanticConclusion': 'The four validators reject backslash anywhere, reject //, and disallow a leading or trailing slash. The catalog source with empty quotes was wrong; source text now matches all four callers.',
    'heldLocaleCells': 12,
    'heldSourceOrdinal': 884,
    'heldSourceId': SOURCE_ID,
    'translationReviewState': 'held pending fresh exact-head review against the corrected source',
}

# Evidence destination and source-change inputs are validated before any repo writes.
source_targets = [source_path, source_hash_path, registry_path, runtime_path, followup_path]
assert all(path.exists() for path in source_targets)
assert len(locale_files) == 12

EVIDENCE.mkdir(parents=True)
shutil.copytree(PRIMARY, EVIDENCE / 'primary')
shutil.copytree(CROSS, EVIDENCE / 'cross-review')
shutil.copytree(ADJ, EVIDENCE / 'third-party-adjudication')
source_evidence = EVIDENCE / 'source-correction'
source_evidence.mkdir()
(source_evidence / 'source-correction-record.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True)+'\n', encoding='utf-8')
application = EVIDENCE / 'application'
application.mkdir()
shutil.copy2(Path(__file__), application / 'assemble_apply.py')
(application / 'source-metadata-before-after.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True)+'\n', encoding='utf-8')

for rel, item in catalogs.items():
    after = render_json(item['data'])
    if after != item['raw']:
        item['path'].write_bytes(after)
source_path.write_bytes(render_json(source_en))
source_hash_path.write_bytes(new_source_hash_bytes)
registry_path.write_bytes(render_json(registry))
runtime_path.write_bytes(render_json(runtime))
followup_path.write_bytes(render_json(followup))

readback = []
for row in final_rows:
    data = read_json(REPO / row['localeFile'])
    value = data[row['sourceId']]
    assert value == row['finalTarget'] and sha_text(value) == row['finalTargetHash']
    row['readbackTargetHash'] = sha_text(value)
    row['sourceTextAfterCorrection'] = NEW_SOURCE if row['sourceId'] == SOURCE_ID else None
    readback.append(row)
for rel, item in catalogs.items():
    raw = (REPO / rel).read_bytes(); data = json.loads(raw)
    assert render_json(data) == raw and len(data) == 4165 and set(data) == key_sets[0]
source_after = read_json(source_path)
hashes_after = read_json(source_hash_path)
registry_after = read_json(registry_path)
runtime_after = read_json(runtime_path)
followup_after = read_json(followup_path)
assert source_after[SOURCE_ID] == NEW_SOURCE
assert hashes_after['messages'][SOURCE_ID] == new_fingerprint
assert next(row for row in registry_after['records'] if row['id'] == SOURCE_ID)['source'] == NEW_SOURCE
assert next(row for row in runtime_after if row['id'] == SOURCE_ID)['source'] == NEW_SOURCE
assert followup_after['sourceMessageHashSnapshotSha256'] == sha_bytes(source_hash_path.read_bytes())

post_catalogs = []
for locale, rel in sorted(locale_files.items()):
    path = REPO / rel
    raw = path.read_bytes(); data = json.loads(raw); keys = list(data)
    post_catalogs.append({'locale': locale, 'file': rel, 'sha256': sha_bytes(raw), 'keyCount': len(keys), 'orderedKeySetSha256': ordered_key_hash(keys)})

application.joinpath('catalog-preapply-pins.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True)+'\n' for row in preapply_catalogs), encoding='utf-8')
application.joinpath('apply-plan.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True)+'\n' for row in final_rows), encoding='utf-8')
application.joinpath('apply-readback.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True)+'\n' for row in readback), encoding='utf-8')
application.joinpath('post-apply-catalog-attestation.json').write_text(json.dumps({'catalogs':post_catalogs,'allKeySetsEqual':True,'keyCount':4165},ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
counts = collections.Counter(row['crossReviewDisposition'] for row in final_rows)
summary = {
    'repository':'snapetech-org/ChaptarrNG','pullRequest':190,'state':'OPEN','draft':True,
    'exactInputHead':EXPECTED_HEAD,'exactInputTree':EXPECTED_TREE,
    'sourceOrdinals':[850,899],'sourceIds':50,'cells':600,
    'primaryCounts':{'accept-current':509,'propose-correction':69,'propose-refinement':10,'hold':12},
    'crossReviewCounts':dict(counts),'thirdPartyAdditionalCorrections':{'accepted':14,'revised':0,'holds':0},
    'finalChangedCatalogCells':sum(row['changed'] for row in final_rows),'heldCells':len(held),'heldSourceId':SOURCE_ID,
    'catalogs':post_catalogs,'allCatalogKeySetsEqual':True,'keyCount':4165,
    'callerReferences':74,'pipelineReferences':76,'placeholderMarkupProtectedLiteralFailures':0,
    'sourceCorrection':metadata,
    'browserReview':'blocked: no deployment exists for the exact input head; existing Agent VM tabs were left untouched',
    'nativeSpeakerApproval':False,'nativeSpeakerReviewOutstanding':True,
    'testsBuildsCiRun':False,'workflowFilesTouched':False,'mergeReleaseTag':False,
}
application.joinpath('apply-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
readme = f'''# ChaptarrNG PR #190 semantic review: W850–W899\n\nPrimary review covered 50 source messages × 12 locales (600 cells): 509 accepted existing values, 69 corrections, 10 refinements, and 12 held W884 cells. Independent cross-review accepted the 79 primary proposals, found 14 additional corrections, and retained the same 12 holds. A separate adjudication accepted all 14 additional corrections.\n\nApplication changed 93 locale targets. The 12 W884 targets remain held because the old English source omitted a backslash present in all four pinned validators. The English source was corrected under the existing stable ID; its runtime registry, source hashes, server-message inventory, and source-followup record were updated. The 12 locale targets will receive a fresh exact-head translation review against the corrected source.\n\nThe 12 target catalogs each retain the 4,165-key set and their existing order. Final placeholder, markup, protected-literal, and readback mismatches: zero for the approved targets. Review covered 74 caller references and 76 generic-pipeline references.\n\n`primary/`, `cross-review/`, and `third-party-adjudication/` preserve the full input packets and checksums. `source-correction/` records the stable-ID source correction and four caller pins. `application/` includes the exact apply plan, pre-apply pins, readback, source metadata readback, and catalog attestation.\n\nThis is static review only. The current PR head has no exact-SHA deployment, so headed-browser acceptance is blocked; existing Agent VM tabs were left untouched. Qualified native-speaker review is outstanding. No tests, builds, scans, CI runs, workflow edits, merges, releases, or tags were made.\n'''
(EVIDENCE / 'README.md').write_text(readme,encoding='utf-8')
manifest=EVIDENCE/'SHA256SUMS'
lines=[]
for path in sorted(p for p in EVIDENCE.rglob('*') if p.is_file() and p!=manifest):
    lines.append(f'{sha_bytes(path.read_bytes())}  {path.relative_to(EVIDENCE).as_posix()}')
manifest.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'evidence':str(EVIDENCE),'files':len(lines)+1,'summary':summary},ensure_ascii=False,indent=2))
