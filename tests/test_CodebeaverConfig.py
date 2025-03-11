import logging
import sys
import unittest
import pathlib
from codebeaver.CodebeaverConfig import (
    CodeBeaverConfig,
    E2EConfig,
    E2ETestConfig,
    UnitTestConfig,
)

import pytest
import yaml

class TestCodeBeaverConfig(unittest.TestCase):
    """Tests for validating the CodeBeaverConfig behavior."""

    def test_e2e_conversion_and_unit_max_attempts_template_merge(self):
        """
        Test that when an 'e2e' field is provided as a dictionary in the YAML,
        CodeBeaverConfig automatically converts it to an instance of E2EConfig.
        Also, when a 'from' field is provided for the unit config and max_attempts is not set,
        the value is merged from the template.
        """
        yaml_content = {
            "name": "CombinedTestWorkspace",
            "path": "/tmp/combined_test",
            "unit": {
                "max_files_to_test": 50,
                "single_file_test_commands": ["echo unit test"],
                "setup_commands": ["echo setup"],
                "test_commands": ["echo run"],
                "run_setup": False,
                "ignore": ["ignore_unit"],
            },
            "e2e": {
                "checkout": {
                    "url": "http://example.org",
                    "steps": ["stepA", "stepB"],
                }
            },
            "from": "dummy_template",
        }
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
                max_attempts=9,
            )

        CodeBeaverConfig.parse_template = staticmethod(fake_parse_template)
        config = CodeBeaverConfig.from_yaml(yaml_content)
        self.assertIsInstance(
            config.e2e,
            E2EConfig,
            "e2e section should be automatically converted to an E2EConfig instance.",
        )
        self.assertIn("checkout", config.e2e.tests)
        self.assertEqual(config.e2e.tests["checkout"].url, "http://example.org")
        self.assertEqual(config.e2e.tests["checkout"].steps, ["stepA", "stepB"])
        self.assertEqual(
            config.unit.max_attempts,
            9,
            "max_attempts should be merged from the template when not provided in the unit config.",
        )
        CodeBeaverConfig.parse_template = original_parse_template

    def test_from_yaml_without_workspaces(self):
        """Test that from_yaml correctly constructs CodeBeaverConfig from a YAML dictionary without workspaces."""
        yaml_content = {
            "name": "TestWorkspace",
            "path": "/tmp/test",
            "ignore": ["*.tmp"],
            "unit": {
                "template": "basic",
                "max_files_to_test": 10,
                "single_file_test_commands": ["echo test"],
                "setup_commands": ["echo setup"],
                "test_commands": ["echo run"],
                "run_setup": False,
                "ignore": ["ignore1"],
                "max_attempts": 3,
            },
            "e2e": {
                "login": {"url": "http://example.com", "steps": ["step1", "step2"]}
            },
        }
        config = CodeBeaverConfig.from_yaml(yaml_content)
        self.assertEqual(config.name, "TestWorkspace")
        self.assertEqual(config.path, "/tmp/test")
        self.assertEqual(config.ignore, ["*.tmp"])
        self.assertIsInstance(config.unit, UnitTestConfig)
        self.assertEqual(config.unit.max_files_to_test, 10)
        self.assertIsInstance(config.e2e, E2EConfig)
        self.assertIn("login", config.e2e.tests)
        self.assertEqual(config.e2e.tests["login"].url, "http://example.com")

    def test_from_yaml_with_workspace(self):
        """Test that from_yaml correctly picks the right workspace when a workspaces dictionary is provided."""
        yaml_content = {
            "workspaces": {
                "ws1": {
                    "name": "Workspace1",
                    "path": "/tmp/ws1",
                    "unit": {"max_files_to_test": 5},
                },
                "ws2": {
                    "name": "Workspace2",
                    "path": "/tmp/ws2",
                    "unit": {"max_files_to_test": 20},
                },
            }
        }
        config = CodeBeaverConfig.from_yaml(yaml_content, workspace_name="ws2")
        self.assertEqual(config.name, "Workspace2")
        self.assertEqual(config.path, "/tmp/ws2")
        self.assertIsInstance(config.unit, UnitTestConfig)
        self.assertEqual(config.unit.max_files_to_test, 20)

    def test_unit_config_template_merge(self):
        """Test that when a 'from' field is provided, the UnitTestConfig merges values from the template."""
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
        input_dict = {"name": "TemplateTest", "unit": {}, "from": "dummy"}
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


