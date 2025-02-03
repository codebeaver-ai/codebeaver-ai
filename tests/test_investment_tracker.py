import pytest
import unittest

from investment_tracker import InvestmentTracker

class TestInvestmentTracker(unittest.TestCase):
    """Test class for InvestmentTracker methods."""

    def test_record_transaction(self):
        """Test recording a valid transaction and raising errors for invalid transactions."""
        tracker = InvestmentTracker()

        # Test a valid transaction
        result = tracker.record_transaction(50.0, "food", "Dinner")
        self.assertTrue(result)
        self.assertEqual(len(tracker.expenses), 1)

        # Test invalid amount: zero
        with self.assertRaises(ValueError):
            tracker.record_transaction(0, "food", "Zero expense")

        # Test invalid amount: negative number
        with self.assertRaises(ValueError):
            tracker.record_transaction(-10, "food", "Negative expense")

        # Test invalid category
        with self.assertRaises(ValueError):
            tracker.record_transaction(25, "nonexistent", "Invalid category")

    def test_register_new_category(self):
        """Test adding a new category successfully."""
        tracker = InvestmentTracker()
        self.assertEqual(tracker.register_new_category("Food"), True)

    def test_register_new_category_empty_string(self):
        """Test that registering an empty string category raises ValueError."""
        tracker = InvestmentTracker()
        with self.assertRaises(ValueError):
            tracker.register_new_category("")

if __name__ == "__main__":
    unittest.main()

def test_calculations_filter_and_category_sum():
    """
    Test overall spending calculation, filtering by category, and computing the category sums.

    This test verifies that:
    - The overall spending is the sum of the individual transaction amounts.
    - Filtering by a valid category returns only transactions of that category.
    - Compute_category_sum returns the correct sum.
    - Filtering or computing the sum for an invalid category raises a ValueError.
    """
    tracker = InvestmentTracker()

    # Record sample transactions
    tracker.record_transaction(20, "food", "Breakfast")
    tracker.record_transaction(30, "transport", "Bus fare")
    tracker.record_transaction(10, "food", "Snack")

    # Verify overall spending calculation:
    overall_spending = tracker.calculate_overall_spending()
    assert overall_spending == 60   # 20 + 30 + 10

    # Verify filtering by category "food":
    food_expenses = tracker.filter_by_category("food")
    assert len(food_expenses) == 2
    assert all(expense["category"] == "food" for expense in food_expenses)

    # Verify computing the sum for each category:
    food_sum = tracker.compute_category_sum("food")
    transport_sum = tracker.compute_category_sum("transport")
    assert food_sum == 30   # 20 + 10
    assert transport_sum == 30  # only one expense of 30

    # Ensure that filtering by an invalid category raises a ValueError.
    with pytest.raises(ValueError):
        tracker.filter_by_category("nonexistent")

    # Ensure that computing sum for an invalid category raises a ValueError.
    with pytest.raises(ValueError):
        tracker.compute_category_sum("nonexistent")