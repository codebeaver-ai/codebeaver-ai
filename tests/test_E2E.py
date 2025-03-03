import os
import json
import asyncio
import pytest
from codebeaver.E2E import E2E, End2endTest, TestCase

# DummyHistory class simulates the history returned by Agent.run
class DummyHistory:
    def __init__(self, task: str):
        self.task = task

    def final_result(self):
        # If the task string contains 'http://success.com', return a valid JSON result.
        if "http://success.com" in self.task:
            return json.dumps({"passed": True, "comment": "Success"})
        return None

# Dummy asynchronous function to simulate Agent.run behavior
async def dummy_run(self):
    return DummyHistory(self.task)

# Dummy asynchronous function to simulate Browser.close behavior
async def dummy_close(self):
    return

# Import Agent and Browser for monkey patching.
from browser_use import Agent
from browser_use.browser.browser import Browser

# Automatically patch Agent.run and Browser.close in all tests.
@pytest.fixture(autouse=True)
def patch_agent_and_browser(monkeypatch):
    monkeypatch.setattr(Agent, "run", dummy_run)
    monkeypatch.setattr(Browser, "close", dummy_close)

# Fixture to work in a temporary directory to avoid creating files in the project root.
@pytest.fixture
def temp_cwd(tmp_path, monkeypatch):
    original_cwd = os.getcwd()
    monkeypatch.chdir(tmp_path)
    yield tmp_path
    monkeypatch.chdir(original_cwd)

@pytest.mark.asyncio
async def test_run_test_success():
    """
    Test run_test returns a successful test result when the Agent returns a valid result.
    """
    test = End2endTest(name="test_success", steps=["click element", "verify element"], url="http://success.com")
    e2e = E2E(tests={})
    result = await e2e.run_test(test)
    assert result.passed is True
    assert result.comment == "Success"
    assert result.errored is False

@pytest.mark.asyncio
async def test_run_test_failure():
    """
    Test run_test flags an error when the Agent returns no result.
    """
    test = End2endTest(name="test_failure", steps=["click element"], url="http://failure.com")
    e2e = E2E(tests={})
    result = await e2e.run_test(test)
    assert result.passed is False
    assert result.comment == "No result from the test"
    assert result.errored is True

@pytest.mark.asyncio
async def test_run_all(temp_cwd):
    """
    Test that the run method processes multiple tests and writes the results to an e2e.json file.
    """
    tests = {
        "test1": {"steps": ["step1", "step2"], "url": "http://success.com"},
        "test2": {"steps": ["step1"], "url": "http://failure.com"}
    }
    e2e = E2E(tests=tests)
    results = await e2e.run()
    # Assert that two test results are returned
    assert len(results) == 2
    # Verify that the file e2e.json exists and contains valid JSON
    assert os.path.exists("e2e.json")
    with open("e2e.json", "r") as f:
        data = json.load(f)
    assert isinstance(data, list)
    for res in data:
        if res["name"] == "test1":
            assert res["passed"] is True
            assert res["comment"] == "Success"
        elif res["name"] == "test2":
            assert res["errored"] is True
            assert res["comment"] == "No result from the test"

@pytest.mark.asyncio
async def test_run_json_output(temp_cwd):
    """
    Test that the run method writes a valid JSON file with the expected keys for each test result.
    """
    tests = {
        "test_json": {"steps": ["action1", "action2"], "url": "http://success.com"}
    }
    e2e = E2E(tests=tests)
    await e2e.run()
    with open("e2e.json", "r") as f:
        data = json.load(f)
    # Assert one result is written and it contains the expected keys
    assert len(data) == 1
    expected_keys = {"steps", "url", "passed", "errored", "comment", "name"}
    assert expected_keys.issubset(set(data[0].keys()))
@pytest.mark.asyncio
async def test_run_test_invalid_json(monkeypatch):
    """Test run_test raises an exception when Agent returns invalid JSON."""
    # Define a dummy asynchronous run that returns an invalid JSON string.
    async def dummy_run_invalid(self):
        class DummyHistoryInvalid:
            def final_result(self):
                return "invalid json"
        return DummyHistoryInvalid()

    monkeypatch.setattr(Agent, "run", dummy_run_invalid)
    test = End2endTest(name="test_invalid", steps=["step1"], url="http://invalid.com")
    e2e = E2E(tests={})
    with pytest.raises(Exception):
        await e2e.run_test(test)

