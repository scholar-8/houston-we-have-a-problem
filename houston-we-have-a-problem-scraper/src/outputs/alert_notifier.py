thonimport logging

class AlertNotifier:
    def send_alert(self, event):
        logging.warning(f"ALERT! {event['system_name']} has a {event['severity']} issue: {event['description']}")