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
