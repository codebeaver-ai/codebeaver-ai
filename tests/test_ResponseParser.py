import pytest
from src.codebeaver.ResponseParser import ResponseParser

def test_parse_returns_stripped_content():
    """Test that parse returns the correctly stripped content between tags."""
    input_str = "<test>[test]   Hello world   </test>"
    expected = "Hello world"
    result = ResponseParser.parse(input_str)
    assert result == expected

def test_parse_no_match_returns_empty():
    """Test that parse returns an empty string when no matching tag is present."""
    input_str = "This string does not have the proper tags"
    expected = ""
    result = ResponseParser.parse(input_str)
    assert result == expected

def test_parse_handles_multiline_content():
    """Test that parse correctly handles and strips multiline content."""
    content = "line1\nline2\nline3"
    input_str = f"<test>[test]{content}</test>"
    expected = content.strip()
    result = ResponseParser.parse(input_str)
    assert result == expected

def test_parse_multiple_test_tags():
    """Test that parse returns the first match when multiple test blocks are present."""
    input_str = "<test>[test]First</test><test>[test]Second</test>"
    expected = "First"
    result = ResponseParser.parse(input_str)
    assert result == expected

def test_parse_with_extra_spaces():
    """Test that parse strips extra spaces around the matching content."""
    input_str = "   <test>  [test]   spaced content   </test>   "
    expected = "spaced content"
    result = ResponseParser.parse(input_str)
    assert result == expected
def test_parse_empty_response():
    """Test that parse returns an empty string when an empty input is provided."""
    input_str = ""
    result = ResponseParser.parse(input_str)
    assert result == ""

def test_parse_only_spaces_inside():
    """Test that parse returns an empty string when the content between tags is only spaces."""
    input_str = "<test>[test]      </test>"
    result = ResponseParser.parse(input_str)
    assert result == ""

def test_parse_unclosed_tag():
    """Test that parse returns an empty string when the tag is not properly closed."""
    input_str = "<test>[test]Incomplete"
    result = ResponseParser.parse(input_str)
    assert result == ""

def test_parse_with_junk_around_tag():
    """Test that parse correctly extracts content even when there is extra junk text surrounding the tag."""
    input_str = "random text <test>[test]extracted content</test> more random text"
    result = ResponseParser.parse(input_str)
    assert result == "extracted content"

def test_parse_handles_inner_test_keyword():
    """Test that parse correctly handles when the content includes the literal string '[test]' inside the valid content."""
    input_str = "<test>[test]This [test] is tricky</test>"
    result = ResponseParser.parse(input_str)
    assert result == "This [test] is tricky"
def test_parse_missing_test_keyword():
    """Test that parse returns an empty string when the '[test]' marker is missing."""
    input_str = "<test>    Some content but missing marker  </test>"
    result = ResponseParser.parse(input_str)
    assert result == ""

def test_parse_incorrect_closing_tag():
    """Test that parse returns an empty string when the closing tag is not correctly formed."""
    input_str = "<test>[test]content</test >"
    result = ResponseParser.parse(input_str)
    assert result == ""

def test_parse_newline_after_opening_tag():
    """Test that parse correctly handles a newline immediately after the opening tag."""
    input_str = "<test>\n[test]content\n</test>"
    result = ResponseParser.parse(input_str)
    assert result == "content"

def test_parse_multiple_brackets():
    """Test that parse correctly extracts content when multiple '[test]' appear in the content."""
    input_str = "<test>[test][test] extra content</test>"
    expected = "[test] extra content"
    result = ResponseParser.parse(input_str)
    assert result == expected

def test_parse_tag_with_extra_space_in_tag():
    """Test that parse returns an empty string when the opening tag has extra spaces."""
    input_str = "<test >[test]content</test>"
    result = ResponseParser.parse(input_str)
    assert result == ""
def test_parse_empty_marker():
    """Test that parse returns an empty string when the [test] marker exists but no content follows."""
    input_str = "<test>[test]</test>"
    result = ResponseParser.parse(input_str)
    assert result == ""

def test_parse_with_characters_before_marker():
    """Test that parse returns an empty string when non-whitespace characters precede the [test] marker."""
    input_str = "<test>junk [test]content</test>"
    result = ResponseParser.parse(input_str)
    assert result == ""

def test_parse_with_preceding_closing_tag():
    """Test that parse correctly extracts content when an unrelated closing tag precedes the valid tag."""
    input_str = "</test><test>[test]content</test>"
    result = ResponseParser.parse(input_str)
    assert result == "content"

def test_parse_with_windows_newlines():
    """Test that parse correctly handles Windows style newlines."""
    input_str = "<test>\r\n[test]  Windows newline  \r\n</test>"
    result = ResponseParser.parse(input_str)
    assert result == "Windows newline"

def test_parse_with_unicode():
    """Test that parse correctly handles Unicode characters in the content."""
    input_str = "<test>[test]こんにちは世界</test>"
    result = ResponseParser.parse(input_str)
    assert result == "こんにちは世界"