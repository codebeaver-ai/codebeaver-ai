## 1.0.0 (2025-03-10)


### Bug Fixes

* **release:** better types, logging and first version of analyzer ([ce4ac77](https://github.com/codebeaver-ai/codebeaver-ai/commit/ce4ac77814b4c780503b287823cdf03a7769ecfa))


### Test

* Add coverage improvement test for tests/test_E2E.py ([b128e32](https://github.com/codebeaver-ai/codebeaver-ai/commit/b128e320ae895880fbfd1aefec221d93f24bcc11))
* Add coverage improvement test for tests/test_TestRunner.py ([489862f](https://github.com/codebeaver-ai/codebeaver-ai/commit/489862ffba10bc33c653ade165dff7ad120ab539))

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
