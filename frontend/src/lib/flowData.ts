import type { Node, Edge } from "reactflow";
import { MarkerType } from "reactflow";

export type FlowNodeKind = "trigger" | "tool" | "agent" | "output" | "approve";

export interface FlowNodeData {
  kind: FlowNodeKind;
  typeLabel: string;
  title: string;
  op: string;
  /** MCP 도구처럼 본인 키 연결이 필요한 노드 */
  needsKey?: boolean;
  /** 노드의 × 버튼 핸들러 (렌더 시 주입) */
  onDelete?: (id: string) => void;
}

export const NODE_COLOR: Record<FlowNodeKind, string> = {
  trigger: "var(--sc-node-trigger)",
  tool: "var(--sc-node-tool)",
  agent: "var(--sc-node-agent)",
  output: "var(--sc-node-output)",
  approve: "var(--sc-node-approve)",
};

/** cs-complaint-handler 예시 플로우 (자연어 추천 결과 목업) */
export const INITIAL_NODES: Node<FlowNodeData>[] = [
  {
    id: "n1",
    type: "flow",
    position: { x: 40, y: 180 },
    data: { kind: "trigger", typeLabel: "트리거", title: "웹훅 시작", op: "trigger.webhook" },
  },
  {
    id: "n2",
    type: "flow",
    position: { x: 330, y: 40 },
    data: { kind: "tool", typeLabel: "도구", title: "페이지 가져오기", op: "http.get" },
  },
  {
    id: "n3",
    type: "flow",
    position: { x: 330, y: 300 },
    data: { kind: "tool", typeLabel: "도구", title: "본문 추출", op: "html.parse" },
  },
  {
    id: "n4",
    type: "flow",
    position: { x: 630, y: 180 },
    data: { kind: "agent", typeLabel: "에이전트", title: "요약 생성", op: "claude.summarize" },
  },
  {
    id: "n5",
    type: "flow",
    position: { x: 910, y: 90 },
    data: {
      kind: "output",
      typeLabel: "출력",
      title: "Slack 전송",
      op: "slack.post",
      needsKey: true,
    },
  },
];

const EDGE_STYLE = {
  stroke: "#e8843c",
  strokeWidth: 1.6,
  strokeDasharray: "5 5",
};

function edge(id: string, source: string, target: string): Edge {
  return {
    id,
    source,
    target,
    animated: true,
    style: EDGE_STYLE,
    markerEnd: { type: MarkerType.ArrowClosed, color: "#e8843c" },
  };
}

export const INITIAL_EDGES: Edge[] = [
  edge("e1", "n1", "n2"),
  edge("e2", "n1", "n3"),
  edge("e3", "n2", "n4"),
  edge("e4", "n3", "n4"),
  edge("e5", "n4", "n5"),
];
