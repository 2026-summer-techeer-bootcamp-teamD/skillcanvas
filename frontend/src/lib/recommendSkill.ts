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
  /** 블록 클릭 시 펼쳐지는 한 줄 설명 */
  desc: string;
}

export interface SkillDraft {
  name: string;
  /** 스킬 전체가 무엇을 하는지 한 문장 요약 */
  summary: string;
  blocks: SkillBlock[];
  /** 실제로 쓰는 카탈로그 MCP 키들 (로컬 저장 시 allowed-tools로) */
  mcps?: string[];
  /** 사용자가 입력한 원본 자연어 (로컬 저장 시 description으로) */
  source?: string;
}

const MAIL_DRAFT: SkillDraft = {
  name: "메일 비서",
  summary: "새 메일이 오면 요약·분류해서 Slack과 Notion으로 정리해주는 자동화예요.",
  blocks: [
    {
      id: "b1",
      type: "trigger",
      typeLabel: "트리거",
      title: "새 메일 수신",
      meta: "Gmail",
      desc: "Gmail에 새 메일이 도착하면 워크플로우를 시작해요.",
    },
    {
      id: "b2",
      type: "agent",
      typeLabel: "에이전트",
      title: "본문 요약",
      meta: "claude-sonnet",
      desc: "메일 본문을 claude-sonnet이 핵심만 짧게 요약해요.",
    },
    {
      id: "b3",
      type: "tool",
      typeLabel: "도구",
      title: "우선순위 분류",
      meta: "rules + LLM",
      desc: "규칙과 LLM으로 급함·보통·스팸을 판단해요.",
    },
    {
      id: "b4",
      type: "output",
      typeLabel: "출력",
      title: "Slack 알림",
      meta: "Slack",
      desc: "요약과 우선순위를 지정한 Slack 채널로 보내요.",
    },
    {
      id: "b5",
      type: "tool",
      typeLabel: "도구",
      title: "Notion 기록",
      meta: "Notion MCP",
      desc: "처리한 메일을 Notion 데이터베이스에 남겨요.",
    },
  ],
};

const CS_DRAFT: SkillDraft = {
  name: "CS 대응 봇",
  summary: "CS 컴플레인이 들어오면 배송을 조회하고 사과문과 쿠폰을 보내는 자동화예요.",
  blocks: [
    {
      id: "b1",
      type: "trigger",
      typeLabel: "트리거",
      title: "컴플레인 접수",
      meta: "Webhook",
      desc: "웹훅으로 들어온 고객 문의를 시작점으로 삼아요.",
    },
    {
      id: "b2",
      type: "tool",
      typeLabel: "도구",
      title: "배송 조회",
      meta: "Shipping API",
      desc: "주문번호로 현재 배송 상태를 조회해요.",
    },
    {
      id: "b3",
      type: "agent",
      typeLabel: "에이전트",
      title: "사과 메시지 작성",
      meta: "claude-sonnet",
      desc: "상황에 맞는 사과문을 claude-sonnet이 작성해요.",
    },
    {
      id: "b4",
      type: "approve",
      typeLabel: "승인",
      title: "쿠폰 발송 승인",
      meta: "사람 확인",
      desc: "쿠폰을 보내기 전에 담당자가 한 번 확인해요.",
    },
    {
      id: "b5",
      type: "output",
      typeLabel: "출력",
      title: "답변·쿠폰 발송",
      meta: "Email",
      desc: "확정된 답변과 쿠폰을 이메일로 발송해요.",
    },
  ],
};

const MEETING_DRAFT: SkillDraft = {
  name: "회의록 정리",
  summary: "슬랙 대화를 회의록으로 요약하고 액션아이템을 뽑아 Notion에 저장해요.",
  blocks: [
    {
      id: "b1",
      type: "trigger",
      typeLabel: "트리거",
      title: "새 슬랙 메시지",
      meta: "Slack",
      desc: "지정한 채널에 메시지가 올라오면 시작해요.",
    },
    {
      id: "b2",
      type: "agent",
      typeLabel: "에이전트",
      title: "핵심 요약",
      meta: "claude-sonnet",
      desc: "대화 내용을 claude-sonnet이 회의록 형태로 요약해요.",
    },
    {
      id: "b3",
      type: "agent",
      typeLabel: "에이전트",
      title: "액션아이템 추출",
      meta: "claude-sonnet",
      desc: "할 일과 담당자를 자동으로 뽑아내요.",
    },
    {
      id: "b4",
      type: "output",
      typeLabel: "출력",
      title: "Notion 회의록 저장",
      meta: "Notion MCP",
      desc: "정리된 회의록을 Notion에 기록해요.",
    },
  ],
};

const GENERIC_DRAFT: SkillDraft = {
  name: "새 스킬",
  summary: "입력한 내용을 처리해서 원하는 곳으로 결과를 내보내는 기본 스킬이에요.",
  blocks: [
    {
      id: "b1",
      type: "trigger",
      typeLabel: "트리거",
      title: "시작 조건",
      meta: "직접 설정",
      desc: "언제 이 스킬이 실행될지 정해요.",
    },
    {
      id: "b2",
      type: "agent",
      typeLabel: "에이전트",
      title: "작업 처리",
      meta: "claude-sonnet",
      desc: "핵심 작업을 claude-sonnet이 처리해요.",
    },
    {
      id: "b3",
      type: "output",
      typeLabel: "출력",
      title: "결과 내보내기",
      meta: "직접 설정",
      desc: "처리 결과를 원하는 곳으로 보내요.",
    },
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
