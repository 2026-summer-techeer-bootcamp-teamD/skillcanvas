import { useEffect, useRef, useState } from "react";
import { useClerk } from "@clerk/clerk-react";
import { PixelArt } from "./PixelArt";
import { ROBOT_BLACK, ROBOT_MUTED } from "../lib/pixelMaps";
import { ApiError, useApi } from "../lib/api";
import "./TopNav.css";

interface UserMe {
  id: number;
  clerk_user_id: string;
  nickname: string;
  created_at: string;
  updated_at: string;
}

export type NavTab = "START" | "CREATE" | "SKILL" | "AUTO-FLOW" | "MY WORLD" | "SHARE";

const TABS: NavTab[] = ["START", "CREATE", "SKILL", "AUTO-FLOW", "MY WORLD", "SHARE"];

// SKILL·AUTO-FLOW 탭은 그 편집 페이지에 있을 때만 활성. 그 외(Create 등)에선 비활성.
// = Create에서 선택해 페이지로 들어가야 그 탭이 켜진다.
function isTabDisabled(tab: NavTab, active?: NavTab): boolean {
  if (tab === "SKILL" || tab === "AUTO-FLOW") return tab !== active;
  return false;
}

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
  /** 닉네임이 조회/수정으로 바뀔 때마다 호출 — TopNav를 감싸는 페이지가 자체 상태(예: 프로필 보드)를 동기화할 때 씀 */
  onNicknameChange?: (nickname: string) => void;
}

export function TopNav({ active, onNavigate, onNicknameChange }: TopNavProps) {
  const { signOut } = useClerk();
  const call = useApi();
  const [nickname, setNickname] = useState(loadNickname);
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState(nickname);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const profileRef = useRef<HTMLDivElement>(null);

  // 내 프로필 조회 (GET /users/me) — 첫 로그인이면 백엔드가 자동 생성해서 반환
  useEffect(() => {
    let cancelled = false;
    call<UserMe>("/users/me")
      .then((me) => {
        if (cancelled) return;
        setNickname(me.nickname);
        onNicknameChange?.(me.nickname);
        try {
          localStorage.setItem(NICK_KEY, me.nickname);
        } catch {
          /* 무시 */
        }
      })
      .catch(() => {
        /* 실패 시 로컬 캐시 닉네임 유지 */
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [call]);

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
    setError(null);
    setOpen((v) => !v);
  };

  const trimmed = draft.trim();
  const valid = trimmed.length >= 2 && trimmed.length <= 20;
  const changed = trimmed !== nickname;

  const save = async () => {
    if (!valid || !changed || saving) return;
    setSaving(true);
    setError(null);
    try {
      const me = await call<UserMe>("/users/me", { method: "PATCH", json: { nickname: trimmed } });
      setNickname(me.nickname);
      onNicknameChange?.(me.nickname);
      try {
        localStorage.setItem(NICK_KEY, me.nickname);
      } catch {
        /* 무시 */
      }
      setOpen(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "닉네임 저장에 실패했습니다");
    } finally {
      setSaving(false);
    }
  };

  return (
    <header className="nav">
      <button className="nav__brand" type="button" onClick={() => onNavigate?.("START")}>
        <PixelArt sprite={ROBOT_BLACK} className="nav__mark" />
        <span className="nav__logo">SkillCanvas</span>
      </button>

      <nav className="nav__tabs">
        {TABS.map((tab) => {
          const disabled = isTabDisabled(tab, active);
          const cls = [
            "nav__tab",
            tab === active ? "nav__tab--active" : "",
            disabled ? "nav__tab--disabled" : "",
          ]
            .filter(Boolean)
            .join(" ");
          return (
            <button
              key={tab}
              type="button"
              className={cls}
              disabled={disabled}
              aria-disabled={disabled}
              onClick={() => !disabled && onNavigate?.(tab)}
            >
              {tab}
            </button>
          );
        })}
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
                onChange={(e) => {
                  setDraft(e.target.value);
                  setError(null);
                }}
                onKeyDown={(e) => e.key === "Enter" && save()}
                maxLength={20}
                autoFocus
              />
            </label>
            <p
              className={
                error || (!valid && trimmed) ? "nav__popHint nav__popHint--err" : "nav__popHint"
              }
            >
              {error ?? "2~20자로 지어주세요"}
            </p>

            <button
              className="nav__popSave"
              type="button"
              onClick={save}
              disabled={!valid || !changed || saving}
            >
              {saving ? "저장 중…" : "저장"}
            </button>
            <button
              className="nav__popLogout"
              type="button"
              onClick={() => {
                // 계정 전환 후 재로그인 시 이전 계정 닉네임이 잠깐 보이지 않도록 캐시도 지운다
                try {
                  localStorage.removeItem(NICK_KEY);
                } catch {
                  /* 무시 */
                }
                signOut({ redirectUrl: "/" });
              }}
            >
              로그아웃
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
