---
name: database-schema-designer
description: >-
  Use when the user wants to model data for a new app or feature, review or
  fix an existing schema, choose keys or indexes, plan multi-tenancy, normalize
  or denormalize, or asks how to store something. Also use when they want
  CREATE TABLE statements or a schema design document for PostgreSQL, MySQL,
  SQLite, or MongoDB. This repo does not move data between database providers.
---
# Database Schema Designer

Design a schema that enforces the data's rules in the database and makes the app's real queries fast. A vague request is refined with a few numbered product decisions; a detailed specification is read first and only its gaps are confirmed. The interview stays inside a short round cap. The required outputs are standalone, engine-correct schema script(s) and a Markdown design document that explains each table's purpose and relationships.

PostgreSQL and MySQL are first-class. Follow [references/postgres.md](references/postgres.md) or [references/mysql.md](references/mysql.md) for the chosen engine. If the user needs both, emit two scripts, each idiomatic to its engine, and document the differences. Do not write one lowest-common-denominator script. For SQLite or MongoDB, use [references/other-engines.md](references/other-engines.md).

## Interview first

Before modeling, classify the input and ask only the product decisions that would change the schema. Follow [references/interview.md](references/interview.md). The skill-exchange example there is the pattern to copy.

- A short request ("帮我设计一个技能交换 app 的后台数据库") is a **brief**. Do not ask the user to pick an interview depth. Ask one numbered product decision per round, in their language. Default cap: 4 rounds. Options describe this product, and the last option is "其他，我补充".
- A detailed requirements specification is a **spec**. Read it first. Ask only where it is silent or contradictory and the answer would add or remove a table or relationship. Default cap: 2 rounds. If nothing at that level is open, ask nothing and start designing.
- If they say to design now, treat the cap as `0`, write assumptions, and deliver. "shallow" / "medium" / "deep" apply only when the user names them.
- Questions stay in product language. Do not ask the user to choose key types, indexes, or normal forms.
- Engine is a first-class question: PostgreSQL, MySQL, or both. Infer it from the repo when possible. Default to PostgreSQL only when it is still unknown after the cap, and say so in Assumptions. If the next step is a backend scaffold in this repo (`sql-to-fastapi`, `sql-to-flask`, `sql-to-gin`, `sql-to-springboot`), choose MySQL instead and say so: those skills expect MySQL `CREATE TABLE`.
- Supabase is not PostgreSQL 18. Read the project's major version before using `uuidv7()`, virtual generated columns, or `WITHOUT OVERLAPS`. On 17 or earlier, use the fallbacks in [references/postgres.md](references/postgres.md) and name the version in Assumptions. `auth.uid()` belongs only in Supabase policies.

## Workflow

1. **Collect requirements** under the interview rules above. Pull from the conversation, attachments, and codebase first, and treat those as already decided. Ask product decisions before engine, volume, or ORM. Engine and version, when still unknown after the interview: PostgreSQL (default 18 only when the version is unknown and the target is not Supabase), MySQL (default 8.4 LTS, InnoDB), or both. Check `docker-compose.yml`, ORM config, the Supabase project's Postgres version, or a MySQL connection string before assuming.

2. **Choose the deliverable shape before modeling.**
   - No existing schema: a full executable script plus `database-design.md`.
   - An existing schema (SQL files, Prisma/Drizzle schema, Flyway/Liquibase/Alembic/Rails migrations, or a live definition the user agrees to read): read it first. Deliver a difference list and up/down migrations for the requested change. Emit a full `schema.sql` only when the user asks to rebuild, or when no schema exists. Do not replace an existing migration history with a greenfield script.
   - MongoDB: skip steps 4, 5, and 6. Follow [references/other-engines.md](references/other-engines.md) (access patterns, embed versus reference, `$jsonSchema`, ESR indexes). Do not emit relational foreign keys. Deliver `schema.js` plus the design document.

3. **Model entities and relationships.** List entities, attributes, and cardinality (1:1, 1:N, N:M). Normalize to 3NF by default; denormalize only for a named query that needs it, and say which. The conceptual model is shared across engines; types, indexes, and tenancy enforcement are not. Skip 3NF for MongoDB and shape documents from the access patterns instead.

