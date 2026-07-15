import { tokens } from "../tokens";

interface HeadlineProps {
  parts: string[];
}

export default function Headline({ parts }: HeadlineProps) {
  return (
    <span style={{ fontWeight: 700, fontSize: 23, lineHeight: 1.5, whiteSpace: "pre-line" }}>
      {parts.map((t, i) => (
        <span key={i} style={{ color: i % 2 === 1 ? tokens.accent : tokens.ink }}>
          {t}
        </span>
      ))}
    </span>
  );
}
