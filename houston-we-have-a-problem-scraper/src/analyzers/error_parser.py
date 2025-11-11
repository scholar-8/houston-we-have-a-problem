import json
import logging
from dataclasses import dataclass
from typing import Iterable, List, Optional, Dict, Tuple

from utils.time_helper import parse_timestamp

logger = logging.getLogger("houston.error_parser")

@dataclass
class ErrorRecord:
    errorMessage: str
    errorType: str
    timestamp: str
    severity: str
    filePath: str
    lineNumber: int
    stackTrace: str
    environment: str
    status: str

    def dedup_key(self) -> Tuple[str, str, int, str]:
        return (self.errorMessage, self.filePath, self.lineNumber, self.environment)

class ErrorParser:
    """
    Parses raw log lines into structured ErrorRecord objects.
    Expects JSON-per-line by default but attempts to handle simple
    key=value pairs as a fallback.
    """

    def parse(self, lines: Iterable[str]) -> List[ErrorRecord]:
        records: List[ErrorRecord] = []
        for idx, line in enumerate(lines, start=1):
            line = line.strip()
            if not line:
                continue

            record = None
            if line.lstrip().startswith("{"):
                record = self._parse_json_line(line, idx)
            else:
                record = self._parse_key_value_line(line, idx)

            if record:
                records.append(record)

        records = self._normalize_and_sort(records)
        records = self._deduplicate(records)
        return records

    def _parse_json_line(self, line: str, line_no: int) -> Optional[ErrorRecord]:
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            logger.warning("Line %d is invalid JSON; skipping", line_no)
            return None

        return self._build_record(data, line_no)

    def _parse_key_value_line(self, line: str, line_no: int) -> Optional[ErrorRecord]:
        # Simple "key=value; key2=value2" style parser as a fallback
        parts = [p.strip() for p in line.split(";") if p.strip()]
        data: Dict[str, str] = {}
        for part in parts:
            if "=" in part:
                k, v = part.split("=", 1)
                data[k.strip()] = v.strip()

        if not data:
            logger.warning("Line %d has unsupported format; skipping", line_no)
            return None

        return self._build_record(data, line_no)

    def _build_record(self, data: Dict[str, object], line_no: int) -> ErrorRecord:
        # Provide sensible defaults; for missing fields, try to infer or fallback
        error_message = str(data.get("errorMessage") or data.get("message") or "Unknown error")
        error_type = str(data.get("errorType") or data.get("type") or "UnknownType")
        timestamp_raw = str(data.get("timestamp") or data.get("time") or "")
        timestamp = parse_timestamp(timestamp_raw).isoformat()

        severity = str(data.get("severity") or "medium").lower()
        if severity not in {"low", "medium", "high"}:
            logger.debug("Line %d has unknown severity '%s'; defaulting to medium", line_no, severity)
            severity = "medium"

        file_path = str(data.get("filePath") or data.get("file") or "unknown.py")
        try:
            line_number = int(data.get("lineNumber") or data.get("line") or 0)
        except (ValueError, TypeError):
            line_number = 0

        stack_trace = str(data.get("stackTrace") or data.get("stack") or "")
        environment = str(data.get("environment") or data.get("env") or "unknown").lower()
        status = str(data.get("status") or "new").lower()

        record = ErrorRecord(
            errorMessage=error_message,
            errorType=error_type,
            timestamp=timestamp,
            severity=severity,
            filePath=file_path,
            lineNumber=line_number,
            stackTrace=stack_trace,
            environment=environment,
            status=status,
        )

        return record

    def _normalize_and_sort(self, records: List[ErrorRecord]) -> List[ErrorRecord]:
        # Sort by timestamp ascending
        try:
            records.sort(key=lambda r: r.timestamp)
        except Exception:
            logger.debug("Failed to sort records by timestamp; leaving as-is")
        return records

    def _deduplicate(self, records: List[ErrorRecord]) -> List[ErrorRecord]:
        seen: Dict[Tuple[str, str, int, str], ErrorRecord] = {}
        for record in records:
            key = record.dedup_key()
            # Keep the latest occurrence based on timestamp string
            existing = seen.get(key)
            if existing is None or record.timestamp > existing.timestamp:
                seen[key] = record
        return list(seen.values())