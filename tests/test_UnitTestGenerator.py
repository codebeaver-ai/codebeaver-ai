import os
import pytest
from pathlib import Path

from src.codebeaver.UnitTestGenerator import UnitTestGenerator, ResponseParser, ContentCleaner
from src.codebeaver.models.provider_factory import ProviderFactory, ProviderType


class FakeProvider:
    def create_chat_completion(self, messages, max_completion_tokens):
        class FakeChoice:
            message = type("FakeMessage", (), {"content": "fake test code"})
        class FakeResponse:
            choices = [FakeChoice()]
        return FakeResponse()


class TestUnitTestGenerator:
    """Tests for the UnitTestGenerator class to ensure generate_test works as expected."""

    @pytest.fixture(autouse=True)
    def patch_dependencies(self, monkeypatch):
        # Patch ProviderFactory.get_provider to always return a FakeProvider instance.
        monkeypatch.setattr(ProviderFactory, "get_provider", lambda provider_type: FakeProvider())
        # Patch ResponseParser.parse to return its input (the fake test code).
        monkeypatch.setattr(ResponseParser, "parse", lambda content: content)
        # Patch ContentCleaner.merge_files to return the new test content unless it equals "raise_value".
        monkeypatch.setattr(ContentCleaner, "merge_files", lambda file_path, new_content, old_content: new_content if new_content != "raise_value" else "")

    def test_generate_test_with_test_file_and_console(self, tmp_path):
        """
        Test generate_test when a test file exists and a console output is provided.
        Verifies that the method builds the prompt correctly and returns the fake test code.
        """
        # Create a temporary source file.
        source_file = tmp_path / "source.py"
        source_file.write_text("def foo():\n    return 'bar'")

        # Create a temporary existing test file.
        test_file = tmp_path / "test_source.py"
        test_file.write_text("import pytest\n\n# Existing tests")

        console_output = "Error: Something went wrong"

        # Instantiate the UnitTestGenerator with the temporary source file.
        utg = UnitTestGenerator(source_file)

        # Call generate_test providing the test file and console output.
        result = utg.generate_test(test_file_path=test_file, console=console_output)

        # Assert that the result equals the fake test code from the FakeProvider.
        assert result == "fake test code"

    def test_generate_test_without_test_file(self, tmp_path):
        """
        Test generate_test when no test file is provided.
        Verifies that the method handles generating a new test (using a new test file scenario) correctly.
        """
        # Create a temporary source file.
        source_file = tmp_path / "source.py"
        source_file.write_text("def foo():\n    return 'bar'")

        # Instantiate UnitTestGenerator with the source file.
        utg = UnitTestGenerator(source_file)

        # Call generate_test without providing a test file and without console output.
        result = utg.generate_test()

        # Assert that the result equals the fake test code.
        assert result == "fake test code"

    def test_generate_test_raises_error_on_empty_merge(self, tmp_path, monkeypatch):
        """
        Test generate_test raises a ValueError when the merged test content is empty.
        Verifies that the method correctly raises an error if no test content is found.
        """
        # Create a temporary source file.
        source_file = tmp_path / "source.py"
        source_file.write_text("def foo():\n    return 'bar'")

        # Create a temporary test file.
        test_file = tmp_path / "test_source.py"
        test_file.write_text("import pytest\n\n# Existing tests")

        # Override ContentCleaner.merge_files to return an empty string to simulate a failed merge.
        monkeypatch.setattr(ContentCleaner, "merge_files", lambda file_path, new_content, old_content: "")

        # Instantiate UnitTestGenerator with the source file.
        utg = UnitTestGenerator(source_file)

        # Expect a ValueError because merge_files returned empty content.
        with pytest.raises(ValueError, match="Error: No test content found"):
            utg.generate_test(test_file_path=test_file)
    def test_generate_test_source_file_not_found(self, tmp_path):
        """Test generate_test raises FileNotFoundError when the source file does not exist."""
        missing_source = tmp_path / "nonexistent.py"
        utg = UnitTestGenerator(missing_source)
        with pytest.raises(FileNotFoundError):
            utg.generate_test()

    def test_generate_test_prompt_content(self, tmp_path, monkeypatch):
        """Test generate_test builds the correct prompt by capturing the prompt content."""
        source_file = tmp_path / "source.py"
        source_file.write_text("def bar():\n    return 42")
        captured = []
        class CustomFakeProvider:
            def create_chat_completion(self, messages, max_completion_tokens):
                captured.append(messages[0]["content"])
                class FakeChoice:
                    message = type("FakeMessage", (), {"content": "fake from custom"})
                class FakeResponse:
                    choices = [FakeChoice()]
                return FakeResponse()

        monkeypatch.setattr(ProviderFactory, "get_provider", lambda provider_type: CustomFakeProvider())
        monkeypatch.setattr(ResponseParser, "parse", lambda content: content)
        monkeypatch.setattr(ContentCleaner, "merge_files", lambda file_path, new_content, old_content: new_content)
        utg = UnitTestGenerator(source_file)
        result = utg.generate_test(console="dummy console")
        assert "Source code file path:" in captured[0]
        assert "def bar():" in captured[0]
        assert "Last console output:" in captured[0]
        assert result == "fake from custom"
    def test_generate_test_with_empty_test_file(self, tmp_path):
        """Test generate_test when an empty test file is provided so that the new test scenario is used."""
        # Create a temporary source file.
        source_file = tmp_path / "source.py"
        source_file.write_text("def foo():\n    return 'bar'")

        # Create a temporary empty test file.
        test_file = tmp_path / "test_source.py"
        test_file.write_text("")

        # Instantiate UnitTestGenerator with the source file.
        utg = UnitTestGenerator(source_file)

        # Call generate_test providing the empty test file.
        result = utg.generate_test(test_file_path=test_file)

        # Assert that the result equals the fake test code returned from the provider.
        assert result == "fake test code"

    def test_generate_test_file_not_found(self, tmp_path):
        """Test generate_test raises FileNotFoundError when the provided test file does not exist."""
        # Create a temporary valid source file.
        source_file = tmp_path / "source.py"
        source_file.write_text("def test_func(): pass")
        # Define a non-existent test file path.
        non_existent_test_file = tmp_path / "nonexistent_test.py"
        # Instantiate UnitTestGenerator with the valid source file.
        utg = UnitTestGenerator(source_file)
        # Expect a FileNotFoundError because the test file does not exist.
        with pytest.raises(FileNotFoundError):
            utg.generate_test(test_file_path=non_existent_test_file)

    def test_generate_test_custom_provider_env(self, tmp_path, monkeypatch):
        """Test generate_test when a custom provider environment variable is set (non-default) and its provider is used."""
        # Set the non-default provider type environment variable.
        monkeypatch.setenv("CODEBEAVER_PROVIDER", "openai")
        class CustomProvider:
            def create_chat_completion(self, messages, max_completion_tokens):
                # Return a fake response with a custom marker.
                class FakeChoice:
                    message = type("FakeMessage", (), {"content": "custom fake test code"})
                class FakeResponse:
                    choices = [FakeChoice()]
                return FakeResponse()
        # Patch ProviderFactory.get_provider to check that it receives the custom provider type.
        def fake_get_provider(provider_type):
            assert provider_type == ProviderType("openai")
            return CustomProvider()
        monkeypatch.setattr(ProviderFactory, "get_provider", fake_get_provider)
        # Create a temporary source file.
        source_file = tmp_path / "source.py"
        source_file.write_text("def baz():\n    return 'qux'")
        # Instantiate UnitTestGenerator with the source file.
        utg = UnitTestGenerator(source_file)
        # Call generate_test without providing a test file or console output.
        result = utg.generate_test()
        # Assert that the result matches the content produced by the custom provider.
        assert result == "custom fake test code"
        """Test generate_test raises FileNotFoundError when the provided test file does not exist."""
        # Create a temporary valid source file.
        source_file = tmp_path / "source.py"
        source_file.write_text("def test_func(): pass")

        # Define a non-existent test file path.
        non_existent_test_file = tmp_path / "nonexistent_test.py"

        # Instantiate UnitTestGenerator with the valid source file.
        utg = UnitTestGenerator(source_file)

        # Expect a FileNotFoundError because the test file does not exist.
        with pytest.raises(FileNotFoundError):
            utg.generate_test(test_file_path=non_existent_test_file)
        """Test generate_test when a custom provider environment variable is set (non-default) and its provider is used."""
        # Set the non-default provider type environment variable.
        monkeypatch.setenv("CODEBEAVER_PROVIDER", "openai")

        class CustomProvider:
            def create_chat_completion(self, messages, max_completion_tokens):
                # Return a fake response with a custom marker.
                class FakeChoice:
                    message = type("FakeMessage", (), {"content": "custom fake test code"})
                class FakeResponse:
                    choices = [FakeChoice()]
                return FakeResponse()

        # Patch ProviderFactory.get_provider to check that it receives the custom provider type.
        def fake_get_provider(provider_type):
            assert provider_type == ProviderType("openai")
            return CustomProvider()

        monkeypatch.setattr(ProviderFactory, "get_provider", fake_get_provider)

        # Create a temporary source file.
        source_file = tmp_path / "source.py"
        source_file.write_text("def baz():\n    return 'qux'")

        # Instantiate UnitTestGenerator with the source file.
        utg = UnitTestGenerator(source_file)

        # Call generate_test without providing a test file or console output.
        result = utg.generate_test()

        # Assert that the result matches the content produced by the custom provider.
        assert result == "custom fake test code"