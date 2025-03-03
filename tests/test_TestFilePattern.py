import os
from pathlib import Path
import pytest

# Import the TestFilePattern class from its source location.
from src.codebeaver.TestFilePattern import TestFilePattern

class TestTestFilePattern:
    """Tests for the TestFilePattern class functionality."""

    def test_create_new_file_fallback(self, tmp_path: Path):
        """Test creating a new test file using the fallback standard convention."""
        # Setup a fake project structure.
        project_root = tmp_path / "project"
        project_root.mkdir()
        # Create a source file in a new folder structure.
        src_dir = project_root / "src" / "module"
        src_dir.mkdir(parents=True)
        source_file = src_dir / "source.py"
        source_file.touch()

        # Instantiate our TestFilePattern with the project root.
        tfp = TestFilePattern(project_root)

        # Run create_new_test_file, expecting fallback to tests/test_source.py
        new_test = tfp.create_new_test_file(str(source_file.relative_to(project_root)))
        expected_test = project_root / "tests" / "test_source.py"

        # Verify that the file was created and is at the expected location.
        assert new_test == expected_test
        assert expected_test.exists()

    def test_create_new_file_with_similar_and_pattern(self, tmp_path: Path):
        """Test that the naming convention is copied from a similar file’s test file."""
        # Setup a fake project structure.
        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create a source file that we want to create a test for.
        src_dir = project_root / "src" / "module"
        src_dir.mkdir(parents=True)
        target_file = src_dir / "target.py"
        target_file.touch()

        # Create a similar source file and its associated test file.
        similar_file = src_dir / "other.py"
        similar_file.touch()

        # For Python, the test patterns include "test_other.py" so we create that.
        similar_test = project_root / "test_other.py"
        similar_test.touch()

        # Instantiate our TestFilePattern with the project root.
        tfp = TestFilePattern(project_root)

        # Run create_new_test_file; it should pick up the naming based on similar_test.
        new_test = tfp.create_new_test_file(str(target_file.relative_to(project_root)))
        # Expected new test file: "test_target.py" (replacing "other" with "target")
        expected_test = project_root / "tests" / "test_target.py"

        # Verify that the file was created at the expected location.
        assert new_test == expected_test
        assert expected_test.exists()

    def test_find_test_file(self, tmp_path: Path):
        """Test finding the test file for a given source file when it exists."""
        # Setup a fake project structure.
        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create a source file.
        src_dir = project_root / "src" / "module"
        src_dir.mkdir(parents=True)
        source_file = src_dir / "source.py"
        source_file.touch()

        # Create a test file based on one of the test patterns.
        tests_dir = project_root / "tests"
        tests_dir.mkdir(parents=True)
        test_file = tests_dir / "test_source.py"
        test_file.touch()

        # Instantiate the TestFilePattern.
        tfp = TestFilePattern(project_root)

        # Call find_test_file with the relative path of the source file.
        found = tfp.find_test_file(str(source_file.relative_to(project_root)))
        assert found is not None
        assert found.resolve() == test_file.resolve()

    def test_find_test_file_no_match(self, tmp_path: Path):
        """Test that find_test_file returns None when no test file exists."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create a source file without a corresponding test file.
        src_dir = project_root / "src" / "module"
        src_dir.mkdir(parents=True)
        source_file = src_dir / "nomatch.py"
        source_file.touch()

        tfp = TestFilePattern(project_root)
        found = tfp.find_test_file(str(source_file.relative_to(project_root)))
        assert found is None

    def test_find_source_file(self, tmp_path: Path):
        """Test finding the source file for a given test file when it exists."""
        # Setup a fake project structure.
        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create a source file.
        src_dir = project_root / "src" / "module"
        src_dir.mkdir(parents=True)
        source_file = src_dir / "source.py"
        source_file.touch()

        # Create its corresponding test file using the naming convention.
        tests_dir = project_root / "tests"
        tests_dir.mkdir(parents=True)
        test_file = tests_dir / "test_source.py"
        test_file.touch()

        tfp = TestFilePattern(project_root)
        found = tfp.find_source_file(str(test_file.relative_to(project_root)))
        # Our basic matching should find the source file we created.
        assert found is not None
        assert found.resolve() == source_file.resolve()

    def test_find_source_file_no_match(self, tmp_path: Path):
        """Test that find_source_file returns None when no source file exists."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create a test file without a corresponding source file.
        tests_dir = project_root / "tests"
        tests_dir.mkdir(parents=True)
        test_file = tests_dir / "test_nomatch.py"
        test_file.touch()

        tfp = TestFilePattern(project_root)
        found = tfp.find_source_file(str(test_file.relative_to(project_root)))
        assert found is None

    def test_create_new_file_in_nextjs_structure(self, tmp_path: Path):
        """Test creating a new test file for a JS/TS file in a Next.js folder structure. This is currently a placeholder test."""
        # Setup a fake Next.js project structure with pages directory.
        project_root = tmp_path / "project"
        project_root.mkdir()

        pages_dir = project_root / "pages"
        pages_dir.mkdir(parents=True)

        # Create a JS source file in "pages" to simulate a Next.js page.
        source_file = pages_dir / "About.jsx"
        source_file.touch()

        tfp = TestFilePattern(project_root)
        new_test = tfp.create_new_test_file(str(source_file.relative_to(project_root)))

        # Expected new test file location for Next.js: in __tests__ folder at the same level as source.
        expected_test = pages_dir / "__tests__" / "About.test.jsx"

        assert new_test == expected_test
        assert new_test.exists()

    def test_find_source_file_for_js(self, tmp_path: Path):
        """Test that find_source_file can locate a TS/JS source file for a given test file using glob patterns."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create a JS/TS source file in a nested directory.
        src_dir = project_root / "src" / "module"
        src_dir.mkdir(parents=True)
        source_file = src_dir / "component.tsx"
        source_file.touch()

        # Create a test file for the component using the naming convention.
        tests_dir = project_root / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_component.tsx"
        test_file.touch()

        tfp = TestFilePattern(project_root)
        found = tfp.find_source_file(str(test_file.relative_to(project_root)))
        assert found is not None, "Source file was not found for the given test file."
        assert found.resolve() == source_file.resolve(), f"Expected source file {source_file}, but got {found}"
        """Test creating a new test file for a JS/TS file in a Next.js folder structure."""
        project_root = tmp_path / "project"
        project_root.mkdir(exist_ok=True)

        # Create a JS source file in a "pages" folder to simulate Next.js structure.
        pages_dir = project_root / "pages"
        pages_dir.mkdir(parents=True)
        source_file = pages_dir / "Home.tsx"
        source_file.touch()

        tfp = TestFilePattern(project_root)
        new_test = tfp.create_new_test_file(str(source_file.relative_to(project_root)))

        # By standard, if no similar test exists, it should create the test file in the __tests__ folder with "test" inserted.
        expected_test = source_file.parent / "__tests__" / "Home.test.tsx"
        assert new_test == expected_test
        assert new_test.exists()

# End of tests for TestFilePattern
    def test_create_new_test_file_already_exists(self, tmp_path: Path):
        """Test that create_new_test_file returns the existing test file if it already exists."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create a source file.
        src_dir = project_root / "src" / "module"
        src_dir.mkdir(parents=True)
        source_file = src_dir / "source.py"
        source_file.touch()

        # Pre-create the expected test file using fallback convention.
        tests_dir = project_root / "tests"
        tests_dir.mkdir(parents=True)
        expected_test = tests_dir / "test_source.py"
        expected_test.touch()

        tfp = TestFilePattern(project_root)
        new_test = tfp.create_new_test_file(str(source_file.relative_to(project_root)))

        # The returned test file should be the same as the already existing one.
        assert new_test == expected_test
        assert new_test.exists()

    def test_find_source_file_multiple_matches(self, tmp_path: Path):
        """Test that find_source_file returns the direct match when multiple source files exist."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create a candidate source file in the project root.
        source_root = project_root / "source.py"
        source_root.touch()

        # Also create another candidate source file in a nested directory.
        src_dir = project_root / "src" / "module"
        src_dir.mkdir(parents=True)
        source_nested = src_dir / "source.py"
        source_nested.touch()

        # Create a test file corresponding to the source files.
        tests_dir = project_root / "tests"
        tests_dir.mkdir(parents=True)
        test_file = tests_dir / "test_source.py"
        test_file.touch()

        tfp = TestFilePattern(project_root)
        found = tfp.find_source_file(str(test_file.relative_to(project_root)))

        # Expect that the direct match in project_root is returned due to the order of search.
        assert found is not None
        assert found.resolve() == source_root.resolve()
    def test_create_new_file_fallback_js_ts(self, tmp_path: Path):
        """Test creating a new test file for a JS/TS source file using fallback convention.
        For a .ts file not in a Next.js folder, the fallback should create the test alongside the source file as 'main.test.ts'."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        src_dir = project_root / "src" / "module"
        src_dir.mkdir(parents=True)
        source_file = src_dir / "main.ts"
        source_file.touch()
        tfp = TestFilePattern(project_root)
        new_test = tfp.create_new_test_file(str(source_file.relative_to(project_root)))
        expected_test = src_dir / "main.test.ts"
        assert new_test == expected_test
        assert expected_test.exists()
    
    def test_find_test_file_via_glob(self, tmp_path: Path):
        """Test that find_test_file returns a test file when it is only discoverable via glob patterns.
        The test file is placed in a non‐direct location (e.g. in an 'other' folder) so that the direct path check fails,
        but the glob pattern (e.g. '**/test_custom.py') will find it."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        src_dir = project_root / "src" / "module"
        src_dir.mkdir(parents=True)
        source_file = src_dir / "custom.py"
        source_file.touch()
        # Create a test file in a different directory so that the direct resolution (e.g. project_root / "test_custom.py")
        # does not find it, but globbing (e.g. "**/test_custom.py") discovers it.
        other_dir = project_root / "other"
        other_dir.mkdir()
        glob_test_file = other_dir / "test_custom.py"
        glob_test_file.touch()
        tfp = TestFilePattern(project_root)
        found = tfp.find_test_file(str(source_file.relative_to(project_root)))
    def test_file_test_pattern_js(self, tmp_path: Path):
        """Test that _file_test_pattern returns expected JS/JSX patterns."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        tfp = TestFilePattern(project_root)
        # Call _file_test_pattern on a dummy JS file
        patterns = tfp._file_test_pattern("src/component.jsx")
        # Check that common JSX test naming patterns are included in the output.
        assert any("component.test" in pat or "component.spec" in pat for pat in patterns)

    def test_create_new_file_with_absolute_nonrelative_path(self, tmp_path: Path):
        """Test create_new_test_file when passed an absolute path not under the project root, forcing fallback."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        # Create a source file outside the project root
        external_source = tmp_path / "external.py"
        external_source.touch()
        tfp = TestFilePattern(project_root)
        # Pass the absolute path of the external file
        new_test = tfp.create_new_test_file(str(external_source.resolve()))
        # Fallback convention for non-JS files should create tests/test_external.py
        expected_test = project_root / "tests" / "test_external.py"
        assert new_test == expected_test
        assert expected_test.exists()

    def test_find_source_file_edge_complex_naming(self, tmp_path: Path):
        """Test find_source_file correctly resolves a source file from a test file with extra test markers."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        # Create a source file that is normally named "test_file.py"
        src_dir = project_root / "src" / "complex"
        src_dir.mkdir(parents=True)
        source_file = src_dir / "test_file.py"
        source_file.touch()
        # Create a test file with multiple test markers: prefix and suffix "test_"
        tests_dir = project_root / "tests"
        tests_dir.mkdir(parents=True)
        test_file = tests_dir / "test_test_file_test.py"
        test_file.touch()
        tfp = TestFilePattern(project_root)
        found = tfp.find_source_file(str(test_file.relative_to(project_root)))
        # The algorithm should remove the extra test prefixes/suffixes and locate "test_file.py"
        assert found is not None
        assert found.resolve() == source_file.resolve()

    def test_find_source_file_nextjs_route_group(self, tmp_path: Path):
        """Test that find_source_file can handle Next.js route group folders (with square brackets)."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        # Create a folder with Next.js route group naming (square brackets)
        src_dir = project_root / "src" / "[group]"
        src_dir.mkdir(parents=True)
        source_file = src_dir / "page.js"
        source_file.touch()
        # Create a test file in the tests folder for the file "page.js"
        tests_dir = project_root / "tests"
        tests_dir.mkdir(parents=True)
        test_file = tests_dir / "test_page.js"
        test_file.touch()
        tfp = TestFilePattern(project_root)
        found = tfp.find_source_file(str(test_file.relative_to(project_root)))
        assert found is not None
        assert found.resolve() == source_file.resolve()
    
    def test_file_test_pattern_python(self, tmp_path: Path):
        """Test that _file_test_pattern returns expected Python patterns."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        tfp = TestFilePattern(project_root)
        patterns = tfp._file_test_pattern("src/module/foo.py")
        # We expect to see patterns containing "test_foo.py"
        assert any("test_foo.py" in pat for pat in patterns)

    def test_find_test_file_via_glob_complete(self, tmp_path: Path):
        """Test that find_test_file returns a test file via glob patterns when direct path resolution fails."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        src_dir = project_root / "src" / "module"
        src_dir.mkdir(parents=True)
        source_file = src_dir / "custom.py"
        source_file.touch()
        # Create a test file in a different directory so that the direct resolution doesn't find it
        other_dir = project_root / "other"
        other_dir.mkdir()
        glob_test_file = other_dir / "test_custom.py"
        glob_test_file.touch()
        
        tfp = TestFilePattern(project_root)
        found = tfp.find_test_file(str(source_file.relative_to(project_root)))
        assert found is not None, "Should find the test file via glob patterns"
        assert found.resolve() == glob_test_file.resolve(), f"Expected {glob_test_file.resolve()}, got {found.resolve()}"

    def test_find_test_file_empty_path(self, tmp_path: Path):
        """Test that find_test_file returns None when provided an empty file path."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        tfp = TestFilePattern(project_root)
        found = tfp.find_test_file("")
        assert found is None

    def test_create_new_file_fallback_jsx(self, tmp_path: Path):
        """Test creating a new test file for a JSX source file (non‑Next.js) using the fallback convention."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        src_dir = project_root / "src" / "module"
        src_dir.mkdir(parents=True)
        source_file = src_dir / "widget.jsx"
        source_file.touch()
        tfp = TestFilePattern(project_root)
        new_test = tfp.create_new_test_file(str(source_file.relative_to(project_root)))
        # For non‑Next.js JSX, we expect the test file to be created next to the source file following fallback rules.
        expected_test = src_dir / "widget.test.jsx"
        assert new_test == expected_test
        assert expected_test.exists()
    def test_file_test_pattern_with_leading_underscore_js(self, tmp_path: Path):
        """Test that _file_test_pattern correctly strips leading underscores in JS file names."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        tfp = TestFilePattern(project_root)
        patterns = tfp._file_test_pattern("src/_component.jsx")
        # Ensure the underscore is stripped so that "component" (without _) appears in the test patterns
        assert any("component.test" in p or "component.spec" in p for p in patterns), f"Patterns: {patterns}"

    def test_find_source_file_absolute(self, tmp_path: Path):
        """Test that find_source_file works correctly even when given an absolute test file path."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        src_dir = project_root / "src" / "module"
        src_dir.mkdir(parents=True)
        source_file = src_dir / "source.py"
        source_file.touch()
        tests_dir = project_root / "tests"
        tests_dir.mkdir(parents=True)
        test_file = tests_dir / "test_source.py"
        test_file.touch()
        tfp = TestFilePattern(project_root)
        found = tfp.find_source_file(str(test_file.resolve()))
        assert found is not None, "Should find the source file from an absolute test file path"
        assert found.resolve() == source_file.resolve()

    def test_file_test_pattern_unknown_extension(self, tmp_path: Path):
        """Test that _file_test_pattern returns Python test patterns for unknown file extensions."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        tfp = TestFilePattern(project_root)
        patterns = tfp._file_test_pattern("src/file.txt")
        # Since .txt is not a JS/TS extension, the python patterns should be returned.
        assert any("test_file.py" in pat for pat in patterns), f"Unexpected patterns: {patterns}"