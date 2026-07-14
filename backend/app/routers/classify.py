"""유형 판단 API. (API 명세서 3-4)

자연어 요청 → 스킬/워크플로우 중 어디에 가까운지 판단.
Claude는 점수만 매기고, 최종 판정(closer_to)은 백엔드가 계산한다.
원칙: 틀린 추천보다 중립(neutral).
"""

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user
from app.core.llm import ask_claude_json
from app.models.user import User
from app.schemas.classify import ClassifyRequest, ClassifyResponse

router = APIRouter(prefix="/classify", tags=["유형 판단"])

# 판정 튜닝 손잡이 — 오추천 잦으면 올린다 (명세 3-4)
MIN_CONFIDENCE = 60  # 이긴 쪽 점수가 이보다 낮으면 neutral
MIN_MARGIN = 20  # 두 점수 차가 이보다 작으면 neutral

SYSTEM = (
    "너는 자연어 요청이 '스킬'에 가까운지 '워크플로우'에 가까운지 판단한다.\n"
    "워크플로우에 가까움: 여러 단계 순서 흐름 · 자동/스케줄 트리거('매일', '~오면') · "
    "사람 승인 지점 · 외부 도구 여러 개 · 조건 분기/반복\n"
    "스킬에 가까움: 단일 작업/능력 · 단발성 · 도구 없거나 하나 · 흐름 없음\n"
    "각각 0~100 점수를 독립적으로 매긴다(합이 100일 필요 없음).\n"
    "반드시 JSON만 답한다: "
    '{"skill": 0~100, "workflow": 0~100, "reason": "한 줄 근거"}'
)


@router.post("", response_model=ClassifyResponse, summary="유형 판단 (스킬 vs 오토플로우)")
def classify(
    payload: ClassifyRequest,
    user: User = Depends(get_current_user),
):
    data = ask_claude_json(SYSTEM, payload.text, fail_code="CLASSIFY_FAILED")

    # Claude 응답 방어 — 점수가 정수가 아니면 파싱 실패로 간주 (422)
    skill = data.get("skill")
    workflow = data.get("workflow")
    if not isinstance(skill, int) or not isinstance(workflow, int):
        raise HTTPException(
            422, {"code": "CLASSIFY_FAILED", "message": "AI 응답을 해석하지 못했습니다"}
        )
    skill = max(0, min(100, skill))
    workflow = max(0, min(100, workflow))

    # 최종 판정은 백엔드가 계산 — 애매하면 neutral (틀린 추천보다 중립)
    winner = "workflow" if workflow > skill else "skill"
    win_score = max(skill, workflow)
    margin = abs(skill - workflow)
    closer_to = "neutral" if win_score < MIN_CONFIDENCE or margin < MIN_MARGIN else winner

    reason = data.get("reason")
    return {
        "closer_to": closer_to,
        "confidence": win_score,
        "scores": {"skill": skill, "workflow": workflow},
        "reason": reason if isinstance(reason, str) else None,
    }
