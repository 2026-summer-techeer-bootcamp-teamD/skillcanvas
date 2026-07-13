import { PixelArt } from "./PixelArt";
import { BLOCK_MARK } from "../lib/pixelMaps";

interface BrandNavProps {
  /** 우측 액션 (예: 건너뛰기). 없으면 표시 안 함. */
  action?: React.ReactNode;
  /** 로고 클릭 시. 없으면 홈("/") 링크. */
  onLogoClick?: () => void;
}

/** 상단 바 — 블록 로고 + SkillCanvas. 스플래시·온보딩·로그인 공용. */
export function BrandNav({ action, onLogoClick }: BrandNavProps) {
  return (
    <header className="sc-nav">
      <a className="sc-nav__logo" href="/" onClick={onLogoClick}>
        <PixelArt sprite={BLOCK_MARK} className="sc-nav__mark" />
        <span className="sc-nav__brand">SkillCanvas</span>
      </a>
      {action ? <div className="sc-nav__action">{action}</div> : null}
    </header>
  );
}
