"""A-2: 스킬 구조 → SKILL.md 저장 (본문 보존).

핵심: 기존 파일이 있으면 body(사용자가 쓴 지시문)는 건드리지 않고
frontmatter(name/description/allowed-tools)만 새 값으로 교체한다.
없는 스킬이면 신규 생성(이슈 #20 결정).
"""

from app.core import config
from app.sync.skillfile import read_skill, write_skill


def save_skill(skill: str, name: str, description: str, allowed_tools: list[str]) -> None:
    skill_md = config.SKILLS_DIR / skill / "SKILL.md"

    if skill_md.exists():
        _old_meta, body = read_skill(skill_md)  # 기존 본문 보존
    else:
        body = f"\n# {name}\n\n(여기에 스킬 지시문을 작성하세요.)\n"  # 신규 기본 본문

    metadata = {
        "name": name,
        "description": description,
        "allowed-tools": allowed_tools,  # 파일 규약은 하이픈(-), 요청은 snake_case
    }
    write_skill(skill_md, metadata, body)
