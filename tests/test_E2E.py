import asyncio
import json
import os
import pytest
from pydantic import ValidationError

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
        self.task = task
        self.llm = llm
        self.browser = browser
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
    @pytest.mark.asyncio
    async def test_run_test_with_delay(self, monkeypatch):
        """Test run_test method when the Agent's run method is delayed."""
        # Define a delayed run method that simulates latency
        async def delayed_run(self):
            await asyncio.sleep(0.01)
            return FakeHistory(self.task)
        monkeypatch.setattr(FakeAgent, "run", delayed_run)
        e2e = E2E(tests={})
        """Test that End2endTest.model_dump returns all expected keys."""
        test_obj = End2endTest(name="TestDelay", steps=["step1"], url="http://example.com")
        result = await e2e.run_test(test_obj)
        assert result.passed is True
        assert result.comment == "Test succeeded"
        # Reset the FakeAgent.run to its original behavior for other tests
        assert set(dump.keys()) == expected_keys
    @pytest.mark.asyncio
    async def test_run_test_empty_result_string(self, monkeypatch):
        """Test run_test marks the test as errored when the agent returns an empty string."""
        e2e = E2E(tests={})
        test_obj = End2endTest(name="TestEmptyResultString", steps=["step_empty"], url="http://example.com")
        # Patch FakeHistory.final_result to return an empty string
        monkeypatch.setattr(FakeHistory, "final_result", lambda self: "")
        result = await e2e.run_test(test_obj)
        assert result.errored is True
        assert result.comment == "No result from the test"

    @pytest.mark.asyncio
    async def test_run_test_null_json(self, monkeypatch):
        """Test run_test raises an exception when the agent returns JSON 'null'."""
        e2e = E2E(tests={})
        test_obj = End2endTest(name="TestNullJSON", steps=["step_null"], url="http://example.com")
        # Patch FakeHistory.final_result to return the JSON string "null"
        monkeypatch.setattr(FakeHistory, "final_result", lambda self: "null")
        with pytest.raises(Exception) as excinfo:
            await e2e.run_test(test_obj)
        # Check that the error message indicates missing fields (pydantic error)
        assert ("field required" in str(excinfo.value).lower()) or ("none is not an allowed value" in str(excinfo.value).lower())
    @pytest.mark.asyncio
    async def test_run_test_invalid_field_types(self, monkeypatch):
        """Test run_test raises an exception when agent returns JSON with fields of incorrect types."""
        e2e = E2E(tests={})
        test_obj = End2endTest(name="TestInvalidTypes", steps=["invalid types"], url="http://example.com")
        monkeypatch.setattr(FakeHistory, "final_result", lambda self: json.dumps({"passed": "yes", "comment": 123}))
        with pytest.raises(Exception):
            await e2e.run_test(test_obj)
    @pytest.mark.asyncio
    async def test_run_method_exception_in_run_test(self, monkeypatch, tmp_path):
        """Test that an exception in run_test stops the overall run execution and does not write the results file."""
        monkeypatch.chdir(tmp_path)
        tests_dict = {
            "ThrowTest": {"steps": ["raise error"], "url": "http://example.com"},
            "NormalTest": {"steps": ["step1"], "url": "http://example.com"}
        }
        e2e = E2E(tests=tests_dict)
        original_run_test = e2e.run_test
        async def new_run_test(test):
            if test.name == "ThrowTest":
                raise Exception("Forced test error")
            return await original_run_test(test)
        monkeypatch.setattr(e2e, "run_test", new_run_test)
        with pytest.raises(Exception, match="Forced test error"):
            await e2e.run()
        # Verify that the e2e.json results file was not created because an exception interrupted run()
    @pytest.mark.asyncio
    async def test_run_test_invalid_json_browser_closed(self, monkeypatch):
        """Test that even if FakeHistory.final_result returns invalid JSON, the browser is closed before the exception propagates."""
        captured_browser = []
        orig_init = FakeBrowser.__init__
        def custom_init(self, config):
            captured_browser.append(self)
            orig_init(self, config)
        monkeypatch.setattr(FakeBrowser, "__init__", custom_init)
        monkeypatch.setattr(FakeHistory, "final_result", lambda self: "not json")
        e2e = E2E(tests={})
        test_obj = End2endTest(name="TestInvalidJSONClosed", steps=["invalid"], url="http://example.com")
        with pytest.raises(Exception):
            try:
                await e2e.run_test(test_obj)
            except Exception as e:
                pass
        assert captured_browser, "Browser instance was not created."
        assert captured_browser[0].closed is True, "Browser was not closed after invalid JSON result."
        monkeypatch.setattr(FakeBrowser, "__init__", orig_init)
        assert not (tmp_path / "e2e.json").exists()
    @pytest.mark.asyncio
    async def test_run_test_empty_url(self):
        """Test run_test method with an empty URL."""
        e2e = E2E(tests={})
        test_obj = End2endTest(name="TestEmptyURL", steps=["step1"], url="")
        result = await e2e.run_test(test_obj)
        assert result.passed is True
        assert result.comment == "Test succeeded"
        assert result.errored is False

    @pytest.mark.asyncio
    async def test_run_test_whitespace_steps(self):
        """Test run_test method with steps that are whitespace strings."""
        e2e = E2E(tests={})
        test_obj = End2endTest(name="TestWhitespaceSteps", steps=["  ", "\t"], url="http://example.com")
        result = await e2e.run_test(test_obj)
        assert result.passed is True
        assert result.comment == "Test succeeded"
        assert result.errored is False

    @pytest.mark.asyncio
    async def test_run_test_empty_json_object(self, monkeypatch):
        """Test run_test method when the agent returns an empty JSON object, expecting a validation error."""
        e2e = E2E(tests={})
        test_obj = End2endTest(name="TestEmptyJSONObject", steps=["step1"], url="http://example.com")
        monkeypatch.setattr(FakeHistory, "final_result", lambda self: json.dumps({}))
        with pytest.raises(Exception):
            await e2e.run_test(test_obj)
    def test_e2e_constructor_tests_assignment(self):
        """Test that the E2E constructor correctly assigns the tests dict."""
        tests = {"SomeTest": {"steps": ["step1"], "url": "http://example.com"}}
        e2e = E2E(tests=tests)
        assert e2e.tests == tests

    @pytest.mark.asyncio
    async def test_run_invalid_test_dict(self, monkeypatch, tmp_path):
        """Test that run() raises KeyError if a test dictionary is missing a required key."""
        monkeypatch.chdir(tmp_path)
        # This test item is missing the "url" field
        tests_dict = {"TestMissingURL": {"steps": ["step1"]}}
        e2e = E2E(tests=tests_dict)
        with pytest.raises(KeyError):
            await e2e.run()

    def test_chrome_instance_path_empty_env(self, monkeypatch):
        """Test that an empty CHROME_INSTANCE_PATH environment variable does not override the default chrome_instance_path."""
        monkeypatch.setenv("CHROME_INSTANCE_PATH", "")
        e2e = E2E(tests={})
        # Since an empty string is falsy, the default should be used.
        assert e2e.chrome_instance_path == "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    @pytest.mark.asyncio
    async def test_run_overall_extra_keys_in_test_definition(self, monkeypatch, tmp_path):
        """Test that extra keys in the test definitions are ignored in the dumped JSON output."""
        monkeypatch.chdir(tmp_path)
        tests_dict = {
            "TestExtra": {"steps": ["step1"], "url": "http://example.com", "extra": "should be ignored"}
        }
        e2e = E2E(tests=tests_dict)
        results = await e2e.run()
        e2e_file = tmp_path / "e2e.json"
        with open(e2e_file, "r") as f:
            data = json.load(f)
        for test in data:
            assert set(test.keys()) == {"steps", "url", "passed", "errored", "comment", "name"}

    @pytest.mark.asyncio
    async def test_run_overall_print_format(self, monkeypatch, tmp_path, capsys):
        """Test that the run method prints the correct header and test summary format."""
        monkeypatch.chdir(tmp_path)
        tests_dict = {
            "TestA": {"steps": ["stepA"], "url": "http://example.com/A"},
            "TestB": {"steps": ["simulate_failure"], "url": "http://example.com/B"}
        }
        e2e = E2E(tests=tests_dict)
        await e2e.run()
        captured = capsys.readouterr().out
        # Check that the header is printed in the summary section.
        assert "Name" in captured
        assert "Passed" in captured
        assert "Comment" in captured
        # Check that each test name appears somewhere in the printed summary.
        assert "TestA" in captured
        assert "TestB" in captured
    @pytest.mark.asyncio
    async def test_run_overwrites_existing_file(self, monkeypatch, tmp_path):
        """Test that the run() method overwrites an existing e2e.json file.""" 
        monkeypatch.chdir(tmp_path)
        # Create a dummy e2e.json file before running
        with open("e2e.json", "w") as f:
            f.write("dummy content")
        tests_dict = {
            "TestOverwrite": {"steps": ["step1"], "url": "http://example.com"}
        }
        e2e = E2E(tests=tests_dict)
        # Run the overall tests; this should overwrite the file
        results = await e2e.run()
        # Read and check that the file no longer contains the dummy content
        with open("e2e.json", "r") as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert data != "dummy content"
        # Also verify that the dumped file contains exactly one test result
        assert len(data) == 1
    
    @pytest.mark.asyncio
    async def test_test_order_preservation(self, monkeypatch, tmp_path, capsys):
        """Test that tests are processed and dumped in the same order as defined in the tests dictionary."""
        monkeypatch.chdir(tmp_path)
        # Define tests in a specific insertion order
        tests_dict = {
            "FirstTest": {"steps": ["step1"], "url": "http://example.com/first"},
            "SecondTest": {"steps": ["step2"], "url": "http://example.com/second"},
            "ThirdTest": {"steps": ["simulate_failure"], "url": "http://example.com/third"}
        }
        e2e = E2E(tests=tests_dict)
        results = await e2e.run()
        # Read the dumped JSON to verify the order. The dumped results should have their 'name' fields in the same order.
        e2e_file = tmp_path / "e2e.json"
        with open(e2e_file, "r") as f:
            dump = json.load(f)
        dumped_order = [item["name"] for item in dump]
        expected_order = ["FirstTest", "SecondTest", "ThirdTest"]
        assert dumped_order == expected_order
        # Also check that the printed output from run() reflects the processing order
        captured = capsys.readouterr().out
        for test_name in expected_order:
            assert test_name in captured
    def test_end2endtest_invalid_steps_not_list(self):
        """Test that End2endTest raises a validation error when steps is not provided as a list."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError) as excinfo:
            End2endTest(name="InvalidStepsNotList", steps="not a list", url="http://example.com")
        assert "list" in str(excinfo.value)

    def test_end2endtest_invalid_url_type(self):
        """Test that End2endTest raises a validation error when url is not a string."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError) as excinfo:
            End2endTest(name="InvalidUrl", steps=["step1"], url=123)
        assert "str" in str(excinfo.value)