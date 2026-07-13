import { useState } from "react";
import { PixelArt } from "../components/PixelArt";
import { BrandNav } from "../components/BrandNav";
import { NodeMotif } from "../components/NodeMotif";
import { ROBOT_BLACK } from "../lib/pixelMaps";
import "../styles/scene.css";
import "./Onboarding.css";

interface OnboardingStep {
  eyebrow: string;
  message: string;
  highlight: string;
  cta: string;
}

const STEPS: OnboardingStep[] = [
  {
    eyebrow: "STEP 1 · 보기 & 조립",
    message: "눈에 안 보이던 내 AI 스킬과 자동화,\n이제 캔버스에서 눈으로 보고 조립하세요.",
    highlight: "눈으로 보고 조립",
    cta: "다음 →",
  },
  {
    eyebrow: "STEP 2 · 말하면 완성",
    message:
      "말로 설명하면 스킬·도구를 이어 나만의 워크플로우가 완성되고,\n중요한 순간엔 승인받고 안전하게 돌아가요.",
    highlight: "승인받고 안전하게",
    cta: "다음 →",
  },
  {
    eyebrow: "STEP 3 · 나누고 가져오기",
    message: "잘 만든 워크플로우는 갤러리에서 나누고,\n남의 것도 가져와 내 것으로.",
    highlight: "가져와 내 것으로",
    cta: "시작하기 →",
  },
];

/** 메시지에서 키워드만 강조. 나머지 줄바꿈은 CSS white-space: pre-line 이 처리. */
function HighlightedMessage({ text, highlight }: { text: string; highlight: string }) {
  const idx = text.indexOf(highlight);
  if (idx < 0) {
    return <>{text}</>;
  }
  return (
    <>
      {text.slice(0, idx)}
      <span className="ob__hl">{highlight}</span>
      {text.slice(idx + highlight.length)}
    </>
  );
}

interface OnboardingProps {
  onDone?: () => void;
}

export function Onboarding({ onDone }: OnboardingProps) {
  const [step, setStep] = useState(0);
  const current = STEPS[step];
  const isLast = step === STEPS.length - 1;

  const handleNext = () => {
    if (isLast) {
      onDone?.();
    } else {
      setStep((prev) => prev + 1);
    }
  };

  return (
    <section className="sc-scene">
      <NodeMotif />
      <BrandNav
        action={
          <button className="sc-skip" type="button" onClick={onDone}>
            건너뛰기
          </button>
        }
      />

      <main className="ob__hero">
        <span className="ob__eyebrow">{current.eyebrow}</span>

        <p className="ob__message">
          <HighlightedMessage text={current.message} highlight={current.highlight} />
        </p>

        <div className="ob__dots" aria-hidden="true">
          {STEPS.map((_, i) => (
            <span key={i} className={i === step ? "ob__dot ob__dot--active" : "ob__dot"} />
          ))}
        </div>

        <button className="ob__cta" type="button" onClick={handleNext}>
          {current.cta}
        </button>
      </main>

      <div className="ob__character" aria-hidden="true">
        <PixelArt sprite={ROBOT_BLACK} className="ob__characterArt" />
        <span className="ob__characterShadow" />
      </div>
    </section>
  );
}
