from datetime import datetime, timedelta
from dateutil.parser import parse
from typing import List, Dict, Any


class TaskUtils:
    @staticmethod
    def compute_task_importance(task: Dict[str, Any]) -> int:
        """
        Compute an importance score for a task based on its priority level and due date.
        Higher scores indicate more important tasks that should be addressed first.
        """
        priority_weights = {"HIGH": 100, "MEDIUM": 50, "LOW": 10}

        base_score = priority_weights.get(task["priority"], 0)

        if task.get("due_date"):
            due_date = (
                parse(task["due_date"])
                if isinstance(task["due_date"], str)
                else task["due_date"]
            )
            now = datetime.now(due_date.tzinfo)

            # Add urgency score based on due date proximity
            days_until_due = (due_date - now).days
            if days_until_due <= 1:
                base_score += 50  # Very urgent - due within 24 hours
            elif days_until_due <= 3:
                base_score += 30  # Urgent - due within 3 days
            elif days_until_due <= 7:
                base_score += 10  # Approaching - due within a week

        return base_score

    @staticmethod
    def get_tasks_by_importance(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Return tasks sorted by their importance score in descending order.
        Most important tasks appear first in the list.
        """
        return sorted(
            tasks, key=lambda x: TaskUtils.compute_task_importance(x), reverse=True
        )

    @staticmethod
    def find_pending_overdue_tasks(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find all incomplete tasks that have passed their due date.
        Returns a list of tasks that need immediate attention.
        """
        now = datetime.now(datetime.now().astimezone().tzinfo)
        return [
            task
            for task in tasks
            if task.get("due_date")
            and (
                parse(task["due_date"])
                if isinstance(task["due_date"], str)
                else task["due_date"]
            )
            < now
            and task["status"] != "DONE"
        ]
