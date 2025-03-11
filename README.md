 <div align="center">
 <picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://www.codebeaver.ai/logo_complete_inverted.png" width="330">
  <source media="(prefers-color-scheme: light)" srcset="https://www.codebeaver.ai/logo_complete_color.png" width="330">
  <img src="https://www.codebeaver.ai/logo_complete_color.png" alt="logo" width="330">

</picture>
<h1 align="center">Testing on Autopilot</h1>
</div>
<br/><br/>

[![GitHub license](https://img.shields.io/badge/License-MIT-orange.svg)](https://github.com/codebeaver-ai/codebeaver-ai/blob/main/LICENSE)
[![Discord](https://badgen.net/badge/icon/discord?icon=discord&label&color=orange)](https://discord.gg/4QMwWdsMGt)
[![Documentation](https://img.shields.io/badge/Documentation-📖-orange)](https://docs.codebeaver.ai)
<a href="https://github.com/codebeaver-ai/codebeaver-ai/commits/main">
<img alt="GitHub" src="https://img.shields.io/github/last-commit/codebeaver-ai/codebeaver-ai/main?style=for-the-badge" height="20">
</a><br>

CodeBeaver is an open-source testing automation tool that leverages AI to simplify the testing process. It helps developers:

- 🤖 **Run end-to-end tests** using natural language descriptions
- 🧪 **Generate and maintain unit tests** automatically for your codebase
- 🐛 **Detect potential bugs** and provide detailed fix explanations
- ⚡ **Reduce testing overhead** while improving code quality

Currently supporting Python and TypeScript, with more languages coming soon.

## Quickstart

Install the package

```bash
pip install codebeaver
```

Add a yaml file to your project called `codebeaver.yaml`. This tells CodeBeaver what to test and how.

```yaml
e2e:
  login-test: # Name of the test. You can add more
    url: "localhost:3000" # Starting URL of your app. It can be a local server or a remote server
    steps:
      - Login with Github
      - Go to the team page
      - Change the team name to "e2e"
      - Click on the "Save" button
      - Check that the team name is "e2e" # use words like "Check that" to assert the results of the test
unit:
  from: pytest # The Unit testing framework you want to use
```

That's it. To run it, you need to have an OpenAI API key and Chrome installed.

```bash
export OPENAI_API_KEY="your-openai-api-key"
codebeaver

```

You will get a summary report like the following:

```bash

🖥️ 1/1 E2E tests

login-test: Success!

🧪 14/15 Unit tests

🔄 1 test added and 1 test updated to reflect recent changes.
🐛 Found 1 bug
```

## Examples

- [CodeBeaver discovers a bug and explains where the problem is](https://github.com/codebeaver-ai/codebeaver-ai/pull/8)
- [CodeBeaver updates a test given the new code commited](https://github.com/codebeaver-ai/codebeaver-ai/pull/12)

## GitHub Action

CodeBeaver can be used in a [GitHub Action](https://github.com/codebeaver-ai/codebeaver-oss-action) to run unit tests on every commit and E2E tests after you release a new version.

Check out the action's [README](https://github.com/codebeaver-ai/codebeaver-oss-action/blob/main/README.md) for more information, but here's a quick example:

```yaml
name: Run CodeBeaver

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: codebeaver-ai/codebeaver-oss-action@0.1.0
        with:
          action-type: "unit"
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  after-deployment: # In this example, this step runs after a new release is deployed
    needs: unit-tests
    runs-on: ubuntu-latest
    steps:
      - uses: codebeaver-ai/codebeaver-os-action@v0.1.0
        with:
          action-type: "e2e"
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          STARTING_URL: "http://yourstaging.yourwebsite.com"
```

## CLI Reference

### Commands

- `codebeaver`: Without any command, runs both unit and E2E tests if defined in codebeaver.yml
- `codebeaver unit`: Generates and runs unit tests for a specific file
- `codebeaver e2e`: Runs end-to-end tests defined in codebeaver.yml

### Command Options

#### Global Options

- `-v, --verbose`: Enable verbose logging output
- `--version`: Display CodeBeaver version number

#### Unit Test Command

```bash
codebeaver unit --file <file_path> [--template <template_name>] [--max-files-to-test <number>] [--verbose]
```

- `--file`: (Required) Path to the file to analyze
- `--template`: (Optional) Testing framework template to use (e.g., pytest, jest, vitest). If not specified, uses template from codebeaver.yml
- `--max-files-to-test`: (Optional) Maximum number of files to generate unit tests for (default: 10)
- `-v, --verbose`: (Optional) Enable verbose logging output

#### E2E Test Command

```bash
codebeaver e2e [--config <config_file>] [--verbose]
```

- `--config`: (Optional) Path to the YAML configuration file (defaults to codebeaver.yml)
- `-v, --verbose`: (Optional) Enable verbose logging output

### Environment Variables

- `OPENAI_API_KEY`: (Required) Your OpenAI API key
- `CHROME_INSTANCE_PATH`: Path to your Chrome instance. Defaults to `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`

### Supported Languages and Frameworks

CodeBeaver currently supports:

- Python
- TypeScript

## Resources

- [Documentation](https://docs.codebeaver.ai/)
- [E2E is powered by BrowserUse](https://github.com/browser-use/browser-use)

## Roadmap

- [✅] Unit tests
- [✅] E2E Tests
- [ ] Integration Tests
- [ ] Unit Tests: Add support for more languages and frameworks
- [ ] Unit Tests: Add support for more testing frameworks
- [ ] Add support for more models

## Let's chat!

- Found a bug? Open an issue!
- Join the community on [Discord](https://discord.gg/4QMwWdsMGt)
- Questions? Hit us up at [info@codebeaver.ai](mailto:info@codebeaver.ai)
