"""Test cases for the CLI module."""

import os
import pytest
import tempfile
import pathlib
from codebeaver import cli, __version__
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


def test_missing_api_key(capsys, monkeypatch, temp_file):
    """Test that missing OPENAI_API_KEY raises an error."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["unit", "pytest", temp_file])
    assert exc_info.value.code == 1


def test_invalid_template(capsys, mock_env, temp_file):
    """Test that invalid template raises an error."""
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["unit", "invalid_template", temp_file])
    assert exc_info.value.code == 2  # argparse exits with code 2 for invalid choice
    captured = capsys.readouterr()
    assert "invalid choice: 'invalid_template'" in captured.err


def test_nonexistent_file(capsys, mock_env):
    """Test that nonexistent file raises an error."""
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["unit", "pytest", "nonexistent_file.py"])
    assert exc_info.value.code == 2  # argparse exits with code 2 for invalid argument
    captured = capsys.readouterr()
    assert "File not found: nonexistent_file.py" in captured.err


def test_run_command_missing_args(capsys, mock_env):
    """Test the run command with missing arguments."""
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["unit"])
    assert exc_info.value.code == 2  # argparse exits with code 2 for missing arguments
    captured = capsys.readouterr()
    # The error message might vary so we check for a substring
    assert "the following arguments are required:" in captured.err


def test_run_command_no_args(capsys):
    """Test the run command with no arguments."""
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["unit"])
    assert exc_info.value.code == 2
    # captured = capsys.readouterr()
    # assert "Error: Please specify what to run" in captured.out


def test_run_command_with_correct_args_but_invalid_setup(capsys, mock_env, temp_file, monkeypatch):
    """Test the run command with correct arguments but with an invalid setup by monkeypatching TestRunner.setup to simulate failure."""
    # Monkeypatch TestRunner.setup to return a dummy result with a nonzero return code
    def dummy_setup(self):
        class DummyResult:
            returncode = 1
        return DummyResult()
    monkeypatch.setattr(cli.TestRunner, "setup", dummy_setup)
    """Test the run command with correct arguments."""
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
            ["codebeaver", "unit", "pytest", test_project_path],
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

def test_run_unit_command_success(tmp_path, monkeypatch, mock_env):
    """Test successful execution of unit command with valid arguments."""
    # Create a temporary templates directory with a valid template file.
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_file = template_dir / "pytest.yml"
    template_file.write_text("single_file_test_commands: ['echo test']\nsetup_commands: ['echo setup']")
    monkeypatch.setattr(cli, "get_template_dir", lambda: template_dir)
    
    # Create a temporary target file with non-empty content.
    target_file = tmp_path / "dummy.py"
    target_file.write_text("print('Hello')")
    
    # Monkey-patch TestRunner.setup to simulate a successful setup.
    class DummyResult:
        returncode = 0
    def dummy_setup(self):
        return DummyResult()
    monkeypatch.setattr(cli.TestRunner, "setup", dummy_setup)
    
    # Force TestFilePattern to create a new test file.
    monkeypatch.setattr(cli.TestFilePattern, "find_test_file", lambda self, path: None)
    new_test_file = str(tmp_path / "generated_test.py")
    monkeypatch.setattr(cli.TestFilePattern, "create_new_test_file", lambda self, path: new_test_file)
    
    # Monkey-patch TestGenerator.generate_test to return dummy test content.
    monkeypatch.setattr(cli.TestGenerator, "generate_test", lambda self, logfile, console: "dummy test content")
    
    # Monkey-patch TestRunner.run_test to simulate a successful test run.
    def dummy_run_test(self, source, test_file):
        class DummyResult:
            returncode = 0
            stdout = ""
            stderr = ""
        return DummyResult()
    monkeypatch.setattr(cli.TestRunner, "run_test", dummy_run_test)
    
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["unit", "pytest", str(target_file)])
    assert exit_info.value.code == 0
    # Check that the new test file was created with the expected content.
    assert pathlib.Path(new_test_file).read_text() == "dummy test content"

def test_run_e2e_command_success(tmp_path, monkeypatch, mock_env):
    """Test successful execution of e2e command with valid YAML configuration."""
    # Create a temporary YAML configuration file with valid 'e2e' key.
    yaml_file = tmp_path / "e2e_config.yml"
    yaml_file.write_text("e2e: []")
    
    # Monkey-patch E2E.run to a dummy async function.
    async def dummy_run(self):
        pass
    monkeyatch_target = getattr(cli.E2E, "run", None)
    monkeypatch.setattr(cli.E2E, "run", dummy_run)
    
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["e2e", str(yaml_file)])
    assert exit_info.value.code == 0

def test_unit_command_empty_file(tmp_path, monkeypatch, mock_env):
    """Test that unit command errors out when the target file is empty."""
    # Create a valid template.
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_file = template_dir / "pytest.yml"
    template_file.write_text("single_file_test_commands: ['echo test']\nsetup_commands: ['echo setup']")
    monkeypatch.setattr(cli, "get_template_dir", lambda: template_dir)
    
    # Create an empty target file.
    empty_file = tmp_path / "empty.py"
    empty_file.write_text("")
    
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["unit", "pytest", str(empty_file)])
    assert exit_info.value.code == 1

def test_unit_command_template_no_test_commands(tmp_path, monkeypatch, mock_env):
    """Test that unit command errors out if the template contains no test commands."""
    # Create a template with an empty list for test commands.
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_file = template_dir / "pytest.yml"
    template_file.write_text("single_file_test_commands: []\nsetup_commands: ['echo setup']")
    monkeypatch.setattr(cli, "get_template_dir", lambda: template_dir)
    
    # Create a valid non-empty file.
    dummy_file = tmp_path / "non_empty.py"
    dummy_file.write_text("print('hello')")
    
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["unit", "pytest", str(dummy_file)])
    assert exit_info.value.code == 1

def test_run_e2e_command_empty_yaml(tmp_path, monkeypatch, mock_env):
    """Test that e2e command errors out when the YAML configuration is empty."""
    yaml_file = tmp_path / "empty.yml"
    yaml_file.write_text("")
    
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["e2e", str(yaml_file)])
    assert exit_info.value.code == 1