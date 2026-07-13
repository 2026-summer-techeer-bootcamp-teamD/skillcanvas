import { Handle, Position, type NodeProps } from "reactflow";
import { NODE_COLOR, type FlowNodeData } from "../../lib/flowData";
import "./FlowNode.css";

export function FlowNode({ id, data, selected }: NodeProps<FlowNodeData>) {
  return (
    <div className={selected ? "afn afn--selected" : "afn"}>
      <Handle type="target" position={Position.Left} className="afn__handle" />

      <div className="afn__head">
        <span className="afn__icon" style={{ color: NODE_COLOR[data.kind] }}>
          ◆
        </span>
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
