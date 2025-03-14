import pytest
from src.codebeaver.ResponseParser import ResponseParser

class TestResponseParser:
    """Test cases for ResponseParser class."""

    def test_valid_response(self):
        """Test that parse method returns expected content when valid test tags are provided."""
        response = "<test>[test]Hello World</test>"
        result = ResponseParser.parse(response)
        assert result == "Hello World"

    def test_valid_response_with_whitespace(self):
        """Test that parse method strips whitespace from content."""
        response = "<test>   [test]   spaced text   </test>"
        result = ResponseParser.parse(response)
        assert result == "spaced text"

    def test_no_test_tag_present(self):
        """Test that parse method returns empty string when <test> tag is missing."""
        response = "<notatest>[test]No test tag</notatest>"
        result = ResponseParser.parse(response)
        assert result == ""

    def test_multiple_test_tags(self):
        """Test that parse method only returns the first occurrence of test content."""
        response = "<test>[test]First</test> additional text <test>[test]Second</test>"
        result = ResponseParser.parse(response)
        assert result == "First"

    def test_empty_response(self):
        """Test that parse method returns empty string when provided with an empty response."""
        response = ""
        result = ResponseParser.parse(response)
        assert result == ""

    def test_unexpected_format(self):
        """Test that parse method returns empty string if the test format is not followed due to case mismatch."""
        response = "<test>[TEST]Not proper tag</test>"
        result = ResponseParser.parse(response)
        assert result == ""