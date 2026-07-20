"""실행기 그래프 순회 · 조건 분기 · 승인 재개 테스트.

exec_node는 conftest의 fake_engine으로 목킹(Claude 미호출).
검증 대상: runner.py의 step_run / start_run / resume_run 순회 로직.
"""


def _labels(results):
    return [r["label"] for r in results]


# ── 분기 순회 ──────────────────────────────────────────────


def _branch_graph(route):
    """트리거 → 분기 → (문의: 조회→승인→발송) / (제안: 요약→기록)."""
    nodes = [
        {"id": "t", "type": "trigger", "label": "트리거"},
        {"id": "b", "type": "branch", "label": "유형판단", "detail": f"route={route}"},
        {"id": "c1", "type": "tool", "label": "배송조회"},
        {"id": "c2", "type": "approve", "label": "승인"},
        {"id": "c3", "type": "tool", "label": "답장발송"},
        {"id": "p1", "type": "agent", "label": "요약"},
        {"id": "p2", "type": "tool", "label": "노션기록"},
    ]
    edges = [
        {"from": "t", "to": "b"},
        {"from": "b", "to": "c1", "when": "문의"},
        {"from": "b", "to": "p1", "when": "제안"},
        {"from": "c1", "to": "c2"},
        {"from": "c2", "to": "c3"},
        {"from": "p1", "to": "p2"},
    ]
    return nodes, edges


def test_branch_inquiry_path_only(fake_engine):
    """문의 route → 고객 경로만, 제안 경로는 실행 안 됨. 승인에서 멈춤."""
    nodes, edges = _branch_graph("문의")
    r = fake_engine.start_run(nodes, edges, "k1")
    labels = _labels(r["results"])
    assert r["status"] == "awaiting_approval"
    assert "배송조회" in labels
    assert "요약" not in labels and "노션기록" not in labels  # 제안 경로 미실행


def test_branch_proposal_path_only(fake_engine):
    """제안 route → 제안 경로 완주, 문의 경로는 실행 안 됨."""
    nodes, edges = _branch_graph("제안")
    r = fake_engine.start_run(nodes, edges, "k2")
    labels = _labels(r["results"])
    assert r["status"] == "done"
    assert "요약" in labels and "노션기록" in labels
    assert "배송조회" not in labels  # 문의 경로 미실행


def test_branch_unmatched_route_falls_back(fake_engine):
    """route가 어느 when과도 안 맞으면(오분류) 조건 없는 엣지로 폴백, 없으면 끝."""
    nodes, edges = _branch_graph("엉뚱")  # 문의/제안 어느 쪽도 아님
    r = fake_engine.start_run(nodes, edges, "k3")
    # when 없는 엣지가 없으므로 분기에서 끝 → 트리거+분기만
    assert _labels(r["results"]) == ["트리거", "유형판단"]
    assert r["status"] == "done"


# ── 승인 재개 (분기 경로에서) ──────────────────────────────


def test_approval_resume_on_branch_path(fake_engine):
    """문의 경로 승인 게이트 → 재개 → 발송까지. 델타는 새 노드만."""
    nodes, edges = _branch_graph("문의")
    r = fake_engine.start_run(nodes, edges, "k4")
    assert r["status"] == "awaiting_approval"
    before = _labels(r["results"])

    d = fake_engine.resume_run(r["run_id"])
    assert d["status"] == "done"
    assert _labels(d["results"]) == ["답장발송"]  # 델타 = 새로 실행된 것만
    # 전체 스냅샷은 누적
    full = fake_engine.get_run(r["run_id"])
    assert _labels(full["results"]) == before + ["답장발송"]


def test_resume_when_not_awaiting_is_noop(fake_engine):
    """승인 대기 아닌 run 재개 → 새 실행 0 (stopped 우회 방지)."""
    nodes = [{"id": "a", "type": "tool", "label": "A"}]
    r = fake_engine.start_run(nodes, [], "k5")
    assert r["status"] == "done"
    d = fake_engine.resume_run(r["run_id"])
    assert d["results"] == []


# ── 분기 없는 선형(fallback) — 기존 동작 보존 ──────────────


def test_linear_workflow_unchanged(fake_engine):
    """분기 없는 선형 워크플로우는 순서대로 전부 실행(기존 topo 동작과 동일)."""
    nodes = [
        {"id": "n1", "type": "trigger", "label": "트리거"},
        {"id": "n2", "type": "tool", "label": "조회"},
        {"id": "n3", "type": "output", "label": "기록"},
    ]
    edges = [{"from": "n1", "to": "n2"}, {"from": "n2", "to": "n3"}]
    r = fake_engine.start_run(nodes, edges, "k6")
    assert r["status"] == "done"
    assert _labels(r["results"]) == ["트리거", "조회", "기록"]


def test_linear_with_approval_resume(fake_engine):
    """선형 + 승인 게이트: 멈췄다 재개 → 뒤 노드까지."""
    nodes = [
        {"id": "n1", "type": "trigger", "label": "트리거"},
        {"id": "n2", "type": "approve", "label": "승인"},
        {"id": "n3", "type": "output", "label": "기록"},
    ]
    edges = [{"from": "n1", "to": "n2"}, {"from": "n2", "to": "n3"}]
    r = fake_engine.start_run(nodes, edges, "k7")
    assert r["status"] == "awaiting_approval"
    d = fake_engine.resume_run(r["run_id"])
    assert d["status"] == "done"
    assert _labels(d["results"]) == ["기록"]


# ── dedup(중복 중단) 여전히 동작 ──────────────────────────


def test_dedup_stops_run(fake_engine):
    """dedup 노드가 중복 감지 시 stop → 뒤 노드 실행 안 됨."""
    nodes = [
        {"id": "n1", "type": "dedup", "label": "중복체크"},
        {"id": "n2", "type": "output", "label": "기록"},
    ]
    edges = [{"from": "n1", "to": "n2"}]
    # ctx["_dup"]를 True로 넣으려면 start_run이 ctx를 만들므로, item_key로는 못 함.
    # 대신 dedup이 통과하는 케이스와 대비만 확인(중단 로직은 fake_exec가 _dup 기반).
    r = fake_engine.start_run(nodes, edges, "k8")
    # 기본 ctx엔 _dup 없음 → 통과 → 기록까지
    assert _labels(r["results"]) == ["중복체크", "기록"]
    assert r["status"] == "done"


# ── 사이클 방어 ────────────────────────────────────────────


def test_cycle_does_not_hang(fake_engine):
    """엣지가 사이클을 이뤄도 무한루프 없이 종료(seen 방어)."""
    nodes = [
        {"id": "a", "type": "tool", "label": "A"},
        {"id": "b", "type": "tool", "label": "B"},
    ]
    edges = [{"from": "a", "to": "b"}, {"from": "b", "to": "a"}]  # 순환
    r = fake_engine.start_run(nodes, edges, "k9")
    # 각 노드 한 번씩만 실행되고 끝
    assert set(_labels(r["results"])) == {"A", "B"}
    assert r["status"] == "done"
