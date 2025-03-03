import asyncio
import json
import os
import pytest
from codebeaver.E2E import E2E, End2endTest, TestCase

# Fake classes to simulate behavior of external components used in E2E
class FakeHistorySuccess:
    def final_result(self):
        return '{"passed": true, "comment": "Test passed"}'

class FakeHistoryNoResult:
    def final_result(self):
        return None

class FakeAgentSuccess:
    def __init__(self, **kwargs):
        pass
    async def run(self):
        return FakeHistorySuccess()

class FakeAgentNoResult:
    def __init__(self, **kwargs):
        pass
    async def run(self):
        return FakeHistoryNoResult()

class FakeBrowser:
    def __init__(self, config=None):
        self.config = config
    async def close(self):
        pass

@pytest.mark.asyncio
async def test_run_test_success(monkeypatch):
    """Test the run_test method when a valid test result is returned."""
    monkeypatch.setattr("codebeaver.E2E.Agent", FakeAgentSuccess)
    monkeypatch.setattr("codebeaver.E2E.Browser", FakeBrowser)
    test = End2endTest(name="test_success", steps=["dummy step"], url="http://example.com")
    e2e = E2E(tests={})
    result = await e2e.run_test(test)
    assert result.passed is True
    assert result.comment == "Test passed"
    assert result.errored is False

@pytest.mark.asyncio
async def test_run_test_no_result(monkeypatch):
    """Test the run_test method when no valid result is returned."""
    monkeypatch.setattr("codebeaver.E2E.Agent", FakeAgentNoResult)
    monkeypatch.setattr("codebeaver.E2E.Browser", FakeBrowser)
    test = End2endTest(name="test_no_result", steps=["dummy step"], url="http://example.com")
    e2e = E2E(tests={})
    result = await e2e.run_test(test)
    assert result.errored is True
    assert result.comment == "No result from the test"

@pytest.mark.asyncio
async def test_run_method(monkeypatch, tmp_path):
    """Test the run method to check if multiple tests are processed and a JSON file is created."""
    monkeypatch.setattr("codebeaver.E2E.Agent", FakeAgentSuccess)
    monkeypatch.setattr("codebeaver.E2E.Browser", FakeBrowser)
    tests_dict = {
        "test1": {"steps": ["step1"], "url": "http://example.com"},
        "test2": {"steps": ["step2"], "url": "http://example.org"}
    }
    e2e = E2E(tests=tests_dict)
    monkeypatch.chdir(tmp_path)
    results = await e2e.run()
    json_file = tmp_path / "e2e.json"
    assert json_file.exists()
    with open(json_file, "r") as f:
        data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == 2
        for test_data in data:
            assert test_data["passed"] is True
            assert test_data["comment"] == "Test passed"

def test_chrome_instance_env(monkeypatch):
    """Test that the chrome_instance_path is overridden by the environment variable."""
    monkeypatch.setenv("CHROME_INSTANCE_PATH", "dummy_chrome_path")
    e2e = E2E(tests={})
    assert e2e.chrome_instance_path == "dummy_chrome_path"
# Fake classes to simulate invalid JSON output from final_result
class FakeHistoryInvalid:
    def final_result(self):
        return "invalid json"

class FakeAgentInvalid:
    def __init__(self, **kwargs):
        pass
    async def run(self):
        return FakeHistoryInvalid()

@pytest.mark.asyncio
async def test_run_test_invalid_json(monkeypatch):
    """Test the run_test method when an invalid JSON string is returned,
    expecting a validation error due to invalid format."""
    monkeypatch.setattr("codebeaver.E2E.Agent", FakeAgentInvalid)
    monkeypatch.setattr("codebeaver.E2E.Browser", FakeBrowser)
    test = End2endTest(name="test_invalid_json", steps=["dummy step"], url="http://example.com")
    e2e = E2E(tests={})
    with pytest.raises(Exception):
        await e2e.run_test(test)

@pytest.mark.asyncio
async def test_run_empty(monkeypatch, tmp_path):
    """Test the run method with an empty tests dictionary,
    expecting an empty e2e.json file and an empty results list."""
    e2e = E2E(tests={})
    monkeypatch.chdir(tmp_path)
    results = await e2e.run()
    json_file = tmp_path / "e2e.json"
    assert json_file.exists()
    with open(json_file, "r") as f:
        data = json.load(f)
        assert data == []
    assert results == []
