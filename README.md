# CodeBeaver

Get to 100% Unit Test Coverage in 2 clicks

## What is CodeBeaver?

**CodeBeaver** is an A.I. agent that writes and runs unit tests. You can connect it to your Github or Gitlab repository and it will write unit tests for your code until you get to 100% coverage.

Developers can interact with the A.I. agent via comments on Pull Requests by adding `@codebeaver` to the comment. You can also add a `codebeaver.yaml` file to your repository to configure the test pipeline.

## Quickstart

1. Visit [CodeBeaver](https://www.codebeaver.ai)
2. Authenticate using your GitHub or Bitbucket credentials
3. Follow the guided setup to grant CodeBeaver access to your organization/workspace
4. Select the repositories you want to enable CodeBeaver for

## Integrations with GitHub and GitLab

**CodeBeaver** integrates with GitHub, GitLab, and Bitbucket repositories. After a defined action - by default, when a PR is opened - CodeBeaver will analyze your codebase. It will determine if it needs to write tests for the PR. If it does, it will write the tests and run them. It will then iterate on the tests until you get to 100% coverage. Once it does, CodeBeaver will open a PR on top of the original PR, so you can merge it into your PR.

## Add your repository

By default, CodeBeaer will ask you to add a repository to your account. You can also add one by:

- Going to your Dashboard
- Clicking on "Add Repository"
- Selecting your repository
- Clicking on "Add"

## Need help?

- You can join the [Discord community](https://discord.gg/4QMwWdsMGt) to get help from the community and the team. You will find the link in the email invite.
- Contact us at [info@codebeaver.ai](mailto:info@codebeaver.ai)
