import { useCallback } from "react";
import { useAuth } from "@clerk/clerk-react";

// 프로덕션 빌드에서 VITE_API_BASE_URL이 없으면 localhost가 번들에 박혀 전 API가 실패한다.
// (Clerk 키처럼) 빌드/로드 시 크게 터뜨려 조용한 배포 사고를 막는다. 로컬 dev만 fallback 허용.
if (import.meta.env.PROD && !import.meta.env.VITE_API_BASE_URL) {
  throw new Error(
    "VITE_API_BASE_URL이 설정되지 않았습니다. 배포(Vercel 등) 환경변수를 확인하세요.",
  );
}
const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, detail: unknown) {
    const message =
      (detail as { detail?: { message?: string } })?.detail?.message ??
      (detail as { message?: string })?.message ??
      `요청 실패 (${status})`;
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

type FetchOptions = RequestInit & {
  /** Clerk 세션 토큰. useApi() 훅이 자동으로 채워준다. */
  token?: string | null;
  /** JSON으로 직렬화할 본문 */
  json?: unknown;
};

/** 저수준 호출 — 토큰을 직접 넘길 때 쓴다. 보통은 useApi() 훅을 쓰면 편하다. */
export async function apiFetch<T = unknown>(path: string, opts: FetchOptions = {}): Promise<T> {
  const { token, json, headers, ...rest } = opts;
  const res = await fetch(`${BASE}${path}`, {
    ...rest,
    headers: {
      ...(json !== undefined ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    body: json !== undefined ? JSON.stringify(json) : rest.body,
  });

  if (!res.ok) {
    let detail: unknown = null;
    try {
      detail = await res.json();
    } catch {
      /* 본문 없음 */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return res.json() as Promise<T>;
}

/**
 * 인증된 API 호출 훅. 매 호출마다 Clerk 세션 토큰(JWT)을 붙여 보낸다 — JWT 처리는 Clerk가 한다.
 *
 * 사용:
 *   const call = useApi();
 *   const wf = await call("/workflows", { method: "POST", json: { name, graph_json, ... } });
 */
export function useApi() {
  const { getToken } = useAuth();
  return useCallback(
    async <T = unknown>(path: string, opts: FetchOptions = {}) => {
      const token = await getToken();
      return apiFetch<T>(path, { ...opts, token });
    },
    [getToken],
  );
}
