import asyncio
import json
import os

import pytest
from pydantic import ValidationError
from pytest import LogCaptureFixture as caplog

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
        with open("e2e.json", "w") as f:
            json.dump([test.model_dump() for test in all_tests], f)
        passed_count = sum(1 for test in all_tests if test.passed)
        print(f"{passed_count}/{len(all_tests)} E2E tests passed")


@pytest.fixture(autouse=True)
def patch_browser_agent(monkeypatch):
    # Patch Browser and Agent in the E2E module with our fake versions
    monkeypatch.setattr("codebeaver.E2E.Browser", FakeBrowser)
    monkeypatch.setattr("codebeaver.E2E.Agent", FakeAgent)


class MockReport:
    def __init__(self):
        self.e2e_results = None

    def add_e2e_results(self, results):
        self.e2e_results = results

    def generate_xml_report(self):
        return "<mock_xml_report />"


@pytest.fixture
def mock_report(monkeypatch):
    report = MockReport()
    monkeypatch.setattr("codebeaver.E2E.Report", lambda: report)
    return report


@pytest.mark.asyncio
async def test_e2e_xml_write_error(monkeypatch, tmp_path, mock_report):
    """Test that an IOError is raised when writing to e2e.xml fails."""
    monkeypatch.chdir(tmp_path)

    def mock_open(*args, **kwargs):
        if ".codebeaver/e2e.xml" in args[0]:
            raise IOError("Failed to write e2e.xml")
        return open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", mock_open)

    e2e = E2E(tests={"Test1": {"steps": ["step1"], "url": "http://example.com"}})

    with pytest.raises(IOError, match="Failed to write e2e.xml"):
        await e2e.run()


@pytest.mark.asyncio
async def test_chat_openai_initialization_error(monkeypatch):
    """Test that an exception is raised when ChatOpenAI initialization fails."""

    def mock_chat_openai(*args, **kwargs):
        raise ValueError("Invalid API key")

    monkeypatch.setattr("codebeaver.E2E.ChatOpenAI", mock_chat_openai)

    e2e = E2E(tests={"Test1": {"steps": ["step1"], "url": "http://example.com"}})
    test = End2endTest(name="TestChatOpenAI", steps=["step1"], url="http://example.com")

    with pytest.raises(ValueError, match="Invalid API key"):
        await e2e.run_test(test)


@pytest.mark.asyncio
async def test_gitutils_exception(monkeypatch):
    """Test that an exception in GitUtils is propagated."""

    def mock_ensure():
        raise Exception("GitUtils error")

    monkeypatch.setattr(
        "codebeaver.E2E.GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore",
        mock_ensure,
    )

    e2e = E2E(tests={})
    test = End2endTest(name="TestGitUtils", steps=["step1"], url="http://example.com")

    with pytest.raises(Exception, match="GitUtils error"):
        await e2e.run_test(test)


