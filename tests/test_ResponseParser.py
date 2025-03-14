import pytest

from src.codebeaver.ResponseParser import ResponseParser


class TestResponseParser:
    """Tests for the ResponseParser.parse method."""

    def test_valid_pattern_with_whitespace(self):
        """Test that parse returns the content with leading and trailing whitespace trimmed."""
        response = "<test>   [test]   Hello World   </test>"
        result = ResponseParser.parse(response)
        assert result == "Hello World"

    def test_valid_pattern_with_newlines(self):
        """Test that parse correctly handles newlines inside the content."""
        response = "<test>\n    [test]line1\nline2\n</test>"
        result = ResponseParser.parse(response)
        assert result == "line1\nline2"

    def test_invalid_pattern_no_brackets(self):
        """Test that parse returns an empty string when the [test] literal is missing."""
        response = "<test>   Hello World   </test>"
        result = ResponseParser.parse(response)
        assert result == ""

    def test_no_test_tag(self):
        """Test that parse returns an empty string when no <test> tag is present."""
        response = "Some random content without proper tags"
        result = ResponseParser.parse(response)
        assert result == ""

    def test_multiple_test_tags(self):
        """Test that parse only returns the content from the first <test> tag when multiple are present."""
        response = "<test> [test]First content</test><test> [test]Second content</test>"
        result = ResponseParser.parse(response)
        assert result == "First content"

    def test_empty_response(self):
        """Test that parse returns an empty string for an empty input."""
        response = ""
        result = ResponseParser.parse(response)
        assert result == ""

    def test_pattern_with_extra_spaces_and_tabs(self):
        """Test that parse properly strips excessive spaces and tabs around the content."""
        response = "<test>\t [test]   Some\tText  \t </test>"
        result = ResponseParser.parse(response)
        assert result == "Some\tText"

    def test_whitespace_only_content(self):
        """Test that parse returns an empty string when the content is only whitespace."""
        response = "<test> [test]     </test>"
        result = ResponseParser.parse(response)
        assert result == ""

    def test_multiple_test_literal_in_content(self):
        """Test that parse returns the entire content after the first '[test]' literal,
        including any subsequent '[test]' occurrences."""
        response = "<test> [test] [test] extra text </test>"
        result = ResponseParser.parse(response)
        # Captures everything after the initial '[test]' and strips extra whitespace.
        assert result == "[test] extra text"

    def test_no_leading_test_literal(self):
        """Test that parse returns an empty string when '[test]' is not immediately after the tag."""
        response = "<test> something [test] Some content </test>"
        result = ResponseParser.parse(response)
        assert result == ""

    def test_wrong_case_brackets(self):
        """Test that parse returns an empty string when the literal '[test]' is in the wrong case."""
        response = "<test> [TEST] some text </test>"
        result = ResponseParser.parse(response)
        assert result == ""

    def test_unicode_content(self):
        """Test that parse handles unicode characters properly."""
        response = "<test> [test]こんにちは世界</test>"
        result = ResponseParser.parse(response)
        assert result == "こんにちは世界"

    def test_invalid_first_valid_second(self):
        """Test that parse returns content from the first matching <test> tag even if an earlier tag doesn't match the pattern."""
        response = "<test> no literal here </test><test> [test]Valid Content</test>"
        result = ResponseParser.parse(response)
        assert result == "Valid Content"

    def test_missing_closing_tag(self):
        """Test that parse returns an empty string when the closing </test> tag is missing."""
        response = "<test> [test] content without closing tag"
        result = ResponseParser.parse(response)
        assert result == ""

    def test_none_input(self):
        """Test that parse raises a TypeError when input is None."""
        with pytest.raises(TypeError):
            ResponseParser.parse(None)

    def test_non_string_input(self):
        """Test that parse raises a TypeError when input is not a string (e.g., an integer)."""
        with pytest.raises(TypeError):
            ResponseParser.parse(123)

    def test_nested_tags(self):
        """Test that parse returns the content from the first <test> tag even when nested <test> tags are present.
        The regex stops at the first closing </test> tag, so extra nested tags are included in the captured group.
        """
        response = "<test> [test] Outer <test> [test] Inner </test> end </test>"
        result = ResponseParser.parse(response)
        # Expected result: the regex stops after "Inner" as it finds the first </test> tag.
        assert result == "Outer <test> [test] Inner"
