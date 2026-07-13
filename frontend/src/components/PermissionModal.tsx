import { PixelArt } from "./PixelArt";
import { ROBOT_BLACK } from "../lib/pixelMaps";
import "./PermissionModal.css";

const PERMISSIONS = [
  "로컬 파일 읽기·쓰기 (워크플로우 실행)",
  "백그라운드 실행 및 알림 표시",
  "포털 실행기 설치 (약 42 MB)",
];

interface PermissionModalProps {
  open: boolean;
  onLater?: () => void;
  onAllow?: () => void;
}

export function PermissionModal({ open, onLater, onAllow }: PermissionModalProps) {
  if (!open) {
    return null;
  }

  return (
    <div className="pm__scrim" role="dialog" aria-modal="true" aria-labelledby="pm-title">
      <div className="pm__card">
        <header className="pm__head">
          <PixelArt sprite={ROBOT_BLACK} className="pm__mascot" />
          <h2 className="pm__title" id="pm-title">
            실행 준비가 필요해요
          </h2>
        </header>

        <p className="pm__body">
          SkillCanvas가 자동화를 실행하려면 로컬 컴퓨터 사용 권한과{" "}
          <span className="pm__bodyAccent">실행기 설치</span>가 필요해요.
        </p>

        <ul className="pm__list">
          {PERMISSIONS.map((item) => (
            <li className="pm__item" key={item}>
              <span className="pm__arrow" aria-hidden="true">
                ▸
              </span>
              {item}
            </li>
          ))}
        </ul>

        <p className="pm__note">⚠ 권한은 설정에서 언제든 회수할 수 있어요.</p>

        <div className="pm__actions">
          <button className="pm__later" type="button" onClick={onLater}>
            나중에
          </button>
          <button className="pm__allow" type="button" onClick={onAllow}>
            허용하고 설치
          </button>
        </div>
      </div>
    </div>
  );
}
