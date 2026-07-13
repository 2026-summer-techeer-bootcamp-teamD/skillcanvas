import { Routes, Route, useNavigate } from "react-router-dom";
import { Splash } from "./pages/Splash";
import { Onboarding } from "./pages/Onboarding";
import { Login } from "./pages/Login";
import { Signup } from "./pages/Signup";

function SplashRoute() {
  const navigate = useNavigate();
  return <Splash onStart={() => navigate("/onboarding")} onSkip={() => navigate("/onboarding")} />;
}

function OnboardingRoute() {
  const navigate = useNavigate();
  return <Onboarding onDone={() => navigate("/login")} />;
}

function LoginRoute() {
  const navigate = useNavigate();
  return (
    <Login
      onSkip={() => navigate("/login")}
      // 권한 모달 "허용하고 설치" → 앱 화면 퍼블리싱 후 "/skill" 등으로 연결 예정.
      onEnter={() => navigate("/login")}
      onSignup={() => navigate("/signup")}
    />
  );
}

function SignupRoute() {
  const navigate = useNavigate();
  return (
    <Signup
      onSkip={() => navigate("/login")}
      onSignup={() => navigate("/login")}
      onLogin={() => navigate("/login")}
    />
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<SplashRoute />} />
      <Route path="/onboarding" element={<OnboardingRoute />} />
      <Route path="/login" element={<LoginRoute />} />
      <Route path="/signup" element={<SignupRoute />} />
    </Routes>
  );
}
