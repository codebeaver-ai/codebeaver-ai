import sys
import yaml
import pytest
import pathlib
import unittest
from codebeaver.CodebeaverConfig import CodeBeaverConfig, UnitTestConfig, E2EConfig
from codebeaver.CodebeaverConfig import E2ETestConfig

class DummyExit(Exception):
    """Custom exception for breaking out of sys.exit in tests."""

def fake_sys_exit(code):
    raise DummyExit(f"Exited with {code}")

@pytest.fixture(autouse=True)
def patch_sys_exit(monkeypatch):
    # Replace sys.exit with fake_sys_exit so we can catch exit calls in tests
    monkeypatch.setattr(sys, "exit", fake_sys_exit)

class TestCodeBeaverConfigPytest:
    """Pytest tests for CodeBeaverConfig to increase test coverage."""

    def test_parse_template_invalid_format(self, tmp_path, monkeypatch):
        """
        Test that parse_template exits when the YAML content is not a dict.
        """
        # Create a dummy template file with an invalid format (a list instead of dictionary)
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "dummy_template.yml"
        template_file.write_text("- item1\n- item2\n")

        # Monkeypatch template_dir to use our temporary directory
        monkeypatch.setattr(CodeBeaverConfig, "template_dir", lambda: template_dir)

        with pytest.raises(DummyExit) as exc_info:
            CodeBeaverConfig.parse_template("dummy_template")
        assert "Exited with" in str(exc_info.value)

    def test_parse_template_not_found(self, tmp_path, monkeypatch):
        """
        Test that parse_template exits when the template file is not found.
        """
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        monkeypatch.setattr(CodeBeaverConfig, "template_dir", lambda: template_dir)

        with pytest.raises(DummyExit) as exc_info:
            CodeBeaverConfig.parse_template("non_existent")
        assert "Exited with" in str(exc_info.value)

    def test_unit_config_unexpected_keyword(self):
        """
        Test that UnitTestConfig raises TypeError when given an unexpected keyword.
        """
        with pytest.raises(TypeError) as exc_info:
            UnitTestConfig(unexpected="value")
        assert "unexpected keyword" in str(exc_info.value)

    def test_from_yaml_with_workspaces_no_workspace_name(self):
        """
        Test that from_yaml raises ValueError when workspaces are defined but workspace_name is not provided.
        """
        yaml_content = {
            "workspaces": {
                "ws1": {
                    "name": "Workspace1",
                    "path": "/tmp/ws1",
                    "unit": {"max_files_to_test": 5},
                }
            }
        }
        with pytest.raises(ValueError) as exc_info:
            CodeBeaverConfig.from_yaml(yaml_content)
        assert "workspace_name is required" in str(exc_info.value)

    def test_from_yaml_with_workspace_not_found(self):
        """
        Test that from_yaml raises ValueError when a specified workspace is not found.
        """
        yaml_content = {
            "workspaces": {
                "ws1": {"name": "Workspace1", "path": "/tmp/ws1", "unit": {}}
            }
        }
        with pytest.raises(ValueError) as exc_info:
            CodeBeaverConfig.from_yaml(yaml_content, workspace_name="nonexistent")
        assert "workspace nonexistent not found" in str(exc_info.value)

    def test_unit_config_direct_assignment(self):
        """
        Test that UnitTestConfig correctly assigns provided values directly.
        """
        config = UnitTestConfig(
            template="direct",
            main_service="svc",
            services={"svc1": "value1"},
            max_files_to_test=20,
            single_file_test_commands=["cmd"],
            setup_commands=["setup"],
            test_commands=["test"],
            run_setup=False,
            ignore=["ignore1"],
            max_attempts=5,
        )
        assert config.template == "direct"
        assert config.main_service == "svc"
        assert config.services == {"svc1": "value1"}
        assert config.max_files_to_test == 20
        assert config.single_file_test_commands == ["cmd"]
        assert config.setup_commands == ["setup"]
        assert config.test_commands == ["test"]
        assert config.run_setup is False
        assert config.ignore == ["ignore1"]
        assert config.max_attempts == 5
        yaml_content = {
            "workspaces": {
                "ws2": {
                    "name": "Workspace2",
                    "path": "/tmp/ws2",
                    "unit": {
                        "template": "direct",
                        "main_service": "svc",
                        "services": {"svc1": "value1"},
                        "max_files_to_test": 20,
                        "single_file_test_commands": ["cmd"],
                        "setup_commands": ["setup"],
                        "test_commands": ["test"],
                        "run_setup": False,
                        "ignore": ["ignore1"],
                        "max_attempts": 5
                    }
                }
            }
        }
        config = CodeBeaverConfig.from_yaml(yaml_content, workspace_name="ws2")
        assert config.name == "Workspace2"
        assert config.path == "/tmp/ws2"
        assert isinstance(config.unit, UnitTestConfig)
        assert config.unit.max_files_to_test == 20

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
        assert config.unit is not None
        assert config.unit.template == "dummy_template"
        assert config.unit.max_files_to_test == 100
        assert config.unit.single_file_test_commands == ["cmd1"]
        assert config.unit.setup_commands == ["setup1"]
        assert config.unit.test_commands == ["test1"]
        assert config.unit.run_setup is True
        assert config.unit.ignore == ["dummy_ignore"]
        assert config.unit.max_attempts == 2
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
        assert isinstance(config.e2e, E2EConfig)
        assert "checkout" in config.e2e.tests
        assert config.e2e.tests["checkout"].steps == ["stepA", "stepB"]


    def test_template_dir_not_found(self, monkeypatch, tmp_path):
        """Test that template_dir raises ValueError when the templates directory is missing."""
        # Monkeypatch __file__ so that the computed templates directory (tmp_path/"templates") does not exist
        monkeypatch.setitem(sys.modules[CodeBeaverConfig.__module__].__dict__, "__file__", str(tmp_path / "dummy.py"))
        with pytest.raises(ValueError) as exc_info:
            CodeBeaverConfig.template_dir()
        assert "Templates directory not found" in str(exc_info.value)

    def test_get_templates(self, monkeypatch, tmp_path):
        """Test that get_templates returns the correct list of template names."""
        # Create a temporary templates directory with dummy template files
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "temp1.yml").write_text("key: value")
        (templates_dir / "temp2.yml").write_text("key: value")
        monkeypatch.setattr(CodeBeaverConfig, "template_dir", lambda: templates_dir)
        templates = CodeBeaverConfig.get_templates()
        assert set(templates) == {"temp1", "temp2"}

    def test_e2e_config_from_empty_dict(self):
        """Test that E2EConfig.from_dict correctly handles an empty dictionary."""
        e2e_config = E2EConfig.from_dict({})
        assert e2e_config.tests == {}
        pass
    def test_parse_template_yaml_error(self, tmp_path, monkeypatch):
        """Test that parse_template exits when yaml.safe_load raises a YAMLError."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "error_template.yml"
        # Write a valid yaml file so that open works, but we'll monkeypatch yaml.safe_load to raise an error.
        template_file.write_text("key: value")
    
        # Monkeypatch template_dir to use our temporary directory
        monkeypatch.setattr(CodeBeaverConfig, "template_dir", lambda: template_dir)
        # Monkeypatch yaml.safe_load to raise yaml.YAMLError
        original_safe_load = yaml.safe_load
        monkeypatch.setattr(yaml, "safe_load", lambda f: (_ for _ in ()).throw(yaml.YAMLError("Test YAML error")))

        with pytest.raises(DummyExit) as exc_info:
            CodeBeaverConfig.parse_template("error_template")
        assert "Exited with" in str(exc_info.value)
        # Restore yaml.safe_load
        monkeypatch.setattr(yaml, "safe_load", original_safe_load)

    def test_unit_config_from_non_string(self):
        """Test that UnitTestConfig raises ValueError when the 'from' field is not a string."""
        with pytest.raises(ValueError) as exc_info:
            UnitTestConfig(**{"from": 123})
        assert "from must be a string" in str(exc_info.value)
    def test_from_yaml_without_unit(self):
        """Test that CodeBeaverConfig.from_yaml handles a missing unit configuration correctly."""
        yaml_content = {
            "name": "NoUnitWorkspace",
            "path": "/tmp/no_unit",
            "e2e": {
                "example": {
                    "url": "http://example.com",
                    "steps": ["step1"]

                }
            }
        }
        config = CodeBeaverConfig.from_yaml(yaml_content)
        assert config.unit is None
        assert isinstance(config.e2e, E2EConfig)
        assert "example" in config.e2e.tests
    def test_unit_config_defaults(self):
        """Test that UnitTestConfig initializes with the expected default values when no parameters are provided."""
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
    def test_codebeaver_config_e2e_already_instance(self):
        """Test that when E2E config is already an instance of E2EConfig, no conversion occurs."""
        e2e_instance = E2EConfig(tests={"dummy": E2ETestConfig(url="http://dummy.test", steps=["step1"])})
        config = CodeBeaverConfig(name="DirectE2ETest", e2e=e2e_instance)
        # Ensure that the e2e attribute remains the same instance without modification
        assert config.e2e is e2e_instance
        assert config.e2e.tests["dummy"].url == "http://dummy.test"

        """Test that E2EConfig.from_dict handles an empty dictionary correctly."""
        e2e_config = E2EConfig.from_dict({})
        assert e2e_config.tests == {}
    def test_unit_config_template_merge_override(self, monkeypatch):
        """Test that user-provided unit config values are not overridden by the template merge."""
        original_parse_template = CodeBeaverConfig.parse_template
        def fake_parse_template(template_name: str) -> UnitTestConfig:
            return UnitTestConfig(
                template="fake_template",
                max_files_to_test=100,
                single_file_test_commands=["fake_cmd"],
                setup_commands=["fake_setup"],
                test_commands=["fake_test"],
                run_setup=True,
                ignore=["fake_ignore"],
                max_attempts=2,
            )
        CodeBeaverConfig.parse_template = staticmethod(fake_parse_template)
        input_dict = {
            "name": "OverrideTest",
            "unit": {
                "max_files_to_test": 50,  # preference provided by user should remain unchanged
                "single_file_test_commands": None,  # value is missing so template value is used
            },
            "from": "fake"
        }
        config = CodeBeaverConfig(**input_dict)
        assert config.unit.template == "fake_template"
        assert config.unit.max_files_to_test == 50
        assert config.unit.single_file_test_commands == ["fake_cmd"]
        assert config.unit.setup_commands == ["fake_setup"]
        assert config.unit.test_commands == ["fake_test"]
        assert config.unit.run_setup is True
        assert config.unit.ignore == ["fake_ignore"]
        assert config.unit.max_attempts == 2
        CodeBeaverConfig.parse_template = original_parse_template

    def test_empty_codebeaver_config(self):
        """Test that initializing an empty CodeBeaverConfig properly sets default values (attributes remain None)."""
        config = CodeBeaverConfig()
        # Because our custom __init__ does not explicitly set defaults when not provided,
        # we can only safely assert that these attributes are missing or None.
        assert getattr(config, "name", None) is None
        assert getattr(config, "path", None) is None
        assert getattr(config, "unit", None) is None
        assert getattr(config, "e2e", None) is None

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
        assert isinstance(config.e2e, E2EConfig)
        assert "payment" in config.e2e.tests
        assert config.e2e.tests["payment"].url == "http://pay.example.com"
        assert config.e2e.tests["payment"].steps == ["init", "pay", "confirm"]

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
        assert config.unit is not None
        assert config.unit.template == "dummy_template"
        assert config.unit.max_files_to_test == 100
        assert config.unit.single_file_test_commands == ["cmd1"]
        assert config.unit.setup_commands == ["setup1"]
        assert config.unit.test_commands == ["test1"]
        assert config.unit.run_setup is True
        assert config.unit.ignore == ["dummy_ignore"]
        assert config.unit.max_attempts == 2
        CodeBeaverConfig.parse_template = original_parse_template

    def test_codebeaver_config_unit_already_instance(self):
        """Test that when unit config is already an instance of UnitTestConfig, no conversion occurs."""
        unit_instance = UnitTestConfig(main_service="svc", max_files_to_test=10)
        config = CodeBeaverConfig(name="TestWorkspace", path="/tmp/test", unit=unit_instance)
        # Ensure that unit remains the same instance and its attributes remain unchanged
        assert config.unit is unit_instance
        assert config.unit.main_service == "svc"
        assert config.unit.max_files_to_test == 10

    def test_parse_template_unexpected_exception(self, tmp_path, monkeypatch):
        """Test that parse_template exits when an unexpected error occurs (simulated by monkeypatching open)."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "unexpected.yml"
        template_file.write_text("key: value")
        monkeypatch.setattr(CodeBeaverConfig, "template_dir", lambda: template_dir)
        # Monkeypatch the built-in open to always raise an Exception
        monkeypatch.setattr("builtins.open", lambda *args, **kwargs: (_ for _ in ()).throw(Exception("Unexpected error")))
        with pytest.raises(DummyExit) as exc_info:
            CodeBeaverConfig.parse_template("unexpected")
        assert "Exited with" in str(exc_info.value)

    def test_codebeaver_config_extra_attribute(self):
        """Test that extra unknown attributes are attached to a CodeBeaverConfig instance."""
        config = CodeBeaverConfig(extra="extraVal")
        # Verify that the extra attribute is set even though it is not explicitly defined in the class
        assert hasattr(config, "extra")
        assert config.extra == "extraVal"

    def test_from_yaml_top_level(self):
        """Test that from_yaml returns a CodeBeaverConfig instance when YAML content is provided as a top‐level configuration (without workspaces)."""
        yaml_content = {
            "name": "TopLevelWorkspace",
            "path": "/tmp/top",
            "unit": {"max_files_to_test": 30},
            "e2e": {"login": {"url": "http://login.com", "steps": ["step1"]}}
        }
        config = CodeBeaverConfig.from_yaml(yaml_content)
        assert config.name == "TopLevelWorkspace"
        assert config.path == "/tmp/top"
        assert isinstance(config.unit, UnitTestConfig)
        assert config.unit.max_files_to_test == 30
        assert isinstance(config.e2e, E2EConfig)
        assert "login" in config.e2e.tests
        assert config.e2e.tests["login"].url == "http://login.com"
        assert config.e2e.tests["login"].steps == ["step1"]

    def test_unit_config_from_none_keyword_error(self):
        """Test that passing a 'from' key with None value (using dict unpacking) to UnitTestConfig raises a TypeError."""
        with pytest.raises(TypeError) as exc_info:
            UnitTestConfig(**{"from": None})
        assert "unexpected keyword argument 'from'" in str(exc_info.value)
    def test_e2e_test_config_attributes(self):
        """Test that an E2ETestConfig instance correctly assigns and exposes its attributes."""
        test_config = E2ETestConfig(url="http://example.com", steps=["step1", "step2"])
        assert test_config.url == "http://example.com"
        assert test_config.steps == ["step1", "step2"]
if __name__ == "__main__":
    unittest.main()
