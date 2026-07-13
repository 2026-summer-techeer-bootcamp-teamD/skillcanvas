import { PixelArt } from "./PixelArt";
import { BLOCK_MARK } from "../lib/pixelMaps";
import "./TopNav.css";

export type NavTab = "START" | "SKILL" | "AUTO-FLOW" | "MY WORLD" | "SHARE";

const TABS: NavTab[] = ["START", "SKILL", "AUTO-FLOW", "MY WORLD", "SHARE"];

interface TopNavProps {
  active?: NavTab;
  onNavigate?: (tab: NavTab) => void;
}

export function TopNav({ active, onNavigate }: TopNavProps) {
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

      <div className="nav__avatar" aria-hidden="true">
        t
      </div>
    </header>
  );
}
