import pytest
from src.alert_manager import (
    AlertManager,
)


class TestAlertManager:
    """Tests for the AlertManager class."""

    def test_alert_class_instantiation(self):
        """
        Test that an alert created using the AlertManager.Alert TypedDict class is correctly updated by the AlertManager.

        This test creates an alert instance using the defined AlertManager.Alert type with an initial value above
        the threshold, ensuring that is_alarm_triggered() sets 'alert_triggered' to True. Then, it updates the alert's value
        to below the threshold and verifies that the alert's trigger status is updated to False.
        """
        threshold = 10
        manager = AlertManager(threshold)
        alert = AlertManager.Alert(date="2023-07-01", value=15, alert_triggered=False)
        manager.add_alert(alert)
        manager.is_alarm_triggered()
        assert alert["alert_triggered"] is True
        alert["value"] = 5
        manager.is_alarm_triggered()
        assert alert["alert_triggered"] is False

    def test_repeated_is_alarm_triggered_consistency(self):
        """
        Test that multiple sequential calls to is_alarm_triggered consistently update
        and return the correct alarm status without side effects.

        The test first verifies that when the alert's value is below threshold, repeated
        calls return False and the alert's 'alert_triggered' field remains False. Then, it
        updates the alert's value to exceed the threshold and verifies that several calls
        consistently return True and update the 'alert_triggered' field accordingly.
        """
        manager = AlertManager(threshold=10)
        alert = {"date": "2023-01-10", "value": 5, "alert_triggered": False}
        manager.add_alert(alert)
        first_call = manager.is_alarm_triggered()
        second_call = manager.is_alarm_triggered()
        assert first_call is False
        assert second_call is False
        assert alert["alert_triggered"] is False
        alert["value"] = 15
        third_call = manager.is_alarm_triggered()
        fourth_call = manager.is_alarm_triggered()
        assert third_call is True
        assert fourth_call is True
        assert alert["alert_triggered"] is True

    def test_update_threshold_effect(self):
        """
        Test that modifying the AlertManager's threshold updates the alert's triggered status.

        This test creates an alert whose value is less than the initial threshold so that it is not triggered.
        Then, it lowers the threshold so that the alert becomes triggered, and further modifies the threshold
        to ensure that the alert's status updates correctly following any change to the threshold.
        """
        manager = AlertManager(threshold=20)
        alert = {"date": "2023-05-01", "value": 15, "alert_triggered": False}
        manager.add_alert(alert)
        assert manager.is_alarm_triggered() is False
        assert alert["alert_triggered"] is False
        manager.threshold = 10
        assert manager.is_alarm_triggered() is True
        assert alert["alert_triggered"] is True
        manager.threshold = 16
        assert manager.is_alarm_triggered() is False
        assert alert["alert_triggered"] is False

    def test_alert_missing_value_field(self):
        """
        Test that an alert missing the 'value' field raises a KeyError when updating alert_triggered.
        This ensures that the AlertManager correctly expects all required fields in an alert dictionary.
        """
        threshold = 10
        manager = AlertManager(threshold)
        alert = {"date": "2023-01-08", "alert_triggered": False}
        manager.add_alert(alert)
        with pytest.raises(KeyError):
            manager.is_alarm_triggered()

    def test_extra_fields_unchanged(self):
        """
        Test that additional fields in an alert dictionary remain unchanged after updating the alert_triggered field.
        This ensures that the update process only modifies 'alert_triggered' based on the 'value' and leaves extra keys intact.
        """
        threshold = 10
        manager = AlertManager(threshold)
        alert = {
            "date": "2023-04-02",
            "value": 12,
            "alert_triggered": False,
            "note": "important",
        }
        manager.add_alert(alert)
        manager.is_alarm_triggered()
        assert alert["alert_triggered"] is True
        assert alert["note"] == "important"
        alert["value"] = 8
        manager.is_alarm_triggered()
        assert alert["alert_triggered"] is False
        assert alert["note"] == "important"

    def test_initial_trigger_value_overridden(self):
        """
        Test that the initial value of the alert's 'alert_triggered' field is overridden by the update process.
        Even if an alert is added with a pre-set (and incorrect) 'alert_triggered' value, calling
        is_alarm_triggered() computes the correct status based solely on the alert's 'value' relative to the threshold.
        """
        threshold = 10
        manager = AlertManager(threshold)
        alert = {"date": "2023-04-01", "value": 5, "alert_triggered": True}
        manager.add_alert(alert)
        manager.is_alarm_triggered()
        assert alert["alert_triggered"] is False
        alert["value"] = 15
        manager.is_alarm_triggered()
        assert alert["alert_triggered"] is True

    def test_dynamic_alert_update_sequence(self):
        """
        Test dynamic updating of alert trigger statuses over a sequence of value changes.

        This test creates two alerts with values initially below and above the threshold.
        It then updates the alerts' 'value' fields in several steps. After each update,
        is_alarm_triggered is called to refresh the alert statuses, and assertions
        verify that the 'alert_triggered' fields are correctly updated based on the manager's threshold.
        """
        threshold = 10
        manager = AlertManager(threshold)
        alert_a = {"date": "2023-03-01", "value": 5, "alert_triggered": False}
        alert_b = {"date": "2023-03-02", "value": 20, "alert_triggered": False}
        manager.add_alert(alert_a)
        manager.add_alert(alert_b)
        manager.is_alarm_triggered()
        assert alert_a["alert_triggered"] is False
        assert alert_b["alert_triggered"] is True
        alert_a["value"] = 15
        manager.is_alarm_triggered()
        assert alert_a["alert_triggered"] is True
        assert alert_b["alert_triggered"] is True
        alert_b["value"] = 9
        manager.is_alarm_triggered()
        assert alert_a["alert_triggered"] is True
        assert alert_b["alert_triggered"] is False
        alert_a["value"] = 7
        alert_b["value"] = 7
        manager.is_alarm_triggered()
        assert alert_a["alert_triggered"] is False
        assert alert_b["alert_triggered"] is False
        alert_a["value"] = 20
        alert_b["value"] = 25
        manager.is_alarm_triggered()
        assert alert_a["alert_triggered"] is True
        assert alert_b["alert_triggered"] is True

    def test_multiple_alerts_update(self):
        """
        Test that multiple alerts are updated correctly when their values change.

        This test creates several alerts with initial values both below and above the threshold,
        verifies their initial trigger status, then updates their values and confirms that the
        trigger statuses are updated as expected.
        """
        threshold = 10
        manager = AlertManager(threshold)
        alert1 = {"date": "2023-02-01", "value": 8, "alert_triggered": False}
        alert2 = {"date": "2023-02-02", "value": 12, "alert_triggered": False}
        alert3 = {"date": "2023-02-03", "value": 10, "alert_triggered": False}
        manager.add_alert(alert1)
        manager.add_alert(alert2)
        manager.add_alert(alert3)
        assert manager.is_alarm_triggered() is True
        assert alert1["alert_triggered"] is False
        assert alert2["alert_triggered"] is True
        assert alert3["alert_triggered"] is False
        alert1["value"] = 11
        alert2["value"] = 9
        alert3["value"] = 15
        assert manager.is_alarm_triggered() is True
        assert alert1["alert_triggered"] is True
        assert alert2["alert_triggered"] is False
        assert alert3["alert_triggered"] is True

    def test_direct_alert_field_update(self):
        """
        Test that the alert dictionary's 'alert_triggered' field is correctly updated.

        This test verifies that:
        - When is_alarm_triggered is called, each alert's 'alert_triggered' value is updated
          based on whether alert["value"] > threshold.
        - If the alert's value is above the threshold it gets updated to True, and if the value
          is subsequently modified to be less than or equal to the threshold, its status is updated to False.
        """
        threshold = 10
        manager = AlertManager(threshold)
        alert = {"date": "2023-01-07", "value": 12, "alert_triggered": False}
        manager.add_alert(alert)
        assert alert["alert_triggered"] is False
        manager.is_alarm_triggered()
        assert alert["alert_triggered"] is True
        alert["value"] = 9
        manager.is_alarm_triggered()
        assert alert["alert_triggered"] is False

    def test_alert_value_equals_threshold_does_not_trigger_alarm(self):
        """
        Test that an alert with a value exactly equal to the threshold does not trigger the alarm.
        This test verifies that if an alert's value equals the threshold (and is not greater),
        the alarm is not triggered.
        """
        threshold = 10
        manager = AlertManager(threshold)
        alert = {"date": "2023-01-06", "value": 10, "alert_triggered": False}
        manager.add_alert(alert)
        assert manager.is_alarm_triggered() is False

    def test_alert_reset_status(self):
        """
        Test that updating an alert's value from above threshold to below threshold correctly resets its
        triggered status. An alert initially above threshold which triggers an alarm should no longer trigger
        after its value is updated.
        """
        threshold = 10
        manager = AlertManager(threshold)
        alert = {"date": "2023-01-05", "value": 20, "alert_triggered": False}
        manager.add_alert(alert)
        assert manager.is_alarm_triggered() is True
        alert["value"] = 5
        assert manager.is_alarm_triggered() is False

    def test_no_alerts(self):
        """
        Test that is_alarm_triggered returns False when no alerts have been added.
        This checks that the AlertManager handles an empty alert list gracefully.
        """
        manager = AlertManager(threshold=10)
        assert manager.is_alarm_triggered() is False

    def test_alert_triggered(self):
        """
        Test that is_alarm_triggered returns True when at least one alert's value
        exceeds the threshold.
        """
        threshold = 10
        manager = AlertManager(threshold)
        alert1 = {"date": "2023-01-01", "value": 5, "alert_triggered": False}
        alert2 = {"date": "2023-01-02", "value": 15, "alert_triggered": False}
        manager.add_alert(alert1)
        manager.add_alert(alert2)
        assert manager.is_alarm_triggered() is True

    def test_no_alert_triggered(self):
        """
        Test that is_alarm_triggered returns False when all alerts' values
        are at or below the threshold.
        """
        threshold = 20
        manager = AlertManager(threshold)
        alert = {"date": "2023-01-03", "value": 15, "alert_triggered": False}
        manager.add_alert(alert)
        assert manager.is_alarm_triggered() is False

    def test_alert_updates_after_modification(self):
        """
        Test that updating an alert's value after it has been added to the AlertManager
        correctly updates its trigger status upon calling is_alarm_triggered.
        """
        threshold = 10
        manager = AlertManager(threshold)
        alert = {"date": "2023-01-04", "value": 5, "alert_triggered": False}
        manager.add_alert(alert)
        assert manager.is_alarm_triggered() is False
        alert["value"] = 20
        assert manager.is_alarm_triggered() is True
