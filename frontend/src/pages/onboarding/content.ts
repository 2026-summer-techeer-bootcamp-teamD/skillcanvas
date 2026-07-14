// ---- Step content -------------------------------------------------------
// video는 public/videos/ 안에 있는 파일을 절대경로로 참조합니다.
// (Vite public 폴더 방식이라 import 없이 바로 문자열 경로로 씁니다)

export interface OnboardingStep {
  pill: string;
  parts: string[];
  video: string;
  cta: string;
}

export const STEPS: OnboardingStep[] = [
  {
    pill: "STEP 1 · 보기 & 조립",
    parts: ["보이지 않던 ", "자동화", "를,\n캔버스 위에서 눈으로 ", "조립하세요", "."],
    video: "/videos/step1-canvas.mp4",
    cta: "다음 →",
  },
  {
    pill: "STEP 2 · 말하면 완성",
    parts: ["말만 하면 워크플로우가 ", "완성돼요", ".\n중요한 순간엔 승인받고 ", "안전하게", "."],
    video: "/videos/step2-autoflow.mp4",
    cta: "다음 →",
  },
  {
    pill: "STEP 3 · 나누고 가져오기",
    parts: ["잘 만든 워크플로우,\n갤러리에서 ", "나누고 가져오세요", "."],
    video: "/videos/step3-gallery.mp4",
    cta: "시작하기 →",
  },
];
