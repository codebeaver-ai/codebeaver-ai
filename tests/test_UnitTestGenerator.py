import os
import pytest
from pathlib import Path

# Import the UnitTestGenerator from the source code module
from src.codebeaver.UnitTestGenerator import UnitTestGenerator

#############################
# Dummy implementations and fixtures for dependencies

class DummyResponseMessage:
    def __init__(self, content):
        self.content = content

class DummyResponseChoice:
    def __init__(self, message):
        self.message = message

class DummyResponse:
    def __init__(self, choices):
        self.choices = choices

class DummyProvider:
    def __init__(self):
        self.model = 'dummy_model'

    def get_model_info(self, model):
        return {'context_window': 1024}

    def create_chat_completion(self, messages, max_completion_tokens):
        # Return a dummy response with test content wrapped in <test> blocks.
        dummy_message = DummyResponseMessage("<test>import unittest\n# Test code</test>")
        return DummyResponse([DummyResponseChoice(dummy_message)])

@pytest.fixture(autouse=True)
def patch_provider(monkeypatch):
    # Patch ProviderFactory.get_provider to return a DummyProvider instance
    from src.codebeaver.UnitTestGenerator import ProviderFactory
    monkeypatch.setattr(ProviderFactory, 'get_provider', lambda provider_type: DummyProvider())

@pytest.fixture(autouse=True)
def patch_response_parser(monkeypatch):
    # Patch ResponseParser.parse to simply return the input content for testing
    from src.codebeaver.UnitTestGenerator import ResponseParser
    monkeypatch.setattr(ResponseParser, 'parse', lambda content: content)

@pytest.fixture(autouse=True)
def patch_content_cleaner(monkeypatch):
    # Patch ContentCleaner.merge_files to just return the new test content for testing
    from src.codebeaver.UnitTestGenerator import ContentCleaner
    monkeypatch.setattr(ContentCleaner, 'merge_files', lambda fp, nt, ot: nt)

def write_temp_file(tmp_path, filename, content):
    file = tmp_path / filename
    file.write_text(content)
    return file

#############################
# Tests for UnitTestGenerator.generate_test

def test_generate_test_with_existing_test_file(tmp_path):
    """
    Test generate_test when an existing test file is provided along with console output.
    It verifies that the result includes the dummy test content from the provider.
    """
    source_code = "def foo():\n    return 'bar'"
    test_file_code = "import pytest\n\ndef existing_test():\n    pass"
    # Create temporary source and test files
    source_file = write_temp_file(tmp_path, "source.py", source_code)
    test_file = write_temp_file(tmp_path, "test_source.py", test_file_code)

    generator = UnitTestGenerator(source_file)
    output = generator.generate_test(test_file_path=test_file, console="Test console output")
    # Verify that output contains the dummy test content wrapped in <test> block
    assert "<test>" in output
    assert "import unittest" in output
    assert "</test>" in output

def test_generate_test_without_test_file(tmp_path):
    """
    Test generate_test when no test file is provided.
    It verifies that the method still generates dummy test content.
    """
    source_code = "def add(a, b):\n    return a + b"
    source_file = write_temp_file(tmp_path, "source.py", source_code)

    generator = UnitTestGenerator(source_file)
    output = generator.generate_test(test_file_path=None, console="")
    # Verify that output contains the dummy test result wrapped in <test> block
    assert "<test>" in output
    assert "import unittest" in output
    assert "</test>" in output

def test_generate_test_merge_failure(tmp_path, monkeypatch):
    """
    Test generate_test raises a ValueError when ContentCleaner.merge_files returns empty content.
    This simulates a merge failure.
    """
    source_code = "def subtract(a, b):\n    return a - b"
    source_file = write_temp_file(tmp_path, "source.py", source_code)

    # Patch merge_files to return an empty string to simulate a merge failure
    from src.codebeaver.UnitTestGenerator import ContentCleaner
    monkeypatch.setattr(ContentCleaner, 'merge_files', lambda fp, nt, ot: "")

    generator = UnitTestGenerator(source_file)
    with pytest.raises(ValueError, match="Error: No test content found"):
        generator.generate_test(test_file_path=None, console="")
def test_generate_test_with_empty_test_file(tmp_path):
    """
    Test generate_test when a test file exists but is empty.
    This verifies that an empty test file is treated as a new test file.
    """
    source_code = "def multiply(a, b):\n    return a * b"
    test_file_code = ""
    source_file = write_temp_file(tmp_path, "source.py", source_code)
    test_file = write_temp_file(tmp_path, "test_source.py", test_file_code)

    generator = UnitTestGenerator(source_file)
    output = generator.generate_test(test_file_path=test_file, console="Some console output")
    # Verify that output contains the dummy test content wrapped in <test> block
    assert "<test>" in output
    assert "import unittest" in output
    assert "</test>" in output

def test_generate_test_source_file_not_found(tmp_path):
    """
    Test generate_test raises FileNotFoundError when the source file does not exist.
    """
    non_existent_file = tmp_path / "non_existent.py"
    generator = UnitTestGenerator(non_existent_file)
    with pytest.raises(FileNotFoundError):
        generator.generate_test(test_file_path=None, console="")

