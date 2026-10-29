"""Seed the initial public tags into the formal ``app_private.tags`` master.

This is not the prototype ``seed.py`` and it is not an Alembic migration:

* It runs only when an operator invokes it, as a dry run unless ``--apply`` is passed, so no
  environment receives data as a side effect of ``alembic upgrade head`` or application start.
* It only inserts missing rows. A tag that already exists with the same ID, name and slug is
  left exactly as it is (``display_order`` and ``is_active`` included), so a tag an operator
  deactivated is never reactivated. Any other overlap on ID, name or slug aborts the run
  before anything is written.

Usage, from ``backend/``::

    python -m app_private.seed_tags            # dry run: print the plan, write nothing
    python -m app_private.seed_tags --apply    # insert the missing initial tags
"""

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import insert, select, text
from sqlalchemy.orm import Session

from app_private.models import SCHEMA, Tag


@dataclass(frozen=True)
class InitialTag:
    id: UUID
    name: str
    slug: str
    display_order: int


# DEC-066 D3 vocabulary, in display order. The IDs are fixed literals (uuid5 over
# ``campus-circle-initial-tag-<slug>`` in the URL namespace, generated once) so every
# environment shares them and the mobile client never needs them hard-coded. The slugs are
# a technical choice of this implementation, not part of the approved vocabulary.
INITIAL_TAGS: tuple[InitialTag, ...] = (
    InitialTag(UUID("e5fdecdb-7477-51ed-9a5e-7dc869981b75"), "初心者歓迎", "beginner-friendly", 1),
    InitialTag(
        UUID("500d310f-dd4e-5ef1-8216-73c9e1177a92"),
        "留学生歓迎",
        "international-students-welcome",
        2,
    ),
    InitialTag(UUID("f630f70a-22d5-5c07-9a82-93ba399963fe"), "兼サーOK", "multiple-circles-ok", 3),
    InitialTag(
        UUID("dc78f642-b6fd-5f36-8fda-83e02727dcb3"),
        "途中入部歓迎",
        "mid-year-joining-welcome",
        4,
    ),
    InitialTag(UUID("56a73206-9865-5246-b417-5e0fef6fba6d"), "友達作り", "make-friends", 5),
    InitialTag(UUID("595b88ac-e3ac-5b68-929f-57c269cabeea"), "少人数", "small-group", 6),
    InitialTag(UUID("837b2009-87c6-5d9f-bf2b-b43285be6e0f"), "大会あり", "tournaments", 7),
)


class SeedConflictError(Exception):
    """An initial tag overlaps an existing row on ID, name or slug without being identical."""


@dataclass(frozen=True)
class SeedPlan:
    to_insert: tuple[InitialTag, ...]
    unchanged: tuple[InitialTag, ...]


def plan_initial_tags(session: Session) -> SeedPlan:
    """Compare the initial tags with the database. Read-only; raises on any conflict."""

    rows = session.execute(
        select(Tag.id, Tag.name, Tag.slug).where(
            Tag.id.in_([tag.id for tag in INITIAL_TAGS])
            | Tag.name.in_([tag.name for tag in INITIAL_TAGS])
            | Tag.slug.in_([tag.slug for tag in INITIAL_TAGS])
        )
    ).all()

    to_insert: list[InitialTag] = []
    unchanged: list[InitialTag] = []
    conflicts: list[str] = []
    for tag in INITIAL_TAGS:
        overlapping = [
            row for row in rows if row.id == tag.id or row.name == tag.name or row.slug == tag.slug
        ]
        if not overlapping:
            to_insert.append(tag)
        elif len(overlapping) == 1 and (
            (overlapping[0].id, overlapping[0].name, overlapping[0].slug)
            == (tag.id, tag.name, tag.slug)
        ):
            unchanged.append(tag)
        else:
            found = ", ".join(f"{row.id} / {row.name} / {row.slug}" for row in overlapping)
            conflicts.append(f"{tag.id} / {tag.name} / {tag.slug} conflicts with: {found}")
    if conflicts:
        raise SeedConflictError("; ".join(conflicts))
    return SeedPlan(to_insert=tuple(to_insert), unchanged=tuple(unchanged))


def seed_initial_tags(session: Session, *, apply: bool) -> SeedPlan:
    """Insert the missing initial tags when ``apply`` is true; commit on success only."""

    if apply:
        # Serialise concurrent seed runs. Readers of the catalog are not blocked.
        session.execute(text(f'LOCK TABLE "{SCHEMA}".tags IN SHARE ROW EXCLUSIVE MODE'))
    try:
        plan = plan_initial_tags(session)
        if apply and plan.to_insert:
            session.execute(
                insert(Tag),
                [
                    {
                        "id": tag.id,
                        "name": tag.name,
                        "slug": tag.slug,
                        "display_order": tag.display_order,
                        "is_active": True,
                    }
                    for tag in plan.to_insert
                ],
            )
        if apply:
            session.commit()
        else:
            session.rollback()
    except BaseException:
        session.rollback()
        raise
    return plan


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Seed the initial public tags (dry run by default)."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="insert the missing tags; without it nothing is written",
    )
    args = parser.parse_args(argv)

    from database import SessionLocal, engine

    with SessionLocal() as session:
        database_name = session.scalar(text("SELECT current_database()"))
        print(f"Target database: {engine.url.host}/{database_name}")
        try:
            plan = seed_initial_tags(session, apply=args.apply)
        except SeedConflictError as error:
            print(f"Aborted without writing: {error}")
            return 1

    verb = "Inserted" if args.apply else "Would insert"
    print(f"{verb} {len(plan.to_insert)} tag(s); {len(plan.unchanged)} already present, untouched.")
    if not args.apply and plan.to_insert:
        print("Dry run only. Re-run with --apply to write.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
