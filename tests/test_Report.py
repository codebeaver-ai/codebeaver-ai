import pytest
from codebeaver.Report import Report
import xml.etree.ElementTree as ET
# Dummy class to simulate the End2endTest type used in Report
class DummyEnd2endTest:
    def __init__(self, name, passed, errored, steps, comment):
        self.name = name
        self.passed = passed
        self.errored = errored
        self.steps = steps
        self.comment = comment

def test_generate_xml_report_empty():
    """Test generate_xml_report with no E2E results added."""
    report = Report()
    xml = report.generate_xml_report()
    # Check that declarations are present and that no tests have been run
    assert '<?xml version="1.0" encoding="UTF-8"?>' in xml
    assert 'tests="0"' in xml
    assert 'failures="0"' in xml
    assert 'errors="0"' in xml

def test_generate_xml_report_passed_test():
    """Test generate_xml_report with a passed test (no failure or error)."""
    report = Report()
    test_item = DummyEnd2endTest(
            name="TestSuccess",
            passed=True,
            errored=False,
            steps=["Step1", "Step2"],
            comment="All good"
    )
    report.add_e2e_results([test_item])
    xml = report.generate_xml_report()
    # Check that the test name and steps are in the XML
    assert 'TestSuccess' in xml
    assert 'Step1' in xml
    assert 'Step2' in xml
    # Verify that no failure or error tags are generated for a passed test
    assert '<failure' not in xml
    assert '<error' not in xml

def test_generate_xml_report_failure_and_error():
    """Test generate_xml_report with one failed test and one errored test."""
    report = Report()
    failed_test = DummyEnd2endTest(
            name="TestFailure",
            passed=False,
            errored=False,
            steps=["StepA", "StepB"],
            comment="Assertion failed"
    )
    error_test = DummyEnd2endTest(
            name="TestError",
            passed=False,  # This property is secondary since errored=True will trigger error branch.
            errored=True,
            steps=["StepX", "StepY"],
            comment="Exception occurred"
    )
    report.add_e2e_results([failed_test, error_test])
    xml = report.generate_xml_report()
    # Verify the test names and steps are present in the report.
    assert 'TestFailure' in xml
    assert 'TestError' in xml
    # Check that the failure tag is present for the failed test
    assert '<failure message="Test failed" type="Failure">' in xml
    assert 'Assertion failed' in xml
    # Check that the error tag is present for the errored test
    assert '<error message="Test execution error" type="Error">' in xml
    assert 'Exception occurred' in xml
    # Verify that the counts for tests, failures, and errors are accurate.
    assert 'tests="2"' in xml
    assert 'failures="1"' in xml
    assert 'errors="1"' in xml

def test_generate_not_implemented():
    """Test that generate_html_report and generate_json_report raise NotImplementedError."""
    report = Report()
    with pytest.raises(NotImplementedError):
            report.generate_html_report()
    with pytest.raises(NotImplementedError):
            report.generate_json_report()
def test_add_multiple_e2e_results():
    """Test that add_e2e_results can be called multiple times and the report aggregates results correctly."""
    report = Report()
    test_item1 = DummyEnd2endTest(
        name="Test1", passed=True, errored=False, steps=["Step1"], comment="First test"
    )
    test_item2 = DummyEnd2endTest(
        name="Test2", passed=False, errored=False, steps=["Step2"], comment="Second test"
    )
    test_item3 = DummyEnd2endTest(
        name="Test3", passed=False, errored=True, steps=["Step3"], comment="Third test"
    )
    report.add_e2e_results([test_item1])
    report.add_e2e_results([test_item2, test_item3])
    xml = report.generate_xml_report()
    # There should be 3 tests in total
    assert 'tests="3"' in xml
    # There should be 1 failure (Test2) and 1 error (Test3)
    assert 'failures="1"' in xml
    assert 'errors="1"' in xml

def test_generate_xml_report_empty_steps_and_comment():
    """Test generate_xml_report for a test with empty steps and comment."""
    report = Report()
    test_item = DummyEnd2endTest(
        name="EmptyTest", passed=False, errored=False, steps=[], comment=""
    )
    report.add_e2e_results([test_item])
    xml = report.generate_xml_report()
    # Check that <testcase> with name "EmptyTest" exists
    assert 'EmptyTest' in xml
    # Check that the <system-out> tag is present and empty (accounting for possible formatting variations)
    assert ("<system-out></system-out>" in xml or 
            "<system-out/>" in xml or 
            "<system-out>\n</system-out>" in xml)
    # Check that a failure tag is present even if the comment is empty
    assert '<failure message="Test failed" type="Failure">' in xml

