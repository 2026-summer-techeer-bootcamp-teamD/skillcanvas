"""SKILL.md 파일 읽기 — frontmatter(설정)와 body(본문)로 분리.

PoC의 parseFrontmatter를 python-frontmatter 라이브러리로 대체.
A-1(그래프 생성)은 metadata만 쓰지만, A-2(저장)에서 body 보존이 필요하므로
둘 다 반환해둔다.
"""

from pathlib import Path

import frontmatter


def read_skill(skill_md_path: Path) -> tuple[dict, str]:
    """SKILL.md 경로를 받아 (metadata, body) 반환.

    metadata: name/description/allowed-tools 등 위쪽 YAML → dict
    body: '---' 아래 본문 문자열
    """
    post = frontmatter.load(skill_md_path)
    return post.metadata, post.content
