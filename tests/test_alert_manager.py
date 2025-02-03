import pytest

from alert_manager import AlertManager

class TestAlertManager:
    """Test suite for the AlertManager class."""

    def test_value_equal_threshold_does_not_trigger(self):
        """
        Test that an alert with a value equal to the threshold does not trigger an alarm.
        This tests the condition where alert["value"] == threshold, ensuring the alert remains false.
        """
        threshold = 10
        manager = AlertManager(threshold)

        # Create an alert with value equal to the threshold; it should not trigger the alarm.
        alert = {"date": "2023-10-01", "value": 10, "alert_triggered": False}
        manager.add_alert(alert)

        # Call to update alarms and check the aggregate result.
        assert manager.is_alarm_triggered() is False
        # Also verify that the individual alert's triggered status remains False.
        assert alert["alert_triggered"] is False