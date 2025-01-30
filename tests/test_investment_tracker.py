from investment_tracker import InvestmentTracker

class TestInvestment:
    def test_record_transaction(self):
        """
        Test the record_transaction method of InvestmentTracker.

        This test checks:
        1. Valid transaction recording
        2. Invalid amount (negative number)
        3. Invalid category
        """
        tracker = InvestmentTracker()

        # Test valid transaction
        assert tracker.record_transaction(50.0, "food", "Groceries") == True

        # Test invalid amount (negative number)
        try:
            tracker.record_transaction(-10.0, "food", "Invalid amount")
            assert False, "Should raise ValueError for negative amount"
        except ValueError:
            pass

        # Test invalid category
        try:
            tracker.record_transaction(30.0, "invalid_category", "Invalid category")
            assert False, "Should raise ValueError for invalid category"
        except ValueError:
            pass

    def test_calculate_overall_spending(self):
        """
        Test the calculate_overall_spending method of InvestmentTracker.

        This test checks:
        1. The method correctly calculates the sum of all recorded transactions.
        2. The method returns 0 when no transactions are recorded.
        """
        tracker = InvestmentTracker()

        # Test with no transactions
        assert tracker.calculate_overall_spending() == 0

        # Add some transactions
        tracker.record_transaction(50.0, "food", "Groceries")
        tracker.record_transaction(30.0, "transport", "Bus fare")
        tracker.record_transaction(100.0, "utilities", "Electricity bill")

        # Test the total spending
        assert tracker.calculate_overall_spending() == 180.0