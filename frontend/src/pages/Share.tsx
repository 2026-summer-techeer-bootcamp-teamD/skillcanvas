import { useState } from "react";
import { PixelArt } from "../components/PixelArt";
import { TopNav, type NavTab } from "../components/TopNav";
import { GalleryCard } from "../components/GalleryCard";
import { NodeTrail } from "../components/NodeTrail";
import { ROBOT_BLACK } from "../lib/pixelMaps";
import { FEATURED, GALLERY_ITEMS, type GalleryItem, type ItemKind } from "../lib/galleryData";
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

  const items = GALLERY_ITEMS.filter((it) => filter === "all" || it.kind === filter);

  const handleImport = (item: GalleryItem) => {
    // TODO: 백엔드 연결 시 POST /workflows/{id}/import 또는 /skills/{id}/import
    console.log("[가져오기] import", item.id, item.title);
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

        {/* 그리드 */}
        <div className="share__grid">
          {items.map((item) => (
            <GalleryCard key={item.id} item={item} onImport={handleImport} />
          ))}
        </div>
      </main>
    </div>
  );
}
