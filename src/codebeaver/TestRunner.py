import subprocess
import pathlib


class TestRunner:
    def __init__(
        self, single_file_test_commands: list[str], setup_commands: list[str]
    ) -> None:
        self.single_file_test_commands = single_file_test_commands
        self.setup_commands = setup_commands

    def setup(self) -> subprocess.CompletedProcess:
        commands = self.setup_commands.copy()
        command = " && ".join(commands)
        setup_result = subprocess.run(command, shell=True, cwd=pathlib.Path.cwd())
        return setup_result

    def run_test(
        self, source_file_path: str, test_file_path: str
    ) -> subprocess.CompletedProcess:
        commands = self.single_file_test_commands.copy()
        commands.insert(0, f"export TO_BE_COVERED_FILE='{source_file_path}'")
        commands.insert(0, f"export TEST_FILE='{test_file_path}'")
        command = " && ".join(commands)
        test_result = subprocess.run(command, shell=True, cwd=pathlib.Path.cwd())
        print("RUNNING:")
        print(command)
        return test_result
