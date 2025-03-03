import asyncio
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
pytestmark = pytest.mark.asyncio

from src.codebeaver.E2E import E2E, End2endTest, TestCase

# Test for run_test method when the agent returns a valid JSON result
async def test_run_test_success():
    """Test run_test returns a successful test result when agent returns valid JSON result."""
    dummy_result = json.dumps({"passed": True, "comment": "All good."})
    with patch("src.codebeaver.E2E.Agent", autospec=True) as mock_agent:
        agent_instance = mock_agent.return_value
        history = MagicMock()
        history.final_result.return_value = dummy_result
        agent_instance.run = AsyncMock(return_value=history)
        with patch("src.codebeaver.E2E.Browser", autospec=True) as mock_browser:
            browser_instance = mock_browser.return_value
            browser_instance.close = AsyncMock(return_value=None)
            test_obj = End2endTest(name="Test1", steps=["Do something"], url="http://example.com")
            e2e = E2E(tests={"Test1": {"steps": ["Do something"], "url": "http://example.com"}})
            result_test = await e2e.run_test(test_obj)
            assert result_test.passed == True
            assert result_test.comment == "All good."

# Test for run_test method when the agent returns no result
async def test_run_test_failure():
    """Test run_test handles no result scenario by setting errored and appropriate comment."""
    with patch("src.codebeaver.E2E.Agent", autospec=True) as mock_agent:
        agent_instance = mock_agent.return_value
        history = MagicMock()
        history.final_result.return_value = None
        agent_instance.run = AsyncMock(return_value=history)
        with patch("src.codebeaver.E2E.Browser", autospec=True) as mock_browser:
            browser_instance = mock_browser.return_value
            browser_instance.close = AsyncMock(return_value=None)
            test_obj = End2endTest(name="Test2", steps=["Do something else"], url="http://example.org")
            e2e = E2E(tests={"Test2": {"steps": ["Do something else"], "url": "http://example.org"}})
            result_test = await e2e.run_test(test_obj)
            assert result_test.errored == True
            assert result_test.comment == "No result from the test"

# Test for the run method that iterates over tests and writes the results to a JSON file
async def test_run_method(tmp_path, monkeypatch):
    """Test the run method processes multiple tests and writes results to a JSON file."""
    # Prepare a dummy run_test that simulates each test as passed
    async def dummy_run_test(test):
        test.passed = True
        test.comment = "Simulated"
        return test

    # Patch the run_test method in the E2E instance with our dummy_run_test
    monkeyatch_set = monkeypatch.setattr  # just to ease readability
    monkeyatch_set(E2E, "run_test", dummy_run_test)

    # Change current directory to tmp_path so that file writes are isolated
    monkeypatch.chdir(tmp_path)

    tests_dict = {
        "Test1": {"steps": ["Step1"], "url": "http://example.com"},
        "Test2": {"steps": ["Step2"], "url": "http://example.org"}
    }
    e2e = E2E(tests=tests_dict)
    results = await e2e.run()
    # Verify that both tests are processed and marked as passed
    assert len(results) == 2
    for test in results:
        assert test.passed == True
        assert test.comment == "Simulated"

    # Verify that e2e.json file was created and contains the correct keys
    e2e_file = tmp_path / "e2e.json"
    assert e2e_file.exists()
    with open(e2e_file, "r") as f:
        data = json.load(f)
        assert isinstance(data, list)
        for item in data:
            assert "name" in item
            assert "steps" in item
            assert "url" in item
            assert "passed" in item
            assert "errored" in item
            assert "comment" in item
# Test for verifying CHROME_INSTANCE_PATH environment variable overrides default in E2E.__init__
async def test_chrome_instance_env(monkeypatch):
    """Test that CHROME_INSTANCE_PATH environment variable overrides the default chrome_instance_path."""
    dummy_path = "/dummy/path/chrome"
    monkeypatch.setenv("CHROME_INSTANCE_PATH", dummy_path)
    e2e = E2E(tests={})
    assert e2e.chrome_instance_path == dummy_path
    # Clean up: remove the environment variable for subsequent tests
    monkeypatch.delenv("CHROME_INSTANCE_PATH", raising=False)

