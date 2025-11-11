thonimport json
import logging
from extractors.event_parser import EventParser
from outputs.alert_notifier import AlertNotifier

logging.basicConfig(level=logging.INFO)

def main():
    logging.info("Houston, We Have a Problem! scraper is starting...")

    # Load sample data
    with open('data/sample_events.json', 'r') as f:
        events = json.load(f)

    # Initialize parser and notifier
    parser = EventParser()
    notifier = AlertNotifier()

    for event in events:
        logging.info(f"Processing event: {event['event_time']} - {event['system_name']}")
        parsed_event = parser.parse_event(event)
        if parsed_event['severity'] == 'critical':
            notifier.send_alert(parsed_event)

if __name__ == "__main__":
    main()