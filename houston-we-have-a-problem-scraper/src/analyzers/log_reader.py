import logging
from pathlib import Path
from typing import Generator

logger = logging.getLogger("houston.log_reader")

class LogReader:
    """
    Reads log lines from a file. For this reference implementation
    we support reading existing files (historical logs).
    """

    def read_logs(self, path: Path) -> Generator[str, None, None]:
        if isinstance(path, str):
            path = Path(path)

        if not path.exists():
            logger.error("Log file does not exist: %s", path)
            raise FileNotFoundError(f"Log file not found: {path}")

        try:
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    yield line
        except Exception as exc:
            logger.exception("Failed to read log file %s: %s", path, exc)
            raise