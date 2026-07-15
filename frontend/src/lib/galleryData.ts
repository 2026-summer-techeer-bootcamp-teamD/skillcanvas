export type ItemKind = "workflow" | "skill";

export interface GalleryItem {
  id: string;
  kind: ItemKind;
  title: string;
  description: string;
  tags: string[];
  owner: string;
  imports: number;
}

export const FEATURED: GalleryItem & { rating: number; installs: string } = {
  id: "f1",
  kind: "workflow",
  title: "메일 비서 Pro",
  description:
    "받은 편지함을 요약해 Slack·Notion으로 라우팅하는 인기 스킬. 설치 즉시 STACK에서 바로 실행돼요.",
  tags: ["메일", "자동화", "slack"],
  owner: "teamd",
  imports: 1240,
  rating: 4.9,
  installs: "1.2k",
};

export const GALLERY_ITEMS: GalleryItem[] = [
  {
    id: "g1",
    kind: "workflow",
    title: "CS 컴플레인 봇",
    description: "매일 컴플레인 대응 · 사과+쿠폰 자동 발송",
    tags: ["cs", "자동화"],
    owner: "teamd",
    imports: 34,
  },
  {
    id: "g2",
    kind: "workflow",
    title: "meeting-notes",
    description: "회의록을 요약해 Notion에 저장",
    tags: ["회의", "notion"],
    owner: "teamd",
    imports: 34,
  },
  {
    id: "g3",
    kind: "workflow",
    title: "뉴스 브리핑",
    description: "매일 아침 관심 키워드를 요약해 전달",
    tags: ["뉴스", "요약"],
    owner: "teamd",
    imports: 34,
  },
  {
    id: "g4",
    kind: "skill",
    title: "invoice-parser",
    description: "인보이스 파싱해 스프레드시트에 정리",
    tags: ["인보이스", "sheets"],
    owner: "teamd",
    imports: 34,
  },
  {
    id: "g5",
    kind: "workflow",
    title: "슬랙 스탠드업",
    description: "아침 스탠드업을 취합해 채널에 게시",
    tags: ["slack", "스탠드업"],
    owner: "teamd",
    imports: 34,
  },
  {
    id: "g6",
    kind: "skill",
    title: "blog-writer",
    description: "키워드만 주면 블로그 초안을 작성",
    tags: ["글쓰기", "llm"],
    owner: "teamd",
    imports: 34,
  },
];
