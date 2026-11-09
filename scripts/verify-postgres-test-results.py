#!/usr/bin/env python3
"""Reject empty, skipped or incomplete PostgreSQL acceptance test runs."""
import argparse
from pathlib import Path
from defusedxml import ElementTree as ET


REQUIRED_FIXTURES = {
    "BookshelfPostgresDatabaseConverterFixture",
    "BookshelfPostgresExternalBackupFixture",
    "BookshelfPostgresDatabaseSelectionFixture",
    "PostgresDatabaseInspectorFixture",
    "BookshelfQualityProfilePostgresServiceFixture",
    "PostgresDatabaseAtomicOperationFixture",
}
NS = {"t": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}


def verify(path):
    if Path(path).stat().st_size > 64 * 1024 * 1024:
        raise ValueError("PostgreSQL test evidence exceeds its 64 MiB limit")
    root = ET.parse(path, forbid_dtd=True).getroot()
    results = root.findall("t:Results/t:UnitTestResult", NS)
    definitions = {test.attrib["id"]: test for test in root.findall("t:TestDefinitions/t:UnitTest", NS)}
    if not results:
        raise ValueError("PostgreSQL acceptance discovered no tests")
    failures = [result.get("testName", "unknown") for result in results if result.get("outcome") != "Passed"]
    if failures:
        raise ValueError("PostgreSQL acceptance must not fail or skip tests: " + ", ".join(failures))
    fixtures = set()
    for result in results:
        definition = definitions.get(result.get("testId"))
        method = None if definition is None else definition.find("t:TestMethod", NS)
        if method is None:
            raise ValueError("Missing test definition for " + result.get("testName", "unknown"))
        fixtures.add(method.attrib["className"].split(",")[0].rsplit(".", 1)[-1])
    missing = REQUIRED_FIXTURES - fixtures
    if missing:
        raise ValueError("PostgreSQL acceptance omitted required fixtures: " + ", ".join(sorted(missing)))
    counters = root.find("t:ResultSummary/t:Counters", NS)
    summary = root.find("t:ResultSummary", NS)
    if summary is None or summary.get("outcome") not in ("Completed", "Passed"):
        raise ValueError("PostgreSQL acceptance did not complete successfully")
    if counters is None or any(int(counters.get(key, "-1")) != len(results) for key in ("total", "executed", "passed")):
        raise ValueError("PostgreSQL acceptance counters do not match successful executed tests")
    print(f"PostgreSQL acceptance: {len(results)} passed; no skipped tests; all {len(REQUIRED_FIXTURES)} required live fixtures executed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    args = parser.parse_args()
    verify(args.results)