# Test for the run method with an empty tests dictionary
async def test_run_empty(monkeypatch, tmp_path, capsys):
    """Test that run() handles an empty tests dictionary by creating an empty e2e.json file and printing a summary."""
    # Define a dummy run_test that returns the test as is
    async def dummy_run_test(test):
        return test

    monkeypatch.setattr(E2E, "run_test", dummy_run_test)
    monkeypatch.chdir(tmp_path)

    e2e = E2E(tests={})
    results = await e2e.run()

    # Expect no tests processed, so results list should be empty
    assert results == []

    # Verify that e2e.json file was created and contains an empty list
    e2e_file = tmp_path / "e2e.json"
    assert e2e_file.exists()
    with open(e2e_file, "r") as f:
        data = json.load(f)
        assert data == []

    # Capture printed output and verify summary message is printed
    captured = capsys.readouterr().out
    assert "0/0 E2E tests passed" in captured
# Additional tests to improve test coverage
async def test_run_test_invalid_json():
    """Test run_test raises an error when agent returns invalid JSON string."""
    from src.codebeaver.E2E import E2E, End2endTest
    with patch("src.codebeaver.E2E.Agent", autospec=True) as mock_agent:
        agent_instance = mock_agent.return_value
        history = MagicMock()
        # Return a string that is not valid JSON to trigger a validation error
        history.final_result.return_value = "invalid json string"
        agent_instance.run = AsyncMock(return_value=history)
        with patch("src.codebeaver.E2E.Browser", autospec=True) as mock_browser:
            browser_instance = mock_browser.return_value
            browser_instance.close = AsyncMock(return_value=None)
            test_obj = End2endTest(name="TestInvalid", steps=["Invalid step"], url="http://invalid")
            e2e = E2E(tests={"TestInvalid": {"steps": ["Invalid step"], "url": "http://invalid"}})
            with pytest.raises(Exception):
                await e2e.run_test(test_obj)

async def test_end2end_test_defaults():
    """Test that End2endTest initializes with the correct default attributes."""
    from src.codebeaver.E2E import End2endTest
    test_obj = End2endTest(name="DefaultTest", steps=["Step1", "Step2"], url="http://default")
    assert test_obj.name == "DefaultTest"
    assert test_obj.steps == ["Step1", "Step2"]
    assert test_obj.url == "http://default"
    # Verify the default values are as expected
    assert test_obj.passed is False
    assert test_obj.errored is False
    assert test_obj.comment == ""
async def test_run_test_agent_exception():
    """Test run_test propagates exception when Agent.run() raises an exception."""
    with patch("src.codebeaver.E2E.Agent", autospec=True) as mock_agent:
        agent_instance = mock_agent.return_value
        # Make agent.run raise an Exception
        agent_instance.run = AsyncMock(side_effect=Exception("Agent failure"))
        with patch("src.codebeaver.E2E.Browser", autospec=True) as mock_browser:
            browser_instance = mock_browser.return_value
            browser_instance.close = AsyncMock(return_value=None)
            test_obj = End2endTest(name="TestException", steps=["Step"], url="http://exception")
            e2e = E2E(tests={"TestException": {"steps": ["Step"], "url": "http://exception"}})
            with pytest.raises(Exception, match="Agent failure"):
                await e2e.run_test(test_obj)

