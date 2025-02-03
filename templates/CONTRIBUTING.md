# Contributing to CodeBeaver Templates

Welcome! We're excited that you want to contribute to CodeBeaver Templates. This document provides guidelines and information about contributing.

## Getting Started

1. Fork the repository
2. Clone your fork:

````bash
git clone git@github.com:codebeaver-ai/codebeaver-templates.git

Copy

Apply

CONTRIBUTING.md
3. Create a new branch for your changes:
```bash
git checkout -b template/your-template-name

Copy

Apply

CONTRIBUTING.md
## Adding New Templates

When adding a new template:

1. Check if your framework already exists under the `templates/` folder. If not, add a new directory under `templates/` with your framework name.
2. Add a new template file with the base configuration. Possible naming configurations:
   - {framework}.yml -> `pytest.yml`
   - {language}-{framework}.yml -> `python-pytest.yml`
   - {language}-{version}-{framework}.yml -> `python-3.11-pytest.yml`
   - {language}-{shortened-version}-{framework}.yml -> `node-22-vitest.yml`
   - {language}-{version/shortened-version}-{framework}-{package_manager}.yml -> `node-22-vitest-yarn.yml`
3. Update the list of supported templates in the template directory's README.md

## Template Guidelines
- Keep templates minimal but functional
- Include only necessary services and dependencies
- Document environment variables clearly

## Testing Your Changes
1. Test your template with various project structures
2. Verify all commands work in isolation
3. Ensure proper service dependencies
4. Check environment variable propagation

## Submitting Changes
1. Push your changes to your fork
2. Create a Pull Request with:
    - Clear description of the template's structure
    - Example usage
    - If possible, include a link to a sample project for testing
    - Updates to documentation

## Code Review Process
1. Maintainers will review your PR
2. Address any feedback or requested changes
3. Once approved, your template will be merged

## Community
- [Join our Discord community for discussions](https://discord.gg/4QMwWdsMGt)
- Report issues through GitHub Issues
- Contact the team at info@codebeaver.ai

## License
By contributing, you agree that your contributions will be licensed under the same license as the project.

Thank you for contributing to CodeBeaver Templates!