4. **Choose keys and types** from the reference for each target engine. Do not apply Postgres habits to MySQL, or the reverse. Use `uuidv7()` only when the detected PostgreSQL version is 18 or newer.
   - Naming, unless the project already has a convention: `snake_case`, **singular table names** (`user`, `order_item`), and a primary key named after its table (`user.user_id`, `order_item.order_item_id`). Never a bare `id`. A foreign key reuses the referenced primary key name (`city_id`); when one table is referenced twice, prefix the role (`assignee_app_user_id`, `creator_app_user_id`). If the singular form is reserved (`user`, `order`, `group`), prefix it (`app_user`, `sales_order`). A reference column is a plain `<table>_id` column carrying the parent's exact type; the `REFERENCES` clause is not emitted (step 5).
   - Time columns (`created_at`, `updated_at`, and every other instant): the engine's `TIMESTAMP` in UTC, never `DATETIME`. MySQL `TIMESTAMP` (whole seconds, no fractional precision) with the session at `time_zone = '+00:00'`; PostgreSQL `timestamptz`. Only a value beyond 2038-01-19 UTC justifies MySQL `DATETIME`, and the design document states that exception.
   - Status and flag columns (`status`, `is_deleted`, `audit_state`): an integer code, not a string. MySQL `TINYINT UNSIGNED NOT NULL DEFAULT 1`, PostgreSQL `smallint NOT NULL DEFAULT 1` (PostgreSQL has no `tinyint`), with the code map in the column comment (`'状态：0=禁用；1=启用'`) and a `CHECK` on the allowed codes. Never renumber a code that has shipped; append a new one and mark the old one deprecated.
   - PostgreSQL: `bigint generated always as identity` or `uuid DEFAULT uuidv7()` primary keys, `text` over `varchar(n)`, `timestamptz`, `numeric` for money. See [references/postgres.md](references/postgres.md).
   - MySQL: `BIGINT UNSIGNED AUTO_INCREMENT` or `BINARY(16)` holding app-generated UUIDv7, `VARCHAR(n)` with a real limit for indexed strings, `TIMESTAMP` in UTC, `DECIMAL` for money, `ENGINE=InnoDB` and `utf8mb4`. See [references/mysql.md](references/mysql.md).

5. **Encode the rules as constraints, without foreign keys.** `UNIQUE` for natural keys and `CHECK` for ranges and allowed values. `NOT NULL` is the exception: keep it only where the row is meaningless without the value (a name, an owner, a join key) or where a `DEFAULT` lets the insert omit the column (`status TINYINT UNSIGNED NOT NULL DEFAULT 1`). Leave optional text, settings, and fields a later feature fills in nullable; making every column required turns each insert into a full form and breaks staged writes. Do **not** emit `REFERENCES` or `FOREIGN KEY` in `CREATE TABLE`: the default script declares reference columns only. Keep the column, give it the parent primary key's exact type (MySQL: same `UNSIGNED`), index it, and record the intended referential action (`CASCADE`, `SET NULL`, `RESTRICT`) in `database-design.md` as the service layer's job. Say so explicitly in the design document, and offer the FK constraints as a separate follow-up migration only when the user asks for them. `UNIQUE`, `CHECK`, and the justified `NOT NULL` stay in the script: those are the rules the database still enforces.

6. **Derive indexes from the known queries**, not from a checklist. For each query, name the index that serves it on each target engine. Do not add an index a `UNIQUE` or primary key already provides.
   - No FK constraint means no index either: declare an index on every `<table>_id` reference column you join, filter, sort, or cascade on, in both engines. Do not duplicate a primary key or unique key that already leads with that column.
   - InnoDB creates an index for a foreign key if one is missing; do not add a duplicate. MySQL has no partial indexes. A stored generated column that is `NULL` for excluded rows is only a substitute when the query filters and sorts on that column (`due_sort_key IS NOT NULL ORDER BY due_sort_key`). InnoDB still stores the `NULL` entries. Document the rewritten query. `utf8mb4_0900_ai_ci` uniqueness ignores accents as well as case; say so when the PostgreSQL side uses `lower(email)` only.
   - If the interview was shallow and few queries were given, index primary keys, unique keys, and foreign keys, and state that more query-specific indexes were deferred.

7. **Write the required deliverables**, using [references/schema-templates.md](references/schema-templates.md) and the layout in [references/output-format.md](references/output-format.md):
   - New schema, one engine: `schema.sql` (or `schema.js` for MongoDB)
   - New schema, both PostgreSQL and MySQL: `schema.postgres.sql` and `schema.mysql.sql`
   - Existing schema: up/down migration files per engine, plus the difference list inside `database-design.md`. A full script only for an explicit rebuild.
   - `database-design.md`: assumptions, ERD, relationship overview, a subsection for every table covering purpose, columns, keys, relationships, and indexes, and an **Engine differences** section when targeting both
   - **Comments are part of the deliverable.** Every table **and every column** carries an engine-native comment: MySQL `COMMENT '...'` on each column plus `COMMENT='...'` on the table; PostgreSQL `COMMENT ON TABLE` / `COMMENT ON COLUMN` after the DDL. Write them in the user's language, describe the business meaning of the field (what it stores, its unit, its allowed values), not a restatement of the type. Keep them consistent with the `Meaning` column in `database-design.md`.
   Write the document's prose in the user's language. If they also use a migration tool or ORM, add those files as supplements; they do not replace the required outputs.

