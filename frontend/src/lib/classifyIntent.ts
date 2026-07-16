/**
 * 자연어 입력 → 스킬/오토플로우 어디에 가까운지 판단.
 *
 * 지금은 키워드 목업. 백엔드 `POST /classify` 붙으면 본문만 fetch로 교체.
 * "neutral" = 판단 애매 → 사용자가 직접 고름.
 */
export type Intent = "skill" | "workflow" | "neutral";
