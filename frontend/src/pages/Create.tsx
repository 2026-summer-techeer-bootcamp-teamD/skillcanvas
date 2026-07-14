import { useState } from "react";
import { PixelArt } from "../components/PixelArt";
import { TopNav, type NavTab } from "../components/TopNav";
import { ROBOT_BLACK, ROBOT_ORANGE } from "../lib/pixelMaps";
import { classifyIntent, type Intent } from "../lib/classifyIntent";
import "./Create.css";

const EXAMPLES = [
  "매일 CS 컴플레인 오면 긴급도 보고 배송조회해서 사과·쿠폰 발송",
  "회의록을 3줄로 요약해서 정리",
  "받은 메일 분류해서 라벨 붙이기",
];

type Phase = "input" | "classifying" | "choose";
type Choice = "skill" | "workflow";

interface CreateProps {
  onNavigate?: (tab: NavTab) => void;
  /** 선택 확정 시 해당 빌더로 입력 텍스트와 함께 이동 */
  onCreate?: (choice: Choice, text: string) => void;
}

export function Create({ onNavigate, onCreate }: CreateProps) {
  const [phase, setPhase] = useState<Phase>("input");
  const [text, setText] = useState("");
  const [intent, setIntent] = useState<Intent>("neutral");
  const [selected, setSelected] = useState<Choice | null>(null);

  const run = async (value: string) => {
    if (!value.trim()) return;
    setText(value);
    setSelected(null);
    setPhase("classifying");
    const result = await classifyIntent(value);
    setIntent(result);
    setPhase("choose");
  };

  const confirm = () => {
    if (!selected) return;
    onCreate?.(selected, text);
  };

  const chip = (kind: Choice, label: string) => {
    const recommended = intent === kind; // 크기 강조 대상
    const isSel = selected === kind;
    const cls = ["cr__chip", recommended ? "cr__chip--rec" : "", isSel ? "cr__chip--sel" : ""]
      .filter(Boolean)
      .join(" ");
    return (
      <button type="button" className={cls} onClick={() => setSelected(kind)}>
        {recommended && <span className="cr__recBadge">추천</span>}
        {label}
      </button>
    );
  };

  return (
    <div className="cr">
      <TopNav active="CREATE" onNavigate={onNavigate} />

      <main className="cr__hero">
        <div className="cr__mascots" aria-hidden="true">
          <PixelArt sprite={ROBOT_BLACK} className="cr__mascot" />
          <PixelArt sprite={ROBOT_ORANGE} className="cr__mascot" />
          <PixelArt sprite={ROBOT_BLACK} className="cr__mascot" />
        </div>

        <h1 className="cr__title">무엇을 만들고 싶으세요?</h1>

        {phase === "input" && (
          <p className="cr__sub">
            하고 싶은 일을 문장으로 적으면, 스킬이나 오토플로우로 만들어 드려요.
          </p>
        )}

        {/* 입력창은 항상 표시 (choose에서는 맥락으로 유지) */}
        <form
          className={phase === "choose" ? "cr__inputRow cr__inputRow--ctx" : "cr__inputRow"}
          onSubmit={(e) => {
            e.preventDefault();
            run(text);
          }}
        >
          <input
            className="cr__input"
            placeholder="예: 매일 CS 컴플레인 오면 긴급도 보고 배송조회해서 사과·쿠폰 발송"
            value={text}
            onChange={(e) => setText(e.target.value)}
            readOnly={phase === "choose"}
          />
          {phase !== "choose" && (
            <button className="cr__make" type="submit" disabled={phase === "classifying"}>
              {phase === "classifying" ? "보는 중…" : "만들기"}
            </button>
          )}
        </form>

        {phase === "input" && (
          <div className="cr__examples">
            {EXAMPLES.map((ex) => (
              <button key={ex} type="button" className="cr__example" onClick={() => run(ex)}>
                {ex}
              </button>
            ))}
          </div>
        )}

        {phase === "classifying" && <p className="cr__loading">어디에 더 가까운지 보는 중…</p>}

        {phase === "choose" && (
          <div className="cr__choose">
            <div className="cr__chips">
              {chip("skill", "스킬")}
              {chip("workflow", "오토플로우")}
            </div>
            <button
              className={selected ? "cr__go" : "cr__go cr__go--wait"}
              type="button"
              onClick={confirm}
              disabled={!selected}
            >
              {selected ? "이걸로 만들기" : "타입을 고르면 활성"}
            </button>
            <button className="cr__back" type="button" onClick={() => setPhase("input")}>
              ← 다시 입력
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
