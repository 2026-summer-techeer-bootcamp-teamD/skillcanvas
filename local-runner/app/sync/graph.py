"""A-1: .claude 파일들 → 노드 그래프.

PoC server.mjs의 buildGraph 이식.
  - .mcp.json      → mcp 노드
  - settings.json  → rule 노드 (권한 룰)
  - skills/*/SKILL.md → skill 노드 + allowed-tools 엣지(→mcp), rule 엣지
반환: {"nodes": [...], "edges": [...]}
"""

import json

import yaml

from app.core import config
from app.sync.skillfile import read_skill


def _read_json(path, fallback):
    """JSON 파일을 안전하게 읽는다. 없거나 깨지면 fallback."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return fallback


def build_graph() -> dict:
    nodes: list[dict] = []
    edges: list[dict] = []

    # 1) MCP 노드 — .mcp.json의 mcpServers 키 하나 = 도구 하나
    mcp_servers = _read_json(config.MCP_FILE, {}).get("mcpServers", {})
    mcp_names = list(mcp_servers.keys())
    for name in mcp_names:
        nodes.append({"id": f"mcp:{name}", "type": "mcp", "label": name})

    # 2) 룰 노드 — 권한 설정 파일이 있으면 하나
    has_settings = config.SETTINGS_FILE.exists()
    if has_settings:
        nodes.append(
            {"id": "rule:settings", "type": "rule", "label": "권한 룰", "detail": "settings.json"}
        )

    # 3) 스킬 노드 + 엣지 — skills/ 하위 각 폴더의 SKILL.md
    mcp_names_lower = {n.lower() for n in mcp_names}
    if config.SKILLS_DIR.exists():
        for skill_dir in sorted(config.SKILLS_DIR.iterdir()):
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            name = skill_dir.name
            try:
                meta, _body = read_skill(skill_md)
            except yaml.YAMLError:
                # 깨진 SKILL.md: 전체 500 대신 이 스킬만 오류 표시(엣지 생략)
                nodes.append(
                    {
                        "id": f"skill:{name}",
                        "type": "skill",
                        "label": name,
                        "detail": "⚠️ SKILL.md 형식 오류",
                    }
                )
                continue
            nodes.append(
                {
                    "id": f"skill:{name}",
                    "type": "skill",
                    "label": meta.get("name") or name,
                    "detail": meta.get("description", ""),
                }
            )
            # allowed-tools → 카탈로그에 있는 mcp로만 'uses' 엣지
            for tool in meta.get("allowed-tools", []):
                if str(tool).lower() in mcp_names_lower:
                    edges.append({"from": f"skill:{name}", "to": f"mcp:{tool}", "kind": "uses"})
            # 스킬 → 룰 엣지
            if has_settings:
                edges.append({"from": f"skill:{name}", "to": "rule:settings", "kind": "rule"})

    return {"nodes": nodes, "edges": edges}
