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

def test_get_tasks_by_importance(sample_tasks):
    """
    Test that the get_tasks_by_importance method correctly sorts tasks
    based on their importance score in descending order.
    """
    sorted_tasks = TaskUtils.get_tasks_by_importance(sample_tasks)
    assert len(sorted_tasks) == 4
    # "Urgent Task" should be at the top due to high priority and near due date.
    assert sorted_tasks[0]["title"] == "Urgent Task"
    # "Low Priority Task" should be last since it's low priority with a due date far in the future.
    assert sorted_tasks[-1]["title"] == "Low Priority Task"

def test_find_pending_overdue_tasks(sample_tasks):
    """
    Test that the find_pending_overdue_tasks method correctly identifies
    tasks that are overdue and not completed.
    """
    overdue_tasks = TaskUtils.find_pending_overdue_tasks(sample_tasks)
    assert len(overdue_tasks) == 1
    assert overdue_tasks[0]["title"] == "Overdue Task"
