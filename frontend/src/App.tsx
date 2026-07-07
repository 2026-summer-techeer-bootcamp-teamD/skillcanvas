import { Background, Controls, ReactFlow, type Edge, type Node } from "reactflow";
import "reactflow/dist/style.css";

// 뼈대 확인용 노드 1개. 실제 캔버스(부품/워크플로우)는 여기부터 구현.
const nodes: Node[] = [
  {
    id: "1",
    position: { x: 120, y: 120 },
    data: { label: "SkillCanvas 캔버스 뼈대 ✅" },
  },
];
const edges: Edge[] = [];

export default function App() {
  return (
    <div style={{ width: "100vw", height: "100vh" }}>
      <ReactFlow nodes={nodes} edges={edges} fitView>
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
}
