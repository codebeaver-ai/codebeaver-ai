from dataclasses import dataclass

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
            name: E2ETestConfig(**test_config)
            for name, test_config in data.items()
        }
        return E2EConfig(tests=tests)

@dataclass
class UnitTestConfig:
  template: str | None = None
  max_files_to_test: int | None = None
  single_file_test_commands: list[str] | None = None
  setup_commands: list[str] | None = None
  test_commands: list[str] | None = None
  post_clone_commands: list[str] | None = None

@dataclass
class WorkspaceConfig:
  """
  Represents a workspace configuration as defined in codebeaver.yml
  """
  name: str | None = None
  path: str | None = None
  ignore: list[str] | None = None
  unit: UnitTestConfig | None = None
  e2e: E2EConfig | None = None

  @staticmethod
  def from_yaml(yaml_content: dict, workspace_name: str | None = None) -> "WorkspaceConfig":
    if "workspaces" in yaml_content:
      if not workspace_name:
        raise ValueError("workspace_name is required when workspaces are defined")
      if workspace_name not in yaml_content["workspaces"]:
        raise ValueError(f"workspace {workspace_name} not found in workspaces")
      return WorkspaceConfig(**yaml_content["workspaces"][workspace_name])
    else:
      return WorkspaceConfig(**yaml_content)