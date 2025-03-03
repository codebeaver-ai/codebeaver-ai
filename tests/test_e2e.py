"""Test cases for the E2E module."""

import os
import pytest
import json
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from src.codebeaver.E2E import E2E, End2endTest, TestCase


@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment with OPENAI_API_KEY."""
    monkeypatch.setenv(
        "OPENAI_API_KEY",
        "test-api-key",
    )


@pytest.fixture
def sample_tests():
    """Sample test configuration for E2E tests."""
    return {
        "test1": {
            "url": "https://example.com",
            "steps": ["Click on the login button", "Enter username and password"],
        },
        "test2": {
            "url": "https://example.org",
            "steps": ["Search for 'test'", "Click on the first result"],
        },
    }


@pytest.fixture
def e2e_instance(sample_tests):
    """Create an E2E instance with sample tests."""
    return E2E(tests=sample_tests, chrome_instance_path="/mock/chrome/path")


@pytest.fixture
def sample_end2end_test():
    """Create a sample End2endTest instance."""
    return End2endTest(
        name="test1",
        steps=["Click on the login button", "Enter username and password"],
        url="https://example.com",
    )


@pytest.mark.asyncio
async def test_run_test_success(e2e_instance, sample_end2end_test):
    """Test the run_test method with a successful test."""
    # Mock the Browser, Agent, and history
    with patch("codebeaver.E2E.Browser") as mock_browser_class, patch(
        "codebeaver.E2E.Agent"
    ) as mock_agent_class:

        # Setup mocks
        mock_browser = MagicMock()
        mock_browser.close = AsyncMock()
        mock_browser_class.return_value = mock_browser

        mock_agent = MagicMock()
        mock_history = MagicMock()
        mock_history.final_result.return_value = (
            '{"passed": true, "comment": "Test passed successfully"}'
        )
        mock_agent.run = AsyncMock(return_value=mock_history)
        mock_agent_class.return_value = mock_agent

        # Run the test
        result = await e2e_instance.run_test(sample_end2end_test)

        # Assertions
        assert result.passed is True
        assert result.errored is False
        assert result.comment == "Test passed successfully"
        mock_browser_class.assert_called_once()
        mock_agent_class.assert_called_once()
        mock_agent.run.assert_called_once()
        mock_browser.close.assert_called_once()


@pytest.mark.asyncio
async def test_run_test_failure(e2e_instance, sample_end2end_test):
    """Test the run_test method with a failed test."""
    # Mock the Browser, Agent, and history
    with patch("codebeaver.E2E.Browser") as mock_browser_class, patch(
        "codebeaver.E2E.Agent"
    ) as mock_agent_class:

        # Setup mocks
        mock_browser = MagicMock()
        mock_browser.close = AsyncMock()
        mock_browser_class.return_value = mock_browser

        mock_agent = MagicMock()
        mock_history = MagicMock()
        mock_history.final_result.return_value = (
            '{"passed": false, "comment": "Test failed: could not find login button"}'
        )
        mock_agent.run = AsyncMock(return_value=mock_history)
        mock_agent_class.return_value = mock_agent

        # Run the test
        result = await e2e_instance.run_test(sample_end2end_test)

        # Assertions
        assert result.passed is False
        assert result.errored is False
        assert result.comment == "Test failed: could not find login button"
        mock_browser_class.assert_called_once()
        mock_agent_class.assert_called_once()
        mock_agent.run.assert_called_once()
        mock_browser.close.assert_called_once()


@pytest.mark.asyncio
async def test_run_test_error(e2e_instance, sample_end2end_test):
    """Test the run_test method with an error (no result)."""
    # Mock the Browser, Agent, and history
    with patch("codebeaver.E2E.Browser") as mock_browser_class, patch(
        "codebeaver.E2E.Agent"
    ) as mock_agent_class:

        # Setup mocks
        mock_browser = MagicMock()
        mock_browser.close = AsyncMock()
        mock_browser_class.return_value = mock_browser

        mock_agent = MagicMock()
        mock_history = MagicMock()
        mock_history.final_result.return_value = None  # No result
        mock_agent.run = AsyncMock(return_value=mock_history)
        mock_agent_class.return_value = mock_agent

        # Run the test
        result = await e2e_instance.run_test(sample_end2end_test)

        # Assertions
        assert result.passed is False
        assert result.errored is True
        assert result.comment == "No result from the test"
        mock_browser_class.assert_called_once()
        mock_agent_class.assert_called_once()
        mock_agent.run.assert_called_once()
        mock_browser.close.assert_called_once()


@pytest.mark.asyncio
async def test_run_method(e2e_instance, sample_tests):
    """Test the run method with multiple tests."""
    # Mock the run_test method to avoid actual test execution
    with patch.object(e2e_instance, "run_test") as mock_run_test, patch(
        "builtins.open", create=True
    ) as mock_open, patch("json.dump") as mock_json_dump, patch(
        "builtins.print"
    ) as mock_print:

        # Setup mock for run_test to return different results for different tests
        async def mock_run_test_side_effect(test):
            if test.name == "test1":
                test.passed = True
                test.comment = "Test 1 passed"
            else:
                test.passed = False
                test.comment = "Test 2 failed"
            return test

        mock_run_test.side_effect = mock_run_test_side_effect

        # Run the tests
        results = await e2e_instance.run()

        # Assertions
        assert len(results) == 2
        assert results[0].name == "test1"
        assert results[0].passed is True
        assert results[0].comment == "Test 1 passed"
        assert results[1].name == "test2"
        assert results[1].passed is False
        assert results[1].comment == "Test 2 failed"

        # Check if the results were written to e2e.json
        mock_open.assert_called_once_with("e2e.json", "w")
        mock_json_dump.assert_called_once()

        # Check if the summary was printed
        assert mock_print.call_count > 0


def test_end2end_test_initialization():
    """Test the initialization of End2endTest class."""
    test = End2endTest(
        name="test_name", steps=["step1", "step2"], url="https://example.com"
    )

    assert test.name == "test_name"
    assert test.steps == ["step1", "step2"]
    assert test.url == "https://example.com"
    assert test.passed is False
    assert test.errored is False
    assert test.comment == ""


def test_e2e_initialization(sample_tests):
    """Test the initialization of E2E class."""
    e2e = E2E(tests=sample_tests, chrome_instance_path="/custom/chrome/path")

    assert e2e.tests == sample_tests
    assert e2e.chrome_instance_path == "/custom/chrome/path"

    # Test with default chrome path
    e2e_default = E2E(tests=sample_tests)
    assert (
        e2e_default.chrome_instance_path
        == "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    )
