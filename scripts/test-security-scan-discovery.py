#!/usr/bin/env python3
"""Regression checks for scanner discovery failures, using a temporary PATH."""
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class DiscoveryTests(unittest.TestCase):
    def run_scan(self, rg=None):
        with tempfile.TemporaryDirectory() as directory:
            for tool in ("bash", "git", "dirname"):
                os.symlink(shutil.which(tool), pathlib.Path(directory, tool))
            if rg is not None:
                executable = pathlib.Path(directory, "rg")
                executable.write_text("#!/bin/bash\nexit " + str(rg) + "\n")
                executable.chmod(0o755)
            env = dict(os.environ, PATH=directory, SEMGREP_USE_GENERIC="1")
            return subprocess.run(["/bin/bash", "scripts/security-scan-local.sh", "--trivy-only", "--ci"],
                                  cwd=ROOT, env=env, text=True, capture_output=True)

    def test_missing_ripgrep_fails(self):
        self.assertEqual(self.run_scan().returncode, 127)

    def test_discovery_io_failure_is_not_an_empty_scan(self):
        self.assertEqual(self.run_scan(2).returncode, 2)

    def test_empty_ci_scan_fails(self):
        self.assertEqual(self.run_scan(1).returncode, 1)

if __name__ == "__main__":
    unittest.main()
