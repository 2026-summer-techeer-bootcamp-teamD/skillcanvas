import { useEffect, useState } from "react";
import { useApi, ApiError } from "../lib/api";
import { PixelArt } from "../components/PixelArt";
import { TopNav, type NavTab } from "../components/TopNav";
import { GalleryCard } from "../components/GalleryCard";
import { NodeTrail } from "../components/NodeTrail";
import { ROBOT_BLACK } from "../lib/pixelMaps";
import { FEATURED, type GalleryItem, type ItemKind } from "../lib/galleryData";
import "./Share.css";

const FILTERS: { key: "all" | ItemKind; label: string }[] = [
  { key: "all", label: "전체" },
  { key: "workflow", label: "워크플로우" },
  { key: "skill", label: "스킬" },
];

interface ShareProps {
  onNavigate?: (tab: NavTab) => void;
}

export function Share({ onNavigate }: ShareProps) {
  const [filter, setFilter] = useState<"all" | ItemKind>("all");
  const [tags, setTags] = useState<string[]>([]);
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const call = useApi();
  const [items, setItems] = useState<GalleryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  // POST /{skills|workflows}/{id}/import — 종류별로 라우팅해 가져오기
  const handleImport = async (item: GalleryItem) => {
    // 실제 백엔드 항목만 (피처드 등 목업 카드는 제외)
    if (!items.some((it) => it.kind === item.kind && it.id === item.id)) {
      alert("예시 카드예요. 아래 갤러리에서 가져오세요.");
      return;
    }
    const base = item.kind === "workflow" ? "workflows" : "skills";
    try {
      const data = await call<{ import_count: number }>(`/${base}/${item.id}/import`, {
        method: "POST",
      });
      setItems((prev) =>
        prev.map((it) =>
          it.kind === item.kind && it.id === item.id ? { ...it, imports: data.import_count } : it,
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
            <GalleryCard key={`${item.kind}-${item.id}`} item={item} onImport={handleImport} />
          ))}
        </div>
      </main>
    </div>
  );
}
