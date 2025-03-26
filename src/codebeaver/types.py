from enum import Enum
from pydantic import BaseModel


class TestErrorType(Enum):
    TEST = "test"  # this means the test is not written correctly
    BUG = "bug"  # this means the code that is being tested is not written correctly
    SETTINGS = "settings"  # this means the test settings are not configured correctly


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
    failure: bool
    comment: str
    errored: bool = False
