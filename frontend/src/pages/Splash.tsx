import { PixelArt } from "../components/PixelArt";
import { BrandNav } from "../components/BrandNav";
import { NodeMotif } from "../components/NodeMotif";
import { ROBOT_BLACK, ROBOT_ORANGE } from "../lib/pixelMaps";
import "../styles/scene.css";
import "./Splash.css";

interface SplashProps {
  onStart?: () => void;
  onSkip?: () => void;
}

export function Splash({ onStart, onSkip }: SplashProps) {
  return (
    <section className="sc-scene">
      <NodeMotif />
      <BrandNav
        action={
          <button className="sc-skip" type="button" onClick={onSkip}>
            건너뛰기
          </button>
        }
      />

      <main className="splash__hero">
        <span className="splash__badge splash__enter splash__enter--1">
          <PixelArt sprite={ROBOT_BLACK} className="splash__badgeMascot" />
          AI 업무 비서 빌더
        </span>

        <h1 className="splash__wordmark splash__enter splash__enter--2">
          SkillCanvas
          <PixelArt sprite={ROBOT_ORANGE} label="SkillCanvas 마스코트" className="splash__rider" />
        </h1>

        <p className="splash__tagline splash__enter splash__enter--3">
          블록을 쌓듯 노드를 올리면 워크플로우가 완성돼요.
          <br />
          말만 하면 Claude가 블록을 쌓아드려요.
        </p>

        <button
          className="splash__cta splash__enter splash__enter--4"
          type="button"
          onClick={onStart}
        >
          시작하기
        </button>
      </main>

      <div className="splash__progress" aria-hidden="true">
        <span className="splash__progressBar" />
        <span className="splash__progressDot" />
        <span className="splash__progressDot" />
      </div>
    </section>
  );
}
