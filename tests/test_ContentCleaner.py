import ast
import re
import pytest

from src.codebeaver.ContentCleaner import ContentCleaner

class TestContentCleaner:
    """Tests for ContentCleaner methods."""

    def test_get_and_set_supported_languages(self):
        """Test getting and setting supported languages configuration."""
        original = ContentCleaner.get_supported_languages()
        new_config = {"ruby": {"aliases": ["rb"], "merge_function": "merge_python_files"}}
        ContentCleaner.set_supported_languages(new_config)
        assert ContentCleaner.get_supported_languages() == new_config
        # Restore original configuration
        ContentCleaner.set_supported_languages(original)

    def test_clean_python(self):
        """Test cleaning of Python source code with various imports, docstrings, and blocks."""
        source = '''"""Module Docstring"""
import os
import sys
from collections import defaultdict
def foo():
    return 'foo'
if __name__ == "__main__":
    print("Hello")'''
        cleaned = ContentCleaner.clean_python(source)
        # Check that the docstring and import statements are preserved (and likely re-ordered)
        assert 'Module Docstring' in cleaned
        assert 'import os' in cleaned
        assert 'import sys' in cleaned
        assert 'from collections import defaultdict' in cleaned
        assert 'def foo()' in cleaned
        assert 'if __name__ == "__main__":' in cleaned

    def test_clean_typescript(self):
        """Test cleaning of TypeScript source code containing import statements and code."""
        source = """
import { B, A } from 'module1';
import type { T } from 'module2';
const x = 5;
"""
        cleaned = ContentCleaner.clean_typescript(source)
        # Since the formatting may change order of imports, check parts of the expected output.
        assert "import type { T } from 'module2';" in cleaned
        assert "const x = 5;" in cleaned
        # Check that at least one of the named imports appear in the formatted result
        assert ("import {" in cleaned and ("A" in cleaned or "B" in cleaned))

    def test_merge_python_files_valid(self):
        """Test merging two valid Python files produces valid merged code."""
        file1 = "def foo():\n    return 1\n"
        file2 = "def bar():\n    return 2\n"
        merged = ContentCleaner.merge_python_files(file1, file2)
        assert merged is not None
        # Try parsing the merged file to be sure it is valid Python
        parsed = ast.parse(merged)
        assert isinstance(parsed, ast.Module)

    def test_merge_python_files_invalid(self):
        """Test merging when one file contains invalid Python code returns None."""
        file1 = "def foo():\n    return 1\n"
        # file2 has invalid syntax (missing closing parenthesis)
        file2 = "def bar(  \n    return 2\n"
        merged = ContentCleaner.merge_python_files(file1, file2)
        assert merged is None

    def test_merge_files_unsupported(self):
        """Test that merge_files raises ValueError for unsupported file extensions."""
        file_content = "function test() {}"
        with pytest.raises(ValueError):
            ContentCleaner.merge_files("file.unsupported", file_content, file_content)

    def test_merge_typescript_files_valid_ts(self):
        """Test merging two valid TypeScript files (TS) produces merged content without errors."""
        file1 = "import { A } from 'mod';\nconst a = 1;"
        file2 = "import { B } from 'mod';\nconst b = 2;"
        merged = ContentCleaner.merge_typescript_files(file1, file2, "ts")
        assert merged is not None
        # Check that the merged output does not contain the string "ERROR"
        assert "ERROR" not in merged

    def test_merge_typescript_files_valid_tsx(self):
        """Test merging two valid TypeScript files (TSX) produces merged content without errors."""
        file1 = "import { A } from 'mod';\nconst a = 1;"
        file2 = "import { B } from 'mod';\nconst b = 2;"
        merged = ContentCleaner.merge_typescript_files(file1, file2, "tsx")
        assert merged is not None
        assert "ERROR" not in merged