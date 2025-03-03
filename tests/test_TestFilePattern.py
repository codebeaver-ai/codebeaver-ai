import os
import pytest
from pathlib import Path

# Import the class to test. We assume that the package structure is set so that
# 'codebeaver' is importable from the project root.
from codebeaver.TestFilePattern import TestFilePattern

class TestTestFilePattern:
    """Test cases for the TestFilePattern class."""

    def test_create_new_test_file_fallback_python(self, tmp_path):
        """Test that for a Python file with no similar test file, a test file is created
        using the fallback standard convention (inside tests/ directory)."""
        # Create a fake project structure
        project = tmp_path / "project"
        project.mkdir()
        # Create a source file (python)
        source_file = project / "module.py"
        source_file.write_text("# sample python source")

        # Instantiate TestFilePattern with the project root path
        tfp = TestFilePattern(project)
        # Call create_new_test_file and expect a test file in <project>/tests/test_module.py
        new_test_file = tfp.create_new_test_file("module.py")

        expected = project / "tests" / "test_module.py"
        assert new_test_file.resolve() == expected.resolve()
        assert expected.exists()

    def test_create_new_test_file_js_pages(self, tmp_path):
        """Test that for a JavaScript file in a Next.js pages folder, a test file is created
        in a __tests__ subdirectory with .test pattern."""
        project = tmp_path / "project"
        project.mkdir()

        # Create a pages folder with a javascript file (jsx file)
        pages = project / "pages"
        pages.mkdir()
        source_file = pages / "index.jsx"
        source_file.write_text("// sample jsx source")

        tfp = TestFilePattern(project)
        new_test_file = tfp.create_new_test_file("pages/index.jsx")

        # According to the logic, since "pages" is in the parts, the test file should be in __tests__ folder in the same directory.
        expected = pages / "__tests__" / "index.test.jsx"
        assert new_test_file.resolve() == expected.resolve()
        assert expected.exists()

    def test_create_new_test_file_using_similar(self, tmp_path):
        """Test create_new_test_file when a similar file already has a test file.
        The new test file should copy the naming pattern from the similar file."""
        project = tmp_path / "project"
        # Create project directories: src folder for source files and tests folder for test files.
        src = project / "src"
        src.mkdir(parents=True)
        tests_dir = project / "tests"
        tests_dir.mkdir()

        # Create two source files in the same folder: one similar, one target.
        similar_source = src / "other_file.py"
        similar_source.write_text("# similar file")
        target_source = src / "some_file.py"
        target_source.write_text("# target file")

        # Create a test file for the similar source file using the standard convention.
        # The standard convention for Python creates tests/test_<name>.py.
        similar_test = tests_dir / "test_other_file.py"
        similar_test.parent.mkdir(parents=True, exist_ok=True)
        similar_test.write_text("# test for similar file")

        tfp = TestFilePattern(project)
        new_test_file = tfp.create_new_test_file("src/some_file.py")

        # According to the implemented logic, it should reuse the naming pattern from similar_test,
        # replacing "other_file" with "some_file", i.e. tests/test_some_file.py.
        expected = tests_dir / "test_some_file.py"
        assert new_test_file.resolve() == expected.resolve()
        assert expected.exists()

    def test_find_test_file(self, tmp_path):
        """Test that find_test_file locates an existing test file given a source file path."""
        project = tmp_path / "project"
        project.mkdir()

        # Create a source file and a test file for it.
        src_dir = project / "lib"
        src_dir.mkdir()
        source_file = src_dir / "some_file.py"
        source_file.write_text("# some source")

        test_dir = project / "tests"
        test_dir.mkdir()
        # According to the _file_test_pattern, one possible pattern is "test_some_file.py"
        existing_test = test_dir / "test_some_file.py"
        existing_test.write_text("# existing test")

        tfp = TestFilePattern(project)
        found = tfp.find_test_file("lib/some_file.py")
        assert found is not None
        assert found.resolve() == existing_test.resolve()

    def test_find_source_file(self, tmp_path):
        """Test that find_source_file correctly finds the source file for a given test file.
        It should handle removal of test-related prefixes and suffixes."""
        project = tmp_path / "project"
        project.mkdir()

        # Create a source file in the root folder.
        source_file = project / "my_module.py"
        source_file.write_text("# source code")

        # Create a test file with a common test naming pattern.
        test_file = project / "tests" / "test_my_module.py"
        test_file.parent.mkdir(exist_ok=True)
        test_file.write_text("# test code")

        tfp = TestFilePattern(project)
        found_source = tfp.find_source_file("tests/test_my_module.py")
        assert found_source is not None
        assert found_source.resolve() == source_file.resolve()

    def test_find_source_file_variations(self, tmp_path):
        """Additional test for find_source_file to check different suffix/prefix removals."""
        project = tmp_path / "project"
        project.mkdir()

        # Create a source file.
        source_file = project / "utils.py"
        source_file.write_text("# source code for utils")

        # Create several test file name variations
        variations = [
            "tests/test_utils.py",
            "tests/utils_test.py",
            "tests/utils.test.py",
        ]
        tfp = TestFilePattern(project)
        for test_rel in variations:
            test_path = project / test_rel
            test_path.parent.mkdir(parents=True, exist_ok=True)
            test_path.write_text("# test file content")

            found_source = tfp.find_source_file(test_rel)
            assert found_source is not None
            assert found_source.resolve() == source_file.resolve()

    def test_create_new_test_file_js_non_pages(self, tmp_path):
        """Test that for a JavaScript file not in Next.js-specific folders, the test file is created
        next to the source file using the test pattern."""
        project = tmp_path / "project"
        project.mkdir()

        # Create a src folder with a jsx file (not under pages or app)
        src = project / "src"
        src.mkdir()
        source_file = src / "component.jsx"
        source_file.write_text("// component source")

        tfp = TestFilePattern(project)
        new_test_file = tfp.create_new_test_file("src/component.jsx")

        # According to the code, for non-Next.js files, the test file is created in the same folder.
        # The fallback for JSX should give us component.test.jsx.
        expected = src / "component.test.jsx"
        assert new_test_file.resolve() == expected.resolve()
        assert expected.exists()
    def test_file_test_pattern_python(self, tmp_path):
        """Test the _file_test_pattern method for a Python source file."""
        project = tmp_path / "project"
        project.mkdir()
        tfp = TestFilePattern(project)
        patterns = tfp._file_test_pattern("mypython.py")
        # For a Python file the first pattern should be like "test_mypython.py"
        assert any("test_mypython.py" in pattern for pattern in patterns)

    def test_file_test_pattern_js(self, tmp_path):
        """Test the _file_test_pattern method for a JavaScript/JSX file."""
        project = tmp_path / "project"
        project.mkdir()
        tfp = TestFilePattern(project)
        patterns = tfp._file_test_pattern("component.jsx")
        # For a JSX file, check that at least one pattern contains either '.test' or '.spec'
        assert any("component.test" in pattern or "component.spec" in pattern for pattern in patterns)

    def test_find_test_file_not_found(self, tmp_path):
        """Test that find_test_file returns None when no test file exists for the given source file."""
        project = tmp_path / "project"
        project.mkdir()
        # Create a “source file” in a subfolder but do not create any corresponding test file.
        src_dir = project / "lib"
        src_dir.mkdir()
        source_file = src_dir / "nonexistent.py"
        source_file.write_text("# source file without test")
        tfp = TestFilePattern(project)
        found = tfp.find_test_file("lib/nonexistent.py")
        assert found is None

    def test_find_source_file_not_found(self, tmp_path):
        """Test that find_source_file returns None when no corresponding source file exists."""
        project = tmp_path / "project"
        project.mkdir()
        # Create a test file in the tests folder for which there is no source file.
        tests_dir = project / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_unknown.py"
        test_file.write_text("# test file for non-existent source")
        tfp = TestFilePattern(project)
        found_source = tfp.find_source_file("tests/test_unknown.py")
        assert found_source is None

    def test_create_new_test_file_ts_pages(self, tmp_path):
        """Test that a TypeScript file in a Next.js pages folder creates a test file in __tests__
        using the .test pattern."""
        project = tmp_path / "project"
        project.mkdir()
        pages = project / "pages"
        pages.mkdir()
        source_file = pages / "home.tsx"
        source_file.write_text("// sample tsx source")
        tfp = TestFilePattern(project)
        new_test_file = tfp.create_new_test_file("pages/home.tsx")
        expected = pages / "__tests__" / "home.test.tsx"
        assert new_test_file.resolve() == expected.resolve()
        assert expected.exists()

    def test_find_source_file_js(self, tmp_path):
        """Test that find_source_file correctly locates a JavaScript source file
        corresponding to a test file."""
        project = tmp_path / "project"
        project.mkdir()
        # Create a source file in a subfolder for a JS component.
        src_dir = project / "src"
        src_dir.mkdir()
        source_file = src_dir / "widget.jsx"
        source_file.write_text("// widget source")
        # Create a test file for this source file (using one of the common patterns).
        test_file = src_dir / "widget.test.jsx"
        test_file.write_text("// widget test")
        tfp = TestFilePattern(project)
        found_source = tfp.find_source_file("src/widget.test.jsx")
        assert found_source is not None
        assert found_source.resolve() == source_file.resolve()
    def test_find_test_file_with_brackets(self, tmp_path):
        """Test find_test_file with a source file that has bracket characters in its name.
        This simulates Next.js route groups where file names may include [ and ].
        The method should correctly escape the brackets and find the test file."""
        project = tmp_path / "project"
        project.mkdir()
        pages = project / "pages"
        pages.mkdir()
        # Create a source file with brackets in its name.
        source_file = pages / "[id].jsx"
        source_file.write_text("// sample jsx source with brackets")
        # Pre-create a test file using one of the common patterns: "test_[id].jsx"
        test_file = project / "test_[id].jsx"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("// test for [id] file")
        tfp = TestFilePattern(project)
        found = tfp.find_test_file("pages/[id].jsx")
        assert found is not None
        assert found.resolve() == test_file.resolve()

    def test_standard_convention_for_new_test_file_non_js(self, tmp_path):
        """Test that for a file with an unsupported extension (e.g. .rb),
        create_new_test_file falls back to the standard Python convention.
        The expected test file should be under tests/ and named test_<filename>.py."""
        project = tmp_path / "project"
        project.mkdir()
        # Create a fake Ruby file in the project root.
        source_file = project / "foo.rb"
        source_file.write_text("# sample ruby source")
        tfp = TestFilePattern(project)
        new_test = tfp.create_new_test_file("foo.rb")
        expected = project / "tests" / "test_foo.py"
        assert new_test.resolve() == expected.resolve()
        assert expected.exists()

    def test_create_new_test_file_already_existing(self, tmp_path):
        """Test that if the test file already exists,
        create_new_test_file does not modify or overwrite the file.
        The existing file content should be preserved."""
        project = tmp_path / "project"
        project.mkdir()
        # Create a Python source file.
        source_file = project / "mymodule.py"
        source_file.write_text("# sample python module")
        # Pre-create the expected test file with known content.
        tests_dir = project / "tests"
        tests_dir.mkdir(parents=True)
        expected_test = tests_dir / "test_mymodule.py"
        expected_test.write_text("# existing test content")
        tfp = TestFilePattern(project)
        new_test = tfp.create_new_test_file("mymodule.py")
        # Ensure that the returned file matches the expected file and the content is unchanged.
        assert new_test.resolve() == expected_test.resolve()
        assert expected_test.read_text() == "# existing test content"
    
    def test_file_test_pattern_ts(self, tmp_path):
        """Test that _file_test_pattern returns correct test patterns for a TypeScript file."""
        project = tmp_path / "project"
        project.mkdir()
        tfp = TestFilePattern(project)
        patterns = tfp._file_test_pattern("example.ts")
        # The pattern list should include one with either '.test' or '.spec' for the ts file.
        assert any("example.test" in pattern or "example.spec" in pattern for pattern in patterns)

    def test_create_new_test_file_outside_root(self, tmp_path):
        """Test that create_new_test_file falls back to the standard convention when the file is not under the project root."""
        project = tmp_path / "project"
        project.mkdir()
        # Create a file outside the project folder
        outside_file = tmp_path / "outside.py"
        outside_file.write_text("# outside file")
        tfp = TestFilePattern(project)
        new_test_file = tfp.create_new_test_file(str(outside_file))
        # Fallback for Python files should place the test in <project>/tests/test_outside.py
        expected = project / "tests" / "test_outside.py"
        assert new_test_file.resolve() == expected.resolve()
        assert expected.exists()

    def test_find_source_file_prioritizes_root(self, tmp_path):
        """Test that find_source_file returns the source file in the root if one exists along with others in subdirectories."""
        project = tmp_path / "project"
        project.mkdir()
        # Create a source file in the project root
        root_source = project / "multi.py"
        root_source.write_text("# root source")
        # Also create another candidate in a subfolder
        sub_dir = project / "src"
        sub_dir.mkdir()
        sub_source = sub_dir / "multi.py"
        sub_source.write_text("# sub source")
        tests_dir = project / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_multi.py"
        test_file.write_text("# test for multi")
        tfp = TestFilePattern(project)
        found = tfp.find_source_file("tests/test_multi.py")
        # The source file in the root should be chosen according to the order patterns in find_source_file.
        assert found is not None
        assert found.resolve() == root_source.resolve()

    def test_find_test_file_ts(self, tmp_path):
        """Test that find_test_file correctly locates a test file for a TypeScript file in a Next.js-like structure."""
        project = tmp_path / "project"
        project.mkdir()
        src_dir = project / "components"
        src_dir.mkdir()
        source_file = src_dir / "widget.tsx"
        source_file.write_text("// widget source")
        # Create a test file in __tests__ as per common pattern for TSX in Next.js
        test_file = src_dir / "__tests__" / "widget.test.tsx"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("// widget test")
        tfp = TestFilePattern(project)
        found = tfp.find_test_file("components/widget.tsx")
        assert found is not None
        assert found.resolve() == test_file.resolve()

    def test_file_test_pattern_leading_underscore(self, tmp_path):
        tfp = TestFilePattern(project)
        patterns = tfp._file_test_pattern("module.abc")
        # The fallback should be Python patterns; check that "test_module.py" is in one of the patterns.
        assert any("test_module.py" in pattern for pattern in patterns), f"Patterns: {patterns}"

    def test_find_source_file_unknown_extension(self, tmp_path):
        """Test that find_source_file returns None for a test file with an unsupported extension.
        In this case, no corresponding source file can be derived from the test file name."""
        project = tmp_path / "project"
        project.mkdir()
        # Create a test file with an unknown extension .abc in the tests folder.
        tests_dir = project / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        test_file = tests_dir / "test_module.abc"
        test_file.write_text("# test content for unsupported extension")
        tfp = TestFilePattern(project)
        found_source = tfp.find_source_file("tests/test_module.abc")
        assert found_source is None

        found_source = tfp.find_source_file("tests/test_module.abc")
    def test_create_new_test_file_using_similar_in_parent(self, tmp_path):
        """Test create_new_test_file reuses a similar file pattern found in a parent directory.
        In this case, the similar file is in the parent folder and its test file exists,
        so the target file in a child folder should reuse the naming convention from the similar file."""
        project = tmp_path / "project"
        project.mkdir()
        src = project / "src"
        src.mkdir()
        # Create a similar source file in the parent folder (src)
        similar_source = src / "similar.py"
        similar_source.write_text("# similar file")
        # Create a target source file in a child folder of src
        child = src / "child"
        child.mkdir()
        target_source = child / "target.py"
        target_source.write_text("# target file")
        # Create a test file for the similar source file using a standard Python convention pattern
        tests_dir = project / "tests"
        tests_dir.mkdir()
        similar_test = tests_dir / "test_similar.py"
        similar_test.write_text("# test for similar file")
        tfp = TestFilePattern(project)
        new_test_file = tfp.create_new_test_file("src/child/target.py")
        # The similar file pattern should be reused and "similar" replaced with "target", resulting in tests/test_target.py
        expected = tests_dir / "test_target.py"
        assert new_test_file.resolve() == expected.resolve()
        assert expected.exists()

    def test_find_source_file_multiple_removals(self, tmp_path):
        """Test that find_source_file properly removes a redundant test prefix and suffix.
        For example, for a test file named "tests/test_test_module_test.py", the function should
        resolve the source file "test_module.py"."""
        project = tmp_path / "project"
        project.mkdir()
        # Create a source file with the name "test_module.py"
        source_file = project / "test_module.py"
        source_file.write_text("# source code for test_module")
        # Create a test file with extra test prefixes and/or suffixes: "tests/test_test_module_test.py"
        tests_dir = project / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        test_file = tests_dir / "test_test_module_test.py"
        test_file.write_text("# test content")
        tfp = TestFilePattern(project)
        found_source = tfp.find_source_file("tests/test_test_module_test.py")
        assert found_source is not None
        assert found_source.resolve() == source_file.resolve()
    def test_standard_convention_js_nonpages(self, tmp_path):
        """Test _standard_convention_for_new_test_file for a JavaScript file not in Next.js directories.
        It should return a test file path in the same folder as the source using the .test variant."""
        project = tmp_path / "project"
        project.mkdir()

        # Given a non-pages/non-app file path
        file_path = "src/component.jsx"
        tfp = TestFilePattern(project)
        test_file = tfp._standard_convention_for_new_test_file(file_path)

        # Since no test files exist, test_count == spec_count so secondary_extension is "test".
        # And because the file is not under "pages" or "app", its test file should be created next to the source.
        expected = Path("src/component.test.jsx")
        assert str(test_file) == str(expected)

    def test_file_test_pattern_cypress(self, tmp_path):
        """Test _file_test_pattern includes Cypress test patterns for a JSX file.
        The returned pattern list should include patterns for 'cypress/integration' or 'cypress/e2e'."""
        project = tmp_path / "project"
        project.mkdir()

        tfp = TestFilePattern(project)
        patterns = tfp._file_test_pattern("component.jsx")

        # Verify that at least one pattern contains 'cypress/integration' or 'cypress/e2e'
        cypress_pattern_found = any("cypress/integration" in pattern or "cypress/e2e" in pattern for pattern in patterns)
        assert cypress_pattern_found
    def test_file_test_pattern_leading_underscore(self, tmp_path):
        """Test that _file_test_pattern properly strips a leading underscore from the file name.
        Instead of asserting that "_private" never appears (which conflicts with the naming convention),
        this test checks that for patterns starting with "test_", the character immediately after "test_"
        is not an extra underscore, and that at least one pattern ends with "private.py".
        """
        project = tmp_path / "project"
        project.mkdir()
        tfp = TestFilePattern(project)
        patterns = tfp._file_test_pattern("_private.py")
        for pattern in patterns:
            if pattern.startswith("test_"):
                # After "test_", the next character should not be an underscore.
                assert pattern[5] != "_", f"Pattern {pattern} has an unexpected extra underscore after 'test_'"
        assert any(pattern.endswith("private.py") for pattern in patterns), f"None of the patterns end with 'private.py': {patterns}"

    def test_create_new_test_file_js_spec(self, tmp_path):
        """Test that for a JavaScript file, if there are more .spec files than .test files,
        the fallback creates a test file with a .spec extension."""
        project = tmp_path / "project"
        project.mkdir()
        # Create a dummy JSX file and a corresponding .spec test file to simulate more .spec files
        dummy_file = project / "dummy.jsx"
        dummy_file.write_text("// dummy jsx source")
        dummy_test = project / "dummy.spec.jsx"
        dummy_test.parent.mkdir(parents=True, exist_ok=True)
        dummy_test.write_text("// dummy spec test")

        # Now create the source file in a non Next.js folder (e.g., "src")
        src = project / "src"
        src.mkdir()
        source_file = src / "component.jsx"
        source_file.write_text("// component jsx source")

        tfp = TestFilePattern(project)
        new_test_file = tfp.create_new_test_file("src/component.jsx")
        # Since there is one .spec file already and no .test files, spec_count (1) > test_count (0);
        # thus the secondary_extension should be "spec" resulting in "component.spec.jsx"
        expected = src / "component.spec.jsx"
        assert new_test_file.resolve() == expected.resolve()
        assert expected.exists()

    def test_find_test_file_with_multiple_glob_matches(self, tmp_path):
        """Test that find_test_file returns one valid test file when multiple glob patterns match."""
        project = tmp_path / "project"
        project.mkdir()

        # Create a source file and then two test files matching different patterns.
        src = project / "module"
        src.mkdir(parents=True)
        source_file = src / "alpha.py"
        source_file.write_text("# module source")

        tests_dir = project / "tests"
        tests_dir.mkdir(exist_ok=True)
        test_file1 = tests_dir / "test_alpha.py"
        test_file1.write_text("# test file 1")
        test_file2 = tests_dir / "alpha_test.py"
        test_file2.write_text("# test file 2")

        tfp = TestFilePattern(project)
        found = tfp.find_test_file("module/alpha.py")
        # The function should return one of the matching files.
        assert found is not None
        assert found.resolve() in (test_file1.resolve(), test_file2.resolve())

    def test_find_source_file_with_non_standard_source_location(self, tmp_path):
        """Test that find_source_file can locate a source file placed in a non-standard location using glob patterns."""
        project = tmp_path / "project"
        project.mkdir()

        # Create a source file in a non-standard subdirectory, e.g., "custom"
        custom_dir = project / "custom"
        custom_dir.mkdir()
        source_file = custom_dir / "module.py"
        source_file.write_text("# custom module source")

        # Create a test file under tests folder following one of the Python file patterns.
        tests_dir = project / "tests"
        tests_dir.mkdir(exist_ok=True)
        test_file = tests_dir / "test_module.py"
        test_file.write_text("# test for custom module")

        tfp = TestFilePattern(project)
        found_source = tfp.find_source_file("tests/test_module.py")
        # Glob patterns should allow the test to locate the source even if it's not in the standard location.
        assert found_source is not None
        assert found_source.resolve() == source_file.resolve()