#!/usr/bin/env python3
"""Negative-path coverage for the audit's policy and custom-platform lock gates."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


suppression = module("suppression", "scripts/check-scan-suppressions.py")
locks = module("locks", "packaging/scripts/verify-platform-locks.py")


class AuditPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.base = self.root / "base"
        self.source = self.root / "source"
        self.base.mkdir()
        self.source.mkdir()

    def test_unchanged_reviewed_annotation_is_accepted(self):
        for folder in (self.base, self.source):
            (folder / "safe.py").write_text("# nosemgrep: reviewed-rule\nsafe_call()\n")
        suppression.check(self.base, self.source)

    def test_new_annotation_is_rejected(self):
        (self.source / "unsafe.py").write_text("# nosemgrep: rule\nunsafe_call()\n")
        with self.assertRaisesRegex(ValueError, "New or changed"):
            suppression.check(self.base, self.source)

    def test_changed_code_beneath_reviewed_annotation_is_rejected(self):
        (self.base / "code.py").write_text("# nosemgrep: rule\nsafe_call()\n")
        (self.source / "code.py").write_text("# nosemgrep: rule\nunsafe_call()\n")
        with self.assertRaisesRegex(ValueError, "New or changed"):
            suppression.check(self.base, self.source)

    def test_new_ignore_file_is_rejected(self):
        (self.source / ".semgrepignore").write_text("**/*\n")
        with self.assertRaisesRegex(ValueError, "ignore policy"):
            suppression.check(self.base, self.source)

    def test_symlink_is_rejected_without_following_it(self):
        (self.source / "escape").symlink_to(self.base, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symbolic links"):
            suppression.check(self.base, self.source)

    def dependency(self, version="1.0.0", digest="reviewed-hash"):
        return {"dependencies": {"net10.0": {"Example": {"type": "Direct", "resolved": version, "contentHash": digest}}}}

    def lock_fixture(self):
        (self.base / "Example.csproj").write_text("<Project />")
        (self.base / "packages.lock.json").write_text(json.dumps(self.dependency()))
        path = self.source / "Example.lock.json"
        path.write_text(json.dumps(self.dependency()))
        return path

    def test_identical_package_version_and_hash_are_accepted(self):
        self.lock_fixture()
        locks.verify(self.base, self.source)

    def test_changed_package_version_is_rejected(self):
        path = self.lock_fixture()
        path.write_text(json.dumps(self.dependency(version="2.0.0")))
        with self.assertRaisesRegex(ValueError, "Unlocked"):
            locks.verify(self.base, self.source)

    def test_changed_package_hash_is_rejected(self):
        path = self.lock_fixture()
        path.write_text(json.dumps(self.dependency(digest="modified")))
        with self.assertRaisesRegex(ValueError, "Unlocked"):
            locks.verify(self.base, self.source)

    def test_missing_custom_lock_output_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "no lockfiles"):
            locks.verify(self.base, self.source)


if __name__ == "__main__":
    unittest.main()
