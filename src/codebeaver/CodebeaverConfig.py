from dataclasses import dataclass, field
import importlib.resources
import pathlib
from pathlib import Path
import yaml
import sys
import logging

logger = logging.getLogger("codebeaver")


@dataclass
class E2ETestConfig:
    """
    Represents a single E2E test configuration
    """

    url: str
    steps: list[str]


@dataclass
class E2EConfig:
    """
    Represents the E2E testing configuration section
    """

    tests: dict[str, E2ETestConfig]

    @staticmethod
    def from_dict(data: dict) -> "E2EConfig":
        tests = {
            name: E2ETestConfig(**test_config) for name, test_config in data.items()
        }
        return E2EConfig(tests=tests)


@dataclass
class UnitTestConfig:
    template: str | None = None
    main_service: str | None = None
    services: dict[str, str] | None = None
    max_files_to_test: int | None = None
    single_file_test_commands: list[str] | None = None
    setup_commands: list[str] | None = None
    test_commands: list[str] | None = None
    run_setup: bool = True
    ignore: list[str] = field(default_factory=list)
    max_attempts: int = 4

    def __init__(self, **kwargs):
        # Apply the from directive from template
        self.template = None
        self.main_service = None
        self.services = None
        self.max_files_to_test = None
        self.single_file_test_commands = None
        self.setup_commands = None
        self.test_commands = None
        self.run_setup = True
        self.ignore = []
        self.max_attempts = 4

        if kwargs.get("from"):
            if not isinstance(kwargs.get("from"), str):
                raise ValueError("from must be a string")
            template_name = kwargs[
                "from"
            ]  # Use direct dictionary access instead of get()
            template_config = CodeBeaverConfig.parse_template(template_name)
            self.template = template_config.template
            self.max_files_to_test = template_config.max_files_to_test
            self.single_file_test_commands = template_config.single_file_test_commands
            self.setup_commands = template_config.setup_commands
            self.test_commands = template_config.test_commands
            self.run_setup = template_config.run_setup or True
            self.ignore = template_config.ignore or []
            self.max_attempts = template_config.max_attempts or 4
            # remove `from` from kwargs
            kwargs.pop("from")

        # directly set attributes from kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise TypeError(
                    f"__init__() got an unexpected keyword argument '{key}'"
                )


@dataclass
class CodeBeaverConfig:
    """
    Represents a workspace configuration as defined in codebeaver.yml
    """

    name: str | None = None
    path: str | None = None
    ignore: list[str] | None = None
    unit: UnitTestConfig | None = None
    e2e: E2EConfig | None = None

    def __init__(self, **kwargs):
        # Extract template name if provided
        template_name = kwargs.pop("from", None)

        # Initialize with provided kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

        # Always convert unit config to UnitTestConfig if it's a dictionary
        if (
            hasattr(self, "unit")
            and self.unit is not None
            and isinstance(self.unit, dict)
        ):
            self.unit = UnitTestConfig(**self.unit)

        # Always convert e2e config to E2EConfig if it's a dictionary
        if hasattr(self, "e2e") and self.e2e is not None and isinstance(self.e2e, dict):
            self.e2e = E2EConfig.from_dict(self.e2e)

        # Apply template if specified
        if template_name and hasattr(self, "unit"):
            # Parse the template
            template_config = self.parse_template(template_name)

            # If unit config is just a string or None, convert to UnitTestConfig
            if not isinstance(self.unit, UnitTestConfig):
                if isinstance(self.unit, dict):
                    self.unit = UnitTestConfig(**self.unit)
                else:
                    self.unit = UnitTestConfig()

            # Merge template with existing unit config
            # Only apply template values where the unit config doesn't have values
            if template_config.template is not None and self.unit.template is None:
                self.unit.template = template_config.template

            if (
                template_config.max_files_to_test is not None
                and self.unit.max_files_to_test is None
            ):
                self.unit.max_files_to_test = template_config.max_files_to_test

            if (
                template_config.single_file_test_commands is not None
                and self.unit.single_file_test_commands is None
            ):
                self.unit.single_file_test_commands = (
                    template_config.single_file_test_commands
                )

            if (
                template_config.setup_commands is not None
                and self.unit.setup_commands is None
            ):
                self.unit.setup_commands = template_config.setup_commands

            if (
                template_config.test_commands is not None
                and self.unit.test_commands is None
            ):
                self.unit.test_commands = template_config.test_commands

            if template_config.run_setup is not None and self.unit.run_setup is None:
                self.unit.run_setup = template_config.run_setup

            # Add max_attempts merge logic
            if (
                template_config.max_attempts != 4
            ):  # Only merge if template has non-default value
                self.unit.max_attempts = template_config.max_attempts

            # For ignore list, merge if template has values and current list is empty
            if template_config.ignore and not self.unit.ignore:
                self.unit.ignore = template_config.ignore

    @staticmethod
    def from_yaml(
        yaml_content: dict, workspace_name: str | None = None
    ) -> "CodeBeaverConfig":
        if "workspaces" in yaml_content:
            if not workspace_name:
                raise ValueError(
                    "workspace_name is required when workspaces are defined"
                )
            if workspace_name not in yaml_content["workspaces"]:
                raise ValueError(f"workspace {workspace_name} not found in workspaces")
            return CodeBeaverConfig(**yaml_content["workspaces"][workspace_name])
        else:
            return CodeBeaverConfig(**yaml_content)

    @staticmethod
    def template_dir() -> Path:
        """Returns the path to the templates directory"""
        template_dir = pathlib.Path(__file__).parent / "templates"
        if template_dir.exists():
            return template_dir
        raise ValueError(
            "Templates directory not found. Please ensure CodeBeaver is installed correctly."
        )

    @staticmethod
    def get_templates() -> list[str]:
        """Returns a list of the available templates"""
        templates = [f.stem for f in CodeBeaverConfig.template_dir().glob("*.yml")]
        return templates

    @staticmethod
    def parse_template(template_name: str) -> UnitTestConfig:
        # parse the yaml of the template
        template_path = CodeBeaverConfig.template_dir() / f"{template_name}.yml"
        try:
            with open(template_path, "r") as f:
                parsed_file = yaml.safe_load(f)
            if not isinstance(parsed_file, dict):
                logger.error(
                    f"Invalid template format in {template_path} - expected a dictionary"
                )
                sys.exit(1)
        except FileNotFoundError:
            logger.error(f"Could not find {template_name} template at {template_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing template YAML at {template_path}: {str(e)}")
            sys.exit(1)
        except Exception as e:
            logger.error(
                f"Unexpected error reading template at {template_path}: {str(e)}"
            )
            sys.exit(1)
        parsed_file = UnitTestConfig(**parsed_file)
        return parsed_file
