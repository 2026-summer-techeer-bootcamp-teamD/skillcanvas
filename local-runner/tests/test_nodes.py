"""분기 노드의 순수 헬퍼 테스트 (Claude 미호출).

_parse_route: 모델 출력 문자열에서 라벨 하나를 안전하게 뽑는지.
"""

from app.engine.nodes import _parse_route

ROUTES = ["문의", "제안"]


def test_parse_exact_match():
    assert _parse_route("문의", ROUTES) == "문의"
    assert _parse_route("제안", ROUTES) == "제안"


def test_parse_with_whitespace():
    assert _parse_route("  제안  ", ROUTES) == "제안"


def test_parse_contained_in_sentence():
    """모델이 문장으로 답해도 라벨이 들어있으면 잡는다."""
    assert _parse_route("이 메일은 제안으로 분류됩니다", ROUTES) == "제안"


def test_parse_fallback_to_first():
    """어느 라벨도 못 찾으면 첫 라벨로 폴백(런이 안 죽게)."""
    assert _parse_route("모르겠음", ROUTES) == "문의"
    assert _parse_route("", ROUTES) == "문의"


def test_parse_first_match_wins_order():
    """여러 라벨이 다 들어있으면 routes 순서상 먼저 일치하는 것."""
    # "문의"가 routes[0]이라 정확일치 우선; 여기선 포함 검사에서 문의가 먼저
    assert _parse_route("문의 아니면 제안", ROUTES) == "문의"
