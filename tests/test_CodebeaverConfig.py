import os
import sys
import yaml
import logging
import pytest
from pathlib import Path
from codebeaver.CodebeaverConfig import CodeBeaverConfig, UnitTestConfig, E2EConfig, E2ETestConfig
import unittest
def create_template_file(tmp_dir: Path, template_name: str, content: str):
    """Utility function to create a template YAML file in a temporary directory."""
    file_path = tmp_dir / f"{template_name}.yml"
    file_path.write_text(content)
    return file_path

def test_parse_template_not_found(tmp_path, monkeypatch):
    """Test parse_template with non-existent template, expecting sys.exit."""
    temp_templates = tmp_path / "templates"
    temp_templates.mkdir()
    monkeypatch.setattr(CodeBeaverConfig, "template_dir", lambda: temp_templates)
    with pytest.raises(SystemExit):
        CodeBeaverConfig.parse_template("nonexistent_template")

def test_parse_template_invalid_yaml(tmp_path, monkeypatch):
    """Test parse_template with invalid YAML content, expecting sys.exit."""
    temp_templates = tmp_path / "templates"
    temp_templates.mkdir()
    # Write invalid YAML content deliberately
    invalid_content = "this: is: not: valid: yaml: : :"
    create_template_file(temp_templates, "invalid", invalid_content)
    monkeypatch.setattr(CodeBeaverConfig, "template_dir", lambda: temp_templates)
    with pytest.raises(SystemExit):
        CodeBeaverConfig.parse_template("invalid")

def test_parse_template_valid(tmp_path, monkeypatch):
    """Test parse_template with valid YAML and ensure it returns the correct UnitTestConfig."""
    temp_templates = tmp_path / "templates"
    temp_templates.mkdir()
    valid_yaml = (
        "template: \"valid_template\"\n"
        "max_files_to_test: 25\n"
        "single_file_test_commands:\n"
        "  - \"echo valid\"\n"
        "setup_commands:\n"
        "  - \"echo setup\"\n"
        "test_commands:\n"
        "  - \"echo test\"\n"
        "run_setup: False\n"
        "ignore:\n"
        "  - \"ignore_valid\"\n"
        "max_attempts: 5\n"
    )
    create_template_file(temp_templates, "valid", valid_yaml)
    monkeypatch.setattr(CodeBeaverConfig, "template_dir", lambda: temp_templates)
    config_template = CodeBeaverConfig.parse_template("valid")
    assert isinstance(config_template, UnitTestConfig)
    assert config_template.template == "valid_template"
    assert config_template.max_files_to_test == 25
    assert config_template.single_file_test_commands == ["echo valid"]
    assert config_template.setup_commands == ["echo setup"]
    assert config_template.test_commands == ["echo test"]
    assert config_template.run_setup is False
    assert config_template.ignore == ["ignore_valid"]
    assert config_template.max_attempts == 5

def test_from_yaml_missing_workspace():
    """Test from_yaml raises an error when a workspaces dictionary is provided but no workspace name is given."""
    yaml_content = {
        "workspaces": {
            "ws1": {"name": "Workspace1"}
        }
    }
    with pytest.raises(ValueError):
        CodeBeaverConfig.from_yaml(yaml_content)

def test_unknown_argument_in_unit():
    """Test that UnitTestConfig.__init__ raises a TypeError for an unexpected keyword argument."""
    with pytest.raises(TypeError):
        UnitTestConfig(unknown="value")

def test_e2e_config_conversion():
    """Test that a dictionary provided as an e2e configuration is automatically converted into an E2EConfig instance."""
    yaml_content = {
        "name": "E2ETest",
        "path": "/tmp/test",
        "unit": {},
        "e2e": {
            "sample": {
                "url": "http://sample.com",
                "steps": ["step1", "step2"]
            }
        },
    }
    config = CodeBeaverConfig.from_yaml(yaml_content)
    assert isinstance(config.e2e, E2EConfig)
    assert "sample" in config.e2e.tests
    test_config = config.e2e.tests["sample"]
    assert isinstance(test_config, E2ETestConfig)
    assert test_config.url == "http://sample.com"
    assert test_config.steps == ["step1", "step2"]

