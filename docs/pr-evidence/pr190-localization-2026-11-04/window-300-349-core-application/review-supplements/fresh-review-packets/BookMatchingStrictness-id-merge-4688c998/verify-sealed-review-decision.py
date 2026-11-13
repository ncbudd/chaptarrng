#!/usr/bin/env python3
"""Verify the sealed translation decision and its binding to this packet."""

import hashlib
import json
from pathlib import Path


PACKET = Path(__file__).resolve().parent
DECISION_PATH = PACKET / "sealed-review-decision.json"
INPUT_PATH = PACKET / "fresh-review-input.json"


def canonical_bytes(value):
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).replace("\n", "").encode("utf-8")


def sha256_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def require(condition, message):
    if not condition:
        raise SystemExit(f"FAIL: {message}")


try:
    decision = json.loads(DECISION_PATH.read_text(encoding="utf-8"))
    packet = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    raise SystemExit(f"FAIL: cannot load packet JSON: {exc}") from exc

seal = decision.get("seal")
require(isinstance(seal, dict), "decision has no seal object")
require(seal.get("algorithm") == "SHA-256", "unsupported seal algorithm")
require(
    seal.get("canonicalization")
    == "UTF-8 compact JSON, sorted keys, ensure_ascii=false, no trailing newline; omit the top-level seal field.",
    "unexpected seal canonicalization description",
)
unsigned_decision = dict(decision)
unsigned_decision.pop("seal", None)
actual_seal = hashlib.sha256(canonical_bytes(unsigned_decision)).hexdigest()
require(actual_seal == seal.get("sha256"), "canonical decision seal mismatch")

cell = decision["reviewCell"]
pins = decision["pins"]
hashes = decision["hashes"]
source = packet["source"]
target = packet["currentTarget"]
repo_pin = packet["repositoryPin"]
context = packet["callerContext"]
prior_current = packet["priorAndCurrentContext"]

require(cell["sourceKey"] == packet["reviewCell"]["sourceKey"], "source key mismatch")
require(cell["locale"] == packet["reviewCell"]["locale"], "locale mismatch")
require(cell["cellId"] == packet["reviewCell"]["cellId"], "cell ID mismatch")
require(cell["sourceText"] == source["text"], "source text mismatch")
require(cell["targetText"] == target["text"], "target text mismatch")
require(sha256_text(source["text"]) == hashes["sourceTextSha256"] == source["textSha256"], "source text hash mismatch")
require(sha256_text(target["text"]) == hashes["targetTextSha256"] == target["textSha256"], "target text hash mismatch")

context_obj = {
    "sourceKey": packet["reviewCell"]["sourceKey"],
    "literalAndIndirectReferences": context["literalAndIndirectReferences"],
    "relatedDynamicTranslationCallsites": context["relatedDynamicTranslationCallsites"],
}
context_hash = hashlib.sha256(canonical_bytes(context_obj)).hexdigest()
require(context_hash == hashes["currentContextSha256"] == context["callerContextSha256"], "current context hash mismatch")
require(hashes["priorContextSha256"] == prior_current["priorContextSha256"], "prior context hash mismatch")
require(pins["head"] == repo_pin["head"], "head pin mismatch")
require(pins["tree"] == repo_pin["tree"], "tree pin mismatch")
require(pins["previousMain"] == repo_pin["previousMain"], "previous main pin mismatch")
require(pins["currentMain"] == repo_pin["currentMain"], "current main pin mismatch")
require(pins["sourcePath"] == repo_pin["sourcePath"], "source path mismatch")
require(pins["sourceBlob"] == repo_pin["sourceBlob"], "source blob mismatch")
require(pins["sourceCatalogSha256"] == repo_pin["sourceCatalogSha256"], "source catalog hash mismatch")
require(pins["targetPath"] == repo_pin["targetPath"], "target path mismatch")
require(pins["targetBlob"] == repo_pin["targetBlob"], "target blob mismatch")
require(pins["targetCatalogSha256"] == repo_pin["targetCatalogSha256"], "target catalog hash mismatch")

print(f"PASS: canonical decision seal {actual_seal}")
print("PASS: source, target, caller-context, and repository pins match fresh-review-input.json")
