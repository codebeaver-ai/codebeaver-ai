from codebeaver.E2E import End2endTest
import logging

logger = logging.getLogger('codebeaver')

class Report:
  """
  Generate a report for the CodeBeaver run. This is a WIP class that right now only renders a super simple summary.
  TODO:
  - Generate a JUnit XML report
  - Enhance it with the additional CodeBeaver info
  - Finalize the report
  - Render it to HTML, JSON, text and markdown
  See ReportRequirements.md for more details
  """
  def __init__(self, e2e_tests: list[End2endTest]) -> None:
    self.e2e_tests = e2e_tests

  def to_console(self) -> None:
    passed_tests = len([test for test in self.e2e_tests if test.passed])
    logger.info(f"🖥️  {passed_tests}/{len(self.e2e_tests)} E2E tests")
    for test in self.e2e_tests:
      if test.passed:
        logger.info(f"{test.name}: Success!")
      else:
        logger.info(f"{test.name}: Failed!")
        logger.info(f"  Comment: {test.comment}")
      logger.info("\n")

