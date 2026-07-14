import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { PixelArt } from "../components/PixelArt";
import { TopNav, type NavTab } from "../components/TopNav";
import { PublishModal, type PublishPayload } from "../components/PublishModal";
import { ROBOT_BLACK, ROBOT_ORANGE } from "../lib/pixelMaps";
import type { SkillBlock, SkillDraft, SkillNodeType } from "../lib/recommendSkill";
import { useApi, ApiError } from "../lib/api";
import { saveSkill, RunnerError } from "../lib/runner";
import "./Skill.css";

const EXAMPLES = [
  "슬랙메세지를 회의록으로 정리",
  "캘린더 일정 리마인드해주기",
  "CS 컴플레인 오면 배송조회해서 사과+쿠폰 발송",
];

const NODE_COLOR: Record<SkillNodeType, string> = {
  trigger: "var(--sc-node-trigger)",
  agent: "var(--sc-node-agent)",
  tool: "var(--sc-node-tool)",
  output: "var(--sc-node-output)",
  approve: "var(--sc-node-approve)",
};

interface ChatMessage {
  from: "user" | "ai";
  text: string;
}

const SEED_CHAT: ChatMessage[] = [
  { from: "user", text: "본문 요약을 3줄 이내로 더 짧게 해줘" },
  { from: "ai", text: "‘본문 요약’ 블록을 3줄 요약으로 바꿨어요. 원하면 더 줄일 수도 있어요." },
];

type Phase = "input" | "generating" | "result";

interface SkillProps {
  onNavigate?: (tab: NavTab) => void;
}

interface SkillNodeProps {
  block: SkillBlock;
  dragging: boolean;
  selected: boolean;
  onSelect: () => void;
  onDragStart: () => void;
  onDragEnter: () => void;
  onDragEnd: () => void;
}

function SkillNode({
  block,
  dragging,
  selected,
  onSelect,
  onDragStart,
  onDragEnter,
  onDragEnd,
}: SkillNodeProps) {
  const className = [
    "skill__node",
    dragging ? "skill__node--dragging" : "",
    selected ? "skill__node--selected" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={className}
      draggable
      onClick={onSelect}
      onDragStart={onDragStart}
      onDragEnter={onDragEnter}
      onDragEnd={onDragEnd}
      onDragOver={(e) => e.preventDefault()}
    >
      <span className="skill__nodeBar" style={{ background: NODE_COLOR[block.type] }} />
      <div className="skill__nodeText">
        <p className="skill__nodeTitle">{block.title}</p>
        <p className="skill__nodeMeta">
          {block.typeLabel} · <span className="skill__nodeTool">{block.meta}</span>
        </p>
        {selected && <p className="skill__nodeDesc">{block.desc}</p>}
      </div>
      <span className="skill__nodeHandle" aria-hidden="true">
        ⠿
      </span>
    </div>
  );
}