# Additional tests for increased coverage
class FakeHistoryEmpty:
    def final_result(self):
        return ""

class FakeAgentException:
    def __init__(self, **kwargs):
        pass
    async def run(self):
        raise Exception("Agent error")

class FakeAgentEmpty:
    def __init__(self, **kwargs):
        pass
    async def run(self):
        return FakeHistoryEmpty()

@pytest.mark.asyncio
async def test_run_test_exception(monkeypatch):
    """Test run_test method when agent.run raises an exception."""
    monkeypatch.setattr("codebeaver.E2E.Agent", FakeAgentException)
    monkeypatch.setattr("codebeaver.E2E.Browser", FakeBrowser)
    test = End2endTest(name="test_exception", steps=["dummy step"], url="http://example.com")
    e2e = E2E(tests={})
    with pytest.raises(Exception, match="Agent error"):
        await e2e.run_test(test)

@pytest.mark.asyncio
async def test_run_test_empty_result(monkeypatch):
    """Test run_test method when final_result returns an empty string (falsey value)."""
    monkeypatch.setattr("codebeaver.E2E.Agent", FakeAgentEmpty)
    monkeypatch.setattr("codebeaver.E2E.Browser", FakeBrowser)
    test = End2endTest(name="test_empty", steps=["dummy step"], url="http://example.com")
    e2e = E2E(tests={})
    result = await e2e.run_test(test)
    assert result.errored is True
    assert result.comment == "No result from the test"
@pytest.mark.asyncio
async def test_run_mixed(monkeypatch, tmp_path):
    """Test the run method with mixed outcomes: one test returns a valid result and one returns no result."""
    # Define a FakeAgent that returns different histories based on the test URL in the task string
    class FakeAgentMixed:
        def __init__(self, task, llm, browser, controller):
            self.task = task
        async def run(self):
            if "http://example.com" in self.task:
                return FakeHistorySuccess()
            else:
                return FakeHistoryNoResult()

    monkeypatch.setattr("codebeaver.E2E.Agent", FakeAgentMixed)
    monkeypatch.setattr("codebeaver.E2E.Browser", FakeBrowser)

    tests_dict = {
        "test_success": {"steps": ["step1"], "url": "http://example.com"},
        "test_failure": {"steps": ["step2"], "url": "http://example.org"}
    }
    e2e = E2E(tests=tests_dict)
    monkeypatch.chdir(tmp_path)
    results = await e2e.run()
    json_file = tmp_path / "e2e.json"
    assert json_file.exists()
    with open(json_file, "r") as f:
        data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == 2
        for test_data in data:
            if test_data["name"] == "test_success":
                assert test_data["passed"] is True
                assert test_data["comment"] == "Test passed"
            elif test_data["name"] == "test_failure":
                assert test_data["errored"] is True
                assert test_data["comment"] == "No result from the test"

@pytest.mark.asyncio
async def test_chrome_instance_default(monkeypatch):
    """Test that the default chrome_instance_path is used when the environment variable is not set."""
    monkeypatch.delenv("CHROME_INSTANCE_PATH", raising=False)
    e2e = E2E(tests={})
@pytest.mark.asyncio
async def test_agent_task_format(monkeypatch):
    """Test that the agent is instantiated with a task string that contains the steps and URL."""
    captured_task = {}

    class FakeAgentCapture:
        def __init__(self, task, llm, browser, controller):
            self.task = task
        async def run(self):
            captured_task['value'] = self.task
            return FakeHistorySuccess()

    monkeypatch.setattr("codebeaver.E2E.Agent", FakeAgentCapture)
    monkeypatch.setattr("codebeaver.E2E.Browser", FakeBrowser)
    test = End2endTest(name="test_task_format", steps=["verify element", "check title"], url="http://example.net")
    e2e = E2E(tests={})
    result = await e2e.run_test(test)
    task_text = captured_task.get('value', '')
    assert "http://example.net" in task_text
    assert "verify element" in task_text and "check title" in task_text
    assert result.passed is True
    assert e2e.chrome_instance_path == "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
def test_end2end_test_defaults():
    """Test that default values in End2endTest are correctly initialized."""
    test = End2endTest(name="default_test", steps=["step1"], url="http://example.com")
    assert test.passed is False
    assert test.errored is False
    assert test.comment == ""

