export type Circle = {
  id: number;
  name: string;
  category: string;
  official: boolean;
  activityDays: string;
  place: string;
  description: string;
  tags: string[];
  sns: string;
  recruiting: boolean;
};

export type CampusEvent = {
  id: number;
  title: string;
  circleName: string;
  startsAt: string;
  place: string;
  type: string;
  description: string;
  tags: string[];
};

export const circles: Circle[] = [
  {
    id: 1,
    name: "プログラミング研究会",
    category: "技術",
    official: true,
    activityDays: "水曜・金曜",
    place: "情報棟ラウンジ",
    description: "Webアプリ、ゲーム、AIなどをゆるく作るサークルです。",
    tags: ["初心者歓迎", "Web", "アプリ開発"],
    sns: "https://example.com/programming",
    recruiting: true,
  },
  {
    id: 2,
    name: "軽音サークル",
    category: "音楽",
    official: true,
    activityDays: "火曜・土曜",
    place: "学生会館スタジオ",
    description: "バンド演奏やライブ企画を行っています。",
    tags: ["バンド", "ライブ", "途中入部OK"],
    sns: "https://example.com/music",
    recruiting: true,
  },
  {
    id: 3,
    name: "フットサル同好会",
    category: "スポーツ",
    official: false,
    activityDays: "日曜",
    place: "第2体育館",
    description: "経験者も初心者も参加できるフットサル団体です。",
    tags: ["運動", "初心者歓迎", "非公認"],
    sns: "https://example.com/futsal",
    recruiting: false,
  },
];

export const events: CampusEvent[] = [
  {
    id: 1,
    title: "新入生向けアプリ開発体験会",
    circleName: "プログラミング研究会",
    startsAt: "2026-07-20 18:00",
    place: "情報棟ラウンジ",
    type: "体験会",
    description: "Next.jsを使って簡単なWebページを作る体験会です。",
    tags: ["初心者歓迎", "途中参加OK"],
  },
  {
    id: 2,
    title: "夏ライブ",
    circleName: "軽音サークル",
    startsAt: "2026-07-27 16:30",
    place: "学生会館ホール",
    type: "ライブ",
    description: "複数バンドによる合同ライブです。",
    tags: ["見学自由", "音楽"],
  },
  {
    id: 3,
    title: "日曜フットサル体験",
    circleName: "フットサル同好会",
    startsAt: "2026-08-02 10:00",
    place: "第2体育館",
    type: "体験会",
    description: "運動しやすい服装で参加できます。",
    tags: ["スポーツ", "持ち物あり"],
  },
];
