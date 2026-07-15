import type { ReactNode } from "react";
import { Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "@clerk/clerk-react";
import { Splash } from "./pages/Splash";
import { Onboarding } from "./pages/Onboarding";
import { Login } from "./pages/Login";
import { Signup } from "./pages/Signup";
import { Create } from "./pages/Create";
import { Skill } from "./pages/Skill";
import { AutoFlow } from "./pages/AutoFlow";
import { Share } from "./pages/Share";
import { MyWorld } from "./pages/MyWorld";
import type { NavTab } from "./components/TopNav";

const TAB_ROUTES: Record<NavTab, string> = {
  START: "/",
  CREATE: "/create",
  SKILL: "/skill",
  "AUTO-FLOW": "/auto-flow",
  "MY WORLD": "/my-world",
  SHARE: "/share",
};

/** 로그인해야 볼 수 있는 앱 화면 가드. 미로그인 시 /login 으로 보냄. */
function RequireAuth({ children }: { children: ReactNode }) {
  const { isLoaded, isSignedIn } = useAuth();
  if (!isLoaded) return null; // Clerk 세션 확인 중
  if (!isSignedIn) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

/** 로그인/회원가입 페이지 가드. 이미 로그인했으면 앱으로 보냄(이중 로그인 방지). */
function RedirectIfSignedIn({ children }: { children: ReactNode }) {
  const { isLoaded, isSignedIn } = useAuth();
  if (!isLoaded) return null;
  if (isSignedIn) return <Navigate to="/create" replace />;
  return <>{children}</>;
}

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
      onSkip={() => navigate("/create")}
      // 권한 모달 통과 → 통합 입력(Create)로 진입
      onEnter={() => navigate("/create")}
      onSignup={() => navigate("/signup")}
    />
  );
}

function SignupRoute() {
  const navigate = useNavigate();
  return (
    <Signup
      onSkip={() => navigate("/login")}
      // 회원가입+이메일 인증 완료 → 로그인된 상태로 Create 진입
      onSignup={() => navigate("/create")}
      onLogin={() => navigate("/login")}
    />
  );
}

function CreateRoute() {
  const navigate = useNavigate();
  return (
    <Create
      onNavigate={(tab) => navigate(TAB_ROUTES[tab])}
      // 선택 확정 → 해당 빌더로 입력 텍스트와 함께 이동(그때 그 탭이 활성화됨)
      onCreate={(choice, text) =>
        navigate(choice === "workflow" ? "/auto-flow" : "/skill", { state: { text } })
      }
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
      <Route
        path="/login"
        element={
          <RedirectIfSignedIn>
            <LoginRoute />
          </RedirectIfSignedIn>
        }
      />
      <Route
        path="/signup"
        element={
          <RedirectIfSignedIn>
            <SignupRoute />
          </RedirectIfSignedIn>
        }
      />
      <Route
        path="/create"
        element={
          <RequireAuth>
            <CreateRoute />
          </RequireAuth>
        }
      />
      <Route
        path="/skill"
        element={
          <RequireAuth>
            <SkillRoute />
          </RequireAuth>
        }
      />
      <Route
        path="/auto-flow"
        element={
          <RequireAuth>
            <AutoFlowRoute />
          </RequireAuth>
        }
      />
      <Route
        path="/share/:kind?/:id?"
        element={
          <RequireAuth>
            <ShareRoute />
          </RequireAuth>
        }
      />
      <Route
        path="/my-world"
        element={
          <RequireAuth>
            <MyWorldRoute />
          </RequireAuth>
        }
      />
    </Routes>
  );
}
