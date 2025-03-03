"""
Command-line interface for CodeBeaver
"""

import sys
import argparse
import os
import pathlib
from . import __version__
import yaml
import subprocess
from .TestFilePattern import TestFilePattern
from .TestGenerator import TestGenerator
from .TestRunner import TestRunner
from .E2E import E2E
import asyncio


def get_template_dir():
    """Get the template directory path."""
    import importlib.resources

    # First try the installed package path
    try:
        with importlib.resources.path("codebeaver.templates", "") as templates_path:
            if templates_path.exists():
                return templates_path
    except Exception:
        pass

    # Then try the development path
    dev_path = pathlib.Path(__file__).parent.parent.parent / "templates"
    if dev_path.exists():
        return dev_path

    raise ValueError(
        "Templates directory not found. Please ensure CodeBeaver is installed correctly."
    )


def get_available_templates():
    """Get list of available templates from the templates directory."""
    template_dir = get_template_dir()
    templates = [f.stem for f in template_dir.glob("*.yml")]
    if len(templates) == 0:
        raise ValueError("No templates found in the templates directory")
    return templates


def valid_file_path(path):
    """Validate if the given path exists and is a file."""
    file_path = pathlib.Path(path)
    if not file_path.is_file():
        raise argparse.ArgumentTypeError(f"File not found: {path}")
    return str(file_path)


def main(args=None):
    """Main entry point for the CLI."""

    if args is None:
        args = sys.argv[1:]

    # Handle --version and --help before any other checks
    if args and args[0] in ["--version", "--help", "-h"]:
        parser = argparse.ArgumentParser(
            description="CodeBeaver - AI-powered code analysis and testing"
        )
        parser.add_argument(
            "--version", action="version", version=f"CodeBeaver {__version__}"
        )
        parser.parse_args(args)
        return

    # Check for empty args before environment check
    if not args:
        print("Error: Please specify a command (unit or e2e)")
        sys.exit(1)

    # Create the main parser
    parser = argparse.ArgumentParser(
        description="CodeBeaver - AI-powered code analysis and testing"
    )
    parser.add_argument(
        "--version", action="version", version=f"CodeBeaver {__version__}"
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Unit test command (previously 'run')
    available_templates = get_available_templates()
    unit_parser = subparsers.add_parser("unit", help="Generate unit tests for a file")
    unit_parser.add_argument(
        "template",
        choices=available_templates,
        help="Template to use (e.g., pytest, jest, vitest)",
    )
    unit_parser.add_argument(
        "file_path",
        type=valid_file_path,
        help="Path to the file to analyze",
    )

    # E2E test command (mocked for now)
    e2e_parser = subparsers.add_parser("e2e", help="Generate end-to-end tests")
    e2e_parser.add_argument(
        "yaml_file",
        type=valid_file_path,
        help="Path to the YAML configuration file",
    )

    args = parser.parse_args(args)

    # Check environment variable after parsing arguments
    if "OPENAI_API_KEY" not in os.environ:
        print("Error: OPENAI_API_KEY environment variable is not set")
        sys.exit(1)

    if args.command == "unit":
        run_unit_command(args)
    elif args.command == "e2e":
        run_e2e_command(args)
    else:
        print("Error: Please specify a valid command (unit or e2e)")
        sys.exit(1)


def run_unit_command(args):
    """Run the unit test command (previously 'run')."""
    print(f"Using template: {args.template}")
    print(f"Analyzing file: {args.file_path}")

    # parse the yaml of the template
    template_path = get_template_dir() / f"{args.template}.yml"
    parsed_file = yaml.safe_load(template_path.open())
    print(parsed_file)

    single_file_test_commands = parsed_file["single_file_test_commands"]
    if len(single_file_test_commands) == 0:
        print("Error: No test commands found in the template")
        sys.exit(1)
    file_content = open(args.file_path).read()
    if not file_content or file_content == "":
        print("Error: File is empty")
        sys.exit(1)
    testrunner = TestRunner(single_file_test_commands)
    test_result = testrunner.run_test(args.file_path)
    if (
        test_result.returncode != 0
        and test_result.returncode != 1
        and test_result.returncode != 5
    ):
        print("Error: Could not run tests")
        sys.exit(1)

    test_file = None
    try:
        test_file_pattern = TestFilePattern(pathlib.Path.cwd())
        test_file = test_file_pattern.find_test_file(args.file_path)
        if not test_file:
            test_file = test_file_pattern.create_new_test_file(args.file_path)
    except Exception as e:
        print(f"No test file found for {args.file_path}")
        print(test_file)
        sys.exit(1)

    max_tentatives = 4
    tentatives = 0
    console = ""
    test_content = None
    while tentatives < max_tentatives:
        test_generator = TestGenerator(args.file_path)
        test_content = test_generator.generate_test(str(test_file), console)

        # write the test content to a file
        with open(test_file, "w") as f:
            f.write(test_content)

        test_results = testrunner.run_test(args.file_path)
        if test_results.returncode == 0:
            break
        if test_results.stdout:
            console += test_results.stdout
        if test_results.stderr:
            console += test_results.stderr
        tentatives += 1

    print("TEST CONTENT:", test_content)
    print("TEST FILE written to:", test_file)
    if tentatives >= max_tentatives:
        print("Error: Could not generate valid tests")
        sys.exit(1)

    sys.exit(0)


def run_e2e_command(args):
    """Run the e2e test command (mocked for now)."""
    print(f"E2E testing with YAML file: {args.yaml_file}")
    print("E2E testing functionality is not yet implemented.")

    # Mock implementation - just read and display the YAML file
    try:
        with open(args.yaml_file, "r") as f:
            yaml_content = yaml.safe_load(f)
            if "e2e" not in yaml_content:
                print("Error: No e2e tests found in the YAML file")
                sys.exit(1)
            e2e = E2E(
                yaml_content["e2e"],
                chrome_instance_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            )
            asyncio.run(e2e.run())
    except Exception as e:
        print(f"Error reading YAML file: {e}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
