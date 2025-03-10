import subprocess
import pytest
from codebeaver.UnitTestRunner import UnitTestRunner

import pathlib
class TestTestRunner:
    """Tests for the TestRunner class."""

    def test_setup(self, monkeypatch):
        """Test that the setup method constructs and runs the correct command."""
        # Prepare a dummy result for subprocess.run
        dummy_result = subprocess.CompletedProcess(args="dummy", returncode=0)

        def fake_run(command, shell, cwd):
            # Verify the command is constructed properly using the setup commands.
            assert command == "echo setup1 && echo setup2"
            return dummy_result

        monkeypatch.setattr(subprocess, "run", fake_run)

        runner = UnitTestRunner(single_file_test_commands=[], setup_commands=["echo setup1", "echo setup2"])
        result = runner.setup()
        assert result.returncode == 0

    def test_run_test(self, monkeypatch, capsys):
        """Test that run_test executes the correct command with proper exported variables."""
        # Prepare a dummy result for subprocess.run
        dummy_result = subprocess.CompletedProcess(args="dummy", returncode=0)

        recorded_command = []

        def fake_run(command, shell, cwd):
            recorded_command.append(command)
            return dummy_result

        monkeypatch.setattr(subprocess, "run", fake_run)

        runner = UnitTestRunner(single_file_test_commands=["echo test", "exit 0"], setup_commands=[])
        source_file = "src/main.py"
        test_file = "tests/test_main.py"
        result = runner.run_test(source_file, test_file)
        assert result.returncode == 0

        # Verify that the command constructed is as expected.
        expected_prefix = f"export TEST_FILE='{test_file}' && export FILE_TO_COVER='{source_file}'"
        expected_command = expected_prefix + " && echo test && exit 0"
        assert recorded_command[0] == expected_command

        # Capture and check printed output.
        captured = capsys.readouterr().out
        assert "RUNNING:" in captured
        assert expected_command in captured

    def test_run_test_empty_commands(self, monkeypatch, capsys):
        """Test run_test behavior when single_file_test_commands is empty."""
        dummy_result = subprocess.CompletedProcess(args="", returncode=0)

        recorded_command = []

        def fake_run(command, shell, cwd):
            recorded_command.append(command)
            return dummy_result

        monkeypatch.setattr(subprocess, "run", fake_run)

        runner = UnitTestRunner(single_file_test_commands=[], setup_commands=[])
        source_file = "src/empty.py"
        test_file = "tests/empty_test.py"
        result = runner.run_test(source_file, test_file)
        assert result.returncode == 0

        expected_prefix = f"export TEST_FILE='{test_file}' && export FILE_TO_COVER='{source_file}'"
        expected_command = expected_prefix  # No additional test commands provided.
        assert recorded_command[0] == expected_command

        captured = capsys.readouterr().out
        assert "RUNNING:" in captured
        assert expected_command in captured
    def test_setup_empty_commands(self, monkeypatch):
        """Test the behavior of setup when setup_commands list is empty."""
        dummy_result = subprocess.CompletedProcess(args="", returncode=0)
        recorded_command = []
        def fake_run(command, shell, cwd):
            recorded_command.append(command)
            return dummy_result
        monkeypatch.setattr(subprocess, "run", fake_run)
        runner = UnitTestRunner(single_file_test_commands=[], setup_commands=[])
        result = runner.setup()
        assert result.returncode == 0
        # Since setup_commands is empty, command should be an empty string.
        assert recorded_command[0] == ""

    def test_run_test_failure(self, monkeypatch, capsys):
        """Test that run_test returns a non-zero exit code on failure."""
        dummy_result = subprocess.CompletedProcess(args="dummy", returncode=1)
        recorded_command = []
        def fake_run(command, shell, cwd):
            recorded_command.append(command)
            return dummy_result
        monkeypatch.setattr(subprocess, "run", fake_run)
        runner = UnitTestRunner(single_file_test_commands=["echo test"], setup_commands=[])
        source_file = "src/error.py"
        test_file = "tests/error_test.py"
        result = runner.run_test(source_file, test_file)
        # Verify that a failure exit code is reported.
        assert result.returncode == 1
        expected_prefix = f"export TEST_FILE='{test_file}' && export FILE_TO_COVER='{source_file}'"
        expected_command = expected_prefix + " && echo test"
        assert recorded_command[0] == expected_command
        captured = capsys.readouterr().out
        assert "RUNNING:" in captured
        assert expected_command in captured

    def test_run_test_special_chars(self, monkeypatch, capsys):
        """Test run_test with file paths containing special characters and spaces."""
        dummy_result = subprocess.CompletedProcess(args="dummy", returncode=0)
        recorded_command = []
        def fake_run(command, shell, cwd):
            recorded_command.append(command)
            return dummy_result
        monkeypatch.setattr(subprocess, "run", fake_run)
        special_source = "src/special file's test.py"
        special_test = "tests/test file.txt"
        runner = UnitTestRunner(single_file_test_commands=["echo Special"], setup_commands=[])
        result = runner.run_test(special_source, special_test)
        assert result.returncode == 0
        expected_prefix = f"export TEST_FILE='{special_test}' && export FILE_TO_COVER='{special_source}'"
        expected_command = expected_prefix + " && echo Special"
        assert recorded_command[0] == expected_command
        captured = capsys.readouterr().out
        assert "RUNNING:" in captured
        assert expected_command in captured
    def test_run_test_empty_file_paths(self, monkeypatch, capsys):
        """Test run_test behavior when provided empty file paths."""
        dummy_result = subprocess.CompletedProcess(args="", returncode=0)
        recorded_command = []
        def fake_run(command, shell, cwd):
            recorded_command.append(command)
            return dummy_result
        monkeypatch.setattr(subprocess, "run", fake_run)
        runner = UnitTestRunner(single_file_test_commands=["echo test_empty"], setup_commands=[])
        result = runner.run_test("", "")
        assert result.returncode == 0
        expected_prefix = "export TEST_FILE='' && export FILE_TO_COVER=''"
        expected_command = expected_prefix + " && echo test_empty"
        assert recorded_command[0] == expected_command
        captured = capsys.readouterr().out
        assert "RUNNING:" in captured
        assert expected_command in captured

    def test_run_test_cwd(self, monkeypatch):
        """Test that run_test is executed with the current working directory."""
        # Import pathlib locally to compare with the cwd parameter.
        import pathlib
        dummy_result = subprocess.CompletedProcess(args="dummy", returncode=0)
        def fake_run(command, shell, cwd):
            # Verify that cwd is set to the current directory.
            assert cwd == pathlib.Path.cwd()
            return dummy_result
        monkeypatch.setattr(subprocess, "run", fake_run)
        runner = UnitTestRunner(single_file_test_commands=["echo cwd"], setup_commands=[])
        result = runner.run_test("src/file.py", "tests/file_test.py")
        assert result.returncode == 0
    def test_setup_does_not_modify_commands(self, monkeypatch):
        """Test that setup method does not modify the setup_commands list."""
        original_commands = ["echo original1", "echo original2"]
        dummy_result = subprocess.CompletedProcess(args="dummy", returncode=0)

        def fake_run(command, shell, cwd):
            return dummy_result

        monkeypatch.setattr(subprocess, "run", fake_run)
        runner = UnitTestRunner(single_file_test_commands=[], setup_commands=original_commands.copy())
        result = runner.setup()
        assert result.returncode == 0
        # Ensure that runner.setup_commands remains unchanged
        assert runner.setup_commands == original_commands

    def test_run_test_does_not_modify_commands(self, monkeypatch, capsys):
        """Test that run_test method does not modify single_file_test_commands list."""
        original_commands = ["echo run_test1", "echo run_test2"]
        dummy_result = subprocess.CompletedProcess(args="dummy", returncode=0)
        recorded_command = []

        def fake_run(command, shell, cwd):
            recorded_command.append(command)
            return dummy_result

        monkeypatch.setattr(subprocess, "run", fake_run)
        runner = UnitTestRunner(single_file_test_commands=original_commands.copy(), setup_commands=[])
        result = runner.run_test("src/dummy.py", "tests/dummy_test.py")
        assert result.returncode == 0
        # Ensure that runner.single_file_test_commands remains unchanged after run_test call
        assert runner.single_file_test_commands == original_commands