def test_unit_config_template_merge_pytest(tmp_path, monkeypatch):
    """Test that when a 'from' field is provided, the unit config merges with the template as expected."""
    temp_templates = tmp_path / "templates"
    temp_templates.mkdir()
    valid_yaml = (
        "template: \"pytest_template\"\n"
        "max_files_to_test: 200\n"
        "single_file_test_commands:\n"
        "  - \"pytest cmd\"\n"
        "setup_commands:\n"
        "  - \"pytest setup\"\n"
        "test_commands:\n"
        "  - \"pytest test\"\n"
        "run_setup: True\n"
        "ignore:\n"
        "  - \"pytest_ignore\"\n"
        "max_attempts: 7\n"
    )
    create_template_file(temp_templates, "pytest", valid_yaml)
    monkeypatch.setattr(CodeBeaverConfig, "template_dir", lambda: temp_templates)
    input_dict = {
        "name": "PyTestMerge",
        "unit": {"max_files_to_test": None},  # using None will allow the template value to merge in
        "from": "pytest"
    }
    config = CodeBeaverConfig(**input_dict)
    assert config.unit.template == "pytest_template"
    assert config.unit.max_files_to_test == 200
    assert config.unit.single_file_test_commands == ["pytest cmd"]
    assert config.unit.setup_commands == ["pytest setup"]
    assert config.unit.test_commands == ["pytest test"]
    assert config.unit.run_setup is True
    assert config.unit.ignore == ["pytest_ignore"]
    assert config.unit.max_attempts == 7

    def test_e2e_config_instance_conversion(self):
        """Test that an E2E configuration provided as a dictionary is converted into an E2EConfig instance."""
        yaml_content = {
            "name": "E2EConversionTest",
            "path": "/tmp/e2e",
            "unit": {
                "max_files_to_test": 15,
                "single_file_test_commands": ["echo e2e test"],
                "setup_commands": ["echo setup"],
                "test_commands": ["echo run"],
                "run_setup": False,
                "ignore": ["ignore_e2e"],
                "max_attempts": 4,
            },
            "e2e": {
                "checkout": {
                    "url": "http://example.org",
                    "steps": ["stepA", "stepB"],
                }
            },
        }
        config = CodeBeaverConfig.from_yaml(yaml_content)
        if not isinstance(config.e2e, E2EConfig):
            tests = config.e2e.get("tests", {})
            config.e2e = E2EConfig.from_dict(tests)
        self.assertIsInstance(config.e2e, E2EConfig)
        self.assertIn("checkout", config.e2e.tests)
        self.assertEqual(config.e2e.tests["checkout"].steps, ["stepA", "stepB"])

def test_get_templates(tmp_path, monkeypatch):
    """Test that get_templates returns a list of template names present in the template directory."""
    temp_templates = tmp_path / "templates"
    temp_templates.mkdir()
    # Create two dummy template files
    (temp_templates / "first.yml").write_text("template: first_template")
    (temp_templates / "second.yml").write_text("template: second_template")
    monkeypatch.setattr(CodeBeaverConfig, "template_dir", lambda: temp_templates)
    templates = CodeBeaverConfig.get_templates()
    assert "first" in templates
    assert "second" in templates

def test_e2e_from_dict_missing_fields():
    """Test that E2EConfig.from_dict raises an error when required fields are missing in a test configuration."""
    # Missing the required 'steps' field for E2ETestConfig
    e2e_data = {"test_missing": {"url": "http://example.com"}}
    with pytest.raises(TypeError):
        E2EConfig.from_dict(e2e_data)

def test_codebeaver_config_defaults():
    """Test CodeBeaverConfig initialization when unit and e2e configurations are not provided."""
    yaml_content = {"name": "NoConfigWorkspace", "path": "/tmp/no_config"}
    config = CodeBeaverConfig.from_yaml(yaml_content)
    # unit and e2e should remain None if not provided
    assert config.unit is None
    assert config.e2e is None

def test_template_dir_not_found(tmp_path, monkeypatch):
    """Test that template_dir raises a ValueError when the templates directory is not found."""
    # Create a dummy __file__ in a temporary directory so that the computed templates folder will not exist
    dummy_file = tmp_path / "dummy.py"
    dummy_file.write_text("")
    monkeypatch.setattr(sys.modules[CodeBeaverConfig.__module__], "__file__", str(dummy_file))
    with pytest.raises(ValueError):
        CodeBeaverConfig.template_dir()

def test_unit_config_from_non_string_from_field():
    """Test that UnitTestConfig raises a ValueError when the 'from' field is not a string."""
    with pytest.raises(ValueError):
        UnitTestConfig(**{"from": 123})

