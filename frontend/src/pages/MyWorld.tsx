import { useState } from "react";
import { useNavigate } from "react-router-dom";
import ReactFlow, { Background, BackgroundVariant, type Edge, type Node } from "reactflow";
import "reactflow/dist/style.css";
import { TopNav, type NavTab } from "../components/TopNav";
import { NodeTrail } from "../components/NodeTrail";
import { FlowNode } from "../components/flow/FlowNode";
import { getGraph, RunnerError, type RunnerGraph, type RunnerGraphNode } from "../lib/runner";
import { useApi, ApiError } from "../lib/api";
import { assembleToFlow, type AssembledNode, type FlowNodeData } from "../lib/flowData";
import "./MyWorld.css";

const nodeTypes = { flow: FlowNode };

const WORLDS = [
  { name: "My World", icon: "🌐" },
  { name: "Team-Growth", icon: "📈" },
  { name: "Team-Ops", icon: "🛠" },
];

const MW_SKILLS = [
  { title: "본문 요약", meta: "claude-sonnet", color: "var(--sc-node-agent)" },
  { title: "우선순위 분류", meta: "rules + LLM", color: "var(--sc-node-tool)" },
  { title: "감정 분석", meta: "CS 티켓 태깅", color: "var(--sc-accent)" },
  { title: "키워드 추출", meta: "claude-sonnet", color: "var(--sc-node-output)" },
];

const MW_FLOWS = [
  { title: "메일 비서", desc: "받은 편지함 요약 → Slack·Notion" },
  { title: "리서치 수집기", desc: "키워드 뉴스 요약 브리핑" },
  { title: "고객 타겟 분류", desc: "세그먼트 라벨링 자동화" },
];

interface MyWorldProps {
  onNavigate?: (tab: NavTab) => void;
}

