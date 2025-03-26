import pytest

from src.codebeaver.ResponseParser import ResponseParser


class TestResponseParser:
    @pytest.mark.parametrize(
        "input_response, expected_output",
        [
            ("<test>[test]Hello, World!</test>", "Hello, World!"),
            ("No test block here", ""),
            ("<test>[test]First</test><test>[test]Second</test>", "First"),
            ("<test>[test]  Whitespace  </test>", "Whitespace"),
            ("", ""),
            (
                "<test>[test]Outer<test>[test]Inner</test></test>",
                "Outer<test>[test]Inner",
            ),
        ],
    )
    def test_parse(self, input_response, expected_output):
        """
        Test the parse method of ResponseParser with various input scenarios.
        This test covers:
        - Valid response with a test block
        - Response without a test block
        - Response with multiple test blocks
        - Response with whitespace around the test content
        - Empty response
        - Response with nested test blocks
        """
        assert ResponseParser.parse(input_response) == expected_output

    def test_parse_with_multiline_content(self):
        """
        Test the parse method with multiline content inside the test block.
        """
        input_response = """
        <test>[test]
        This is a
        multiline
        test content
        </test>
        """
        expected_output = "This is a\n        multiline\n        test content"
        assert ResponseParser.parse(input_response).strip() == expected_output

    def test_parse_with_special_characters(self):
        """
        Test the parse method with special characters in the test block.
        """
        input_response = "<test>[test]!@#$%^&*()_+{}|:<>?</test>"
        expected_output = "!@#$%^&*()_+{}|:<>?"
        assert ResponseParser.parse(input_response) == expected_output

    def test_parse_with_large_input(self):
        """
        Test the parse method with a large input to ensure it can handle significant amounts of data.
        """
        large_content = "x" * 1000000  # 1 million characters
        input_response = f"<test>[test]{large_content}</test>"
        assert ResponseParser.parse(input_response) == large_content

    def test_parse_with_malformed_tags(self):
        """
        Test the parse method with malformed tags to ensure it handles them gracefully.
        """
        input_response = "<test[test]Malformed</test>"
        assert ResponseParser.parse(input_response) == ""

        input_response = "<test>[test]Malformed<test>"
        assert ResponseParser.parse(input_response) == ""

    @pytest.mark.parametrize(
        "input_response",
        [
            None,
            123,
            ["not", "a", "string"],
            {"key": "value"},
        ],
    )
    def test_parse_with_invalid_input_types(self, input_response):
        """
        Test the parse method with invalid input types to ensure it raises appropriate exceptions.
        """
        with pytest.raises(TypeError):
            ResponseParser.parse(input_response)

    def test_parse_with_nested_test_blocks(self):
        """
        Test the parse method with nested test blocks to ensure it handles them correctly.
        """
        input_response = "<test>[test]Outer<test>[test]Inner</test></test>"
        expected_output = "Outer<test>[test]Inner"
        assert ResponseParser.parse(input_response) == expected_output

    def test_parse_with_multiple_test_blocks(self):
        """
        Test the parse method with multiple test blocks to ensure it returns only the first one.
        """
        input_response = "<test>[test]First</test><test>[test]Second</test>"
        expected_output = "First"
        assert ResponseParser.parse(input_response) == expected_output

    def test_parse_with_empty_test_block(self):
        """
        Test the parse method with an empty test block to ensure it handles it correctly.
        """
        input_response = "<test>[test]</test>"
        expected_output = ""
        assert ResponseParser.parse(input_response) == expected_output

    def test_parse_with_whitespace_only_test_block(self):
        """
        Test the parse method with a test block containing only whitespace.
        """
        input_response = "<test>[test]   \n   \t   </test>"
        expected_output = ""
        assert ResponseParser.parse(input_response) == expected_output
