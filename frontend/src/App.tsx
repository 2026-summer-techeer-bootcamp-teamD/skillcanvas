import { Routes, Route, useNavigate } from "react-router-dom";
import { Splash } from "./pages/Splash";
import { Onboarding } from "./pages/Onboarding";
import { Login } from "./pages/Login";
import { Signup } from "./pages/Signup";
import { Skill } from "./pages/Skill";
import { AutoFlow } from "./pages/AutoFlow";
import { Share } from "./pages/Share";
import { MyWorld } from "./pages/MyWorld";
import type { NavTab } from "./components/TopNav";

const TAB_ROUTES: Record<NavTab, string> = {
  START: "/",
  SKILL: "/skill",
  "AUTO-FLOW": "/auto-flow",
  "MY WORLD": "/my-world",
  SHARE: "/share",
};

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
      onSkip={() => navigate("/skill")}
      onEnter={() => navigate("/skill")}
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

function SkillRoute() {
  const navigate = useNavigate();
  return <Skill onNavigate={(tab) => navigate(TAB_ROUTES[tab])} />;
}

function AutoFlowRoute() {
  const navigate = useNavigate();
  return <AutoFlow onNavigate={(tab) => navigate(TAB_ROUTES[tab])} />;
}

function ShareRoute() {
  const navigate = useNavigate();
  return <Share onNavigate={(tab) => navigate(TAB_ROUTES[tab])} />;
}

function MyWorldRoute() {
  const navigate = useNavigate();
  return <MyWorld onNavigate={(tab) => navigate(TAB_ROUTES[tab])} />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<SplashRoute />} />
      <Route path="/onboarding" element={<OnboardingRoute />} />
      <Route path="/login" element={<LoginRoute />} />
      <Route path="/signup" element={<SignupRoute />} />
      <Route path="/skill" element={<SkillRoute />} />
      <Route path="/auto-flow" element={<AutoFlowRoute />} />
      <Route path="/share" element={<ShareRoute />} />
      <Route path="/my-world" element={<MyWorldRoute />} />
    </Routes>
  );
}