async def test_run_test_extra_fields():
    """Test run_test correctly parses valid JSON result with extra fields included."""
    dummy_result = json.dumps({"passed": True, "comment": "Extra", "unexpected": "value"})
    with patch("src.codebeaver.E2E.Agent", autospec=True) as mock_agent:
        agent_instance = mock_agent.return_value
        history = MagicMock()
        history.final_result.return_value = dummy_result
        agent_instance.run = AsyncMock(return_value=history)
        with patch("src.codebeaver.E2E.Browser", autospec=True) as mock_browser:
            browser_instance = mock_browser.return_value
            browser_instance.close = AsyncMock(return_value=None)
            test_obj = End2endTest(name="TestExtra", steps=["Step extra"], url="http://extra")
            e2e = E2E(tests={"TestExtra": {"steps": ["Step extra"], "url": "http://extra"}})
            result_test = await e2e.run_test(test_obj)
            assert result_test.passed is True
            assert result_test.comment == "Extra"

async def test_run_print_summary_single(tmp_path, monkeypatch, capsys):
    """Test that run prints the correct summary for a single test execution."""
    async def dummy_run_test(test):
        test.passed = True
        test.comment = "Single test"
        return test

    # Override run_test with our dummy implementation.
    monkeypatch.setattr(E2E, "run_test", dummy_run_test)
    # Change to a temporary directory to isolate file output.
    monkeypatch.chdir(tmp_path)

    tests_dict = {
        "SingleTest": {"steps": ["Do one thing"], "url": "http://single"}
    }
    e2e = E2E(tests=tests_dict)
    results = await e2e.run()
    # Capture the printed output.
    captured = capsys.readouterr().out
    assert "1/1 E2E tests passed" in captured
    assert "SingleTest" in captured
    assert "Single test" in captured
    # Verify that the e2e.json file was created and contains one test.
    e2e_file = tmp_path / "e2e.json"
    assert e2e_file.exists()
    with open(e2e_file, "r") as f:
        data = json.load(f)
        assert len(data) == 1
async def test_run_test_browser_close_exception():
    """Test that run_test propagates exception from browser.close() method."""
    with patch("src.codebeaver.E2E.Agent", autospec=True) as mock_agent:
        agent_instance = mock_agent.return_value
        history = MagicMock()
        # Simulate returning a valid JSON result.
        dummy_result = json.dumps({"passed": True, "comment": "Should propagate close error"})
        history.final_result.return_value = dummy_result
        agent_instance.run = AsyncMock(return_value=history)
        with patch("src.codebeaver.E2E.Browser", autospec=True) as mock_browser:
            browser_instance = mock_browser.return_value
            # Simulate an error during browser.close
            browser_instance.close = AsyncMock(side_effect=Exception("Browser close failed"))
            test_obj = End2endTest(name="TestBrowserClose", steps=["Test step"], url="http://browserclose")
            e2e = E2E(tests={"TestBrowserClose": {"steps": ["Test step"], "url": "http://browserclose"}})
            with pytest.raises(Exception, match="Browser close failed"):
                await e2e.run_test(test_obj)

