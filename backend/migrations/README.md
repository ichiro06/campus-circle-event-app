# Database migrations

Alembic is the selected migration tool for the formal PostgreSQL schema.

`20260915_0001` is the first formal product migration. It creates 27 tables in
the private `app_private` schema and deliberately leaves the current
`public.circles` and `public.events` technical-verification tables unchanged.
The approved source is `docs/data-dictionary.md`.

From `backend/`, inspect the migration history with:

```bash
alembic history
```

Apply the formal migration after PostgreSQL is ready:

```bash
alembic upgrade head
```

Product ORM mappings will be added with implementation slices. Until then,
Alembic autogenerate is intentionally disabled so the runtime prototype models
cannot produce a destructive migration candidate. Do not run `downgrade`
against a shared or production database without a reviewed rollback plan. CI
verifies upgrade, downgrade, and re-upgrade against an ephemeral database.
