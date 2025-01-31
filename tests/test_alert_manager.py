import pytest

from alert_manager import AlertManager

class TestAlertManager:
    def test_is_alarm_triggered_no_alerts(self):
        """
        Test that is_alarm_triggered returns False when no alerts have been added.
        This tests the scenario where the AlertManager is initialized but no alerts are present.
        """
        alert_manager = AlertManager(threshold=100)
        assert not alert_manager.is_alarm_triggered()