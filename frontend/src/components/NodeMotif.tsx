/** 배경 노드 칩 (SVG). viewBox 좌표는 Figma 모티프와 동일. */
function MotifChip({ x, y, dot }: { x: number; y: number; dot: string }) {
  return (
    <g transform={`translate(${x} ${y})`}>
      <rect width="96" height="34" rx="9" fill="rgba(255,255,255,0.55)" stroke="var(--sc-line)" />
      <rect x="12" y="13" width="8" height="8" rx="2" fill={dot} />
      <rect x="30" y="14" width="48" height="6" rx="3" fill="var(--sc-line)" />
    </g>
  );
}

/** 은은한 노드 그래프 모티프 — 좌상단·우하단 코너 클러스터 + 주황 점선 커넥터. 페이지 공용 배경 장식. */
export function NodeMotif() {
  return (
    <svg
      className="sc-motif"
      viewBox="0 0 1280 800"
      preserveAspectRatio="xMidYMid slice"
      aria-hidden="true"
    >
      <g opacity="0.6">
        <line x1="150" y1="150" x2="150" y2="250" className="sc-motif__line" />
        <line x1="198" y1="267" x2="300" y2="267" className="sc-motif__line" />
        <line x1="398" y1="267" x2="494" y2="267" className="sc-motif__dash" />
        <rect x="496" y="262" width="11" height="11" rx="3" fill="var(--sc-accent)" />
        <MotifChip x={102} y={116} dot="var(--sc-node-trigger)" />
        <MotifChip x={102} y={250} dot="var(--sc-node-tool)" />
        <MotifChip x={300} y={250} dot="var(--sc-node-agent)" />
      </g>
      <g opacity="0.5">
        <line x1="1030" y1="540" x2="1030" y2="640" className="sc-motif__line" />
        <line x1="980" y1="557" x2="1082" y2="557" className="sc-motif__line" />
        <MotifChip x={1082} y={523} dot="var(--sc-node-output)" />
        <MotifChip x={1082} y={640} dot="var(--sc-node-approve)" />
      </g>
    </svg>
  );
}
