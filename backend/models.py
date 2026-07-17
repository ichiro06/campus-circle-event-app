from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Circle(Base):
    __tablename__ = "circles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(50), index=True)
    official: Mapped[bool] = mapped_column(Boolean)
    activity_days: Mapped[str] = mapped_column(String(100))
    place: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(JSONB, default=list)
    sns: Mapped[str] = mapped_column(String(500))
    recruiting: Mapped[bool] = mapped_column(Boolean, index=True)


class CampusEvent(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150))
    circle_name: Mapped[str] = mapped_column(String(100), index=True)
    starts_at: Mapped[str] = mapped_column(String(50), index=True)
    place: Mapped[str] = mapped_column(String(150))
    type: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[str] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(JSONB, default=list)
