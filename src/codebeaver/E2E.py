import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

from browser_use import Agent, Controller
from browser_use.browser.browser import Browser, BrowserConfig
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

load_dotenv()


class End2endTest:
    steps: "list[str]"
    url: str
    passed: bool
    errored: bool
    comment: str
    name: str

    def __init__(self, name: str, steps: "list[str]", url: str):
        self.name = name
        self.steps = steps
        self.url = url
        self.passed = False
        self.errored = False
        self.comment = ""


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

    async def run(self):
        all_tests: list[End2endTest] = []
        for test_name, test in self.tests.items():
            print("Running test: ", test_name)
            test = End2endTest(
                name=test_name,
                steps=test["steps"],
                url=test["url"],
            )
            test_result = await self.run_test(test)
            all_tests.append(test_result)
        # write the results to e2e.json
        with open("e2e.json", "w") as f:
            json.dump(all_tests, f)
        total_passed = sum(1 for test in all_tests if test.passed)
        print(f"🖥️ {total_passed}/{len(all_tests)} E2E tests passed")
        print("-" * 80)
        print("Name", "Passed", "Comment")
        print("-" * 80)
        for test in all_tests:
            print(test.name, test.passed, test.comment)
        print("-" * 80)
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
