from pathlib import Path
import logging
import fnmatch
from .CodebeaverConfig import CodeBeaverConfig

logger = logging.getLogger('codebeaver')


class TestFilePattern:

    def __init__(self, root_path: Path, workspace_config: CodeBeaverConfig):
        """
        Initialize TestFilePattern with a root path.

        Args:
            root_path: Path object representing the root of the project
        """
        self.root_path = root_path
        self.workspace_config = workspace_config

    def create_new_test_file(self, file_path: Path) -> Path:
        """
        Create a new test file for a given source file.

        In order to best follow the test file naming convention of the repository, we should:
        - Try to see if there are similar files in the same folder as file_path_str
        - Check if any of them has a test test using the _test_patterns
        - If there is a test file, use the same naming convention and folder structure but with file_path_str
        - If there is no test file, go one parent folder up and try again
        - If everything else fails, fallback to standard convention

        Returns the absolute path to the new test file.
        """
        test_file = None
        extension = file_path.suffix

        # Start from the file's directory and work up
        current_dir = file_path.parent
        root_dir = self.root_path

        while current_dir.is_relative_to(root_dir):
            # Find similar files (same extension) in current directory
            similar_files = [
                f for f in current_dir.glob(f"*{extension}") if f != file_path
            ]

            # For each similar file, try to find its test file
            for similar_file in similar_files:
                relative_similar = similar_file.relative_to(root_dir)
                test_patterns = self._file_test_pattern(relative_similar)

                # Check each test pattern
                for pattern in test_patterns:
                    potential_test = root_dir / pattern
                    if potential_test.exists():
                        # Found a test file! Use its pattern to create our new test file
                        test_pattern = str(potential_test.relative_to(root_dir))
                        # Replace the original filename with our target filename in the pattern
                        test_pattern = test_pattern.replace(
                            similar_file.stem, file_path.stem
                        )
                        test_file = Path(test_pattern)
                        break

                if test_file:
                    break

            if test_file:
                break

            # Move up one directory if no test files found
            if current_dir == root_dir:
                break
            current_dir = current_dir.parent

        if test_file is None:
            # fallback to standard convention
            test_file = self._standard_convention_for_new_test_file(file_path)
        absolute_test_file = Path(self.root_path / test_file)
        # create the parent directory if it doesn't exist
        if not absolute_test_file.parent.exists():
            absolute_test_file.parent.mkdir(parents=True, exist_ok=True)
        if not absolute_test_file.exists():
            absolute_test_file.touch()

        logger.warning(f"Creating new test file: {absolute_test_file}")
        return absolute_test_file

    def _standard_convention_for_new_test_file(self, file_path: Path) -> Path:
        file_name = file_path.stem
        extension = file_path.suffix

        # Handle JavaScript/TypeScript files
        if extension in [".js", ".jsx", ".ts", ".tsx"]:
            test_count = 0
            spec_count = 0
            for test_file in self.root_path.rglob(f"*.test{extension}"):
                test_count += 1
            for spec_file in self.root_path.rglob(f"*.spec{extension}"):
                spec_count += 1

            secondary_extension = "test" if test_count >= spec_count else "spec"

            # For Next.js, create in __tests__ directory at same level as source
            if "pages" in file_path.parts or "app" in file_path.parts:
                test_dir = file_path.parent / "__tests__"
                # Prefer .test pattern, but fall back to .spec if test file already exists
                test_file = test_dir / f"{file_name}.{secondary_extension}{extension}"

            # For React/Jest, create test next to source file
            else:
                test_dir = file_path.parent
                # Prefer .test pattern, but fall back to .spec if test file already exists
                test_file = test_dir / f"{file_name}.{secondary_extension}{extension}"

            # If source uses .jsx/.tsx, convert test to .tsx for TypeScript
            if extension == ".jsx":
                test_file = test_file.with_suffix(".jsx")
            elif extension == ".tsx":
                test_file = test_file.with_suffix(".tsx")

        # Handle Python files
        else:
            tests_dir = self.root_path / "tests"
            test_file = tests_dir / f"test_{file_name}.py"

        return test_file

    def find_test_file(self, file_path: Path) -> Path | None:
        """
        Find the corresponding test file for a given source file.

        Args:
        file_path: The relative path from the root path to the source file. It has to include the folder path.
                    (e.g. "frontend/src/components/Button.tsx")

        Returns:
            Path: Absolute path to the matching test file if found
            None: If no matching test file exists
        """
        test_patterns = self._file_test_pattern(file_path)

        for pattern in test_patterns:
            rootpath = self.root_path

            # First try direct path resolution for Next.js route groups
            direct_path = rootpath / pattern
            if direct_path.exists():
                return direct_path

            # Then try glob patterns with escaped brackets for Next.js route groups
            pattern_escaped = pattern.replace("[", "[[]").replace("]", "[]]")
            matches = list(rootpath.glob(pattern_escaped))
            if matches:
                return matches[0]

            # Finally try standard glob pattern
            matches = list(rootpath.glob(pattern))
            if matches:
                return matches[0]

        return None

    def _file_test_pattern(self, file_path: Path) -> list[str]:
        """
        Return the test pattern for a given file path.
        """
        file_name = file_path.stem
        clean_name = file_name.lstrip("_")

        # Get file extension to determine language
        extension = Path(file_path).suffix
        # Define test patterns based on file type
        if extension in [".js", ".jsx", ".ts", ".tsx"]:
            # Common JavaScript/TypeScript test patterns
            test_patterns = [
                # Jest/React patterns
                f"test_{clean_name}{extension}",
                f"{clean_name}.test{extension}",
                f"{clean_name}.spec{extension}",
                f"__tests__/{clean_name}.test{extension}",
                f"__tests__/{clean_name}.spec{extension}",
                f"tests/{clean_name}.test{extension}",
                f"tests/{clean_name}.spec{extension}",
                f"test/{clean_name}.test{extension}",
                f"test/{clean_name}.spec{extension}",
                # Replace extension with test variants
                f"test_{clean_name}.ts",
                f"{clean_name}.test.ts",
                f"{clean_name}.spec.ts",
                f"test_{clean_name}.tsx",
                f"{clean_name}.test.tsx",
                f"{clean_name}.spec.tsx",
                # Cypress patterns
                f"cypress/integration/{clean_name}.spec{extension}",
                f"cypress/e2e/{clean_name}.cy{extension}",
                # Next.js patterns
                f"__tests__/{clean_name}{extension}",
                f"**/__tests__/{clean_name}{extension}",
                # Generic glob patterns
                f"**/test_{clean_name}{extension}",
                f"**/{clean_name}.test{extension}",
                f"**/{clean_name}.spec{extension}",
            ]
        else:  # Python and other languages
            test_patterns = [
                f"test_{clean_name}.py",
                f"{clean_name}_test.py",
                f"tests/test_{clean_name}.py",
                f"test/test_{clean_name}.py",
                f"tests/{clean_name}_test.py",
                f"test/{clean_name}.test.py",
                f"**/test_{clean_name}.py",
                f"**/{clean_name}_test.py",
                f"**/tests/test_{clean_name}.py",
                f"**/tests/{clean_name}_test.py",
                f"**/test/test_{clean_name}.py",
                f"**/test/{clean_name}_test.py",
            ]
        return test_patterns

    def find_source_file(self, test_file_path: str) -> Path | None:
        """Find the corresponding source file for a given test file."""
        file_name = Path(test_file_path).stem
        extension = Path(test_file_path).suffix

        # Remove test-related prefixes/suffixes
        source_name = file_name
        for prefix in ["test_"]:
            if source_name.startswith(prefix):
                source_name = source_name[len(prefix) :]
        for suffix in ["_test", ".test", ".spec", ".cy"]:
            if source_name.endswith(suffix):
                source_name = source_name[: -len(suffix)]

        # Determine source extension based on test file
        if extension in [".ts", ".tsx"]:
            source_extensions = [".ts", ".tsx", ".js", ".jsx"]
        elif extension == ".py":
            source_extensions = [".py"]
        else:
            source_extensions = [extension]

        # Build source file patterns
        source_patterns = []
        for ext in source_extensions:
            # Standard source locations
            source_patterns.extend(
                [
                    f"{source_name}{ext}",
                    f"**/{source_name}{ext}",
                    f"src/**/{source_name}{ext}",
                    f"src/pages/**/{source_name}{ext}",
                    f"src/components/**/{source_name}{ext}",
                    f"src/app/**/{source_name}{ext}",
                    # Then check other common Next.js directories
                    f"pages/**/{source_name}{ext}",
                    f"app/**/{source_name}{ext}",
                    f"components/**/{source_name}{ext}",
                    # Fallback to general patterns, but exclude node_modules
                    f"[!node_modules]/**/{source_name}{ext}",
                ]
            )

        # Search for source file
        rootpath = self.root_path

        for pattern in source_patterns:
            # Direct path check
            direct_path = rootpath / pattern
            if direct_path.exists():
                return direct_path

            # Next.js route groups with escaped brackets
            pattern_escaped = pattern.replace("[", "[[]").replace("]", "[]]")
            matches = list(rootpath.glob(pattern_escaped))
            if matches:
                return matches[0]

            # Standard glob pattern
            matches = list(rootpath.glob(pattern))
            if matches:
                return matches[0]

        return None

    def list_files_and_tests(self) -> tuple[list[Path], list[Path]]:
        """Returns a tuple of files and tests in the project, sorted by last modified date (newest first)."""
        logger.debug(f"Listing files and tests in {self.root_path}")
        all_files = list(self.root_path.rglob("**/*.py")) + list(self.root_path.rglob("**/*.js")) + list(self.root_path.rglob("**/*.ts")) + list(self.root_path.rglob("**/*.jsx")) + list(self.root_path.rglob("**/*.tsx"))
        ignore = self.workspace_config.ignore or []
        if self.workspace_config.unit:
            ignore.extend(self.workspace_config.unit.ignore or [])
        
        # Read patterns from .gitignore if it exists
        gitignore_path = self.root_path / ".gitignore"
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        # Convert .gitignore pattern to fnmatch pattern
                        if not line.startswith('*'):
                            line = f"*{line}*"
                        ignore.append(line)
        
        # Add default ignore patterns as fallback
        default_ignores = ["*node_modules*", "*__pycache__*", "*dist*", "*build*", "*coverage*", 
                          "*.log*", "*.tmp*", "*.temp*", "*.tmp.*", "*.temp.*", 
                          "*.tmp.*.*", "*.temp.*.*", "*.spec.*", "*.test.*", "*_test*.py"]
        for pattern in default_ignores:
            if pattern not in ignore:
                ignore.append(pattern)
                
        logger.debug(f"Ignoring {ignore}")

        def should_ignore(file_path, patterns):
            """Check if a file path matches any of the ignore patterns."""
            # Convert path to string for easier pattern matching
            path_str = str(file_path.relative_to(self.root_path))
            for pattern in patterns:
                # Convert glob pattern to regex pattern
                if fnmatch.fnmatch(path_str, pattern):
                    return True
            return False
            
        all_files = [file for file in all_files if not should_ignore(file, ignore)]
        test_files = []
        source_files = []
        logger.debug(f"All files: {str(len(all_files))}")
        
        # First, identify test files by checking if the file matches test patterns
        for file in all_files:
            relative_path = file.relative_to(self.root_path)
            file_name = file.name
            
            # Check if the file is a test file based on common test file patterns
            is_test_file = (
                file_name.startswith("test_") or 
                file_name.endswith("_test.py") or
                ".test." in file_name or 
                ".spec." in file_name or
                (file.parent.name == "__tests__") or
                (file.parent.name == "tests" and file_name.startswith("test_")) or
                (file.parent.name == "test" and file_name.startswith("test_"))
            )
            
            if is_test_file:
                test_files.append(file)
            else:
                source_files.append(file)
                
        logger.debug(f"Found {len(source_files)} files and {len(test_files)} tests")
        # Sort both lists by modification time (newest first)
        source_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        test_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        return source_files, test_files
