import os
import sys
import subprocess
import pathlib
import pytest

# Adjust sys.path to import the TestRunner module from src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from codebeaver.TestRunner import TestRunner

def fake_run(command, shell, cwd):
    """
    Fake subprocess.run that returns a dummy CompletedProcess.
    The stdout attribute is set to the passed command, so tests can verify command formatting.
    """
    return subprocess.CompletedProcess(args=command, returncode=0, stdout=command, stderr='')
def fake_run_error(command, shell, cwd):
    """Fake subprocess.run that simulates a failed process execution."""
    return subprocess.CompletedProcess(args=command, returncode=1, stdout=command, stderr='error occurred')


class TestTestRunner:
    def test_initialization(self):
        """Test that TestRunner instance initializes attributes correctly."""
        single_file_commands = ["echo 'test command'"]
        setup_commands = ["echo 'setup command'"]
        tr = TestRunner(single_file_test_commands=single_file_commands, setup_commands=setup_commands)
        assert tr.single_file_test_commands == single_file_commands
        assert tr.setup_commands == setup_commands
    def test_setup_runs_setup_commands(self, monkeypatch):
        """Test that setup() correctly combines the setup commands and runs them."""
        commands = ["echo 'Setting up environment'", "echo 'Another setup command'"]
        tr = TestRunner(single_file_test_commands=["echo 'test'"], setup_commands=commands)

        # Monkeypatch subprocess.run to capture the invocation.
        monkeypatch.setattr(subprocess, "run", fake_run)

        result = tr.setup()
        expected_command = " && ".join(commands)
        assert result.stdout == expected_command
        assert result.returncode == 0

    def test_run_test_builds_command(self, monkeypatch, capsys):
        """Test that run_test() correctly builds the command including environment variable exports and test commands."""
        commands = ["echo 'Running tests'"]
        tr = TestRunner(single_file_test_commands=commands, setup_commands=[])

        monkeypatch.setattr(subprocess, "run", fake_run)

        source_file = "src_file.py"
        test_file = "test_file.py"

        result = tr.run_test(source_file, test_file)

        # The run_test() method inserts two export commands at the beginning.
        # Note: The first inserted is for TEST_FILE, then TO_BE_COVERED_FILE.
        export_test = f"export TEST_FILE='{test_file}'"
        export_cov = f"export TO_BE_COVERED_FILE='{source_file}'"
        expected_command = " && ".join([export_test, export_cov, "echo 'Running tests'"])

        # Verify output printed to stdout contains the expected command.
        captured = capsys.readouterr().out
        assert "RUNNING:" in captured
        assert expected_command in captured
        # Also check that the dummy subprocess.Run returned the expected command.
        assert result.stdout == expected_command

    def test_empty_commands(self, monkeypatch):
        """Test behavior when empty command lists are provided for both setup() and run_test()."""
        tr = TestRunner(single_file_test_commands=[], setup_commands=[])
        monkeypatch.setattr(subprocess, "run", fake_run)
        result_setup = tr.setup()
        # An empty list joined with " && " returns an empty string.
        assert result_setup.stdout == ""

        result_run = tr.run_test("file.py", "test_file.py")
        export_test = f"export TEST_FILE='test_file.py'"
        export_cov = f"export TO_BE_COVERED_FILE='file.py'"
        expected_command = " && ".join([export_test, export_cov])
        assert result_run.stdout == expected_command
    def test_run_test_error(self, monkeypatch, capsys):
        """Test run_test() behavior when subprocess.run returns an error (non-zero exit code)."""
        monkeypatch.setattr(subprocess, "run", fake_run_error)
        tr = TestRunner(single_file_test_commands=["echo 'Error test'"], setup_commands=[])
        result = tr.run_test("source_err.py", "test_err.py")
        # Verify that the returned process indicates an error and that stderr contains the error message
        assert result.returncode == 1
        assert result.stderr == 'error occurred'
        captured = capsys.readouterr().out
        assert "RUNNING:" in captured

    def test_setup_error(self, monkeypatch, capsys):
        """Test setup() behavior when subprocess.run returns an error (non-zero exit code)."""
        monkeypatch.setattr(subprocess, "run", fake_run_error)
        tr = TestRunner(single_file_test_commands=[], setup_commands=["echo 'Setup error'"])
        result = tr.setup()
        assert result.returncode == 1
        assert result.stderr == 'error occurred'

        """Test that run_test() correctly handles file paths with special characters."""
        commands = ["echo 'special test'"]
        tr = TestRunner(single_file_test_commands=commands, setup_commands=[])
        monkeypatch.setattr(subprocess, "run", fake_run)
        special_source = "file with spaces.py"
        special_test = 'test_file "quoted".py'
        result = tr.run_test(special_source, special_test)
        expected_command = " && ".join([
            f"export TEST_FILE='{special_test}'",
            f"export TO_BE_COVERED_FILE='{special_source}'",
            "echo 'special test'"
        ])
        captured = capsys.readouterr().out
        assert "RUNNING:" in captured
        assert expected_command in captured
        assert result.stdout == expected_command
    def test_run_test_cwd(self, monkeypatch):
        """Test that run_test() passes the correct current working directory to subprocess.run."""
        def fake_run_check(command, shell, cwd):
            # Verify that cwd matches the current working directory.
            assert cwd == pathlib.Path.cwd()
            return subprocess.CompletedProcess(args=command, returncode=0, stdout=command, stderr='')
        commands = ["echo 'cwd test'"]
        tr = TestRunner(single_file_test_commands=commands, setup_commands=[])
        monkeypatch.setattr(subprocess, "run", fake_run_check)
        source_file = "dummy_source.py"
        test_file = "dummy_test.py"
        tr.run_test(source_file, test_file)
    def test_setup_cwd(self, monkeypatch):
        """Test that setup() passes the correct current working directory to subprocess.run."""
        def fake_run_check(command, shell, cwd):
            # Verify that cwd matches the current working directory.
            assert cwd == pathlib.Path.cwd()
            return subprocess.CompletedProcess(args=command, returncode=0, stdout=command, stderr='')
        commands = ["echo 'setup cwd test'"]
        tr = TestRunner(single_file_test_commands=[], setup_commands=commands)
        monkeypatch.setattr(subprocess, "run", fake_run_check)
        tr.setup()