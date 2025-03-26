import pytest

from src.codebeaver.ResponseParser import ResponseParser


class TestResponseParser:
    """Tests for the ResponseParser class."""

    def test_parse_valid_input(self):
        """Test parsing a valid input with a single test block."""
        input_str = "<test>[test]This is a test</test>"
        result = ResponseParser.parse(input_str)
        assert result == "This is a test"

    def test_parse_empty_input(self):
        """Test parsing an empty input string."""
        input_str = ""
        result = ResponseParser.parse(input_str)
        assert result == ""

    def test_parse_no_match(self):
        """Test parsing input with no matching test block."""
        input_str = "This is not a test block"
        result = ResponseParser.parse(input_str)
        assert result == ""

    def test_parse_multiple_matches(self):
        """Test parsing input with multiple test blocks."""
        input_str = "<test>[test]First test</test><test>[test]Second test</test>"
        result = ResponseParser.parse(input_str)
        assert result == "First test"

    def test_parse_with_whitespace(self):
        """Test parsing input with extra whitespace."""
        input_str = "<test>  [test]  Test with spaces  </test>"
        result = ResponseParser.parse(input_str)
        assert result == "Test with spaces"

    def test_parse_case_sensitivity(self):
        """Test parsing with different case in tags."""
        input_str = "<TEST>[test]Case insensitive</TEST>"
        result = ResponseParser.parse(input_str)
        assert result == ""  # Should not match due to case sensitivity

    def test_parse_nested_tags(self):
        """Test parsing with nested tags."""
        input_str = "<test>[test]Outer <inner>inner</inner> test</test>"
        result = ResponseParser.parse(input_str)
        assert result == "Outer <inner>inner</inner> test"

    def test_parse_multiline_input(self):
        """Test parsing multiline input."""
        input_str = """
        <test>
        [test]
        This is a
        multiline
        test
        </test>
        """
        result = ResponseParser.parse(input_str)
        assert result == "This is a\nmultiline\ntest"

    @pytest.mark.parametrize(
        "input_str, expected",
        [
            ("<test>[test]Test 1</test>", "Test 1"),
            ("<test>[test]</test>", ""),
            ("<test>[test] </test>", ""),
            ("<test>[test]  Test 2  </test>", "Test 2"),
        ],
    )
    def test_parse_parametrized(self, input_str, expected):
        """Test parsing with various inputs using parametrization."""
        result = ResponseParser.parse(input_str)
        assert result == expected

    def test_parse_malformed_input(self):
        """Test parsing malformed input."""
        input_str = "<test[test]Malformed</test>"
        result = ResponseParser.parse(input_str)
        assert result == ""

    def test_parse_with_attributes(self):
        """Test parsing input with attributes in the test tag."""
        input_str = '<test id="1">[test]Test with attributes</test>'
        result = ResponseParser.parse(input_str)
        assert result == "Test with attributes"
