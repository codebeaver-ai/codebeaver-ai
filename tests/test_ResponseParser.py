import pytest
from src.codebeaver.ResponseParser import ResponseParser

class TestResponseParser:
    def test_parse_with_valid_tag(self):
        """Test that parse extracts the content from a properly formatted tag.""" 
        response = "<test> [test]Hello World</test>"
        result = ResponseParser.parse(response)
        assert result == "Hello World"

    def test_parse_with_no_tag(self):
        """Test that parse returns an empty string if no matching tag exists.""" 
        response = "No test here"
        result = ResponseParser.parse(response)
        assert result == ""

    def test_parse_with_whitespace(self):
        """Test that parse method strips extra whitespace from the extracted content."""
        response = "<test>    [test]   Some Text    </test>"
        result = ResponseParser.parse(response)
        assert result == "Some Text"

    def test_parse_with_multiple_matches(self):
        """Test that parse returns the first match if multiple are present."""
        response = "<test> [test]First</test> <test> [test]Second</test>"
        result = ResponseParser.parse(response)
        assert result == "First"
    
    def test_parse_empty_content(self):
        """Test that parse returns an empty string when there is no content after the marker."""
        response = "<test> [test]</test>"
        result = ResponseParser.parse(response)
        assert result == ""
    
    def test_parse_without_whitespace_between_tag_and_marker(self):
        """Test that parse works even when there is no whitespace between <test> and [test]."""
        response = "<test>[test]No Space</test>"
        result = ResponseParser.parse(response)
        assert result == "No Space"
    
    def test_parse_with_malformed_marker(self):
        """Test that parse returns an empty string when the marker is not exactly '[test]'."""
        response = "<test> [invalid]Not matching</test>"
        result = ResponseParser.parse(response)
        assert result == ""
    
    def test_parse_with_missing_closing_tag(self):
        """Test that parse returns an empty string if the closing tag is missing."""
        response = "<test> [test]Missing closing"
        result = ResponseParser.parse(response)
        assert result == ""
    
    def test_parse_with_multiline_content(self):
        """Test that parse correctly captures multiline content, stripping only leading/trailing whitespace."""
        response = "<test> [test]   Line1\n   Line2 \n   Line3   </test>"
        result = ResponseParser.parse(response)
        # Only the leading/trailing spaces are stripped; internal newlines are preserved
        assert result == "Line1\n   Line2 \n   Line3"
    
    def test_parse_with_html_content(self):
        """Test that parse returns inner HTML content without modification."""
        response = "<test> [test]<div>Content</div></test>"
        result = ResponseParser.parse(response)
        assert result == "<div>Content</div>"
    def test_parse_with_empty_response(self):
        """Test that parse returns an empty string for an empty input."""
        response = ""
        result = ResponseParser.parse(response)
        assert result == ""

    def test_parse_with_none_response_raises_exception(self):
        """Test that parse raises a TypeError when response is None."""
        with pytest.raises(TypeError):
            ResponseParser.parse(None)

    def test_parse_with_prefix_text(self):
        """Test that parse returns an empty string when non-whitespace text appears before the [test] marker."""
        response = "<test>prefix [test]Content</test>"
        result = ResponseParser.parse(response)
        assert result == ""

    def test_parse_with_unicode_characters(self):
        """Test that parse correctly extracts unicode content."""
        response = "<test> [test]こんにちは世界</test>"
        result = ResponseParser.parse(response)
        assert result == "こんにちは世界"

    def test_parse_with_nested_square_brackets(self):
        """Test that parse correctly handles content with additional square brackets."""
        response = "<test> [test]Content with [brackets] inside</test>"
        result = ResponseParser.parse(response)
        assert result == "Content with [brackets] inside"
    def test_parse_with_uppercase_tag(self):
        """Test that parse returns an empty string when the tags are in uppercase as the regex is case sensitive."""
        response = "<TEST> [test]Uppercase tag</TEST>"
        result = ResponseParser.parse(response)
        assert result == ""

    def test_parse_with_extra_attributes(self):
        """Test that parse returns an empty string when the tag has extra attributes."""
        response = "<test attr='value'> [test]Extra attributes</test>"
        result = ResponseParser.parse(response)
        assert result == ""

    def test_parse_with_incorrect_marker_case(self):
        """Test that parse returns an empty string when the marker is in the wrong case."""
        response = "<test> [TEST]Incorrect marker case</test>"
        result = ResponseParser.parse(response)
        assert result == ""

    def test_parse_with_nonstring_input_list(self):
        """Test that parse raises a TypeError when the response is a list instead of a string."""
        with pytest.raises(TypeError):
            ResponseParser.parse([1, 2, 3])

    def test_parse_with_nonstring_input_int(self):
        """Test that parse raises a TypeError when the response is an integer instead of a string."""
        with pytest.raises(TypeError):
            ResponseParser.parse(123)