8. **Verify.** If a database is available, run the script on that engine (local Postgres matching the detected version, or Docker `postgres:18` only when the design targets 18; local MySQL or Docker `mysql:8.4`; a Supabase branch of the same major version), insert a few rows, and `EXPLAIN` the key queries to confirm the planned indexes are used. When targeting both, verify each script on its own engine. Otherwise, walk each known query against the schema by hand, using the SQL the application will actually run. Then check the list below.

9. **Hand off a backend only when the script matches the scaffold.** In this repo, `sql-to-fastapi-restfulapi-scaffold`, `sql-to-flask-restfulapi-scaffold`, `sql-to-gin-restfulapi-scaffold`, and `sql-to-springboot-restfulapi-scaffold` consume MySQL `CREATE TABLE` and do not execute DDL. Pass them `schema.mysql.sql` when the user asks for an API next. Do not pass a PostgreSQL script to those skills. This skill does not move data between providers.

## Checks before delivering

- The required files exist. A new schema has an executable script for each target engine. An existing schema has up/down migrations and a difference list, and a full script only when the user asked to rebuild. Every table or collection in the script(s) has a subsection in the design document that states its purpose and relationships. Scripts targeting both engines are not copies of one dialect with types renamed only where convenient; each follows its reference.
- Every table and every column has a comment in the script, in the user's language: MySQL uses a column `COMMENT '...'` and table `COMMENT='...'`; PostgreSQL uses `COMMENT ON COLUMN` and `COMMENT ON TABLE`; SQLite has no comment syntax, so put a `--` comment on the line above each column. A comment says what the field means to the product, not what type it is. Tables or columns with no comment are a defect, not a style choice.
- Every known query is served by a stated index or is explained as a scan that is fine at the expected size. A MySQL generated-column substitute names the query that filters and sorts on that column. Accent-insensitive MySQL uniqueness is called out when the PostgreSQL side is only case-insensitive.
- PostgreSQL 18-only syntax (`uuidv7()`, virtual generated columns, `WITHOUT OVERLAPS`) appears only when the detected version is 18 or newer. Supabase policies use `auth.uid()`; other PostgreSQL policies use `current_setting`. MongoDB output has no relational foreign keys.
- No `REFERENCES` / `FOREIGN KEY` clause appears in `CREATE TABLE` unless the user asked for foreign keys. Every reference column carries the parent primary key's type (including `UNSIGNED` in MySQL), has its own index, and its intended `ON DELETE` behavior is written in `database-design.md` with a note that the service layer enforces it.
- Nullability is deliberate, not uniform: `NOT NULL` appears only on columns the row cannot exist without or on columns that carry a `DEFAULT`, and optional fields stay nullable. A script where nearly every column is `NOT NULL` and few have defaults is a defect, because every insert then has to supply a full form.
- Names: singular table names, a `<table>_id` primary key, and foreign key columns named after the referenced primary key. No bare `id`.
- Status and flag columns (`status`, `is_deleted`) are integer codes (MySQL `TINYINT UNSIGNED`, PostgreSQL `smallint`) with the map in the column comment and a `CHECK` on the domain; no free-text status strings.
- Types follow the target engine: no `timestamp` without time zone in PostgreSQL; no `DATETIME` for application timestamps in MySQL; no floating point for money; no `varchar(255)` by habit in PostgreSQL; no `TEXT` for short indexed strings in MySQL; no `utf8` (3-byte) charset in MySQL.
- `updated_at` actually updates: PostgreSQL needs a trigger or the ORM (`DEFAULT now()` only sets insert); MySQL should use `ON UPDATE CURRENT_TIMESTAMP` or a trigger.
- Uniqueness that should ignore case (emails, usernames) is enforced case-insensitively (Postgres expression index or `citext`; MySQL `_0900_ai_ci` or a functional index on `LOWER(email)`).
- Multi-tenant tables carry `tenant_id` (or `org_id`) and include it in unique constraints and leading index columns. PostgreSQL: row-level security if the database is reachable from clients (always on Supabase). MySQL: no RLS; the design document states whether the app or a view enforces tenancy.
- Migrations that touch large existing tables avoid long locks (PostgreSQL: [migration safety in postgres.md](references/postgres.md); MySQL: [migration safety in mysql.md](references/mysql.md)).
- Rollback scripts, when present, are real inverses, and destructive rollbacks (dropping a column with data) are called out.
- Assumptions that filled in for skipped interview questions are listed in the design document.

