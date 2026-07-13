import { Routes, Route, useNavigate } from "react-router-dom";
import { Splash } from "./pages/Splash";
import { Onboarding } from "./pages/Onboarding";
import { Login } from "./pages/Login";

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
      // 앱 화면 퍼블리싱 후 "/skill" 등으로 연결 예정.
      onLogin={() => navigate("/login")}
      onSignup={() => navigate("/signup")}
    />
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<SplashRoute />} />
      <Route path="/onboarding" element={<OnboardingRoute />} />
      <Route path="/login" element={<LoginRoute />} />
    </Routes>
  );
}
