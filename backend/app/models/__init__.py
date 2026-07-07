# 모델 = ERD의 각 테이블을 SQLAlchemy 클래스로 옮긴 것.
# 여기서 전부 import 해둬야 Alembic autogenerate가 인식한다.
#
# 컬럼 규칙(확정 ERD): PK=id(BIGSERIAL), FK=참조테이블명+_id(예 users_id, BIGINT),
#   timestamp=TIMESTAMPTZ(created_at/updated_at), is_public 기본 true, import_count 기본 0.

from app.models.master_tag import MasterTag
from app.models.skill import Skill
from app.models.skill_tag import SkillTag
from app.models.tool_catalog import ToolCatalog
from app.models.user import User
from app.models.workflow import Workflow
from app.models.workflow_tag import WorkflowTag

__all__ = [
    "User",
    "Skill",
    "Workflow",
    "MasterTag",
    "SkillTag",
    "WorkflowTag",
    "ToolCatalog",
]
