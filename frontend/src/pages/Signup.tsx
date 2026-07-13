import { useState } from "react";
import { useSignUp } from "@clerk/clerk-react";
import { PixelArt } from "../components/PixelArt";
import { BrandNav } from "../components/BrandNav";
import { NodeMotif } from "../components/NodeMotif";
import { clerkErrorMessage } from "../lib/clerkError";
import { ROBOT_BLACK, ROBOT_ORANGE } from "../lib/pixelMaps";
import "../styles/scene.css";
import "./auth.css";

interface SignupProps {
  onSkip?: () => void;
  onSignup?: () => void;
  onLogin?: () => void;
}

export function Signup({ onSkip, onSignup, onLogin }: SignupProps) {
  const { isLoaded, signUp, setActive } = useSignUp();
  const [form, setForm] = useState({ nickname: "", email: "", password: "", confirm: "" });
  // "form" = 가입정보 입력, "verify" = 이메일로 온 인증코드 입력
  const [step, setStep] = useState<"form" | "verify">("form");
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const update = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((prev) => ({ ...prev, [key]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isLoaded || busy) return;
    setError("");
    if (form.password !== form.confirm) {
      setError("비밀번호가 서로 달라요.");
      return;
    }
    setBusy(true);
    try {
      // 닉네임은 우리 DB용 → Clerk 메타데이터에 실어 보낸다.
      await signUp.create({
        emailAddress: form.email,
        password: form.password,
        unsafeMetadata: { nickname: form.nickname },
      });
      // 이메일로 인증코드 발송 → verify 단계로.
      await signUp.prepareEmailAddressVerification({ strategy: "email_code" });
      setStep("verify");
    } catch (err) {
      setError(clerkErrorMessage(err, "가입에 실패했어요. 입력값을 확인해 주세요."));
    } finally {
      setBusy(false);
    }
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isLoaded || busy) return;
    setError("");
    setBusy(true);
    try {
      const res = await signUp.attemptEmailAddressVerification({ code });
      if (res.status === "complete") {
        await setActive({ session: res.createdSessionId });
        onSignup?.();
      } else {
        setError("인증이 완료되지 않았어요. 코드를 다시 확인해 주세요.");
      }
    } catch (err) {
      setError(clerkErrorMessage(err, "인증코드가 올바르지 않아요."));
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
        {step === "form" ? (
          <>
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

              {error && <p className="auth__error">{error}</p>}

              {/* Clerk 봇 방지(보이지 않는 캡차)용 마운트 지점 */}
              <div id="clerk-captcha" />

              <button className="auth__submit" type="submit" disabled={busy || !isLoaded}>
                {busy ? "만드는 중…" : "가입하기"}
              </button>

              <button className="auth__alt" type="button" onClick={onLogin}>
                이미 계정이 있나요? <span className="auth__altAccent">로그인 →</span>
              </button>
            </form>
          </>
        ) : (
          <>
            <h1 className="auth__title auth__enter auth__enter--1">이메일을 확인해 주세요</h1>
            <p className="auth__subtitle auth__enter auth__enter--2">
              {form.email} 로 보낸 인증코드를 입력하면 끝이에요.
            </p>

            <form className="auth__card auth__enter auth__enter--3" onSubmit={handleVerify}>
              <PixelArt
                sprite={ROBOT_ORANGE}
                label="SkillCanvas 마스코트"
                className="auth__cardMascot"
              />
              <h2 className="auth__cardTitle">인증코드</h2>

              <input
                className="auth__input"
                type="text"
                inputMode="numeric"
                placeholder="메일로 받은 6자리 코드"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                autoFocus
              />

              {error && <p className="auth__error">{error}</p>}

              <button className="auth__submit" type="submit" disabled={busy || !isLoaded}>
                {busy ? "확인 중…" : "인증하고 시작하기"}
              </button>

              <button className="auth__alt" type="button" onClick={() => setStep("form")}>
                ← 정보 다시 입력
              </button>
            </form>
          </>
        )}
      </main>

      <div className="auth__buddy" aria-hidden="true">
        <PixelArt sprite={ROBOT_BLACK} className="auth__buddyArt" />
        <span className="auth__buddyShadow" />
      </div>
    </section>
  );
}
