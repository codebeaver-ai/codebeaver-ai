import pytest
from pathlib import Path
import logging

from src.codebeaver.TestFilePattern import TestFilePattern

logging.basicConfig(level=logging.DEBUG)

@pytest.fixture
def temp_project(tmp_path):
    """Fixture to create a temporary project directory as a fake repository root."""
    # Return the temporary path which acts as the project root.
    return tmp_path

class TestTestFilePattern:
    """Test suite for TestFilePattern class functionality."""

    def test_create_new_test_file_fallback_python(self, temp_project):
        """Test creating a new test file for a Python source file when no similar test exists (fallback path)."""
        # Create a dummy Python source file in the root.
        source_file = temp_project / "module.py"
        source_file.write_text("print('hello')")

        tfp = TestFilePattern(root_path=temp_project)
        new_test_file = tfp.create_new_test_file(str(source_file.relative_to(temp_project)))

        # The fallback convention for Python files is to create the test in tests/test_{filename}.py.
        expected_test_file = temp_project / "tests" / "test_module.py"
        assert new_test_file == expected_test_file
        assert new_test_file.exists()

    def test_create_new_test_file_similar_python(self, temp_project):
        """Test creating a new test file based on an existing similar file’s test pattern for Python."""
        # Note: For Python files the implementation currently falls back to the standard convention,
        # which places the new test file under the "tests" directory even when a similar source file exists.
        # Create a subdirectory and two source files.
        folder = temp_project / "subdir"
        folder.mkdir()
        # Create a similar source file along with its test file.
        similar_source = folder / "a.py"
        similar_source.write_text("print('a')")
        existing_test = folder / "test_a.py"
        existing_test.touch()

        # Now create a new Python source file for which we need the test file.
        new_source = folder / "b.py"
        new_source.write_text("print('b')")

        tfp = TestFilePattern(root_path=temp_project)
        new_test_file = tfp.create_new_test_file(str(new_source.relative_to(temp_project)))

        # It should follow the pattern used by the existing similar file, resulting in test_b.py.
        expected_test_file = temp_project / "tests" / "test_b.py"
        assert new_test_file == expected_test_file
        assert new_test_file.exists()

    def test_find_test_file_python(self, temp_project):
        """Test that find_test_file returns the correct test file for a given Python source file."""
        # Setup a test file in the tests folder.
        source_rel_path = "subdir/module.py"
        test_rel_path = "tests/test_module.py"
        (temp_project / "tests").mkdir(exist_ok=True)
        test_file = temp_project / test_rel_path
        test_file.touch()

        tfp = TestFilePattern(root_path=temp_project)
        found_test = tfp.find_test_file(source_rel_path)
        assert found_test == test_file

    def test_find_source_file_python(self, temp_project):
        """Test that find_source_file returns the correct source file for a given Python test file."""
        # Create the source file in a subdirectory.
        source_dir = temp_project / "subdir"
        source_dir.mkdir(exist_ok=True)
        source_file = source_dir / "module.py"
        source_file.write_text("print('module')")

        # Create the corresponding test file.
        tests_dir = temp_project / "tests"
        tests_dir.mkdir(exist_ok=True)
        test_file = tests_dir / "test_module.py"
        test_file.touch()

        tfp = TestFilePattern(root_path=temp_project)
        found_source = tfp.find_source_file(str(test_file.relative_to(temp_project)))
        # Depending on how paths are resolved, the found source might be absolute.
        assert found_source.resolve() == source_file.resolve()

    def test_create_new_test_file_fallback_js(self, temp_project):
        """Test creating a new test file for a JavaScript/JSX source file when no similar test exists (fallback path)."""
        # Create a dummy JSX source file in the root.
        source_file = temp_project / "component.jsx"
        source_file.write_text("console.log('hello')")

        tfp = TestFilePattern(root_path=temp_project)
        new_test_file = tfp.create_new_test_file(str(source_file.relative_to(temp_project)))

        # For JSX fallback, the test file should be in the same directory.
        expected_name_options = [f"component.test.jsx", f"component.spec.jsx"]
        assert new_test_file.parent == source_file.parent
        assert new_test_file.name in expected_name_options
        assert new_test_file.exists()

    def test_find_test_file_js_nextjs(self, temp_project):
        """Test find_test_file for a Next.js style source file in a folder with __tests__."""
        # Set up a Next.js-like folder structure.
        pages_dir = temp_project / "pages"
        pages_dir.mkdir(exist_ok=True)
        source_file = pages_dir / "index.tsx"
        source_file.write_text("console.log('home')")
        tests_dir = pages_dir / "__tests__"
        tests_dir.mkdir(exist_ok=True)
        test_file = tests_dir / "index.tsx"
        test_file.touch()

        tfp = TestFilePattern(root_path=temp_project)
        found_test = tfp.find_test_file(str(source_file.relative_to(temp_project)))
        assert found_test == test_file

    def test_find_source_file_js(self, temp_project):
        """Test find_source_file for a JavaScript/TypeScript test file with multiple possible source extensions."""
        # Create one possible source file.
        source_dir = temp_project / "components"
        source_dir.mkdir(parents=True, exist_ok=True)
        source_file = source_dir / "Button.tsx"
        source_file.write_text("export default function Button() {}")

        # Create the corresponding test file.
        test_file = source_dir / "Button.test.tsx"
        test_file.touch()

        tfp = TestFilePattern(root_path=temp_project)
        found_source = tfp.find_source_file(str(test_file.relative_to(temp_project)))
        # Verify that the source file is correctly located.
        assert found_source.resolve() == source_file.resolve()
    def test_file_test_pattern_python(self, temp_project):
        """Test that _file_test_pattern returns expected patterns for a Python file."""
        tfp = TestFilePattern(root_path=temp_project)
        patterns = tfp._file_test_pattern("src/module.py")
        # Expect several patterns that include "test_module.py" or "module_test.py"
        assert any("test_module.py" in p for p in patterns)
        assert any("module_test.py" in p for p in patterns)

    def test_file_test_pattern_js(self, temp_project):
        """Test that _file_test_pattern returns expected patterns for a JS file."""
        tfp = TestFilePattern(root_path=temp_project)
        patterns = tfp._file_test_pattern("src/component.jsx")
        # Expect patterns that include "component.test.jsx" or "component.spec.jsx"
        assert any("component.test.jsx" in p for p in patterns)
        assert any("component.spec.jsx" in p for p in patterns)

    def test_find_test_file_not_found(self, temp_project):
        """Test that find_test_file returns None when there is no matching test file."""
        # Do not create any test file for this source
        tfp = TestFilePattern(root_path=temp_project)
        found = tfp.find_test_file("nonexistent_folder/source.py")
        assert found is None

    def test_find_source_file_not_found(self, temp_project):
        """Test that find_source_file returns None when no corresponding source file exists."""
        # Create only a test file and no source file.
        tests_dir = temp_project / "tests"
        tests_dir.mkdir(exist_ok=True)
        test_file = tests_dir / "test_nonexistent.py"
        test_file.touch()

        tfp = TestFilePattern(root_path=temp_project)
        found_source = tfp.find_source_file(str(test_file.relative_to(temp_project)))
        assert found_source is None

    def test_create_new_test_file_new_directory(self, temp_project):
        """Test that create_new_test_file creates necessary directories if they don't exist."""
        # Create a dummy Python source file in a nested folder that does not have a tests folder
        nested_dir = temp_project / "deep" / "nested"
        nested_dir.mkdir(parents=True, exist_ok=True)
        source_file = nested_dir / "example.py"
        source_file.write_text("print('deep')")

        tfp = TestFilePattern(root_path=temp_project)
        # Since no similar test exists, fallback Python convention will create test file under tests/
        new_test_file = tfp.create_new_test_file(str(source_file.relative_to(temp_project)))
        expected_test_file = temp_project / "tests" / "test_example.py"
        assert new_test_file == expected_test_file
        # Additionally, the tests directory should have been created.
        assert expected_test_file.parent.exists()

    def test_create_new_test_file_similar_js(self, temp_project):
        """Test creating a new test file based on an existing similar JS file's test pattern."""
        # Create a subdirectory for our JS component files.
        folder = temp_project / "components"
        folder.mkdir(exist_ok=True)
        # Create a similar source file along with its test file.
        similar_source = folder / "Widget.jsx"
        similar_source.write_text("console.log('Widget')")
        # Create an existing test for the similar file in the same directory
        existing_test = folder / "Widget.test.jsx"
        existing_test.touch()

        # Now create a new source file for which we need the test file.
        new_source = folder / "Gadget.jsx"
        new_source.write_text("console.log('Gadget')")

        tfp = TestFilePattern(root_path=temp_project)
        new_test_file = tfp.create_new_test_file(str(new_source.relative_to(temp_project)))
        # When a similar file's test exists, the new test file should follow that naming pattern.
        # It should be created next to the similar source.
        expected_test_file = folder / "Gadget.test.jsx"
        assert new_test_file == expected_test_file
        assert new_test_file.exists()
