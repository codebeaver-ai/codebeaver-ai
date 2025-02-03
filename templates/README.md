# CodeBeaver Templates

## Introduction

CodeBeaver is an automated testing platform that analyzes, executes, and generates unit tests for your codebase. This repository includes a number of open-source templates to setup CodeBeaver using a `codebeaver.yml` configuration file.

The `codebeaver.yml` file supports advanced features including:

- Multi-repository (monorepo) management
- Service dependencies
- External service integration
- Custom test execution and coverage reporting

## First configuration

CodeBeaver looks for a `codebeaver.yml` configuration file in your repository's root directory. If no configuration file is present, CodeBeaver will:

1. Analyze your codebase structure
2. Generate an appropriate `codebeaver.yml` file
3. Include this file in its initial pull request
4. Use this configuration for subsequent operations

For projects following standard structures (e.g., Python projects using pytest or React projects using Jest), the auto-generated configuration typically provides sufficient functionality, using [templates](#using-templates). You can then customize the configuration to your needs.

> Having issues with the first configuration? [Join our Discord](https://discord.gg/4QMwWdsMGt)

## Workspace

A Codebeaver.yml file is divided in workspaces. A workspace represent a separate test environment.

### Single Workspace

For repositories requiring one test environment, you can define the workspace at the root level like so:

```yaml
from: pytest
environment:
  - DJANGO_DEBUG=True
```

### Multiple Workspaces

For monorepos or projects requiring multiple test environments, you can define separate workspaces like so:

```yaml
workspaces:
  - name: django # Name of the workspace. Required.
    path: django-service # Path to the root of the workspace inside your repository. Required.
    from: pytest # In this case, we are using a template to configure the workspace.
  - name: react # This is the name of the second workspace.
    path: react-service
    from: jest
```

### Workspace reference

A workspace can have the following properties:

```yaml
services: # The services that you need to run your tests. These work exactly like docker-compose services. (Required)
  python:
    image: python:3.11
    environment: # You can define environment variables for your service. If you do, this environment variable will only be available to this service.
      - DJANGO_DEBUG=True
    depends_on:
      - redis
  redis:
    image: redis:latest
  postgres:
    build: # like docker-compose, you can define a build context and a Dockerfile to build your service.
      context: .
      dockerfile: Dockerfile
main_service: python # Primary service for test execution. It has to be one of the services defined in the services section. (Required)
environment: # Workspace-level environment variables. These will be available to all services in this workspace.
  - ENV=test

test_commands: # Test execution commands (Required)
  - coverage run -m pytest --show-capture=no --json-report
  - coverage combine
  - coverage json -i || true

single_file_test_commands: # Single file test execution
  - coverage run -m pytest --json-report "$TEST_FILE"
  - coverage json

setup_commands: # Pre-test setup commands
  - python --root-user-action=ignore -m ensurepip --default-pip || true

ignore: # A list of paths that CodeBeaver will ignore. Supports wildcards.
  - "**/node_modules"
  - "**/dist"
```

Services work just like docker-compose services. You can define ports, depends_on, and so on.

## Using templates

CodeBeaver provides pre-configured templates to simplify setup. Templates can be referenced using the `from` directive. For example, to use the `pytest` template without any customization:

```yaml
from: pytest
```

You can see a list of the [available templates below](#templates-list).

### Template Customization

Templates serve as a foundation that you can extend. For example, to add environment variables to a template:

```yaml
from: pytest
environment:
  - DJANGO_DEBUG=True
```

### Template Merging with @merge

The `@merge` directive is a powerful feature that allows you to combine any root-level configuration from a template with your custom configuration. It can be used in two ways:

1. As a list marker (`@merge`):
   - Place it as the first item in a list to combine with the template's list
2. As a dictionary directive (`{"@merge": value}`):
   - Use it to merge nested dictionaries or lists

The `@merge` directive can be used with any root-level configuration, including:

- `services`
- `environment`
- `setup_commands`
- `test_commands`
- `single_file_test_commands`

#### List Merging Example

```yaml
from: pytest
setup_commands:
  - @merge  # This will include all setup_commands from the pytest template
  - pip install -q selenium
  - pip install -q playwright
```

#### Dictionary Merging Example

```yaml
from: pytest
services:
  python:
    environment:
      "@merge": # This will merge with the template's python service environment
        CUSTOM_VAR: "true"
        ANOTHER_VAR: "123"
```

Without the `@merge` directive, your configuration would completely override the template's configuration. Including `@merge` ensures you're extending rather than replacing the template's settings:

```yaml
# With @merge - Extends template
from: pytest
environment:
  - @merge
  - CUSTOM_VAR=true  # Adds to template's environment variables

# Without @merge - Replaces template
from: pytest
environment:
  - CUSTOM_VAR=true  # Replaces ALL template's environment variables
```

## Templates list

CodeBeaver provides official templates for common testing frameworks:

- pytest
- pytest-django
- unittest
- jest
- nyc
- vitest
- bun

## Support and Feedback

CodeBeaver is currently in open beta. We welcome your feedback and suggestions:

- General Inquiries: [Contact info@codebeaver.ai](mailto:info@codebeaver.ai)
- Community Support: Join our [Discord community](https://discord.gg/4QMwWdsMGt)
