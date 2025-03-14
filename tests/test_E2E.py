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
        with open("e2e.json", "w") as f:
            json.dump([test.model_dump() for test in all_tests], f)
        passed_count = sum(1 for test in all_tests if test.passed)
        print(f"{passed_count}/{len(all_tests)} E2E tests passed")


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
        test_obj = End2endTest(
            name="TestNonStringResult",
            steps=["simulate_non_string"],
            url="http://example.com",
        )
        # Patch FakeHistory.final_result to return a non-string (integer) result
        monkeypatch.setattr(FakeHistory, "final_result", lambda self: 123)
        with pytest.raises(Exception):
            await e2e.run_test(test_obj)

    async def test_gitutils_called_in_run_test(self, monkeypatch):
        """Test that GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore is called in run_test."""
        flag = {"called": False}

        def fake_ensure():
            flag["called"] = True

        monkeypatch.setattr(
            "codebeaver.E2E.GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore",
            fake_ensure,
        )

        async def fake_run(self):
            class FakeHistory:
                def final_result(inner_self):
                    return json.dumps({"passed": True, "comment": "Test succeeded"})

            return FakeHistory()

        monkeypatch.setattr("codebeaver.E2E.Agent.run", fake_run)
        from codebeaver.E2E import E2E, End2endTest

        test_obj = End2endTest(
            name="TestGitUtils", steps=["any_step"], url="http://example.com"
        )
        e2e = E2E(tests={})
        result = await e2e.run_test(test_obj)
        assert flag["called"] is True

    async def test_report_methods_called_in_run(self, monkeypatch, tmp_path):
        """Test that Report.add_e2e_results and Report.generate_xml_report are called during run."""
        flag = {"add_called": False, "generate_called": False}

        def fake_add(self, results):
            flag["add_called"] = True

        def fake_generate(self):
            flag["generate_called"] = True
            return "fake_xml_report"

        monkeypatch.setattr("codebeaver.E2E.Report.add_e2e_results", fake_add)
        monkeypatch.setattr("codebeaver.E2E.Report.generate_xml_report", fake_generate)

        async def fake_run(self):
            class FakeHistory:
                def final_result(inner_self):
                    return json.dumps({"passed": True, "comment": "Test succeeded"})

            return FakeHistory()

        monkeypatch.setattr("codebeaver.E2E.Agent.run", fake_run)
        from codebeaver.E2E import E2E

        tests_dict = {"TestReport": {"steps": ["step1"], "url": "http://example.com"}}
        e2e = E2E(tests=tests_dict)
        monkeypatch.chdir(tmp_path)
        # Ensure the .codebeaver folder exists before writing files
        (tmp_path / ".codebeaver").mkdir()
        await e2e.run()
        xml_file = tmp_path / ".codebeaver" / "e2e.xml"
        assert xml_file.exists()
        with open(xml_file, "r") as f:
            content = f.read()
        assert content == "fake_xml_report"
        assert flag["add_called"] is True
        assert flag["generate_called"] is True

    async def test_run_invalid_test_data(self):
        """Test that run() method raises a KeyError when a test dictionary is missing required keys."""
        tests_dict = {"TestMissing": {"steps": ["step1"]}}  # Missing 'url'
        e2e = E2E(tests=tests_dict)
        with pytest.raises(KeyError):
            # run() will loop over tests and try to access test["url"] which is missing.
            await e2e.run()

    async def test_run_test_invalid_json_type(self, monkeypatch):
        """Test that run_test raises an exception when agent returns JSON with invalid type for a field."""
        e2e = E2E(tests={})
        test_obj = End2endTest(
            name="TestInvalidType",
            steps=["simulate_invalid_type"],
            url="http://example.com",
        )

        # Patch Agent.run to return a FakeHistory whose final_result returns JSON
        # with an unexpected type for the 'passed' field (string instead of bool)
        async def fake_run(self):
            class FakeHistory:
                def final_result(inner_self):
                    return json.dumps(
                        {"passed": "true", "comment": "Wrong type"}
                    )  # Invalid type for 'passed'

            return FakeHistory()

        monkeypatch.setattr("codebeaver.E2E.Agent.run", fake_run)
        with pytest.raises(Exception):
            await e2e.run_test(test_obj)

    async def test_run_test_trim_whitespace(self, monkeypatch):
        """Test run_test method with a JSON output that has extra whitespaces and newline characters."""
        e2e = E2E(tests={})
        test_obj = End2endTest(
            name="TestTrimWhitespace", steps=["step1"], url="http://example.com"
        )
        # Patch FakeHistory.final_result to return JSON with extra whitespace/newlines
        monkeypatch.setattr(
            FakeHistory,
            "final_result",
            lambda self: "  \n"
            + json.dumps({"passed": True, "comment": "Test succeeded"})
            + " \n  ",
        )
        result = await e2e.run_test(test_obj)
        assert result.passed is True
        assert result.comment == "Test succeeded"
        assert result.errored is False

    async def test_gitutils_exception_in_run_test(self, monkeypatch):
        """Test that run_test propagates an exception thrown by GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore."""
        e2e = E2E(tests={})
        test_obj = End2endTest(
            name="TestGitUtilsException", steps=["step1"], url="http://example.com"
        )
        monkeypatch.setattr(
            "codebeaver.E2E.GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore",
            lambda: (_ for _ in ()).throw(Exception("GitUtils error")),
        )
        with pytest.raises(Exception, match="GitUtils error"):
            await e2e.run_test(test_obj)

    async def test_agent_final_result_with_extra_whitespace(self, monkeypatch):
        """Test run_test method to ensure that extra whitespace in the agent result does not affect parsing."""
        e2e = E2E(tests={})
        test_obj = End2endTest(
            name="TestExtraWhitespace", steps=["step1"], url="http://example.com"
        )
        # Patch FakeHistory.final_result to return JSON output with extra whitespace/newlines
        monkeypatch.setattr(
            FakeHistory,
            "final_result",
            lambda self: " \n "
            + json.dumps({"passed": True, "comment": "Whitespace handled"})
            + " \n",
        )
        result = await e2e.run_test(test_obj)
        assert result.passed is True
        assert result.comment == "Whitespace handled"
        assert result.errored is False

    async def test_run_test_final_result_dict(self, monkeypatch):
        """Test run_test raises an exception when agent final_result returns a dict instead of a JSON string."""
        e2e = E2E(tests={})
        test_obj = End2endTest(
            name="TestDictFinalResult",
            steps=["simulate_dict"],
            url="http://example.com",
        )
        # Monkey-patch FakeHistory.final_result to return a dictionary instead of JSON text.
        monkeypatch.setattr(
            FakeHistory,
            "final_result",
            lambda self: {"passed": True, "comment": "Dict result"},
        )
        with pytest.raises(Exception):
            await e2e.run_test(test_obj)

    async def test_browser_context_config(self, monkeypatch):
        """Test that BrowserContext is initialized with the correct configuration paths."""
        captured_config = {}

        # Patch FakeAgent.__init__ to capture the browser_context configuration passed to it.
        def fake_agent_init(self, task, llm, browser_context, controller):
            captured_config["save_recording_path"] = (
                browser_context.config.save_recording_path
            )
            captured_config["trace_path"] = browser_context.config.trace_path
            self.task = task
            self.llm = llm
            self.browser_context = browser_context
            self.controller = controller

        monkeypatch.setattr(FakeAgent, "__init__", fake_agent_init)
        # Execute run_test to trigger agent initialization.
        e2e = E2E(tests={})
        test_obj = End2endTest(
            name="TestBrowserContext", steps=["step1"], url="http://example.com"
        )
        await e2e.run_test(test_obj)
        from pathlib import Path

        expected_path = Path.cwd() / ".codebeaver/"
        assert captured_config.get("save_recording_path") == expected_path
        assert captured_config.get("trace_path") == expected_path

    async def test_run_report_generate_exception(self, monkeypatch, tmp_path):
        """Test that run() propagates an exception if Report.generate_xml_report throws an error."""
        monkeypatch.chdir(tmp_path)
        tests_dict = {
            "TestReportGenerate": {"steps": ["step1"], "url": "http://example.com"}
        }
        e2e = E2E(tests=tests_dict)
        # Ensure .codebeaver directory exists
        (tmp_path / ".codebeaver").mkdir(exist_ok=True)
        from codebeaver.E2E import Report

        monkeypatch.setattr(
            Report,
            "generate_xml_report",
            lambda self: (_ for _ in ()).throw(Exception("Generate error")),
        )
        with pytest.raises(Exception, match="Generate error"):
            await e2e.run()

    async def test_run_report_add_exception(self, monkeypatch, tmp_path):
        """Test that run() propagates an exception if Report.add_e2e_results throws an error."""
        monkeypatch.chdir(tmp_path)
        tests_dict = {
            "TestReportAdd": {"steps": ["step1"], "url": "http://example.com"}
        }
        e2e = E2E(tests=tests_dict)
        (tmp_path / ".codebeaver").mkdir(exist_ok=True)
        from codebeaver.E2E import Report

        monkeypatch.setattr(
            Report,
            "add_e2e_results",
            lambda self, results: (_ for _ in ()).throw(Exception("Add error")),
        )
        with pytest.raises(Exception, match="Add error"):
            await e2e.run()

    async def test_run_test_empty_json_object(self, monkeypatch):
        """Test that run_test raises an exception when agent returns an empty JSON object."""
        e2e = E2E(tests={})
        test_obj = End2endTest(
            name="TestEmptyJSONObject", steps=["dummy"], url="http://example.com"
        )
        monkeypatch.setattr(FakeHistory, "final_result", lambda self: "{}")
        with pytest.raises(Exception):
            await e2e.run_test(test_obj)

    async def test_agent_task_string_empty_steps(self, monkeypatch):
        """Test that the Agent task string is correctly formatted when steps list is empty."""
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
            name="TestEmptyStepsTaskString", steps=[], url="http://example.com"
        )
        await e2e.run_test(test_obj)
        expected_task = (
            f"You are a QA tester. Follow these steps:\n* Go to {test_obj.url}\n"
        )
        assert captured_tasks[0] == expected_task
        monkeypatch.setattr(FakeAgent, "__init__", original_init)

    async def test_run_test_comment_wrong_type(self, monkeypatch):
        """Test that run_test raises an exception when the 'comment' field has a wrong type (non-string)."""
        e2e = E2E(tests={})
        test_obj = End2endTest(
            name="TestWrongCommentType", steps=["dummy"], url="http://example.com"
        )
        monkeypatch.setattr(
            FakeHistory,
            "final_result",
            lambda self: json.dumps({"passed": True, "comment": 123}),
        )
        with pytest.raises(Exception):
            await e2e.run_test(test_obj)

    @pytest.mark.asyncio
    async def test_run_test_json_list(self, monkeypatch):
        """Test run_test raises an exception when agent returns a JSON list instead of an object."""
        e2e = E2E(tests={})
        test_obj = End2endTest(
            name="TestJSONList", steps=["simulate_list"], url="http://example.com"
        )
        monkeypatch.setattr(FakeHistory, "final_result", lambda self: "[]")
        with pytest.raises(Exception):
            await e2e.run_test(test_obj)

    @pytest.mark.asyncio
    async def test_run_test_whitespace_only(self, monkeypatch):
        """Test run_test raises an exception when agent returns a string consisting only of whitespace."""
        e2e = E2E(tests={})
        test_obj = End2endTest(
            name="TestWhitespaceOnly",
            steps=["simulate_whitespace"],
            url="http://example.com",
        )
        monkeypatch.setattr(FakeHistory, "final_result", lambda self: "     ")
        with pytest.raises(Exception):
            await e2e.run_test(test_obj)

    async def test_e2e_initialization(self, monkeypatch):
        """Test that E2E initializes with given tests and sets chrome_instance_path correctly."""
        tests_dict = {"TestInit": {"steps": ["dummy"], "url": "http://example.com"}}
        # Remove the environment variable if set
        monkeypatch.delenv("CHROME_INSTANCE_PATH", raising=False)
        e2e = E2E(tests=tests_dict)
        assert e2e.tests == tests_dict
        assert (
            e2e.chrome_instance_path
            == "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        )
        # Now set the CHROME_INSTANCE_PATH env variable and reinitialize
        monkeypatch.setenv("CHROME_INSTANCE_PATH", "/env/chrome")
        e2e_env = E2E(tests=tests_dict)
        assert e2e_env.chrome_instance_path == "/env/chrome"

    async def test_run_creates_codebeaver_folder(self, monkeypatch, tmp_path):
        """Test that run() creates the .codebeaver folder if it is missing and writes e2e.json and e2e.xml files."""
        import json
        import shutil

        monkeypatch.chdir(tmp_path)
        codebeaver_dir = tmp_path / ".codebeaver"
        if codebeaver_dir.exists():
            shutil.rmtree(codebeaver_dir)
        # Monkey-patch GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore to create the folder
        monkeypatch.setattr(
            "codebeaver.E2E.GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore",
            lambda: codebeaver_dir.mkdir(exist_ok=True),
        )

        # Define a fake Agent.run that returns a valid JSON result
        async def fake_run(self):
            class FakeRes:
                def final_result(inner_self):
                    return json.dumps({"passed": True, "comment": "Test succeeded"})

            return FakeRes()

        monkeypatch.setattr("codebeaver.E2E.Agent.run", fake_run)
        # Monkey-patch Report methods so that a fixed XML report is written
        monkeypatch.setattr(
            "codebeaver.E2E.Report.add_e2e_results", lambda self, results: None
        )
        monkeypatch.setattr(
            "codebeaver.E2E.Report.generate_xml_report", lambda self: "XML_REPORT"
        )
        tests_dict = {"TestDir": {"steps": ["dummy"], "url": "http://example.com"}}
        e2e = E2E(tests=tests_dict)
        results = await e2e.run()
        json_file = tmp_path / ".codebeaver" / "e2e.json"
        xml_file = tmp_path / ".codebeaver" / "e2e.xml"
        assert json_file.exists()
        assert xml_file.exists()
        with open(json_file, "r") as f:
            data = json.load(f)
        assert isinstance(data, list)
        with open(xml_file, "r") as f:
            xml_content = f.read()
        assert xml_content == "XML_REPORT"

    async def test_run_xml_content_empty_e2e(self, monkeypatch, tmp_path):
        """Test that run() creates e2e.xml with the correct content when no tests are provided."""
        monkeypatch.chdir(tmp_path)
        # Patch GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore to create the .codebeaver directory
        monkeypatch.setattr(
            "codebeaver.E2E.GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore",
            lambda: (tmp_path / ".codebeaver").mkdir(exist_ok=True),
        )
        from codebeaver.E2E import Report

        # Patch Report.generate_xml_report to return a known XML string
        monkeypatch.setattr(Report, "generate_xml_report", lambda self: "default_xml")
        e2e = E2E(tests={})
        # Run the overall E2E tests even though there are no tests provided
        await e2e.run()
        xml_file = tmp_path / ".codebeaver" / "e2e.xml"
        assert xml_file.exists(), "Expected e2e.xml to be created"
        with open(xml_file, "r") as f:
            content = f.read()
        assert (
            content == "default_xml"
        ), "The XML report content did not match the expected value"
