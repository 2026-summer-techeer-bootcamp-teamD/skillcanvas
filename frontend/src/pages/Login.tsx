import { useState } from "react";
import { useSignIn } from "@clerk/clerk-react";
import { PixelArt } from "../components/PixelArt";
import { BrandNav } from "../components/BrandNav";
import { NodeMotif } from "../components/NodeMotif";
import { PermissionModal } from "../components/PermissionModal";
import { clerkErrorMessage } from "../lib/clerkError";
import { ROBOT_BLACK, ROBOT_ORANGE } from "../lib/pixelMaps";
import "../styles/scene.css";
import "./auth.css";

interface LoginProps {
  onSkip?: () => void;
  onEnter?: () => void;
  onSignup?: () => void;
}

export function Login({ onSkip, onEnter, onSignup }: LoginProps) {
  const { isLoaded, signIn, setActive } = useSignIn();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  // 로그인 성공 직후 로컬 실행기 권한 모달을 띄운다.
  const [permissionOpen, setPermissionOpen] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isLoaded || busy) return;
    setError("");
    setBusy(true);
    try {
      // 인증·세션·토큰(JWT)은 Clerk가 처리한다. 우리는 결과 상태만 본다.
      const res = await signIn.create({ identifier: email, password });
      if (res.status === "complete") {
        await setActive({ session: res.createdSessionId });
        setPermissionOpen(true);
      } else {
        setError("추가 인증이 필요한 계정이에요.");
      }
    } catch (err) {
      setError(clerkErrorMessage(err, "이메일 또는 비밀번호를 확인해 주세요."));
    } finally {
      setBusy(false);
    }
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
        <h1 className="auth__title auth__enter auth__enter--1">만나서 반가워요</h1>
        <p className="auth__subtitle auth__enter auth__enter--2">로그인하고 블록을 쌓아볼까요?</p>

        <form className="auth__card auth__enter auth__enter--3" onSubmit={handleSubmit}>
          <PixelArt
            sprite={ROBOT_ORANGE}
            label="SkillCanvas 마스코트"
            className="auth__cardMascot"
          />
          <h2 className="auth__cardTitle">로그인</h2>

          <input
            className="auth__input"
            type="email"
            placeholder="이메일"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
          />
          <input
            className="auth__input"
            type="password"
            placeholder="비밀번호"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />

          {error && <p className="auth__error">{error}</p>}

          <button className="auth__submit" type="submit" disabled={busy || !isLoaded}>
            {busy ? "확인 중…" : "로그인"}
          </button>

          <button className="auth__alt" type="button" onClick={onSignup}>
            처음이신가요? <span className="auth__altAccent">신규 계정 등록 →</span>
          </button>
        </form>
      </main>

      <div className="auth__buddy" aria-hidden="true">
        <PixelArt sprite={ROBOT_BLACK} className="auth__buddyArt" />
        <span className="auth__buddyShadow" />
      </div>

      <PermissionModal
        open={permissionOpen}
        onLater={() => setPermissionOpen(false)}
        onAllow={onEnter}
      />
    </section>
  );
}
