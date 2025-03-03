import sys
import pathlib
import subprocess
import pytest
from subprocess import CompletedProcess
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from codebeaver.TestRunner import TestRunner

def test_setup(monkeypatch):
    """Test that the setup method runs the setup commands correctly and returns the expected subprocess.CompletedProcess."""
    def fake_run(cmd, shell, cwd):
        expected_cmd = "echo hello && echo world"
        # Verify that the command is joined correctly
        assert cmd == expected_cmd, f"Got: {cmd}, Expected: {expected_cmd}"
        return CompletedProcess(args=cmd, returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    # Create a TestRunner instance with dummy setup commands
    runner = TestRunner(single_file_test_commands=[], setup_commands=["echo hello", "echo world"])
    result = runner.setup()
    assert result.returncode == 0

def test_run_test(monkeypatch, capsys):
    """Test that the run_test method constructs the correct command and prints it, and returns the expected subprocess.CompletedProcess."""
    def fake_run(cmd, shell, cwd):
        # The expected ordering: the TEST_FILE export is inserted at index 0, then the FILE_TO_COVER export, then the command(s)
        expected_cmd = "export TEST_FILE='test.py' && export FILE_TO_COVER='source.py' && echo Running tests"
        assert cmd == expected_cmd, f"Got: {cmd}, Expected: {expected_cmd}"
        return CompletedProcess(args=cmd, returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    # Create a TestRunner instance with a dummy single file test command
    runner = TestRunner(single_file_test_commands=["echo Running tests"], setup_commands=[])
    result = runner.run_test("source.py", "test.py")
    assert result.returncode == 0
    # Verify that the printed output contains the expected information
    captured = capsys.readouterr().out
    assert "RUNNING:" in captured
    assert "export TEST_FILE='test.py'" in captured
def test_run_test_empty(monkeypatch, capsys):
    """Test that run_test method works correctly when no single file test commands are provided."""
    def fake_run(cmd, shell, cwd):
        expected_cmd = "export TEST_FILE='test.py' && export FILE_TO_COVER='source.py'"
        assert cmd == expected_cmd, f"Got: {cmd}, Expected: {expected_cmd}"
        return CompletedProcess(args=cmd, returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    # Create a TestRunner instance with an empty single_file_test_commands list.
    runner = TestRunner(single_file_test_commands=[], setup_commands=[])
    result = runner.run_test("source.py", "test.py")
    assert result.returncode == 0
    captured = capsys.readouterr().out
    assert "RUNNING:" in captured

def test_setup_empty(monkeypatch):
    """Test that the setup method runs correctly when no setup commands are provided."""
    def fake_run(cmd, shell, cwd):
        expected_cmd = ""
        assert cmd == expected_cmd, f"Got: {cmd}, Expected: {expected_cmd}"
        return CompletedProcess(args=cmd, returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    # Create a TestRunner instance with an empty setup_commands list.
    runner = TestRunner(single_file_test_commands=[], setup_commands=[])
    result = runner.setup()
    assert result.returncode == 0

def test_init():
    """Test that the __init__ method correctly assigns the commands to TestRunner instance attributes."""
    single_file_commands = ["echo test"]
    setup_commands = ["echo setup"]
    runner = TestRunner(single_file_test_commands=single_file_commands, setup_commands=setup_commands)
    assert runner.single_file_test_commands == single_file_commands
    assert runner.setup_commands == setup_commands
def test_setup_nonzero(monkeypatch):
    """Test that when a setup command fails (returns non-zero), setup returns a failing CompletedProcess."""
    def fake_run(cmd, shell, cwd):
            # Simulate failure by returning a non-zero return code regardless of the command
            return CompletedProcess(args=cmd, returncode=1)
    monkeypatch.setattr(subprocess, "run", fake_run)
    runner = TestRunner(single_file_test_commands=[], setup_commands=["false"])
    result = runner.setup()
    assert result.returncode != 0

def test_run_test_nonzero(monkeypatch, capsys):
    """Test that run_test method returns non-zero when the executed command fails."""
    def fake_run(cmd, shell, cwd):
            # The expected ordering: the TEST_FILE export is inserted at index 0, then the FILE_TO_COVER export, then the command(s)
            expected_cmd = "export TEST_FILE='test_fail.py' && export FILE_TO_COVER='source_fail.py' && false"
            assert cmd == expected_cmd, f"Got: {cmd}, Expected: {expected_cmd}"
            return CompletedProcess(args=cmd, returncode=2)
    monkeypatch.setattr(subprocess, "run", fake_run)
    runner = TestRunner(single_file_test_commands=["false"], setup_commands=[])
    result = runner.run_test("source_fail.py", "test_fail.py")
    assert result.returncode == 2
    captured = capsys.readouterr().out
    assert "RUNNING:" in captured

def test_run_test_with_special_characters(monkeypatch, capsys):
    """Test run_test method with file paths containing special characters to ensure proper command construction."""
    def fake_run(cmd, shell, cwd):
            expected_cmd = "export TEST_FILE='weird test!@#.py' && export FILE_TO_COVER='odd source &*.py' && echo Testing special characters"
            assert cmd == expected_cmd, f"Got: {cmd}, Expected: {expected_cmd}"
            return CompletedProcess(args=cmd, returncode=0)
    monkeypatch.setattr(subprocess, "run", fake_run)
    runner = TestRunner(single_file_test_commands=["echo Testing special characters"], setup_commands=[])
    result = runner.run_test("odd source &*.py", "weird test!@#.py")
    assert result.returncode == 0
    captured = capsys.readouterr().out
    assert "RUNNING:" in captured