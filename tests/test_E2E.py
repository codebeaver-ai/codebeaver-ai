import asyncio
import json
import os
import pytest
from pydantic import ValidationError

from codebeaver.E2E import E2E, End2endTest
from browser_use.browser.context import BrowserContextConfig

# Fake classes to simulate Browser and Agent behavior
class FakeBrowser:
    def __init__(self, config):
        self.config = config
        with open(Path.cwd() / ".codebeaver/e2e.json", "w") as f:
            json.dump([test.model_dump() for test in all_tests], f)
        passed_count = sum(1 for test in all_tests if test.passed and not test.errored)
        print(f"{passed_count}/{len(all_tests)} E2E tests passed")
        return all_tests
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
        assert "1/3 E2E tests passed" in captured
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
    async def test_run_missing_fields_in_tests(self):
        """Test that run method raises KeyError when test dictionary is missing required fields."""
        tests_dict = {
            "TestMissing": {"url": "http://example.com"}  # missing "steps" key intentionally
        }
        e2e = E2E(tests=tests_dict)
        with pytest.raises(KeyError):
            await e2e.run()

    @pytest.mark.asyncio
    async def test_gitutils_called(self, monkeypatch):
        """Test that GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore is called in run_test."""
        call_count = 0
        def fake_gitutils():
            nonlocal call_count
            call_count += 1
        monkeypatch.setattr("codebeaver.E2E.GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore", fake_gitutils)
        e2e = E2E(tests={})
        test_obj = End2endTest(name="TestGitUtils", steps=["step1"], url="http://example.com")
        await e2e.run_test(test_obj)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_logging_debug_output(self, monkeypatch, caplog, tmp_path):
        """Test that debug logging output is generated during run method execution."""
        # set logger level to DEBUG
        import logging
        logger_instance = logging.getLogger("codebeaver")
        logger_instance.setLevel("DEBUG")
        monkeypatch.chdir(tmp_path)
        tests_dict = {"TestLog": {"steps": ["step1"], "url": "http://example.com"}}
        e2e = E2E(tests=tests_dict)
        await e2e.run()
        debug_messages = [record.message for record in caplog.records if record.levelname == "DEBUG"]
        # Check that at least one debug message contains "Running E2E"
        assert any("Running E2E:" in message for message in debug_messages)
    async def test_run_test_browser_init_exception(self, monkeypatch):
        """Test that run_test propagates exception when Browser.__init__ raises an error."""
        def faulty_browser_init(self, config):
            raise Exception("Browser initialization error")
        monkeypatch.setattr("codebeaver.E2E.Browser.__init__", faulty_browser_init)
        e2e = E2E(tests={})
        test_obj = End2endTest(name="TestBrowserInitException", steps=["step1"], url="http://example.com")
        with pytest.raises(Exception, match="Browser initialization error"):
            await e2e.run_test(test_obj)
    @pytest.mark.asyncio
    async def test_run_test_context_config_error(self, monkeypatch):
        """Test that run_test propagates an exception when BrowserContextConfig initialization fails."""
        # Monkey-patch BrowserContextConfig.__init__ to simulate an initialization error
        monkeypatch.setattr(BrowserContextConfig, "__init__", lambda self, *args, **kwargs: (_ for _ in ()).throw(Exception("Config error")))
        e2e = E2E(tests={})
        test_obj = End2endTest(name="TestContextConfigError", steps=["step1"], url="http://example.com")
        with pytest.raises(Exception, match="Config error"):
            await e2e.run_test(test_obj)
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_run_aborts_on_exception(self, monkeypatch, tmp_path):
        """Test that the run method aborts immediately if any test execution raises an exception and no output file is written."""
        monkeypatch.chdir(tmp_path)
        tests_dict = {
            "TestAbort": {"steps": ["trigger_exception"], "url": "http://example.com"}
        }
        e2e = E2E(tests=tests_dict)
        # Monkey-patch run_test to always throw an exception so that run() aborts.
        monkeypatch.setattr(e2e, "run_test", lambda test: (_ for _ in ()).throw(Exception("Test failure")))
        with pytest.raises(Exception, match="Test failure"):
            await e2e.run()
        from pathlib import Path
        output_file = Path.cwd() / ".codebeaver" / "e2e.json"
        assert not output_file.exists(), "Output file should not exist when run() aborts due to an exception."

    @pytest.mark.asyncio
    async def test_run_twice(self, monkeypatch, tmp_path):
        """Test that running the E2E.run() method twice overwrites the output file each time."""
        from pathlib import Path
        monkeypatch.chdir(tmp_path)
        tests_dict = {
            "TestRepeat": {"steps": ["step1"], "url": "http://example.com"}
        }
        e2e = E2E(tests=tests_dict)
        # First run of the tests triggers creation of the output file.
        results_first = await e2e.run()
        output_path = Path.cwd() / ".codebeaver" / "e2e.json"
        assert output_path.exists(), "The e2e.json file should exist after the first run."
        with open(output_path, "r") as f:
            data_first = json.load(f)
        assert isinstance(data_first, list)
        assert len(data_first) == 1, "Expected one test result in the output file after the first run."
        # Second run – the file should be overwritten, not appended.
        results_second = await e2e.run()
        with open(output_path, "r") as f:
            data_second = json.load(f)
        assert isinstance(data_second, list)
        assert len(data_second) == 1, "Expected one test result in the output file after the second run."
        # Verify that the test result remains as expected—the fake agent always returns success.
        assert data_second[0]["comment"] == "Test succeeded"
        assert data_second[0]["comment"] == "Test succeeded"
    @pytest.mark.asyncio
    async def test_e2e_directory_created(self, monkeypatch, tmp_path):
        """Test that the .codebeaver directory is created by GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore during run_test."""
        import os
        from pathlib import Path
        monkeypatch.chdir(tmp_path)
        # Monkey-patch the GitUtils function to create the .codebeaver directory when run_test is called.
        monkeypatch.setattr("codebeaver.E2E.GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore", lambda: os.makedirs(Path.cwd() / ".codebeaver", exist_ok=True))
        from codebeaver.E2E import E2E, End2endTest
        # Create a simple test definition; note that run_test expects an End2endTest instance.
        e2e = E2E(tests={"TestCreate": {"steps": ["step1"], "url": "http://example.com"}})
        test_obj = End2endTest(name="TestCreate", steps=["step1"], url="http://example.com")
        await e2e.run_test(test_obj)
        assert (Path.cwd() / ".codebeaver").exists(), "Expected .codebeaver directory to be created"
    @pytest.mark.asyncio
    async def test_gitutils_exception(self, monkeypatch):
        """Test that run_test propagates an exception when GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore fails."""
        monkeypatch.setattr("codebeaver.E2E.GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore", lambda: (_ for _ in ()).throw(Exception("GitUtils error")))
        e2e = E2E(tests={})
        test_obj = End2endTest(name="TestGitUtilsError", steps=["step1"], url="http://example.com")
        with pytest.raises(Exception, match="GitUtils error"):
            await e2e.run_test(test_obj)
    async def test_browser_context_config_values(self, monkeypatch, tmp_path):
        """Test that BrowserContextConfig is initialized with the correct save and trace paths."""
        from pathlib import Path
        # Import BrowserContext here as it is needed to capture its config argument.
        from browser_use.browser.context import BrowserContext
        # Prepare a container to capture the config values.
        captured_config = {}
        original_init = BrowserContext.__init__
        def fake_init(self, browser, config):
            captured_config['save_recording_path'] = config.save_recording_path
            captured_config['trace_path'] = config.trace_path
        monkeypatch.setattr(BrowserContext, "__init__", fake_init)
        # Change current directory to tmp_path so that Path.cwd() returns tmp_path.
        monkeypatch.chdir(tmp_path)
        tests_dict = {"TestDummy": {"steps": ["step1"], "url": "http://example.com"}}
        from codebeaver.E2E import E2E, End2endTest
        e2e = E2E(tests=tests_dict)
        test_obj = End2endTest(name="TestDummy", steps=["step1"], url="http://example.com")
        # Run the test (we are not interested in the actual outcome here, only the underlying config)
        await e2e.run_test(test_obj)
        expected_path = Path(tmp_path) / ".codebeaver"
        assert captured_config.get('save_recording_path') == expected_path
        assert captured_config.get('trace_path') == expected_path
        # Restore the original BrowserContext.__init__
        monkeyatch.setattr(BrowserContext, "__init__", original_init)
    @pytest.mark.asyncio
    async def test_run_results_order(self, monkeypatch, tmp_path):
        """Test that run() returns test results in the same order as the input tests dictionary."""
        monkeypatch.chdir(tmp_path)
        tests_dict = {
            "first": {"steps": ["step1"], "url": "http://example.com"},
            "second": {"steps": ["step2"], "url": "http://example.com"},
            "third": {"steps": ["step3"], "url": "http://example.com"}
        }
        e2e = E2E(tests=tests_dict)
        results = await e2e.run()
        order = [res.name for res in results]
        assert order == ["first", "second", "third"]

    @pytest.mark.asyncio
    async def test_agent_llm_parameter(self, monkeypatch):
        """Test that the ChatOpenAI instance with model 'gpt-4o' is passed to the Agent."""
        from langchain_openai import ChatOpenAI
        captured_llm = []
        original_init = FakeAgent.__init__
        def new_init(self, task, llm, browser, controller):
            captured_llm.append(llm)
            self.task = task
            self.llm = llm
            self.browser = browser
            self.controller = controller
        monkeypatch.setattr(FakeAgent, "__init__", new_init)
        e2e = E2E(tests={"TestLLM": {"steps": ["step1"], "url": "http://example.com"}})
        await e2e.run_test(End2endTest(name="TestLLM", steps=["step1"], url="http://example.com"))
        assert captured_llm, "Expected llm to be captured in Agent.__init__"
        llm_instance = captured_llm[0]
        assert hasattr(llm_instance, "model"), "Expected llm to have attribute 'model'"
        assert llm_instance.model == "gpt-4o"
        monkeypatch.setattr(FakeAgent, "__init__", original_init)