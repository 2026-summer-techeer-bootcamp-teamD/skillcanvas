"""SKILL.md 읽기/쓰기 — frontmatter(설정)와 body(본문) 분리·결합.

PoC의 parseFrontmatter/writeSkillRaw를 python-frontmatter 라이브러리로 대체.
읽기(read_skill)와 쓰기(write_skill)가 짝. A-2 저장에서 body 보존에 쓰인다.
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


def write_skill(skill_md_path: Path, metadata: dict, body: str) -> None:
    """metadata(frontmatter) + body(본문)를 SKILL.md로 저장.

    폴더가 없으면 생성(신규 스킬 대비). frontmatter.dumps가 '---' 래핑까지 처리.
    """
    post = frontmatter.Post(body)
    post.metadata = metadata
    skill_md_path.parent.mkdir(parents=True, exist_ok=True)
    # sort_keys=False: 넣은 순서(name→description→allowed-tools) 유지 → diff 최소화
    skill_md_path.write_text(frontmatter.dumps(post, sort_keys=False), encoding="utf-8")
