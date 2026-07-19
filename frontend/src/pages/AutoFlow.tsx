import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type DragEvent,
  type ReactNode,
} from "react";
import { useLocation } from "react-router-dom";
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
import { KeyModal } from "../components/KeyModal";
import { FlowNode } from "../components/flow/FlowNode";
import { ROBOT_BLACK, ROBOT_ORANGE } from "../lib/pixelMaps";
import {
  INITIAL_EDGES,
  INITIAL_NODES,
  NODE_COLOR,
  assembleWorkflowToFlow,
  type FlowNodeData,
  type FlowNodeKind,
} from "../lib/flowData";
import { useApi, ApiError } from "../lib/api";
import type { ToolCatalogItem } from "../lib/toolCatalog";
import {
  runFlow,
  approveRun,
  saveCredential,
  getCredentials,
  startWatch,
  stopWatch,
  getWatchStatus,
  RunnerError,
  type RunResultItem,
  type RunResponse,
  type WatchStatus,
} from "../lib/runner";
import "./AutoFlow.css";

const EXAMPLES = [
  "매일 아침 뉴스 요약해서 Slack으로",
  "CS 컴플레인 오면 배송조회해서 사과+쿠폰 발송",
  "메일 오면 분류해서 라벨 붙이기",
];

// map-node 응답의 type → 노드 타입 라벨(인스펙터 표시용).
const KIND_LABEL: Record<FlowNodeKind, string> = {
  trigger: "트리거",
  tool: "도구",
  agent: "에이전트",
  approve: "승인",
  output: "출력",
  branch: "분기",
};

// 실행 결과 표시용: 러너 노드 타입 → 라벨·색 (이모지 대신 색 라벨로 타입 구분)
const RESULT_TYPE: Record<string, { label: string; color: string }> = {
  trigger: { label: "트리거", color: "var(--sc-node-trigger)" },
  tool: { label: "도구", color: "var(--sc-node-tool)" },
  agent: { label: "에이전트", color: "var(--sc-node-agent)" },
  ai: { label: "에이전트", color: "var(--sc-node-agent)" },
  branch: { label: "분기", color: "var(--sc-node-branch)" },
  approve: { label: "승인", color: "var(--sc-node-approve)" },
  output: { label: "출력", color: "var(--sc-node-output)" },
};

// 러너 결과 문자열의 이모지(⏱🔌🧠🔀📤 등)를 걷어낸다 — 화살표·대시는 살린다.
const RESULT_EMOJI_RE =
  /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{2300}-\u{23FF}\u{2B00}-\u{2BFF}\u{FE0F}\u{200D}]/gu;

function cleanResultLine(s: string): string {
  return s
    .replace(RESULT_EMOJI_RE, "")
    .replace(/[ \t]{2,}/g, " ")
    .trimStart();
}

