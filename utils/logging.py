import logging
import re
from collections.abc import Mapping
from typing import Any


TELEGRAM_BOT_URL_RE = re.compile(r"/bot[0-9]+:[A-Za-z0-9_-]+")


class SensitiveDataFilter(logging.Filter):
    def __init__(self, secrets: list[str] | None = None) -> None:
        super().__init__()
        self.secrets = [secret for secret in (secrets or []) if secret]

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self._redact(record.msg)
        if record.args:
            record.args = self._redact(record.args)
        return True

    def _redact(self, value: Any) -> Any:
        if isinstance(value, str):
            return redact_sensitive_text(value, self.secrets)
        if isinstance(value, tuple):
            return tuple(self._redact(item) for item in value)
        if isinstance(value, list):
            return [self._redact(item) for item in value]
        if isinstance(value, Mapping):
            return {key: self._redact(item) for key, item in value.items()}
        return value


def redact_sensitive_text(text: str, secrets: list[str] | None = None) -> str:
    redacted = TELEGRAM_BOT_URL_RE.sub("/bot<redacted>", text)
    for secret in secrets or []:
        redacted = redacted.replace(secret, "<redacted>")
    return redacted


def configure_logging(telegram_bot_token: str) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    sensitive_filter = SensitiveDataFilter([telegram_bot_token])
    for handler in logging.getLogger().handlers:
        handler.addFilter(sensitive_filter)

    logging.getLogger("httpx").setLevel(logging.WARNING)
