from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import CampusEvent, Circle

CIRCLES = [
    {
        "name": "プログラミング研究会",
        "category": "技術",
        "official": True,
        "activity_days": "水曜・金曜",
        "place": "情報棟ラウンジ",
        "description": "Webアプリ、ゲーム、AIなどをゆるく作るサークルです。",
        "tags": ["初心者歓迎", "Web", "アプリ開発"],
        "sns": "https://example.com/programming",
        "recruiting": True,
    },
    {
        "name": "軽音サークル",
        "category": "音楽",
        "official": True,
        "activity_days": "火曜・土曜",
        "place": "学生会館スタジオ",
        "description": "バンド演奏やライブ企画を行っています。",
        "tags": ["バンド", "ライブ", "途中入部OK"],
        "sns": "https://example.com/music",
        "recruiting": True,
    },
    {
        "name": "フットサル同好会",
        "category": "スポーツ",
        "official": False,
        "activity_days": "日曜",
        "place": "第2体育館",
        "description": "経験者も初心者も参加できるフットサル団体です。",
        "tags": ["運動", "初心者歓迎", "非公認"],
        "sns": "https://example.com/futsal",
        "recruiting": False,
    },
]

EVENTS = [
    {
        "title": "新入生向けアプリ開発体験会",
        "circle_name": "プログラミング研究会",
        "starts_at": "2026-07-20 18:00",
        "place": "情報棟ラウンジ",
        "type": "体験会",
        "description": "Next.jsを使って簡単なWebページを作る体験会です。",
        "tags": ["初心者歓迎", "途中参加OK"],
    },
    {
        "title": "夏ライブ",
        "circle_name": "軽音サークル",
        "starts_at": "2026-07-27 16:30",
        "place": "学生会館ホール",
        "type": "ライブ",
        "description": "複数バンドによる合同ライブです。",
        "tags": ["見学自由", "音楽"],
    },
    {
        "title": "日曜フットサル体験",
        "circle_name": "フットサル同好会",
        "starts_at": "2026-08-02 10:00",
        "place": "第2体育館",
        "type": "体験会",
        "description": "運動しやすい服装で参加できます。",
        "tags": ["スポーツ", "持ち物あり"],
    },
]


def seed_database(session: Session) -> None:
    circle_count = session.scalar(select(func.count()).select_from(Circle))
    if circle_count == 0:
        session.add_all(Circle(**circle) for circle in CIRCLES)

    event_count = session.scalar(select(func.count()).select_from(CampusEvent))
    if event_count == 0:
        session.add_all(CampusEvent(**event) for event in EVENTS)

    session.commit()
