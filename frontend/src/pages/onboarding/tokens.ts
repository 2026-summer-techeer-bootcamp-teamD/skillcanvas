// ---- Design tokens ----------------------------------------------------------
// TODO(team): 팀 디자인 시스템에 동일한 토큰(색상/폰트)이 있다면 이 파일 대신
// 그쪽 theme을 import 해서 씁니다. 이 파일은 기존 토큰이 없을 때의 기본값입니다.
// (Tailwind/styled-components 미사용 프로젝트라 CSS-in-JS 인라인 스타일 방식 유지)

import type { CSSProperties } from "react";

export const tokens = {
  ink: "rgb(35,32,25)",
  accent: "rgb(232,132,60)",
  muted: "rgb(125,115,103)",
  line: "rgb(230,221,208)",
  badgeText: "rgb(138,107,63)",
  pageBg: "rgb(250,248,244)",
  font: "Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif",
} as const;

export const NODE_COLORS = {
  trigger: "rgb(183,121,31)",
  tool: "rgb(42,93,176)",
  agent: "rgb(122,79,214)",
  output: "rgb(31,138,76)",
  approve: "rgb(232,132,60)",
} as const;

export const inputStyle: CSSProperties = {
  width: "100%",
  borderRadius: 10,
  background: "rgb(251,250,247)",
  boxShadow: "inset 0 0 0 1px rgb(230,226,217)",
  padding: "12px 14px",
  fontSize: 14,
  fontFamily: "inherit",
  color: tokens.ink,
  border: "none",
};
