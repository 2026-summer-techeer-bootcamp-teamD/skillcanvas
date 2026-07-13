import { useState } from "react";
import { PixelArt } from "../components/PixelArt";
import { BrandNav } from "../components/BrandNav";
import { NodeMotif } from "../components/NodeMotif";
import { ROBOT_BLACK, ROBOT_ORANGE } from "../lib/pixelMaps";
import "../styles/scene.css";
import "./auth.css";

interface SignupProps {
  onSkip?: () => void;
  onSignup?: () => void;
  onLogin?: () => void;
}

export function Signup({ onSkip, onSignup, onLogin }: SignupProps) {
  const [form, setForm] = useState({ nickname: "", email: "", password: "", confirm: "" });

  const update = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((prev) => ({ ...prev, [key]: e.target.value }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSignup?.();
  };

  return (
    <section className="sc-scene">
      <NodeMotif />
      <BrandNav
        action={
          <button className="sc-skip" type="button" onClick={onSkip}>
            건너뛰기
          </button>
        }
      />

      <main className="auth__center">
        <h1 className="auth__title auth__enter auth__enter--1">계정 만들기</h1>
        <p className="auth__subtitle auth__enter auth__enter--2">
          30초면 첫 스킬을 쌓기 시작할 수 있어요.
        </p>

        <form className="auth__card auth__enter auth__enter--3" onSubmit={handleSubmit}>
          <PixelArt
            sprite={ROBOT_ORANGE}
            label="SkillCanvas 마스코트"
            className="auth__cardMascot"
          />
          <h2 className="auth__cardTitle">회원가입</h2>

          <input
            className="auth__input"
            type="text"
            placeholder="닉네임"
            value={form.nickname}
            onChange={update("nickname")}
            autoComplete="nickname"
          />
          <input
            className="auth__input"
            type="email"
            placeholder="이메일"
            value={form.email}
            onChange={update("email")}
            autoComplete="email"
          />
          <input
            className="auth__input"
            type="password"
            placeholder="비밀번호"
            value={form.password}
            onChange={update("password")}
            autoComplete="new-password"
          />
          <input
            className="auth__input"
            type="password"
            placeholder="비밀번호 확인"
            value={form.confirm}
            onChange={update("confirm")}
            autoComplete="new-password"
          />

          <button className="auth__submit" type="submit">
            가입하기
          </button>

          <button className="auth__alt" type="button" onClick={onLogin}>
            이미 계정이 있나요? <span className="auth__altAccent">로그인 →</span>
          </button>
        </form>
      </main>

      <div className="auth__buddy" aria-hidden="true">
        <PixelArt sprite={ROBOT_BLACK} className="auth__buddyArt" />
        <span className="auth__buddyShadow" />
      </div>
    </section>
  );
}