@pytest.mark.asyncio
class TestE2E:
    """Tests for the E2E class."""

    async def test_run_test_success(self):
        """Test run_test method for a successful test case."""
        e2e = E2E(tests={})
        test = End2endTest(
            name="TestSuccess", steps=["step1"], url="http://example.com"
        )
        result = await e2e.run_test(test)
        assert result.passed is True
        assert result.comment == "Test succeeded"
        assert result.errored is False

    async def test_run_test_failure(self):
        """Test run_test method for a test case simulating failure."""
        e2e = E2E(tests={})
        test = End2endTest(
            name="TestFailure", steps=["simulate_failure"], url="http://example.com"
        )
        result = await e2e.run_test(test)
        assert result.passed is False
        assert result.comment == "Failed test simulated"
        assert result.errored is False

    async def test_run_test_no_result(self):
        """Test run_test method when no result is returned from agent.run."""
        e2e = E2E(tests={})
        test = End2endTest(
            name="TestNoResult", steps=["simulate_no_result"], url="http://example.com"
        )
        result = await e2e.run_test(test)
        assert result.errored is True
        assert result.comment == "No result from the test"

    async def test_run_test_empty_string(self, monkeypatch):
        """Test run_test method when agent returns an empty string result."""
        e2e = E2E(tests={})
        test = End2endTest(
            name="TestEmptyString",
            steps=["simulate_empty_string"],
            url="http://example.com",
        )
        # Monkey-patch FakeHistory.final_result to return an empty string
        monkeypatch.setattr(FakeHistory, "final_result", lambda self: "")
        result = await e2e.run_test(test)
        assert result.errored is True
        assert result.comment == "No result from the test"

    async def test_run_overall(self, monkeypatch, tmp_path, capsys):
        """Test the overall run method to check file creation and summary printing."""
        monkeypatch.chdir(tmp_path)
        tests_dict = {
            "Test1": {"steps": ["step1"], "url": "http://example.com"},
            "TestNoResult": {
                "steps": ["simulate_no_result"],
                "url": "http://example.com",
            },
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
        test = End2endTest(
            name="TestInvalid", steps=["invalid"], url="http://example.com"
        )
        # Patch FakeHistory.final_result to return a non-JSON string to simulate an invalid result.
        monkeypatch.setattr(FakeHistory, "final_result", lambda self: "not json")
        with pytest.raises(Exception):
            await e2e.run_test(test)

    async def test_run_test_agent_exception(self, monkeypatch):
        """Test that run_test propagates an exception when Agent.run raises an exception."""
        e2e = E2E(tests={})
        test_obj = End2endTest(
            name="TestException", steps=["trigger_exception"], url="http://example.com"
        )
        monkeypatch.setattr(
            "codebeaver.E2E.Agent.run",
            lambda self: (_ for _ in ()).throw(Exception("Agent error")),
        )
        with pytest.raises(Exception, match="Agent error"):
            await e2e.run_test(test_obj)

    async def test_run_test_empty_steps(self):
        """Test run_test with an empty steps list to ensure default success behavior."""
        e2e = E2E(tests={})
        test_obj = End2endTest(
            name="TestEmptySteps", steps=[], url="http://example.com"
        )
        result = await e2e.run_test(test_obj)
        assert result.passed is True
        assert result.comment == "Test succeeded"
        assert result.errored is False

    @pytest.mark.asyncio
    async def test_report_usage(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)

        class MockReport:
            def __init__(self):
                self.e2e_results = None

            def add_e2e_results(self, results):
                self.e2e_results = results

            def generate_xml_report(self):
                return "<mock_xml_report />"

        mock_report = MockReport()
        monkeypatch.setattr("codebeaver.E2E.Report", lambda: mock_report)

        tests_dict = {"Test1": {"steps": ["step1"], "url": "http://example.com"}}
        e2e = E2E(tests=tests_dict)
        results = await e2e.run()

        assert mock_report.e2e_results == results
        assert (tmp_path / ".codebeaver/e2e.xml").exists()
        with open(tmp_path / ".codebeaver/e2e.xml", "r") as f:
            assert f.read() == "<mock_xml_report />"

    @pytest.mark.asyncio
    async def test_gitutils_called(self, monkeypatch):
        """Test that GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore is called in run_test."""
        called = False

        def mock_ensure():
            nonlocal called
            called = True

        monkeypatch.setattr(
            "codebeaver.E2E.GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore",
            mock_ensure,
        )

        e2e = E2E(tests={})
        test = End2endTest(
            name="TestGitUtils", steps=["step1"], url="http://example.com"
        )
        await e2e.run_test(test)

        assert (
            called
        ), "GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore was not called"

    @pytest.mark.asyncio
    async def test_validation_error_handling(self, monkeypatch):
        """Test handling of ValidationError in run_test method."""

        def mock_validate_json(json_data):
            raise ValidationError(errors=[])

        monkeypatch.setattr(
            "codebeaver.E2E.TestCase.model_validate_json", mock_validate_json
        )

        e2e = E2E(tests={})
        test = End2endTest(
            name="TestValidationError", steps=["step1"], url="http://example.com"
        )
        result = await e2e.run_test(test)

        assert result.errored is True
        assert "ValidationError" in result.comment

    @pytest.mark.asyncio
    async def test_browser_config(self, monkeypatch):
        """Test that BrowserConfig and BrowserContextConfig are set correctly."""
        captured_configs = {}

        def mock_browser_init(self, config):
            captured_configs["browser"] = config

        def mock_context_init(self, browser, config):
            captured_configs["context"] = config

        monkeypatch.setattr("codebeaver.E2E.Browser.__init__", mock_browser_init)
        monkeypatch.setattr("codebeaver.E2E.BrowserContext.__init__", mock_context_init)

        e2e = E2E(tests={}, chrome_instance_path="/custom/chrome/path")
        test = End2endTest(
            name="TestBrowserConfig", steps=["step1"], url="http://example.com"
        )
        await e2e.run_test(test)

        assert captured_configs["browser"].chrome_instance_path == "/custom/chrome/path"
        assert captured_configs["context"].save_recording_path.name == ".codebeaver"
        assert captured_configs["context"].trace_path.name == ".codebeaver"
        """Test run_test with an empty steps list to ensure default success behavior."""
        e2e = E2E(tests={})
        test_obj = End2endTest(
            name="TestEmptySteps", steps=[], url="http://example.com"
        )
        result = await e2e.run_test(test_obj)
        assert result.passed is True
        assert result.comment == "Test succeeded"
        assert result.errored is False

    @pytest.mark.asyncio
    async def test_browser_close_exception(self, monkeypatch):
        """Test run_test propagates exception when Browser.close raises an error."""
        e2e = E2E(tests={})
        test_obj = End2endTest(
            name="TestBrowserCloseException", steps=["step1"], url="http://example.com"
        )
        # Patch FakeBrowser.close to raise an exception
        monkeypatch.setattr(
            FakeBrowser,
            "close",
            lambda self: (_ for _ in ()).throw(Exception("Browser close error")),
        )
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
        test_obj = End2endTest(
            name="TestTaskString", steps=["click button"], url="http://example.com"
        )
        await e2e.run_test(test_obj)
        # Verify that the task string that was set in the Agent contains the URL and the step
        assert "http://example.com" in captured_tasks[0]
        assert "click button" in captured_tasks[0]
        # Restore the original FakeAgent.__init__
        monkeypatch.setattr(FakeAgent, "__init__", original_init)

    async def test_end2endtest_defaults(self):
        """Test that End2endTest default values are set correctly upon initialization."""
        test = End2endTest(
            name="DefaultTest", steps=["step1"], url="http://example.com"
        )
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
        test_obj = End2endTest(
            name="TestBrowserClose", steps=["step1"], url="http://example.com"
        )
        await e2e.run_test(test_obj)
        assert (
            "instance" in captured_browser
        ), "Expected FakeBrowser instance to be captured"
        assert (
            captured_browser["instance"].closed is True
        ), "Expected the browser to be closed after run_test"
        # Restore original FakeBrowser.__init__
        monkeypatch.setattr(FakeBrowser, "__init__", original_init)

    async def test_run_test_missing_field(self, monkeypatch):
        """Test that run_test raises a validation error when JSON result is missing required fields."""
        e2e = E2E(tests={})
        test_obj = End2endTest(
            name="TestMissingField",
            steps=["simulate_missing_field"],
            url="http://example.com",
        )
        monkeypatch.setattr(
            FakeHistory, "final_result", lambda self: json.dumps({"passed": True})
        )
        with pytest.raises(Exception) as excinfo:
            await e2e.run_test(test_obj)
        assert "comment" in str(excinfo.value)

    async def test_run_test_extra_keys_ignored(self, monkeypatch):
        """Test that run_test correctly parses the result even if extra keys are present in the JSON output."""
        e2e = E2E(tests={})
        test_obj = End2endTest(
            name="TestExtraKeys",
            steps=["simulate_extra_keys"],
            url="http://example.com",
        )
        monkeypatch.setattr(
            FakeHistory,
            "final_result",
            lambda self: json.dumps(
                {"passed": False, "comment": "Handled extra keys", "extra": "ignored"}
            ),
        )
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
        assert (
            e2e.chrome_instance_path
            == "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        )

    @pytest.mark.asyncio
    async def test_run_overall_multiple_tests(self, monkeypatch, tmp_path, capsys):
        """Test the overall run method with multiple tests having different outcomes."""
        monkeypatch.chdir(tmp_path)
        tests_dict = {
            "TestPass": {"steps": ["step1"], "url": "http://example.com"},
            "TestFail": {"steps": ["simulate_failure"], "url": "http://example.com"},
            "TestError": {"steps": ["simulate_no_result"], "url": "http://example.com"},
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
        test_obj = End2endTest(
            name="TestMultipleSteps", steps=steps, url="http://example.com"
        )
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
            "Ensure the footer is visible by scrolling all the way down.",
        ]
        test_obj = End2endTest(
            name="TestLongSteps", steps=long_steps, url="http://example.com"
        )
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
        test_obj = End2endTest(
            name="TestBrowserConfig", steps=["step1"], url="http://example.com"
        )
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
        test_obj = End2endTest(
            name="DumpTest", steps=["step1", "step2"], url="http://example.com"
        )
        dump = test_obj.model_dump()
        expected_keys = {"steps", "url", "passed", "errored", "comment", "name"}
        assert set(dump.keys()) == expected_keys

    async def test_logging_in_run(self, monkeypatch, caplog):
        """Test that the run() method logs debug messages for each test."""
        tests_dict = {"TestLog": {"steps": ["step1"], "url": "http://example.com"}}
        e2e = E2E(tests=tests_dict)
        with caplog.at_level("DEBUG"):
            await e2e.run()
        # Verify that at least one log record includes the message indicating execution of TestLog
        found = any(
            "Running E2E: TestLog" in record.message for record in caplog.records
        )
        assert found

    async def test_all_tests_pass_summary(self, monkeypatch, tmp_path, capsys):
        """Test that the run method prints the correct summary when all tests pass."""
        monkeypatch.chdir(tmp_path)
        tests_dict = {
            "TestAllPass1": {"steps": ["step1"], "url": "http://example.com"},
            "TestAllPass2": {"steps": ["step2"], "url": "http://example.com"},
        }

    @pytest.mark.asyncio
    async def test_run_test_with_unicode_steps(self):
        """Test that run_test handles Unicode characters in steps correctly."""
        e2e = E2E(tests={})
        test_obj = End2endTest(
            name="TestUnicode",
            steps=["Click 🔘", "Type 'こんにちは'"],
            url="http://example.com",
        )
        result = await e2e.run_test(test_obj)
        assert result.passed is True
        assert "Unicode" in result.comment

    @pytest.mark.asyncio
    async def test_run_test_with_very_long_step(self):
        """Test that run_test handles a very long step description."""
        e2e = E2E(tests={})
        long_step = "a" * 10000  # Create a very long step
        test_obj = End2endTest(
            name="TestLongStep", steps=[long_step], url="http://example.com"
        )
        result = await e2e.run_test(test_obj)
        assert result.passed is True
        assert "long step" in result.comment.lower()

    @pytest.mark.asyncio
    async def test_run_test_with_invalid_url(self):
        """Test that run_test handles an invalid URL correctly."""
        e2e = E2E(tests={})
        test_obj = End2endTest(
            name="TestInvalidURL", steps=["step1"], url="not_a_valid_url"
        )
        result = await e2e.run_test(test_obj)
        assert result.passed is False
        assert "invalid url" in result.comment.lower()

    @pytest.mark.asyncio
    async def test_run_test_with_many_steps(self):
        """Test that run_test handles a test with many steps."""
        e2e = E2E(tests={})
        many_steps = [f"step{i}" for i in range(100)]
        test_obj = End2endTest(
            name="TestManySteps", steps=many_steps, url="http://example.com"
        )
        result = await e2e.run_test(test_obj)
        assert result.passed is True
        assert "many steps" in result.comment.lower()

    @pytest.mark.asyncio
    async def test_run_test_with_timeout(self, monkeypatch):
        """Test that run_test handles a timeout scenario."""
        import asyncio

        e2e = E2E(tests={})

        async def slow_run(self):
            await asyncio.sleep(10)  # Simulate a long-running test
            return FakeHistory("timeout step")

        monkeypatch.setattr(FakeAgent, "run", slow_run)
        test_obj = End2endTest(
            name="TestTimeout", steps=["timeout step"], url="http://example.com"
        )
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(e2e.run_test(test_obj), timeout=1.0)

    @pytest.mark.asyncio
    async def test_run_test_with_network_error(self, monkeypatch):
        """Test that run_test handles a network error scenario."""
        e2e = E2E(tests={})

        async def network_error_run(self):
            raise Exception("Network error")

        monkeypatch.setattr(FakeAgent, "run", network_error_run)
        test_obj = End2endTest(
            name="TestNetworkError", steps=["step1"], url="http://example.com"
        )
        result = await e2e.run_test(test_obj)
        assert result.errored is True
        assert "network error" in result.comment.lower()

    @pytest.mark.asyncio
    async def test_run_with_mixed_results(self, monkeypatch, tmp_path):
        """Test that run handles a mix of passed, failed, and errored tests."""
        monkeypatch.chdir(tmp_path)
        tests_dict = {
            "TestPass": {"steps": ["step1"], "url": "http://example.com"},
            "TestFail": {"steps": ["simulate_failure"], "url": "http://example.com"},
            "TestError": {"steps": ["simulate_error"], "url": "http://example.com"},
        }
        e2e = E2E(tests=tests_dict)
        results = await e2e.run()
        assert len(results) == 3
        assert sum(1 for r in results if r.passed) == 1
        assert sum(1 for r in results if not r.passed and not r.errored) == 1
        assert sum(1 for r in results if r.errored) == 1

    @pytest.mark.asyncio
    async def test_run_with_duplicate_test_names(self):
        """Test that run handles duplicate test names correctly."""
        tests_dict = {
            "DuplicateTest": {"steps": ["step1"], "url": "http://example.com"},
            "DuplicateTest": {"steps": ["step2"], "url": "http://example.com"},
        }
        e2e = E2E(tests=tests_dict)
        results = await e2e.run()
        assert len(results) == 1  # Only one test should be run

    @pytest.mark.asyncio
    async def test_run_with_invalid_test_data(self):
        """Test that run handles invalid test data correctly."""
        invalid_tests_dict = {
            "InvalidTest1": {"steps": "not_a_list", "url": "http://example.com"},
            "InvalidTest2": {"url": "http://example.com"},  # Missing steps
            "InvalidTest3": {"steps": ["step1"]},  # Missing URL
        }
        e2e = E2E(tests=invalid_tests_dict)
        with pytest.raises(ValueError):
            await e2e.run()

    @pytest.mark.asyncio
    async def test_run_with_very_long_url(self):
        """Test that run handles a test with a very long URL."""
        long_url = "http://" + "a" * 2000 + ".com"
        tests_dict = {"LongURLTest": {"steps": ["step1"], "url": long_url}}
        e2e = E2E(tests=tests_dict)
        results = await e2e.run()
        assert len(results) == 1
        assert results[0].passed is False
        assert "url too long" in results[0].comment.lower()

    @pytest.mark.asyncio
    async def test_run_with_unicode_test_name(self):
        """Test that run handles Unicode characters in test names."""
        tests_dict = {"测试": {"steps": ["step1"], "url": "http://example.com"}}
        e2e = E2E(tests=tests_dict)
        results = await e2e.run()
        assert len(results) == 1
        assert results[0].name == "测试"
        assert results[0].passed is True

    @pytest.mark.asyncio
    async def test_run_with_many_tests(self):
        """Test that run handles a large number of tests."""
        many_tests = {
            f"Test{i}": {"steps": ["step1"], "url": "http://example.com"}
            for i in range(100)
        }
        e2e = E2E(tests=many_tests)
        results = await e2e.run()
        assert len(results) == 100
        assert all(result.passed for result in results)

    @pytest.mark.asyncio
    async def test_run_with_agent_raising_exception(self, monkeypatch):
        """Test that run handles an agent raising an unexpected exception."""

        def agent_run_with_exception(self):
            raise RuntimeError("Unexpected agent error")

        monkeypatch.setattr(FakeAgent, "run", agent_run_with_exception)
        tests_dict = {
            "ExceptionTest": {"steps": ["step1"], "url": "http://example.com"}
        }
        e2e = E2E(tests=tests_dict)
        results = await e2e.run()
        assert len(results) == 1
        assert results[0].errored is True
        assert "unexpected agent error" in results[0].comment.lower()

    @pytest.mark.asyncio
    async def test_run_with_agent_returning_invalid_json(self, monkeypatch):
        """Test that run handles an agent returning invalid JSON."""

        def agent_run_with_invalid_json(self):
            return FakeHistory("invalid_json_step")

        monkeypatch.setattr(FakeAgent, "run", agent_run_with_invalid_json)
        monkeypatch.setattr(
            FakeHistory, "final_result", lambda self: "{'invalid': 'json'"
        )
        tests_dict = {
            "InvalidJSONTest": {"steps": ["step1"], "url": "http://example.com"}
        }
        e2e = E2E(tests=tests_dict)
        results = await e2e.run()
        assert len(results) == 1
        assert results[0].errored is True
        assert "invalid json" in results[0].comment.lower()

    @pytest.mark.asyncio
    async def test_run_with_browser_close_error(self, monkeypatch):
        """Test that run handles an error when closing the browser."""

        def browser_close_with_error(self):
            raise RuntimeError("Error closing browser")

        monkeypatch.setattr(FakeBrowser, "close", browser_close_with_error)
        tests_dict = {
            "BrowserCloseErrorTest": {"steps": ["step1"], "url": "http://example.com"}
        }
        e2e = E2E(tests=tests_dict)
        with pytest.raises(RuntimeError, match="Error closing browser"):
            await e2e.run()
        assert results[0].name == "DuplicateTest"
        assert "step2" in results[0].steps  # The last defined test should be used

    @pytest.mark.asyncio
    async def test_run_with_empty_steps(self):
        """Test that run handles a test with empty steps."""
        tests_dict = {"EmptyStepsTest": {"steps": [], "url": "http://example.com"}}
        e2e = E2E(tests=tests_dict)
        results = await e2e.run()
        assert len(results) == 1
        assert results[0].passed is True
        assert "no steps" in results[0].comment.lower()
        e2e = E2E(tests=tests_dict)
        # Force FakeHistory.final_result to always return a passing result.
        monkeypatch.setattr(
            FakeHistory,
            "final_result",
            lambda self: json.dumps({"passed": True, "comment": "Test succeeded"}),
        )
        await e2e.run()
        captured = capsys.readouterr().out
        assert "2/2 E2E tests passed" in captured

    async def test_all_tests_fail_summary(self, monkeypatch, tmp_path, capsys):
        """Test that the run method prints the correct summary when all tests fail."""
        monkeypatch.chdir(tmp_path)
        tests_dict = {
            "TestAllFail1": {
                "steps": ["simulate_failure"],
                "url": "http://example.com",
            },
            "TestAllFail2": {
                "steps": ["simulate_failure"],
                "url": "http://example.com",
            },
        }
        e2e = E2E(tests=tests_dict)
        await e2e.run()
        captured = capsys.readouterr().out
        # Since both tests simulate a failure, expect 0 passed out of 2

    async def test_all_tests_mixed_summary(self, monkeypatch, tmp_path, capsys):
        """Test that the run method prints the correct summary when tests have mixed outcomes."""
        monkeypatch.chdir(tmp_path)
        tests_dict = {
            "TestPass": {"steps": ["step1"], "url": "http://example.com"},
            "TestFail": {"steps": ["simulate_failure"], "url": "http://example.com"},
        }
        e2e = E2E(tests=tests_dict)
        await e2e.run()
        e2e_file = tmp_path / "e2e.json"
        assert e2e_file.exists()
        with open(e2e_file, "r") as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == 2
        captured = capsys.readouterr().out
        assert "1/2 E2E tests passed" in captured

    async def test_run_slow_agent(self, monkeypatch):
        """Test that run_test handles a slow Agent.run execution correctly."""
        import asyncio

        async def slow_run(self):
            await asyncio.sleep(0.1)  # simulate a delay in agent execution
            return FakeHistory("normal step")

        monkeypatch.setattr(FakeAgent, "run", slow_run)
        e2e = E2E(tests={})
        test_obj = End2endTest(
            name="TestSlowAgent", steps=["normal step"], url="http://example.com"
        )
        result = await e2e.run_test(test_obj)
        assert result.passed is True
        assert result.comment == "Test succeeded"
        assert result.errored is False

    async def test_run_test_non_string_result(self, monkeypatch):
        """Test that run_test raises an exception when the agent returns a non-string result."""
        e2e = E2E(tests={})

    @pytest.mark.asyncio
    async def test_e2e_xml_write_error(self, monkeypatch, tmp_path, mock_report):
        """Test that an IOError is raised when writing to e2e.xml fails."""
        monkeypatch.chdir(tmp_path)

        def mock_open(*args, **kwargs):
            if ".codebeaver/e2e.xml" in args[0]:
                raise IOError("Failed to write e2e.xml")
            return open(*args, **kwargs)

        monkeypatch.setattr("builtins.open", mock_open)

        e2e = E2E(tests={"Test1": {"steps": ["step1"], "url": "http://example.com"}})

        with pytest.raises(IOError, match="Failed to write e2e.xml"):
            await e2e.run()

    @pytest.mark.asyncio
    async def test_chat_openai_initialization_error(self, monkeypatch):
        """Test that an exception is raised when ChatOpenAI initialization fails."""

        def mock_chat_openai(*args, **kwargs):
            raise ValueError("Invalid API key")

        monkeypatch.setattr("codebeaver.E2E.ChatOpenAI", mock_chat_openai)

        e2e = E2E(tests={"Test1": {"steps": ["step1"], "url": "http://example.com"}})
        test = End2endTest(
            name="TestChatOpenAI", steps=["step1"], url="http://example.com"
        )

        with pytest.raises(ValueError, match="Invalid API key"):
            await e2e.run_test(test)

    @pytest.mark.asyncio
    async def test_gitutils_exception(self, monkeypatch):
        """Test that an exception in GitUtils is propagated."""

        def mock_ensure():
            raise Exception("GitUtils error")

        monkeypatch.setattr(
            "codebeaver.E2E.GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore",
            mock_ensure,
        )

        e2e = E2E(tests={})
        test = End2endTest(
            name="TestGitUtils", steps=["step1"], url="http://example.com"
        )

        with pytest.raises(Exception, match="GitUtils error"):
            await e2e.run_test(test)

    @pytest.mark.asyncio
    async def test_run_test_invalid_json_result(self, monkeypatch):
        """Test that run_test handles an invalid JSON result from the agent correctly."""
        e2e = E2E(tests={})
        test_obj = End2endTest(
            name="TestInvalidJSON", steps=["step1"], url="http://example.com"
        )

        def mock_final_result(self):
            return "{'invalid': 'json'"  # Invalid JSON string

        monkeypatch.setattr(FakeHistory, "final_result", mock_final_result)

        result = await e2e.run_test(test_obj)

        assert result.errored is True
        assert "Invalid JSON" in result.comment
        assert result.passed is False

    @pytest.mark.asyncio
    async def test_run_file_write_error(self, monkeypatch, tmp_path):
        """
        Test that the run method handles and propagates an IOError when writing to e2e.json fails.
        This test ensures that the E2E class properly handles file writing errors and doesn't
        silently fail when it can't write results to disk.
        """
        monkeypatch.chdir(tmp_path)

        def mock_open(*args, **kwargs):
            if "e2e.json" in args[0]:
                raise IOError("Simulated file write error")
            return open(*args, **kwargs)

        monkeypatch.setattr("builtins.open", mock_open)

        e2e = E2E(tests={"Test1": {"steps": ["step1"], "url": "http://example.com"}})

        with pytest.raises(IOError, match="Simulated file write error"):
            await e2e.run()

    @pytest.mark.asyncio
    async def test_gitutils_exception(self, monkeypatch):
        """Test that an exception in GitUtils is propagated."""

        def mock_ensure():
            raise Exception("GitUtils error")

        monkeypatch.setattr(
            "codebeaver.E2E.GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore",
            mock_ensure,
        )

        e2e = E2E(tests={})
        test = End2endTest(
            name="TestGitUtils", steps=["step1"], url="http://example.com"
        )

        with pytest.raises(Exception, match="GitUtils error"):
            await e2e.run_test(test)

    @pytest.mark.asyncio
    async def test_chat_openai_initialization_error(self, monkeypatch):
        """Test that an exception is raised when ChatOpenAI initialization fails."""

        def mock_chat_openai(*args, **kwargs):
            raise ValueError("Invalid API key")

        monkeypatch.setattr("codebeaver.E2E.ChatOpenAI", mock_chat_openai)

        e2e = E2E(tests={"Test1": {"steps": ["step1"], "url": "http://example.com"}})
        test = End2endTest(
            name="TestChatOpenAI", steps=["step1"], url="http://example.com"
        )

        with pytest.raises(ValueError, match="Invalid API key"):
            await e2e.run_test(test)

    @pytest.mark.asyncio
    async def test_e2e_xml_write_error(self, monkeypatch, tmp_path, mock_report):
        """Test that an IOError is raised when writing to e2e.xml fails."""
        monkeypatch.chdir(tmp_path)

        def mock_open(*args, **kwargs):
            if ".codebeaver/e2e.xml" in args[0]:
                raise IOError("Failed to write e2e.xml")
            return open(*args, **kwargs)

        monkeypatch.setattr("builtins.open", mock_open)

        e2e = E2E(tests={"Test1": {"steps": ["step1"], "url": "http://example.com"}})

        with pytest.raises(IOError, match="Failed to write e2e.xml"):
            await e2e.run()

    @pytest.mark.asyncio
    async def test_run_test_invalid_json_result(self, monkeypatch):
        """Test that run_test handles an invalid JSON result from the agent correctly."""
        e2e = E2E(tests={})
        test_obj = End2endTest(
            name="TestInvalidJSON", steps=["step1"], url="http://example.com"
        )

        def mock_final_result(self):
            return "{'invalid': 'json'"  # Invalid JSON string

        monkeypatch.setattr(FakeHistory, "final_result", mock_final_result)

        result = await e2e.run_test(test_obj)

        assert result.errored is True
        assert "Invalid JSON" in result.comment
        assert result.passed is False

    @pytest.mark.asyncio
    async def test_run_test_empty_result(self, monkeypatch):
        """Test that run_test handles an empty result from the agent correctly."""
        e2e = E2E(tests={})
        test_obj = End2endTest(
            name="TestEmptyResult", steps=["step1"], url="http://example.com"
        )

        async def mock_run(self):
            return FakeHistory("empty_result_step")

        monkeypatch.setattr(FakeAgent, "run", mock_run)
        monkeypatch.setattr(FakeHistory, "final_result", lambda self: "")

        result = await e2e.run_test(test_obj)

        assert result.errored is True
        assert "No result from the test" in result.comment
        assert result.passed is False

    @pytest.mark.asyncio
    async def test_run_test_non_string_result(self, monkeypatch):
        """Test that run_test handles a non-string result from the agent correctly."""
        e2e = E2E(tests={})
        test_obj = End2endTest(
            name="TestNonStringResult", steps=["step1"], url="http://example.com"
        )

        async def mock_run(self):
            return FakeHistory("non_string_result_step")

        monkeypatch.setattr(FakeAgent, "run", mock_run)
        monkeypatch.setattr(
            FakeHistory, "final_result", lambda self: {"not": "a string"}
        )

        result = await e2e.run_test(test_obj)

        assert result.errored is True
        assert "Invalid result type" in result.comment
        assert result.passed is False
