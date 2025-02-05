import pytest
from datetime import datetime, timedelta
from tasks.utils import TaskUtils


@pytest.fixture
def sample_tasks():
    now = datetime.now(datetime.now().astimezone().tzinfo)
    return [
        {
            "title": "Urgent Task",
            "priority": "HIGH",
            "due_date": (now + timedelta(days=1)).isoformat(),
            "status": "TODO",
        },
        {
            "title": "Regular Task",
            "priority": "MEDIUM",
            "due_date": (now + timedelta(days=5)).isoformat(),
            "status": "TODO",
        },
        {
            "title": "Low Priority Task",
            "priority": "LOW",
            "due_date": (now + timedelta(days=10)).isoformat(),
            "status": "TODO",
        },
        {
            "title": "Overdue Task",
            "priority": "HIGH",
            "due_date": (now - timedelta(days=1)).isoformat(),
            "status": "TODO",
        },
    ]


def test_calculate_priority_score():
    task = {
        "priority": "HIGH",
        "due_date": (datetime.now() + timedelta(days=1)).isoformat(),
    }
    score = TaskUtils.calculate_priority_score(task)
    assert score > 100  # Base score (100) + urgency bonus (50)


def test_sort_tasks_by_priority(sample_tasks):
    sorted_tasks = TaskUtils.sort_tasks_by_priority(sample_tasks)
    assert len(sorted_tasks) == 4
    assert sorted_tasks[0]["title"] == "Urgent Task"  # High priority + due soon
    assert sorted_tasks[-1]["title"] == "Low Priority Task"  # Low priority + due later


def test_get_overdue_tasks(sample_tasks):
    overdue_tasks = TaskUtils.get_overdue_tasks(sample_tasks)
    assert len(overdue_tasks) == 1
    assert overdue_tasks[0]["title"] == "Overdue Task"


def test_priority_score_without_due_date():
    task = {"priority": "HIGH"}
    score = TaskUtils.calculate_priority_score(task)
    assert score == 100  # Only base priority score, no urgency bonus
