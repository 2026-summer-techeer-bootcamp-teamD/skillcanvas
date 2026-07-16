import { useEffect, useState } from "react";
import type { ToolCatalogItem } from "../lib/toolCatalog";
import "./PublishModal.css"; // 스크림·카드 스타일 재사용
import "./KeyModal.css"; // 발급 절차 안내·필드 힌트

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
  const [values, setValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setValues({});
      setError(null);
      setSaving(false);
    }
  }, [open]);

  if (!open) return null;

  const meta = tool?.metadata_json ?? null;
  const name = tool?.name ?? toolKey;

  // 입력칸 목록. fields가 있으면 그대로, 없으면 예전 단일 field 형식으로 폴백.
  const fields = meta?.fields?.length
    ? meta.fields
    : [{ name: meta?.field ?? "API 키", placeholder: meta?.placeholder, help: meta?.help }];

  // 붙여넣을 게 없는 건 key_required로만 판단한다.
  // auth_owner는 '누가 발급하는가'(developer=개발자/관리자 발급)이지 '안 넣어도 된다'가 아니다.
  // discord·telegram이 developer면서 봇 토큰이 필요한데, 예전 로직은 이걸 '키 불필요'로 처리해
  // 입력칸을 아예 안 그렸다 → 모달로는 토큰을 넣을 방법이 없었다.
  const noKeyNeeded = tool !== null && !tool.key_required;

  const filled = fields.every((f) => (values[f.name] ?? "").trim());

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!filled) return;
    setSaving(true);
    setError(null);
    try {
      // 칸이 하나면 값 그대로, 여러 개면 JSON으로 묶는다.
      // 실행기(core/mcp.py)가 두 형식을 다 읽는다.
      const secret =
        fields.length === 1
          ? values[fields[0].name].trim()
          : JSON.stringify(Object.fromEntries(fields.map((f) => [f.name, values[f.name].trim()])));
      await onSave(secret);
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

            {/* 발급 절차. 링크만 던지면 어디서 뭘 눌러야 하는지 몰라 헤맨다. */}
            {meta?.guide?.length ? (
              <ol className="key__guide">
                {meta.guide.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ol>
            ) : null}

            {tool?.key_issue_url && (
              <p className="pub__optional">
                <a href={tool.key_issue_url} target="_blank" rel="noreferrer">
                  발급하러 가기 →
                </a>
              </p>
            )}

            {fields.map((f, i) => (
              <label className="pub__field" key={f.name}>
                {/* 환경변수 원문(MCP_EMAIL_ADDRESS)이 그대로 보이면 사용자에겐 암호문이다 */}
                {f.label ?? f.name}
                <input
                  className="pub__input"
                  value={values[f.name] ?? ""}
                  onChange={(e) => setValues((v) => ({ ...v, [f.name]: e.target.value }))}
                  placeholder={f.placeholder ?? "값을 붙여넣으세요"}
                  autoFocus={i === 0}
                />
                {f.help && <span className="key__hint">{f.help}</span>}
              </label>
            ))}

            {error && <p className="pub__optional">{error}</p>}
            <div className="pub__actions">
              <button className="pub__ghost" type="button" onClick={onClose}>
                취소
              </button>
              <button className="pub__primary" type="submit" disabled={!filled || saving}>
                {saving ? "저장 중…" : "로컬에 저장"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
