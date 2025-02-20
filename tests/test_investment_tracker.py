import unittest

from investment_tracker import InvestmentTracker


class TestInvestmentTracker(unittest.TestCase):
    def test_record_transaction(self):
        raise Exception("Test not implemented")

    def test_register_new_category(self):
        investment_tracker = InvestmentTracker()
        self.assertEqual(investment_tracker.register_new_category("Food"), True)

    def test_register_new_category_empty_string(self):
        investment_tracker = InvestmentTracker()
        self.assertEqual(investment_tracker.register_new_category(""), False)