@pytest.mark.asyncio
async def test_chrome_instance_path_env_override(monkeypatch):
    """Test that the CHROME_INSTANCE_PATH environment variable overrides the default chrome_instance_path."""
    dummy_path = "/dummy/chrome/path"
    monkeypatch.setenv("CHROME_INSTANCE_PATH", dummy_path)
    e2e = E2E(tests={})
    assert e2e.chrome_instance_path == dummy_path

@pytest.mark.asyncio
async def test_run_empty_tests(temp_cwd):
    """Test that running E2E.run with no tests creates an empty e2e.json file and returns an empty list."""
    e2e = E2E(tests={})
    results = await e2e.run()
    assert results == []
    assert os.path.exists("e2e.json")
    with open("e2e.json", "r") as f:
        data = json.load(f)
    assert data == []

@pytest.mark.asyncio
async def test_run_missing_key_error():
    """Test that running E2E.run with tests missing required keys (e.g. 'url') raises a KeyError."""
    tests = {
        "test_missing": {"steps": ["action"]}  # Missing 'url'
    }
    e2e = E2E(tests=tests)
    with pytest.raises(KeyError):
        await e2e.run()
@pytest.mark.asyncio
async def test_run_test_agent_exception(monkeypatch):
    """Test that run_test propagates exceptions raised by Agent.run."""
    async def dummy_run_exception(self):
        raise Exception("Agent error")
    monkeypatch.setattr(Agent, "run", dummy_run_exception)
    test = End2endTest(name="test_exception", steps=["step1"], url="http://exception.com")
    e2e = E2E(tests={})
    with pytest.raises(Exception) as excinfo:
        await e2e.run_test(test)
    assert "Agent error" in str(excinfo.value)

@pytest.mark.asyncio
async def test_run_exception_in_one_test(monkeypatch, temp_cwd):
    """Test that E2E.run propagates an exception if a test fails during Agent.run."""
    async def dummy_run_exception(self):
        raise Exception("Test failure")
    tests = {"test_exception": {"steps": ["step1"], "url": "http://exception.com"}}
    monkeypatch.setattr(Agent, "run", dummy_run_exception)
    e2e = E2E(tests=tests)
    with pytest.raises(Exception) as excinfo:
        await e2e.run()
    assert "Test failure" in str(excinfo.value)

@pytest.mark.asyncio
async def test_run_test_empty_steps():
    """Test that run_test works correctly when steps are an empty list."""
    test = End2endTest(name="test_empty_steps", steps=[], url="http://success.com")
    e2e = E2E(tests={})
    result = await e2e.run_test(test)
    assert result.passed is True
    assert result.comment == "Success"
    assert result.errored is False
@pytest.mark.asyncio
async def test_run_test_task_format(monkeypatch):
    """Test that run_test constructs the correct task string for Agent."""
    # Create a storage dict to capture the task string passed to Agent.__init__
    storage = {}
    # Define a dummy __init__ that stores the task and sets a minimal attribute
    def dummy_init(self, task, llm, browser, controller):
        storage["task"] = task
        self.task = task
    monkeypatch.setattr(Agent, "__init__", dummy_init)
    test = End2endTest(name="test_task_format", steps=["action1", "action2"], url="http://format.com")
    e2e = E2E(tests={})
    await e2e.run_test(test)
    # Verify that the task string contains the expected instructions, including the URL and steps.
    assert "Go to http://format.com" in storage["task"]
    assert ("action1" in storage["task"] and "action2" in storage["task"]) or ("['action1', 'action2']" in storage["task"])

@pytest.mark.asyncio
async def test_chrome_instance_path_default(monkeypatch):
    """Test that the default chrome_instance_path is used when the environment variable is not set."""
    monkeypatch.delenv("CHROME_INSTANCE_PATH", raising=False)
    e2e = E2E(tests={})
    default_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    assert e2e.chrome_instance_path == default_path
