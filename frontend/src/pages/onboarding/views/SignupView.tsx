import { useState, type ChangeEvent, type FormEvent } from "react";
import Mascot from "../components/Mascot";
import { tokens, inputStyle } from "../tokens";

export interface SignupFormData {
  name: string;
  email: string;
  password: string;
}

interface SignupViewProps {
  onSubmit?: (data: SignupFormData) => void;
  onBack: () => void;
  onLoginClick?: () => void;
}

// TODO(team): 이 프로젝트는 @clerk/clerk-react를 쓰고 있어요. 실제 가입 처리는
// 이 커스텀 폼 UI를 유지하면서 useSignUp() 훅으로 Clerk에 붙이거나,
// 아예 Clerk의 <SignUp /> 컴포넌트로 이 폼을 대체하는 두 가지 방법이 있습니다.
// onSubmit: 팀 회원가입 로직(Clerk signUp.create 등)으로 교체하세요.
export default function SignupView({ onSubmit, onBack, onLoginClick }: SignupViewProps) {
  const [form, setForm] = useState<SignupFormData>({ name: "", email: "", password: "" });

  const update = (key: keyof SignupFormData) => (e: ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [key]: e.target.value }));

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    onSubmit?.(form);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center" }}>
      <span style={{ fontWeight: 800, fontSize: 30, letterSpacing: "-0.6px", color: tokens.ink }}>계정 만들기</span>
      <div style={{ height: 8 }} />
      <span style={{ fontWeight: 400, fontSize: 15, color: tokens.muted }}>30초면 첫 스킬을 쌓기 시작할 수 있어요.</span>
      <div style={{ height: 24 }} />

      <form
        onSubmit={handleSubmit}
        style={{
          width: 380,
          maxWidth: "88vw",
          borderRadius: 18,
          background: "rgb(255,255,255)",
          boxShadow: `inset 0 0 0 1px ${tokens.line}, 0px 14px 36px -8px rgba(120,79,20,0.12)`,
          padding: "26px 28px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <Mascot size={42} />
        <div style={{ height: 8 }} />
        <span style={{ fontWeight: 800, fontSize: 18, color: tokens.ink }}>회원가입</span>
        <div style={{ height: 18 }} />
        <div style={{ display: "flex", flexDirection: "column", gap: 10, width: "100%" }}>
          <input placeholder="이름" value={form.name} onChange={update("name")} style={inputStyle} required />
          <input placeholder="이메일" type="email" value={form.email} onChange={update("email")} style={inputStyle} required />
          <input placeholder="비밀번호" type="password" value={form.password} onChange={update("password")} style={inputStyle} required />
        </div>
        <div style={{ height: 18 }} />
        <button
          type="submit"
          style={{
            width: "100%",
            border: "none",
            borderRadius: 10,
            background: tokens.ink,
            padding: "12px 14px",
            fontWeight: 700,
            fontSize: 14,
            color: "#fff",
            fontFamily: "inherit",
            cursor: "pointer",
          }}
        >
          가입하기
        </button>
        <div style={{ height: 14 }} />
        <a
          href="#"
          onClick={(e) => {
            e.preventDefault();
            onLoginClick?.();
          }}
          style={{ fontSize: 13, color: tokens.badgeText, textDecoration: "none" }}
        >
          이미 계정이 있나요? 로그인 →
        </a>
      </form>

      <div style={{ height: 22 }} />
      <button
        onClick={onBack}
        style={{ border: "none", background: "transparent", fontWeight: 600, fontSize: 14, color: "rgb(138,127,113)", fontFamily: "inherit", cursor: "pointer" }}
      >
        ← 처음으로
      </button>
    </div>
  );
}
