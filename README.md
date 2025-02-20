 <div align="center">
 <picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://www.codebeaver.ai/logo_complete_color_inverted.png" width="330">
  <source media="(prefers-color-scheme: light)" srcset="https://www.codebeaver.ai/logo_complete_color.png" width="330">
  <img src="https://www.codebeaver.ai/logo_complete_color.png" alt="logo" width="330">

</picture>
<h1 align="center">Unit Tests on Autopilot</h1>
</div>
<br/><br/>

[![GitHub license](https://img.shields.io/badge/License-AGPL_3.0-blue.svg)](https://github.com/codebeaver-ai/codebeaver-ai/blob/main/LICENSE)
[![Discord](https://badgen.net/badge/icon/discord?icon=discord&label&color=purple)](https://discord.gg/4QMwWdsMGt)
<a href="https://github.com/codebeaver-ai/codebeaver-ai/commits/main">
<img alt="GitHub" src="https://img.shields.io/github/last-commit/codebeaver-ai/codebeaver-ai/main?style=for-the-badge" height="20">
</a><br>

🪵 CodeBeaver runs, writes and updates unit tests.

🐛 If a test fails due to a bug, CodeBeaver will spot it and explain how to fix it.

🌩️ Skip the setup - [try our hosted version](https://www.codebeaver.ai) to get Unit Tests after every Pull Request!

**CodeBeaver** supercharges your development workflow by:

- Writing new tests when you need them
- Keeping your test suite up-to-date as your code evolves
- Adding edge cases you might have missed
- Pinpointing exactly where bugs are hiding in your code

## Quick start

Quickstart:

```bash
pip install codebeaver
codebeaver run pytest
```

This will run CodeBeaver with the pytest framework. You will get a report like the following:

```
🔄 1 test added and 1 test updated to reflect recent changes.
🐛 Found 1 bug
🛠️ 15/15 tests passed

🔄 Test Updates
I've added or updated 6 tests. They all pass ☑️
Updated Tests:

tests/test_expense_tracker.py 🩹
Fixed: tests/test_expense_tracker.py::TestExpenseTracker::test_categories_is_set_with_default_categories

New Tests:

tests/test_alert_manager.py
tests/test_investment_tracker.py

🐛 Bug Detection
Potential issues found in the following files:

expense_tracker.py
The error occurs because the code in total_expense_by_category only converts the input parameter (category) to lower-case and compares it with the expense entries exactly. However, the expenses added in the test have "category" values in different cases (e.g., "FOOD", "Food") that are not converted to lower-case, so they don't match "food" (the lowercased input). This makes the method only sum the expense that exactly matches "food" in lower-case, resulting in an incorrect sum.
```

## See it in action

Want to see the magic? Check out these real examples from our Pull Requests:

- [CodeBeaver discovers a bug and explains where the problem is](https://github.com/codebeaver-ai/codebeaver-ai/pull/8)
- [CodeBeaver updates a test given the new code commited](https://github.com/codebeaver-ai/codebeaver-ai/pull/12)

## Try it yourself

Got a project in mind? Let's see CodeBeaver in action with your code:

1. Fork this repo (main branch is fine)
2. Create a new branch
3. Drop in your code
4. Open a PR
5. Watch CodeBeaver do its thing
6. Check out the results!

## Resources

- [Read the docs](https://docs.codebeaver.ai/getting-started/quickstart)
- [Configure with codebeaver.yml](https://docs.codebeaver.ai/configuration)

## Let's chat!

- Found a bug? Open an issue!
- Join the community on [Discord](https://discord.gg/4QMwWdsMGt)
- Questions? Hit us up at [info@codebeaver.ai](mailto:info@codebeaver.ai)
