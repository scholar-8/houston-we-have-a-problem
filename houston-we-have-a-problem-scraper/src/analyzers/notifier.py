import logging
from typing import Iterable, List, Optional

from analyzers.error_parser import ErrorRecord

logger = logging.getLogger("houston.notifier")

class Notifier:
    """
    Simple notifier that can be extended to integrate with real
    alerting systems like Slack, email, or webhooks.

    For this implementation, alerts are logged to the console,
    and real integrations can be wired in where noted.
    """

    def __init__(
        self,
        enable_console: bool = True,
        slack_webhook_url: Optional[str] = None,
        email_recipients: Optional[List[str]] = None,
    ) -> None:
        self.enable_console = enable_console
        self.slack_webhook_url = slack_webhook_url
        self.email_recipients = email_recipients or []

    def notify(self, errors: Iterable[ErrorRecord]) -> None:
        errors = list(errors)
        if not errors:
            logger.debug("No errors to notify")
            return

        if self.enable_console:
            self._notify_console(errors)

        # Extension points for real-world integrations:
        # if self.slack_webhook_url:
        #     self._notify_slack(errors)
        # if self.email_recipients:
        #     self._notify_email(errors)

    def _notify_console(self, errors: List[ErrorRecord]) -> None:
        logger.warning("---- Houston, we have a problem! ----")
        logger.warning("Critical error batch size: %d", len(errors))
        for err in errors:
            logger.warning(
                "[%s] %s (%s:%d, env=%s, status=%s)",
                err.severity.upper(),
                err.errorMessage,
                err.filePath,
                err.lineNumber,
                err.environment,
                err.status,
            )
        logger.warning("---- End of critical error batch ----")