## Worked example

Request: "Multi-tenant project tracker: orgs, users who can belong to several orgs, projects per org, tasks per project. The main screen lists a project's open tasks by due date."

- Entities: `org`, `app_user`, `org_member` (N:M between app_user and org with a `role`), `project` (N:1 org), `task` (N:1 project, optional assignee).
- Key query: open tasks for one project ordered by due date. PostgreSQL: a partial index `ON task (project_id, due_at) WHERE status <> 2`, queried as `WHERE project_id = $1 AND status <> 2 ORDER BY due_at`. MySQL: a stored generated column `due_sort_key` that is `NULL` when the task is done (`status = 2`), indexed as `(project_id, due_sort_key)`, queried as `WHERE project_id = ? AND due_sort_key IS NOT NULL ORDER BY due_sort_key`. The `NULL` rows stay in the InnoDB index.
- Rules as constraints: `UNIQUE (org_id, app_user_id)` on `org_member`; `CHECK (role IN ('owner','admin','member'))`; `status smallint` limited by `CHECK (status IN (0, 1, 2))` with the map in the comment; unique project name per org with `UNIQUE (org_id, name)`.
- Deletes, enforced by the service and documented (the script has no FK constraints): removing an org deletes its projects and tasks; deleting a user sets `task.assignee_app_user_id` to null instead of deleting tasks.
- Tenancy: `task` carries `org_id`, and the service checks it against the project's org on write. PostgreSQL can add RLS; MySQL cannot, so the app or a view must enforce membership.

The full DDL for this example, in both engines, is in [references/schema-templates.md](references/schema-templates.md). In a real run, that DDL goes into the schema script(s), and `database-design.md` gets a subsection for each of `org`, `app_user`, `org_member`, `project`, and `task`.

## Failure modes

- Designing tables before knowing the queries, then indexing every column "just in case". Each index slows every write.
- Letting the interview run on after the cap, or blocking the deliverables because a nice-to-have question was skipped. Opening with "choose shallow, medium, or deep". Asking about primary keys, indexes, or normal forms before the product decisions. Sending several unrelated decisions in one message. Re-asking a point the specification already answered.
- Delivering only an ERD, only a chat explanation, or a design document that buries DDL inside it without a standalone script. Replacing an existing migration history with a greenfield `schema.sql`.
- Emitting `uuidv7()` or other PostgreSQL 18 syntax because the target is Supabase, without reading the project's major version. Using `auth.uid()` on a database that is not Supabase.
- Treating a MySQL generated column as a partial index while the application still filters on `status <> 2 ORDER BY due_at`.
- Marking almost every column `NOT NULL` with no `DEFAULT`, so each insert must supply a full form and staged or partial writes fail. Nullable is the default; require only what the row cannot exist without.
- Applying one engine's habits to the other: Postgres `varchar(255)` / `text` guidance used in MySQL; MySQL `AUTO_INCREMENT` or `DATETIME` used in Postgres; partial `CREATE INDEX ... WHERE` emitted for MySQL; `utf8` instead of `utf8mb4`; `BIGINT` joined to `BIGINT UNSIGNED`; `CHAR(36)` UUIDs in InnoDB when `BINARY(16)` was the design; a single "portable" script that is mediocre on both engines.
- Postgres `ENUM` types, or MySQL `ENUM` columns, for values that will change. A `CHECK` constraint or lookup table is easier to evolve.
- Soft deletes (`deleted_at`) added everywhere by default. They leak into every query and unique constraint. Use them where there is a real restore or audit need, and pair them with partial unique indexes (PostgreSQL) or a generated-column unique index (MySQL).
- Emitting `REFERENCES` / `FOREIGN KEY` after the user asked for reference columns without FK constraints, or leaving a reference column unindexed because an FK would have created that index for you.
- Polymorphic foreign keys (`commentable_type` + `commentable_id`) that the database cannot enforce. Prefer separate nullable reference columns with a `CHECK` that exactly one is set, or separate tables.
- Storing structured, queried fields inside `jsonb` or MySQL `JSON`. JSON is for sparse or truly variable attributes; anything you filter, join, or constrain on deserves a column.

## Attribution

Adapted from [OneWave AI's database-schema-designer](https://github.com/OneWave-AI/claude-skills/tree/main/database-schema-designer), MIT License, Copyright (c) 2025 OneWave AI. See `NOTICE` and `LICENSE`.