async def test_end2end_test_wrong_types():
    """Test that initializing End2endTest with wrong types raises ValidationError."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        # 'steps' should be a list, but here we pass a string to trigger the validation error.
        End2endTest(name="WrongTypeTest", steps="not a list", url="http://wrong")
async def test_run_test_wrong_json_structure():
    """Test run_test raises a validation error when agent returns JSON with an unexpected structure."""
    from pydantic import ValidationError
    with patch("src.codebeaver.E2E.Agent", autospec=True) as mock_agent:
        agent_instance = mock_agent.return_value
        history = MagicMock()
        # Return valid JSON missing the required 'comment' field for TestCase
        dummy_result = json.dumps({"passed": True})
        history.final_result.return_value = dummy_result
        agent_instance.run = AsyncMock(return_value=history)
        with patch("src.codebeaver.E2E.Browser", autospec=True) as mock_browser:
            browser_instance = mock_browser.return_value
            browser_instance.close = AsyncMock(return_value=None)
            test_obj = End2endTest(name="TestWrongStructure", steps=["Step"], url="http://wrongstructure")
            e2e = E2E(tests={"TestWrongStructure": {"steps": ["Step"], "url": "http://wrongstructure"}})
            with pytest.raises(ValidationError):
                await e2e.run_test(test_obj)

async def test_run_mixed_results(tmp_path, monkeypatch, capsys):
    """Test the run method processes tests with mixed results (passed and failed) correctly and prints summary."""
    async def dummy_run_test(test):
        if test.name == "PassTest":
            test.passed = True
            test.comment = "Passed"
        elif test.name == "FailTest":
            test.passed = False
            test.comment = "Failed"
        return test

    monkeypatch.setattr(E2E, "run_test", dummy_run_test)
    monkeypatch.chdir(tmp_path)

    tests_dict = {
        "PassTest": {"steps": ["Step1"], "url": "http://pass.com"},
        "FailTest": {"steps": ["Step2"], "url": "http://fail.com"}
    }
    e2e = E2E(tests=tests_dict)
    results = await e2e.run()

    # Verify summary: 1 out of 2 tests passed
    captured = capsys.readouterr().out
    assert "1/2 E2E tests passed" in captured

    # Verify each test's result in the returned results list
    for test in results:
        if test.name == "PassTest":
            assert test.passed is True
            assert test.comment == "Passed"
        elif test.name == "FailTest":
            assert test.passed is False
            assert test.comment == "Failed"

    # Verify that the e2e.json file is created with the appropriate content
    e2e_file = tmp_path / "e2e.json"
    assert e2e_file.exists()
    with open(e2e_file, "r") as f:
        data = json.load(f)
        assert len(data) == 2
# Additional test: verify that if run_test raises an exception during iteration in run(), the exception is propagated and no output file is created.
async def test_run_raises_exception_in_run_test(tmp_path, monkeypatch):
    """Test that run() propagates an exception from run_test and does not create the output file."""
    async def dummy_run_test(test):
        raise Exception("Simulated run_test failure")

    monkeypatch.setattr(E2E, "run_test", dummy_run_test)
    monkeypatch.chdir(tmp_path)

    tests_dict = {"FailingTest": {"steps": ["Step failure"], "url": "http://fail.com"}}
    e2e = E2E(tests=tests_dict)
    with pytest.raises(Exception, match="Simulated run_test failure"):
        await e2e.run()
    # Verify that the output file was not created
    assert not (tmp_path / "e2e.json").exists()

# Additional test: verify that passing an invalid tests structure (non-dictionary) causes an AttributeError when run() is called.
async def test_run_invalid_tests_structure(tmp_path, monkeypatch):
    """Test that run() raises an error when tests is not a dictionary."""
    # Pass an invalid tests structure (a list instead of dict) – .items() will not be available.
    e2e = E2E(tests=["not", "a", "dict"])
    monkeypatch.chdir(tmp_path)
    with pytest.raises(AttributeError):
        await e2e.run()
# Additional tests to increase test coverage
async def test_run_test_creates_correct_agent_task(monkeypatch):
    """Test that run_test constructs the Agent with the correct task string including URL and steps."""
    dummy_result = json.dumps({"passed": True, "comment": "Task check"})
    captured_task = ""

    # Import Agent from our module and override its __init__
    from src.codebeaver.E2E import Agent, E2E, End2endTest, Browser
    original_init = Agent.__init__
    def fake_init(self, *args, **kwargs):
        nonlocal captured_task
        captured_task = kwargs.get("task", "")
        # Set up run to return a dummy history with a final_result method
        self.run = AsyncMock(return_value=MagicMock(final_result=MagicMock(return_value=dummy_result)))
    monkeypatch.setattr(Agent, "__init__", fake_init)

    # Patch Browser to simulate a valid browser instance with a close method
    fake_browser = MagicMock()
    fake_browser.close = AsyncMock(return_value=None)
    monkeypatch.setattr("src.codebeaver.E2E.Browser", lambda config: fake_browser)

    # Create an End2endTest instance and run run_test
    test_obj = End2endTest(name="TestTask", steps=["Click X", "Enter Y"], url="http://taskurl.com")
    e2e = E2E(tests={"TestTask": {"steps": ["Click X", "Enter Y"], "url": "http://taskurl.com"}})
    result_test = await e2e.run_test(test_obj)

    # Check that the constructed task string contains the URL and steps
    assert "http://taskurl.com" in captured_task
    assert "Click X" in captured_task
    assert "Enter Y" in captured_task
    # Verify that the test result is as expected
    assert result_test.passed is True
    assert result_test.comment == "Task check"

async def test_model_dump_of_end2end_test():
    """Test that the model_dump method of End2endTest returns all expected fields."""
    from src.codebeaver.E2E import End2endTest
    test_obj = End2endTest(name="DumpTest", steps=["Step A", "Step B"], url="http://dump.com")
    dump = test_obj.model_dump()
    expected_keys = {"name", "steps", "url", "passed", "errored", "comment"}
    assert isinstance(dump, dict)
    assert expected_keys.issubset(dump.keys())
async def test_run_missing_keys(monkeypatch, tmp_path):
    """Test that run() raises KeyError when a test dictionary is missing required keys."""
    # Change to a temporary directory so file writes (if any) are isolated.
    monkeypatch.chdir(tmp_path)
    # Provide a test case with a missing "steps" key.
    e2e = E2E(tests={"MissingTest": {"url": "http://missing.com"}})
    with pytest.raises(KeyError):
        await e2e.run()

async def test_default_chrome_path(monkeypatch):
    """Test that the default chrome_instance_path is used when CHROME_INSTANCE_PATH env variable is not set."""
    # Ensure CHROME_INSTANCE_PATH is not set.
    monkeypatch.delenv("CHROME_INSTANCE_PATH", raising=False)
    e2e = E2E(tests={})
    default_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    assert e2e.chrome_instance_path == default_path
async def test_run_test_browser_close_called(monkeypatch):
    """Test that run_test calls browser.close exactly once."""
    from src.codebeaver.E2E import E2E, End2endTest
    import json
    with patch("src.codebeaver.E2E.Agent", autospec=True) as mock_agent:
        agent_instance = mock_agent.return_value
        history = MagicMock()
        dummy_result = json.dumps({"passed": True, "comment": "Browser close test"})
        history.final_result.return_value = dummy_result
        agent_instance.run = AsyncMock(return_value=history)
        with patch("src.codebeaver.E2E.Browser", autospec=True) as mock_browser:
            browser_instance = mock_browser.return_value
            browser_instance.close = AsyncMock(return_value=None)
            test_obj = End2endTest(name="TestCloseCalled", steps=["Verify close"], url="http://close.test")
            e2e = E2E(tests={"TestCloseCalled": {"steps": ["Verify close"], "url": "http://close.test"}})
            result_test = await e2e.run_test(test_obj)
            assert result_test.passed == True
            assert result_test.comment == "Browser close test"
            browser_instance.close.assert_called_once()

async def test_run_json_dump_error(tmp_path, monkeypatch):
    """Test that run() propagates an exception when json.dump fails."""
    from src.codebeaver.E2E import E2E
    async def dummy_run_test(test):
        test.passed = True
        test.comment = "dummy"
        return test
    monkeypatch.setattr(E2E, "run_test", dummy_run_test)
    monkeypatch.chdir(tmp_path)
    tests_dict = {"TestError": {"steps": ["Step error"], "url": "http://error.com"}}
    e2e = E2E(tests=tests_dict)
    def fake_json_dump(data, f):
        raise Exception("Dump failed")
    monkeypatch.setattr(json, "dump", fake_json_dump)
    with pytest.raises(Exception, match="Dump failed"):
        await e2e.run()
    # Ensure that the file was not created
    assert not (tmp_path / "e2e.json").exists()