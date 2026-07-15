import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import ReactFlow, {
  Background,
  BackgroundVariant,
  type Edge,
  type Node,
  type NodeProps,
} from "reactflow";
import "reactflow/dist/style.css";
import { useApi, ApiError } from "../lib/api";
import { PixelArt } from "../components/PixelArt";
import { TopNav, type NavTab } from "../components/TopNav";
import { GalleryCard } from "../components/GalleryCard";
import { NodeTrail } from "../components/NodeTrail";
import { FlowNode } from "../components/flow/FlowNode";
import type { FlowNodeData } from "../lib/flowData";
import { ROBOT_BLACK } from "../lib/pixelMaps";
import { FEATURED, type GalleryItem, type ItemKind } from "../lib/galleryData";
import "./Share.css";

const FILTERS: { key: "all" | ItemKind; label: string }[] = [
  { key: "all", label: "전체" },
  { key: "workflow", label: "워크플로우" },
  { key: "skill", label: "스킬" },
];

// 상세 미리보기는 읽기 전용 — 삭제/편집 컨트롤을 숨긴 FlowNode를 쓴다.
const readOnlyFlowNodeTypes = {
  flow: (props: NodeProps<FlowNodeData>) => <FlowNode {...props} readOnly />,
};
const proOptions = { hideAttribution: true };

const apiBaseFor = (kind: ItemKind) => (kind === "workflow" ? "workflows" : "skills");

interface DetailBase {
  id: number;
  name: string;
  description: string | null;
  owner: { nickname: string };
  tags: string[];
  import_count: number;
}
interface SkillDetail extends DetailBase {
  content_md: string;
}
interface WorkflowDetail extends DetailBase {
  // 백엔드는 graph_json을 검증되지 않은 dict로 저장 — nodes/edges가 없을 수도 있다고 가정한다.
  graph_json: { nodes?: Node[]; edges?: Edge[] };
}

interface ShareProps {
  onNavigate?: (tab: NavTab) => void;
}

