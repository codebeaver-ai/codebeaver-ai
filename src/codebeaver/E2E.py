import os
import json
from browser_use import Agent, Controller
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from .GitUtils import GitUtils
import logging
from browser_use.browser.context import BrowserContextConfig
from pathlib import Path
from .types import End2endTest, TestCase
from .Report import Report

load_dotenv()

logger = logging.getLogger("codebeaver")


controller = Controller(output_model=TestCase)


class E2E:
    """
    E2E class for running end2end tests.
    """

    def __init__(
        self,
        tests: dict,
        chrome_instance_path: str = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ):
        self.tests = tests
        self.chrome_instance_path = chrome_instance_path
        if os.getenv("CHROME_INSTANCE_PATH"):
            self.chrome_instance_path = os.getenv("CHROME_INSTANCE_PATH")

    async def run(self) -> list[End2endTest]:
        all_tests: list[End2endTest] = []
        for test_name, test in self.tests.items():
            logger.debug(f"Running E2E: {test_name}")
            test = End2endTest(
                name=test_name,
                steps=test["steps"],
                url=test["url"],
            )
            test_result = await self.run_test(test)
            test.passed = not test_result.failure
            test.errored = test_result.errored
            test.comment = test_result.comment
            all_tests.append(test)
        # write the results to e2e.json. this is temporary, we will eventually use the report class
        with open(Path.cwd() / ".codebeaver/e2e.json", "w") as f:
            json.dump([test.model_dump() for test in all_tests], f)
        report = Report()
        report.add_e2e_results(all_tests)
        with open(Path.cwd() / ".codebeaver/e2e.xml", "w") as f:
            f.write(report.generate_xml_report())
        return all_tests

    async def run_test(self, test: End2endTest) -> TestCase:
        GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore()  # avoid committing logs, screenshots and so on
        config_context = BrowserContextConfig(
            save_recording_path=Path.cwd() / ".codebeaver/",
            trace_path=Path.cwd() / ".codebeaver/",
        )
        browser = Browser(
            config=BrowserConfig(
                # NOTE: you need to close your chrome browser - so that this can open your browser in debug mode
                chrome_instance_path=self.chrome_instance_path,
            )
        )
        context = BrowserContext(browser=browser, config=config_context)
        agent = Agent(
            task=f"""You are a QA tester. Follow these instructions to perform the test called {test.name}:
* Go to {test.url}
"""
            + "\n".join(f"* {step}" for step in test.steps)
            + "\n\nIf any step that starts with 'Check' fails, the result is a failure",
            llm=ChatOpenAI(model="gpt-4o"),
            controller=controller,
            browser_context=context,
        )
        history = await agent.run()
        await context.close()
        result = history.final_result()
        if result:
            test_result: TestCase = TestCase.model_validate_json(result)
            return test_result
        else:
            test_result.errored = True
            test_result.comment = "No result from the test"
            return test_result
