// 도구 카탈로그(GET /tool-catalog) 응답 타입. 키 붙여넣기 팝업을 이 메타로 자동 생성한다.
export interface ToolMeta {
  /** 붙여넣을 필드명 (예: SLACK_BOT_TOKEN) */
  field?: string;
  /** 안내 문구 */
  help?: string;
  /** 입력창 placeholder */
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
