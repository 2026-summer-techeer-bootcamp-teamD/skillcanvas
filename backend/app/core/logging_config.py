"""구조화(JSON) 로깅 설정 — Loki+Promtail이 한 줄씩 파싱할 수 있는 형태로 로그를 남긴다.

configure_logging()을 main.py에서 앱 시작 시 한 번 호출하면, 이후
logging.getLogger(...).info(..., extra={...}) 로 남긴 모든 로그가 JSON 한 줄로 stdout에 찍힌다.
extra로 넘긴 필드(handler/status/fail_code 등)가 그대로 JSON 최상위 키로 들어간다.
"""

import json
import logging

# LogRecord 기본 속성 + getMessage()로 이미 반영되는 것들은 JSON에서 제외
_RESERVED_KEYS = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # extra={...}로 넘긴 구조화 필드(handler/method/status/fail_code/duration_ms 등)
        for key, value in record.__dict__.items():
            if key not in _RESERVED_KEYS:
                payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    """루트 로거의 핸들러를 JSON 포맷터가 붙은 StreamHandler 하나로 교체."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
