// 기존 src/pages/Onboarding.tsx 가 export하던 이름(Onboarding)과 props(onDone)를
// 그대로 맞춰서, App.tsx에서는 import 경로 한 줄만 바꾸면 됩니다.
export { default as Onboarding } from "./OnboardingFlow";
