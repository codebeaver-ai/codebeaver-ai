import pathlib

from .CodebeaverConfig import CodeBeaverConfig

from .UnitTestGenerator import UnitTestGenerator
from .UnitTestRunner import UnitTestRunner
from .TestFilePattern import TestFilePattern
from .AnalyzeError import AnalyzeError
from .GitUtils import GitUtils
from .types import TestErrorType
import logging
from pathlib import Path

logger = logging.getLogger("codebeaver")


class UnitTestManager:
    class CouldNotRunTests(Exception):
        pass

    class CouldNotRunSetup(Exception):
        pass

    class CouldNotGenerateValidTests(Exception):
        pass

    class FoundBug(Exception):
        pass

    def __init__(
        self, file_path: str | Path, workspace_config: CodeBeaverConfig
    ) -> None:
        if isinstance(file_path, str):
            self.file_path = Path(file_path)
        else:
            self.file_path = file_path
        self.workspace_config: CodeBeaverConfig = workspace_config
        if not self.workspace_config.unit:
            raise ValueError("unit_test_config is required")

        # The conversion is now handled in CodeBeaverConfig.__init__

    def generate_unit_test(self, run_setup: bool = True):
        if not self.workspace_config.unit:
            raise ValueError("unit_test_config is required")
        GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore()
        testrunner = UnitTestRunner(
            self.workspace_config.unit.single_file_test_commands or [],
            self.workspace_config.unit.setup_commands or [],
        )
        if self.workspace_config.unit.run_setup and run_setup:
            test_result = testrunner.setup()
            if test_result.returncode != 0:
                logger.error(
                    f"Could not run setup commands for {self.file_path}: {test_result.stderr}"
                )
                raise UnitTestManager.CouldNotRunSetup(
                    f"Could not run setup commands for {self.file_path}: {test_result.stderr}"
                )
        test_files_pattern = TestFilePattern(
            pathlib.Path.cwd(), workspace_config=self.workspace_config
        )
        test_file = test_files_pattern.find_test_file(self.file_path)
        logger.info(f"Writing tests for {self.file_path} at {test_file}")
        if test_file:
            test_result = testrunner.run_test(self.file_path, test_file)
            if (
                test_result.returncode != 0
                and test_result.returncode != 1
                and test_result.returncode != 5
            ):
                logger.error(
                    f"Could not run tests for {self.file_path}: {test_result.stderr}"
                )
                raise UnitTestManager.CouldNotRunTests(
                    f"Could not run tests for {self.file_path}: {test_result.stderr}"
                )
        else:
            test_file = test_files_pattern.create_new_test_file(self.file_path)
        max_attempts = self.workspace_config.unit.max_attempts or 4
        attempts = 0
        console = ""
        test_content = None
        while attempts < max_attempts:
            test_generator = UnitTestGenerator(self.file_path)
            test_content = test_generator.generate_test(test_file, console)

            # write the test content to a file
            with open(test_file, "w") as f:
                f.write(test_content)

            test_results = testrunner.run_test(self.file_path, test_file)
            if test_results.returncode == 0:
                break
            if test_results.stdout:
                console += test_results.stdout
            if test_results.stderr:
                console += test_results.stderr
            error_analyzer = AnalyzeError(
                self.file_path, test_file, test_results.stderr
            )
            error_type, error_message = error_analyzer.analyze()
            if error_type == TestErrorType.BUG:
                logger.warning(f"Found a bug in {self.file_path}")
                raise UnitTestManager.FoundBug(
                    f"""
Bug found in {self.file_path}: {error_message}
"""
                )
            attempts += 1
            logger.debug(f"Attempt {attempts} of {max_attempts}")
            logger.debug(f"Errors:\n\n{test_results.stderr}")
            console = f"Errors:\n{test_results.stderr}\nstdout: {test_results.stdout}\n"

        logger.debug(f"TEST CONTENT: {test_content}")
        logger.debug(f"TEST FILE written to: {test_file}")
        if attempts >= max_attempts:
            logger.warning(f"Could not generate valid tests for {self.file_path}")
            raise UnitTestManager.CouldNotGenerateValidTests(
                f"""Could not generate valid tests for {self.file_path}

{console}
"""
            )
