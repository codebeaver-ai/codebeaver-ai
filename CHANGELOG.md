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
