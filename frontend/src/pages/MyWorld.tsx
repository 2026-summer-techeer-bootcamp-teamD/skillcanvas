import { useState } from "react";
import { TopNav, type NavTab } from "../components/TopNav";
import { NodeTrail } from "../components/NodeTrail";
import "./MyWorld.css";

const WORLDS = [
  { name: "My World", icon: "🌐" },
  { name: "Team-Growth", icon: "📈" },
  { name: "Team-Ops", icon: "🛠" },
];

const MW_SKILLS = [
  { title: "본문 요약", meta: "claude-sonnet", color: "var(--sc-node-agent)" },
  { title: "우선순위 분류", meta: "rules + LLM", color: "var(--sc-node-tool)" },
  { title: "감정 분석", meta: "CS 티켓 태깅", color: "var(--sc-accent)" },
  { title: "키워드 추출", meta: "claude-sonnet", color: "var(--sc-node-output)" },
];

const MW_FLOWS = [
  { title: "메일 비서", desc: "받은 편지함 요약 → Slack·Notion" },
  { title: "리서치 수집기", desc: "키워드 뉴스 요약 브리핑" },
  { title: "고객 타겟 분류", desc: "세그먼트 라벨링 자동화" },
];

interface MyWorldProps {
  onNavigate?: (tab: NavTab) => void;
}

export function MyWorld({ onNavigate }: MyWorldProps) {
  const [activeWorld, setActiveWorld] = useState("My World");

  return (
    <div className="mw">
      <TopNav active="MY WORLD" onNavigate={onNavigate} />

      <div className="mw__body">
        <aside className="mw__side">
          <p className="mw__sideLabel">WORLDS</p>
          {WORLDS.map((w) => (
            <button
              key={w.name}
              type="button"
              className={w.name === activeWorld ? "mw__world mw__world--on" : "mw__world"}
              onClick={() => setActiveWorld(w.name)}
            >
              <span aria-hidden="true">{w.icon}</span>
              {w.name}
            </button>
          ))}
          <button className="mw__newWorld" type="button">
            + New World
          </button>
        </aside>

        <main className="mw__main">
          <h1 className="mw__title">My World</h1>
          <p className="mw__sub">내가 만든 스킬과 자동화를 한 곳에서 관리해요.</p>

          <div className="mw__section">
            <p className="mw__sectionLabel">
              <span className="mw__dot" style={{ background: "var(--sc-node-agent)" }} />
              SKILL <span className="mw__count">{MW_SKILLS.length}개</span>
            </p>
            <div className="mw__grid">
              {MW_SKILLS.map((s) => (
                <article className="mw__skill" key={s.title}>
                  <span className="mw__pill">
                    <span className="mw__pillDot" style={{ background: s.color }} />
                    스킬
                  </span>
                  <h3 className="mw__cardTitle">{s.title}</h3>
                  <p className="mw__cardMeta">{s.meta}</p>
                </article>
              ))}
            </div>
          </div>

          <div className="mw__section">
            <p className="mw__sectionLabel">
              <span className="mw__dot" style={{ background: "var(--sc-accent)" }} />
              AUTO-FLOW <span className="mw__count">{MW_FLOWS.length}개</span>
            </p>
            <div className="mw__grid mw__grid--flow">
              {MW_FLOWS.map((f) => (
                <article className="mw__flow" key={f.title}>
                  <h3 className="mw__cardTitle">{f.title}</h3>
                  <p className="mw__cardDesc">{f.desc}</p>
                  <NodeTrail className="mw__flowTrail" />
                </article>
              ))}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
