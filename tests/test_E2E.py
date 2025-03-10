import asyncio
import json
import os
import pytest
from pydantic import ValidationError
import logging

from codebeaver.E2E import E2E, End2endTest

# Fake classes to simulate Browser and Agent behavior
class FakeBrowser:
    def __init__(self, config):
        self.config = config
        self.closed = False
    async def close(self):
        self.closed = True

class FakeHistory:
    def __init__(self, task):
        self.task = task
    def final_result(self):
        if "simulate_no_result" in self.task:
            return None
        elif "simulate_failure" in self.task:
            return json.dumps({"passed": False, "comment": "Failed test simulated"})
        else:
            return json.dumps({"passed": True, "comment": "Test succeeded"})

class FakeAgent:
    def __init__(self, task, llm, browser, controller):
        with open("e2e.json", "w") as f:
            json.dump([test.model_dump() for test in all_tests], f)
        passed_count = sum(1 for t in all_tests if t.passed)
        print(f"{passed_count}/{len(all_tests)} E2E tests passed")
        self.controller = controller
    async def run(self):
        if "simulate_no_result" in self.task:
            return FakeHistory("simulate_no_result")
        return FakeHistory(self.task)

@pytest.fixture(autouse=True)
def patch_browser_agent(monkeypatch):
    # Patch Browser and Agent in the E2E module with our fake versions
    monkeypatch.setattr("codebeaver.E2E.Browser", FakeBrowser)
    monkeypatch.setattr("codebeaver.E2E.Agent", FakeAgent)