export function MyWorld({ onNavigate }: MyWorldProps) {
  const navigate = useNavigate();
  const call = useApi();
  const [activeWorld, setActiveWorld] = useState("My World");
  // 로컬 실행기(GET /graph)에서 읽어온 내 .claude 전체 그래프 (스킬 목록용)
  const [graph, setGraph] = useState<RunnerGraph | null>(null);
  const [localMsg, setLocalMsg] = useState<string | null>(null);
  const [localLoading, setLocalLoading] = useState(false);
  // 노드 뷰(실행 플로우)로 펼쳐 볼 스킬
  const [openSkill, setOpenSkill] = useState<RunnerGraphNode | null>(null);
  const [flow, setFlow] = useState<{ nodes: Node<FlowNodeData>[]; edges: Edge[] } | null>(null);
  const [flowLoading, setFlowLoading] = useState(false);
  const [flowError, setFlowError] = useState<string | null>(null);
  // 열린 스킬이 쓰는 MCP 도구들 (graph의 skill→mcp 엣지 = SKILL.md allowed-tools)
  const [openMcps, setOpenMcps] = useState<string[]>([]);

  const localSkills = graph?.nodes.filter((n) => n.type === "skill") ?? null;

  const loadLocalSkills = async () => {
    setLocalLoading(true);
    setLocalMsg(null);
    try {
      setGraph(await getGraph());
    } catch (e) {
      setLocalMsg(e instanceof RunnerError ? e.message : "불러오기 실패");
    } finally {
      setLocalLoading(false);
    }
  };

  // 스킬 카드 클릭 → 설명을 /assemble(AI)에 넣어 실행 플로우로 그린다.
  const openLocalSkill = async (node: RunnerGraphNode) => {
    setOpenSkill(node);
    setFlow(null);
    setFlowError(null);
    setFlowLoading(true);
    // 이 스킬이 쓰는 MCP = graph의 skill→mcp(uses) 엣지 (SKILL.md allowed-tools)
    const mcps = (graph?.edges ?? [])
      .filter((e) => e.from === node.id && e.kind === "uses")
      .map((e) => e.to.replace(/^mcp:/, ""));
    setOpenMcps(mcps);
    try {
      const seed = node.detail?.trim() || node.label;
      const data = await call<{ nodes: AssembledNode[] }>("/assemble", {
        method: "POST",
        json: { text: seed, target: "skill" },
      });
      setFlow(assembleToFlow(data.nodes, mcps));
    } catch (e) {
      // fetch 자체 실패(서버 미기동/CORS)는 ApiError가 아니라 TypeError로 온다
      const msg =
        e instanceof ApiError
          ? e.message
          : e instanceof TypeError
            ? "백엔드 서버(localhost:8000)에 연결 못 했어요. 백엔드를 켜주세요."
            : e instanceof Error
              ? e.message
              : "플로우 생성 실패";
      setFlowError(msg);
    } finally {
      setFlowLoading(false);
    }
  };

  const closeModal = () => {
    setOpenSkill(null);
    setFlow(null);
    setFlowError(null);
    setOpenMcps([]);
  };

  return (
    <div className="mw">
      <TopNav active="MY WORLD" onNavigate={onNavigate} />

      <div className="mw__body">
        <aside className="mw__side">
          <p className="mw__sideLabel">WORLDS</p>
          {WORLDS.map((w) => (
            <button
              key={w.name}
              type="button"
              className={w.name === activeWorld ? "mw__world mw__world--on" : "mw__world"}
              onClick={() => setActiveWorld(w.name)}
            >
              <span aria-hidden="true">{w.icon}</span>
              {w.name}
            </button>
          ))}
          <button className="mw__newWorld" type="button">
            + New World
          </button>
        </aside>

        <main className="mw__main">
          <h1 className="mw__title">My World</h1>
          <p className="mw__sub">내가 만든 스킬과 자동화를 한 곳에서 관리해요.</p>

          <div className="mw__section">
            <p className="mw__sectionLabel">
              <span className="mw__dot" style={{ background: "var(--sc-node-tool)" }} />내 로컬 스킬
              {localSkills && <span className="mw__count">{localSkills.length}개</span>}
              <button
                type="button"
                className="mw__newWorld"
                style={{ marginLeft: "auto" }}
                onClick={loadLocalSkills}
                disabled={localLoading}
              >
                {localLoading ? "불러오는 중…" : "💻 로컬 불러오기"}
              </button>
            </p>
            {localMsg && <p className="mw__cardMeta">{localMsg}</p>}
            {localSkills &&
              (localSkills.length === 0 ? (
                <p className="mw__cardMeta">로컬 .claude에 스킬이 없어요.</p>
              ) : (
                <div className="mw__grid">
                  {localSkills.map((s) => (
                    <article
                      className="mw__skill"
                      key={s.id}
                      style={{ cursor: "pointer" }}
                      role="button"
                      tabIndex={0}
                      onClick={() => openLocalSkill(s)}
                      onKeyDown={(e) => e.key === "Enter" && openLocalSkill(s)}
                    >
                      <span className="mw__pill">
                        <span
                          className="mw__pillDot"
                          style={{ background: "var(--sc-node-tool)" }}
                        />
                        로컬
                      </span>
                      <h3 className="mw__cardTitle">{s.label}</h3>
                      <p className="mw__cardMeta">{s.detail || ".claude/skills"}</p>
                      <p className="mw__cardMeta" style={{ opacity: 0.7 }}>
                        클릭 → 실행 플로우 보기
                      </p>
                    </article>
                  ))}
                </div>
              ))}
          </div>

          <div className="mw__section">
            <p className="mw__sectionLabel">
              <span className="mw__dot" style={{ background: "var(--sc-node-agent)" }} />
              SKILL <span className="mw__count">{MW_SKILLS.length}개</span>
            </p>
            <div className="mw__grid">
              {MW_SKILLS.map((s) => (
                <article className="mw__skill" key={s.title}>
                  <span className="mw__pill">
                    <span className="mw__pillDot" style={{ background: s.color }} />
                    스킬
                  </span>
                  <h3 className="mw__cardTitle">{s.title}</h3>
                  <p className="mw__cardMeta">{s.meta}</p>
                </article>
              ))}
            </div>
          </div>

          <div className="mw__section">
            <p className="mw__sectionLabel">
              <span className="mw__dot" style={{ background: "var(--sc-accent)" }} />
              AUTO-FLOW <span className="mw__count">{MW_FLOWS.length}개</span>
            </p>
            <div className="mw__grid mw__grid--flow">
              {MW_FLOWS.map((f) => (
                <article className="mw__flow" key={f.title}>
                  <h3 className="mw__cardTitle">{f.title}</h3>
                  <p className="mw__cardDesc">{f.desc}</p>
                  <NodeTrail className="mw__flowTrail" />
                </article>
              ))}
            </div>
          </div>
        </main>
      </div>

      {openSkill && (
        <div className="mw__modalBackdrop" onClick={closeModal}>
          <div className="mw__modal" onClick={(e) => e.stopPropagation()}>
            <header className="mw__modalHead">
              <div>
                <p className="mw__modalKicker">로컬 스킬 · 실행 플로우 (AI)</p>
                <h3 className="mw__modalTitle">{openSkill.label}</h3>
                {openMcps.length > 0 && (
                  <div className="mw__mcpRow">
                    <span className="mw__mcpLabel">쓰는 MCP</span>
                    {openMcps.map((m) => (
                      <span className="mw__mcpChip" key={m}>
                        ◈ {m}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <div className="mw__modalActions">
                <button
                  type="button"
                  className="mw__modalEdit"
                  disabled={!flow}
                  onClick={() => flow && navigate("/auto-flow", { state: { graph: flow } })}
                >
                  ✏️ AUTO-FLOW에서 편집
                </button>
                <button
                  type="button"
                  className="mw__modalClose"
                  aria-label="닫기"
                  onClick={closeModal}
                >
                  ✕
                </button>
              </div>
            </header>
            <div className="mw__modalCanvas">
              {flowLoading ? (
                <p className="mw__modalState">AI가 실행 플로우를 그리는 중…</p>
              ) : flowError ? (
                <p className="mw__modalState">에러: {flowError}</p>
              ) : flow ? (
                <ReactFlow
                  nodes={flow.nodes}
                  edges={flow.edges}
                  nodeTypes={nodeTypes}
                  fitView
                  nodesDraggable={false}
                  nodesConnectable={false}
                  elementsSelectable={false}
                  proOptions={{ hideAttribution: true }}
                >
                  <Background
                    variant={BackgroundVariant.Dots}
                    gap={26}
                    size={1.4}
                    color="#ddd7c7"
                  />
                </ReactFlow>
              ) : null}
            </div>
            <p className="mw__modalHint">
              스킬 설명을 AI가 실행 순서로 재구성 · 편집은 “AUTO-FLOW에서 편집”으로
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