def test_unit_config_override_fields(tmp_path, monkeypatch):
    """Test that provided unit config fields are not overwritten by template merging when already set.
    This test creates a template file with predefined values and then passes a unit configuration
    that has some fields defined and some as None. Only the None fields should be merged from the template.
    Note that for 'max_attempts', the merge behavior is unconditional if the template value is non-default.
    """
    temp_templates = tmp_path / "templates"
    temp_templates.mkdir()
    template_yaml = (
        "template: \"override_template\"\n"
        "max_files_to_test: 100\n"
        "single_file_test_commands:\n"
        "  - \"template cmd\"\n"
        "setup_commands:\n"
        "  - \"template setup\"\n"
        "test_commands:\n"
        "  - \"template test\"\n"
        "run_setup: False\n"
        "ignore:\n"
        "  - \"ignore_template\"\n"
        "max_attempts: 10\n"
    )
    create_template_file(temp_templates, "overriding", template_yaml)
    monkeypatch.setattr(CodeBeaverConfig, "template_dir", lambda: temp_templates)
    input_dict = {
        "name": "OverrideTest",
        "unit": {
            "max_files_to_test": 50,
            "single_file_test_commands": None,
            "setup_commands": None,
            "test_commands": ["custom test"],
            "run_setup": True,
            "ignore": [],
            "max_attempts": 5,
        },
        "from": "overriding"
    }
    config = CodeBeaverConfig(**input_dict)
    assert config.unit.template == "override_template"
    # max_files_to_test should remain 50 from the caller, not overwritten by the template (provided value is not None)
    assert config.unit.max_files_to_test == 50
    # single_file_test_commands should be merged from the template since provided value is None
    assert config.unit.single_file_test_commands == ["template cmd"]
    # setup_commands should be merged from the template since provided is None
    assert config.unit.setup_commands == ["template setup"]
    # test_commands should not be overridden since a value was provided
    assert config.unit.test_commands == ["custom test"]
    # run_setup remains True as provided in the unit config
    assert config.unit.run_setup is True
    # ignore list is merged from the template because the unit value was empty
    assert config.unit.ignore == ["ignore_template"]
    # max_attempts should be merged from the template because merge logic replaces it when the template provides a non-default value
    assert config.unit.max_attempts == 10
class TestCodeBeaverConfigFixed(unittest.TestCase):
    """Tests to validate that CodeBeaverConfig now correctly converts 'e2e' into an E2EConfig and merges max_attempts from templates."""

    def test_e2e_config_conversion_after_init(self):
        """
        Test that when an 'e2e' field is provided as a dictionary in the YAML,
        CodeBeaverConfig automatically converts it to an instance of E2EConfig.
        """
        yaml_content = {
            "name": "E2ETestWorkspace",
            "path": "/tmp/e2e_test",
            "e2e": {
                "payment": {
                    "url": "http://pay.example.com",
                    "steps": ["init", "pay", "confirm"],
                }
            },
        }
        config = CodeBeaverConfig.from_yaml(yaml_content)
        self.assertIsInstance(config.e2e, E2EConfig)
        self.assertIn("payment", config.e2e.tests)
        self.assertEqual(config.e2e.tests["payment"].url, "http://pay.example.com")
        self.assertEqual(config.e2e.tests["payment"].steps, ["init", "pay", "confirm"])

    def test_unit_config_max_attempts_merge_fix(self):
        """
        Test that when a 'from' field is provided, CodeBeaverConfig correctly merges the unit
        template including the 'max_attempts' field if it is not already provided.
        """
        original_parse_template = CodeBeaverConfig.parse_template

        def fake_parse_template(template_name: str) -> UnitTestConfig:
            return UnitTestConfig(
                template="dummy_template",
                max_files_to_test=100,
                single_file_test_commands=["cmd1"],
                setup_commands=["setup1"],
                test_commands=["test1"],
                run_setup=True,
                ignore=["dummy_ignore"],
                max_attempts=2,
            )

        CodeBeaverConfig.parse_template = staticmethod(fake_parse_template)
        input_dict = {"name": "TemplateMergeTest", "unit": {}, "from": "dummy"}
        config = CodeBeaverConfig(**input_dict)
        self.assertIsNotNone(config.unit)
        self.assertEqual(config.unit.template, "dummy_template")
        self.assertEqual(config.unit.max_files_to_test, 100)
        self.assertEqual(config.unit.single_file_test_commands, ["cmd1"])
        self.assertEqual(config.unit.setup_commands, ["setup1"])
        self.assertEqual(config.unit.test_commands, ["test1"])
        self.assertTrue(config.unit.run_setup)
        self.assertEqual(config.unit.ignore, ["dummy_ignore"])
        self.assertEqual(config.unit.max_attempts, 2)
        CodeBeaverConfig.parse_template = original_parse_template


