import type { ReactNode } from "react";
import { BrandNav } from "../../components/BrandNav";
import { tokens } from "./tokens";
import "../../styles/scene.css";

interface OnboardingLayoutProps {
  onSkip: () => void;
  children: ReactNode;
}

// 상단 nav + 배경 도트 패턴 + 가운데 콘텐츠 슬롯을 담당하는 공용 쉘.
// hero/step/signup 뷰는 모두 이 안에서 children으로 렌더됩니다.
// 상단 바는 Splash/Login/Signup과 동일하게 공용 BrandNav + sc-nav 스타일을 씁니다.
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

      <BrandNav
        action={
          <button className="sc-skip" type="button" onClick={onSkip}>
            건너뛰기
          </button>
        }
      />

      <div
        style={{
          position: "relative",
          zIndex: 1,
          flex: 1,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "84px 24px 64px",
        }}
      >
        {children}
      </div>
    </div>
  );
}
