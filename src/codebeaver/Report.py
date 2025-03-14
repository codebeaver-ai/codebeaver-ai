from .types import End2endTest


class Report:
    """
    A class that generates a report of the test results. For now, only used for E2E test results, but in the future it will produce one unique report if it will be the case.
    """

    def __init__(self) -> None:
        self.e2e_results: list[End2endTest] = []

    def add_e2e_results(self, e2e_results: list[End2endTest]) -> None:
        self.e2e_results.extend(e2e_results)

    def generate_xml_report(self) -> str:
        """
        Generate a XML report of the test results, in a format that is compatible with junit.xml
        """
        xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml_lines.append('<testsuites name="End2End Tests">')

        # Create a single test suite for all E2E tests
        xml_lines.append(
            '  <testsuite name="E2E Test Suite" tests="{}"'.format(
                len(self.e2e_results)
            )
        )

        # Count failures and errors
        failures = sum(
            1 for test in self.e2e_results if not test.passed and not test.errored
        )
        errors = sum(1 for test in self.e2e_results if test.errored)
        xml_lines.append(f'    failures="{failures}" errors="{errors}">')

        # Add individual test cases
        for test in self.e2e_results:
            xml_lines.append(
                '    <testcase name="{}" classname="E2ETest">'.format(test.name)
            )

            # Add steps as system-out
            steps_text = "\n".join(test.steps)
            xml_lines.append(f"      <system-out>{steps_text}</system-out>")

            # Add failure or error information if present
            if test.errored:
                xml_lines.append(
                    '      <error message="Test execution error" type="Error">'
                )
                xml_lines.append(f"        {test.comment}")
                xml_lines.append("      </error>")
            elif not test.passed:
                xml_lines.append('      <failure message="Test failed" type="Failure">')
                xml_lines.append(f"        {test.comment}")
                xml_lines.append("      </failure>")

            xml_lines.append("    </testcase>")

        xml_lines.append("  </testsuite>")
        xml_lines.append("</testsuites>")

        return "\n".join(xml_lines)

    def generate_html_report(self) -> str:
        raise NotImplementedError("HTML report generation not implemented")

    def generate_json_report(self) -> str:
        raise NotImplementedError("JSON report generation not implemented")
