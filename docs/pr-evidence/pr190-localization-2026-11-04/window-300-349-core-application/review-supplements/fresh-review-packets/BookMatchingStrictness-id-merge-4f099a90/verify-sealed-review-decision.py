#!/usr/bin/env python3
"""Verify the sealed decision against this packet's pinned input and its canonical SHA-256 seal."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
read = lambda name: (root / name).read_bytes()
load = lambda name: json.loads(read(name).decode("utf-8"))
sha = lambda data: hashlib.sha256(data).hexdigest()
canonical = lambda obj: json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).replace("\n", "").encode("utf-8")

packet = load("fresh-review-input.json")
decision = load("sealed-review-decision.json")
seal = decision["seal"]
payload = {key: value for key, value in decision.items() if key != "seal"}
assert sha(canonical(payload)) == seal["sha256"], "decision seal mismatch"
binding = decision["binding"]
assert binding["inputJsonSha256"] == sha(read("fresh-review-input.json")), "input checksum mismatch"
assert binding["readmeSha256"] == sha(read("README.md")), "README checksum mismatch"
assert binding["head"] == packet["repositoryPin"]["head"]
assert binding["tree"] == packet["repositoryPin"]["tree"]
assert binding["source"]["textSha256"] == packet["source"]["textSha256"]
assert binding["target"]["textSha256"] == packet["currentTarget"]["textSha256"]
context = packet["callerContext"]
context_payload = {
    "sourceKey": packet["reviewCell"]["sourceKey"],
    "literalAndIndirectReferences": context["literalAndIndirectReferences"],
    "relatedDynamicTranslationCallsites": context["relatedDynamicTranslationCallsites"],
}
context_hash = sha(canonical(context_payload))
assert binding["currentCallerContextSha256"] == context_hash
assert context_hash == packet["priorAndCurrentContext"]["currentContextSha256"]
assert decision["decision"] == "ACCEPT" and decision["correctionRequired"] is False
assert decision["nativeSpeakerSignoff"] is False
print("sealed decision verified")