@pytest.mark.asyncio
async def test_end2end_test_defaults():
    """Test that End2endTest initializes with default values correctly."""
    e2e_test = End2endTest(name="dummy", steps=["action"], url="http://dummy.com")
    assert e2e_test.passed is False
    assert e2e_test.errored is False
    assert e2e_test.comment == ""

@pytest.mark.asyncio
async def test_run_test_browser_close_exception(monkeypatch):
    """Test that run_test propagates an exception when Browser.close raises an error."""
    # Define a dummy run that returns a valid DummyHistory result
    async def dummy_run_success(self):
        # We use a fixed string including 'http://success.com' so DummyHistory.final_result returns valid JSON
        return DummyHistory("Visit http://success.com")

    monkeypatch.setattr(Agent, "run", dummy_run_success)
    # Monkey patch Browser.close to raise an exception
    async def dummy_close_exception(self):
        raise Exception("Closing error")
    monkeypatch.setattr(Browser, "close", dummy_close_exception)

    test = End2endTest(name="test_browser_exception", steps=["click element"], url="http://success.com")
    e2e_obj = E2E(tests={})
    with pytest.raises(Exception) as excinfo:
        await e2e_obj.run_test(test)
    assert "Closing error" in str(excinfo.value)

@pytest.mark.asyncio
async def test_run_test_final_result_exception(monkeypatch):
    """Test that run_test propagates an exception when history.final_result raises an error."""
    # Define a dummy history class whose final_result method raises an exception.
    class DummyHistoryError:
        def final_result(self):
            raise Exception("final_result error")

    async def dummy_run_error(self):
        # The task string here is arbitrary.
        return DummyHistoryError()

    monkeypatch.setattr(Agent, "run", dummy_run_error)
    # Ensure Browser.close is a no-op
    async def dummy_close_nop(self):
        return
    monkeypatch.setattr(Browser, "close", dummy_close_nop)

    test = End2endTest(name="test_final_result_exception", steps=["action"], url="http://any.com")
    e2e_obj = E2E(tests={})
    with pytest.raises(Exception) as excinfo:
        await e2e_obj.run_test(test)
    assert "final_result error" in str(excinfo.value)
@pytest.mark.asyncio
async def test_run_test_invalid_schema(monkeypatch):
    """Test that run_test raises an exception when the JSON is valid but does not follow the TestCase schema."""
    async def dummy_run_invalid_schema(self):
        class DummyHistoryInvalidSchema:
            def final_result(self):
                # Return valid JSON but missing required keys ('passed' and 'comment')
                return json.dumps({"unexpected_key": True})
        return DummyHistoryInvalidSchema()
    monkeypatch.setattr(Agent, "run", dummy_run_invalid_schema)
    async def dummy_close_noop(self):
        return
    monkeypatch.setattr(Browser, "close", dummy_close_noop)
    test = End2endTest(name="test_invalid_schema", steps=["action"], url="http://failure.com")
    e2e = E2E(tests={})
    with pytest.raises(Exception):
        await e2e.run_test(test)
@pytest.mark.asyncio
async def test_run_print_output(capsys, temp_cwd):
    """
    Test that the E2E.run method prints the expected output summary and writes a valid e2e.json file.
    """
    tests = {
        "test_print": {"steps": ["click button"], "url": "http://success.com"}
    }
    e2e = E2E(tests=tests)
    results = await e2e.run()
    captured = capsys.readouterr().out
    # Verify that the printed output includes expected phrases.
    assert "Running test:" in captured
    assert "E2E tests passed" in captured
    assert "test_print" in captured

    # Verify that the file e2e.json exists and its content matches the test result.
    assert os.path.exists("e2e.json")
    with open("e2e.json", "r") as f:
        data = json.load(f)
    # Data is a list with one test result dictionary.
    assert isinstance(data, list)
    assert len(data) == 1
    result_data = data[0]
    expected_keys = {"steps", "url", "passed", "errored", "comment", "name"}
    assert expected_keys.issubset(set(result_data.keys()))
    assert result_data["name"] == "test_print"
    assert result_data["passed"] is True