def test_testcase_validation():
    """Test that TestCase model correctly validates a JSON string."""
    json_str = '{"passed": false, "comment": "Failed test"}'
    testcase = TestCase.model_validate_json(json_str)
    assert testcase.passed is False
    assert testcase.comment == "Failed test"

@pytest.mark.asyncio
async def test_browser_close_called(monkeypatch):
    """Test that the browser's close method is called after a test run."""
    closed_flag = {"closed": False}

    class SpyBrowser(FakeBrowser):
        async def close(self):
            closed_flag["closed"] = True

    monkeypatch.setattr("codebeaver.E2E.Browser", SpyBrowser)
    monkeypatch.setattr("codebeaver.E2E.Agent", FakeAgentSuccess)
    test = End2endTest(name="browser_close_test", steps=["dummy step"], url="http://example.com")
    e2e = E2E(tests={})
    await e2e.run_test(test)
    assert closed_flag["closed"] is True
@pytest.mark.asyncio
async def test_run_test_browser_close_exception(monkeypatch):
    """Test that an exception in browser.close is propagated."""
    class FakeBrowserCloseException(FakeBrowser):
        async def close(self):
            raise Exception("Browser close error")
    monkeypatch.setattr("codebeaver.E2E.Browser", FakeBrowserCloseException)
    monkeypatch.setattr("codebeaver.E2E.Agent", FakeAgentSuccess)
    test = End2endTest(name="test_browser_close_exception", steps=["dummy step"], url="http://example.com")
    e2e = E2E(tests={})
    with pytest.raises(Exception, match="Browser close error"):
        await e2e.run_test(test)

@pytest.mark.asyncio
async def test_run_test_empty_steps(monkeypatch):
    """Test run_test when the steps list is empty; the task string should reflect the empty list."""
    captured_task = {}
    class FakeAgentCaptureSteps:
        def __init__(self, task, llm, browser, controller):
            self.task = task
        async def run(self):
            captured_task["value"] = self.task
            return FakeHistorySuccess()
    monkeypatch.setattr("codebeaver.E2E.Agent", FakeAgentCaptureSteps)
    monkeypatch.setattr("codebeaver.E2E.Browser", FakeBrowser)
    test = End2endTest(name="test_empty_steps", steps=[], url="http://example.com")
    e2e = E2E(tests={})
    await e2e.run_test(test)
    task_value = captured_task.get("value", "")
    assert "[]" in task_value
# New tests to increase test coverage
@pytest.mark.asyncio
async def test_run_test_extra_fields(monkeypatch):
    """Test run_test when extra fields are present in the returned JSON string.
    The TestCase model should correctly pick out the 'passed' and 'comment' fields even if extra keys exist.
    """
    class FakeHistoryExtra:
        def final_result(self):
            return '{"passed": true, "comment": "Extra fields here", "another": "ignored"}'

    class FakeAgentExtra:
        def __init__(self, **kwargs):
            pass
        async def run(self):
            return FakeHistoryExtra()

    monkeypatch.setattr("codebeaver.E2E.Agent", FakeAgentExtra)
    monkeypatch.setattr("codebeaver.E2E.Browser", FakeBrowser)
    test = End2endTest(name="test_extra_fields", steps=["dummy step"], url="http://example.com")
    e2e = E2E(tests={})
    result = await e2e.run_test(test)
    assert result.passed is True
    assert result.comment == "Extra fields here"

@pytest.mark.asyncio
async def test_run_output_and_file_content(monkeypatch, tmp_path, capsys):
    """Test the run method output by verifying both the printed output and the JSON file contents.
    This helps ensure that the run() method correctly processes a tests dictionary and writes the expected file.
    """
    tests_dict = {
        "test1": {"steps": ["step1"], "url": "http://example.com"},
        "test2": {"steps": ["step2"], "url": "http://example.org"}
    }

    monkeypatch.setattr("codebeaver.E2E.Agent", FakeAgentSuccess)
    monkeypatch.setattr("codebeaver.E2E.Browser", FakeBrowser)
    e2e = E2E(tests=tests_dict)
    monkeypatch.chdir(tmp_path)
    _ = await e2e.run()
    # Capture printed output
    captured = capsys.readouterr().out
    assert "E2E tests passed" in captured
    json_file = tmp_path / "e2e.json"
    assert json_file.exists()
    with open(json_file, "r") as f:
        data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == 2
        for test_data in data:
            assert test_data["passed"] is True
            assert test_data["comment"] == "Test passed"

