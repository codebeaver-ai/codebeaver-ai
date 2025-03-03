import os
import json
import asyncio
import pytest
from pydantic import ValidationError

from src.codebeaver.E2E import E2E, End2endTest, TestCase
import src.codebeaver.E2E as e2e_mod

# Dummy classes to replace external dependencies in tests
class DummyHistory:
    def __init__(self, result):
        self._result = result

    def final_result(self):
        return self._result

class DummyAgent:
    def __init__(self, result, *args, **kwargs):
        self.result = result

    async def run(self):
        # Simulate agent execution and return a dummy history
        return DummyHistory(self.result)

class DummyBrowser:
    def __init__(self, config):
        self.config = config

    async def close(self):
        # Simulate closing the browser
        pass

class TestE2E:
    """Tests for the E2E class."""

    @pytest.fixture(autouse=True)
    def patch_dependencies(self, monkeypatch):
        # Patch the Agent and Browser in the E2E module with dummy implementations.
        monkeypatch.setattr(e2e_mod, 'Agent', lambda *args, **kwargs: DummyAgent(monkeypatch.agent_result, *args, **kwargs))
        monkeypatch.setattr(e2e_mod, 'Browser', DummyBrowser)

    @pytest.mark.asyncio
    async def test_run_pass(self, tmp_path, monkeypatch):
        """Test that E2E.run produces a passing test result when the Agent returns a valid JSON result."""
        # Set up the dummy agent to return a valid JSON result indicating success.
        monkeypatch.agent_result = json.dumps({"passed": True, "comment": "Test passed"})

        tests = {
            "test_pass": {
                "steps": ["Click button", "Verify text"],
                "url": "http://example.com"
            }
        }
        e2e_instance = E2E(tests)

        # Change working directory to the temporary path to avoid file system side-effects.
        os.chdir(tmp_path)
        results = await e2e_instance.run()

        assert len(results) == 1
        result = results[0]
        assert result.passed is True
        assert result.comment == "Test passed"
        assert result.errored is False

        # Validate that the results file e2e.json is created and contains the expected content.
        result_file = tmp_path / "e2e.json"
        assert result_file.exists()
        with open(result_file, "r") as f:
            data = json.load(f)
        assert data[0]["passed"] is True
        assert data[0]["comment"] == "Test passed"

    @pytest.mark.asyncio
    async def test_run_no_result(self, tmp_path, monkeypatch):
        """Test that E2E.run handles the scenario where the Agent returns None (no result)."""
        # Set the dummy agent to return None to simulate an error in test execution.
        monkeypatch.agent_result = None

        tests = {
            "test_error": {
                "steps": ["Navigate to page", "Submit form"],
                "url": "http://example.com"
            }
        }
        e2e_instance = E2E(tests)
        os.chdir(tmp_path)
        results = await e2e_instance.run()

        assert len(results) == 1
        result = results[0]
        # When no result is returned, the test should be flagged as errored.
        assert result.errored is True
        assert result.comment == "No result from the test"
        assert result.passed is False

    @pytest.mark.asyncio
    async def test_run_multiple_tests(self, tmp_path, monkeypatch):
        """Test E2E.run with multiple tests where some pass and some error out."""
        # In this test, we override the Agent to produce responses based on the URL.
        def side_effect(*args, **kwargs):
            task = kwargs.get("task", "")
            if "http://pass.com" in task:
                return DummyAgent(json.dumps({"passed": True, "comment": "Passed"}), *args, **kwargs)
            else:
                return DummyAgent(None, *args, **kwargs)

        monkeypatch.setattr(e2e_mod, 'Agent', side_effect)

        tests = {
            "test_pass": {
                "steps": ["Step 1", "Step 2"],
                "url": "http://pass.com"
            },
            "test_fail": {
                "steps": ["Step A", "Step B"],
                "url": "http://fail.com"
            }
        }
        e2e_instance = E2E(tests)
        os.chdir(tmp_path)
        results = await e2e_instance.run()

        assert len(results) == 2
        for res in results:
            if res.name == "test_pass":
                assert res.passed is True
                assert res.comment == "Passed"
            elif res.name == "test_fail":
                assert res.errored is True
                assert res.comment == "No result from the test"

    @pytest.mark.asyncio
    async def test_run_invalid_json(self, tmp_path, monkeypatch):
        """Test that E2E.run raises an exception when agent returns invalid JSON."""
        # Set dummy agent to return an invalid JSON string which will cause the validation to fail.
        monkeypatch.agent_result = "invalid json"
        tests = {
            "test_invalid": {
                "steps": ["Step 1", "Step 2"],
                "url": "http://example.com"
            }
        }
        e2e_instance = E2E(tests)
        os.chdir(tmp_path)
        with pytest.raises(Exception):
            await e2e_instance.run()

    @pytest.mark.asyncio
    async def test_env_variable_chrome_instance_path(self, monkeypatch):
        """Test that E2E correctly uses the environment variable CHROME_INSTANCE_PATH."""
        monkeypatch.setenv("CHROME_INSTANCE_PATH", "dummy_path")
        e2e_instance = E2E({})
        assert e2e_instance.chrome_instance_path == "dummy_path"

    @pytest.mark.asyncio
    async def test_run_capture_stdout(self, tmp_path, monkeypatch, capsys):
        """Test that E2E.run prints expected output to stdout."""
        # Set up a dummy agent that returns a passing JSON result.
        monkeypatch.agent_result = json.dumps({"passed": True, "comment": "Output captured"})
        tests = {
            "test_print": {
                "steps": ["step one", "step two"],
                "url": "http://example.com"
            }
        }
        e2e_instance = E2E(tests)
        os.chdir(tmp_path)
        await e2e_instance.run()
        captured = capsys.readouterr().out
        # Check that the output contains the expected log messages.
        assert "Running test:" in captured
        assert "test_print" in captured
        assert "E2E tests passed" in captured
    @pytest.mark.asyncio
    async def test_run_empty(self, tmp_path):
        """Test that E2E.run properly handles an empty tests dictionary."""
        tests = {}
        e2e_instance = E2E(tests)
        results = await e2e_instance.run()
        assert results == []
        result_file = tmp_path / "e2e.json"
        assert result_file.exists()
        with open(result_file, "r") as f:
            data = json.load(f)
        assert data == []
        results = await e2e_instance.run()
        assert results == []
        result_file = tmp_path / "e2e.json"
        assert result_file.exists()
        with open(result_file, "r") as f:
            data = json.load(f)
        assert data == []
    async def test_run_missing_key(self, tmp_path):
        """Test that E2E.run raises a KeyError when a test dictionary is missing required keys."""
        # Create a test dictionary with a missing 'steps' key.
        tests = {
            "test_missing": {
                "url": "http://example.com"
            }
        }
        e2e_instance = E2E(tests)
        os.chdir(tmp_path)
        with pytest.raises(KeyError):
            await e2e_instance.run()

    @pytest.mark.asyncio
    async def test_browser_close_called(self, tmp_path, monkeypatch):
        """Test that each browser instance is properly closed by E2E.run."""
        browser_instances = []
        class DummyBrowserClose:
            def __init__(self, config):
                self.config = config
                self.closed = False
                browser_instances.append(self)
            async def close(self):
                self.closed = True
        monkeypatch.setattr(e2e_mod, 'Browser', DummyBrowserClose)
        monkeypatch.agent_result = json.dumps({"passed": True, "comment": "Browser closed ok"})
        tests = {
            "test_browser": {
                "steps": ["dummy step"],
                "url": "http://example.com"
            }
        }
        e2e_instance = E2E(tests)
        os.chdir(tmp_path)
        await e2e_instance.run()
        for browser in browser_instances:
            assert browser.closed is True

    @pytest.mark.asyncio
    async def test_run_test_direct_valid(self, tmp_path, monkeypatch):
        """Test the run_test method in isolation with a valid agent result."""
        monkeypatch.setattr(e2e_mod, 'Agent', lambda *args, **kwargs: DummyAgent(monkeypatch.agent_result, *args, **kwargs))
        monkeypatch.setattr(e2e_mod, 'Browser', DummyBrowser)
        monkeypatch.agent_result = json.dumps({"passed": True, "comment": "Direct test valid"})
        test_instance = End2endTest(name="direct_test", steps=["step1"], url="http://example.com")
        e2e_instance = E2E(tests={})
        os.chdir(tmp_path)
        result = await e2e_instance.run_test(test_instance)
        assert result.passed is True
        assert result.comment == "Direct test valid"
        assert result.errored is False
    @pytest.mark.asyncio
    async def test_run_test_exception(self, tmp_path, monkeypatch):
        """Test that E2E.run propagates exceptions raised from agent.run."""
        # Define an Agent that always raises an exception when run() is called.
        class ExceptionAgent:
            def __init__(self, *args, **kwargs):
                pass

            async def run(self):
                raise Exception("Agent run failure")

        # Patch the Agent in the module with our ExceptionAgent.
        monkeypatch.setattr(e2e_mod, 'Agent', ExceptionAgent)

        tests = {
            "test_exception": {
                "steps": ["Do something"],
                "url": "http://example.com"
            }
        }
        e2e_instance = E2E(tests)
        os.chdir(tmp_path)
        with pytest.raises(Exception, match="Agent run failure"):
            await e2e_instance.run()
        os.chdir(tmp_path)
        results = await e2e_instance.run()
        # Expect that no tests are executed, so results is an empty list and e2e.json contains an empty list.
        assert results == []
        result_file = tmp_path / "e2e.json"
        assert result_file.exists()
        with open(result_file, "r") as f:
            data = json.load(f)
        assert data == []
    @pytest.mark.asyncio
    async def test_run_invalid_schema(self, tmp_path, monkeypatch):
        """Test that E2E.run raises an exception when the agent returns JSON missing required schema fields."""
        monkeypatch.agent_result = json.dumps({"passed": True})  # missing the "comment" field
        tests = {
            "test_invalid_schema": {
                "steps": ["step1"],
                "url": "http://example.com"
            }
        }
        e2e_instance = E2E(tests)
        os.chdir(tmp_path)
        with pytest.raises(Exception):
            await e2e_instance.run()
    @pytest.mark.asyncio
    async def test_run_test_browser_close_exception(self, tmp_path, monkeypatch):
        """Test that if Browser.close() raises an exception, run_test propagates the error."""
        class DummyBrowserException:
            def __init__(self, config):
                self.config = config
            async def close(self):
                raise Exception("Browser close failure")
        monkeypatch.setattr(e2e_mod, 'Browser', DummyBrowserException)
        monkeypatch.agent_result = json.dumps({"passed": True, "comment": "Test result"})
        test_instance = End2endTest(name="test_browser_exception", steps=["step"], url="http://example.com")
        e2e_instance = E2E(tests={})
        os.chdir(tmp_path)
        with pytest.raises(Exception, match="Browser close failure"):
            await e2e_instance.run_test(test_instance)
    @pytest.mark.asyncio
    async def test_invalid_steps_type(self, tmp_path, monkeypatch):
        """Test that E2E.run raises an exception when steps is not a list (invalid type)."""
        tests = {
            "test_invalid_steps": {
                "steps": "not a list",
                "url": "http://example.com"
            }
        }
        e2e_instance = E2E(tests)
        os.chdir(tmp_path)
        with pytest.raises(Exception):
            await e2e_instance.run()
    @pytest.mark.asyncio
    async def test_run_missing_url(self, tmp_path):
        """Test that E2E.run raises a KeyError when a test dictionary is missing the 'url' key."""
        tests = {
            "test_missing_url": {
                "steps": ["step"]
            }
        }
        e2e_instance = E2E(tests)
        os.chdir(tmp_path)
        with pytest.raises(KeyError):
            await e2e_instance.run()
    @pytest.mark.asyncio
    async def test_run_empty_steps(self, tmp_path, monkeypatch):
        """Test that E2E.run correctly handles an empty steps list."""
        # Set up the dummy agent to return a valid JSON result indicating success.
        monkeypatch.agent_result = json.dumps({"passed": True, "comment": "Empty steps test passed"})
        tests = {
            "test_empty_steps": {
                "steps": [],
                "url": "http://example.com"
            }
        }
        e2e_instance = E2E(tests)
        os.chdir(tmp_path)
        results = await e2e_instance.run()
        assert len(results) == 1
        res = results[0]
        assert res.passed is True
        assert res.comment == "Empty steps test passed"
        assert res.errored is False

    @pytest.mark.asyncio
    async def test_default_chrome_instance_path(self, monkeypatch):
        """Test that E2E uses the default chrome_instance_path when the environment variable is not set."""
        monkeypatch.delenv("CHROME_INSTANCE_PATH", raising=False)
        e2e_instance = E2E({})
        # The default path is set inside the __init__ of E2E.
        expected_default = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        assert e2e_instance.chrome_instance_path == expected_default
    @pytest.mark.asyncio
    async def test_run_non_string_result(self, tmp_path, monkeypatch):
        """Test that E2E.run_test raises an exception when the agent returns a non-string result."""
        monkeypatch.setattr(e2e_mod, 'Agent', lambda *args, **kwargs: DummyAgent(monkeypatch.agent_result, *args, **kwargs))
        monkeypatch.setattr(e2e_mod, 'Browser', DummyBrowser)
        monkeypatch.agent_result = {}  # non-string result, which should trigger a validation exception
        test_instance = End2endTest(name="non_string_result", steps=["step"], url="http://example.com")
        e2e_instance = E2E(tests={})
        os.chdir(tmp_path)
        with pytest.raises(Exception):
            await e2e_instance.run_test(test_instance)
    
    @pytest.mark.asyncio
    async def test_run_empty_string_result(self, tmp_path, monkeypatch):
        """Test that E2E.run_test handles an empty string result as no result and flags the test as errored."""
        monkeypatch.setattr(e2e_mod, 'Agent', lambda *args, **kwargs: DummyAgent(monkeypatch.agent_result, *args, **kwargs))
        monkeypatch.setattr(e2e_mod, 'Browser', DummyBrowser)
        monkeypatch.agent_result = ""  # empty string, which should be falsy
        test_instance = End2endTest(name="empty_string_result", steps=["step"], url="http://example.com")
        e2e_instance = E2E(tests={})
        os.chdir(tmp_path)
        result = await e2e_instance.run_test(test_instance)
        assert result.errored is True
        assert result.comment == "No result from the test"
    @pytest.mark.asyncio
    async def test_non_string_test_key(self, tmp_path, monkeypatch):
        """Test that non-string test name keys are converted to string in End2endTest model."""
        # Set the dummy agent to return a valid JSON result.
        monkeypatch.agent_result = json.dumps({"passed": True, "comment": "Test for non-string key"})
        tests = {
            123: {
                "steps": ["Click"],
                "url": "http://example.com"
            }
        }
        e2e_instance = E2E(tests)
        os.chdir(tmp_path)
        results = await e2e_instance.run()
        assert len(results) == 1
        result = results[0]
        # Although the key was an integer, End2endTest expects a string so it should convert it.
        assert result.name == "123"
        assert result.passed is True
        assert result.comment == "Test for non-string key"

    @pytest.mark.asyncio
    async def test_run_agent_returns_list(self, tmp_path, monkeypatch):
        """Test that E2E.run_test raises an exception when the agent returns a list instead of a JSON string."""
        monkeypatch.setattr(e2e_mod, 'Agent', lambda *args, **kwargs: DummyAgent(monkeypatch.agent_result, *args, **kwargs))
        monkeypatch.setattr(e2e_mod, 'Browser', DummyBrowser)
        # Set agent_result to a list (invalid type) to trigger a validation error.
        monkeypatch.agent_result = []  # list instead of a JSON string
        test_instance = End2endTest(name="list_result", steps=["step"], url="http://example.com")
        e2e_instance = E2E(tests={})
        os.chdir(tmp_path)
        with pytest.raises(Exception):
            await e2e_instance.run_test(test_instance)
    @pytest.mark.asyncio
    async def test_run_empty_url(self, tmp_path, monkeypatch):
        """Test that E2E.run_test handles an empty URL."""
        monkeypatch.setattr(e2e_mod, 'Agent', lambda *args, **kwargs: DummyAgent(monkeypatch.agent_result, *args, **kwargs))
        monkeypatch.setattr(e2e_mod, 'Browser', DummyBrowser)
        monkeypatch.agent_result = json.dumps({"passed": True, "comment": "Empty URL test passed"})
        test_instance = End2endTest(name="empty_url_test", steps=["do nothing"], url="")
        e2e_instance = E2E(tests={})
        os.chdir(tmp_path)
        result = await e2e_instance.run_test(test_instance)
        assert result.passed is True
        assert result.comment == "Empty URL test passed"
        assert result.errored is False

    @pytest.mark.asyncio
    async def test_run_extra_keys(self, tmp_path, monkeypatch):
        """Test that extra keys in test dictionary do not interfere with execution."""
        monkeypatch.setattr(e2e_mod, 'Agent', lambda *args, **kwargs: DummyAgent(monkeypatch.agent_result, *args, **kwargs))
        monkeypatch.setattr(e2e_mod, 'Browser', DummyBrowser)
        monkeypatch.agent_result = json.dumps({"passed": True, "comment": "Extra keys handled"})
        tests = {
            "test_extra": {
                "steps": ["some step"],
                "url": "http://example.com",
                "extra": "this key is extra"
            }
        }
        e2e_instance = E2E(tests)
        os.chdir(tmp_path)
        results = await e2e_instance.run()
        assert len(results) == 1
        res = results[0]
        assert res.passed is True
        assert res.comment == "Extra keys handled"
        assert res.errored is False

    @pytest.mark.asyncio
    async def test_run_non_string_steps(self, tmp_path, monkeypatch):
        """Test that E2E.run_test handles steps list containing non-string elements."""
        monkeypatch.setattr(e2e_mod, 'Agent', lambda *args, **kwargs: DummyAgent(monkeypatch.agent_result, *args, **kwargs))
        monkeypatch.setattr(e2e_mod, 'Browser', DummyBrowser)
        monkeypatch.agent_result = json.dumps({"passed": True, "comment": "Non-string steps test passed"})
        tests = {
            "test_non_string_steps": {
                "steps": [123, "click"],
                "url": "http://example.com"
            }
        }
        e2e_instance = E2E(tests)
        os.chdir(tmp_path)
        results = await e2e_instance.run()
        assert len(results) == 1
        res = results[0]
        assert res.passed is True
        assert res.comment == "Non-string steps test passed"
        assert res.errored is False