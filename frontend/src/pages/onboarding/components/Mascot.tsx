import type { CSSProperties } from "react";

interface MascotProps {
  size?: number;
  style?: CSSProperties;
}

// ---- Mini pixel-art mascot (pure CSS, no image asset) ----------------------
// size: rendered box size in px. The pattern is authored on a 21px grid then
// scaled via transform, so it stays crisp at any requested size.
export default function Mascot({ size = 21, style }: MascotProps) {
  const scale = size / 21;
  const shadow =
    "6px 0 0 0 rgb(232,132,60), 12px 0 0 0 rgb(232,132,60), " +
    "0px 3px 0 0 rgb(42,38,32), 3px 3px 0 0 rgb(42,38,32), 6px 3px 0 0 rgb(42,38,32), 9px 3px 0 0 rgb(42,38,32), 12px 3px 0 0 rgb(42,38,32), 15px 3px 0 0 rgb(42,38,32), 18px 3px 0 0 rgb(42,38,32), " +
    "0px 6px 0 0 rgb(42,38,32), 6px 6px 0 0 rgb(42,38,32), 9px 6px 0 0 rgb(42,38,32), 12px 6px 0 0 rgb(42,38,32), 18px 6px 0 0 rgb(42,38,32), " +
    "0px 9px 0 0 rgb(42,38,32), 3px 9px 0 0 rgb(42,38,32), 6px 9px 0 0 rgb(42,38,32), 9px 9px 0 0 rgb(42,38,32), 12px 9px 0 0 rgb(42,38,32), 15px 9px 0 0 rgb(42,38,32), 18px 9px 0 0 rgb(42,38,32), " +
    "3px 12px 0 0 rgb(42,38,32), 6px 12px 0 0 rgb(232,132,60), 9px 12px 0 0 rgb(232,132,60), 12px 12px 0 0 rgb(232,132,60), 15px 12px 0 0 rgb(42,38,32), " +
    "0px 15px 0 0 rgb(42,38,32), 3px 15px 0 0 rgb(42,38,32), 6px 15px 0 0 rgb(42,38,32), 9px 15px 0 0 rgb(42,38,32), 12px 15px 0 0 rgb(42,38,32), 15px 15px 0 0 rgb(42,38,32), 18px 15px 0 0 rgb(42,38,32), " +
    "3px 18px 0 0 rgb(42,38,32), 15px 18px 0 0 rgb(42,38,32)";
  return (
    <div
      style={{
        width: size,
        height: size,
        flexShrink: 0,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        ...style,
      }}
    >
      <div style={{ width: 21, height: 21, transform: `scale(${scale})` }}>
        <div style={{ width: 3, height: 3, boxShadow: shadow }} />
      </div>
    </div>
  );
}
