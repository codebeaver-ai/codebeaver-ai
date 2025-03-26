import pytest
from pydantic import ValidationError

from src.codebeaver.types import End2endTest, TestCase, TestErrorType


# Tests for TestErrorType Enum
def test_test_error_type_values():
    """Test that TestErrorType enum contains the correct values."""
    assert TestErrorType.TEST.value == "test"
    assert TestErrorType.BUG.value == "bug"
    assert TestErrorType.SETTINGS.value == "settings"


# Tests for End2endTest Model
def test_end2end_test_defaults():
    """Test that End2endTest initializes with given parameters and defaults for optional fields."""
    steps = ["step1", "step2"]
    url = "http://example.com"
    name = "MyEnd2endTest"
    test_instance = End2endTest(name=name, steps=steps, url=url)
    # Verify that provided fields are set correctly.
    assert test_instance.name == name
    assert test_instance.steps == steps
    assert test_instance.url == url
    # Verify default values.
    assert test_instance.passed is False
    assert test_instance.errored is False
    assert test_instance.comment == ""


def test_end2end_test_missing_field():
    """Test that missing required fields in End2endTest raise a TypeError."""
    steps = ["step1", "step2"]
    url = "http://example.com"
    # The __init__ method requires the 'name' argument.
    with pytest.raises(TypeError):
        End2endTest(steps=steps, url=url)


# Tests for TestCase Model
def test_test_case_initialization():
    """Test that TestCase initializes properly with required and optional fields."""
    # Create a TestCase with failure set to True, a comment provided, and use default for errored
    test_case = TestCase(failure=True, comment="Test failure occurred")
    assert test_case.failure is True
    assert test_case.comment == "Test failure occurred"
    assert test_case.errored is False


def test_test_case_validation_error():
    """Test that TestCase raises a ValidationError if required fields are missing."""
    with pytest.raises(ValidationError):
        # 'failure' field is missing which is required.
        TestCase(comment="Missing failure field")


def test_end2end_test_invalid_steps_type():
    """Test that End2endTest raises a ValidationError if steps is not a list of strings."""
    with pytest.raises(ValidationError):
        # Passing a string instead of a list of strings should fail validation.
        End2endTest(name="InvalidSteps", steps="not-a-list", url="http://example.com")


def test_end2end_test_extra_field():
    """Test that End2endTest __init__ does not allow extra keyword arguments."""
    with pytest.raises(TypeError):
        # The __init__ signature only accepts name, steps, and url.
        End2endTest(
            name="ExtraFieldTest",
            steps=["step1"],
            url="http://example.com",
            passed=True,
        )


def test_end2end_test_dict_method():
    """Test that the dict() method of End2endTest returns a correct dictionary representation including default values."""
    instance = End2endTest(name="DictTest", steps=["s1"], url="http://example.com")
    # Manually update the optional fields to non‑default values.
    instance = instance.copy(
        update={"passed": True, "errored": True, "comment": "Test complete"}
    )
    result = instance.dict()
    expected = {
        "name": "DictTest",
        "steps": ["s1"],
        "url": "http://example.com",
        "passed": True,
        "errored": True,
        "comment": "Test complete",
    }
    assert result == expected


def test_test_case_extra_field():
    """Test that TestCase ignores extra fields not defined in the model."""
    # pydantic by default ignores extra fields, so extra_field should not appear in instance.dict().
    instance = TestCase(
        failure=False, comment="Extra field allowed", extra_field="ignored"
    )
    result = instance.dict()
    expected = {"failure": False, "comment": "Extra field allowed", "errored": False}
    assert result == expected


def test_test_case_to_dict():
    """Test that the dict() method of TestCase returns the correct dictionary representation."""
    instance = TestCase(failure=True, comment="All good", errored=True)
    result = instance.dict()
    expected = {"failure": True, "comment": "All good", "errored": True}
    assert result == expected


def test_test_case_update():
    """Test that updating a TestCase model using copy(update=...) works as expected."""
    instance = TestCase(failure=False, comment="Initial")
    updated = instance.copy(
        update={"failure": True, "comment": "Updated", "errored": True}
    )
    expected = {"failure": True, "comment": "Updated", "errored": True}
    assert updated.dict() == expected


def test_end2end_test_json_method():
    """Test that the json() method returns the correct JSON representation."""
    instance = End2endTest(
        name="JSONTest", steps=["step1", "step2"], url="http://example.com"
    )
    # Manually update optional fields to non-default values.
    instance = instance.copy(
        update={"passed": True, "errored": True, "comment": "JSON test complete"}
    )
    json_str = instance.json()
    import json

    result = json.loads(json_str)
    expected = {
        "name": "JSONTest",
        "steps": ["step1", "step2"],
        "url": "http://example.com",
        "passed": True,
        "errored": True,
        "comment": "JSON test complete",
    }
    assert result == expected


def test_test_case_invalid_failure_type():
    """Test that providing an invalid type for the 'failure' field raises a ValidationError."""
    with pytest.raises(ValidationError):
        TestCase(failure="not boolean", comment="Invalid failure type")


def test_test_case_parse_obj():
    """Test that parse_obj() initializes a TestCase correctly, ignoring extra fields."""
    data = {
        "failure": True,
        "comment": "Parsed successfully",
        "errored": False,
        "extra": "should be ignored",
    }
    obj = TestCase.parse_obj(data)
    expected = {"failure": True, "comment": "Parsed successfully", "errored": False}
    assert obj.dict() == expected


def test_end2end_test_steps_must_all_be_strings():
    """Test that End2endTest raises a ValidationError if any step in 'steps' is not a string."""
    with pytest.raises(ValidationError):
        End2endTest(
            name="InvalidStepType", steps=["valid", 123], url="http://example.com"
        )
