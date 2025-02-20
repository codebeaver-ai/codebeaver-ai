import subprocess
import pathlib


class TestRunner:
    def __init__(self, single_file_test_commands: list[str]) -> None:
        self.single_file_test_commands = single_file_test_commands

    def run_test(self, file_path: str) -> subprocess.CompletedProcess:
        commands = self.single_file_test_commands.copy()
        commands.insert(0, f"export TEST_FILE='{file_path}'")
        command = " && ".join(commands)
        test_result = subprocess.run(command, shell=True, cwd=pathlib.Path.cwd())
        return test_result
