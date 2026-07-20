"""분기 노드의 순수 헬퍼 테스트 (Claude 미호출).

_parse_route: 모델 출력 문자열에서 라벨 하나를 안전하게 뽑는지.
_needs_search: agent 노드가 웹검색을 켤지 label/detail로 판단하는지.
"""

from app.engine.nodes import _needs_search, _parse_route

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


# ── _needs_search: 검색 켤지 판단 (기본 꺼, 키워드 있을 때만 켬) ──


def test_needs_search_off_by_default():
    """답변·요약·판단 노드는 검색 안 켬 (상시 빠름)."""
    assert _needs_search("고객 응대 초안", "답장 작성") is False
    assert _needs_search("제안 요약", "summarize") is False
    assert _needs_search("긴급도 판단", "") is False


def test_needs_search_on_for_search_keywords():
    """label/detail에 검색·뉴스·조사 등이 있으면 켬."""
    assert _needs_search("뉴스 요약", "") is True
    assert _needs_search("배송 조회", "최신 정보 검색") is True
    assert _needs_search("경쟁사 조사", "") is True
    assert _needs_search("daily news", "") is True


def test_needs_search_case_insensitive():
    assert _needs_search("Latest NEWS", "") is True