// 이모지 제거 + **굵게** 렌더 + 줄바꿈 보존. (원본은 마크다운이라 그냥 뿌리면 별표가 그대로 보인다)
function renderResult(text: string): ReactNode {
  return text.split("\n").map((raw, li) => {
    const line = cleanResultLine(raw);
    return (
      <span key={li} style={{ display: "block" }}>
        {line.split("**").map((seg, si) => (si % 2 === 1 ? <strong key={si}>{seg}</strong> : seg))}
      </span>
    );
  });
}

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
  {
    // op(=detail)에 분기 라벨을 '|'로. 실행기 branch 노드가 이걸 유형 후보로 쓴다.
    title: "분기 (유형 판단)",
    meta: "분기 · branch",
    kind: "branch",
    typeLabel: "분기",
    op: "문의|제안",
  },
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
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);
  const [flowName, setFlowName] = useState("cs-complaint-handler");

  const [nodes, setNodes, onNodesChange] = useNodesState(INITIAL_NODES);
  const [edges, setEdges, onEdgesChange] = useEdgesState(INITIAL_EDGES);
  // 상단 툴바의 MCP 칩은 실제 노드들의 mcpKey에서 파생 — 노드 바꾸기(map-node)·삭제·추가가
  // 바로 반영된다(별도 상태로 두면 노드를 바꿔도 옛 도구가 그대로 남는다).
  const flowMcps = useMemo(
    () => Array.from(new Set(nodes.map((n) => n.data.mcpKey).filter(Boolean))) as string[],
    [nodes],
  );
  const [selected, setSelected] = useState<Node<FlowNodeData> | null>(null);
  // 노드 자연어 수정(POST /map-node) — 예: "팀 슬랙으로 바꿔줘"
  const [mapText, setMapText] = useState("");
  const [mapBusy, setMapBusy] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);
  const idRef = useRef(100);
  const flowWrapper = useRef<HTMLDivElement>(null);
  const [rfInstance, setRfInstance] = useState<ReactFlowInstance | null>(null);
  const [publishOpen, setPublishOpen] = useState(false);
  // ── AI 추천 (POST /recommend) ────────────────────
  const call = useApi();
  const [sideText, setSideText] = useState("");
  const [recLoading, setRecLoading] = useState(false);
  const [recError, setRecError] = useState<string | null>(null);
  const [recMcps, setRecMcps] = useState<string[]>([]);
  const [recSkill, setRecSkill] = useState<{ name: string; description: string } | null>(null);

  // ── 도구 카탈로그 (GET /tool-catalog) — 키 붙여넣기 팝업 자동생성 ──
  const [catalog, setCatalog] = useState<ToolCatalogItem[]>([]);
  const [keyModalOpen, setKeyModalOpen] = useState(false);
  const [savedKeys, setSavedKeys] = useState<Set<string>>(new Set());
  const [keyTarget, setKeyTarget] = useState<{ key: string; tool: ToolCatalogItem | null } | null>(
    null,
  );

  // ── 실행 (로컬 실행기 POST /run) ──────────────────
  const [runId, setRunId] = useState<string | null>(null);
  const [runResults, setRunResults] = useState<RunResultItem[]>([]);
  const [runStatus, setRunStatus] = useState<RunResponse["status"] | null>(null);
  const [runPending, setRunPending] = useState<{ id: string; message: string } | null>(null);
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);

  // ── 스케줄러 감시 (POST /watch) ────────────────────
  const [watch, setWatch] = useState<WatchStatus | null>(null);
  const [watchBusy, setWatchBusy] = useState(false);

  useEffect(() => {
    // 실행기가 켜져 있으면 감시 상태를 읽어와 버튼에 반영(꺼져 있으면 조용히 무시)
    getWatchStatus()
      .then(setWatch)
      .catch(() => {});
  }, []);

  // 로컬에 저장 = 지금 편집한 그래프를 실행기에 저장하고 자동 실행을 켠다.
  // 이미 켜져 있어도 다시 누르면 '최신 그래프로 갱신' — 저장 뒤 노드를 더 고쳤을 때
  // 낡은 저장본이 도는 걸 막는다(어제 노션이 안 됐던 원인).
  const handleSaveLocal = async () => {
    setWatchBusy(true);
    setRunError(null);
    try {
      setWatch(await startWatch(nodes, edges));
    } catch (e) {
      setRunError(e instanceof RunnerError ? e.message : "로컬 저장 실패");
    } finally {
      setWatchBusy(false);
    }
  };

  const handleStopWatch = async () => {
    setWatchBusy(true);
    setRunError(null);
    try {
      setWatch(await stopWatch());
    } catch (e) {
      setRunError(e instanceof RunnerError ? e.message : "자동 실행 끄기 실패");
    } finally {
      setWatchBusy(false);
    }
  };

  const handleRun = async () => {
    setRunning(true);
    setRunError(null);
    setRunResults([]);
    setRunPending(null);
    setRunStatus(null);
    try {
      const r = await runFlow(nodes, edges);
      setRunId(r.run_id);
      setRunResults(r.results); // 러너가 배치로 실행 → 결과 한 번에 반영(정직)
      setRunStatus(r.status);
      setRunPending(r.pending ?? null);
    } catch (e) {
      setRunError(e instanceof RunnerError ? e.message : "실행 실패");
    } finally {
      setRunning(false);
    }
  };

  const handleApprove = async () => {
    if (!runId) return;
    setRunning(true);
    setRunError(null);
    setRunPending(null); // 승인 노드의 🚨 해제하고 이어서 실행
    try {
      const r = await approveRun(runId);
      setRunResults((prev) => [...prev, ...r.results]); // 델타 append
      setRunStatus(r.status);
      setRunPending(r.pending ?? null);
    } catch (e) {
      setRunError(e instanceof RunnerError ? e.message : "승인 실패");
    } finally {
      setRunning(false);
    }
  };

  const handleRecommend = async () => {
    const text = sideText.trim();
    if (!text) return;
    if (text.length > 500) {
      setRecError("500자 이내로 입력해주세요.");
      return;
    }
    setRecLoading(true);
    setRecError(null);
    setRecSkill(null); // 재요청 시 이전 결과 비우기
    setRecMcps([]);
    try {
      const data = await call<{ skill: string; description: string; mcps: string[] }>(
        "/recommend",
        { method: "POST", json: { text } },
      );
      setRecSkill({ name: data.skill, description: data.description });
      setRecMcps(Array.isArray(data.mcps) ? data.mcps : []); // null 방어
    } catch (e) {
      setRecError(e instanceof ApiError ? e.message : "추천 실패");
    } finally {
      setRecLoading(false);
    }
  };
  // 발행 = graph_json(노드+엣지+뷰포트)에 폼 값을 합쳐 POST /workflows.
  const handlePublish = async (payload: PublishPayload) => {
    const graph_json = rfInstance?.toObject() ?? { nodes, edges };
    try {
      await call("/workflows", { method: "POST", json: { ...payload, graph_json } });
      setPublishOpen(false);
      alert("갤러리에 발행됐어요!");
    } catch (e) {
      alert(e instanceof ApiError ? e.message : "발행 실패");
    }
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
    (conn: Connection) => {
      // 분기 노드에서 나가는 엣지면 조건 라벨을 물어본다(라벨=실행기 when 조건).
      const src = nodes.find((n) => n.id === conn.source);
      let label: string | undefined;
      if (src?.data.kind === "branch") {
        const v = window.prompt("이 경로로 갈 조건? (예: 문의 / 제안)")?.trim();
        if (v) label = v;
      }
      setEdges((eds) =>
        addEdge(
          {
            ...conn,
            animated: true,
            label,
            labelStyle: { fill: "#d64550", fontWeight: 600 },
            style: { stroke: "#e8843c", strokeWidth: 1.6, strokeDasharray: "5 5" },
          },
          eds,
        ),
      );
    },
    [setEdges, nodes],
  );

  const updateSelectedData = (patch: Partial<FlowNodeData>) => {
    if (!selected) return;
    setSelected({ ...selected, data: { ...selected.data, ...patch } });
    setNodes((nds) =>
      nds.map((n) => (n.id === selected.id ? { ...n, data: { ...n.data, ...patch } } : n)),
    );
  };

  // 선택 노드를 자연어 지시로 재매핑(POST /map-node). 예: 디스코드 노드에 "슬랙으로 바꿔줘".
  // 응답의 detail이 카탈로그 key면 그게 곧 실행기가 쓸 mcpKey → 실행 대상·키 패널까지 갱신된다.
  const mapNode = async () => {
    if (!selected) return;
    const instruction = mapText.trim();
    if (!instruction || mapBusy) return;
    setMapBusy(true);
    setMapError(null);
    try {
      const data = await call<{
        node: { type: string; label: string; detail: string | null };
        mcp_added: string | null;
      }>("/map-node", {
        method: "POST",
        json: {
          node: {
            type: selected.data.kind,
            label: selected.data.title,
            detail: selected.data.op || null,
          },
          instruction,
        },
      });
      const kind = (
        ["trigger", "tool", "agent", "approve", "output", "branch"].includes(data.node.type)
          ? data.node.type
          : "tool"
      ) as FlowNodeKind;
      const detail = data.node.detail ?? "";
      const isMcp = kind === "tool" && detail !== "" && catalog.some((t) => t.key === detail);
      updateSelectedData({
        kind,
        typeLabel: KIND_LABEL[kind] ?? kind,
        title: data.node.label,
        op: detail,
        mcpKey: isMcp ? detail : undefined,
      });
      setMapText("");
    } catch (e) {
      setMapError(e instanceof ApiError ? e.message : "노드 수정 실패");
    } finally {
      setMapBusy(false);
    }
  };

  // 클릭뿐 아니라 키보드 선택까지 아우르도록 React Flow 선택 상태로 인스펙터를 연다.
  const onSelectionChange = useCallback(({ nodes: sel }: { nodes: Node<FlowNodeData>[] }) => {
    setSelected(sel[0] ?? null);
    setMapText(""); // 다른 노드로 넘어가면 자연어 수정 입력·에러 초기화
    setMapError(null);
  }, []);

  // 연결선을 클릭하면 그 연결을 삭제 (노드는 핸들을 드래그해 다시 이을 수 있다)
  const onEdgeClick = useCallback(
    (_: unknown, clicked: Edge) => {
      setEdges((eds) => eds.filter((e) => e.id !== clicked.id));
    },
    [setEdges],
  );

  // 실행 결과 → 노드별 상태 맵 (캔버스 색칠용)
  const runStateById = useMemo(() => {
    const m: Record<string, "done" | "pending" | "stopped"> = {};
    runResults.forEach((r) => (m[r.id] = "done"));
    if (runStatus === "stopped" && runResults.length) {
      m[runResults[runResults.length - 1].id] = "stopped";
    }
    if (runPending) m[runPending.id] = "pending";
    return m;
  }, [runResults, runStatus, runPending]);

  const nodesWithHandlers = useMemo(
    () =>
      nodes.map((n) => ({
        ...n,
        data: { ...n.data, onDelete: deleteNode, runState: runStateById[n.id] },
      })),
    [nodes, deleteNode, runStateById],
  );

  // 자연어 → 워크플로우 그래프 자동생성 (POST /assemble target=workflow)
  const generate = async (prompt: string) => {
    if (!prompt.trim() || generating) return;
    setText(prompt);
    setGenerating(true);
    setGenError(null);
    try {
      const data = await call<{
        name: string;
        nodes: { id: string; type: string; label: string; detail: string | null }[];
        edges: { from: string; to: string; when?: string | null }[];
        used_mcps: string[];
      }>("/assemble", { method: "POST", json: { text: prompt, target: "workflow" } });
      const { nodes: n, edges: e } = assembleWorkflowToFlow(
        data.nodes,
        data.edges ?? [],
        data.used_mcps ?? [],
      );
      setNodes(n);
      setEdges(e);
      if (data.name) setFlowName(data.name);
      setPhase("builder");
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? err.message
          : err instanceof TypeError
            ? "백엔드 서버(localhost:8000)에 연결 못 했어요. 백엔드를 켜주세요."
            : "생성 실패";
      setGenError(msg);
    } finally {
      setGenerating(false);
    }
  };

  // Create에서 텍스트를, MyWorld 노드뷰에서 그래프를 들고 오면 바로 빌더로.
  const location = useLocation();
  const kickedOff = useRef(false);
  useEffect(() => {
    const s = location.state as {
      text?: string;
      name?: string;
      graph?: { nodes: Node<FlowNodeData>[]; edges: Edge[] };
    } | null;
    if (kickedOff.current) return;
    if (s?.graph) {
      kickedOff.current = true;
      setNodes(s.graph.nodes);
      setEdges(s.graph.edges);
      if (s.name) setFlowName(s.name); // MyWorld 편집 경로에서 원본 이름 유지(하드코딩 오염 방지)
      setPhase("builder");
    } else if (s?.text) {
      kickedOff.current = true;
      generate(s.text); // 자연어 → assemble로 그래프 생성 (setText·setPhase는 generate가 함)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.state, setNodes, setEdges]);

  // 도구 카탈로그 1회 로드 (키 붙여넣기 팝업 메타). 실패해도 폴백 입력으로 동작.
  useEffect(() => {
    call<{ items: ToolCatalogItem[] }>("/tool-catalog?limit=100")
      .then((d) => setCatalog(d.items))
      .catch(() => {});
  }, [call]);

  // 이미 키를 넣은 도구 목록 (로컬 실행기). 이게 없으면 저장하고 나서도 "키 연결 필요"가
  // 그대로 떠서 넣었는지 확인할 방법이 없다. 실행기가 안 떠 있으면 조용히 빈 목록.
  const refreshSavedKeys = useCallback(() => {
    getCredentials()
      .then((d) => setSavedKeys(new Set(d.tool_keys)))
      .catch(() => {});
  }, []);
  useEffect(() => {
    refreshSavedKeys();
  }, [refreshSavedKeys]);

  // MCP 노드 키로 카탈로그 매칭 후 키 팝업 열기
  const openKeyModal = (toolKey: string) => {
    const tool = catalog.find((t) => t.key === toolKey.trim().toLowerCase()) ?? null;
    // 매칭되면 카탈로그 정본 키로 저장(더 견고). 매칭 실패 시 원본 title 폴백.
    setKeyTarget({ key: tool?.key ?? toolKey, tool });
    setKeyModalOpen(true);
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

          {generating ? (
            // 조립 중엔 입력폼 대신 로딩만 (Create 경유 시 입력화면 깜빡임 방지)
            <p className="af__loading">워크플로우를 조립하는 중…</p>
          ) : (
            <>
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
                <button className="af__go" type="submit" disabled={!text.trim()}>
                  입력
                </button>
              </form>

              {genError && <p className="af__subtitle">에러: {genError}</p>}

              <div className="af__examples">
                {EXAMPLES.map((ex) => (
                  <button
                    key={ex}
                    type="button"
                    className="af__example"
                    onClick={() => generate(ex)}
                  >
                    📮 {ex}
                  </button>
                ))}
              </div>
            </>
          )}
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
                  onChange={(e) => updateSelectedData({ title: e.target.value })}
                />
              </label>

              <label className="af__field">
                상세
                {/* defaultValue만 있고 onChange가 없어 입력이 저장되지 않았다(바로 위 '라벨'은
                    controlled인데 여기만 빠짐). 실행기로 detail로 넘어가는 값이라, 스마트택배처럼
                    파라미터를 detail로 받는 도구는 UI에서 고칠 방법 자체가 없었다. */}
                <input
                  className="af__fieldInput"
                  value={selected.data.op ?? ""}
                  onChange={(e) => updateSelectedData({ op: e.target.value })}
                  placeholder={
                    selected.data.mcpKey === "sweettracker"
                      ? "t_code=04&t_invoice=송장번호"
                      : undefined
                  }
                />
              </label>

              {/* 노드 자연어 수정 — 예: 디스코드 노드에 "팀 슬랙으로 바꿔줘" */}
              <div className="af__mapEdit">
                <label className="af__field">
                  노드 바꾸기
                  <input
                    className="af__fieldInput"
                    value={mapText}
                    onChange={(e) => setMapText(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") mapNode();
                    }}
                    placeholder="예: 팀 슬랙으로 바꿔줘"
                  />
                </label>
                <button
                  className="af__recommend"
                  type="button"
                  onClick={mapNode}
                  disabled={mapBusy || !mapText.trim()}
                >
                  {mapBusy ? "바꾸는 중…" : "바꾸기"}
                </button>
                {mapError && <p className="af__recMeta">에러: {mapError}</p>}
              </div>

              {(() => {
                const meta = selected.data.mcpKey
                  ? catalog.find((t) => t.key === selected.data.mcpKey)
                  : undefined;
                // 판단 기준은 key_required 하나. auth_owner는 '누가 발급하는가'이지
                // '안 넣어도 된다'가 아니다 — discord·telegram이 developer면서 봇 토큰이
                // 필요한데, auth_owner를 같이 보면 이 패널이 통째로 사라져 키를 넣을
                // UI 자체가 없어진다(openKeyModal 호출부가 이 버튼 하나뿐).
                // KeyModal.tsx의 noKeyNeeded와 반드시 같은 기준을 써야 한다.
                const showKeyPanel = selected.data.mcpKey
                  ? meta
                    ? meta.key_required
                    : true
                  : false;
                if (!showKeyPanel) return null;
                // 이미 넣은 키면 경고(주황) 대신 완료(초록)로. 이게 없으면 저장하고 나서도
                // "키 연결 필요"가 그대로 떠서 넣었는지 확인할 방법이 없다.
                const done = savedKeys.has((selected.data.mcpKey ?? "").toLowerCase());
                return (
                  <div className={done ? "af__keyWarn af__keyWarn--done" : "af__keyWarn"}>
                    <p className="af__keyWarnTitle">
                      {done ? "✓ 키 연결됨" : "▨ MCP 키 연결 필요"}
                    </p>
                    <p className="af__keyWarnBody">
                      {done
                        ? "이 PC에 저장돼 있어요. 바로 실행할 수 있어요."
                        : "이 도구는 키를 붙여넣어야 실행돼요."}
                    </p>
                    <button
                      className="af__keyBtn"
                      type="button"
                      onClick={() => openKeyModal(selected.data.mcpKey ?? selected.data.title)}
                    >
                      {done ? "키 다시 넣기" : "키 붙여넣기"}
                    </button>
                  </div>
                );
              })()}
            </>
          ) : (
            <>
              {text.trim() && (
                <div className="af__request">
                  <span className="af__requestLabel">요청</span>
                  <p className="af__requestText">{text}</p>
                </div>
              )}
              <p className="af__inspectEmpty">
                노드를 클릭하면 여기서 편집해요.
                <br />
                노드 옆 점을 끌어 서로 연결하고, 연결선을 클릭하면 지워요.
              </p>
            </>
          )}
        </aside>

        {/* 가운데: React Flow 캔버스 */}
        <div className="af__canvas">
          <div className="af__toolbar">
            <span className="af__flowChip">{flowName}</span>
            {flowMcps.map((m) => (
              <span key={m} className="af__conn">
                ◈ {m}
              </span>
            ))}
            <div className="af__toolbarRight">
              <button
                className={watch?.watching ? "af__watch af__watch--on" : "af__watch"}
                type="button"
                onClick={handleSaveLocal}
                disabled={watchBusy}
                title="지금 워크플로우를 실행기에 저장하고, 새 메일이 오면 자동 실행해요. 편집을 다 끝낸 뒤 누르세요. (이미 켜져 있으면 최신 내용으로 다시 저장)"
              >
                {watchBusy
                  ? "저장 중…"
                  : watch?.watching
                    ? "● 저장됨 · 자동 실행 중"
                    : "로컬에 저장"}
              </button>
              {watch?.watching && !watchBusy && (
                <button
                  className="af__watchOff"
                  type="button"
                  onClick={handleStopWatch}
                  title="자동 실행 끄기 (저장본은 남겨둬요)"
                >
                  끄기
                </button>
              )}
              <button className="af__run" type="button" onClick={handleRun} disabled={running}>
                {running ? "실행 중…" : "실행"}
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

          {/* 실행 결과 오버레이 (로컬 실행기 응답) */}
          {(running || runStatus || runError) && (
            <div
              style={{
                position: "absolute",
                right: 20,
                bottom: 20,
                width: "min(380px, calc(100% - 40px))",
                maxHeight: "44vh",
                overflow: "auto",
                background: "#fff",
                border: "1px solid #e5e0d2",
                borderRadius: 12,
                padding: "12px 14px",
                boxShadow: "0 8px 24px rgba(0,0,0,.12)",
                zIndex: 50,
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: 8,
                }}
              >
                <strong>실행 결과</strong>
                {(() => {
                  const label = running
                    ? "실행 중…"
                    : runStatus === "done"
                      ? "완료"
                      : runStatus === "awaiting_approval"
                        ? "승인 대기"
                        : runStatus === "stopped"
                          ? "중단 (중복)"
                          : "";
                  if (!label) return null;
                  // 완료는 우리 브랜드 주황 알약으로 포인트, 나머지는 담백한 회색 텍스트
                  const done = runStatus === "done" && !running;
                  return (
                    <span
                      style={{
                        fontSize: 12,
                        fontWeight: 700,
                        padding: done ? "3px 10px" : 0,
                        borderRadius: 999,
                        color: done ? "#fff" : "#8a8375",
                        background: done ? "var(--sc-accent)" : "transparent",
                      }}
                    >
                      {label}
                    </span>
                  );
                })()}
              </div>
              {runError && (
                <p style={{ color: "#c0392b", fontSize: 13, margin: "4px 0" }}>⚠ {runError}</p>
              )}
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {runResults.map((r, i) => {
                  const meta = RESULT_TYPE[r.type ?? ""] ?? { label: "단계", color: "#b3ab99" };
                  return (
                    <div
                      key={`${r.id}-${i}`}
                      style={{ borderLeft: `3px solid ${meta.color}`, paddingLeft: 10 }}
                    >
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 6,
                          marginBottom: 3,
                        }}
                      >
                        <span style={{ fontSize: 10.5, fontWeight: 700, color: meta.color }}>
                          {meta.label}
                        </span>
                        <span style={{ fontSize: 12.5, fontWeight: 600, color: "#3a3529" }}>
                          {r.label}
                        </span>
                      </div>
                      <div style={{ fontSize: 12.5, lineHeight: 1.65, color: "#5a5545" }}>
                        {renderResult(r.result)}
                      </div>
                    </div>
                  );
                })}
              </div>
              {runPending && (
                <div
                  style={{
                    marginTop: 10,
                    padding: "10px 12px",
                    background: "#fff4ec",
                    border: "1px solid #f2c9a8",
                    borderRadius: 8,
                  }}
                >
                  <p style={{ margin: "0 0 8px", fontSize: 13 }}>
                    {cleanResultLine(runPending.message)}
                  </p>
                  <button
                    type="button"
                    onClick={handleApprove}
                    disabled={running}
                    style={{
                      padding: "6px 14px",
                      background: "#e8843c",
                      color: "#fff",
                      border: "none",
                      borderRadius: 6,
                      cursor: "pointer",
                      fontWeight: 600,
                    }}
                  >
                    승인하고 계속
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* 오른쪽: 자연어 추천 / 라이브러리 패널 */}
        <aside className="af__side">
          <span className="af__sideBadge">✦ 플로우 편집</span>
          <p className="af__flowName">{flowName}</p>
          <h2 className="af__sideTitle">어떤 기능을 넣을까요?</h2>
          <textarea
            className="af__sideInput"
            placeholder="예: 실패하면 3번 재시도하고, 발송 전 승인 단계 추가해줘"
            value={sideText}
            onChange={(e) => setSideText(e.target.value)}
            maxLength={500}
          />
          <button
            className="af__recommend"
            type="button"
            onClick={handleRecommend}
            disabled={recLoading}
          >
            {recLoading ? "추천 중…" : "AI에게 추천받기"}
          </button>
          {recError && <p className="af__recMeta">에러: {recError}</p>}

          <p className="af__group">✦ AI 추천 · 스킬</p>
          {recSkill && (
            <div className="af__rec">
              <span className="af__recBar" style={{ background: NODE_COLOR.agent }} />
              <div className="af__recText">
                <p className="af__recTitle">{recSkill.name}</p>
                <p className="af__recMeta">{recSkill.description}</p>
              </div>
              <button
                className="af__recAdd"
                type="button"
                onClick={() =>
                  addNode({
                    kind: "agent",
                    typeLabel: "스킬",
                    title: recSkill.name,
                    op: recSkill.name,
                  })
                }
              >
                + 추가
              </button>
            </div>
          )}
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
          {recMcps.length === 0 && !recLoading && (
            <p className="af__recMeta">추천받으면 여기에 표시돼요.</p>
          )}
          {recMcps.map((key) => (
            <div className="af__rec" key={key}>
              <span className="af__recIcon" style={{ background: "#7a4fd6" }} />
              <div className="af__recText">
                <p className="af__recTitle">{key}</p>
                <p className="af__recMeta">MCP</p>
              </div>
              <button
                className="af__recAdd af__recAdd--icon"
                type="button"
                aria-label={`${key} 추가`}
                onClick={() =>
                  addNode({
                    kind: "tool",
                    typeLabel: "MCP",
                    title: key,
                    op: "mcp.call",
                    mcpKey: key,
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
        defaultName={flowName}
        onClose={() => setPublishOpen(false)}
        onPublish={handlePublish}
      />

      <KeyModal
        open={keyModalOpen}
        toolKey={keyTarget?.key ?? ""}
        tool={keyTarget?.tool ?? null}
        onClose={() => setKeyModalOpen(false)}
        onSave={async (secret) => {
          if (!keyTarget) return;
          // 저장은 로컬 실행기(POST /credential). 실패하면 throw → 모달이 에러 표시
          await saveCredential(keyTarget.key, secret);
          refreshSavedKeys(); // 패널을 '연결됨'으로 즉시 바꾼다
          setKeyModalOpen(false);
        }}
      />
    </div>
  );
}
