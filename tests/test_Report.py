from xml.etree import ElementTree as ET

import pytest

from codebeaver.Report import Report
from codebeaver.types import End2endTest


@pytest.fixture
def sample_e2e_tests():
    return [
        End2endTest(
            name="Test 1",
            passed=True,
            errored=False,
            steps=["Step 1", "Step 2"],
            comment="",
        ),
        End2endTest(
            name="Test 2",
            passed=False,
            errored=False,
            steps=["Step 1", "Step 2"],
            comment="Failed",
        ),
        End2endTest(
            name="Test 3",
            passed=False,
            errored=True,
            steps=["Step 1"],
            comment="Error occurred",
        ),
    ]


class TestReport:
    """
    Test suite for the Report class.
    """

    def test_add_e2e_results(self, sample_e2e_tests):
        """
        Test that e2e results are correctly added to the Report instance.
        """
        report = Report()
        report.add_e2e_results(sample_e2e_tests)
        assert len(report.e2e_results) == 3
        assert all(isinstance(test, End2endTest) for test in report.e2e_results)

    def test_generate_xml_report_structure(self, sample_e2e_tests):
        """
        Test the structure of the generated XML report.
        """
        report = Report()
        report.add_e2e_results(sample_e2e_tests)
        xml_str = report.generate_xml_report()

        root = ET.fromstring(xml_str)
        assert root.tag == "testsuites"
        assert len(root) == 1

        testsuite = root[0]
        assert testsuite.tag == "testsuite"
        assert testsuite.attrib["name"] == "E2E Test Suite"
        assert testsuite.attrib["tests"] == "3"
        assert testsuite.attrib["failures"] == "1"
        assert testsuite.attrib["errors"] == "1"

        assert len(testsuite) == 3
        for testcase in testsuite:
            assert testcase.tag == "testcase"
            assert "name" in testcase.attrib
            assert testcase.attrib["classname"] == "E2ETest"

    def test_generate_xml_report_content(self, sample_e2e_tests):
        """
        Test the content of the generated XML report.
        """
        report = Report()
        report.add_e2e_results(sample_e2e_tests)
        xml_str = report.generate_xml_report()

        root = ET.fromstring(xml_str)
        testsuite = root[0]

        # Test 1 (Passed)
        testcase1 = testsuite[0]
        assert testcase1.attrib["name"] == "Test 1"
        assert len(testcase1.findall("failure")) == 0
        assert len(testcase1.findall("error")) == 0
        assert testcase1.find("system-out").text == "Step 1\nStep 2"

        # Test 2 (Failed)
        testcase2 = testsuite[1]
        assert testcase2.attrib["name"] == "Test 2"
        failure = testcase2.find("failure")
        assert failure is not None
        assert failure.attrib["message"] == "Test failed"
        assert failure.attrib["type"] == "Failure"
        assert failure.text.strip() == "Failed"

        # Test 3 (Error)
        testcase3 = testsuite[2]
        assert testcase3.attrib["name"] == "Test 3"
        error = testcase3.find("error")
        assert error is not None
        assert error.attrib["message"] == "Test execution error"
        assert error.attrib["type"] == "Error"
        assert error.text.strip() == "Error occurred"

    def test_generate_xml_report_empty(self):
        """
        Test generating an XML report with no test results.
        """
        report = Report()
        xml_str = report.generate_xml_report()

        root = ET.fromstring(xml_str)
        testsuite = root[0]
        assert testsuite.attrib["tests"] == "0"
        assert testsuite.attrib["failures"] == "0"
        assert testsuite.attrib["errors"] == "0"
        assert len(testsuite) == 0

    def test_generate_html_report_not_implemented(self):
        """
        Test that generating HTML report raises NotImplementedError.
        """
        report = Report()
        with pytest.raises(NotImplementedError):
            report.generate_html_report()

    def test_generate_json_report_not_implemented(self):
        """
        Test that generating JSON report raises NotImplementedError.
        """
        report = Report()
        with pytest.raises(NotImplementedError):
            report.generate_json_report()
