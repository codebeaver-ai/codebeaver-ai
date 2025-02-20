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
        print("Error: Please specify what to run (e.g., pytest)")
        sys.exit(1)

    # Now parse the remaining arguments
    available_templates = get_available_templates()
    parser = argparse.ArgumentParser(
        description="CodeBeaver - AI-powered code analysis and testing"
    )
    parser.add_argument(
        "--version", action="version", version=f"CodeBeaver {__version__}"
    )
    parser.add_argument("command", choices=["run"], help="Command to execute")
    parser.add_argument(
        "template",
        choices=available_templates,
        help="Template to use (e.g., pytest, jest, vitest)",
    )
    parser.add_argument(
        "file_path",
        type=valid_file_path,
        help="Path to the file to analyze",
    )

    args = parser.parse_args(args)

    # Check environment variable after parsing arguments
    if "OPENAI_API_KEY" not in os.environ:
        print("Error: OPENAI_API_KEY environment variable is not set")
        sys.exit(1)

    if args.command == "run":
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
        while tentatives < max_tentatives:
            test_generator = TestGenerator(args.file_path)
            test_content = test_generator.generate_test(test_file, console)

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


if __name__ == "__main__":
    main()
