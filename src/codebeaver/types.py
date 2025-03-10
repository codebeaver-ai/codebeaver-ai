from enum import Enum


class TestErrorType(Enum):
    TEST = "test"  # this means the test is not written correctly
    BUG = "bug"  # this means the code that is being tested is not written correctly
    SETTINGS = "settings"  # this means the test settings are not configured correctly
