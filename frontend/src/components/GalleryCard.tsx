import { PixelArt } from "./PixelArt";
import { NodeTrail } from "./NodeTrail";
import { ROBOT_ORANGE } from "../lib/pixelMaps";
import type { GalleryItem } from "../lib/galleryData";
import "./GalleryCard.css";

interface GalleryCardProps {
  item: GalleryItem;
  onImport?: (item: GalleryItem) => void;
  onOpen?: (item: GalleryItem) => void;
}

export function GalleryCard({ item, onImport, onOpen }: GalleryCardProps) {
  return (
    <article className="gcard" onClick={() => onOpen?.(item)}>
      <div className="gcard__top">
        <span className={`gcard__kind gcard__kind--${item.kind}`}>
          {item.kind === "workflow" ? "워크플로우" : "스킬"}
        </span>
        <PixelArt sprite={ROBOT_ORANGE} className="gcard__mascot" />
      </div>

      <h3 className="gcard__title">{item.title}</h3>
      <p className="gcard__desc">{item.description}</p>

      <NodeTrail className="gcard__trail" />

      <div className="gcard__tags">
        {item.tags.map((t) => (
          <span className="gcard__tag" key={t}>
            #{t}
          </span>
        ))}
      </div>

      <div className="gcard__foot">
        <span className="gcard__meta">
          @{item.owner} · <span className="gcard__imports">↓ {item.imports}</span>
        </span>
        <button
          className="gcard__import"
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onImport?.(item);
          }}
        >
          가져오기 ↓
        </button>
      </div>
    </article>
  );
}
