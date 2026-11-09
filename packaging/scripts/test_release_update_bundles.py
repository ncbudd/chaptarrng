import importlib.util
from pathlib import Path
import tempfile
import unittest


spec = importlib.util.spec_from_file_location("release_bundles", Path(__file__).with_name("verify-release-update-bundles.py"))
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class ReleaseBundleTests(unittest.TestCase):
    source = "a" * 40
    digest = "b" * 64
    filename = "ChaptarrNG-1.2.3-linux-x64.tar.gz"

    def verified(self, **changes):
        statement = {
            "predicateType": gate.PREDICATE,
            "predicate": {"version": "1.2.3", "sourceCommit": self.source},
            "subject": [{"name": self.filename, "digest": {"sha256": self.digest}}],
        }
        statement.update(changes)
        return [{"verificationResult": {"statement": statement}}]

    def matches(self, verified):
        return gate.matches_release(verified, "1.2.3", self.source, self.filename, self.digest)

    def test_matching_signed_statement_is_accepted(self):
        self.assertTrue(self.matches(self.verified()))

    def test_other_release_version_is_rejected(self):
        self.assertFalse(self.matches(self.verified(predicate={"version": "1.2.2", "sourceCommit": self.source})))

    def test_other_source_revision_is_rejected(self):
        self.assertFalse(self.matches(self.verified(predicate={"version": "1.2.3", "sourceCommit": "c" * 40})))

    def test_name_and_digest_in_different_subjects_are_rejected(self):
        self.assertFalse(self.matches(self.verified(subject=[
            {"name": self.filename, "digest": {"sha256": "c" * 64}},
            {"name": "different.tar.gz", "digest": {"sha256": self.digest}},
        ])))

    def test_missing_digest_or_predicate_is_rejected(self):
        self.assertFalse(self.matches(self.verified(subject=[{"name": self.filename}])))
        self.assertFalse(self.matches(self.verified(predicate={})))
        self.assertFalse(self.matches(self.verified(predicateType="different")))

    def test_missing_bundle_is_rejected_before_running_verifier(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "Missing archive"):
                gate.verify(Path(directory), "1.2.3", self.source, ["linux-x64"])


if __name__ == "__main__":
    unittest.main()
