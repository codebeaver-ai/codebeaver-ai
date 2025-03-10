import os
import json

from browser_use import Agent, Controller
from browser_use.browser.browser import Browser, BrowserConfig
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

import logging

load_dotenv()

logger = logging.getLogger('codebeaver')


class End2endTest(BaseModel):
    steps: list[str]
    url: str
    passed: bool = False
    errored: bool = False
    comment: str = ""
    name: str

    def __init__(self, name: str, steps: list[str], url: str):
        super().__init__(name=name, steps=steps, url=url)


class TestCase(BaseModel):
    passed: bool
    comment: str


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
            all_tests.append(test_result)
        # write the results to e2e.json
        # with open("e2e.json", "w") as f:
        #     json.dump([test.model_dump() for test in all_tests], f)
        return all_tests

    async def run_test(self, test: End2endTest) -> End2endTest:
        browser = Browser(
            config=BrowserConfig(
                # NOTE: you need to close your chrome browser - so that this can open your browser in debug mode
                chrome_instance_path=self.chrome_instance_path,
            )
        )
        agent = Agent(
            task=f"""You are a QA tester. Follow these steps:
          * Go to {test.url}
          * {test.steps}
          """,
            llm=ChatOpenAI(model="gpt-4o"),
            browser=browser,
            controller=controller,
        )
        history = await agent.run()
        await browser.close()
        result = history.final_result()
        if result:
            parsed: TestCase = TestCase.model_validate_json(result)
            test.passed = parsed.passed
            test.comment = parsed.comment
            return test
        else:
            test.errored = True
            test.comment = "No result from the test"
            return test
