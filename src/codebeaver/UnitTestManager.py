import pathlib

from .UnitTestGenerator import UnitTestGenerator
from .UnitTestRunner import UnitTestRunner
from .TestFilePattern import TestFilePattern
import logging

logger = logging.getLogger(__name__)


class UnitTestManager:
    class CouldNotRunTests(Exception):
        pass
    
    class CouldNotRunSetup(Exception):
        pass

    class CouldNotGenerateValidTests(Exception):
        pass

    def __init__(self, file_path: str, single_file_test_commands: list[str], setup_commands: list[str], max_tentatives: int = 4, run_setup: bool = True) -> None:
        self.file_path = file_path
        self.max_tentatives = max_tentatives
        self.run_setup = run_setup
        self.single_file_test_commands = single_file_test_commands
        self.setup_commands = setup_commands

    def generate_unit_test(self):
      testrunner = UnitTestRunner(self.single_file_test_commands, self.setup_commands)
      if self.run_setup:
        test_result = testrunner.setup()
        if test_result.returncode != 0:
            logger.error(f"Could not run setup commands for {self.file_path}: {test_result.stderr}")
            raise UnitTestManager.CouldNotRunSetup(f"Could not run setup commands for {self.file_path}: {test_result.stderr}")
      test_files_pattern = TestFilePattern(pathlib.Path.cwd())
      test_file = test_files_pattern.find_test_file(self.file_path)
      if test_file:
          test_result = testrunner.run_test(self.file_path, str(test_file))
          if (
              test_result.returncode != 0
              and test_result.returncode != 1
              and test_result.returncode != 5
          ):
              logger.error(f"Could not run tests for {self.file_path}: {test_result.stderr}")
              raise UnitTestManager.CouldNotRunTests(f"Could not run tests for {self.file_path}: {test_result.stderr}")
      else:
          test_file = test_files_pattern.create_new_test_file(self.file_path)
      max_tentatives = 4
      tentatives = 0
      console = ""
      test_content = None
      while tentatives < max_tentatives:
          test_generator = UnitTestGenerator(self.file_path)
          test_content = test_generator.generate_test(str(test_file), console)

          # write the test content to a file
          with open(test_file, "w") as f:
              f.write(test_content)

          test_results = testrunner.run_test(self.file_path, str(test_file))
          if test_results.returncode == 0:
              break
          if test_results.stdout:
              console += test_results.stdout
          if test_results.stderr:
              console += test_results.stderr
          tentatives += 1
          logger.debug(f"Tentative {tentatives} of {max_tentatives}")
          logger.debug(f"errors: {test_results.stderr}")

      logger.debug(f"TEST CONTENT: {test_content}")
      logger.debug(f"TEST FILE written to: {test_file}")
      if tentatives >= max_tentatives:
          logger.warning(f"Could not generate valid tests for {self.file_path}")
          raise UnitTestManager.CouldNotGenerateValidTests(f"Could not generate valid tests for {self.file_path}")