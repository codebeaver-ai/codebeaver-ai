import subprocess
import pathlib
import pytest

from src.codebeaver.TestRunner import TestRunner

class TestTestRunner:
    """Test suite for the TestRunner class.""" 

    @pytest.fixture(autouse=True)
    def patch_subprocess_run(self, monkeypatch):
        """Patch subprocess.run to capture its arguments."""
        def fake_run(command, shell, cwd):
            self.last_command = command
            self.last_shell = shell
            self.last_cwd = cwd
            return subprocess.CompletedProcess(args=command, returncode=0)
        monkeypatch.setattr(subprocess, "run", fake_run)

    def test_setup_runs_correctly(self):
        """Test that setup() joins the setup_commands and calls subprocess.run correctly."""
        commands = ["echo setup", "echo another setup"]
        runner = TestRunner(single_file_test_commands=[], setup_commands=commands)
        result = runner.setup()
        expected_command = " && ".join(commands)
        assert self.last_command == expected_command
        assert self.last_shell is True
        assert self.last_cwd == pathlib.Path.cwd()
        assert result.returncode == 0

    def test_run_test_runs_correctly(self, capsys):
        """Test that run_test() properly prepends export commands and executes the joined command."""
        commands = ["echo test", "echo finish"]
        runner = TestRunner(single_file_test_commands=commands, setup_commands=[])
        source_file = "source.py"
        test_file = "test.py"
        result = runner.run_test(source_file, test_file)
        expected_commands = [
            f"export TEST_FILE='{test_file}'",
            f"export FILE_TO_COVER='{source_file}'",
        ] + commands
        expected_command = " && ".join(expected_commands)
        captured = capsys.readouterr().out
        # Function prints the running command so ensure the expected command is printed.
        assert expected_command in captured
        assert self.last_command == expected_command
        assert self.last_shell is True
        assert self.last_cwd == pathlib.Path.cwd()
        assert result.returncode == 0

    def test_setup_with_empty_commands(self):
        """Test that setup() behaves correctly when setup_commands is an empty list."""
        runner = TestRunner(single_file_test_commands=[], setup_commands=[])
        result = runner.setup()
        expected_command = ""
        assert self.last_command == expected_command
        assert result.returncode == 0

    def test_run_test_with_empty_single_test_commands(self, capsys):
        """Test that run_test() works even when single_file_test_commands is empty."""
        runner = TestRunner(single_file_test_commands=[], setup_commands=[])
        source_file = "source_empty.py"
        test_file = "test_empty.py"
        result = runner.run_test(source_file, test_file)
        expected_commands = [
            f"export TEST_FILE='{test_file}'",
            f"export FILE_TO_COVER='{source_file}'",
        ]
        expected_command = " && ".join(expected_commands)
        captured = capsys.readouterr().out
        assert expected_command in captured
        assert self.last_command == expected_command
        assert result.returncode == 0

    def test_run_test_command_order(self):
        """Test that the 'export' commands appear in the correct order in run_test()."""
        commands = ["echo run"]
        runner = TestRunner(single_file_test_commands=commands, setup_commands=[])
        source_file = "file1.py"
        test_file = "test_file1.py"
        result = runner.run_test(source_file, test_file)
        idx_test = self.last_command.find(f"export TEST_FILE='{test_file}'")
        idx_cover = self.last_command.find(f"export FILE_TO_COVER='{source_file}'")
        idx_echo = self.last_command.find("echo run")
        # Verify that the export commands are prepended and appear before the actual test command.
        assert idx_test < idx_cover
        assert idx_cover < idx_echo and idx_test < idx_echo
        assert result.returncode == 0
    def test_run_test_with_special_characters(self, capsys):
        """Test run_test() with file names containing special characters and spaces."""
        commands = ["echo special"]
        runner = TestRunner(single_file_test_commands=commands, setup_commands=[])
        source_file = "weird source's file.py"
        test_file = 'test file "quoted".py'
        result = runner.run_test(source_file, test_file)
        expected_commands = [
            f"export TEST_FILE='{test_file}'",
            f"export FILE_TO_COVER='{source_file}'",
        ] + commands
        expected_command = " && ".join(expected_commands)
        captured = capsys.readouterr().out
        assert expected_command in captured
        assert self.last_command == expected_command
        assert result.returncode == 0

    def test_run_test_with_empty_file_names(self, capsys):
        """Test run_test() with empty strings for file names."""
        runner = TestRunner(single_file_test_commands=["echo empty"], setup_commands=[])
        source_file = ""
        test_file = ""
        result = runner.run_test(source_file, test_file)
        expected_commands = [
            "export TEST_FILE=''",
            "export FILE_TO_COVER=''",
        ] + ["echo empty"]
        expected_command = " && ".join(expected_commands)
        captured = capsys.readouterr().out
        assert expected_command in captured
        assert self.last_command == expected_command
        assert result.returncode == 0

    def test_setup_with_blank_commands(self):
        """Test setup() with a setup_commands list that includes blank strings."""
        commands = ["echo hello", "", "echo world"]
        runner = TestRunner(single_file_test_commands=[], setup_commands=commands)
        result = runner.setup()
        expected_command = " && ".join(commands)
        assert self.last_command == expected_command
        assert result.returncode == 0