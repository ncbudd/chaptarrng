#!/usr/bin/env python3
"""Verify the sealed root-suggestion translation review packet."""
from pathlib import Path
import argparse
import collections
import hashlib
import json
import re
import sys

DEFAULT_PROPOSALS = Path('/home/keith/Documents/code/task-scratch/chaptarrng-pr190-w300-349-root-hold-suggestions-20261104/root-hold-proposals.jsonl')
DEFAULT_INPUT = Path('/home/keith/Documents/code/task-scratch/chaptarrng-pr190-w300-349-core-20261104/candidate-free/input')
PLACEHOLDER = re.compile(r'\{\d+\}')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def jsonl(path):
    return [json.loads(line) for line in path.read_bytes().splitlines()]

def fail(message):
    raise SystemExit('FAIL: ' + message)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--packet', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--proposals', type=Path, default=DEFAULT_PROPOSALS)
    parser.add_argument('--candidate-free-input', type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()
    packet = args.packet.resolve()
    input_dir = args.candidate_free_input.resolve()
    proposals_path = args.proposals.resolve()
    names = ['candidate-free-manifest.json', 'SHA256SUMS.txt', 'candidate-free-cells.jsonl', 'caller-context.jsonl']
    raw = {name: (input_dir / name).read_bytes() for name in names}
    manifest = json.loads(raw['candidate-free-manifest.json'])
    sums = {}
    for line in raw['SHA256SUMS.txt'].decode('utf-8').splitlines():
        if line.strip():
            digest, name = line.split(None, 1)
            sums[name.strip()] = digest
    expected_manifest = manifest
    if sha(raw['candidate-free-cells.jsonl']) != expected_manifest['candidateFreeCells']['sha256']:
        fail('candidate-free cells do not match candidate manifest')
    if sha(raw['caller-context.jsonl']) != expected_manifest['callerContext']['sha256']:
        fail('caller context does not match candidate manifest')
    for name in ['candidate-free-manifest.json', 'candidate-free-cells.jsonl', 'caller-context.jsonl']:
        if sums.get(name) != sha(raw[name]):
            fail(f'candidate input checksum mismatch: {name}')

    proposals_raw = proposals_path.read_bytes()
    proposals = jsonl(proposals_path)
    results_path = packet / 'review-results.jsonl'
    results_raw = results_path.read_bytes()
    results = jsonl(results_path)
    packet_manifest_raw = (packet / 'manifest.json').read_bytes()
    packet_manifest = json.loads(packet_manifest_raw)

    sums_file = packet / 'SHA256SUMS.txt'
    output_sums = {}
    for line in sums_file.read_text(encoding='utf-8').splitlines():
        if line.strip():
            digest, name = line.split(None, 1)
            name = name.strip()
            if Path(name).name != name:
                fail(f'non-local path in packet checksums: {name}')
            output_sums[name] = digest
    for name, digest in output_sums.items():
        if sha((packet / name).read_bytes()) != digest:
            fail(f'packet checksum mismatch: {name}')
    if packet_manifest['outputs']['reviewResultsSha256'] != sha(results_raw):
        fail('manifest review-results hash mismatch')
    if packet_manifest['outputs']['verifierSha256'] != sha((packet / 'verify-review-packet.py').read_bytes()):
        fail('manifest verifier hash mismatch')
    if packet_manifest['inputs']['rootHoldProposals']['sha256'] != sha(proposals_raw):
        fail('proposal input hash differs from sealed manifest')
    for name in names:
        if packet_manifest['inputs']['candidateFreeInput'][name] != sha(raw[name]):
            fail(f'candidate input differs from sealed manifest: {name}')

    raw_cell_lines = raw['candidate-free-cells.jsonl'].splitlines()
    cells = [json.loads(line) for line in raw_cell_lines]
    by_id = {f"{row['sourceKey']}::{row['locale']}": (line, row) for line, row in zip(raw_cell_lines, cells)}
    contexts = jsonl(input_dir / 'caller-context.jsonl')
    context_by_key = {row['sourceKey']: row for row in contexts}
    prop_by_id = {p['cellId']: (line, p) for line, p in zip(proposals_raw.splitlines(), proposals)}
    result_by_id = {r['cellId']: r for r in results}
    if len(proposals) != 19 or len(results) != 19 or len(result_by_id) != 19:
        fail('expected exactly 19 unique cells')
    if set(prop_by_id) != set(result_by_id):
        fail('proposal and result cell sets differ')

    for cid, (prop_line, prop) in prop_by_id.items():
        result = result_by_id[cid]
        if cid not in by_id:
            fail(f'candidate-free row missing: {cid}')
        row_line, row = by_id[cid]
        ctx = context_by_key.get(prop['sourceKey'])
        if ctx is None:
            fail(f'caller context missing: {prop["sourceKey"]}')
        checks = [
            (prop['candidateFreeRowSha256'] == sha(row_line), 'candidate row hash'),
            (prop['sourceText'] == row['sourceText'] and prop['sourceTextSha256'] == sha(row['sourceText'].encode()), 'source text/hash'),
            (prop['currentTarget'] == row['currentTarget'] and prop['currentTargetSha256'] == sha(row['currentTarget'].encode()), 'current target/hash'),
            (prop['callerContextSha256'] == row['callerContextSha256'] == ctx['callerContextSha256'], 'caller context hash'),
            (prop['callerReferenceCount'] == row['callerReferenceCount'] == ctx['callerReferenceCount'], 'caller reference count'),
            (result['integrity']['proposalRowSha256'] == sha(prop_line), 'proposal row hash in result'),
            (result['proposedTarget'] == prop['proposedTarget'] and result['proposedTargetSha256'] == sha(prop['proposedTarget'].encode()), 'proposed target/hash'),
        ]
        for ok, label in checks:
            if not ok:
                fail(f'{label} mismatch for {cid}')
        if not all(row['integrityChecks'].values()):
            fail(f'candidate row internal checks fail for {cid}')
        src_ph = collections.Counter(PLACEHOLDER.findall(row['sourceText']))
        for text in [row['currentTarget'], prop['proposedTarget']]:
            if collections.Counter(PLACEHOLDER.findall(text)) != src_ph:
                fail(f'placeholder mismatch for {cid}')
        if result['decision'] == 'accept':
            if result['finalTarget'] != prop['proposedTarget']:
                fail(f'accepted target differs from proposal for {cid}')
        elif result['decision'] == 'revise':
            if not result['finalTarget'] or result['finalTarget'] == prop['proposedTarget']:
                fail(f'revision target missing or unchanged for {cid}')
        elif result['decision'] == 'hold':
            if result['finalTarget'] is not None:
                fail(f'held target must be null for {cid}')
        else:
            fail(f'unknown decision for {cid}')
        final = result['finalTarget']
        if final is not None:
            if collections.Counter(PLACEHOLDER.findall(final)) != src_ph:
                fail(f'final target placeholder mismatch for {cid}')
            if result['finalTargetSha256'] != sha(final.encode('utf-8')):
                fail(f'final target hash mismatch for {cid}')

    actual_counts = collections.Counter(r['decision'] for r in results)
    if dict(actual_counts) != packet_manifest['review']['decisionCounts']:
        fail('review decision counts differ from manifest')
    print(f"OK: {len(results)} cells; {dict(actual_counts)}; packet and input hashes verified")

if __name__ == '__main__':
    main()
