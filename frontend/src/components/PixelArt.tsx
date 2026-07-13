import type { CSSProperties } from "react";
import type { PixelSprite } from "../lib/pixelMaps";

interface PixelArtProps {
  sprite: PixelSprite;
  /** 접근성 라벨. 장식용이면 비워두면 aria-hidden 처리됨. */
  label?: string;
  className?: string;
  style?: CSSProperties;
}

/**
 * 픽셀맵을 SVG로 렌더. 크기는 CSS(width/height)로 조절 — 벡터라 무한 확대 가능.
 * 셀을 살짝(1.03) 겹쳐 스케일 시 seam(틈)이 생기지 않게 함.
 */
export function PixelArt({ sprite, label, className, style }: PixelArtProps) {
  const { map, palette } = sprite;
  const rows = map.length;
  const cols = Math.max(...map.map((row) => row.length));

  const cells = [];
  for (let y = 0; y < rows; y += 1) {
    const row = map[y];
    for (let x = 0; x < row.length; x += 1) {
      const color = palette[row[x]];
      if (color) {
        cells.push(<rect key={`${x}-${y}`} x={x} y={y} width={1.03} height={1.03} fill={color} />);
      }
    }
  }

  return (
    <svg
      viewBox={`0 0 ${cols} ${rows}`}
      className={className}
      style={style}
      shapeRendering="crispEdges"
      role={label ? "img" : "presentation"}
      aria-label={label || undefined}
      aria-hidden={label ? undefined : true}
    >
      {cells}
    </svg>
  );
}
