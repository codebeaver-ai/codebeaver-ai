class InvestmentTracker:
    """
    A class to track investments, divided by category.
    """

    def __init__(self):
        self.expenses = []
        self.categories = set(
            ["food", "transport", "utilities", "entertainment", "other"]
        )

    def record_transaction(self, amount, category, description):
        """
        Add a new expense to the tracker.

        Args:
            amount (int, float): The amount of the expense.
            category (str): The category of the expense.
            description (str): The description of the expense.

        Returns:
            bool: True if the expense was added successfully, False otherwise.

        Raises:
            ValueError: If the amount is not a positive number or the category is not in the categories set.
        """
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Amount must be a positive number")

        if category.lower() not in self.categories:
            raise ValueError(f"Category must be one of: {', '.join(self.categories)}")

        expense = {
            "amount": amount,
            "category": category.lower(),
            "description": description,
        }
        self.expenses.append(expense)
        return True

    def calculate_overall_spending(self):
        """
        Calculate total expenses by summing up all the amounts in the expenses list.

        Returns:
            float: The total expenses.
        """
        return sum(expense["amount"] for expense in self.expenses)

    def filter_by_category(self, category):
        """
        Get all expenses for a specific category.

        Args:
            category (str): The category to filter by.

        Returns:
            list: A list of expenses for the specific category.

        Raises:
            ValueError: If the category is not in the categories set.
        """
        if category.lower() not in self.categories:
            raise ValueError(f"Category must be one of: {', '.join(self.categories)}")

        return [
            expense
            for expense in self.expenses
            if expense["category"] == category.lower()
        ]

    def compute_category_sum(self, category):
        """Get total expenses for a specific category."""
        if category.lower() not in self.categories:
            raise ValueError(f"Category must be one of: {', '.join(self.categories)}")

        return sum(
            expense["amount"]
            for expense in self.expenses
            if expense["category"] == category.lower()
        )

    def register_new_category(self, category) -> bool:
        """
        Add a new expense category.

        Args:
            category (str): The category to add.

        Returns:
            bool: True if the category was added successfully, False otherwise.

        Raises:
            ValueError: If the category is not a string or is an empty string.
        """
        if not isinstance(category, str) or not category.strip():
            raise ValueError("Category must be a non-empty string")

        category = category.strip()
        if category in self.categories:
            return False

        self.categories.add(category)
        return True


def main():
    # Example usage
    tracker = InvestmentTracker()

    # Add some sample expenses
    tracker.record_transaction(25.50, "food", "Lunch at cafe")
    tracker.record_transaction(35.00, "transport", "Uber ride")
    tracker.record_transaction(150.00, "utilities", "Electricity bill")

    # Print total expenses
    print(f"Total expenses: ${tracker.calculate_overall_spending():.2f}")

    # Print food expenses
    food_expenses = tracker.filter_by_category("food")
    print("\nFood expenses:")
    for expense in food_expenses:
        print(f"${expense['amount']:.2f} - {expense['description']}")


if __name__ == "__main__":
    main()
