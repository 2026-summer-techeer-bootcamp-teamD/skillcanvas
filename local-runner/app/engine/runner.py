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
            return {
                "status": "awaiting_approval",
                "pending": {
                    "id": node["id"],
                    "message": node.get("detail") or node.get("label", ""),
                },
            }
        if out.get("stop"):
            return {"status": "stopped"}
    return {"status": "done"}


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
