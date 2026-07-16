// 로컬 실행기(localhost:4737) 클라이언트.
// 백엔드 useApi(Clerk 토큰 첨부)와 **별개** — 로컬 실행기는 사용자 PC에서 돌고 인증이 없다.
// 워크플로우 실제 실행(run) / 승인 재개(approve) / 상태 조회(status)를 담당한다.

import type { Edge, Node } from "reactflow";
import type { FlowNodeData } from "./flowData";

const RUNNER_BASE = import.meta.env.VITE_RUNNER_URL ?? "http://localhost:4737";

export interface RunResultItem {
  id: string;
  label: string;
  type: string | null;
  result: string;
}

export interface RunResponse {
  run_id: string;
  status: "done" | "awaiting_approval" | "stopped";
  results: RunResultItem[];
  pending?: { id: string; message: string };
}

export class RunnerError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "RunnerError";
  }
}

async function runnerFetch<T>(path: string, opts: RequestInit = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${RUNNER_BASE}${path}`, {
      ...opts,
      headers: { "Content-Type": "application/json", ...opts.headers },
    });
  } catch {
    // fetch 자체가 터짐 = 로컬 실행기 미기동(연결 거부)
    throw new RunnerError("로컬 실행기에 연결할 수 없어요. 로컬 실행기를 먼저 실행해 주세요.");
  }
  if (!res.ok) {
    let detail: unknown = null;
    try {
      detail = await res.json();
    } catch {
      /* 본문 없음 */
    }
    const msg =
      (detail as { detail?: { message?: string } })?.detail?.message ??
      `실행기 오류 (${res.status})`;
    throw new RunnerError(msg);
  }
  return res.json() as Promise<T>;
}

/** ReactFlow 그래프 → 러너 형식 {nodes, edges}. kind가 곧 러너 type. */
export function toRunnerGraph(nodes: Node<FlowNodeData>[], edges: Edge[]) {
  return {
    nodes: nodes.map((n) => ({
      id: n.id,
      type: n.data.kind, // trigger/tool/agent/output/approve
      label: n.data.title,
      detail: n.data.op,
      // 실행기가 어느 키를 꺼낼지 알아야 한다(카탈로그 key). detail은 노드를 만든 경로에
      // 따라 "discord"(assemble)일 수도 "mcp.call"(추천패널)일 수도 있어 신뢰 불가.
      ...(n.data.mcpKey ? { mcp_key: n.data.mcpKey } : {}),
    })),
    edges: edges.map((e) => ({ from: e.source, to: e.target })),
  };
}

/** 워크플로우 실행 시작. 승인 게이트를 만나면 status=awaiting_approval 로 멈춘다. */
export function runFlow(nodes: Node<FlowNodeData>[], edges: Edge[], itemKey?: string) {
  const graph = toRunnerGraph(nodes, edges);
  return runnerFetch<RunResponse>("/run", {
    method: "POST",
    body: JSON.stringify(itemKey ? { ...graph, item_key: itemKey } : graph),
  });
}

/** 승인 후 이어서 실행. 반환 results는 이번에 새로 실행된 것만(델타). */
export function approveRun(runId: string) {
  return runnerFetch<RunResponse>(`/run/${runId}/approve`, { method: "POST" });
}

/** 실행 상태·전체 결과 조회. */
export function getRunStatus(runId: string) {
  return runnerFetch<RunResponse>(`/run/${runId}/status`);
}

// ── 부품 창고 (.claude 파일 다루기) ─────────────────────
export interface RunnerGraphNode {
  id: string;
  type: string; // graph: mcp/rule/skill · flow: trigger/tool/agent/output/approve
  label: string;
  detail?: string;
}
export interface RunnerGraph {
  nodes: RunnerGraphNode[];
  edges: { from: string; to: string; kind?: string }[];
}

/** A-1: 로컬 .claude를 노드 그래프로 조회(부품 시각화). */
export function getGraph() {
  return runnerFetch<RunnerGraph>("/graph");
}

/** A-2: 스킬 구조를 로컬 SKILL.md로 저장(본문 보존). */
export function saveSkill(
  skill: string,
  name: string,
  description: string,
  allowedTools: string[],
  body?: string,
) {
  // body 미지정(undefined)이면 JSON에서 빠져 러너가 기존 본문 보존(backward compat)
  return runnerFetch<RunnerGraph>("/save", {
    method: "POST",
    body: JSON.stringify({ skill, name, description, allowed_tools: allowedTools, body }),
  });
}

/** A-6: 도구 API 키를 로컬에 저장. */
export function saveCredential(toolKey: string, secret: string) {
  return runnerFetch<{ ok: boolean; tool_key: string }>("/credential", {
    method: "POST",
    body: JSON.stringify({ tool_key: toolKey, secret }),
  });
}