export function Skill({ onNavigate }: SkillProps) {
  const [phase, setPhase] = useState<Phase>("input");
  const [text, setText] = useState("");
  const [draft, setDraft] = useState<SkillDraft | null>(null);
  const [chat, setChat] = useState<ChatMessage[]>(SEED_CHAT);
  const [chatInput, setChatInput] = useState("");
  const [chatBusy, setChatBusy] = useState(false);
  // 드래그 중인 블록의 현재 위치 (끌면서 실시간으로 순서 재배치)
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  // 설명이 펼쳐진 블록 (클릭 토글)
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [publishOpen, setPublishOpen] = useState(false);
  // ── assemble API 연동 ────────────────────────────
  const call = useApi();
  const [genError, setGenError] = useState<string | null>(null);

  const TYPE_LABEL: Record<string, string> = {
    trigger: "트리거",
    agent: "에이전트",
    tool: "도구",
    approve: "승인",
    output: "출력",
  };

  // 블록 배열 → SKILL.md(content_md) 마크다운 문자열로 변환
  const blocksToMarkdown = (d: SkillDraft): string => {
    const lines = [`# ${d.name}`, "", d.summary, "", "## 블록"];
    d.blocks.forEach((b, i) => {
      lines.push(`${i + 1}. **${b.title}** (${b.typeLabel} · ${b.meta})`);
      if (b.desc) {
        lines.push(`   - ${b.desc}`);
      }
    });
    return lines.join("\n");
  };

  // 저장 = content_md(SKILL.md)에 폼 값을 합쳐 POST /skills
  const handlePublish = async (payload: PublishPayload) => {
    if (!draft) return;
    await call("/skills", {
      method: "POST",
      json: { ...payload, content_md: blocksToMarkdown(draft) },
    });
  };

  // 로컬 동기화 = 내 .claude/SKILL.md 로 저장 (본문 보존, POST /save)
  const slugify = (s: string) =>
    s
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9가-힣]+/g, "-")
      .replace(/^-|-$/g, "") || "skill";

  const handleSaveLocal = async () => {
    if (!draft) return;
    try {
      // allowed-tools = 카탈로그 MCP 키(used_mcps). 한글 노드 라벨이 아니라 실제 키여야
      // GET /graph에서 스킬→mcp 엣지가 생긴다.
      const tools = draft.mcps ?? [];
      const description = draft.source?.trim() || draft.summary;
      // 조립한 블록을 마크다운 본문으로 함께 저장(러너 /save body)
      await saveSkill(slugify(draft.name), draft.name, description, tools, blocksToMarkdown(draft));
      alert("로컬 .claude에 저장됐어요.");
    } catch (e) {
      alert(e instanceof RunnerError ? e.message : "로컬 저장 실패");
    }
  };
  const reorder = (from: number, to: number) => {
    setDraft((prev) => {
      if (!prev) return prev;
      const blocks = [...prev.blocks];
      const [moved] = blocks.splice(from, 1);
      blocks.splice(to, 0, moved);
      return { ...prev, blocks };
    });
  };

  const handleDragEnter = (index: number) => {
    if (dragIndex === null || dragIndex === index) return;
    reorder(dragIndex, index);
    setDragIndex(index);
  };

  const generate = async (prompt: string) => {
    if (!prompt.trim()) return;
    setPhase("generating");
    setGenError(null);
    try {
      // POST /assemble — 자연어를 노드(블록)로 조립 (명세 3-1)
      const data = await call<{
        name: string;
        nodes: { id: string; type: string; label: string; detail: string | null }[];
        used_mcps: string[];
      }>("/assemble", { method: "POST", json: { text: prompt, target: "skill" } });

      const blocks: SkillBlock[] = data.nodes.map((n) => ({
        id: n.id,
        type: n.type as SkillNodeType,
        typeLabel: TYPE_LABEL[n.type] ?? n.type,
        title: n.label,
        meta: n.detail || "-", // 블록별 자기 도구/힌트(detail). 스킬 전체 목록 아님
        desc: n.detail ?? "",
      }));

      setDraft({
        name: data.name,
        summary: `${data.nodes.length}개 블록으로 조립했어요.`,
        blocks,
        mcps: data.used_mcps ?? [],
        source: prompt,
      });
      setPhase("result");
    } catch (e) {
      setGenError(e instanceof ApiError ? e.message : "생성 실패");
      setPhase("input");
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    generate(text);
  };

  // Create에서 입력 텍스트를 들고 오면 히어로를 건너뛰고 바로 생성.
  const location = useLocation();
  const kickedOff = useRef(false);
  useEffect(() => {
    const initial = (location.state as { text?: string } | null)?.text;
    if (initial && !kickedOff.current) {
      kickedOff.current = true;
      setText(initial);
      generate(initial);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.state]);

  // AI 편집 = 선택 블록 + 지시문 → POST /map-node → 응답 노드로 그 블록 갱신 (명세 3-3)
  const sendChat = async (e: React.FormEvent) => {
    e.preventDefault();
    const instruction = chatInput.trim();
    if (!instruction || chatBusy || !draft) return;

    const target = draft.blocks.find((b) => b.id === selectedId);
    if (!target) {
      setChat((prev) => [
        ...prev,
        { from: "user", text: instruction },
        { from: "ai", text: "먼저 왼쪽에서 수정할 블록을 클릭해 주세요." },
      ]);
      setChatInput("");
      return;
    }

    setChat((prev) => [...prev, { from: "user", text: instruction }]);
    setChatInput("");
    setChatBusy(true);
    try {
      const data = await call<{
        node: { type: string; label: string; detail: string | null };
        mcp_added: string | null;
      }>("/map-node", {
        method: "POST",
        json: {
          node: { type: target.type, label: target.title, detail: target.desc || null },
          instruction,
        },
      });
      setDraft((prev) =>
        prev
          ? {
              ...prev,
              blocks: prev.blocks.map((b) =>
                b.id === target.id
                  ? {
                      ...b,
                      type: data.node.type as SkillNodeType,
                      typeLabel: TYPE_LABEL[data.node.type] ?? data.node.type,
                      title: data.node.label,
                      meta: data.node.detail || "-",
                      desc: data.node.detail ?? "",
                    }
                  : b,
              ),
              // 새로 필요해진 도구는 mcps에 반영(로컬 저장 allowed-tools로 이어짐)
              mcps:
                data.mcp_added && !prev.mcps?.includes(data.mcp_added)
                  ? [...(prev.mcps ?? []), data.mcp_added]
                  : prev.mcps,
            }
          : prev,
      );
      setChat((prev) => [
        ...prev,
        {
          from: "ai",
          text: `'${data.node.label}'(으)로 바꿨어요.${
            data.mcp_added ? ` ${data.mcp_added} 도구를 추가했어요.` : ""
          }`,
        },
      ]);
    } catch (err) {
      setChat((prev) => [
        ...prev,
        {
          from: "ai",
          text: err instanceof ApiError ? `에러: ${err.message}` : "수정에 실패했어요.",
        },
      ]);
    } finally {
      setChatBusy(false);
    }
  };

  const selectedBlock = draft?.blocks.find((b) => b.id === selectedId) ?? null;

  return (
    <div className="skill">
      <TopNav active="SKILL" onNavigate={onNavigate} />

      {phase !== "result" ? (
        <main className="skill__hero">
          <div className="skill__mascots" aria-hidden="true">
            <PixelArt sprite={ROBOT_BLACK} className="skill__mascot skill__mascot--1" />
            <PixelArt sprite={ROBOT_ORANGE} className="skill__mascot skill__mascot--2" />
            <PixelArt sprite={ROBOT_BLACK} className="skill__mascot skill__mascot--3" />
          </div>

          {phase === "generating" ? (
            <p className="skill__loading">블록을 쌓는 중…</p>
          ) : (
            <>
              <span className="skill__badge">✦ 자동화 생성</span>
              <h1 className="skill__title">어떤 스킬을 만들어 볼까요?</h1>
              <p className="skill__subtitle">
                하고 싶은 일을 문장으로 적으면, 워크플로우 노드로 조립해 드려요.
              </p>

              <form className="skill__inputRow" onSubmit={handleSubmit}>
                <input
                  className="skill__input"
                  placeholder="예: CS 컴플레인 오면 배송조회해서 사과+쿠폰 발송"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                />
                <button className="skill__go" type="submit">
                  입력
                </button>
              </form>

              <div className="skill__examples">
                {EXAMPLES.map((ex) => (
                  <button
                    key={ex}
                    type="button"
                    className="skill__example"
                    onClick={() => {
                      setText(ex);
                      generate(ex);
                    }}
                  >
                    📮 {ex}
                  </button>
                ))}
              </div>
            </>
          )}
        </main>
      ) : (
        <div className="skill__work">
          <main className="skill__canvas">
            <span className="skill__resultBadge">✦ SKILL</span>
            <h1 className="skill__resultTitle">{draft?.name}</h1>
            <p className="skill__resultSummary">{draft?.summary}</p>
            <p className="skill__resultHint">블록을 클릭하면 설명이 열려요 · 끌어서 순서 변경</p>

            <div className="skill__stack">
              {draft?.blocks.map((block, i) => (
                <SkillNode
                  key={block.id}
                  block={block}
                  dragging={dragIndex === i}
                  selected={selectedId === block.id}
                  onSelect={() => setSelectedId((prev) => (prev === block.id ? null : block.id))}
                  onDragStart={() => setDragIndex(i)}
                  onDragEnter={() => handleDragEnter(i)}
                  onDragEnd={() => setDragIndex(null)}
                />
              ))}
              <button className="skill__addBlock" type="button">
                + 블록 추가
              </button>
            </div>
          </main>

          <aside className="skill__chatPanel">
            <header className="skill__chatHead">
              <span className="skill__chatDot" />
              <strong>AI 편집</strong>
              <span className="skill__chatHint">
                {selectedBlock ? `· '${selectedBlock.title}' 편집 중` : "· 블록을 클릭해 고치기"}
              </span>
            </header>

            <div className="skill__chatLog">
              {chat.map((msg, i) => (
                <div key={i} className={`skill__bubble skill__bubble--${msg.from}`}>
                  {msg.text}
                </div>
              ))}
            </div>

            <div className="skill__chatChips">
              <button
                type="button"
                className="skill__chip"
                onClick={() => setChatInput("이 블록을 더 짧게 요약해줘")}
              >
                더 짧게 요약
              </button>
              <button
                type="button"
                className="skill__chip"
                onClick={() => setChatInput("이 단계를 슬랙 대신 노션으로 바꿔줘")}
              >
                도구 바꾸기
              </button>
            </div>

            <form className="skill__chatInputRow" onSubmit={sendChat}>
              <input
                className="skill__chatInput"
                placeholder={
                  chatBusy
                    ? "고치는 중…"
                    : selectedBlock
                      ? "고치고 싶은 걸 말해보세요"
                      : "블록을 먼저 클릭"
                }
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                disabled={chatBusy}
              />
              <button
                className="skill__chatSend"
                type="submit"
                aria-label="보내기"
                disabled={chatBusy || !chatInput.trim()}
              >
                ↑
              </button>
            </form>
            {genError && <p className="skill__subtitle">에러: {genError}</p>}

            <button className="skill__run" type="button" onClick={() => setPublishOpen(true)}>
              ▶ 실행 / 저장
            </button>
            <button className="skill__run" type="button" onClick={handleSaveLocal}>
              💾 로컬에 저장
            </button>
          </aside>
        </div>
      )}

      <PublishModal
        open={publishOpen}
        kind="skill"
        defaultName={draft?.name ?? "새 스킬"}
        onClose={() => setPublishOpen(false)}
        onPublish={handlePublish}
      />
    </div>
  );
}
