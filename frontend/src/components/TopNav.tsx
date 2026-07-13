import { useEffect, useRef, useState } from "react";
import { useClerk } from "@clerk/clerk-react";
import { PixelArt } from "./PixelArt";
import { BLOCK_MARK, ROBOT_MUTED } from "../lib/pixelMaps";
import "./TopNav.css";

export type NavTab = "START" | "SKILL" | "AUTO-FLOW" | "MY WORLD" | "SHARE";

const TABS: NavTab[] = ["START", "SKILL", "AUTO-FLOW", "MY WORLD", "SHARE"];

const NICK_KEY = "sc_nickname";

function loadNickname(): string {
  try {
    return localStorage.getItem(NICK_KEY) || "teamd";
  } catch {
    return "teamd";
  }
}

interface TopNavProps {
  active?: NavTab;
  onNavigate?: (tab: NavTab) => void;
}

export function TopNav({ active, onNavigate }: TopNavProps) {
  const { signOut } = useClerk();
  const [nickname, setNickname] = useState(loadNickname);
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState(nickname);
  const profileRef = useRef<HTMLDivElement>(null);

  // 바깥 클릭 / Esc 로 닫기
  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const toggle = () => {
    setDraft(nickname);
    setOpen((v) => !v);
  };

  const trimmed = draft.trim();
  const valid = trimmed.length >= 2 && trimmed.length <= 20;
  const changed = trimmed !== nickname;

  const save = () => {
    if (!valid || !changed) return;
    // TODO: 백엔드 연결 시 PATCH /users/me { nickname } (중복 409 처리)
    setNickname(trimmed);
    try {
      localStorage.setItem(NICK_KEY, trimmed);
    } catch {
      /* 무시 */
    }
    setOpen(false);
  };

  return (
    <header className="nav">
      <button className="nav__brand" type="button" onClick={() => onNavigate?.("START")}>
        <PixelArt sprite={BLOCK_MARK} className="nav__mark" />
        <span className="nav__logo">SkillCanvas</span>
      </button>

      <nav className="nav__tabs">
        {TABS.map((tab) => (
          <button
            key={tab}
            type="button"
            className={tab === active ? "nav__tab nav__tab--active" : "nav__tab"}
            onClick={() => onNavigate?.(tab)}
          >
            {tab}
          </button>
        ))}
      </nav>

      <div className="nav__profile" ref={profileRef}>
        <button
          className="nav__avatar"
          type="button"
          aria-haspopup="dialog"
          aria-expanded={open}
          aria-label="내 프로필"
          onClick={toggle}
        >
          <PixelArt sprite={ROBOT_MUTED} className="nav__avatarArt" />
        </button>

        {open && (
          <div className="nav__pop" role="dialog" aria-label="프로필">
            <div className="nav__popHead">
              <span className="nav__popAvatar">
                <PixelArt sprite={ROBOT_MUTED} className="nav__avatarArt" />
              </span>
              <span className="nav__popNick">@{nickname}</span>
            </div>

            <label className="nav__popField">
              닉네임
              <input
                className="nav__popInput"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && save()}
                maxLength={20}
                autoFocus
              />
            </label>
            <p className={valid || !trimmed ? "nav__popHint" : "nav__popHint nav__popHint--err"}>
              2~20자로 지어주세요
            </p>

            <button
              className="nav__popSave"
              type="button"
              onClick={save}
              disabled={!valid || !changed}
            >
              저장
            </button>
            <button
              className="nav__popLogout"
              type="button"
              onClick={() => signOut({ redirectUrl: "/" })}
            >
              로그아웃
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
