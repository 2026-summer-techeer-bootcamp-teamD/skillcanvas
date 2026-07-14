import { useCallback, useEffect, useState } from "react";
import { TopNav, type NavTab } from "../components/TopNav";
import { NodeTrail } from "../components/NodeTrail";
import { useApi, ApiError } from "../lib/api";
import "./MyWorld.css";

const WORLDS = [
  { name: "My World", icon: "🌐" },
  { name: "Team-Growth", icon: "📈" },
  { name: "Team-Ops", icon: "🛠" },
];

const MW_FLOWS = [
  { title: "메일 비서", desc: "받은 편지함 요약 → Slack·Notion" },
  { title: "리서치 수집기", desc: "키워드 뉴스 요약 브리핑" },
  { title: "고객 타겟 분류", desc: "세그먼트 라벨링 자동화" },
];

interface MySkill {
  id: number;
  name: string;
  description: string | null;
  is_public: boolean;
}

interface MyWorldProps {
  onNavigate?: (tab: NavTab) => void;
}

export function MyWorld({ onNavigate }: MyWorldProps) {
  const [activeWorld, setActiveWorld] = useState("My World");
  const call = useApi();
  const [mySkills, setMySkills] = useState<MySkill[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // GET /skills?mine=true — 내 스킬 (비공개 포함) (5-1)
  const loadMySkills = useCallback(() => {
    setLoading(true);
    setError(null);
    call<{ items: MySkill[] }>("/skills?mine=true")
      .then((data) => setMySkills(data.items))
      .catch((e) => setError(e instanceof ApiError ? e.message : "불러오기 실패"))
      .finally(() => setLoading(false));
  }, [call]);

  useEffect(() => {
    loadMySkills();
  }, [loadMySkills]);

  // PATCH /skills/{id} — 이름 수정 (5-4)
  const handleRename = async (skill: MySkill) => {
    const name = window.prompt("새 이름", skill.name);
    if (!name || name === skill.name) return;
    try {
      await call(`/skills/${skill.id}`, { method: "PATCH", json: { name } });
      loadMySkills();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "수정 실패");
    }
  };

  // DELETE /skills/{id} — 삭제 (5-5)
  const handleDelete = async (skill: MySkill) => {
    if (!window.confirm(`"${skill.name}" 스킬을 삭제할까요?`)) return;
    try {
      await call(`/skills/${skill.id}`, { method: "DELETE" });
      loadMySkills();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "삭제 실패");
    }
  };

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
              SKILL <span className="mw__count">{mySkills.length}개</span>
            </p>

            {loading && <p className="mw__sub">불러오는 중…</p>}
            {error && <p className="mw__sub">에러: {error}</p>}
            {!loading && !error && mySkills.length === 0 && (
              <p className="mw__sub">아직 만든 스킬이 없어요.</p>
            )}

            <div className="mw__grid">
              {mySkills.map((s) => (
                <article className="mw__skill" key={s.id}>
                  <span className="mw__pill">
                    <span className="mw__pillDot" style={{ background: "var(--sc-node-agent)" }} />
                    {s.is_public ? "공개" : "나만보기"}
                  </span>
                  <h3 className="mw__cardTitle">{s.name}</h3>
                  <p className="mw__cardMeta">{s.description ?? "-"}</p>
                  <div className="mw__cardActions">
                    <button type="button" onClick={() => handleRename(s)}>
                      수정
                    </button>
                    <button type="button" onClick={() => handleDelete(s)}>
                      삭제
                    </button>
                  </div>
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
