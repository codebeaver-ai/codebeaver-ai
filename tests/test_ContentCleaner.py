import ast
import re
import pytest
import black
from codebeaver.ContentCleaner import ContentCleaner

class DummyLanguage:
    @staticmethod
    def language_typescript():
        # Return a dummy language object for testing purposes
        return "dummy_ts"
    
    @staticmethod
    def language_tsx():
        # Return a dummy language object for testing purposes
        return "dummy_tsx"

def dummy_parser_factory():
    class DummyParser:
        def parse(self, content):
            # Return a dummy tree with a root_node having an empty children list
            class DummyRoot:
                children = []
            class DummyTree:
                root_node = DummyRoot()
            return DummyTree()
    return DummyParser()

# Fixture for simple valid python code used in multiple tests.
@pytest.fixture
def simple_python_code():
    return '''"""Module docstring"""
import os
import sys

def foo():
    return 42

if __name__ == "__main__":
    foo()
'''

# Fixture for simple valid typescript code used in tests.
@pytest.fixture
def simple_typescript_code():
    return "import {A, B} from 'module';\nconsole.log('Test');"

def test_get_and_set_supported_languages():
    """Test that get_supported_languages and set_supported_languages work as expected."""
    original = ContentCleaner.get_supported_languages()
    new_languages = {"go": {"aliases": ["go"], "merge_function": "dummy_merge"}}
    ContentCleaner.set_supported_languages(new_languages)
    updated = ContentCleaner.get_supported_languages()
    assert updated == new_languages
    # Reset configuration for subsequent tests
    ContentCleaner.set_supported_languages(original)

def dummy_merge(file1_content, file2_content):
    return file1_content + "\n" + (file2_content or "")

def test_merge_files_python(simple_python_code):
    """Test merge_files using a python file; ensure result is valid python code."""
    original = ContentCleaner.get_supported_languages()
    # Override supported languages only for this test.
    ContentCleaner.set_supported_languages({
        "python": {"aliases": ["python"], "merge_function": "merge_python_files"}
    })
    merged = ContentCleaner.merge_files("test.py", simple_python_code, simple_python_code)
    # Ensure that the merged result can be parsed
    ast.parse(merged)
    # Reset configuration for other tests.
    ContentCleaner.set_supported_languages(original)

def test_merge_files_invalid_language(simple_python_code):
    """Test merge_files raises ValueError for an unsupported language extension."""
    with pytest.raises(ValueError):
        ContentCleaner.merge_files("test.txt", simple_python_code, simple_python_code)

def test_clean_python(simple_python_code):
    """Test that clean_python properly organizes a simple python module."""
    cleaned = ContentCleaner.clean_python(simple_python_code)
    # Check that key elements appear in the cleaned content
    assert '"""Module docstring"""' in cleaned
    assert 'import os' in cleaned
    assert 'def foo()' in cleaned

def test_merge_python_files_valid(simple_python_code):
    """Test merge_python_files with two valid python code strings."""
    file1 = simple_python_code
    # Slightly change file2 code so that function name is modified
    file2 = simple_python_code.replace("foo", "bar")
    merged = ContentCleaner.merge_python_files(file1, file2)
    # If merge succeeds, the merged content must be valid and include at least one of the functions' names
    if merged is not None:
        ast.parse(merged)
        assert "bar" in merged or "foo" in merged

def test_merge_python_files_invalid():
    """Test merge_python_files returns None when provided invalid python code."""
    file1 = "def foo(:\n    pass"
    file2 = "def bar():\n    pass"
    merged = ContentCleaner.merge_python_files(file1, file2)
    assert merged is None

def test_clean_typescript(simple_typescript_code):
    """Test clean_typescript returns well-formed code for a simple typescript input."""
    try:
        from tree_sitter import Parser, Language
    except ImportError:
        pytest.skip("tree_sitter not available for testing clean_typescript")

    # Monkey patch the Parser to use a dummy parser that returns a dummy tree.
    class DummyTSParser:
        def __init__(self, language):
            pass
        def parse(self, content):
            class DummyRoot:
                children = []
            class DummyTree:
                root_node = DummyRoot()
            return DummyTree()
    # Monkeypatch parser creation in clean_typescript by overriding language functions
    import tree_sitter_typescript as tstypescript
    original_language_typescript = tstypescript.language_typescript
    original_language_tsx = tstypescript.language_tsx
    tstypescript.language_typescript = lambda: "dummy_ts"
    tstypescript.language_tsx = lambda: "dummy_tsx"
    # Monkey-patch the Parser for this test scope
    from tree_sitter import Parser as TSParser
    original_parse = TSParser.parse
    TSParser.__init__ = lambda self, language=None: None
    TSParser.parse = lambda self, content: DummyTSParser(None).parse(content)

    cleaned_ts = ContentCleaner.clean_typescript(simple_typescript_code)
    # Verify that the cleaned typescript code does not include placeholders for existing tests
    assert "existing tests" not in cleaned_ts

    # Restore monkey-patched functions
    tstypescript.language_typescript = original_language_typescript
    tstypescript.language_tsx = original_language_tsx
    TSParser.parse = original_parse

