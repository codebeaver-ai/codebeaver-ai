import os
from .ResponseParser import ResponseParser
from .ContentCleaner import ContentCleaner
from .models.provider_factory import ProviderFactory, ProviderType
from pathlib import Path
import logging

logger = logging.getLogger("codebeaver")


class UnitTestGenerator:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        provider_type = os.getenv("CODEBEAVER_PROVIDER", "openai")
        self.provider = ProviderFactory.get_provider(ProviderType(provider_type))
        self.context_window = self.provider.get_model_info(self.provider.model)[
            "context_window"
        ]

    def generate_test(self, test_file_path: Path | None = None, console: str = ""):
        """
        Generate a test for the given file.
        """
        source_content = open(self.file_path).read()
        if test_file_path:
            test_file_content = open(test_file_path).read()
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
        if test_file_path:
            prompt += f"""
Test file path:
`{test_file_path}`

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
    Wrap the new imports and the test function in a <test> [test] </test> block.
    If you want to keep parts of the existing test file content, use a comment that starts with "... existing code" when writing new code.

    Add a docstring to the test to explain what the test is doing.
    """
        logger.debug("PROMPT:")
        logger.debug(prompt)
        response = self.provider.create_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=100000,
        )
        logger.debug("RESPONSE:")
        logger.debug(response)

        test_content = ResponseParser.parse(response.choices[0].message.content)
        logger.debug(f"Test content: {test_content}")

        test_content = ContentCleaner.merge_files(
            str(self.file_path), test_content, test_file_content
        )
        if not test_content:
            raise ValueError("Error: No test content found")
        return test_content
