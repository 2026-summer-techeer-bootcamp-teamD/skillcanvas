import { useCallback, useMemo, useRef, useState, type DragEvent } from "react";
import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
  addEdge,
  useEdgesState,
  useNodesState,
  type Connection,
  type Edge,
  type Node,
  type ReactFlowInstance,
} from "reactflow";
import "reactflow/dist/style.css";
import { PixelArt } from "../components/PixelArt";
import { TopNav, type NavTab } from "../components/TopNav";
import { PublishModal, type PublishPayload } from "../components/PublishModal";
import { FlowNode } from "../components/flow/FlowNode";
import { ROBOT_BLACK, ROBOT_ORANGE } from "../lib/pixelMaps";
import {
  INITIAL_EDGES,
  INITIAL_NODES,
  NODE_COLOR,
  type FlowNodeData,
  type FlowNodeKind,
} from "../lib/flowData";
import "./AutoFlow.css";

const EXAMPLES = [
  "매일 아침 뉴스 요약해서 Slack으로",
  "CS 컴플레인 오면 배송조회해서 사과+쿠폰 발송",
  "메일 오면 분류해서 라벨 붙이기",
];

const REC_SKILLS: {
  title: string;
  meta: string;
  kind: FlowNodeKind;
  typeLabel: string;
  op: string;
}[] = [
  {
    title: "재시도 핸들러",
    meta: "도구 · retry",
    kind: "tool",
    typeLabel: "도구",
    op: "flow.retry",
  },
  {
    title: "승인 게이트",
    meta: "승인 · human-gate",
    kind: "approve",
    typeLabel: "승인",
    op: "human.gate",
  },
];

const REC_MCP: { title: string; meta: string; color: string }[] = [
  { title: "GitHub MCP", meta: "PR·이슈·릴리스", color: "#7a4fd6" },
  { title: "Notion MCP", meta: "문서·DB 읽기/쓰기", color: "#2a2620" },
  { title: "Sheets MCP", meta: "표 데이터 append", color: "#1f8a4c" },
];

const MY_SKILLS: {
  title: string;
  meta: string;
  kind: FlowNodeKind;
  typeLabel: string;
  op: string;
}[] = [
  {
    title: "본문 요약",
    meta: "에이전트 · claude",
    kind: "agent",
    typeLabel: "에이전트",
    op: "claude.summarize",
  },
  {
    title: "우선순위 분류",
    meta: "도구 · rules",
    kind: "tool",
    typeLabel: "도구",
    op: "rules.classify",
  },
];

const DRAG_MIME = "application/scflow";

const nodeTypes = { flow: FlowNode };

interface AutoFlowProps {
  onNavigate?: (tab: NavTab) => void;
}

