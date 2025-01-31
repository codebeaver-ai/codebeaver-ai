import unittest

from expense_tracker import ExpenseTracker


class TestExpenseTracker(unittest.TestCase):
    def test_expense_tracker_initialization(self):
        tracker = ExpenseTracker()
        expected_categories = {
            "food",
            "transport",
            "utilities",
            "entertainment",
            "other",
        }
        self.assertEqual(tracker.categories, expected_categories)
        self.assertEqual(len(tracker.expenses), 0)

    def test_expenses_initialized_as_empty_list(self):
        tracker = ExpenseTracker()
        self.assertIsInstance(tracker.expenses, list)
        self.assertEqual(len(tracker.expenses), 0)

    def test_categories_is_set_with_default_categories(self):
        """
        Test that the ExpenseTracker is initialized with the correct default categories.
        """
        tracker = ExpenseTracker()
        self.assertIsInstance(tracker.categories, set)
        expected_categories = {
            "food",
            "transport",
            "utilities",
            "entertainment",
            "other",
        }
        self.assertEqual(tracker.categories, expected_categories)
        for category in expected_categories:
            self.assertIn(category, tracker.categories)

    def test_add_new_category(self):
        tracker = ExpenseTracker()
        initial_category_count = len(tracker.categories)
        new_category = "healthcare"
        tracker.categories.add(new_category)
        self.assertEqual(len(tracker.categories), initial_category_count + 1)
        self.assertIn(new_category, tracker.categories)

    def test_expenses_remain_empty_after_adding_category(self):
        tracker = ExpenseTracker()
        initial_expense_count = len(tracker.expenses)
        new_category = "healthcare"
        tracker.categories.add(new_category)
        self.assertEqual(len(tracker.expenses), initial_expense_count)
        self.assertEqual(len(tracker.expenses), 0)

    def test_remove_category(self):
        """
        Test that removing a category reduces the total number of categories by one.
        """
        tracker = ExpenseTracker()
        initial_category_count = len(tracker.categories)
        category_to_remove = "entertainment"

        tracker.categories.remove(category_to_remove)

        self.assertEqual(len(tracker.categories), initial_category_count - 1)
        self.assertNotIn(category_to_remove, tracker.categories)
        self.assertEqual(len(tracker.expenses), 0)  # Ensure expenses are still empty

    def test_direct_expense_manipulation(self):
        tracker = ExpenseTracker()
        initial_expense_count = len(tracker.expenses)
        initial_category_count = len(tracker.categories)

        # Directly add an expense to the expenses list
        new_expense = {"amount": 50, "category": "food", "description": "Groceries"}
        tracker.expenses.append(new_expense)

        # Check if the expense was added
        self.assertEqual(len(tracker.expenses), initial_expense_count + 1)
        self.assertIn(new_expense, tracker.expenses)

        # Ensure categories weren't affected
        self.assertEqual(len(tracker.categories), initial_category_count)
        self.assertNotIn("Groceries", tracker.categories)

    def test_add_multiple_categories(self):
        tracker = ExpenseTracker()
        initial_category_count = len(tracker.categories)
        new_categories = {"healthcare", "education", "savings"}

        tracker.categories.update(new_categories)

        self.assertEqual(
            len(tracker.categories), initial_category_count + len(new_categories)
        )
        for category in new_categories:
            self.assertIn(category, tracker.categories)
        self.assertEqual(len(tracker.expenses), 0)  # Ensure expenses are still empty

    def test_clear_all_categories(self):
        tracker = ExpenseTracker()
        initial_expense_count = len(tracker.expenses)

        # Clear all categories
        tracker.categories.clear()

        # Check if categories are empty
        self.assertEqual(len(tracker.categories), 0)

        # Ensure expenses weren't affected
        self.assertEqual(len(tracker.expenses), initial_expense_count)

    def test_modify_existing_category(self):
        tracker = ExpenseTracker()
        initial_category_count = len(tracker.categories)
        old_category = "entertainment"
        new_category = "entertainment_and_leisure"

        # Remove the old category and add the new one
        tracker.categories.remove(old_category)
        tracker.categories.add(new_category)

        # Check if the modification was successful
        self.assertEqual(len(tracker.categories), initial_category_count)
        self.assertNotIn(old_category, tracker.categories)
        self.assertIn(new_category, tracker.categories)

        # Ensure expenses weren't affected
        self.assertEqual(len(tracker.expenses), 0)
