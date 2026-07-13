import { useState } from "react";
import { PixelArt } from "../components/PixelArt";
import { BrandNav } from "../components/BrandNav";
import { NodeMotif } from "../components/NodeMotif";
import { ROBOT_BLACK, ROBOT_ORANGE } from "../lib/pixelMaps";
import "../styles/scene.css";
import "./Login.css";

interface LoginProps {
  onSkip?: () => void;
  onLogin?: () => void;
  onSignup?: () => void;
}

export function Login({ onSkip, onLogin, onSignup }: LoginProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onLogin?.();
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

      <main className="lg__center">
        <h1 className="lg__title lg__enter lg__enter--1">만나서 반가워요</h1>
        <p className="lg__subtitle lg__enter lg__enter--2">로그인하고 블록을 쌓아볼까요?</p>

        <form className="lg__card lg__enter lg__enter--3" onSubmit={handleSubmit}>
          <PixelArt sprite={ROBOT_ORANGE} label="SkillCanvas 마스코트" className="lg__cardMascot" />
          <h2 className="lg__cardTitle">로그인</h2>

          <input
            className="lg__input"
            type="email"
            placeholder="이메일"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
          />
          <input
            className="lg__input"
            type="password"
            placeholder="비밀번호"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />

          <button className="lg__submit" type="submit">
            로그인
          </button>

          <button className="lg__signup" type="button" onClick={onSignup}>
            처음이신가요? <span className="lg__signupAccent">신규 계정 등록 →</span>
          </button>
        </form>
      </main>

      <div className="lg__buddy" aria-hidden="true">
        <PixelArt sprite={ROBOT_BLACK} className="lg__buddyArt" />
        <span className="lg__buddyShadow" />
      </div>
    </section>
  );
}
