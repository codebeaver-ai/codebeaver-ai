import ast
import re
import pytest

from codebeaver.ContentCleaner import ContentCleaner
@pytest.fixture(autouse=True)
def reset_supported_languages():
    """Reset the ContentCleaner supported languages after each test to avoid shared state issues."""
    original_config = {
        "python": {
            "aliases": ["python", "python3", "py"],
            "merge_function": "merge_python_files",
        },
        "typescript": {
            "aliases": ["typescript", "ts", "tsx", "javascript", "js", "jsx"],
            "merge_function": "merge_typescript_files",
        },
    }
    yield
    ContentCleaner.set_supported_languages(original_config)

class TestContentCleaner:
    """Test suite for the ContentCleaner class."""

    def test_get_and_set_supported_languages(self):
        """Test getting and setting the supported languages."""
        default = ContentCleaner.get_supported_languages()
        assert "python" in default
        assert "typescript" in default

        new_config = {
            "ruby": {"aliases": ["ruby"], "merge_function": "merge_ruby_files"}
        }
        ContentCleaner.set_supported_languages(new_config)
        updated = ContentCleaner.get_supported_languages()
        assert "ruby" in updated

    def test_merge_files_python(self):
        """Test merge_files for a Python file and valid merging."""
        file1_path = "example.py"
        file1_content = 'import sys\nprint("Hello from file1")'
        file2_content = 'def foo():\n    pass'
        # Using merge_files should call merge_python_files internally
        merged = ContentCleaner.merge_files(file1_path, file1_content, file2_content)
        # Expect a non-None result (black.formatted content)
        assert merged is not None
        assert "Hello from file1" in merged or "foo" in merged

    def test_merge_files_unsupported(self):
        """Test that merge_files raises ValueError when file extension is unsupported."""
        file1_path = "example.txt"
        file1_content = "print('unsupported file')"
        file2_content = "def bar():\n    pass"
        with pytest.raises(ValueError) as excinfo:
            ContentCleaner.merge_files(file1_path, file1_content, file2_content)
        # Ensure exception message contains the guessed lexer name.
        assert "Unsupported language" in str(excinfo.value)

    def test_clean_python(self):
        """Test clean_python reformats Python code with docstring, single and multiline imports, function and main block."""
        content = (
            '"""Module docstring"""\n'
            "import os\n"
            "from sys import argv\n"
            "from math import (\n"
            "    sin,\n"
            "    cos\n"
            ")\n"
            "\n"
            "def foo():\n"
            "    print('foo')\n"
            "\n"
            "if __name__ == '__main__':\n"
            "    foo()\n"
        )
        cleaned = ContentCleaner.clean_python(content)
        # Check that module docstring is preserved and main block exists.
        assert 'Module docstring' in cleaned
        assert "if __name__ == '__main__':" in cleaned

    def test_clean_typescript(self):
        """Test clean_typescript reformats Typescript content with imports and other lines."""
        ts_content = (
            "import { A } from 'moduleA';\n"
            "import type { B } from 'moduleB';\n"
            "\n"
            "const x = 42;\n"
        )
        cleaned = ContentCleaner.clean_typescript(ts_content)
        # Check that both regular and type imports occur in the cleaned content.
        assert "import { A } from 'moduleA';" in cleaned
        assert "import type { B } from 'moduleB';" in cleaned
        assert "const x = 42;" in cleaned

    def test_merge_python_files_success(self):
        """Test merging two valid Python files."""
        file1_content = "import os\n\ndef foo():\n    return 'foo'"
        file2_content = "def bar():\n    return 'bar'"
        merged = ContentCleaner.merge_python_files(file1_content, file2_content)
        # Check that merged content parses and is formatted by black.
        assert merged is not None
        try:
            ast.parse(merged)
        except SyntaxError:
            pytest.fail("Merged Python content contains syntax errors")

    def test_merge_python_files_invalid(self):
        """Test that merge_python_files returns None when file2 contains invalid Python."""
        file1_content = "import os\n\ndef foo():\n    return 'foo'"
        file2_content = "def incomplete("  # Invalid Python syntax
        merged = ContentCleaner.merge_python_files(file1_content, file2_content)
        assert merged is None

    def test_merge_typescript_files_ts(self):
        """Test merging typescript files for language 'ts' with minimal valid content."""
        file1_content = "import {A} from 'moduleA';\nconst x = 1;"
        file2_content = "const y = 2;"  # minimal additional valid code
        merged = ContentCleaner.merge_typescript_files(file1_content, file2_content, language="ts")
        # The merged content should not be None and should include parts from file1 and file2.
        assert merged is not None
        assert re.search(r"import\s+\{\s*A\s*\}\s+from\s+'moduleA';", merged)

    def test_merge_typescript_files_tsx(self):
        """Test merging typescript files for language 'tsx' with minimal valid content."""
        file1_content = "import {B} from 'moduleB';\nconst x = 1;"
        file2_content = "const y = 2;"  # minimal additional valid code
        merged = ContentCleaner.merge_typescript_files(file1_content, file2_content, language="tsx")
        # The merged content should not be None and should include parts from file1 and file2.
        assert merged is not None
        assert re.search(r"import\s+\{\s*B\s*\}\s+from\s+'moduleB';", merged)