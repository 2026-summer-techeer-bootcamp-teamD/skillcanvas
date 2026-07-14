/**
 * 자연어 입력 → 스킬/오토플로우 어디에 가까운지 판단.
 *
 * 지금은 키워드 목업. 백엔드 `POST /classify` 붙으면 본문만 fetch로 교체.
 * "neutral" = 판단 애매 → 사용자가 직접 고름.
 */
export type Intent = "skill" | "workflow" | "neutral";

const FLOW =
  /(매일|자동|오면|되면|이후|그다음|전송|보내|발송|알림|슬랙|slack|웹훅|배송|순서|단계|→|연동|스케줄|리마인드)/;
const SKILL = /(요약|분류|작성|번역|추출|정리|생성|리라이트|태깅|판단|감정)/;

export function classifyIntent(text: string): Promise<Intent> {
  const t = text.toLowerCase();
  const f = FLOW.test(t);
  const s = SKILL.test(t);
  let intent: Intent = "neutral";
  if (f && !s) intent = "workflow";
  else if (s && !f) intent = "skill";
  else if (f && s) intent = "workflow"; // 복합이면 플로우 쪽으로 유도
  return new Promise((resolve) => setTimeout(() => resolve(intent), 800));
}
