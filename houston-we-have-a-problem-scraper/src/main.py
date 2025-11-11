import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from analyzers.log_reader import LogReader
from analyzers.error_parser import ErrorParser, ErrorRecord
from analyzers.notifier import Notifier
from reports.summary_exporter import SummaryExporter
from utils.time_helper import now_utc_iso

def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

def load_settings(project_root: Path) -> Dict[str, Any]:
    settings_path = project_root / "src" / "config" / "settings.json"
    if not settings_path.exists():
        raise FileNotFoundError(f"Settings file not found at {settings_path}")

    with settings_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def detect_new_critical_errors(
    records: List[ErrorRecord], severity_threshold: str
) -> List[ErrorRecord]:
    severity_order = {"low": 1, "medium": 2, "high": 3}
    threshold_value = severity_order.get(severity_threshold.lower(), 3)

    new_critical = []
    for record in records:
        sev_value = severity_order.get(record.severity.lower(), 0)
        if sev_value >= threshold_value and record.status.lower() in {"new", "recurring"}:
            new_critical.append(record)

    return new_critical

def main() -> None:
    setup_logging()
    logger = logging.getLogger("houston.main")

    project_root = Path(__file__).resolve().parents[1]
    logger.info("Project root resolved to %s", project_root)

    try:
        settings = load_settings(project_root)
    except Exception as exc:
        logger.exception("Failed to load settings: %s", exc)
        raise

    log_file = project_root / settings.get("log_file", "data/logs/system_errors.log")
    output_cfg = settings.get("output", {})
    summary_json_path = project_root / output_cfg.get(
        "summary_json", "data/samples/sample_output.json"
    )
    summary_csv_path = project_root / output_cfg.get(
        "summary_csv", "data/samples/sample_output.csv"
    )

    logger.info("Reading logs from %s", log_file)
    reader = LogReader()
    parser = ErrorParser()
    exporter = SummaryExporter()
    notifier = Notifier(
        enable_console=settings.get("notifier", {}).get("enable_console", True),
        slack_webhook_url=settings.get("notifier", {}).get("slack_webhook_url"),
        email_recipients=settings.get("notifier", {}).get("email_recipients", []),
    )

    try:
        raw_lines = list(reader.read_logs(log_file))
    except Exception as exc:
        logger.exception("Failed to read logs: %s", exc)
        raise

    logger.info("Parsing %d log lines", len(raw_lines))
    records = parser.parse(raw_lines)
    logger.info("Parsed %d error records", len(records))

    logger.info("Building summary")
    summary = exporter.build_summary(records)
    summary["generatedAt"] = now_utc_iso()

    summary_json_path.parent.mkdir(parents=True, exist_ok=True)
    summary_csv_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Exporting summary JSON to %s", summary_json_path)
    exporter.to_json(summary, summary_json_path)

    logger.info("Exporting detailed CSV to %s", summary_csv_path)
    exporter.to_csv(records, summary_csv_path)

    alert_cfg = settings.get("alert_threshold", {})
    severity_threshold = alert_cfg.get("severity", "high")
    min_new_errors = int(alert_cfg.get("min_new_errors", 1))

    logger.info(
        "Checking for new critical errors (severity >= %s, min count = %d)",
        severity_threshold,
        min_new_errors,
    )
    new_critical = detect_new_critical_errors(records, severity_threshold)

    if len(new_critical) >= min_new_errors:
        logger.info(
            "Detected %d new critical errors meeting alert threshold", len(new_critical)
        )
        notifier.notify(new_critical)
    else:
        logger.info("No new critical errors meeting alert threshold")

    logger.info("Houston run completed successfully")

if __name__ == "__main__":
    main()