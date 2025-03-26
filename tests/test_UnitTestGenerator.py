from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from codebeaver.models.provider_factory import ProviderFactory, ProviderType
from codebeaver.UnitTestGenerator import UnitTestGenerator


@pytest.fixture
def mock_provider():
    provider = Mock()
    provider.get_model_info.return_value = {"context_window": 4096}
    return provider


@pytest.fixture
def mock_provider_factory(mock_provider):
    with patch.object(ProviderFactory, "get_provider", return_value=mock_provider):
        yield


class TestUnitTestGenerator:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path, mock_provider_factory):
        self.file_path = tmp_path / "test_file.py"
        self.file_path.write_text("def sample_function():\n    return 42")
        self.test_generator = UnitTestGenerator(self.file_path)

    def test_initialization(self):
        """Test the initialization of UnitTestGenerator."""
        assert isinstance(self.test_generator, UnitTestGenerator)
        assert self.test_generator.file_path == self.file_path
        assert self.test_generator.context_window == 4096

    @patch("builtins.open")
    def test_generate_test_new_file(self, mock_open, mock_provider):
        """Test generating a test for a new file without existing content."""
        mock_open.return_value.__enter__.return_value.read.return_value = (
            "def sample_function():\n    return 42"
        )
        mock_provider.create_chat_completion.return_value.choices = [
            Mock(
                message=Mock(
                    content="<test>\nimport unittest\n\nclass TestSample(unittest.TestCase):\n    def test_sample_function(self):\n        self.assertEqual(sample_function(), 42)\n</test>"
                )
            )
        ]

        result = self.test_generator.generate_test()
        assert "import unittest" in result
        assert "class TestSample(unittest.TestCase):" in result
        assert "def test_sample_function(self):" in result
        assert "self.assertEqual(sample_function(), 42)" in result

    @patch("builtins.open")
    def test_generate_test_existing_file(self, mock_open, mock_provider):
        """Test generating a test for an existing test file."""
        mock_open.return_value.__enter__.return_value.read.side_effect = [
            "def sample_function():\n    return 42",
            "import unittest\n\nclass TestSample(unittest.TestCase):\n    def test_existing(self):\n        pass",
        ]
        mock_provider.create_chat_completion.return_value.choices = [
            Mock(
                message=Mock(
                    content="<test>\nclass TestSample(unittest.TestCase):\n    def test_new_function(self):\n        self.assertEqual(sample_function(), 42)\n</test>"
                )
            )
        ]

        result = self.test_generator.generate_test(
            test_file_path=Path("existing_test.py")
        )
        assert "import unittest" in result
        assert "class TestSample(unittest.TestCase):" in result
        assert "def test_existing(self):" in result
        assert "def test_new_function(self):" in result
        assert "self.assertEqual(sample_function(), 42)" in result

    @patch("builtins.open")
    def test_generate_test_with_console_output(self, mock_open, mock_provider):
        """Test generating a test with console output."""
        mock_open.return_value.__enter__.return_value.read.return_value = (
            "def sample_function():\n    return 42"
        )
        mock_provider.create_chat_completion.return_value.choices = [
            Mock(
                message=Mock(
                    content="<test>\nimport unittest\n\nclass TestSample(unittest.TestCase):\n    def test_sample_function(self):\n        self.assertEqual(sample_function(), 42)\n</test>"
                )
            )
        ]

        result = self.test_generator.generate_test(console="Sample console output")
        assert "import unittest" in result
        assert "class TestSample(unittest.TestCase):" in result
        assert "def test_sample_function(self):" in result
        assert "self.assertEqual(sample_function(), 42)" in result

    @patch("builtins.open")
    def test_generate_test_no_content_error(self, mock_open, mock_provider):
        """Test error handling when no test content is found."""
        mock_open.return_value.__enter__.return_value.read.return_value = (
            "def sample_function():\n    return 42"
        )
        mock_provider.create_chat_completion.return_value.choices = [
            Mock(message=Mock(content="No test content"))
        ]

        with pytest.raises(ValueError, match="Error: No test content found"):
            self.test_generator.generate_test()

    @patch("codebeaver.UnitTestGenerator.ContentCleaner")
    @patch("codebeaver.UnitTestGenerator.ResponseParser")
    @patch("builtins.open")
    def test_generate_test_integration(
        self, mock_open, mock_response_parser, mock_content_cleaner, mock_provider
    ):
        """Test the integration of various components in generate_test method."""
        mock_open.return_value.__enter__.return_value.read.return_value = (
            "def sample_function():\n    return 42"
        )
        mock_provider.create_chat_completion.return_value.choices = [
            Mock(
                message=Mock(
                    content="<test>\nimport unittest\n\nclass TestSample(unittest.TestCase):\n    def test_sample_function(self):\n        self.assertEqual(sample_function(), 42)\n</test>"
                )
            )
        ]
        mock_response_parser.parse.return_value = "Parsed content"
        mock_content_cleaner.merge_files.return_value = "Merged content"

        result = self.test_generator.generate_test()

        mock_response_parser.parse.assert_called_once()
        mock_content_cleaner.merge_files.assert_called_once_with(
            str(self.file_path), "Parsed content", None
        )
        assert result == "Merged content"
