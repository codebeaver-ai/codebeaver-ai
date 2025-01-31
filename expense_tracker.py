class ExpenseTracker:
    """
    A class to track expenses, divided by category.
    """

    def __init__(self):
        self.expenses = []
        self.categories = set(
            ["food", "transport", "utilities", "entertainment", "other"]
        )

    def total_expense_by_category(self, category: str) -> float:
        """
        Get total expenses for a specific category.
        """
        return sum(
            expense["amount"]
            for expense in self.expenses
            if expense["category"] == category.lower()
        )

    def add_expense_that_belongs_to_two_categories(self):
        """
        Add an expense that belongs to two categories.
        Not implemented yet.
        """
        raise NotImplementedError()


def main():
    # Example usage
    tracker = ExpenseTracker()

    print("nothing here yet")


if __name__ == "__main__":
    main()
