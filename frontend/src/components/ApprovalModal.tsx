import { PixelArt } from "./PixelArt";
import { ROBOT_ORANGE } from "../lib/pixelMaps";
import "./ApprovalModal.css";

interface ApprovalModalProps {
  open: boolean;
  message: string;
  busy?: boolean;
  onApprove: () => void;
  onClose: () => void;
}

/**
 * 승인 게이트 모달 — 워크플로우가 발송·기록 같은 되돌리기 어려운 단계 앞에서 멈추면
 * 별도 팝업으로 띄워 사용자 승인을 받는다. (PermissionModal과 동일 오버레이 패턴)
 */
export function ApprovalModal({ open, message, busy, onApprove, onClose }: ApprovalModalProps) {
  if (!open) {
    return null;
  }

  return (
    <div className="am__scrim" role="dialog" aria-modal="true" aria-labelledby="am-title">
      <div className="am__card">
        <header className="am__head">
          <PixelArt sprite={ROBOT_ORANGE} className="am__mascot" />
          <h2 className="am__title" id="am-title">
            승인이 필요해요
          </h2>
        </header>

        <p className="am__body">{message}</p>

        <p className="am__note">
          발송·기록처럼 되돌리기 어려운 단계 앞에서 한 번 멈춰요. 승인하면 이어서 실행돼요.
        </p>

        <div className="am__actions">
          <button className="am__cancel" type="button" onClick={onClose} disabled={busy}>
            나중에
          </button>
          <button className="am__approve" type="button" onClick={onApprove} disabled={busy}>
            {busy ? "처리 중…" : "승인하고 계속"}
          </button>
        </div>
      </div>
    </div>
  );
}
