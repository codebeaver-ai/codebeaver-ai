import pytest

from alert_manager import AlertManager

def test_no_alerts_added():
    """
    Test that when no alerts are added, is_alarm_triggered returns False.
    """
    manager = AlertManager(threshold=100)
    assert not manager.is_alarm_triggered()