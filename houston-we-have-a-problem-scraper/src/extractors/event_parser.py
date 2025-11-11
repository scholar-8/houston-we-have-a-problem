thonclass EventParser:
    def parse_event(self, event):
        parsed_event = {
            'event_time': event['event_time'],
            'system_name': event['system_name'],
            'error_code': event['error_code'],
            'severity': event['severity'],
            'description': event['description']
        }
        return parsed_event