class TestCodebeaverConfigPytest:
    """Pytest based tests for CodeBeaverConfig functionalities."""
    def test_unit_config_from_non_string(self):
        """Ensure ValueError is raised when 'from' field is not a string in UnitTestConfig."""
        with pytest.raises(ValueError, match="from must be a string"):
            UnitTestConfig(**{"from": 123})

    def test_unit_init_unexpected_keyword(self):
        """Ensure TypeError is raised for unexpected keyword arguments in UnitTestConfig."""
        with pytest.raises(TypeError, match="unexpected keyword argument"):
            UnitTestConfig(unexpected="value")

    def test_parse_template_file_not_found(self, monkeypatch):
        """Ensure sys.exit is called when the template file is not found."""
        # Monkey-patch template_dir to return a non-existent directory
        monkeypatch.setattr(CodeBeaverConfig, "template_dir", lambda: pathlib.Path("/nonexistent_dir"))
        with pytest.raises(SystemExit) as e:
            CodeBeaverConfig.parse_template("nonexistent_template")
        assert e.value.code == 1

    def test_get_templates(self, tmp_path, monkeypatch):
        """Test that get_templates returns the correct list from the template directory."""
        # Create a dummy template file in the temporary directory
        dummy_file = tmp_path / "dummy_template.yml"
        dummy_file.write_text("dummy: content")
        monkeypatch.setattr(CodeBeaverConfig, "template_dir", lambda: tmp_path)
        templates = CodeBeaverConfig.get_templates()
        assert "dummy_template" in templates

    def test_from_yaml_missing_workspace_name(self):
        """Ensure ValueError is raised when workspaces are defined but workspace_name is missing."""
        with pytest.raises(ValueError, match="workspace_name is required"):
            CodeBeaverConfig.from_yaml({"workspaces": {"ws1": {"name": "ws1"}}})

    def test_from_yaml_workspace_not_found(self):
        """Ensure ValueError is raised when a specified workspace is not found."""
        with pytest.raises(ValueError, match="workspace ws99 not found"):
            CodeBeaverConfig.from_yaml({"workspaces": {"ws1": {"name": "ws1"}}}, workspace_name="ws99")

    def test_e2e_empty_config(self):
        """Ensure that an empty e2e config dictionary is converted into an E2EConfig with empty tests."""
        yaml_content = {"name": "EmptyE2E", "path": "/tmp/empty", "e2e": {}}
        config = CodeBeaverConfig.from_yaml(yaml_content)
        assert isinstance(config.e2e, E2EConfig)
        assert config.e2e.tests == {}
    def test_parse_template_invalid_yaml_format(self, tmp_path, monkeypatch):
        """Test that parse_template exits when the YAML file has an invalid format (non-dict)."""
        # Create a dummy invalid template file with YAML content that is not a dict
        invalid_file = tmp_path / "invalid.yml"
        invalid_file.write_text("[1, 2, 3]")
        monkeypatch.setattr(CodeBeaverConfig, "template_dir", lambda: tmp_path)
        with pytest.raises(SystemExit) as e:
            CodeBeaverConfig.parse_template("invalid")
        assert e.value.code == 1

    def test_codebeaverconfig_without_unit(self):
        """Test that CodeBeaverConfig correctly handles configuration without a unit section."""
        yaml_content = {
            "name": "TestNoUnit",
            "path": "/tmp/no_unit",
            "e2e": {
                "login": {"url": "http://example.com", "steps": ["step1"]}
            },
        }
        config = CodeBeaverConfig.from_yaml(yaml_content)
        # unit should remain None if not provided
        assert config.unit is None
        # e2e should still be converted to E2EConfig
        assert isinstance(config.e2e, E2EConfig)

    def test_unit_config_template_preserve_existing(self):
        """Test that existing unit config values are preserved over template values when merging."""
        original_parse_template = CodeBeaverConfig.parse_template
        def fake_parse_template(template_name: str) -> UnitTestConfig:
            return UnitTestConfig(
                template="dummy_template",
                max_files_to_test=100,
                single_file_test_commands=["cmd1"],
                setup_commands=["setup1"],
                test_commands=["template_test"],
                run_setup=True,
                ignore=["dummy_ignore"],
                max_attempts=5,
            )
        CodeBeaverConfig.parse_template = staticmethod(fake_parse_template)
        input_dict = {
            "name": "PreserveTest",
            "unit": {"max_files_to_test": 50, "test_commands": ["existing_command"]},
            "from": "dummy",
        }
        config = CodeBeaverConfig(**input_dict)
        # Check that provided values are preserved
        assert config.unit.max_files_to_test == 50
        assert config.unit.test_commands == ["existing_command"]
        # Other values merged from template
        assert config.unit.template == "dummy_template"
        assert config.unit.single_file_test_commands == ["cmd1"]
        assert config.unit.setup_commands == ["setup1"]
        assert config.unit.run_setup is True
        assert config.unit.ignore == ["dummy_ignore"]
        assert config.unit.max_attempts == 5
        CodeBeaverConfig.parse_template = original_parse_template
    def test_unit_config_defaults(self):
        """Test that UnitTestConfig defaults to expected values when no parameters are provided."""
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

    def test_codebeaverconfig_unit_instance_pass_through(self):
        """Test that providing a UnitTestConfig instance in the 'unit' field is preserved and not reinitialized."""
        unit_config = UnitTestConfig(max_files_to_test=42, test_commands=['run test'])
        config = CodeBeaverConfig(name='InstanceTest', unit=unit_config)
        assert config.unit is unit_config
        assert config.unit.max_files_to_test == 42
        assert config.unit.test_commands == ['run test']

    def test_codebeaverconfig_e2e_instance_pass_through(self):
        """Test that providing an E2EConfig instance in the 'e2e' field is preserved and not re-converted."""
        e2e_config = E2EConfig(tests={'sample': E2ETestConfig(url='http://test.com', steps=['step1'])})
        config = CodeBeaverConfig(name='E2EInstanceTest', e2e=e2e_config)
        assert config.e2e is e2e_config
        assert 'sample' in config.e2e.tests
        assert config.e2e.tests['sample'].url == 'http://test.com'

    def test_codebeaverconfig_no_args_creation(self):
        """Test that creating CodeBeaverConfig with no arguments does not raise errors and attributes default to None."""
        config = CodeBeaverConfig()
        assert getattr(config, 'name', None) is None
        assert getattr(config, 'path', None) is None
        assert getattr(config, 'ignore', None) is None
        assert getattr(config, 'unit', None) is None
        assert getattr(config, 'e2e', None) is None
    def test_parse_template_yaml_error(self, tmp_path, monkeypatch):
        """Test that parse_template calls sys.exit when yaml.YAMLError is raised."""
        # Create a dummy template file in tmp_path so that template_dir exists
        dummy_template = tmp_path / "dummy.yml"
        dummy_template.write_text("dummy: content")
        # Set the template_dir to our temporary path
        monkeypatch.setattr(CodeBeaverConfig, "template_dir", lambda: tmp_path)
        # Monkey-patch yaml.safe_load to raise a YAMLError
        monkeypatch.setattr(yaml, "safe_load", lambda stream: (_ for _ in ()).throw(yaml.YAMLError("Mock error")))
        with pytest.raises(SystemExit) as e:
            CodeBeaverConfig.parse_template("dummy")
        assert e.value.code == 1

    def test_from_yaml_with_minimal_config(self):
        """Test CodeBeaverConfig.from_yaml with minimal configuration (only name and path)."""
        yaml_content = {
            "name": "MinimalWorkspace",
            "path": "/tmp/minimal"
        }
        config = CodeBeaverConfig.from_yaml(yaml_content)
        assert config.name == "MinimalWorkspace"
        assert config.path == "/tmp/minimal"
        assert config.unit is None
        assert config.e2e is None

    def test_e2e_already_instance(self):
        """Test that providing an E2EConfig instance as the 'e2e' field is preserved and not re-initialized."""
        e2e_instance = E2EConfig(tests={'test': E2ETestConfig(url='http://instance.com', steps=['step1'])})
        config = CodeBeaverConfig(name="InstanceE2E", e2e=e2e_instance)
        # The e2e instance should be preserved (i.e. not converted or recreated)
        assert config.e2e is e2e_instance
        assert config.e2e.tests['test'].url == 'http://instance.com'
    def test_e2e_from_dict_empty(self):
        """Test that E2EConfig.from_dict correctly handles an empty dictionary."""
        e2e_config = E2EConfig.from_dict({})
        assert isinstance(e2e_config, E2EConfig)
        assert e2e_config.tests == {}

    def test_unit_config_from_field_removal(self, monkeypatch):
        """Test that the 'from' field is removed after processing in UnitTestConfig initialization."""
        def fake_parse_template(template_name: str):
            return UnitTestConfig(
                template="faked_template",
                max_files_to_test=123,
                single_file_test_commands=["cmd"],
                setup_commands=["setup"],
                test_commands=["test"],
                run_setup=True,
                ignore=["ignore_this"],
                max_attempts=7,
            )
        monkeypatch.setattr(CodeBeaverConfig, "parse_template", staticmethod(fake_parse_template))
        monkeypatch.setattr(CodeBeaverConfig, "parse_template", staticmethod(fake_parse_template))
        unit_config = UnitTestConfig(**{"from": "dummy", "main_service": "main"})
        # Ensure that the 'from' key is not stored as an attribute after initialization
        assert unit_config.template == "faked_template"
        assert unit_config.main_service == "main"
        assert unit_config.max_files_to_test == 123
        assert unit_config.max_attempts == 7

    def test_unit_config_conversion_in_constructor(self):
        """Test that CodeBeaverConfig constructor converts a unit dict into a UnitTestConfig instance."""
        config = CodeBeaverConfig(name="conversion_test", unit={"test_commands": ["echo hello"]})
        assert isinstance(config.unit, UnitTestConfig)
        assert config.unit.test_commands == ["echo hello"]

    def test_parse_template_success(self, tmp_path, monkeypatch):
        """Test that parse_template correctly loads a valid template YAML file."""
        # Create a valid YAML template file in the temporary directory
        valid_file = tmp_path / "valid_template.yml"
        valid_file.write_text(
            "template: valid_template\n"
            "max_files_to_test: 42\n"
            "single_file_test_commands:\n"
            "  - cmd_valid\n"
            "setup_commands:\n"
            "  - setup_valid\n"
            "test_commands:\n"
            "  - test_valid\n"
            "run_setup: false\n"
            "ignore:\n"
            "  - ignore_valid\n"
            "max_attempts: 7\n"
        )
        # Monkey-patch template_dir to use tmp_path
        monkeypatch.setattr(CodeBeaverConfig, "template_dir", lambda: tmp_path)
        # Call parse_template and verify the returned UnitTestConfig object
        template_config = CodeBeaverConfig.parse_template("valid_template")
        assert template_config.template == "valid_template"
        assert template_config.max_files_to_test == 42
        assert template_config.single_file_test_commands == ["cmd_valid"]
        assert template_config.setup_commands == ["setup_valid"]
        assert template_config.test_commands == ["test_valid"]
        assert template_config.run_setup is False
        assert template_config.ignore == ["ignore_valid"]
        assert template_config.max_attempts == 7

    def test_codebeaverconfig_unknown_field(self):
        """Test that CodeBeaverConfig accepts extra custom fields and sets them as attributes."""
        # Pass an extra custom field along with the defined ones
        config = CodeBeaverConfig(name="CustomFieldTest", path="/tmp/custom", custom_field="custom_value")
        # Verify that the custom field is available on the config instance
        assert hasattr(config, "custom_field")
        assert config.custom_field == "custom_value"
    def test_e2e_config_conversion_in_constructor(self):
        """Test that CodeBeaverConfig constructor converts an e2e dict into an E2EConfig instance."""
        config = CodeBeaverConfig(name="conversion_e2e", e2e={"sample": {"url": "http://convert.com", "steps": ["s1", "s2"]}})
        assert isinstance(config.e2e, E2EConfig)
        assert "sample" in config.e2e.tests
        assert config.e2e.tests["sample"].url == "http://convert.com"
if __name__ == "__main__":
    unittest.main()
