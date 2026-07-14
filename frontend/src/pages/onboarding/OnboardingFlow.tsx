import { useState } from "react";
import OnboardingLayout from "./OnboardingLayout";
import StepView from "./views/StepView";
import { STEPS } from "./content";

interface OnboardingFlowProps {
  // 온보딩(스텝 1~3)이 끝나면 호출됩니다. 기존 라우팅 그대로
  // App.tsx의 OnboardingRoute에서 onDone={() => navigate("/login")} 로 넘어옵니다.
  onDone: () => void;
}

// Splash 화면이 이미 인트로/시작하기 역할을 하고 있어서, 여기선 별도 hero
// 화면 없이 스텝1부터 바로 시작합니다. (예전엔 hero+3스텝이었는데 hero가
// Splash랑 거의 똑같이 생겨서 "첫 화면이 두 번 나온다"는 문제가 있었음)
//
// TODO(team) 실제 통합 시 확인할 지점
// 1) StepView 안의 video 경로를 실제 asset import로 교체하세요.
// 2) tokens.ts가 팀 디자인 시스템과 겹치면 팀 theme으로 대체하세요.
export default function OnboardingFlow({ onDone }: OnboardingFlowProps) {
  const [step, setStep] = useState(1); // 1..STEPS.length

  const next = () => {
    if (step >= STEPS.length) {
      onDone();
      return;
    }
    setStep((s) => s + 1);
  };

  const currentStep = STEPS[step - 1];

  return (
    <OnboardingLayout onSkip={onDone}>
      <StepView step={currentStep} stepIndex={step - 1} totalSteps={STEPS.length} onNext={next} />
    </OnboardingLayout>
  );
}
