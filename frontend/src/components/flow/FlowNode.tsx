import { Handle, Position, type NodeProps } from "reactflow";
import { NODE_COLOR, type FlowNodeData } from "../../lib/flowData";
import "./FlowNode.css";

// 실행 상태별 표시(테두리색 + 배지)
const RUN_STYLE: Record<NonNullable<FlowNodeData["runState"]>, { color: string; badge: string }> = {
  done: { color: "#2e9e5b", badge: "✓" },
  pending: { color: "#e8843c", badge: "🚨" },
  stopped: { color: "#9a938a", badge: "⛔" },
};

export function FlowNode({ id, data, selected }: NodeProps<FlowNodeData>) {
  const run = data.runState ? RUN_STYLE[data.runState] : null;
  return (
    <div
      className={selected ? "afn afn--selected" : "afn"}
      style={
        run
          ? { position: "relative", borderColor: run.color, boxShadow: `0 0 0 2px ${run.color}55` }
          : undefined
      }
    >
      <Handle type="target" position={Position.Left} className="afn__handle" />

      <div className="afn__head">
        <span className="afn__icon" style={{ color: NODE_COLOR[data.kind] }}>
          ◆
        </span>
        {run && (
          <span
            aria-label={`상태: ${data.runState}`}
            style={{
              position: "absolute",
              top: -8,
              right: -8,
              width: 20,
              height: 20,
              borderRadius: "50%",
              background: run.color,
              color: "#fff",
              fontSize: 11,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {run.badge}
          </span>
        )}
        <div className="afn__text">
          <p className="afn__title">{data.title}</p>
          <p className="afn__op">{data.op}</p>
        </div>
        <button
          className="afn__del"
          type="button"
          aria-label="노드 삭제"
          onClick={(e) => {
            e.stopPropagation();
            data.onDelete?.(id);
          }}
        >
          ×
        </button>
      </div>

      <div className="afn__edit">
        <span aria-hidden="true">✎</span>
        <input className="afn__editInput" placeholder="편집" />
      </div>

      <Handle type="source" position={Position.Right} className="afn__handle" />
    </div>
  );
}