@pytest.mark.asyncio
async def test_browser_config_usage(monkeypatch):
    """Test that the Browser is instantiated with the expected chrome_instance_path configuration."""
    storage = {}
    def dummy_browser_init(self, config):
        storage['chrome_instance_path'] = config.chrome_instance_path
    monkeypatch.setattr(Browser, "__init__", dummy_browser_init)
    async def dummy_close_noop(self):
        return
    monkeypatch.setattr(Browser, "close", dummy_close_noop)
    test = End2endTest(name="test_browser_config", steps=["step1"], url="http://success.com")
    e2e_obj = E2E(tests={})
    await e2e_obj.run_test(test)
    assert storage.get('chrome_instance_path') == e2e_obj.chrome_instance_path

@pytest.mark.asyncio
async def test_end2end_invalid_steps():
    """Test that End2endTest raises a validation error when steps is not a list."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        End2endTest(name="test_invalid_steps", steps="not a list", url="http://dummy.com")
@pytest.mark.asyncio
async def test_run_json_dump_failure(monkeypatch, temp_cwd):
    """Test that E2E.run propagates an exception if json.dump fails during file write."""
    # Create a dummy agent run that returns valid output
    async def dummy_run_success(self):
        from codebeaver.E2E import DummyHistory
        return DummyHistory(f"Visit {self.task}")
    monkeypatch.setattr(Agent, "run", dummy_run_success)
    # Monkeypatch json.dump to raise an exception
    def dummy_json_dump(*args, **kwargs):
        raise Exception("json dump error")
    monkeypatch.setattr(json, "dump", dummy_json_dump)

    tests = {
        "test_json_fail": {"steps": ["action1"], "url": "http://success.com"}
    }
    e2e = E2E(tests=tests)
    with pytest.raises(Exception) as excinfo:
        await e2e.run()
    assert "json dump error" in str(excinfo.value)

@pytest.mark.asyncio
async def test_run_does_not_call_browser_close_on_agent_exception(monkeypatch):
    """Test that if Agent.run raises an exception, Browser.close is not called."""
    # Define a flag to check whether Browser.close was called.
    flag = {"closed": False}

    async def dummy_run_exception(self):
        raise Exception("Agent error before close")

    monkeypatch.setattr(Agent, "run", dummy_run_exception)

    # Patch Browser.close to set the flag if called.
    async def dummy_close_flag(self):
        flag["closed"] = True
    monkeypatch.setattr(Browser, "close", dummy_close_flag)

    test = End2endTest(name="test_no_close", steps=["action"], url="http://exception.com")
    e2e = E2E(tests={})
    with pytest.raises(Exception) as excinfo:
        await e2e.run_test(test)
    # Ensure that Browser.close was not called due to the exception in Agent.run.
    assert flag["closed"] is False

@pytest.mark.asyncio
async def test_run_wrong_tests_type():
    """Test that E2E.run raises an attribute error when tests is not a dict."""
    # Pass a list instead of a dict to the E2E constructor.
    e2e = E2E(tests=["not", "a", "dict"])
    with pytest.raises(AttributeError):
        await e2e.run()
def test_end2end_test_model_dump():
    """
    Test that End2endTest.model_dump produces the expected output dictionary.
    """
    test_instance = End2endTest(name="dump_test", steps=["step1", "step2"], url="http://dump.com")
    dumped = test_instance.model_dump()
    expected_keys = {"steps", "url", "passed", "errored", "comment", "name"}
    assert expected_keys.issubset(set(dumped.keys()))
    assert dumped["passed"] is False
    assert dumped["errored"] is False
    assert dumped["comment"] == ""

def test_end2end_test_repr():
    """
    Test the __repr__ output of End2endTest to ensure it includes the most important fields.
    """
    test_instance = End2endTest(name="repr_test", steps=["action"], url="http://repr.com")
    representation = repr(test_instance)
    # The representation should include the test name and URL
    assert "repr_test" in representation
    assert "http://repr.com" in representation
    # Optionally also check for default boolean values in the representation
    assert "False" in representation