"""REST API 도구(sweettracker) 파라미터 자동 추출 테스트.

실제 HTTP는 안 친다 — 순수 추출 함수(_extract_sweettracker)와, 파라미터를
못 채웠을 때 HTTP 이전에 반환하는 에러 경로만 검증한다.
"""

from app.core import api_tools


def test_extract_from_mail():
    text = "제목: [배송문의]\n- 송장번호: 511951252170\n- 택배사: CJ대한통운"
    out = api_tools._extract_sweettracker(text)
    assert out["t_invoice"] == "511951252170"
    assert out["t_code"] == "04"


def test_extract_courier_variants():
    assert api_tools._extract_sweettracker("우체국택배 1234567890")["t_code"] == "01"
    assert api_tools._extract_sweettracker("한진택배로 보냈어요 12345678901")["t_code"] == "05"
    assert api_tools._extract_sweettracker("롯데택배 1234567890")["t_code"] == "08"


def test_extract_ignores_order_number():
    """주문번호(짧거나 대시 포함)는 잡지 않고 송장번호를 잡는다."""
    text = "주문번호: 20260712-0847\n송장번호: 511951252170\n택배사: CJ대한통운"
    assert api_tools._extract_sweettracker(text)["t_invoice"] == "511951252170"


def test_extract_none_when_no_tracking():
    out = api_tools._extract_sweettracker("안녕하세요, 배송 언제 오나요?")
    assert "t_invoice" not in out
    assert "t_code" not in out


def test_call_api_autofill_miss_errors_before_http(monkeypatch):
    """키는 있고 detail 비었는데 메일에도 송장정보가 없으면, HTTP 치기 전에 '못 찾음' 에러."""
    monkeypatch.setattr(api_tools.db, "get_credential", lambda k: "fake-key")
    r = api_tools.call_api("sweettracker", "", history=[{"result": "송장번호 없는 메일"}])
    assert "error" in r
    assert "못 찾" in r["error"]


def test_call_api_detail_takes_precedence(monkeypatch):
    """detail에 명시하면 그게 우선 — history 추출값으로 덮어쓰지 않는다."""
    captured = {}

    def fake_urlopen(url, timeout=15):
        captured["url"] = url
        raise TimeoutError("stop before real HTTP")

    monkeypatch.setattr(api_tools.db, "get_credential", lambda k: "fake-key")
    monkeypatch.setattr(api_tools.urllib.request, "urlopen", fake_urlopen)
    api_tools.call_api(
        "sweettracker",
        "t_code=99&t_invoice=999",
        history=[{"result": "송장번호: 511951252170 택배사: CJ대한통운"}],
    )
    # detail의 99/999가 쿼리에 들어가야 함(메일의 04/511951252170 아님)
    assert "t_code=99" in captured["url"]
    assert "t_invoice=999" in captured["url"]
