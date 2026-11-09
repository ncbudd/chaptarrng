#!/usr/bin/env python3
"""Exercise the PostgreSQL acceptance gate with missing and skipped evidence."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from defusedxml.common import DefusedXmlException


spec = importlib.util.spec_from_file_location("postgres_results", Path(__file__).with_name("verify-postgres-test-results.py"))
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class PostgresEvidenceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "results.trx"

    def report(self, fixtures=None, outcome="Passed", counter_offset=0):
        if fixtures is None:
            fixtures = sorted(gate.REQUIRED_FIXTURES)
        root = ET.Element("TestRun", xmlns=gate.NS["t"])
        results = ET.SubElement(root, "Results")
        definitions = ET.SubElement(root, "TestDefinitions")
        for index, fixture in enumerate(fixtures):
            test_id = str(index)
            ET.SubElement(results, "UnitTestResult", testId=test_id, testName=fixture, outcome=outcome)
            definition = ET.SubElement(definitions, "UnitTest", id=test_id)
            ET.SubElement(definition, "TestMethod", className="Chaptarr.Core.Test." + fixture)
        summary = ET.SubElement(root, "ResultSummary", outcome="Completed")
        count = str(len(fixtures) + counter_offset)
        ET.SubElement(summary, "Counters", total=count, executed=count, passed=count)
        ET.ElementTree(root).write(self.path, encoding="utf-8", xml_declaration=True)

    def test_complete_success_is_accepted(self):
        self.report()
        gate.verify(self.path)

    def test_empty_run_is_rejected(self):
        self.report([])
        with self.assertRaisesRegex(ValueError, "no tests"):
            gate.verify(self.path)

    def test_skipped_or_failed_fixture_is_rejected(self):
        for outcome in ("NotExecuted", "Failed", "Inconclusive"):
            with self.subTest(outcome=outcome):
                self.report(outcome=outcome)
                with self.assertRaisesRegex(ValueError, "must not fail or skip"):
                    gate.verify(self.path)

    def test_omitted_fixture_is_rejected(self):
        for fixture in gate.REQUIRED_FIXTURES:
            with self.subTest(fixture=fixture):
                self.report(sorted(gate.REQUIRED_FIXTURES - {fixture}))
                with self.assertRaisesRegex(ValueError, "omitted required fixtures"):
                    gate.verify(self.path)

    def test_inconsistent_counters_are_rejected(self):
        self.report(counter_offset=1)
        with self.assertRaisesRegex(ValueError, "counters"):
            gate.verify(self.path)

    def test_result_without_definition_is_rejected(self):
        self.report()
        document = gate.ET.parse(self.path, forbid_dtd=True)
        definitions = document.getroot().find("t:TestDefinitions", gate.NS)
        definitions.remove(definitions[0])
        document.write(self.path)
        with self.assertRaisesRegex(ValueError, "Missing test definition"):
            gate.verify(self.path)

    def test_dtd_and_entity_documents_are_rejected(self):
        self.path.write_text('<!DOCTYPE TestRun [<!ENTITY content SYSTEM "file:///etc/passwd">]><TestRun>&content;</TestRun>')
        with self.assertRaises(DefusedXmlException):
            gate.verify(self.path)

    def test_failed_summary_is_rejected_even_when_individual_results_pass(self):
        self.report()
        document = gate.ET.parse(self.path, forbid_dtd=True)
        document.getroot().find("t:ResultSummary", gate.NS).set("outcome", "Failed")
        document.write(self.path)
        with self.assertRaisesRegex(ValueError, "did not complete successfully"):
            gate.verify(self.path)


if __name__ == "__main__":
    unittest.main()
