import "./NodeTrail.css";

const TRAIL_COLORS = [
  "var(--sc-accent)",
  "var(--sc-node-tool)",
  "var(--sc-node-agent)",
  "var(--sc-node-output)",
];

/** 카드에 얹는 노드 흐름 모티프 (점 4개를 잇는 선) */
export function NodeTrail({ className }: { className?: string }) {
  return (
    <div className={className ? `trail ${className}` : "trail"} aria-hidden="true">
      {TRAIL_COLORS.map((c, i) => (
        <span key={i} className="trail__dot" style={{ background: c }} />
      ))}
    </div>
  );
}
