import type { ReactNode } from "react";
import Mascot from "./components/Mascot";
import { tokens } from "./tokens";

interface OnboardingLayoutProps {
  onSkip: () => void;
  children: ReactNode;
}

// 상단 nav + 배경 도트 패턴 + 가운데 콘텐츠 슬롯을 담당하는 공용 쉘.
// hero/step/signup 뷰는 모두 이 안에서 children으로 렌더됩니다.
export default function OnboardingLayout({ onSkip, children }: OnboardingLayoutProps) {
  return (
    <div
      style={{
        position: "relative",
        width: "100%",
        minHeight: "100vh",
        background: tokens.pageBg,
        fontFamily: tokens.font,
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          opacity: 0.5,
          pointerEvents: "none",
          backgroundImage: "radial-gradient(rgb(222,211,195) 1.4px, transparent 1.4px)",
          backgroundSize: "26px 26px",
        }}
      />

      <div
        style={{
          position: "relative",
          zIndex: 1,
          display: "flex",
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "20px 40px",
          flexShrink: 0,
        }}
      >
        <div style={{ display: "flex", flexDirection: "row", alignItems: "center", gap: 10 }}>
          <Mascot size={21} style={{ width: 26, height: 26 }} />
          <span style={{ fontWeight: 800, fontSize: 17, letterSpacing: "-0.17px", color: tokens.ink }}>
            SkillCanvas
          </span>
        </div>
        <button
          onClick={onSkip}
          style={{
            border: "none",
            borderRadius: 9,
            boxShadow: "inset 0 0 0 1px rgb(224,216,205)",
            padding: "8px 18px",
            background: "transparent",
            fontWeight: 600,
            fontSize: 14,
            color: "rgb(138,127,113)",
            fontFamily: "inherit",
            cursor: "pointer",
          }}
        >
          건너뛰기
        </button>
      </div>

      <div
        style={{
          position: "relative",
          zIndex: 1,
          flex: 1,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "20px 24px 64px",
        }}
      >
        {children}
      </div>
    </div>
  );
}
