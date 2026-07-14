import { useEffect, useState } from "react";
import "./PublishModal.css";

/** WorkflowCreate / SkillCreate 요청 바디와 1:1 대응 (graph_json·content_md는 페이지에서 합침) */
export interface PublishPayload {
  name: string;
  description: string | null;
  tags: string[];
  is_public: boolean;
}

interface PublishModalProps {
  open: boolean;
  /** "skill" | "workflow" — 문구만 달라짐 */
  kind: "skill" | "workflow";
  defaultName: string;
  onClose: () => void;
  onPublish: (payload: PublishPayload) => void | Promise<void>;
  }
const MAX_TAGS = 5;

export function PublishModal({ open, kind, defaultName, onClose, onPublish }: PublishModalProps) {
  const [name, setName] = useState(defaultName);
  const [description, setDescription] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState("");
  const [isPublic, setIsPublic] = useState(true);
  const [done, setDone] = useState<null | { name: string; isPublic: boolean }>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 열릴 때마다 AI 이름을 기본값으로 다시 채운다.
  useEffect(() => {
    if (open) {
      setName(defaultName);
      setDescription("");
      setTags([]);
      setTagInput("");
      setIsPublic(true);
      setDone(null);
      setError(null);
      setSubmitting(false);
    }
  }, [open, defaultName]);

  if (!open) {
    return null;
  }

  const noun = kind === "skill" ? "스킬" : "워크플로우";

  const addTag = () => {
    const t = tagInput.trim().replace(/^#/, "");
    if (!t || tags.includes(t) || tags.length >= MAX_TAGS) {
      setTagInput("");
      return;
    }
    setTags((prev) => [...prev, t]);
    setTagInput("");
  };

  const handleTagKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addTag();
    } else if (e.key === "Backspace" && !tagInput && tags.length) {
      setTags((prev) => prev.slice(0, -1));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;
    setSubmitting(true);
    setError(null);
    try {
      await onPublish({
        name: trimmed,
        description: description.trim() || null,
        tags,
        is_public: isPublic,
      });
      setDone({ name: trimmed, isPublic });
    } catch (err) {
      setError(err instanceof Error ? err.message : "저장에 실패했어요");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="pub__scrim" role="dialog" aria-modal="true" aria-labelledby="pub-title">
      <div className="pub__card">
        {done ? (
          <div className="pub__done">
            <p className="pub__doneMark" aria-hidden="true">
              ✓
            </p>
            <p className="pub__doneTitle">
              {done.isPublic ? "갤러리에 발행됐어요" : "내 세계에 저장됐어요"}
            </p>
            <p className="pub__doneName">{done.name}</p>
            <button className="pub__primary" type="button" onClick={onClose}>
              확인
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <header className="pub__head">
              <h2 className="pub__title" id="pub-title">
                {noun} 저장
              </h2>
              <button className="pub__close" type="button" aria-label="닫기" onClick={onClose}>
                ×
              </button>
            </header>

            <label className="pub__field">
              이름
              <input
                className="pub__input"
                value={name}
                onChange={(e) => setName(e.target.value)}
                maxLength={200}
                placeholder={`${noun} 이름`}
                autoFocus
              />
            </label>

            <label className="pub__field">
              설명 <span className="pub__optional">(선택)</span>
              <textarea
                className="pub__textarea"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                maxLength={500}
                placeholder="어떤 걸 하는지 한두 줄로 적어주세요"
              />
            </label>

            <div className="pub__field">
              태그 <span className="pub__optional">(최대 {MAX_TAGS}개)</span>
              <div className="pub__tags">
                {tags.map((t) => (
                  <span className="pub__tag" key={t}>
                    #{t}
                    <button
                      type="button"
                      aria-label={`${t} 삭제`}
                      onClick={() => setTags((prev) => prev.filter((x) => x !== t))}
                    >
                      ×
                    </button>
                  </span>
                ))}
                {tags.length < MAX_TAGS && (
                  <input
                    className="pub__tagInput"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyDown={handleTagKey}
                    onBlur={addTag}
                    placeholder={tags.length ? "" : "태그 입력 후 Enter"}
                  />
                )}
              </div>
            </div>

            <button
              type="button"
              className="pub__toggle"
              role="switch"
              aria-checked={isPublic}
              onClick={() => setIsPublic((v) => !v)}
            >
              <span className={isPublic ? "pub__switch pub__switch--on" : "pub__switch"}>
                <span className="pub__knob" />
              </span>
              <span className="pub__toggleText">
                <strong>갤러리에 공개</strong>
                <span className="pub__toggleHint">
                  {isPublic ? "누구나 갤러리에서 가져갈 수 있어요" : "나만 보기로 저장돼요"}
                </span>
              </span>
            </button>

            {error && <p className="pub__optional">{error}</p>}

            <div className="pub__actions">
              <button className="pub__ghost" type="button" onClick={onClose}>
                취소
              </button>
              <button className="pub__primary" type="submit" disabled={!name.trim() || submitting}>
                {submitting ? "저장 중…" : isPublic ? "발행" : "저장"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
