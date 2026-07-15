import { useEffect, useState } from "react";
import type { ToolCatalogItem } from "../lib/toolCatalog";
import "./PublishModal.css"; // 스크림·카드 스타일 재사용

interface KeyModalProps {
  open: boolean;
  /** 노드의 도구 키 (카탈로그 매칭 실패 시 폴백 표시) */
  toolKey: string;
  /** 카탈로그 매칭 결과 (없으면 폴백 입력) */
  tool: ToolCatalogItem | null;
  onClose: () => void;
  /** 저장 성공은 호출부에서 처리. 실패 시 throw하면 모달이 에러 표시 */
  onSave: (secret: string) => Promise<void>;
}

/**
 * MCP/API 키 붙여넣기 팝업.
 * GET /tool-catalog의 metadata_json(field·help·placeholder)·key_issue_url로 폼을 자동 구성.
 * 저장은 호출부가 로컬 실행기(POST /credential)로 넘긴다.
 */
export function KeyModal({ open, toolKey, tool, onClose, onSave }: KeyModalProps) {
  const [secret, setSecret] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setSecret("");
      setError(null);
      setSaving(false);
    }
  }, [open]);

  if (!open) return null;

  const meta = tool?.metadata_json ?? null;
  const name = tool?.name ?? toolKey;
  // 공용키(developer)거나 키 불필요면 붙여넣을 게 없음
  const noKeyNeeded = tool !== null && (tool.auth_owner === "developer" || !tool.key_required);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!secret.trim()) return;
    setSaving(true);
    setError(null);
    try {
      await onSave(secret.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : "키 저장 실패");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="pub__scrim" role="dialog" aria-modal="true">
      <div className="pub__card">
        <header className="pub__head">
          <h2 className="pub__title">{name} 키 연결</h2>
          <button className="pub__close" type="button" aria-label="닫기" onClick={onClose}>
            ×
          </button>
        </header>

        {noKeyNeeded ? (
          <>
            <p className="pub__optional">
              이 도구는 공용 키를 쓰거나 키가 필요 없어요. 따로 붙여넣지 않아도 실행돼요.
            </p>
            <div className="pub__actions">
              <button className="pub__primary" type="button" onClick={onClose}>
                확인
              </button>
            </div>
          </>
        ) : (
          <form onSubmit={handleSubmit}>
            {tool?.description && <p className="pub__optional">{tool.description}</p>}
            {tool?.key_issue_url && (
              <p className="pub__optional">
                <a href={tool.key_issue_url} target="_blank" rel="noreferrer">
                  여기서 발급 →
                </a>
              </p>
            )}
            <label className="pub__field">
              {meta?.field ?? "API 키"}
              <input
                className="pub__input"
                value={secret}
                onChange={(e) => setSecret(e.target.value)}
                placeholder={meta?.placeholder ?? "키를 붙여넣으세요"}
                autoFocus
              />
            </label>
            {meta?.help && <p className="pub__optional">{meta.help}</p>}
            {error && <p className="pub__optional">{error}</p>}
            <div className="pub__actions">
              <button className="pub__ghost" type="button" onClick={onClose}>
                취소
              </button>
              <button className="pub__primary" type="submit" disabled={!secret.trim() || saving}>
                {saving ? "저장 중…" : "로컬에 저장"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