def test_generate_xml_report_special_characters():
    """Test generate_xml_report with special XML characters in test fields."""
    report = Report()
    special_name = 'Test & <Test>'
    special_steps = ['Step "One"', "Step 'Two'", "Step <Three> & More"]
    special_comment = 'Failed due to error: <unexpected & error>'
    test_item = DummyEnd2endTest(
        name=special_name, passed=False, errored=False, steps=special_steps, comment=special_comment
    )
    report.add_e2e_results([test_item])
    xml = report.generate_xml_report()
    # Check that the test name, steps, and comment with special characters appear exactly as provided
    assert special_name in xml
    for step in special_steps:
        assert step in xml
    assert special_comment in xml
def test_generate_xml_report_well_formed_xml():
    """Test that the generated XML report is well-formed and can be parsed."""
    report = Report()
    dummy_test = DummyEnd2endTest(
        name="WellFormedTest", passed=True, errored=False, steps=["Line1", "Line2"], comment="No issues"
    )
    report.add_e2e_results([dummy_test])
    xml = report.generate_xml_report()
    # Parse the XML to ensure it is well formed
    root = ET.fromstring(xml)
    assert root.tag == "testsuites"
    # There should be one testsuite inside
    testsuite = root.find("testsuite")
    assert testsuite is not None
    # Verify that the testsuite attribute 'tests' equals "1"
    assert testsuite.attrib.get("tests") == "1"

def test_generate_xml_report_system_out_newlines():
    """Test that the system-out element contains the steps separated by newlines."""
    report = Report()
    dummy_test = DummyEnd2endTest(
        name="NewLineTest", passed=True, errored=False, steps=["Step1", "Step2", "Step3"], comment="All good"
    )
    report.add_e2e_results([dummy_test])
    xml = report.generate_xml_report()
    # Extract the content between the system-out tags
    start = xml.find("<system-out>")
    end = xml.find("</system-out>")
    assert start != -1 and end != -1
    system_out_content = xml[start + len("<system-out>"):end].strip()
    # Expect the steps to be separated by newlines
    assert system_out_content == "Step1\nStep2\nStep3"
def test_generate_xml_report_error_override():
    """Test that an errored test overrides a passed test.
    Even if 'passed' is set to True, the test should be considered errored if 'errored' is True.
    """
    report = Report()
    test_item = DummyEnd2endTest(
        name="OverrideTest", passed=True, errored=True, steps=["Step1 override"], comment="Error overrides pass"
    )
    report.add_e2e_results([test_item])
    xml = report.generate_xml_report()
    assert 'OverrideTest' in xml
    # Check that error tag is generated and not failure tag
    assert '<error message="Test execution error" type="Error">' in xml
    assert '<failure' not in xml

def test_generate_xml_report_multiple_calls():
    """Test that calling generate_xml_report multiple times produces identical outputs.
    This ensures that the Report does not modify its internal state when generating the XML.
    """
    report = Report()
    test_item = DummyEnd2endTest(
        name="MultiCallTest", passed=True, errored=False, steps=["Step multi"], comment="Consistent test"
    )
    report.add_e2e_results([test_item])
    xml1 = report.generate_xml_report()
    xml2 = report.generate_xml_report()
    assert xml1 == xml2

def test_generate_xml_report_state_modification():
    """Test that the Report’s state persists and can be modified after generating a report.
    Initially, one test is added and reported. After generating the first XML, a new test is added,
    and the updated report should include both tests.
    """
    report = Report()
    test_item1 = DummyEnd2endTest(
        name="InitialTest", passed=True, errored=False, steps=["Step1"], comment="Initial test"
    )
    report.add_e2e_results([test_item1])
    xml_initial = report.generate_xml_report()
    assert 'InitialTest' in xml_initial

    test_item2 = DummyEnd2endTest(
        name="AddedLater", passed=False, errored=False, steps=["Step Late"], comment="Later failure"
    )
    report.add_e2e_results([test_item2])
    xml_updated = report.generate_xml_report()
    assert 'InitialTest' in xml_updated
    assert 'AddedLater' in xml_updated
    # Verify that the tests attribute now shows 2 tests.
    assert 'tests="2"' in xml_updated