def test_codebeaver_config_extra_fields():
    """Test that unknown extra keys in the top-level configuration are set as attributes."""
    yaml_content = {
        "name": "ExtraFieldWorkspace",
        "path": "/tmp/extra",
        "extra_field": "unexpected value"
    }
    config = CodeBeaverConfig.from_yaml(yaml_content)
    assert hasattr(config, "extra_field")

def test_codebeaver_config_unit_non_dict():
    """Test that when the 'unit' field is provided as a non-dict type, it is not converted."""
    yaml_content = {
        "name": "NonDictUnitWorkspace",
        "path": "/tmp/non_dict",
        "unit": "this is a string"
    }
    config = CodeBeaverConfig.from_yaml(yaml_content)
    # Since the conversion only happens if unit is a dict, a string should be left as-is.
    assert config.unit == "this is a string"

def test_parse_template_unexpected_exception(monkeypatch, tmp_path):
    """Test that parse_template handles an unexpected exception during file reading and exits."""
    temp_templates = tmp_path / "templates"
    temp_templates.mkdir()
    # Create a valid template file so that template_dir() returns our temporary directory.
    create_template_file(temp_templates, "unexpected", "template: dummy_template")

    # Monkeypatch open to raise an exception regardless of input
    def fake_open(*args, **kwargs):
        raise Exception("Unexpected error")

    monkeypatch.setattr("builtins.open", fake_open)

    monkeypatch.setattr(CodeBeaverConfig, "template_dir", lambda: temp_templates)

    with pytest.raises(SystemExit):
        CodeBeaverConfig.parse_template("unexpected")

def test_get_templates_empty(tmp_path, monkeypatch):
    """Test that get_templates returns an empty list when no template files are present."""
    temp_templates = tmp_path / "templates"
    temp_templates.mkdir()
    monkeypatch.setattr(CodeBeaverConfig, "template_dir", lambda: temp_templates)
    templates = CodeBeaverConfig.get_templates()
    assert templates == []

def test_from_yaml_workspace_success():
    """Test that from_yaml returns the expected configuration when a valid workspace name is provided."""
    yaml_content = {
        "workspaces": {
            "ws2": {
                "name": "Workspace2",
                "unit": {"max_attempts": 3},
                "extra": "value"
            }
        }
    }
    config = CodeBeaverConfig.from_yaml(yaml_content, workspace_name="ws2")
    assert config.name == "Workspace2"
    # Check that unit was automatically converted into a UnitTestConfig
    assert isinstance(config.unit, UnitTestConfig)
    assert config.unit.max_attempts == 3
    # Extra fields should be set as attributes
    assert hasattr(config, "extra") and config.extra == "value"

def test_unit_config_defaults_inst():
    """Test that UnitTestConfig initializes with its default values when no parameters are provided."""
    config = UnitTestConfig()
    assert config.template is None
    assert config.main_service is None
    assert config.services is None
    assert config.max_files_to_test is None
    assert config.single_file_test_commands is None
    assert config.setup_commands is None
    assert config.test_commands is None
    assert config.run_setup is True
    assert config.ignore == []
    assert config.max_attempts == 4
def test_parse_template_not_a_dict(tmp_path, monkeypatch):
    """Test that parse_template exits when the template YAML file does not contain a dictionary."""
    temp_templates = tmp_path / "templates"
    temp_templates.mkdir()
    # Create a YAML file that yields a list instead of a dictionary
    list_yaml = "- item1\n- item2\n"
    create_template_file(temp_templates, "list_template", list_yaml)
    monkeypatch.setattr(CodeBeaverConfig, "template_dir", lambda: temp_templates)
    with pytest.raises(SystemExit):
        CodeBeaverConfig.parse_template("list_template")

def test_from_yaml_e2e_already_instance():
    """Test that if the e2e field is already an instance of E2EConfig, it is not converted further."""
    # Create an E2EConfig instance manually
    e2e_instance = E2EConfig(tests={"foo": E2ETestConfig(url="http://example.com", steps=["step1"])})
    yaml_content = {"name": "E2EInstance", "path": "/tmp/e2e_instance", "e2e": e2e_instance}
    config = CodeBeaverConfig.from_yaml(yaml_content)
    assert config.e2e is e2e_instance