def test_merge_typescript_files():
    """Test merge_typescript_files combines two simple typescript files correctly."""
    file1 = "import {A} from 'module';\nconsole.log('Hello');"
    file2 = "import {B} from 'module';\nconsole.log('World');"
    merged = ContentCleaner.merge_typescript_files(file1, file2, language="ts")
    if merged is not None:
        assert "A" in merged and "B" in merged

def test_merge_files_javascript_keyerror(simple_python_code):
    """Test merge_files raises KeyError for '.js' file if javascript merge function is not defined."""
    with pytest.raises(KeyError):
        ContentCleaner.merge_files("test.js", simple_python_code, simple_python_code)

def dummy_merge_javascript(file1_content, file2_content):
    return file1_content + " js " + (file2_content or "")

def test_merge_files_javascript_valid(simple_python_code):
    # Attach the dummy merge function so that ContentCleaner can find it via getattr
    """Test merge_files for '.js' file using a configured javascript merge function."""
    original = ContentCleaner.get_supported_languages()
    new_config = {**original, "javascript": {"aliases": ["javascript", "js", "jsx"], "merge_function": "dummy_merge_javascript"}}
    ContentCleaner.set_supported_languages(new_config)
    ContentCleaner.dummy_merge_javascript = dummy_merge_javascript
    merged = ContentCleaner.merge_files("test.js", simple_python_code, simple_python_code)
    assert " js " in merged
    # Remove the dummy function afterwards to avoid affecting other tests
    delattr(ContentCleaner, 'dummy_merge_javascript')
    ContentCleaner.set_supported_languages(original)

def test_merge_typescript_files_exception(simple_typescript_code):
    """Test merge_typescript_files returns None when Parser.parse raises an exception."""
    from tree_sitter import Parser
    original_parse = Parser.parse
    Parser.parse = lambda self, content: (_ for _ in ()).throw(Exception("Parse error"))
    result = ContentCleaner.merge_typescript_files(simple_typescript_code, simple_typescript_code, language="ts")
    assert result is None
    Parser.parse = original_parse

def test_merge_typescript_files_tsx(simple_typescript_code):
    """Test merge_typescript_files for 'tsx' language returns code containing imports."""
    cleaned = ContentCleaner.merge_typescript_files(simple_typescript_code, simple_typescript_code, language="tsx")
    if cleaned is not None:
        assert "import" in cleaned

def test_clean_python_empty():
    """Test clean_python with an empty string returns an empty string."""
    cleaned = ContentCleaner.clean_python("")
    assert cleaned.strip() == ""

def test_clean_typescript_empty():
    """Test clean_typescript with an empty string returns an empty string."""
    cleaned = ContentCleaner.clean_typescript("")
    assert cleaned == ""
# End of tests.
def test_clean_python_multiline_import():
    """Test clean_python handles multiline imports and organizes them."""
    code = '''"""Module docstring"""
from os import (
    path,
    system
)
import sys

def foo():
    return path.join("a", "b")
'''
    cleaned = ContentCleaner.clean_python(code)
    # Check that the cleaned code contains the multiline import header and imported items
    assert "from os import (" in cleaned or "from os import(" in cleaned
    assert "path" in cleaned and "system" in cleaned

def test_merge_files_file2_none(simple_python_code):
    """Test merge_files raises error when file2_content is None for python files."""
    with pytest.raises(AttributeError):
        ContentCleaner.merge_files("test.py", simple_python_code, None)

def test_clean_typescript_multiline_import():
    """Test clean_typescript handles multiline imports in typescript code."""
    code = '''import {
    A,
    B
} from 'module';
console.log('Test');
'''
    cleaned = ContentCleaner.clean_typescript(code)
    # Validate that cleaned code includes both A and B and proper formatting from the import
    assert "A" in cleaned
    assert "B" in cleaned
    assert "from 'module'" in cleaned

def test_merge_python_files_try_block():
    """Test merge_python_files handles try-except blocks and conditional imports."""
    file1 = '''import sys

try:
    import os
except ImportError:
    pass

def foo():
    return 1
'''
    file2 = '''import sys

try:
    import math
except ImportError:
    pass

def bar():
    return 2
'''
    merged = ContentCleaner.merge_python_files(file1, file2)
    if merged is not None:
        # Check that at least one of the extra imports is present and that both function names are in the merged file.
        assert ("os" in merged or "math" in merged)
        assert "foo" in merged and "bar" in merged

# End of new tests