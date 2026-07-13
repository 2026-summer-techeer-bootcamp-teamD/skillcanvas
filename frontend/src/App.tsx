import { Routes, Route, useNavigate } from "react-router-dom";
import { Splash } from "./pages/Splash";
import { Onboarding } from "./pages/Onboarding";

function SplashRoute() {
  const navigate = useNavigate();
  return <Splash onStart={() => navigate("/onboarding")} onSkip={() => navigate("/onboarding")} />;
}

function OnboardingRoute() {
  const navigate = useNavigate();
  // 로그인 페이지 퍼블리싱 후 "/login" 으로 연결 예정.
  return <Onboarding onDone={() => navigate("/")} />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<SplashRoute />} />
      <Route path="/onboarding" element={<OnboardingRoute />} />
    </Routes>
  );
}
