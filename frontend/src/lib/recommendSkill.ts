/**
 * 자연어 문장 → 스킬 초안(블록 세트) 추천.
 *
 * 지금은 키워드 기반 목업이지만, 화면은 이 함수의 반환 스키마(SkillDraft)만 알면 된다.
 * 백엔드 AI가 붙으면 본문을 fetch("/api/recommend") 로 교체하고 화면 코드는 그대로 둔다.
 */

export type SkillNodeType = "trigger" | "agent" | "tool" | "output" | "approve";

export interface SkillBlock {
  id: string;
  type: SkillNodeType;
  /** 사람이 읽는 타입 라벨 (트리거/에이전트/도구/출력/승인) */
  typeLabel: string;
  /** 블록 제목 (예: "새 메일 수신") */
  title: string;
  /** 사용하는 도구·모델 (예: "Gmail", "claude-sonnet") */
  meta: string;
}

export interface SkillDraft {
  name: string;
  blocks: SkillBlock[];
}

const MAIL_DRAFT: SkillDraft = {
  name: "메일 비서",
  blocks: [
    { id: "b1", type: "trigger", typeLabel: "트리거", title: "새 메일 수신", meta: "Gmail" },
    { id: "b2", type: "agent", typeLabel: "에이전트", title: "본문 요약", meta: "claude-sonnet" },
    { id: "b3", type: "tool", typeLabel: "도구", title: "우선순위 분류", meta: "rules + LLM" },
    { id: "b4", type: "output", typeLabel: "출력", title: "Slack 알림", meta: "Slack" },
    { id: "b5", type: "tool", typeLabel: "도구", title: "Notion 기록", meta: "Notion MCP" },
  ],
};

const CS_DRAFT: SkillDraft = {
  name: "CS 대응 봇",
  blocks: [
    { id: "b1", type: "trigger", typeLabel: "트리거", title: "컴플레인 접수", meta: "Webhook" },
    { id: "b2", type: "tool", typeLabel: "도구", title: "배송 조회", meta: "Shipping API" },
    {
      id: "b3",
      type: "agent",
      typeLabel: "에이전트",
      title: "사과 메시지 작성",
      meta: "claude-sonnet",
    },
    { id: "b4", type: "approve", typeLabel: "승인", title: "쿠폰 발송 승인", meta: "사람 확인" },
    { id: "b5", type: "output", typeLabel: "출력", title: "답변·쿠폰 발송", meta: "Email" },
  ],
};

const MEETING_DRAFT: SkillDraft = {
  name: "회의록 정리",
  blocks: [
    { id: "b1", type: "trigger", typeLabel: "트리거", title: "새 슬랙 메시지", meta: "Slack" },
    { id: "b2", type: "agent", typeLabel: "에이전트", title: "핵심 요약", meta: "claude-sonnet" },
    {
      id: "b3",
      type: "agent",
      typeLabel: "에이전트",
      title: "액션아이템 추출",
      meta: "claude-sonnet",
    },
    {
      id: "b4",
      type: "output",
      typeLabel: "출력",
      title: "Notion 회의록 저장",
      meta: "Notion MCP",
    },
  ],
};

const GENERIC_DRAFT: SkillDraft = {
  name: "새 스킬",
  blocks: [
    { id: "b1", type: "trigger", typeLabel: "트리거", title: "시작 조건", meta: "직접 설정" },
    { id: "b2", type: "agent", typeLabel: "에이전트", title: "작업 처리", meta: "claude-sonnet" },
    { id: "b3", type: "output", typeLabel: "출력", title: "결과 내보내기", meta: "직접 설정" },
  ],
};

function pickDraft(text: string): SkillDraft {
  const t = text.toLowerCase();
  if (/(메일|이메일|mail|gmail)/.test(t)) return MAIL_DRAFT;
  if (/(cs|컴플레인|배송|쿠폰|고객)/.test(t)) return CS_DRAFT;
  if (/(슬랙|slack|회의|회의록|미팅)/.test(t)) return MEETING_DRAFT;
  return GENERIC_DRAFT;
}

/** 추천 호출. 실제 AI 응답처럼 약간의 지연을 준다. */
export function recommendSkill(text: string): Promise<SkillDraft> {
  const draft = pickDraft(text);
  return new Promise((resolve) => {
    setTimeout(() => resolve(draft), 900);
  });
}
