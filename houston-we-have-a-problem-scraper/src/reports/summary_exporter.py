import csv
import json
import logging
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Any

from analyzers.error_parser import ErrorRecord

logger = logging.getLogger("houston.summary_exporter")

class SummaryExporter:
    """
    Builds aggregated error summaries and exports them to JSON and CSV.
    """

    def build_summary(self, records: List[ErrorRecord]) -> Dict[str, Any]:
        summary: Dict[str, Any] = {}
        summary["totalErrors"] = len(records)

        by_severity: Counter = Counter()
        by_type: Counter = Counter()
        by_environment: Counter = Counter()
        status_counts: Counter = Counter()

        error_key_counts: Counter = Counter()
        error_key_meta: Dict[str, Dict[str, Any]] = {}

        for r in records:
            by_severity[r.severity] += 1
            by_type[r.errorType] += 1
            by_environment[r.environment] += 1
            status_counts[r.status] += 1

            key = f"{r.errorMessage}|{r.filePath}|{r.lineNumber}|{r.environment}"
            error_key_counts[key] += 1
            if key not in error_key_meta:
                error_key_meta[key] = {
                    "errorMessage": r.errorMessage,
                    "filePath": r.filePath,
                    "lineNumber": r.lineNumber,
                    "environment": r.environment,
                    "severity": r.severity,
                    "errorType": r.errorType,
                }

        summary["bySeverity"] = dict(by_severity)
        summary["byType"] = dict(by_type)
        summary["byEnvironment"] = dict(by_environment)
        summary["statusCounts"] = dict(status_counts)

        # Top recurring errors
        top_errors = []
        for key, count in error_key_counts.most_common(5):
            meta = error_key_meta[key]
            item = {
                "errorMessage": meta["errorMessage"],
                "filePath": meta["filePath"],
                "lineNumber": meta["lineNumber"],
                "environment": meta["environment"],
                "severity": meta["severity"],
                "errorType": meta["errorType"],
                "occurrences": count,
            }
            top_errors.append(item)
        summary["topRecurringErrors"] = top_errors

        # Group by filePath for quick drill-down
        by_file: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for r in records:
            by_file[r.filePath].append(
                {
                    "errorMessage": r.errorMessage,
                    "errorType": r.errorType,
                    "timestamp": r.timestamp,
                    "severity": r.severity,
                    "lineNumber": r.lineNumber,
                    "environment": r.environment,
                    "status": r.status,
                }
            )
        summary["byFile"] = by_file

        return summary

    def to_json(self, summary: Dict[str, Any], path: Path) -> None:
        if isinstance(path, str):
            path = Path(path)

        try:
            with path.open("w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            logger.exception("Failed to write summary JSON to %s: %s", path, exc)
            raise

    def to_csv(self, records: List[ErrorRecord], path: Path) -> None:
        if isinstance(path, str):
            path = Path(path)

        fieldnames = [
            "errorMessage",
            "errorType",
            "timestamp",
            "severity",
            "filePath",
            "lineNumber",
            "stackTrace",
            "environment",
            "status",
        ]

        try:
            with path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for r in records:
                    writer.writerow(
                        {
                            "errorMessage": r.errorMessage,
                            "errorType": r.errorType,
                            "timestamp": r.timestamp,
                            "severity": r.severity,
                            "filePath": r.filePath,
                            "lineNumber": r.lineNumber,
                            "stackTrace": r.stackTrace,
                            "environment": r.environment,
                            "status": r.status,
                        }
                    )
        except Exception as exc:
            logger.exception("Failed to write detailed CSV to %s: %s", path, exc)
            raise