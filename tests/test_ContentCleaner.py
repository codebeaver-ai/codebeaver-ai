import pytest
import ast
import black
from src.codebeaver.ContentCleaner import ContentCleaner

class TestContentCleaner:
    """Test cases for ContentCleaner functionality."""

    def test_get_and_set_supported_languages(self):
        """Test the getter and setter for supported languages."""
        # Test default supported languages
        default_langs = ContentCleaner.get_supported_languages()
        assert "python" in default_langs
        assert "typescript" in default_langs

        # Set new languages and verify update
        new_langs = {"ruby": {"aliases": ["ruby", "rb"], "merge_function": "merge_ruby_files"}}
        ContentCleaner.set_supported_languages(new_langs)
        assert ContentCleaner.get_supported_languages() == new_langs

        # Restore original configuration for further tests
        ContentCleaner.set_supported_languages(default_langs)

    def test_clean_python(self):
        """Test cleaning of Python content preserving docstring and organizing imports."""
        content = '''"""Module docstring."""
import os
import sys
from collections import defaultdict
from math import sqrt, pow

def foo():
    pass
'''
        cleaned = ContentCleaner.clean_python(content)
        # Check that docstring is preserved
        assert '"""Module docstring."""' in cleaned
        # Check that the import statements exist (order may change)
        assert "import os" in cleaned or "import sys" in cleaned
        assert "from collections import defaultdict" in cleaned or "from math import" in cleaned
        # Ensure the function definition is retained
        assert "def foo():" in cleaned

    def test_clean_typescript(self):
        """Test cleaning of TypeScript content reorganizing import statements and code sections."""
        ts_content = '''import { A, B } from 'module1';
import type { C } from 'module2';

const x = 10;
function test() {
    return x;
}
'''
        cleaned = ContentCleaner.clean_typescript(ts_content)
        # Check that the reformatted imports exist
        assert "import {" in cleaned
        assert "import type {" in cleaned
        # Ensure that the function remains in the cleaned content
        assert "function test(" in cleaned

    def test_merge_files_unsupported(self):
        """Test merge_files raises ValueError when file extension is unsupported."""
        file1_content = "console.log('Hello');"
        with pytest.raises(ValueError):
            ContentCleaner.merge_files("test.txt", file1_content, "import A from 'a';")

    def test_merge_python_files_success(self):
        """Test successful merging of two valid Python file contents."""
        file1 = '''def foo():
    print("Hello from file1")
'''
        file2 = '''def bar():
    print("Hello from file2")
'''
        merged = ContentCleaner.merge_python_files(file1, file2)
        # Check that the merged content is not None and contains both functions
        assert merged is not None
        assert "def foo():" in merged
        assert "def bar():" in merged

    def test_merge_python_files_failure(self):
        """Test merge_python_files returns None when file2 contains a syntax error."""
        file1 = '''def foo():
    print("Hello")
'''
        # Introduce a syntax error in file2
        file2 = '''def bar(:
    print("Syntax error")
'''
        merged = ContentCleaner.merge_python_files(file1, file2)
        assert merged is None

    def test_merge_typescript_files_success(self):
        """Test successful merging of two valid TypeScript file contents with language 'ts'."""
        file1 = '''import { A } from 'mod';
const x = 5;
'''
        file2 = '''import { B } from 'mod';
const y = 10;
'''
        merged = ContentCleaner.merge_typescript_files(file1, file2, "ts")
        # Expect that merged content combines both parts
        assert merged is not None
        assert "import {" in merged
        assert "const x" in merged
        assert "const y" in merged

    def test_merge_typescript_files_tsx(self):
        """Test successful merging of two valid TypeScript file contents with language 'tsx'."""
        file1 = '''import { A } from 'mod';
const Component = () => <div>A</div>;
'''
        file2 = '''import { B } from 'mod';
const Component2 = () => <span>B</span>;
'''
        merged = ContentCleaner.merge_typescript_files(file1, file2, "tsx")
        assert merged is not None
        assert "import {" in merged
        assert "const Component" in merged
        assert "const Component2" in merged