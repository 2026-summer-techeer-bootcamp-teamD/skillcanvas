import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { ClerkProvider } from "@clerk/clerk-react";
import App from "./App";
import "./styles/global.css";

// Clerk Publishable Key — frontend/.env.local 의 VITE_CLERK_PUBLISHABLE_KEY (pk_...).
const clerkKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;
if (!clerkKey) {
  throw new Error(
    "VITE_CLERK_PUBLISHABLE_KEY 가 없습니다. frontend/.env.local 에 pk_ 키를 넣고 dev 서버를 재시작하세요.",
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ClerkProvider publishableKey={clerkKey} afterSignOutUrl="/">
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ClerkProvider>
  </React.StrictMode>,
);
