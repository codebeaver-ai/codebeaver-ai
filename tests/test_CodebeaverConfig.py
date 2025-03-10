import logging
import sys
import unittest
from codebeaver.CodebeaverConfig import (
    CodeBeaverConfig,
    E2EConfig,
    E2ETestConfig,
    UnitTestConfig,
)


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
                "tests": {
                    "checkout": {
                        "url": "http://example.org",
                        "steps": ["stepA", "stepB"],
                    }
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
                "tests": {
                    "login": {"url": "http://example.com", "steps": ["step1", "step2"]}
                }
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
                "tests": {
                    "checkout": {
                        "url": "http://example.org",
                        "steps": ["stepA", "stepB"],
                    }
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
                "tests": {
                    "payment": {
                        "url": "http://pay.example.com",
                        "steps": ["init", "pay", "confirm"],
                    }
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


if __name__ == "__main__":
    unittest.main()
