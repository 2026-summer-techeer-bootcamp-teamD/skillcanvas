"""워크플로우 실행 오케스트레이션. PoC startRun/stepRun/RUNS 이식.

run 상태는 in-memory(RUNS). 승인 재개(A-5)가 같은 run_id를 이어받는다.
재시작 시 날아가도 무방(처음부터 재실행하면 됨) → run_state는 SQLite 안 감.
"""

from app.engine.nodes import exec_node
from app.engine.topo import topo_order

RUNS: dict[str, dict] = {}  # run_id → 실행 상태(중단/재개용)
_seq = {"n": 0}  # run_id 생성용 카운터


def step_run(run: dict) -> dict:
    """run['idx']부터 실행하다 pause(승인)/stop(중복)/끝에서 멈춘다."""
    order = run["order"]
    while run["idx"] < len(order):
        node = run["by_id"].get(order[run["idx"]])
        run["idx"] += 1
        if node is None:
            continue
        out = exec_node(node, run["ctx"])
        run["results"].append(
            {
                "id": node["id"],
                "label": node.get("label", ""),
                "type": node.get("type"),
                "result": out["result"],
            }
        )
        if out.get("pause"):
            pending = {"id": node["id"], "message": node.get("detail") or node.get("label", "")}
            return _stash(run, "awaiting_approval", pending)
        if out.get("stop"):
            return _stash(run, "stopped")
    return _stash(run, "done")


def start_run(nodes: list[dict], edges: list[dict], item_key: str) -> dict:
    # 입력 방어: id 없는 노드가 오면 아래 dict 컴프리헨션에서 KeyError(500) → 미리 400 처리
    for n in nodes:
        if not isinstance(n, dict) or not n.get("id"):
            raise ValueError("각 노드에는 id가 필요합니다")

    _seq["n"] += 1
    run_id = f"run{_seq['n']}"
    run = {
        "order": topo_order(nodes, edges),
        "by_id": {n["id"]: n for n in nodes},
        "idx": 0,
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
    """A-4: run의 현재 상태·결과 조회. 없으면 None."""
    run = RUNS.get(run_id)
    if run is None:
        return None
    out = {"run_id": run_id, "status": run["status"], "results": run["results"]}
    if run.get("pending"):
        out["pending"] = run["pending"]
    return out


def resume_run(run_id: str) -> dict | None:
    """A-5: 승인 대기 중인 run을 이어서 재개(step_run 한 번 더). 없으면 None.

    승인 대기(awaiting_approval)가 아니면 재개할 것 없음 → 현재 상태만, 새 실행 0.
    (stopped된 run을 이어 돌려 중단을 우회하는 것 방지)
    """
    run = RUNS.get(run_id)
    if run is None:
        return None
    if run.get("status") != "awaiting_approval":
        return get_run(run_id) | {"results": []}
    before = len(run["results"])
    s = step_run(run)
    return {"run_id": run_id, "results": run["results"][before:], **s}
