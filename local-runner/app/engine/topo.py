"""위상정렬(topological sort) — 엣지 방향대로 노드 실행 순서 결정.

PoC topoOrder 이식(Kahn 알고리즘). 진입차수 0인 노드부터 처리하며
연결을 하나씩 풀어간다. 사이클 등으로 안 걸린 노드는 뒤에 붙인다.
"""


def topo_order(nodes: list[dict], edges: list[dict]) -> list[str]:
    indeg = {n["id"]: 0 for n in nodes}  # 각 노드로 들어오는 화살표 개수
    adj: dict[str, list[str]] = {}  # from → [to...]

    for e in edges:
        frm, to = e.get("from"), e.get("to")
        if frm in indeg and to in indeg:  # 모르는 노드 가리키는 엣지는 무시
            indeg[to] += 1
            adj.setdefault(frm, []).append(to)

    queue = [nid for nid, d in indeg.items() if d == 0]  # 시작점(들어오는 화살표 없음)
    seen: set[str] = set()
    order: list[str] = []
    while queue:
        nid = queue.pop(0)
        if nid in seen:
            continue
        seen.add(nid)
        order.append(nid)
        for t in adj.get(nid, []):
            indeg[t] -= 1
            if indeg[t] <= 0:
                queue.append(t)

    for n in nodes:  # 순환 등으로 못 들어간 노드는 뒤에
        if n["id"] not in seen:
            order.append(n["id"])
    return order
