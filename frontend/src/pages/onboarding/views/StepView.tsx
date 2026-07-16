import Mascot from "../components/Mascot";
import Headline from "../components/Headline";
import { tokens } from "../tokens";
import type { OnboardingStep } from "../content";

interface StepViewProps {
  step: OnboardingStep;
  stepIndex: number;
  totalSteps: number;
  onNext: () => void;
}

// step: STEPS[i] 데이터 객체, stepIndex: 0-based 진행률 표시용 인덱스
export default function StepView({ step, stepIndex, totalSteps, onNext }: StepViewProps) {
  const dot = (i: number) => ({
    width: stepIndex === i ? 10 : 8,
    height: stepIndex === i ? 10 : 8,
    borderRadius: "50%",
    background: stepIndex === i ? tokens.accent : "rgb(227,214,196)",
  });

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "row-reverse",
        alignItems: "center",
        justifyContent: "center",
        gap: 56,
        width: "100%",
        maxWidth: 1080,
      }}
    >
      <div style={{ flex: 1, minWidth: 280, maxWidth: 420, display: "flex", flexDirection: "column", alignItems: "flex-start", textAlign: "left" }}>
        <div
          style={{
            borderRadius: 999,
            background: "rgb(255,255,255)",
            boxShadow: "inset 0 0 0 1px rgb(239,230,217)",
            padding: "6px 13px",
            display: "flex",
            alignItems: "center",
            gap: 7,
          }}
        >
          <Mascot size={15} />
          <span style={{ fontWeight: 700, fontSize: 12.5, color: tokens.badgeText }}>{step.pill}</span>
        </div>
        <div style={{ height: 20 }} />
        <Headline parts={step.parts} />
        <div style={{ height: 28 }} />
        <div style={{ display: "flex", flexDirection: "row", alignItems: "center", gap: 8 }}>
          {Array.from({ length: totalSteps }).map((_, i) => (
            <div key={i} style={dot(i)} />
          ))}
        </div>
        <div style={{ height: 28 }} />
        <button
          onClick={onNext}
          style={{
            border: "none",
            borderRadius: 12,
            background: tokens.ink,
            padding: "15px 20px",
            fontWeight: 700,
            fontSize: 15,
            color: "rgb(255,255,255)",
            fontFamily: "inherit",
            cursor: "pointer",
            width: 148,
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          {step.cta}
        </button>
      </div>

      <div
        style={{
          position: "relative",
          flex: 1,
          minWidth: 320,
          maxWidth: 520,
          borderRadius: 20,
          background: "rgb(255,255,255)",
          boxShadow: `inset 0 0 0 1px ${tokens.line}, 0px 14px 36px -8px rgba(120,79,20,0.14)`,
          padding: 14,
          display: "flex",
          flexDirection: "column",
          gap: 10,
        }}
      >
        {/* video 경로는 public/videos/ 안의 실제 파일을 절대경로로 참조합니다. */}
        <video
          key={step.video}
          src={step.video}
          autoPlay
          loop
          muted
          playsInline
          style={{ width: "100%", height: 340, objectFit: "cover", borderRadius: 12, boxShadow: `inset 0 0 0 1px ${tokens.line}` }}
        />
      </div>
    </div>
  );
}
