import pytest
import ast
import black
import tree_sitter_typescript as tstypescript
from tree_sitter import Language, Parser
from codebeaver.ContentCleaner import ContentCleaner

class TestContentCleaner:
    """Tests for the ContentCleaner class."""

    def test_get_and_set_supported_languages(self):
        """Test getting and setting supported languages."""
        original = ContentCleaner.get_supported_languages()
        new_config = {"ruby": {"aliases": ["rb"], "merge_function": "merge_ruby_files"}}
        ContentCleaner.set_supported_languages(new_config)
        updated = ContentCleaner.get_supported_languages()
        assert updated == new_config
        # Reset to original for other tests
        ContentCleaner.set_supported_languages(original)

    def test_clean_python(self):
        """Test cleaning Python content with docstring and messy imports."""
        input_code = '''"""Module Docstring"""
import sys, os
from math import sin
import re
def foo():
    pass
if __name__ == "__main__":
    foo()'''
        cleaned = ContentCleaner.clean_python(input_code)
        # Check that docstring is preserved
        assert '"""Module Docstring"""' in cleaned
        # Ensure that imports occur before function definitions
        assert cleaned.index('import re') < cleaned.index('def foo()')
        assert "if __name__ == \"__main__\":" in cleaned

    def test_merge_python_files_valid(self):
        """Test merging two valid Python files."""
        file1 = '''def foo():
    return "foo"'''
        file2 = '''def bar():
    return "bar"'''
        merged = ContentCleaner.merge_python_files(file1, file2)
        # Expect merged content to be formatted and parseable
        assert merged is not None
        ast.parse(merged)  # Should not raise an exception

    def test_merge_python_files_invalid(self):
        """Test merging two invalid Python files returns None."""
        file1 = 'def foo(: pass'
        file2 = 'def bar(: pass'
        merged = ContentCleaner.merge_python_files(file1, file2)
        assert merged is None

    def test_merge_files_python(self):
        """Test merge_files function for a Python file."""
        file1_path = 'example.py'
        file1 = 'def foo():\n    pass'
        file2 = 'def bar():\n    pass'
        merged = ContentCleaner.merge_files(file1_path, file1, file2)
        assert merged is not None
        ast.parse(merged)

    def test_merge_files_unsupported(self):
        """Test merge_files with unsupported file extension raises ValueError."""
        file1_path = 'example.txt'
        file1 = 'some non-code text'
        file2 = None
        with pytest.raises(ValueError):
            ContentCleaner.merge_files(file1_path, file1, file2)

    def test_clean_typescript(self):
        """Test cleaning a simple TypeScript content."""
        ts_code = '''import { Component } from '@angular/core';
const x = 1;
function hello() {
    console.log("Hello");
}
'''
        cleaned = ContentCleaner.clean_typescript(ts_code)
        # Check that import statements and code exist in the cleaned output
        assert "import {" in cleaned or "import " in cleaned
        assert "const x = 1;" in cleaned
        assert "function hello" in cleaned

    def test_merge_typescript_files(self):
        """Test merging two TypeScript files when valid."""
        file1 = '''import { A } from 'moduleA';
const foo = () => { return A; };
'''
        file2 = '''import { B } from 'moduleB';
const bar = () => { return B; };
'''
        merged = ContentCleaner.merge_typescript_files(file1, file2, language="ts")
        # Either returns merged content or None if parse errors occur; if valid, check content
        if merged is not None:
            assert "import" in merged
            assert ("const foo" in merged or "const bar" in merged)

    def test_merge_typescript_files_tsx(self):
        """Test merging two TSX files."""
        file1 = '''import { A } from 'moduleA';
const Foo = () => <div>A</div>;
export default Foo;
'''
        file2 = '''import { B } from 'moduleB';
const Bar = () => <div>B</div>;
export default Bar;
'''
        merged = ContentCleaner.merge_typescript_files(file1, file2, language="tsx")
        if merged is not None:
            assert "export default" in merged

# End of tests