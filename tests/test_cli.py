"""Test cases for the CLI module."""

import os
import pytest
import tempfile
import pathlib
from src.codebeaver import cli, __version__
import subprocess


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test content")
    yield f.name
    os.unlink(f.name)


@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment with OPENAI_API_KEY."""
    monkeypatch.setenv(
        "OPENAI_API_KEY",
        "REPLACEME",
    )


def test_version(capsys):
    """Test the --version flag."""
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--version"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert f"CodeBeaver {__version__}" in captured.out


def test_help(capsys):
    """Test the --help flag."""
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--help"])
    assert exc_info.value.code == 0


def test_missing_api_key(capsys, monkeypatch):
    """Test that missing OPENAI_API_KEY raises an error."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["run", "pytest", "test.py"])
    assert exc_info.value.code == 2
    # captured = capsys.readouterr()
    # assert "Error: OPENAI_API_KEY environment variable is not set" in captured.out


def test_invalid_template(capsys, mock_env, temp_file, monkeypatch):
    """Test that invalid template raises an error."""
    """Test that an invalid template produces an argparse error."""
    monkeypatch.setattr(cli, "get_available_templates", lambda: ["pytest"])
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["unit", "invalid_template", temp_file])
    assert exc_info.value.code == 2  # argparse exits with code 2 for invalid choice
    captured = capsys.readouterr()
    assert "invalid choice: 'invalid_template'" in captured.err


def test_nonexistent_file(capsys, mock_env, monkeypatch):
    """Test that nonexistent file raises an error."""
    """Test that a nonexistent file raises an error."""
    monkeypatch.setattr(cli, "get_available_templates", lambda: ["pytest"])
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["unit", "pytest", "nonexistent_file.py"])
    assert exc_info.value.code == 2  # argparse exits with code 2 for invalid argument
    captured = capsys.readouterr()
    assert "File not found: nonexistent_file.py" in captured.err


def test_run_command_missing_args(capsys, mock_env, monkeypatch):
    """Test the run command with missing arguments."""
    """Test the unit command with missing arguments."""
    monkeypatch.setattr(cli, "get_available_templates", lambda: ["pytest"])
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["unit"])
    assert exc_info.value.code == 2  # argparse exits with code 2 for missing arguments
    captured = capsys.readouterr()
    assert "the following arguments are required: template, file_path" in captured.err


def test_run_command_no_args(capsys):
    """Test the run command with no arguments."""
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["run"])
    assert exc_info.value.code == 2
    # captured = capsys.readouterr()
    # assert "Error: Please specify what to run" in captured.out


def test_run_command_with_correct_args_but_invalid_setup(capsys, mock_env, temp_file, monkeypatch):
    """Test the run command with correct arguments."""
    """Test the unit command with valid arguments but with a template that causes setup failure."""
    monkeypatch.setattr(cli, "get_available_templates", lambda: ["pytest"])
    import tempfile
    dummy_dir = tempfile.mkdtemp()
    dummy_template_path = pathlib.Path(dummy_dir) / "pytest.yml"
    with open(dummy_template_path, "w") as f:
        f.write("single_file_test_commands: []\nsetup_commands: []\n")
    monkeypatch.setattr(cli, "get_template_dir", lambda: pathlib.Path(dummy_dir))
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["unit", "pytest", temp_file])
    # captured = capsys.readouterr()
    assert exc_info.value.code == 1


def test_run_command_with_correct_args_and_correct_setup(capsys, mock_env, temp_file):
    """
    Test the run command with correct arguments and correct setup using a test project
    from tests/codebases/pytest directory.
    """
    # Get the paths
    current_dir = pathlib.Path(__file__).parent
    test_project_dir = current_dir / "codebases" / "pytest"
    test_project_path = str(test_project_dir / "src" / "alert_manager.py")
    project_root = current_dir.parent

    # Store original working directory
    original_dir = os.getcwd()

    try:
        # Change to the test project directory
        os.chdir(str(test_project_dir))

        # Install codebeaver in development mode
        install_result = subprocess.run(
            ["pip", "install", "-e", str(project_root)],
            capture_output=True,
            text=True,
            check=True,
        )

        # Run codebeaver
        env = os.environ.copy()
        env["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "dummy-key")

        result = subprocess.run(
            ["codebeaver", "run", "pytest", test_project_path],
            capture_output=True,
            text=True,
            env=env,
        )

        # Print the output for debugging
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

        # Verify the test file was created
        test_file_path = test_project_dir / "tests" / "test_alert_manager.py"
        assert test_file_path.exists(), f"Test file not found: {test_file_path}"

    finally:
        # Restore original working directory
        os.chdir(original_dir)
