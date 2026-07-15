"""요청 단위 구조화 로깅 미들웨어.

모든 요청에 대해 handler(라우트 경로)/method/status/fail_code/duration_ms를
JSON 로그 한 줄로 남긴다. fail_code는 HTTPException(detail={"code": ...})
컨벤션(SkillCanvas_컨벤션.md)을 그대로 읽어서 뽑는다 — 4xx/5xx가 아니면 None.
"""

import json
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("skillcanvas.access")


def _parse_fail_code(body: bytes) -> str | None:
    """HTTPException(detail={"code": ...})로 만들어진 에러 응답 바디에서 code를 꺼낸다."""
    if not body:
        return None
    try:
        parsed = json.loads(body)
    except (json.JSONDecodeError, TypeError, UnicodeDecodeError):
        return None
    detail = parsed.get("detail") if isinstance(parsed, dict) else None
    return detail.get("code") if isinstance(detail, dict) else None


class AccessLogMiddleware(BaseHTTPMiddleware):
    # Prometheus가 15초마다 스크랩하는 엔드포인트 — 로그에는 노이즈만 됨
    _SKIP_PATHS = {"/metrics"}
    # 매칭 안 된 경로(오타·존재하지 않는 리소스 등)를 그대로 라벨로 쓰면 Loki 카디널리티가
    # 무한정 늘어나므로 하나의 값으로 뭉갠다.
    _UNMATCHED_HANDLER = "unmatched"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in self._SKIP_PATHS:
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        route = request.scope.get("route")
        handler = getattr(route, "path", None) or self._UNMATCHED_HANDLER

        fail_code = None
        if response.status_code >= 400:
            # BaseHTTPMiddleware가 넘기는 response는 body_iterator만 갖고 있고 원본
            # JSONResponse가 아니므로(.body 없음), 직접 소비한 뒤 같은 바이트로 재구성해서 돌려준다.
            body = b"".join([chunk async for chunk in response.body_iterator])
            fail_code = _parse_fail_code(body)
            rebuilt = Response(
                content=body, status_code=response.status_code, background=response.background
            )
            rebuilt.raw_headers = response.raw_headers  # 중복 헤더(Set-Cookie 등) 보존
            response = rebuilt

        logger.info(
            "request",
            extra={
                "handler": handler,
                "method": request.method,
                "status": response.status_code,
                "fail_code": fail_code,
                "duration_ms": duration_ms,
            },
        )
        return response