export function AutoFlow({ onNavigate }: AutoFlowProps) {
  const [phase, setPhase] = useState<"input" | "builder">("input");
  const [text, setText] = useState("");

  const [nodes, setNodes, onNodesChange] = useNodesState(INITIAL_NODES);
  const [edges, setEdges, onEdgesChange] = useEdgesState(INITIAL_EDGES);
  const [selected, setSelected] = useState<Node<FlowNodeData> | null>(null);
  const idRef = useRef(100);
  const flowWrapper = useRef<HTMLDivElement>(null);
  const [rfInstance, setRfInstance] = useState<ReactFlowInstance | null>(null);
  const [publishOpen, setPublishOpen] = useState(false);

  // 발행 = graph_json(노드+엣지+뷰포트)에 폼 값을 합쳐 POST /workflows 로 보낼 자리.
  const handlePublish = (payload: PublishPayload) => {
    const graph_json = rfInstance?.toObject() ?? { nodes, edges };
    // TODO: 백엔드 연결 시 POST /workflows { ...payload, graph_json }
    console.log("[발행] POST /workflows", { ...payload, graph_json });
  };

  const deleteNode = useCallback(
    (id: string) => {
      setNodes((nds) => nds.filter((n) => n.id !== id));
      setEdges((eds) => eds.filter((e) => e.source !== id && e.target !== id));
      setSelected((cur) => (cur?.id === id ? null : cur));
    },
    [setNodes, setEdges],
  );

  const addNode = useCallback(
    (data: FlowNodeData) => {
      const id = `x${idRef.current++}`;
      const offset = (idRef.current % 6) * 26;
      setNodes((nds) => [
        ...nds,
        { id, type: "flow", position: { x: 160 + offset, y: 470 + offset }, data },
      ]);
    },
    [setNodes],
  );

  // 사이드바 "내 스킬"을 캔버스로 드래그해서 노드로 추가
  const onSkillDragStart = (event: DragEvent<HTMLDivElement>, data: FlowNodeData) => {
    event.dataTransfer.setData(DRAG_MIME, JSON.stringify(data));
    event.dataTransfer.effectAllowed = "move";
  };

  const onDragOver = useCallback((event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  const onDrop = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      const raw = event.dataTransfer.getData(DRAG_MIME);
      if (!raw || !rfInstance || !flowWrapper.current) return;
      const data = JSON.parse(raw) as FlowNodeData;
      const bounds = flowWrapper.current.getBoundingClientRect();
      const position = rfInstance.project({
        x: event.clientX - bounds.left,
        y: event.clientY - bounds.top,
      });
      const id = `x${idRef.current++}`;
      setNodes((nds) => [...nds, { id, type: "flow", position, data }]);
    },
    [rfInstance, setNodes],
  );

  const onConnect = useCallback(
    (conn: Connection) =>
      setEdges((eds) =>
        addEdge(
          {
            ...conn,
            animated: true,
            style: { stroke: "#e8843c", strokeWidth: 1.6, strokeDasharray: "5 5" },
          },
          eds,
        ),
      ),
    [setEdges],
  );

  const updateSelectedTitle = (title: string) => {
    if (!selected) return;
    setSelected({ ...selected, data: { ...selected.data, title } });
    setNodes((nds) =>
      nds.map((n) => (n.id === selected.id ? { ...n, data: { ...n.data, title } } : n)),
    );
  };

  // 클릭뿐 아니라 키보드 선택까지 아우르도록 React Flow 선택 상태로 인스펙터를 연다.
  const onSelectionChange = useCallback(
    ({ nodes: sel }: { nodes: Node<FlowNodeData>[] }) => setSelected(sel[0] ?? null),
    [],
  );

  // 연결선을 클릭하면 그 연결을 삭제 (노드는 핸들을 드래그해 다시 이을 수 있다)
  const onEdgeClick = useCallback(
    (_: unknown, clicked: Edge) => {
      setEdges((eds) => eds.filter((e) => e.id !== clicked.id));
    },
    [setEdges],
  );

  const nodesWithHandlers = useMemo(
    () => nodes.map((n) => ({ ...n, data: { ...n.data, onDelete: deleteNode } })),
    [nodes, deleteNode],
  );

  const generate = (prompt: string) => {
    if (!prompt.trim()) return;
    setPhase("builder");
  };

  if (phase === "input") {
    return (
      <div className="af">
        <TopNav active="AUTO-FLOW" onNavigate={onNavigate} />
        <main className="af__hero">
          <div className="af__mascots" aria-hidden="true">
            <PixelArt sprite={ROBOT_ORANGE} className="af__mascot af__mascot--1" />
            <PixelArt sprite={ROBOT_BLACK} className="af__mascot af__mascot--2" />
            <PixelArt sprite={ROBOT_ORANGE} className="af__mascot af__mascot--3" />
          </div>
          <span className="af__badge">✦ 자동화 생성</span>
          <h1 className="af__title">무엇을 자동화할까요?</h1>
          <p className="af__subtitle">
            하고 싶은 자동화를 문장으로 적으면, Claude가 노드 플로우로 조립해 드려요.
          </p>

          <form
            className="af__inputRow"
            onSubmit={(e) => {
              e.preventDefault();
              generate(text);
            }}
          >
            <input
              className="af__input"
              placeholder="예: 웹훅 들어오면 페이지 가져와 요약해서 Slack 전송"
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <button className="af__go" type="submit">
              입력
            </button>
          </form>

          <div className="af__examples">
            {EXAMPLES.map((ex) => (
              <button key={ex} type="button" className="af__example" onClick={() => generate(ex)}>
                📮 {ex}
              </button>
            ))}
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="af">
      <TopNav active="AUTO-FLOW" onNavigate={onNavigate} />

      <div className="af__work">
        {/* 왼쪽: 노드 편집 인스펙터 */}
        <aside className="af__inspect">
          <header className="af__inspectHead">
            <strong>노드 편집</strong>
            {selected && (
              <button
                className="af__inspectClose"
                type="button"
                aria-label="선택 해제"
                onClick={() => setSelected(null)}
              >
                ×
              </button>
            )}
          </header>

          {selected ? (
            <>
              <span className="af__typePill">
                <span
                  className="af__typeDot"
                  style={{ background: NODE_COLOR[selected.data.kind] }}
                />
                {selected.data.typeLabel}
              </span>

              <label className="af__field">
                라벨
                <input
                  className="af__fieldInput"
                  value={selected.data.title}
                  onChange={(e) => updateSelectedTitle(e.target.value)}
                />
              </label>

              <label className="af__field">
                상세
                <input className="af__fieldInput" defaultValue={selected.data.op} />
              </label>

              {selected.data.needsKey && (
                <div className="af__keyWarn">
                  <p className="af__keyWarnTitle">▨ MCP 키 연결 필요</p>
                  <p className="af__keyWarnBody">이 도구는 본인 키를 붙여넣어야 실행돼요.</p>
                  <button className="af__keyBtn" type="button">
                    키 붙여넣기
                  </button>
                </div>
              )}
            </>
          ) : (
            <p className="af__inspectEmpty">
              노드를 클릭하면 여기서 편집해요.
              <br />
              노드 옆 점을 끌어 서로 연결하고, 연결선을 클릭하면 지워요.
            </p>
          )}
        </aside>

        {/* 가운데: React Flow 캔버스 */}
        <div className="af__canvas">
          <div className="af__toolbar">
            <span className="af__flowChip">cs-complaint-handler</span>
            <span className="af__conn">◈ Gmail</span>
            <span className="af__conn">◈ Slack</span>
            <div className="af__toolbarRight">
              <button className="af__run" type="button">
                실행
              </button>
              <button className="af__publish" type="button" onClick={() => setPublishOpen(true)}>
                갤러리에 발행
              </button>
            </div>
          </div>

          <div className="af__flow" ref={flowWrapper} onDragOver={onDragOver} onDrop={onDrop}>
            <ReactFlow
              nodes={nodesWithHandlers}
              edges={edges}
              nodeTypes={nodeTypes}
              onInit={setRfInstance}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onSelectionChange={onSelectionChange}
              onEdgeClick={onEdgeClick}
              connectionLineStyle={{ stroke: "#e8843c", strokeWidth: 1.8 }}
              fitView
              proOptions={{ hideAttribution: true }}
            >
              <Background variant={BackgroundVariant.Dots} gap={26} size={1.4} color="#ddd7c7" />
              <Controls showInteractive={false} />
            </ReactFlow>
          </div>
        </div>

        {/* 오른쪽: 자연어 추천 / 라이브러리 패널 */}
        <aside className="af__side">
          <span className="af__sideBadge">✦ 플로우 편집</span>
          <p className="af__flowName">cs-complaint-handler</p>
          <h2 className="af__sideTitle">어떤 기능을 넣을까요?</h2>
          <textarea
            className="af__sideInput"
            placeholder="예: 실패하면 3번 재시도하고, 발송 전 승인 단계 추가해줘"
          />
          <button className="af__recommend" type="button">
            ⚡ AI에게 추천받기
          </button>

          <p className="af__group">✦ AI 추천 · 스킬</p>
          {REC_SKILLS.map((s) => (
            <div className="af__rec" key={s.title}>
              <span className="af__recBar" style={{ background: NODE_COLOR[s.kind] }} />
              <div className="af__recText">
                <p className="af__recTitle">{s.title}</p>
                <p className="af__recMeta">{s.meta}</p>
              </div>
              <button
                className="af__recAdd"
                type="button"
                onClick={() =>
                  addNode({ kind: s.kind, typeLabel: s.typeLabel, title: s.title, op: s.op })
                }
              >
                + 추가
              </button>
            </div>
          ))}

          <p className="af__group">◇ AI 추천 · MCP</p>
          {REC_MCP.map((m) => (
            <div className="af__rec" key={m.title}>
              <span className="af__recIcon" style={{ background: m.color }} />
              <div className="af__recText">
                <p className="af__recTitle">{m.title}</p>
                <p className="af__recMeta">{m.meta}</p>
              </div>
              <button
                className="af__recAdd af__recAdd--icon"
                type="button"
                aria-label={`${m.title} 추가`}
                onClick={() =>
                  addNode({
                    kind: "tool",
                    typeLabel: "MCP",
                    title: m.title,
                    op: "mcp.call",
                    needsKey: true,
                  })
                }
              >
                +
              </button>
            </div>
          ))}

          <p className="af__group">내 스킬 · 드래그해서 추가</p>
          {MY_SKILLS.map((s) => (
            <div
              className="af__mine"
              key={s.title}
              draggable
              onDragStart={(e) =>
                onSkillDragStart(e, {
                  kind: s.kind,
                  typeLabel: s.typeLabel,
                  title: s.title,
                  op: s.op,
                })
              }
            >
              <span className="af__recBar" style={{ background: NODE_COLOR[s.kind] }} />
              <div className="af__recText">
                <p className="af__recTitle">{s.title}</p>
                <p className="af__recMeta">{s.meta}</p>
              </div>
              <span className="af__mineHandle" aria-hidden="true">
                ⠿
              </span>
            </div>
          ))}
        </aside>
      </div>

      <PublishModal
        open={publishOpen}
        kind="workflow"
        defaultName="cs-complaint-handler"
        onClose={() => setPublishOpen(false)}
        onPublish={handlePublish}
      />
    </div>
  );
}