@pytest.mark.asyncio
class TestE2E:
    """Tests for the E2E class."""

    async def test_run_test_success(self):
        """Test run_test method for a successful test case."""
        e2e = E2E(tests={})
        test = End2endTest(name="TestSuccess", steps=["step1"], url="http://example.com")
        result = await e2e.run_test(test)
        assert result.passed is True
        assert result.comment == "Test succeeded"
        assert result.errored is False

    async def test_run_test_failure(self):
        """Test run_test method for a test case simulating failure."""
        e2e = E2E(tests={})
        test = End2endTest(name="TestFailure", steps=["simulate_failure"], url="http://example.com")
        result = await e2e.run_test(test)
        assert result.passed is False
        assert result.comment == "Failed test simulated"
        assert result.errored is False

    async def test_run_test_no_result(self):
        """Test run_test method when no result is returned from agent.run."""
        e2e = E2E(tests={})
        test = End2endTest(name="TestNoResult", steps=["simulate_no_result"], url="http://example.com")
        result = await e2e.run_test(test)
        assert result.errored is True
        assert result.comment == "No result from the test"

    async def test_run_overall(self, monkeypatch, tmp_path, capsys):
        """Test the overall run method to check file creation and summary printing."""
        monkeypatch.chdir(tmp_path)
        tests_dict = {
            "Test1": {"steps": ["step1"], "url": "http://example.com"},
            "TestNoResult": {"steps": ["simulate_no_result"], "url": "http://example.com"}
        }
        e2e = E2E(tests=tests_dict)
        results = await e2e.run()
        assert len(results) == 2
        e2e_file = tmp_path / "e2e.json"
        assert e2e_file.exists()
        with open(e2e_file, "r") as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == 2
        captured = capsys.readouterr().out
        assert "E2E tests passed" in captured
    @pytest.mark.asyncio
    async def test_env_variable(self, monkeypatch):
        """Test that the CHROME_INSTANCE_PATH environment variable is used if set."""
        monkeypatch.setenv("CHROME_INSTANCE_PATH", "/custom/chrome/path")
        e2e = E2E(tests={})
        assert e2e.chrome_instance_path == "/custom/chrome/path"

    @pytest.mark.asyncio
    async def test_run_empty_tests(self, tmp_path, monkeypatch, capsys):
        """Test run method when no tests are provided."""
        monkeypatch.chdir(tmp_path)
        e2e = E2E(tests={})
        results = await e2e.run()
        # No tests are executed so results should be an empty list.
        assert results == []
        e2e_file = tmp_path / "e2e.json"
        assert e2e_file.exists()
        with open(e2e_file, "r") as f:
            data = json.load(f)
        assert data == []
        captured = capsys.readouterr().out
        assert "0/0 E2E tests passed" in captured

    @pytest.mark.asyncio
    async def test_run_test_invalid_result(self, monkeypatch):
        """Test run_test method when the agent returns invalid JSON."""
        e2e = E2E(tests={})
        test = End2endTest(name="TestInvalid", steps=["invalid"], url="http://example.com")
        # Patch FakeHistory.final_result to return a non-JSON string to simulate an invalid result.
        monkeypatch.setattr(FakeHistory, "final_result", lambda self: "not json")
        with pytest.raises(Exception):
            await e2e.run_test(test)
    async def test_run_test_agent_exception(self, monkeypatch):
        """Test that run_test propagates an exception when Agent.run raises an exception."""
        e2e = E2E(tests={})
        test_obj = End2endTest(name="TestException", steps=["trigger_exception"], url="http://example.com")
        monkeypatch.setattr("codebeaver.E2E.Agent.run", lambda self: (_ for _ in ()).throw(Exception("Agent error")))
        with pytest.raises(Exception, match="Agent error"):
            await e2e.run_test(test_obj)

    async def test_run_test_empty_steps(self):
        """Test run_test with an empty steps list to ensure default success behavior."""
        e2e = E2E(tests={})
        test_obj = End2endTest(name="TestEmptySteps", steps=[], url="http://example.com")
        result = await e2e.run_test(test_obj)
        assert result.passed is True
        assert result.comment == "Test succeeded"
        assert result.errored is False
    @pytest.mark.asyncio
    async def test_browser_close_exception(self, monkeypatch):
        """Test run_test propagates exception when Browser.close raises an error."""
        e2e = E2E(tests={})
        test_obj = End2endTest(name="TestBrowserCloseException", steps=["step1"], url="http://example.com")
        # Patch FakeBrowser.close to raise an exception
        monkeypatch.setattr(FakeBrowser, "close", lambda self: (_ for _ in ()).throw(Exception("Browser close error")))
        with pytest.raises(Exception, match="Browser close error"):
            await e2e.run_test(test_obj)

    @pytest.mark.asyncio
    async def test_agent_task_string(self, monkeypatch):
        """Test that the Agent is initialized with a correctly formatted task string."""
        captured_tasks = []
        original_init = FakeAgent.__init__
        def new_init(self, task, llm, browser, controller):
            captured_tasks.append(task)
            self.llm = llm
            self.browser = browser
            self.controller = controller
        monkeypatch.setattr(FakeAgent, "__init__", new_init)
        e2e = E2E(tests={})
        test_obj = End2endTest(name="TestTaskString", steps=["click button"], url="http://example.com")
        await e2e.run_test(test_obj)
        # Verify that the task string that was set in the Agent contains the URL and the step
        assert "http://example.com" in captured_tasks[0]
        assert "click button" in captured_tasks[0]
        # Restore the original FakeAgent.__init__
        monkeypatch.setattr(FakeAgent, "__init__", original_init)
    async def test_end2endtest_defaults(self):
        """Test that End2endTest default values are set correctly upon initialization."""
        test = End2endTest(name="DefaultTest", steps=["step1"], url="http://example.com")
        # By design, passed should default to False, errored to False and comment to empty string.
        assert test.passed is False
        assert test.errored is False
        assert test.comment == ""
    
    async def test_browser_closed_called(self, monkeypatch):
        """Test that the browser's close method is indeed called in run_test."""
        captured_browser = {}
        original_init = FakeBrowser.__init__
        def new_init(self, config):
            captured_browser["instance"] = self
            original_init(self, config)
        monkeypatch.setattr(FakeBrowser, "__init__", new_init)
        e2e = E2E(tests={})
        test_obj = End2endTest(name="TestBrowserClose", steps=["step1"], url="http://example.com")
        await e2e.run_test(test_obj)
        assert "instance" in captured_browser, "Expected FakeBrowser instance to be captured"
        assert captured_browser["instance"].closed is True, "Expected the browser to be closed after run_test"
        # Restore original FakeBrowser.__init__
        monkeypatch.setattr(FakeBrowser, "__init__", original_init)
    async def test_run_test_missing_field(self, monkeypatch):
        """Test that run_test raises a validation error when JSON result is missing required fields."""
        e2e = E2E(tests={})
        test_obj = End2endTest(name="TestMissingField", steps=["simulate_missing_field"], url="http://example.com")
        monkeypatch.setattr(FakeHistory, "final_result", lambda self: json.dumps({"passed": True}))
        with pytest.raises(Exception) as excinfo:
            await e2e.run_test(test_obj)
        assert "comment" in str(excinfo.value)

    async def test_run_test_extra_keys_ignored(self, monkeypatch):
        """Test that run_test correctly parses the result even if extra keys are present in the JSON output."""
        e2e = E2E(tests={})
        test_obj = End2endTest(name="TestExtraKeys", steps=["simulate_extra_keys"], url="http://example.com")
        monkeypatch.setattr(FakeHistory, "final_result", lambda self: json.dumps({"passed": False, "comment": "Handled extra keys", "extra": "ignored"}))
        result = await e2e.run_test(test_obj)
        assert result.passed is False
        assert result.comment == "Handled extra keys"
        assert result.errored is False
    @pytest.mark.asyncio
    async def test_run_file_write_exception(self, monkeypatch):
        """Test that the run method propagates an exception when file writing fails."""
        # Monkey-patch built-in open to simulate a file write error.
        def faulty_open(*args, **kwargs):
            raise IOError("File write error")
        monkeypatch.setattr("builtins.open", faulty_open)
        tests_dict = {"Test1": {"steps": ["step1"], "url": "http://example.com"}}
        e2e = E2E(tests=tests_dict)
        with pytest.raises(IOError, match="File write error"):
            await e2e.run()

    @pytest.mark.asyncio
    async def test_default_chrome_instance_path(self, monkeypatch):
        """Test that the default chrome_instance_path is used when the environment variable is not set."""
        # Ensure that CHROME_INSTANCE_PATH is not set.
        monkeypatch.delenv("CHROME_INSTANCE_PATH", raising=False)
        e2e = E2E(tests={})
        assert e2e.chrome_instance_path == "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    @pytest.mark.asyncio
    async def test_run_overall_multiple_tests(self, monkeypatch, tmp_path, capsys):
        """Test the overall run method with multiple tests having different outcomes."""
        monkeypatch.chdir(tmp_path)
        tests_dict = {
            "TestPass": {"steps": ["step1"], "url": "http://example.com"},
            "TestFail": {"steps": ["simulate_failure"], "url": "http://example.com"},
            "TestError": {"steps": ["simulate_no_result"], "url": "http://example.com"}
        }
        e2e = E2E(tests=tests_dict)
        results = await e2e.run()
        # Expect three tests to have been executed
        assert len(results) == 3
        # Verify individual test results
        for test in results:
            if test.name == "TestPass":
                assert test.passed is True
                assert test.comment == "Test succeeded"
                assert test.errored is False
            elif test.name == "TestFail":
                assert test.passed is False
                assert test.comment == "Failed test simulated"
                assert test.errored is False
            elif test.name == "TestError":
                assert test.errored is True
                assert test.comment == "No result from the test"
        # Verify file writing by reading back the e2e.json file
        e2e_file = tmp_path / "e2e.json"
        assert e2e_file.exists()
        with open(e2e_file, "r") as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == 3
        # Check that the summary printed output contains "1/3 E2E tests passed"
        captured = capsys.readouterr().out
    @pytest.mark.asyncio
    async def test_agent_task_string_multiple_steps(self, monkeypatch):
        """Test that the Agent is initialized with a correctly formatted task string when multiple steps are provided."""
        captured_tasks = []
        original_init = FakeAgent.__init__
        def new_init(self, task, llm, browser, controller):
            captured_tasks.append(task)
            self.llm = llm
            self.browser = browser
            self.controller = controller
        monkeypatch.setattr(FakeAgent, "__init__", new_init)
        e2e = E2E(tests={})
        steps = ["click button", "scroll down", "enter text"]
        test_obj = End2endTest(name="TestMultipleSteps", steps=steps, url="http://example.com")
        await e2e.run_test(test_obj)
        # Verify the task string contains every step
        task_str = captured_tasks[0]
        for step in steps:
            assert step in task_str
        # Restore the original FakeAgent.__init__
        monkeypatch.setattr(FakeAgent, "__init__", original_init)

    @pytest.mark.asyncio
    async def test_agent_task_string_with_long_steps(self, monkeypatch):
        """Test that the task string is correctly formatted even when steps contain long texts and special characters."""
        captured_tasks = []
        original_init = FakeAgent.__init__
        def new_init(self, task, llm, browser, controller):
            captured_tasks.append(task)
            self.llm = llm
            self.browser = browser
            self.controller = controller
        monkeypatch.setattr(FakeAgent, "__init__", new_init)
        e2e = E2E(tests={})
        long_steps = [
            "Click the very long button that says 'Submit Your Application Now!'",
            "Wait for the confirmation pop-up: ◉_◉",
            "Ensure the footer is visible by scrolling all the way down."
        ]
        test_obj = End2endTest(name="TestLongSteps", steps=long_steps, url="http://example.com")
        await e2e.run_test(test_obj)
        task_str = captured_tasks[0]
        for step in long_steps:
            assert step in task_str
        monkeypatch.setattr(FakeAgent, "__init__", original_init)
        assert "1/3 E2E tests passed" in captured
    async def test_browser_config_usage(self, monkeypatch):
        """Test that the browser is initialized with the correct chrome_instance_path."""
        captured_config = {}
        original_init = FakeBrowser.__init__
        def new_init(self, config):
            captured_config["config"] = config
            original_init(self, config)
        monkeypatch.setattr(FakeBrowser, "__init__", new_init)
        custom_path = "/custom/path/for/chrome"
        e2e = E2E(tests={}, chrome_instance_path=custom_path)
        test_obj = End2endTest(name="TestBrowserConfig", steps=["step1"], url="http://example.com")
        await e2e.run_test(test_obj)
        assert "config" in captured_config
        assert captured_config["config"].chrome_instance_path == custom_path
        monkeypatch.setattr(FakeBrowser, "__init__", original_init)

    def test_end2endtest_invalid_step_type(self):
        """Test that End2endTest raises a validation error when steps contain non-string values."""
        with pytest.raises(Exception) as excinfo:
            End2endTest(name="InvalidStep", steps=[123], url="http://example.com")
        assert "str" in str(excinfo.value)

    def test_end2endtest_model_dump_output(self):
        """Test that End2endTest.model_dump returns all expected keys."""
        test_obj = End2endTest(name="DumpTest", steps=["step1", "step2"], url="http://example.com")
        dump = test_obj.model_dump()
        expected_keys = {"steps", "url", "passed", "errored", "comment", "name"}
        assert set(dump.keys()) == expected_keys
    def test_end2endtest_non_list_steps(self):
        """Test that End2endTest raises a validation error when steps is not a list."""
        with pytest.raises(Exception) as excinfo:
            End2endTest(name="NonListSteps", steps="click button", url="http://example.com")
        assert "list" in str(excinfo.value)
    async def test_run_missing_keys_in_test(self):
        """Test that run() raises KeyError when test dictionary is missing the required 'steps' key."""
        tests_dict = {"TestMissing": {"url": "http://example.com"}}  # Missing 'steps'
        e2e = E2E(tests=tests_dict)
        with pytest.raises(KeyError):
            await e2e.run()

    async def test_debug_logging(self, monkeypatch):
        """Test that debug logging is called with the correct message during run()."""
        debug_messages = []
        logger = logging.getLogger('codebeaver')
        def fake_debug(msg, *args, **kwargs):
            debug_messages.append(msg)
        monkeypatch.setattr(logger, "debug", fake_debug)
        tests_dict = {"TestDebug": {"steps": ["step"], "url": "http://example.com"}}
        e2e = E2E(tests=tests_dict)
        await e2e.run()
        assert any("Running E2E: TestDebug" in message for message in debug_messages)
    async def test_run_preserves_order(self, tmp_path, capsys):
        """Test that the run() method returns tests in the same insertion order as provided."""
        # Change working directory so that the file is written in tmp_path
        import json
        from codebeaver.E2E import E2E, End2endTest
        import asyncio
        import os
        os.chdir(tmp_path)
        tests_dict = {}
        # Insert tests in a known order
        tests_dict["AlphaTest"] = {"steps": ["step1"], "url": "http://example.com"}
        tests_dict["BetaTest"] = {"steps": ["simulate_failure"], "url": "http://example.com"}
        e2e = E2E(tests=tests_dict)
        results = await e2e.run()
        # Check that the results are in the same order as inserted
        names = [res.name for res in results]
        assert names == list(tests_dict.keys())
        # Also check that the summary output printed the correct ratio (AlphaTest passed, BetaTest failed)
        captured = capsys.readouterr().out
        assert "1/2 E2E tests passed" in captured
    async def test_run_non_dict_raises(self):
        """Test that run() method raises an error when tests is not a dict."""
        e2e = E2E(tests=["not", "a", "dict"])
        with pytest.raises(AttributeError):
            await e2e.run()

    async def test_run_missing_url(self, monkeypatch):
        """Test that run() raises a KeyError when a test dictionary is missing the required 'url' key."""
        tests_dict = {"TestMissingURL": {"steps": ["step1"]}}  # Missing 'url' field
        e2e = E2E(tests=tests_dict)
        with pytest.raises(KeyError):
            await e2e.run()
    async def test_run_test_non_string_agent_result(self, monkeypatch):
        """Test run_test when FakeHistory.final_result returns a non-string object, expecting an exception."""
        from codebeaver.E2E import E2E, End2endTest, FakeHistory
        e2e = E2E(tests={})
        test_obj = End2endTest(name="TestNonStringResult", steps=["step1"], url="http://example.com")
        monkeypatch.setattr(FakeHistory, "final_result", lambda self: 123)
        with pytest.raises(Exception):
            await e2e.run_test(test_obj)

    async def test_fake_agent_called_count(self, monkeypatch):
        """Test that FakeAgent.__init__ is called once per test in run() method."""
        from codebeaver.E2E import E2E, FakeAgent
        call_count = 0
        original_init = FakeAgent.__init__
        def counting_init(self, task, llm, browser, controller):
            nonlocal call_count
            call_count += 1
            self.llm = llm
            self.browser = browser
            self.controller = controller
        monkeypatch.setattr(FakeAgent, "__init__", counting_init)
        tests_dict = {
            "TestOne": {"steps": ["step1"], "url": "http://example.com"},
            "TestTwo": {"steps": ["simulate_failure"], "url": "http://example.com"}
        }
        e2e = E2E(tests=tests_dict)
        await e2e.run()
        assert call_count == 2
        monkeypatch.setattr(FakeAgent, "__init__", original_init)
    async def test_run_test_empty_string_result(self, monkeypatch):
        """Test run_test returns error state when the agent returns an empty string as the result."""
        from codebeaver.E2E import E2E, End2endTest, FakeHistory
        e2e = E2E(tests={})
        test_obj = End2endTest(name="TestEmptyStringResult", steps=["empty"], url="http://example.com")
        monkeypatch.setattr(FakeHistory, "final_result", lambda self: "")
        result = await e2e.run_test(test_obj)
        assert result.errored is True
        assert result.comment == "No result from the test"
    async def test_run_ignores_extra_keys_in_test_dictionary(self, monkeypatch, tmp_path):
        """Test that extra keys in the test dictionary are ignored by E2E.run()."""
        monkeypatch.chdir(tmp_path)
        tests_dict = {
            "TestExtra": {"steps": ["step1"], "url": "http://example.com", "unused_key": "value"}
        }
        e2e = E2E(tests=tests_dict)
        results = await e2e.run()
        # Verify that the test result is processed normally despite the extra key
        assert len(results) == 1
        assert results[0].passed is True
        assert results[0].comment == "Test succeeded"

    async def test_run_test_valid_json_whitespace(self, monkeypatch):
        """Test that run_test correctly handles valid JSON output with extra whitespace."""
        e2e = E2E(tests={})
        test_obj = End2endTest(name="TestWhitespace", steps=["step1"], url="http://example.com")
        # Patch FakeHistory.final_result to simulate a valid JSON string surrounded by whitespace.
        monkeypatch.setattr(FakeHistory, "final_result", lambda self: "  " + json.dumps({"passed": True, "comment": "Test succeeded"}) + "  ")
        result = await e2e.run_test(test_obj)
        assert result.passed is True
        assert result.comment == "Test succeeded"
    def test_end2endtest_invalid_url_type(self):
        """Test that End2endTest raises a validation error when url is not a string."""
        with pytest.raises(Exception) as excinfo:
            End2endTest(name="InvalidURLType", steps=["step1"], url=123)
        assert "str" in str(excinfo.value)

    async def test_run_test_browser_constructor_exception(self, monkeypatch):
        """Test that run_test propagates an exception if the Browser constructor fails."""
        monkeypatch.setattr("codebeaver.E2E.Browser.__init__", lambda self, config: (_ for _ in ()).throw(Exception("Browser init error")))
        e2e = E2E(tests={})
        test_obj = End2endTest(name="TestBrowserInitError", steps=["step1"], url="http://example.com")
        with pytest.raises(Exception, match="Browser init error"):
            await e2e.run_test(test_obj)
    async def test_run_none_tests(self):
        """Test that run() raises an error when tests is None."""
        e2e = E2E(tests=None)
        with pytest.raises(AttributeError):
            await e2e.run()

    async def test_env_variable_empty(self, monkeypatch):
        """Test that when CHROME_INSTANCE_PATH is set to an empty string, the default path is used."""
        monkeypatch.setenv("CHROME_INSTANCE_PATH", "")
        e2e = E2E(tests={})
    async def test_agent_exception_browser_not_closed(self, monkeypatch):
        """Test that when Agent.run raises an exception, the browser's close method is not called."""
        captured_browser = {}
        from codebeaver.E2E import E2E, End2endTest, FakeBrowser
        # Patch FakeBrowser.__init__ to capture the created instance
        original_init = FakeBrowser.__init__
        def new_init(self, config):
            captured_browser["instance"] = self
            original_init(self, config)
        monkeypatch.setattr(FakeBrowser, "__init__", new_init)
        # Patch Agent.run to raise an exception so that browser.close() is never reached
        monkeypatch.setattr("codebeaver.E2E.Agent.run", lambda self: (_ for _ in ()).throw(Exception("Agent error")))
        e2e = E2E(tests={})
        test_obj = End2endTest(name="TestAgentException", steps=["step1"], url="http://example.com")
        import pytest
        with pytest.raises(Exception, match="Agent error"):
            await e2e.run_test(test_obj)
        # Verify that the captured FakeBrowser instance was created and its close method was not called
        assert "instance" in captured_browser, "Expected FakeBrowser instance to have been created"
        assert captured_browser["instance"].closed is False, "Expected the browser not to be closed when Agent.run fails"
        # Restore the original FakeBrowser.__init__
        monkeypatch.setattr(FakeBrowser, "__init__", original_init)
        assert e2e.chrome_instance_path == "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"