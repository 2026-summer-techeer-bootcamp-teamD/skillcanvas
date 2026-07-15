"""A-2: 스킬 구조 → SKILL.md 저장 (본문 보존).

핵심: 기존 파일이 있으면 body(사용자가 쓴 지시문)는 건드리지 않고
frontmatter(name/description/allowed-tools)만 새 값으로 교체한다.
없는 스킬이면 신규 생성(이슈 #20 결정).

안전장치:
  - skill 이름이 skills 폴더를 벗어나지 못하게 검증(경로 조작 방어).
  - 잘못된 이름/깨진 기존 파일은 ValueError → 라우터에서 400.
"""

from pathlib import Path

import yaml

from app.core import config
from app.sync.skillfile import read_skill, write_skill


def _skill_md_path(skill: str) -> Path:
    """skills 폴더 안의 SKILL.md 경로. 잘못된 이름이면 ValueError.

    - 1차(이름 검사): 단일 폴더명만 허용 — 슬래시('/'), '.', '..' 를 이름 단계에서 거부.
      ('.'은 name이 ''라 자동 거부, '..'은 name이 '..'라 명시적으로 거부)
    - 2차(경로 검사): resolve 후 skills 폴더 하위인지 재확인 — 예기치 못한 경로 탈출 방어(보루).
    """
    if skill in (".", "..") or skill != Path(skill).name:
        raise ValueError("스킬 이름은 폴더 구분자('/')나 '.'/'..' 없이 단일 폴더명이어야 합니다")
    base = config.SKILLS_DIR.resolve()
    target = (config.SKILLS_DIR / skill / "SKILL.md").resolve()
    if not target.is_relative_to(base):
        raise ValueError("잘못된 스킬 이름입니다")
    return target


def save_skill(
    skill: str,
    name: str,
    description: str,
    allowed_tools: list[str],
    body: str | None = None,
) -> None:
    skill_md = _skill_md_path(skill)  # 경로 조작 방어

    if body is not None:
        # 본문을 명시적으로 받으면 그 값으로 저장(빌더에서 조립한 본문)
        body = body if body.endswith("\n") else body + "\n"
    elif skill_md.exists():
        try:
            _old_meta, body = read_skill(skill_md)  # 기존 본문 보존
        except yaml.YAMLError as e:
            raise ValueError("기존 SKILL.md 형식이 올바르지 않습니다") from e
    else:
        body = f"\n# {name}\n\n(여기에 스킬 지시문을 작성하세요.)\n"  # 신규 기본 본문

    metadata = {
        "name": name,
        "description": description,
        "allowed-tools": allowed_tools,  # 파일 규약은 하이픈(-), 요청은 snake_case
    }
    write_skill(skill_md, metadata, body)
