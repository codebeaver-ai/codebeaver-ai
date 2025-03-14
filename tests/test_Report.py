import xml.etree.ElementTree as ET

import pytest

from src.codebeaver.Report import Report


# Fake End2endTest class for testing purposes.
class FakeEnd2endTest:
    def __init__(self, name, passed, errored, comment, steps):
        self.name = name
        self.passed = passed
        self.errored = errored
        self.comment = comment
        self.steps = steps


class TestReport:
    """Tests for the Report class methods."""

    def test_generate_xml_report_all_pass(self):
        """Test generating XML report when all tests pass (no failures or errors)."""
        report = Report()
        test1 = FakeEnd2endTest("Test1", True, False, "", ["step1", "step2"])
        test2 = FakeEnd2endTest("Test2", True, False, "", ["stepA"])
        report.add_e2e_results([test1, test2])

        xml = report.generate_xml_report()
        # Check header and testsuite attributes
        assert '<?xml version="1.0" encoding="UTF-8"?>' in xml
        assert 'tests="2"' in xml
        # There should be no <failure> or <error> tags
        assert "<failure" not in xml
        assert "<error" not in xml
        # The system-out should contain the steps text
        assert "step1" in xml and "step2" in xml and "stepA" in xml

    def test_generate_xml_report_failure(self):
        """Test generating XML report for a failing test (failure but not error)."""
        report = Report()
        test_fail = FakeEnd2endTest(
            "FailTest", False, False, "Assertion failed", ["step1"]
        )
        report.add_e2e_results([test_fail])

        xml = report.generate_xml_report()
        # Check that failure tag is present with the correct message type and comment
        assert '<failure message="Test failed" type="Failure">' in xml
        assert "Assertion failed" in xml

    def test_generate_xml_report_error(self):
        """Test generating XML report for a test that encountered an error."""
        report = Report()
        test_error = FakeEnd2endTest(
            "ErrorTest", False, True, "Unexpected error", ["init", "run"]
        )
        report.add_e2e_results([test_error])

        xml = report.generate_xml_report()
        # Check that error tag is present with the correct message type and comment
        assert '<error message="Test execution error" type="Error">' in xml
        assert "Unexpected error" in xml

    def test_generate_xml_report_mixed(self):
        """Test generating XML report with a mix of passed, failed, and errored tests."""
        report = Report()
        test_pass = FakeEnd2endTest("PassTest", True, False, "", ["pass_step"])
        test_fail = FakeEnd2endTest(
            "FailTest", False, False, "Failure occurred", ["fail_step"]
        )
        test_error = FakeEnd2endTest(
            "ErrorTest", False, True, "Error occurred", ["error_step"]
        )
        report.add_e2e_results([test_pass, test_fail, test_error])

        xml = report.generate_xml_report()
        # Ensure the testsuite element shows the correct counts for tests, failures, and errors.
        assert 'tests="3"' in xml
        assert 'failures="1"' in xml
        assert 'errors="1"' in xml

    def test_not_implemented_html_report(self):
        """Test that calling generate_html_report raises NotImplementedError."""
        report = Report()
        with pytest.raises(NotImplementedError):
            report.generate_html_report()

    def test_not_implemented_json_report(self):
        """Test that calling generate_json_report raises NotImplementedError."""
        report = Report()
        with pytest.raises(NotImplementedError):
            report.generate_json_report()

    def test_generate_xml_report_empty(self):
        """Test generating XML report when there are no tests added (empty report)."""
        report = Report()
        xml = report.generate_xml_report()
        # The testsuite should report tests, failures, and errors as zero and no <testcase> entries.
        assert 'tests="0"' in xml
        assert 'failures="0"' in xml
        assert 'errors="0"' in xml
        assert "<testcase" not in xml

    def test_multiple_add_e2e_results(self):
        """Test that adding batches of E2E results accumulates the tests correctly."""
        report = Report()
        test1 = FakeEnd2endTest("BatchTest1", True, False, "", ["step1"])
        report.add_e2e_results([test1])
        # The initial report should include one test.
        assert 'tests="1"' in report.generate_xml_report()
        test2 = FakeEnd2endTest(
            "BatchTest2", False, False, "Failure in batch", ["step2"]
        )
        test3 = FakeEnd2endTest("BatchTest3", False, True, "Error in batch", ["step3"])
        report.add_e2e_results([test2, test3])
        xml = report.generate_xml_report()
        # Now the totals should reflect three tests, one failure, and one error.
        assert 'tests="3"' in xml
        assert 'failures="1"' in xml
        assert 'errors="1"' in xml

    def test_generate_xml_report_multiline_steps(self):
        """Test XML report generation when test steps include multiple lines and special characters."""
        # Steps include newline-splittable content and characters that look like XML tags.
        steps = ["First step", "Second step with <tag>", "Third step with & symbol"]
        test_multi = FakeEnd2endTest("MultiStepTest", True, False, "", steps)
        report = Report()
        report.add_e2e_results([test_multi])
        xml = report.generate_xml_report()
        # The system-out block should include the steps joined with newlines.
        expected_steps_text = "\n".join(steps)
        assert expected_steps_text in xml
        # Ensure the test name and classname appear correctly.
        assert 'name="MultiStepTest"' in xml

    def test_generate_xml_report_empty_steps(self):
        """Test generating XML report for a test with an empty steps list.
        Ensures that an empty steps list yields an empty <system-out> tag in the XML."""
        report = Report()
        test_empty = FakeEnd2endTest("EmptyStepsTest", True, False, "No steps", [])
        report.add_e2e_results([test_empty])
        xml = report.generate_xml_report()
        # Check that the system-out tag is empty when no steps are present
        assert "<system-out></system-out>" in xml

    def test_generate_xml_report_failure_with_special_characters(self):
        """Test XML report generation for a failing test with special characters in the comment.
        Checks that the failure tag includes the special characters even though no escaping is performed.
        """
        report = Report()
        special_comment = "Failure & error: <Everything broke>"
        test_fail = FakeEnd2endTest(
            "SpecialCharTest", False, False, special_comment, ["step1", "step2"]
        )
        report.add_e2e_results([test_fail])
        xml = report.generate_xml_report()
        # Validate that the special characters in the comment appear as-is in the XML
        assert special_comment in xml

    def test_valid_xml_structure(self):
        """Test that the generated XML is well formed and follows the expected structure."""
        report = Report()
        test = FakeEnd2endTest("ValidTest", True, False, "All good", ["step1", "step2"])
        report.add_e2e_results([test])
        xml = report.generate_xml_report()
        # Try to parse the XML; if it is malformed, ET.fromstring() will raise an error
        root = ET.fromstring(xml)
        # Check that the root tag is 'testsuites'
        assert root.tag == "testsuites"
        # Check that there is one testsuite element
        testsuite = root.find("testsuite")
        assert testsuite is not None
        # Check that the testsuite has one 'testcase' child element
        testcases = testsuite.findall("testcase")
        assert len(testcases) == 1

    def test_generate_xml_report_with_unicode(self):
        """Test generating XML report with Unicode characters in test data."""
        report = Report()
        # Create a fake test with Unicode characters in name, comment and steps
        unicode_comment = "Ångström failure – тест не пройден"
        unicode_steps = ["step1: ünicode", "step2: ✓ check"]
        test_unicode = FakeEnd2endTest(
            "UnicodeTest", False, False, unicode_comment, unicode_steps
        )
        report.add_e2e_results([test_unicode])
        xml = report.generate_xml_report()
        # Check that the Unicode strings are present in the XML.
        assert "UnicodeTest" in xml
        assert unicode_comment in xml
        for step in unicode_steps:
            assert step in xml