@pytest.mark.asyncio
async def test_run_all_tests_error_handling(monkeypatch, tmp_path):
    """Test the run method when handling a tests dictionary with mixed outcomes.
    One test returns a valid result while the other returns no result. This verifies that run()
    collects both and reports the proper state for each test.
    """
    tests_dict = {
        "success_test": {"steps": ["step1"], "url": "http://example.com"},
        "fail_test": {"steps": ["step2"], "url": "http://example.org"}
    }

    class FakeAgentMixed:
        def __init__(self, task, llm, browser, controller):
            self.task = task
        async def run(self):
            if "http://example.com" in self.task:
                return FakeHistorySuccess()
            else:
                return FakeHistoryNoResult()

    monkeypatch.setattr("codebeaver.E2E.Agent", FakeAgentMixed)
    monkeypatch.setattr("codebeaver.E2E.Browser", FakeBrowser)
    e2e = E2E(tests=tests_dict)
    monkeypatch.chdir(tmp_path)
    results = await e2e.run()
    # Verify results list contains both tests with the appropriate outcomes
    assert len(results) == 2
    for test_result in results:
        if test_result.name == "success_test":
            assert test_result.passed is True
            assert test_result.comment == "Test passed"
        elif test_result.name == "fail_test":
            assert test_result.errored is True
            assert test_result.comment == "No result from the test"

async def test_run_method_exception_propagation(monkeypatch, tmp_path):
    """Test that run() propagates an exception if one test's agent.run raises an exception."""
    class FakeAgentMixedException:
        def __init__(self, task, llm, browser, controller):
            self.task = task
        async def run(self):
            if "http://example.com" in self.task:
                return FakeHistorySuccess()
            else:
                raise Exception("Test exception in agent")
    monkeypatch.setattr("codebeaver.E2E.Agent", FakeAgentMixedException)
    monkeypatch.setattr("codebeaver.E2E.Browser", FakeBrowser)
    tests_dict = {
        "test_success": {"steps": ["step1"], "url": "http://example.com"},
        "test_exception": {"steps": ["step2"], "url": "http://example.org"}
    }
    e2e = E2E(tests=tests_dict)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(Exception, match="Test exception in agent"):
        await e2e.run()
@pytest.mark.asyncio
async def test_run_test_missing_fields(monkeypatch):
    """Test run_test method when final_result returns JSON missing required fields, expecting a validation error."""
    class FakeHistoryMissingFields:
        def final_result(self):
            return '{"passed": true}'
    class FakeAgentMissingFields:
        def __init__(self, **kwargs):
            pass
        async def run(self):
            return FakeHistoryMissingFields()
    monkeypatch.setattr("codebeaver.E2E.Agent", FakeAgentMissingFields)
    monkeypatch.setattr("codebeaver.E2E.Browser", FakeBrowser)
    test = End2endTest(name="test_missing_fields", steps=["dummy step"], url="http://example.com")
    e2e = E2E(tests={})
    with pytest.raises(Exception):
        await e2e.run_test(test)
@pytest.mark.asyncio
async def test_run_test_no_final_result_method(monkeypatch):
    """Test run_test method when the history object does not have a final_result method, expecting an AttributeError."""
    class FakeHistoryNoFinalMethod:
        pass

    class FakeAgentNoFinalMethod:
        def __init__(self, **kwargs):
            pass
        async def run(self):
            return FakeHistoryNoFinalMethod()

    monkeypatch.setattr("codebeaver.E2E.Agent", FakeAgentNoFinalMethod)
    monkeypatch.setattr("codebeaver.E2E.Browser", FakeBrowser)
    test = End2endTest(name="test_no_final_method", steps=["dummy step"], url="http://example.com")
    e2e = E2E(tests={})
    with pytest.raises(AttributeError):
        await e2e.run_test(test)

@pytest.mark.asyncio
async def test_run_missing_test_keys(monkeypatch, tmp_path):
    """Test run method when tests dictionary is missing required keys, expecting a KeyError."""
    tests_dict = {
        "test_missing": {"steps": ["step1"]}  # Missing the required 'url' key.
    }
    e2e = E2E(tests=tests_dict)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(KeyError):
        await e2e.run()