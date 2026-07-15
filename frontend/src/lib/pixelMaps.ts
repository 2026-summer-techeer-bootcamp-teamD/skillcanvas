// 픽셀 마스코트/로고 맵 — Figma "검은 마스코트" 컨셉과 동일한 픽셀맵.
// 각 문자는 팔레트 키. "." 은 투명(그리지 않음). 색만 바꾸면 리컬러됨.

export interface PixelSprite {
  map: string[];
  palette: Record<string, string>;
}

const ROBOT_MAP: string[] = [
  "..A.A..",
  "BBBBBBB",
  "BEBBBEB",
  "BBBBBBB",
  ".BMMMB.",
  "BBBBBBB",
  ".B...B.",
];

// 검은 로봇 마스코트 (몸통 블랙 · 안테나/입 오렌지 · 눈 크림)
export const ROBOT_BLACK: PixelSprite = {
  map: ROBOT_MAP,
  palette: { A: "#e8843c", B: "#2a2620", E: "#faf8f4", M: "#e8843c" },
};

// 반전 오렌지 로봇 (몸통 오렌지 · 안테나/입 다크 · 눈 크림)
export const ROBOT_ORANGE: PixelSprite = {
  map: ROBOT_MAP,
  palette: { A: "#2a2620", B: "#e8843c", E: "#faf8f4", M: "#2a2620" },
};

// 뮤트 테라코타 로봇 (단색 몸통 · 크림 눈) — 아바타처럼 은은하게 쓸 때
export const ROBOT_MUTED: PixelSprite = {
  map: ROBOT_MAP,
  palette: { A: "#c47a4e", B: "#c47a4e", E: "#faf8f4", M: "#c47a4e" },
};
