import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { ClerkProvider } from "@clerk/clerk-react";
import App from "./App";
import "./styles/global.css";

// Clerk Publishable Key (.env.local 의 VITE_CLERK_PUBLISHABLE_KEY).
// 키가 아직 없으면 Clerk 없이 그대로 렌더 → 개발 중 앱이 멈추지 않는다.
const clerkKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY as string | undefined;

const app = (
  <BrowserRouter>
    <App />
  </BrowserRouter>
);

if (!clerkKey) {
  console.warn(
    "[Clerk] VITE_CLERK_PUBLISHABLE_KEY 가 없어 인증 없이 실행합니다. .env.local 에 키를 넣으면 켜집니다.",
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    {clerkKey ? (
      <ClerkProvider publishableKey={clerkKey} afterSignOutUrl="/">
        {app}
      </ClerkProvider>
    ) : (
      app
    )}
  </React.StrictMode>,
);
