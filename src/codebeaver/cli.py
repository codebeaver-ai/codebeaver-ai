"""
Command-line interface for CodeBeaver
"""

import sys
import argparse
import os
import pathlib
import logging

from codebeaver.UnitTestManager import UnitTestManager
from . import __version__
import yaml
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


def setup_logging(verbose=False):
    """Configure logging for the application."""
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = '%(levelname)s: %(message)s'
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        stream=sys.stderr
    )
    
    # Create logger for our package
    logger = logging.getLogger('codebeaver')
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
  codebeaver run # Runs e2e and unit tests defined in codebeaver.yml
  codebeaver unit   # Generate unit tests for the current project
  codebeaver e2e          # Run end-to-end tests defined in codebeaver.yml
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version", version=f"CodeBeaver {__version__}"
    )

    # Add verbose flag
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging output'
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Unit test command with enhanced help
    available_templates = get_available_templates()
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
        required=True,
        help="Path to the file to analyze",
        dest="file_path"
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
        dest="yaml_file"  # Keep the same variable name for compatibility
    )

    args = parser.parse_args(args)

    # Setup logging before any other operations
    logger = setup_logging(args.verbose)

    # Check environment variable after parsing arguments
    if "OPENAI_API_KEY" not in os.environ:
        logger.error("OPENAI_API_KEY environment variable is not set")
        sys.exit(1)

    if args.command == "run":
        run_unit_command(args)
        run_e2e_command(args)
    elif args.command == "unit":
        run_unit_command(args)
    elif args.command == "e2e":
        run_e2e_command(args)
    else:
        logger.error("Error: Please specify a valid command (unit or e2e)")
        sys.exit(1)


def run_unit_command(args):
    """Run the unit test command (previously 'run')."""
    logger = logging.getLogger('codebeaver')
    
    if not args.template:
        try:
            with open("codebeaver.yml", "r") as f:
                config = yaml.safe_load(f)
                if "unit" not in config:
                    logger.error(f"No unit tests defined in {args.yaml_file}")
                    sys.exit(1)
                if "from" not in config["unit"]:
                    logger.error(f"No template specified in {args.yaml_file}")
                    sys.exit(1)
                args.template = config["unit"]["from"]
        except FileNotFoundError:
            logger.error(f"Could not find {args.yaml_file}")
            sys.exit(1)

    logger.info(f"Using template: {args.template}")

    # parse the yaml of the template
    template_path = get_template_dir() / f"{args.template}.yml"
    try:
        parsed_file = yaml.safe_load(template_path.open())
    except FileNotFoundError:
        logger.error(f"Could not find {args.template} template at {template_path}")
        sys.exit(1)

    single_file_test_commands = parsed_file["single_file_test_commands"]
    setup_commands = parsed_file["setup_commands"]
    if len(single_file_test_commands) == 0:
        logger.error("Error: No test commands found in the template")
        sys.exit(1)

    file_path = args.file_path
    if file_path:
        logger.info(f"Analyzing file: {args.file_path}")
    else:
        logger.info("Analyzing current project")


    file_content = open(args.file_path).read()
    if not file_content or file_content == "":
        logger.error("Error: File is empty")
        sys.exit(1)
    if file_path:
        unit_test_manager = UnitTestManager(args.file_path, single_file_test_commands, setup_commands)
        unit_test_manager.generate_unit_test()
    else:
        logger.info("Analyzing current project")

    sys.exit(0)


def run_e2e_command(args):
    """Run the e2e test command (mocked for now)."""
    logger = logging.getLogger('codebeaver')
    logger.debug(f"E2E testing with YAML file: {args.yaml_file}")
    logger.debug("E2E testing functionality is not yet implemented.")

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
            asyncio.run(e2e.run())
    except Exception as e:
        logger.error(f"Error reading YAML file: {e}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
