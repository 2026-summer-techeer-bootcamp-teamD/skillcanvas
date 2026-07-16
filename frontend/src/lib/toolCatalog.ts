// 도구 카탈로그(GET /tool-catalog) 응답 타입. 키 붙여넣기 팝업을 이 메타로 자동 생성한다.

/** 입력칸 하나. name은 실행기가 MCP 서버에 넘길 환경변수명과 일치해야 한다
 *  (local-runner/app/core/mcp.py 의 MCP_SERVERS[*].env_fields). */
export interface ToolMetaField {
  name: string;
  placeholder?: string;
  help?: string;
}

export interface ToolMeta {
  /** 입력칸 여러 개 (예: 텔레그램=토큰+chat_id). 값은 JSON으로 묶여 저장된다. */
  fields?: ToolMetaField[];
  /** 발급 절차 안내. 링크 하나만 던지면 사용자가 헤매서, 단계로 보여준다. */
  guide?: string[];
  /** @deprecated fields를 쓸 것. 입력칸이 하나뿐이던 시절의 형식 */
  field?: string;
  /** @deprecated fields[].help 를 쓸 것 */
  help?: string;
  /** @deprecated fields[].placeholder 를 쓸 것 */
  placeholder?: string;
}

export interface ToolCatalogItem {
  id: number;
  key: string;
  name: string;
  type: string; // mcp / api
  auth_owner: string; // user(본인 붙여넣기) / developer(공용키)
  key_required: boolean;
  key_issue_url: string | null;
  description: string | null;
  metadata_json: ToolMeta | null;
}
