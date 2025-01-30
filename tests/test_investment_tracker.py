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
