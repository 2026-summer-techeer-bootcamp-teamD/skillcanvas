"""워크플로우 실행 오케스트레이션. PoC startRun/stepRun/RUNS 이식.

run 상태는 in-memory(RUNS). 승인 재개(A-5)가 같은 run_id를 이어받는다.
재시작 시 날아가도 무방(처음부터 재실행하면 됨) → run_state는 SQLite 안 감.
"""

from app.engine.nodes import exec_node
from app.engine.topo import topo_order

RUNS: dict[str, dict] = {}  # run_id → 실행 상태(중단/재개용)
_seq = {"n": 0}  # run_id 생성용 카운터


def _outgoing(edges: list[dict], node_id: str) -> list[dict]:
    """node_id에서 나가는 엣지 목록 (from == node_id)."""
    return [e for e in edges if e.get("from") == node_id]


def _next_node_id(run: dict, node: dict, out: dict) -> str | None:
    """현재 노드 실행 결과를 보고 '다음에 갈 노드 id'를 고른다. 없으면 None(끝).

    - 분기 노드(out["route"] 있음): 나가는 엣지 중 when == route 인 것으로만.
      매칭 없으면 when 없는 엣지로 폴백(느슨하게), 그것도 없으면 끝.
    - 일반 노드: 나가는 엣지의 to 하나로. (여러 개면 첫 번째 — 선형 워크플로우 전제)
    - 나가는 엣지 없음: 끝.

    조건 없는 기존 워크플로우(엣지에 when 없음)는 topo 순서의 '다음'과 동일하게 흐른다.
    """
    outs = _outgoing(run["edges"], node["id"])
    if not outs:
        return None

    route = out.get("route")
    if route is not None:  # 분기 노드
        matched = [e for e in outs if e.get("when") == route]
        if not matched:  # 라벨 매칭 실패 → 조건 없는 엣지로 폴백
            matched = [e for e in outs if e.get("when") is None]
        return matched[0]["to"] if matched else None

    # 일반 노드: 조건 없는 엣지 우선(있으면), 없으면 첫 엣지
    plain = [e for e in outs if e.get("when") is None]
    return (plain[0] if plain else outs[0])["to"]


def step_run(run: dict) -> dict:
    """run['cursor'](현재 노드 id)부터 그래프를 따라가며 실행.

    pause(승인)/stop(중복)에서 멈추고 cursor를 '다음 노드'로 세팅해두므로,
    resume_run이 cursor부터 이어서 재개할 수 있다(idx 없이 노드 id 기반).
    엣지의 when 조건에 따라 분기 노드에서 한쪽 경로만 탄다.
    """
    seen: set[str] = run["seen"]  # 사이클 방어(같은 노드 재방문 차단)
    while run["cursor"] is not None:
        node = run["by_id"].get(run["cursor"])
        if node is None or node["id"] in seen:
            break
        seen.add(node["id"])

        # run["results"] = 지금까지 실행된 이전 단계들 → agent가 맥락으로 참고
        out = exec_node(node, run["ctx"], run["results"])
        run["results"].append(
            {
                "id": node["id"],
                "label": node.get("label", ""),
                "type": node.get("type"),
                "result": out["result"],
            }
        )
        # 다음 노드를 미리 정해 cursor에 저장 → pause 시에도 재개 지점 보존
        run["cursor"] = _next_node_id(run, node, out)

        if out.get("pause"):
            pending = {"id": node["id"], "message": node.get("detail") or node.get("label", "")}
            return _stash(run, "awaiting_approval", pending)
        if out.get("stop"):
            return _stash(run, "stopped")
    return _stash(run, "done")


def _start_node_id(nodes: list[dict], edges: list[dict]) -> str | None:
    """시작 노드 = 들어오는 엣지가 없는 노드. 여러 개/없으면 topo 순서 첫 노드로 폴백."""
    targets = {e.get("to") for e in edges}
    roots = [n["id"] for n in nodes if n["id"] not in targets]
    if len(roots) == 1:
        return roots[0]
    order = topo_order(nodes, edges)  # 애매하면 기존 위상정렬 첫 노드
    return order[0] if order else None


def start_run(nodes: list[dict], edges: list[dict], item_key: str) -> dict:
    # 입력 방어: id 없는 노드가 오면 아래 dict 컴프리헨션에서 KeyError(500) → 미리 400 처리
    for n in nodes:
        if not isinstance(n, dict) or not n.get("id"):
            raise ValueError("각 노드에는 id가 필요합니다")

    _seq["n"] += 1
    run_id = f"run{_seq['n']}"
    run = {
        "edges": edges,  # 그래프 순회용(다음 노드 선택)
        "by_id": {n["id"]: n for n in nodes},
        "cursor": _start_node_id(nodes, edges),  # 다음 실행할 노드 id (idx 대체)
        "seen": set(),  # 이미 실행한 노드(사이클 방어)
        "results": [],
        "ctx": {"item_key": item_key},
    }
    RUNS[run_id] = run
    status = step_run(run)
    return {"run_id": run_id, "results": run["results"], **status}


def _stash(run: dict, status: str, pending: dict | None = None) -> dict:
    """마지막 상태를 run에 저장(A-4 조회용) + 반환 dict 생성."""
    run["status"] = status
    run["pending"] = pending
    out = {"status": status}
    if pending is not None:
        out["pending"] = pending
    return out


def get_run(run_id: str) -> dict | None:
    """A-4: run의 현재 상태·결과 조회. 없으면 None.

    results = **전체 스냅샷(누적)**. cf. resume_run(A-5)은 델타만 반환 →
    프론트 계약: approve 응답은 append, status 응답은 전체로 갈아끼워야 중복표시 없음.
    """
    run = RUNS.get(run_id)
    if run is None:
        return None
    # status 미설정(등록 직후 등) 방어 → GET /status가 항상 200
    out = {"run_id": run_id, "status": run.get("status", "running"), "results": run["results"]}
    if run.get("pending"):
        out["pending"] = run["pending"]
    return out


def resume_run(run_id: str) -> dict | None:
    """A-5: 승인 대기 중인 run을 이어서 재개(step_run 한 번 더). 없으면 None.

    results = **이번에 새로 실행된 델타만**(전체 아님). cf. get_run(A-4)은 전체.
    승인 대기(awaiting_approval)가 아니면 재개할 것 없음 → 현재 상태만, 새 실행 0.
    (stopped된 run을 이어 돌려 중단을 우회하는 것 방지)
    """
    run = RUNS.get(run_id)
    if run is None:
        return None
    if run.get("status") != "awaiting_approval":
        snapshot = get_run(run_id)  # run 존재 확정 → None 아님
        snapshot["results"] = []  # 재개할 것 없음 → 새 실행 0
        return snapshot
    before = len(run["results"])
    s = step_run(run)
    return {"run_id": run_id, "results": run["results"][before:], **s}
