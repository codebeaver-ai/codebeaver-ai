## [1.1.0](https://github.com/codebeaver-ai/codebeaver-ai/compare/v1.0.0...v1.1.0) (2025-03-26)


### Features

* add multi model suport ([ae27d19](https://github.com/codebeaver-ai/codebeaver-ai/commit/ae27d198ef20a12a859e5ab22884df9f72e3072f))
* add new regex ([74dd163](https://github.com/codebeaver-ai/codebeaver-ai/commit/74dd1630b92e5be7f2b632846421fc5bbcca2826))
* add support for ollama ([1e85a97](https://github.com/codebeaver-ai/codebeaver-ai/commit/1e85a9732eeb993ce81a723f5a812b95e6696d82))


### Test

* Add coverage improvement test for tests/test_ContentCleaner.py ([1a77a41](https://github.com/codebeaver-ai/codebeaver-ai/commit/1a77a419bbf7d80e182264dd205347c43bb0e29c))
* Update coverage improvement test for tests/test_E2E.py ([48e1338](https://github.com/codebeaver-ai/codebeaver-ai/commit/48e1338de835994147fb97cc61398cf3ab187559))

## [0.1.2] - 2025-03-26

### Added

- Added a new command `codebeaver e2e` to run end-to-end tests defined in configuration
- Added XML report generation for end-to-end tests

## [0.1.0] - 2024-03-10

### Added

- Initial project setup
- Core functionality for automated testing with AI
- End-to-end (E2E) testing capabilities using natural language descriptions
- Unit test generation and maintenance for Python and TypeScript
- Bug detection with detailed fix explanations
- CLI commands for running tests:
  - `codebeaver`: Run both unit and E2E tests
  - `codebeaver unit`: Generate and run unit tests for specific files
  - `codebeaver e2e`: Run end-to-end tests defined in configuration
- Configuration via `codebeaver.yaml` file
- GitHub Action integration for CI/CD workflows
- Support for pytest framework for unit testing
- Browser automation for E2E tests powered by BrowserUse
- Comprehensive logging and reporting

### Notes

This is the first beta release of CodeBeaver. While the core functionality is stable,
some features are still under development. We welcome feedback and contributions from the community.
