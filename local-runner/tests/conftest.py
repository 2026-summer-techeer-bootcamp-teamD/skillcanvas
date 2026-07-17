"""실행기 테스트 공용. (pytest가 자동으로 읽음)

실행:  local-runner 폴더에서  `pytest`

실행기 테스트는 DB 트랜잭션이 불필요하다(runner는 in-memory RUNS + 순회 로직).
Claude 호출(exec_node 안의 claude_call)만 목킹하면 순회 로직을 순수 검증할 수 있어,
가짜 exec_node를 주입하는 fake_engine 픽스처를 제공한다.
"""

import pytest

import app.engine.runner as runner_mod


@pytest.fixture
def fake_engine(monkeypatch):
    """runner의 exec_node를 '노드 타입만 보고 결정론적으로 반환'하는 가짜로 교체.

    - branch : detail이 "route=<라벨>"이면 그 라벨을 route로 반환(AI 대신 강제 분류).
               detail이 "라벨1|라벨2"면 첫 라벨로 분류(기본).
    - approve: pause=True (승인 게이트)
    - dedup  : ctx["_dup"]가 True면 stop=True
    - 그 외  : 그냥 result만

    실제 Claude를 안 부르므로 빠르고 결정론적. 순회·분기·재개 로직만 검증한다.
    """

    def fake_exec(node, ctx, history):
        t = node.get("type")
        label = node.get("label", "")
        detail = node.get("detail", "")
        if t == "branch":
            if detail.startswith("route="):
                route = detail[len("route=") :]
            else:
                route = (detail.split("|")[0] if detail else "").strip()
            return {"result": f"분기→{route}", "route": route}
        if t == "approve":
            return {"result": "승인대기", "pause": True}
        if t == "dedup":
            if ctx.get("_dup"):
                return {"result": "중복→중단", "stop": True}
            return {"result": "신규→통과"}
        return {"result": f"실행:{label}"}

    monkeypatch.setattr(runner_mod, "exec_node", fake_exec)
    return runner_mod
