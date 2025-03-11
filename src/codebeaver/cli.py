"""
Command-line interface for CodeBeaver
"""

import os

os.environ["ANONYMIZED_TELEMETRY"] = "false"
import sys
import argparse

import pathlib
import logging

from codebeaver.reporting import Report

from .CodebeaverConfig import CodeBeaverConfig
from .TestFilePattern import TestFilePattern
from .UnitTestManager import UnitTestManager
from . import __version__
import yaml
from .E2E import E2E
import asyncio


def valid_file_path(path):
    """Validate if the given path exists and is a file."""
    file_path = pathlib.Path(path)
    if not file_path.is_file():
        raise argparse.ArgumentTypeError(f"File not found: {path}")
    return str(file_path)


def setup_logging(verbose=False):
    """Configure logging for the application."""
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = "%(levelname)s: %(message)s"

    # Configure root logger
    logging.basicConfig(level=log_level, format=log_format, stream=sys.stderr)

    # Create logger for our package
    logger = logging.getLogger("codebeaver")
    # Ensure the logger level is set correctly (in case it inherits a different level)
    logger.setLevel(log_level)

    # Test message to verify debug logging
    logger.debug("Debug logging is enabled")
    return logger


def main(args=None):
    """Main entry point for the CLI."""
    if args is None:
        args = sys.argv[1:]

    # Create the main parser with more detailed description
    parser = argparse.ArgumentParser(
        description="""CodeBeaver - AI-powered code analysis and testing

CodeBeaver helps you generate and run tests for your code using AI. It supports:
- Unit test generation and execution
- End-to-end test automation
- Multiple testing frameworks (pytest, jest, vitest)

Examples:
  codebeaver     # Runs both e2e and unit tests if defined in codebeaver.yml
  codebeaver unit   # Generate unit tests for the current project
  codebeaver e2e    # Run end-to-end tests defined in codebeaver.yml
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version", version=f"CodeBeaver {__version__}"
    )

    # Add verbose flag
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging output"
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Unit test command with enhanced help
    available_templates = CodeBeaverConfig.get_templates()
    unit_parser = subparsers.add_parser(
        "unit",
        help="Generate and run unit tests for a file",
        description="""Generate and run unit tests for a specified file using AI.
        
The command will:
1. Analyze the target file
2. Generate appropriate test cases
3. Run the tests to verify they work
4. Save the tests to a new test file

Examples:
  codebeaver unit # Generate unit tests for the current project using the template defined in codebeaver.yml
  codebeaver unit --template=pytest --file=src/my_file.py
  codebeaver unit --template=jest --file=src/component.js
""",
    )
    unit_parser.add_argument(
        "--template",
        choices=available_templates,
        required=False,
        help="Testing framework template to use (e.g., pytest, jest, vitest). If not specified, uses template from codebeaver.yml",
    )
    unit_parser.add_argument(
        "--file",
        type=valid_file_path,
        required=False,
        help="Path to the file to analyze",
        dest="file_path",
    )
    unit_parser.add_argument(
        "--max-files-to-test",
        type=int,
        default=2,
        help="Maximum number of files to generate unit tests for (default: 2)",
        dest="max_files_to_test",
    )
    # Add verbose flag to unit parser
    unit_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging output"
    )

    # E2E test command with enhanced help
    e2e_parser = subparsers.add_parser(
        "e2e",
        help="Generate and run end-to-end tests",
        description="""Generate and run end-to-end tests based on a YAML configuration file.
        
The command will:
1. Read the E2E test configuration from the codebeaver.yml file
2. Set up the test environment
3. Execute the end-to-end tests
4. Report the results

Examples:
  codebeaver e2e --config=codebeaver.yml
""",
    )
    e2e_parser.add_argument(
        "--config",
        type=valid_file_path,
        default="codebeaver.yml",
        help="Path to the YAML configuration file (defaults to codebeaver.yml)",
        dest="yaml_file",  # Keep the same variable name for compatibility
    )
    # Add verbose flag to e2e parser
    e2e_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging output"
    )

    args = parser.parse_args(args)

    # Setup logging before any other operations
    logger = setup_logging(args.verbose)

    # Check environment variable after parsing arguments
    if "OPENAI_API_KEY" not in os.environ:
        logger.error("OPENAI_API_KEY environment variable is not set")
        sys.exit(1)

    # If no command specified, try to run both unit and e2e tests based on config
    if not args.command:
        try:
            with open("codebeaver.yml", "r") as f:
                config = yaml.safe_load(f)

            if "unit" in config:
                # Create new args for unit command
                unit_args = argparse.Namespace()
                unit_args.template = None
                unit_args.file_path = None
                unit_args.max_files_to_test = config["unit"].get("max_files_to_test", 5)
                unit_args.verbose = args.verbose
                unit_args.yaml_file = "codebeaver.yml"
                run_unit_command(unit_args)
            else:
                logger.info("No Unit Tests configured in codebeaver.yml, skipping...")

            if "e2e" in config:
                logger.info("Running e2e tests...")
                args.command = "e2e"
                args.yaml_file = "codebeaver.yml"  # Set the yaml_file attribute

                run_e2e_command(args)
            else:
                logger.info("No E2E Tests configured in codebeaver.yml, skipping...")

            if "unit" not in config and "e2e" not in config:
                logger.error(
                    "No tests configured in codebeaver.yml. Check out the documentation at https://github.com/codebeaver-ai/codebeaver-ai for more information."
                )
                sys.exit(1)

        except FileNotFoundError:
            logger.error("Could not find codebeaver.yml")
            sys.exit(1)
    else:
        # Handle specific commands as before
        if args.command == "unit":
            run_unit_command(args)
        elif args.command == "e2e":
            run_e2e_command(args)
        else:
            logger.error("Error: Please specify a valid command (unit or e2e)")
            sys.exit(1)


def run_unit_command(args):
    """Run the unit test command"""
    logger = logging.getLogger("codebeaver")

    workspace_config = None

    if not args.template:
        try:
            with open("codebeaver.yml", "r") as f:
                config = yaml.safe_load(f)
                workspace_config = CodeBeaverConfig.from_yaml(config)
                if "unit" not in config:
                    logger.info(
                        "No Unit Test defintion in codebeaver.yml. Check the README at https://github.com/codebeaver-ai/codebeaver-ai for more information."
                    )
                    sys.exit(2)
                if "from" not in config["unit"]:
                    logger.error("No template specified in codebeaver.yml")
                    sys.exit(1)
                args.template = config["unit"]["from"]
        except FileNotFoundError:
            logger.error(f"Could not find {args.yaml_file}")
            sys.exit(1)

    logger.info(f"Running Unit Tests using template: {args.template}")

    if not workspace_config:
        logger.error("Error: No workspace config found")
        sys.exit(1)

    logger.debug(f"Workspace config: {workspace_config}")

    file_path = args.file_path
    if file_path:
        logger.info(f"Analyzing file: {args.file_path}")
        file_content = open(args.file_path).read()
        if not file_content or file_content == "":
            logger.error("Error: File is empty")
            sys.exit(1)
        unit_test_manager = UnitTestManager(args.file_path, workspace_config)
        unit_test_manager.generate_unit_test()
    else:
        if not workspace_config:
            logger.error("Error: No workspace config found")
            sys.exit(1)
        logger.debug("Analyzing current project")
        files, test_files = TestFilePattern(
            pathlib.Path.cwd(), workspace_config
        ).list_files_and_tests()
        if len(files) > args.max_files_to_test:
            logger.info(
                f"Found {len(files)} files to write Unit Tests for. Writing tests for the first {args.max_files_to_test} files."
            )
            files = files[: args.max_files_to_test]
        else:
            logger.info(f"Found {len(files)} files to write Unit Tests for.")

        for i, file in enumerate(files):
            unit_test_manager = UnitTestManager(file, workspace_config)
            # Only run setup for the first file
            run_setup = i == 0
            try:
                unit_test_manager.generate_unit_test(run_setup=run_setup)
            except UnitTestManager.FoundBug as e:
                logger.warning(e)
    sys.exit(0)


def run_e2e_command(args):
    """Run the e2e test command (mocked for now)."""
    logger = logging.getLogger("codebeaver")
    logger.debug(f"E2E testing with YAML file: {args.yaml_file}")

    try:
        with open(args.yaml_file, "r") as f:
            yaml_content = yaml.safe_load(f)
            if "e2e" not in yaml_content:
                logger.error("Error: No e2e tests found in the YAML file")
                sys.exit(1)
            e2e = E2E(
                yaml_content["e2e"],
                chrome_instance_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            )
            e2e_tests = asyncio.run(e2e.run())
            report = Report(e2e_tests)
            report.to_console()
    except Exception as e:
        logger.error(f"Error reading YAML file: {e}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
