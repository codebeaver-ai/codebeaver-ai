# Contributing to CodeBeaver Templates

Welcome! We're excited that you want to contribute to CodeBeaver Templates. This document provides guidelines and information about contributing.

## Getting Started

1. Fork this repository
2. Add a new template file
3. Open a pull request

## Adding New Templates

When adding a new template:

1. Make sure that the framework/language is not already present. Feel free to drop into our [Discord](https://discord.gg/4QMwWdsMGt) if you have any questions.
2. Read [the documentation about templates](https://docs.codebeaver.ai/open-source/codebeaver-yml)
3. Write a template and test it out (see below for how to test it)
4. Add the new template file. Try to respect the following naming conventions:
   - {framework}.yml -> `pytest.yml`
   - {language}-{framework}.yml -> `python-pytest.yml`
   - {language}-{version}-{framework}.yml -> `python-3.11-pytest.yml`
   - {language}-{shortened-version}-{framework}.yml -> `node-22-vitest.yml`
   - {language}-{version/shortened-version}-{framework}-{package_manager}.yml -> `node-22-vitest-yarn.yml`
5. Open a Pull Request
6. You are done!

Once your PR is merged, anybody will be able to use your template in their CodeBeaver projects.

## Testing Your Template

To test your changes, you can:

- Create a new Open source repository (here on GitHub or on the Git provider you prefer)
- Use your whole template as the `codebeaver.yml` file for the new repository
- Put some test code in the repository (or your whole code!)
- Open a Pull Request or use a [trigger](https://docs.codebeaver.ai/cloud/features/triggers) to test it out

## Community

- [Join our Discord community for discussions](https://discord.gg/4QMwWdsMGt)
- Report issues through GitHub Issues
- Contact the team at [info@codebeaver.ai](mailto:info@codebeaver.ai)

## License

By contributing, you agree that your contributions will be licensed under the MIT license (same as the other templates).
