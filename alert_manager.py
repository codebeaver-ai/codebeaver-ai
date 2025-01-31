from typing import TypedDict


class AlertManager:

    class Alert(TypedDict):
        date: str
        value: int
        alert_triggered: bool

    def __init__(self, threshold: int):
        self.threshold = threshold
        self.alerts = []
        self.value = 0

    def add_alert(self, alert: Alert):
        """
        Add an alert to the alert manager.
        """
        self.alerts.append(alert)

    def is_alarm_triggered(self) -> bool:
        """
        Check if any alert has been triggered.
        """
        self._update_all_alarms()
        return any(alert["alert_triggered"] for alert in self.alerts)

    def _update_all_alarms(self):
        """
        Update all alerts.
        """
        for alert in self.alerts:
            alert["alert_triggered"] = alert["value"] > self.threshold
