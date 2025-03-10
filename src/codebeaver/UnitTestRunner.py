import subprocess
import pathlib
import logging
from pathlib import Path
logger = logging.getLogger('codebeaver')

class UnitTestRunner:
    def __init__(
        self, single_file_test_commands: list[str], setup_commands: list[str]
    ) -> None:
        self.single_file_test_commands = single_file_test_commands
        self.setup_commands = setup_commands

    def setup(self) -> subprocess.CompletedProcess:
        commands = self.setup_commands.copy()
        command = " && ".join(commands)
        setup_result = subprocess.run(command, shell=True, cwd=pathlib.Path.cwd(), capture_output=True, text=True)
        if setup_result.stdout:
            logger.debug(f"Command stdout: {setup_result.stdout}")
        if setup_result.stderr:
            logger.debug(f"Command stderr: {setup_result.stderr}")
        return setup_result

    def run_test(
        self, source_file_path: Path, test_file_path: Path
    ) -> subprocess.CompletedProcess:
        commands = self.single_file_test_commands.copy()
        commands.insert(0, f"export FILE_TO_COVER='{source_file_path}'")
        commands.insert(0, f"export TEST_FILE='{test_file_path}'")
        command = " && ".join(commands)

        logger.debug(f"UnitTestRunner: {command}")
        test_result = subprocess.run(
            command, 
            shell=True, 
            cwd=pathlib.Path.cwd(),
            capture_output=True,
            text=True
        )
        
        # Log subprocess output at debug level instead of printing to console
        if test_result.stdout:
            logger.debug(f"Command stdout: {test_result.stdout}")
        if test_result.stderr:
            logger.debug(f"Command stderr: {test_result.stderr}")
            
        return test_result