def test_generate_test_with_non_empty_console(tmp_path):
    """
    Test generate_test when no test file is provided but console output is non-empty.
    This verifies that the console output branch in the prompt construction is executed.
    """
    source_code = (
        "def divide(a, b):\n"
        "    if b == 0:\n"
        "        return None\n"
        "    return a / b"
    )
    source_file = write_temp_file(tmp_path, "source.py", source_code)

    generator = UnitTestGenerator(source_file)
    output = generator.generate_test(test_file_path=None, console="Division by zero error")
    # Verify that output contains the dummy test content wrapped in <test> block
    assert "<test>" in output
    assert "import unittest" in output
    assert "</test>" in output

def test_generate_test_with_non_empty_test_file_no_console(tmp_path):
    """
    Test generate_test when a non-empty test file is provided and no console output.
    This verifies that the test generation uses the existing test file content correctly.
    """
    source_code = "def modulo(a, b):\n    return a % b"
    test_file_code = "import pytest\n\ndef existing_test_modulo():\n    pass"
    source_file = write_temp_file(tmp_path, "source.py", source_code)
    test_file = write_temp_file(tmp_path, "test_modulo.py", test_file_code)

    generator = UnitTestGenerator(source_file)
    output = generator.generate_test(test_file_path=test_file, console="")
    # Verify that output contains the dummy test content wrapped in <test> block
    assert "<test>" in output
    assert "import unittest" in output
    assert "</test>" in output
def test_generate_test_with_env_override(tmp_path, monkeypatch):
    """
    Test generate_test when the environment variable CODEBEAVER_PROVIDER is set to a custom value.
    This verifies that the provider is correctly instantiated with the overridden environment variable.
    """
    # Override the environment variable to a custom value ("dummy")
    monkeypatch.setenv("CODEBEAVER_PROVIDER", "openai")
    source_code = "def echo(x):\n    return x"
    source_file = write_temp_file(tmp_path, "echo.py", source_code)
    generator = UnitTestGenerator(source_file)
    # Call generate_test without a test file and without console output.
    output = generator.generate_test(test_file_path=None, console="")
    # Verify that the output includes the dummy test content wrapped in <test> block.
    assert "<test>" in output
    assert "import unittest" in output
    assert "</test>" in output

def test_generate_test_test_file_not_found(tmp_path):
    """
    Test generate_test raises FileNotFoundError when the provided test file does not exist.
    This ensures that a missing test file (when specified) leads to an error.
    """
    source_code = "def fiber(x):\n    return x * 2"
    source_file = write_temp_file(tmp_path, "fiber.py", source_code)
    # Specify a non-existent test file path.
    fake_test_file = tmp_path / "nonexistent_test.py"
    generator = UnitTestGenerator(source_file)
    with pytest.raises(FileNotFoundError):
        generator.generate_test(test_file_path=fake_test_file, console="")
def test_generate_test_includes_console_in_prompt(tmp_path, monkeypatch):
    """
    Test that the generated prompt sent to the provider includes the console output when provided.
    A custom dummy provider is used to capture the messages.
    """
    source_code = "def dummy_func():\n    pass"
    source_file = write_temp_file(tmp_path, "dummy.py", source_code)
    
    # Create a custom dummy provider that captures the messages sent in the request
    messages_sent = []
    class CustomDummyProvider:
        def __init__(self):
            self.model = 'custom_model'
        def get_model_info(self, model):
            return {'context_window': 1024}
        def create_chat_completion(self, messages, max_completion_tokens):
            nonlocal messages_sent
            messages_sent = messages
            dummy_message = DummyResponseMessage("<test>import unittest\n# Custom test</test>")
            return DummyResponse([DummyResponseChoice(dummy_message)])
    
    from src.codebeaver.UnitTestGenerator import ProviderFactory
    monkeypatch.setattr(ProviderFactory, 'get_provider', lambda provider_type: CustomDummyProvider())
    
    generator = UnitTestGenerator(source_file)
    console_output = "Custom console error occurred"
    output = generator.generate_test(test_file_path=None, console=console_output)
    
    # Verify that at least one message in the request includes the provided console output
    assert any("Last console output:" in message["content"] and console_output in message["content"] for message in messages_sent)
    # Verify that the dummy test content is in the output
    assert "<test>" in output
    assert "import unittest" in output
    assert "</test>" in output

def test_generate_test_calls_merge_files(tmp_path, monkeypatch):
    """
    Test that ContentCleaner.merge_files is called with the correct parameters,
    ensuring that the source file path, the new test content, and the original test file content are passed properly.
    """
    source_code = "def test_me():\n    return True"
    test_file_code = "def test_existing():\n    pass"
    source_file = write_temp_file(tmp_path, "test_me.py", source_code)
    test_file = write_temp_file(tmp_path, "test_existing.py", test_file_code)
    
    captured_args = {}
    from src.codebeaver.UnitTestGenerator import ContentCleaner
    def custom_merge(fp, nt, ot):
        captured_args["fp"] = fp
        captured_args["nt"] = nt
        captured_args["ot"] = ot
        return nt
    
    monkeypatch.setattr(ContentCleaner, 'merge_files', custom_merge)
    
    generator = UnitTestGenerator(source_file)
    output = generator.generate_test(test_file_path=test_file, console="")
    
    # Assert that the source file's path is correctly passed as a string
    assert captured_args.get("fp") == str(source_file)
    # Assert that the original test file content is correctly passed
    assert captured_args.get("ot") == test_file_code
    # And that the new test content returned by the dummy provider is included in the merge call
    assert "<test>" in captured_args.get("nt")
    
    # Verify that the output contains the expected dummy test block markers
    assert "<test>" in output and "</test>" in output