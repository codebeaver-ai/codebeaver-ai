import os
import pytest
from pathlib import Path
from codebeaver.AnalyzeError import AnalyzeError, ProviderFactory
from codebeaver.types import TestErrorType

class DummyProvider:
    def create_chat_completion(self, messages, max_completion_tokens):
        # Create a dummy response using the preset dummy_response_content attribute
        class DummyChoice:
            def __init__(self, content):
                self.message = type('Msg', (), {'content': content})
        dummy_response_content = getattr(self, "dummy_response_content", "<explanation>dummy explanation</explanation> /bug")
        return type('DummyResponse', (), {'choices': [DummyChoice(dummy_response_content)]})

class DummyProviderFactory:
    @staticmethod
    def get_provider(provider_type):
        return DummyProvider()

# Monkey-patch the ProviderFactory in AnalyzeError to use our DummyProviderFactory
ProviderFactory.get_provider = DummyProviderFactory.get_provider

@pytest.fixture
def dummy_files(tmp_path):
    """Fixture that creates dummy source code, test content, error string and file paths."""
    source_code = "print('Hello World')"
    tests = "def test_dummy(): assert True"
    error = "Some error occurred"
    return source_code, tests, error, tmp_path / "dummy.py", tmp_path / "dummy_test.py"

def test_analyze_exit_status(dummy_files):
    """Test that analyze returns exit status when error is 'exit status 1'."""
    source_code, tests, error, source_path, tests_path = dummy_files
    error = "exit status 1"
    analyzer = AnalyzeError(source_code, source_path, tests, tests_path, error)
    result = analyzer.analyze()
    assert result == (TestErrorType.TEST, "exit status 1")

def test_parse_response_explanation_tag(dummy_files):
    """Test _parse_response extracting explanation from <explanation> tag and /test tag."""
    source_code, tests, error, source_path, tests_path = dummy_files
    analyzer = AnalyzeError(source_code, source_path, tests, tests_path, error)
    response = "Some text <explanation>This is an explanation</explanation> additional text /test"
    tag, explanation = analyzer._parse_response(response)
    assert explanation == "This is an explanation"
    assert tag == TestErrorType.TEST

def test_parse_response_error_explanation_tag(dummy_files):
    """Test _parse_response extracting explanation from <error_explanation> tag when <explanation> is missing."""
    source_code, tests, error, source_path, tests_path = dummy_files
    analyzer = AnalyzeError(source_code, source_path, tests, tests_path, error)
    response = "Log details <error_explanation>Error explanation content</error_explanation> and /bug"
    tag, explanation = analyzer._parse_response(response)
    assert explanation == "Error explanation content"
    assert tag == TestErrorType.BUG

def test_parse_response_bracket_tags(dummy_files):
    """Test _parse_response using fallback bracket tags when explicit tags are not found."""
    source_code, tests, error, source_path, tests_path = dummy_files
    analyzer = AnalyzeError(source_code, source_path, tests, tests_path, error)

    # Test with [settings]
    response_settings = "Info text [settings]"
    tag, explanation = analyzer._parse_response(response_settings)
    assert tag == TestErrorType.SETTINGS

    # Test with [test]
    response_test = "Info text [test]"
    tag, explanation = analyzer._parse_response(response_test)
    assert tag == TestErrorType.TEST

    # Test with [bug]
    response_bug = "Info text [bug]"
    tag, explanation = analyzer._parse_response(response_bug)
    assert tag == TestErrorType.BUG

def test_parse_response_line_by_line_tags(dummy_files):
    """Test _parse_response using line by line tags such as (test), (bug), (settings)."""
    source_code, tests, error, source_path, tests_path = dummy_files
    analyzer = AnalyzeError(source_code, source_path, tests, tests_path, error)

    response = "Some log\n(test)"
    tag, _ = analyzer._parse_response(response)
    assert tag == TestErrorType.TEST

    response = "Some log\n(bug)"
    tag, _ = analyzer._parse_response(response)
    assert tag == TestErrorType.BUG

    response = "Some log\n(settings)"
    tag, _ = analyzer._parse_response(response)
    assert tag == TestErrorType.SETTINGS

def test_parse_response_no_tag(dummy_files):
    """Test _parse_response raises ValueError when no tag is present."""
    source_code, tests, error, source_path, tests_path = dummy_files
    analyzer = AnalyzeError(source_code, source_path, tests, tests_path, error)
    response = "No tag present in response"
    with pytest.raises(ValueError):
        analyzer._parse_response(response)

def test_analyze_with_provider(dummy_files):
    """Test analyze method with mocked provider that returns a dummy response with /bug and an explanation."""
    source_code, tests, error, source_path, tests_path = dummy_files
    analyzer = AnalyzeError(source_code, source_path, tests, tests_path, error)
    # Set dummy_response_content to simulate provider response with proper tags and explanation.
    analyzer.provider.dummy_response_content = "<explanation>Dummy explanation from provider</explanation> /bug"
    tag, explanation = analyzer.analyze()
    assert tag == TestErrorType.BUG
    assert explanation == "Dummy explanation from provider"