export function Share({ onNavigate }: ShareProps) {
  const navigate = useNavigate();
  const params = useParams<{ kind?: string; id?: string }>();
  const [filter, setFilter] = useState<"all" | ItemKind>("all");
  const [tags, setTags] = useState<string[]>([]);
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const call = useApi();
  const [items, setItems] = useState<GalleryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 상세보기 모달 — URL(/share/:kind/:id)과 동기화해 딥링크·뒤로가기가 되게 한다.
  const rawKind = params.kind ?? null;
  const rawId = params.id ?? null;
  const detailKind: ItemKind | null =
    rawKind === "workflow" ? "workflow" : rawKind === "skill" ? "skill" : null;
  const [detail, setDetail] = useState<SkillDetail | WorkflowDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  // GET /skills/{id} 또는 /workflows/{id} — 카드 클릭 시 상세 조회 (비공개는 404)
  useEffect(() => {
    if (!rawKind || !rawId) {
      setDetail(null);
      setDetailError(null);
      setDetailLoading(false);
      return;
    }
    if (!detailKind) {
      // :kind가 skill/workflow가 아닌 잘못된 링크 — 조용히 무시하지 않고 에러로 보여준다.
      setDetail(null);
      setDetailLoading(false);
      setDetailError("지원하지 않는 링크예요.");
      return;
    }
    let ignore = false;
    setDetail(null);
    setDetailError(null);
    setDetailLoading(true);
    call<SkillDetail | WorkflowDetail>(`/${apiBaseFor(detailKind)}/${rawId}`)
      .then((data) => {
        if (!ignore) setDetail(data);
      })
      .catch((e) => {
        if (!ignore) setDetailError(e instanceof ApiError ? e.message : "불러오기 실패");
      })
      .finally(() => {
        if (!ignore) setDetailLoading(false);
      });
    return () => {
      ignore = true;
    };
  }, [call, rawKind, rawId, detailKind]);

  // GET /tags — 필터 칩용 태그 목록
  useEffect(() => {
    call<{ items: { id: number; name: string }[] }>("/tags")
      .then((data) => setTags(data.items.map((t) => t.name)))
      .catch(() => {
        /* 태그 칩은 부가 기능 — 실패해도 갤러리는 계속 보여준다 */
      });
  }, [call]);

  // GET /skills + GET /workflows — 공개 목록을 하나의 갤러리로. 태그 선택 시 ?tag= 필터.
  useEffect(() => {
    let ignore = false;
    setLoading(true);
    setError(null);
    type ListItem = {
      id: number;
      name: string;
      description: string | null;
      owner: { nickname: string };
      tags: string[];
      import_count: number;
      created_at: string;
    };
    const tagQ = selectedTag ? `&tag=${encodeURIComponent(selectedTag)}` : "";
    // allSettled: 한쪽 API가 죽어도 다른 쪽은 계속 보여준다
    Promise.allSettled([
      call<{ items: ListItem[] }>(`/skills?sort=recent${tagQ}`),
      call<{ items: ListItem[] }>(`/workflows?sort=recent${tagQ}`),
    ]).then(([skillsRes, wfRes]) => {
      if (ignore) return;
      const pick = (res: PromiseSettledResult<{ items: ListItem[] }>, kind: ItemKind) =>
        res.status === "fulfilled" ? res.value.items.map((x) => ({ ...x, kind })) : [];
      // 스킬·워크플로우를 합쳐 created_at 최신순으로 정렬 (단순 concat이면 종류별로 뭉침)
      const merged = [...pick(skillsRes, "skill"), ...pick(wfRes, "workflow")].sort((a, b) =>
        b.created_at.localeCompare(a.created_at),
      );
      setItems(
        merged.map((x): GalleryItem => ({
          id: String(x.id),
          kind: x.kind,
          title: x.name,
          description: x.description ?? "",
          tags: x.tags,
          owner: x.owner.nickname,
          imports: x.import_count,
        })),
      );
      // 둘 다 실패한 경우에만 에러 표시
      if (skillsRes.status === "rejected" && wfRes.status === "rejected") {
        setError(skillsRes.reason instanceof ApiError ? skillsRes.reason.message : "불러오기 실패");
      }
      setLoading(false);
    });
    return () => {
      ignore = true;
    };
  }, [call, selectedTag]);

  const shown = items.filter((it) => filter === "all" || it.kind === filter);

  // 실제 백엔드 항목만 (피처드 등 목업 카드는 제외)
  const isRealItem = (item: GalleryItem) =>
    items.some((it) => it.kind === item.kind && it.id === item.id);

  // POST /{skills|workflows}/{id}/import — 종류별로 라우팅해 가져오기
  const handleImport = async (item: GalleryItem) => {
    if (!isRealItem(item)) {
      alert("예시 카드예요. 아래 갤러리에서 가져오세요.");
      return;
    }
    try {
      const data = await call<{ import_count: number }>(
        `/${apiBaseFor(item.kind)}/${item.id}/import`,
        { method: "POST" },
      );
      setItems((prev) =>
        prev.map((it) =>
          it.kind === item.kind && it.id === item.id ? { ...it, imports: data.import_count } : it,
        ),
      );
    } catch (e) {
      alert(e instanceof ApiError ? e.message : "가져오기 실패");
    }
  };

  // 카드 클릭 → /share/{kind}/{id}로 이동해 상세 모달을 연다 (뒤로가기·공유 링크 가능)
  // 열기/닫기 모두 replace — 카드를 여러 개 열었다 닫아도 히스토리 스택이 쌓이지 않는다.
  const openDetail = (item: GalleryItem) => {
    if (!isRealItem(item)) {
      alert("예시 카드예요. 아래 갤러리에서 가져오세요.");
      return;
    }
    navigate(`/share/${item.kind}/${item.id}`, { replace: true });
  };

  const closeDetail = () => navigate("/share", { replace: true });

  const handleDetailImport = async () => {
    if (!detail || !detailKind) return;
    try {
      const data = await call<{ import_count: number }>(
        `/${apiBaseFor(detailKind)}/${detail.id}/import`,
        { method: "POST" },
      );
      setDetail((prev) => (prev ? { ...prev, import_count: data.import_count } : prev));
      setItems((prev) =>
        prev.map((it) =>
          it.kind === detailKind && it.id === String(detail.id)
            ? { ...it, imports: data.import_count }
            : it,
        ),
      );
    } catch (e) {
      alert(e instanceof ApiError ? e.message : "가져오기 실패");
    }
  };

  return (
    <div className="share">
      <TopNav active="SHARE" onNavigate={onNavigate} />

      <main className="share__main">
        <div className="share__head">
          <h1 className="share__title">
            갤러리
            <PixelArt sprite={ROBOT_BLACK} className="share__titleMascot" />
          </h1>
          <p className="share__sub">
            남들이 만든 워크플로우·스킬을 가져와 내 캔버스에 바로 올려보세요.
          </p>
        </div>

        {/* 피처드 */}
        <section className="share__featured">
          <div className="share__featuredBody">
            <span className="gcard__kind gcard__kind--workflow">워크플로우</span>
            <h2 className="share__featuredTitle">{FEATURED.title}</h2>
            <p className="share__featuredDesc">{FEATURED.description}</p>
            <p className="share__featuredStats">
              <span className="share__stars">★★★★★</span> {FEATURED.rating} · ⌱ {FEATURED.installs}{" "}
              설치 · @{FEATURED.owner}
            </p>
            <button className="share__stack" type="button" onClick={() => handleImport(FEATURED)}>
              ↓ 내 캔버스에 STACK
            </button>
          </div>
          <div className="share__featuredArt" aria-hidden="true">
            <PixelArt sprite={ROBOT_BLACK} className="share__featuredMascot" />
            <NodeTrail className="share__featuredTrail" />
          </div>
        </section>

        {/* 필터 */}
        <div className="share__filters">
          {FILTERS.map((f) => (
            <button
              key={f.key}
              type="button"
              className={f.key === filter ? "share__filter share__filter--on" : "share__filter"}
              onClick={() => setFilter(f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* 태그 칩 */}
        {tags.length > 0 && (
          <div className="share__tags">
            <button
              type="button"
              className={selectedTag === null ? "share__tag share__tag--on" : "share__tag"}
              onClick={() => setSelectedTag(null)}
            >
              전체 태그
            </button>
            {tags.map((tag) => (
              <button
                key={tag}
                type="button"
                className={tag === selectedTag ? "share__tag share__tag--on" : "share__tag"}
                onClick={() => setSelectedTag(tag === selectedTag ? null : tag)}
              >
                #{tag}
              </button>
            ))}
          </div>
        )}

        {loading && <p className="share__sub">불러오는 중…</p>}
        {error && <p className="share__sub">에러: {error}</p>}
        {!loading && !error && shown.length === 0 && (
          <p className="share__sub">조건에 맞는 결과가 없어요.</p>
        )}
        {/* 그리드 */}
        <div className="share__grid">
          {shown.map((item) => (
            <GalleryCard
              key={`${item.kind}-${item.id}`}
              item={item}
              onImport={handleImport}
              onOpen={openDetail}
            />
          ))}
        </div>
      </main>

      {rawKind && rawId && (
        <div className="share__modalBackdrop" onClick={closeDetail}>
          <div className="share__modal" onClick={(e) => e.stopPropagation()}>
            {/* 닫기 버튼은 로딩/에러 상태에서도 항상 보여야 한다 */}
            <header className="share__modalHead">
              <div>
                {detail ? (
                  <>
                    <p className="share__modalKicker">
                      {detailKind === "workflow" ? "워크플로우" : "스킬"} · @{detail.owner.nickname}
                    </p>
                    <h3 className="share__modalTitle">{detail.name}</h3>
                    {detail.description && <p className="share__modalDesc">{detail.description}</p>}
                    {detail.tags.length > 0 && (
                      <div className="share__modalTags">
                        {detail.tags.map((t) => (
                          <span className="share__modalTag" key={t}>
                            #{t}
                          </span>
                        ))}
                      </div>
                    )}
                  </>
                ) : (
                  <p className="share__modalKicker">
                    {detailKind === "workflow"
                      ? "워크플로우"
                      : detailKind === "skill"
                        ? "스킬"
                        : "링크"}
                  </p>
                )}
              </div>
              <div className="share__modalActions">
                {detail && (
                  <button className="share__modalImport" type="button" onClick={handleDetailImport}>
                    ↓ 가져오기 ({detail.import_count})
                  </button>
                )}
                <button
                  className="share__modalClose"
                  type="button"
                  aria-label="닫기"
                  onClick={closeDetail}
                >
                  ✕
                </button>
              </div>
            </header>

            {detailLoading && <p className="share__modalState">불러오는 중…</p>}
            {detailError && <p className="share__modalState">에러: {detailError}</p>}
            {detail &&
              (detailKind === "skill" ? (
                <div className="share__modalMd">
                  <ReactMarkdown>{(detail as SkillDetail).content_md}</ReactMarkdown>
                </div>
              ) : (
                <div className="share__modalCanvas">
                  <ReactFlow
                    // 발행자의 마지막 실행 상태(runState)는 사적 정보 — 공개 미리보기에는 노출하지 않는다.
                    nodes={((detail as WorkflowDetail).graph_json.nodes ?? []).map((n) => ({
                      ...n,
                      data: { ...n.data, runState: undefined },
                    }))}
                    edges={(detail as WorkflowDetail).graph_json.edges ?? []}
                    nodeTypes={readOnlyFlowNodeTypes}
                    fitView
                    nodesDraggable={false}
                    nodesConnectable={false}
                    elementsSelectable={false}
                    proOptions={proOptions}
                  >
                    <Background
                      variant={BackgroundVariant.Dots}
                      gap={26}
                      size={1.4}
                      color="#ddd7c7"
                    />
                  </ReactFlow>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
