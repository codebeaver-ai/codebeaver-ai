import openai
from .ResponseParser import ResponseParser
from .ContentCleaner import ContentCleaner


class TestGenerator:
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

    def generate_test(self, test_file: str | None = None, console: str = ""):
        """
        Generate a test for the given file.
        """
        source_content = open(self.file_path).read()
        if test_file:
            test_file_content = open(test_file).read()
        else:
            test_file_content = None
        prompt = f"""
Source code file path:
`{self.file_path}`

Source code:
```
{source_content}
```
"""
        if test_file:
            prompt += f"""
Test file path:
`{test_file}`

"""
        if test_file_content:
            prompt += f"""
Test file content:
```
{test_file_content}
```
"""
        else:
            prompt += """Test file content: No content, the test file is new.

            """

        if console and console != "":
            prompt += f"""
Last console output:
```
{console}
```
"""
        prompt += """
    Reason out loud about any import statement and any line of code you need to write, then return the actual imports and test code.
    Import the original source code and use it in the test.
    Imports must cover the entire code of the new test, otherwise the test will fail. If you can't import something, mock it.
    If there is an existing test class, write the new test in the same class.
    Wrap the new imports and the test function in a ```test block.
    If you want to keep parts of the existing test file content, use a comment that starts with "... existing code" when writing new code.

    Add a docstring to the test to explain what the test is doing.
    """
        # print("PROMPT:", prompt)
        response = openai.chat.completions.create(
            model="o3-mini",
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=100000,
        )
        # print("RESPONSE:", response.choices[0].message.content)

        test_content = ResponseParser.parse(response.choices[0].message.content)

        test_content = ContentCleaner.merge_files(
            self.file_path, test_content, test_file_content
        )
        if not test_content:
            raise ValueError("Error: No test content found")
        return test_content
