class InvestmentTracker:
    def __init__(self):
        self.expenses = []
        self.categories = set(
            ["food", "transport", "utilities", "entertainment", "other"]
        )

    ## new and improved defs below

    def record_transaction(self, amount, category, description):
        """Add a new expense to the tracker."""
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
        """Calculate total expenses."""
        return sum(expense["amount"] for expense in self.expenses)

    def filter_by_category(self, category):
        """Get all expenses for a specific category."""
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

    def register_new_category(self, category):
        """Add a new expense category."""
        if not isinstance(category, str) or not category.strip():
            raise ValueError("Category must be a non-empty string")

        category = category.lower().strip()
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
