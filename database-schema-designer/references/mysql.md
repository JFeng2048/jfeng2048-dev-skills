# MySQL Design Reference

Current default: MySQL 8.4 LTS, InnoDB. Features that need a newer or older series are marked. MySQL 8.0 is still common; call out anything the user's version cannot do. MySQL 9.x LTS follows the same 8.4 conventions below unless noted. MariaDB is not a drop-in replacement (UUID functions, sequences, `RETURNING`, and some online DDL differ); if the user is on MariaDB, say so and adapt, do not copy this file blindly.

## Contents
- Naming
- Comments
- Character set and collation
- Primary keys
- Data types
- Constraints
- Indexes
- Multi-tenancy (no row-level security)
- Partitioning and scale
- Migration safety

## Naming

- `snake_case`, **singular table names** (`user`, `order_item`), singular column names. Keep names lowercase; on Linux, `lower_case_table_names=0` makes table names case-sensitive.
- **Primary key: `<table>_id`.** Table `city` has `city_id`, table `order_item` has `order_item_id`. Do not use a bare `id`: the key stays self-describing in joins, in `SELECT *` output, and in generated backend code.
- **Foreign key: the referenced primary key name.** `city_id` references `city (city_id)`. When one table is referenced twice, prefix the role: `assignee_app_user_id`, `creator_app_user_id`.
- Name constraints and indexes so errors are readable: `app_user_email_key`, `task_project_id_fkey`, `idx_task_project_due_open`.
- Avoid reserved words as names (`user`, `order`, `group`, `rank`, `rows`). Do not quote identifiers unless you must.
- Keep identifier length at or under 64 characters.

## Comments

- **Every table and every column carries a comment.** Table: `COMMENT='...'` at the end of the table options. Column: `COMMENT '...'` after the column definition, before the comma. A script with only table comments is incomplete.
- Write the comment in the user's language and state the business meaning, the unit, and the allowed values. Say `COMMENT '月租金，单位元，来自城市测评'`, not `COMMENT '租金'` and never `COMMENT 'DECIMAL(10,2)'`.
- Keep each comment on one line. The limit is 1024 characters; double a single quote (`''`) inside the text. Newlines make `SHOW CREATE TABLE` output hard to read and are easy to break in scripts.
- The comment is part of the column definition: changing it later needs `ALTER TABLE ... MODIFY COLUMN` with the full type, nullability, and defaults restated. On a large table that can copy the table, so write it correctly the first time (see migration safety).
- A comment is documentation, not a rule. Anything that must hold (`status` domain, ranges, non-negative money) still needs a `CHECK` or a lookup table.
- `SHOW FULL COLUMNS FROM t` and `information_schema.columns` expose these strings, so they also feed GUI tools and backend generators. Keep the wording consistent with the `Meaning` column in `database-design.md`.

```sql
CREATE TABLE city (
  city_id    BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '城市主键',
  name       VARCHAR(50) NOT NULL COMMENT '城市名，与 province 联合唯一',
  avg_cost   DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '月均开销，单位元，由 UGC 测评聚合',
  status     TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '状态：0=停用；1=启用',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间（UTC）',
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间（UTC）',
  PRIMARY KEY (city_id),
  UNIQUE KEY city_name_key (name),
  CONSTRAINT city_status_check CHECK (status IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
  COMMENT='城市库，评分与成本为 UGC 聚合结果';
```

## Character set and collation

- Every database and table: `DEFAULT CHARSET=utf8mb4` with `utf8mb4_0900_ai_ci` for case-insensitive uniqueness (emails, slugs, names), or `utf8mb4_0900_bin` when case must be distinct.
- Never use `utf8`. In MySQL it is a 3-byte alias and cannot store all of Unicode.
- `utf8mb4_0900_ai_ci` makes `UNIQUE (email)` case-insensitive and accent-insensitive, so `jose` and `josé` collide. That is stricter than PostgreSQL `lower(email)`, which only folds case. When both engines are delivered, write this difference under Engine differences. If accents must stay distinct, use `utf8mb4_0900_as_ci` or a functional unique index on `(LOWER(email))` under a binary collation.
- The old `VARCHAR(191)` unique-key habit was for the 767-byte index limit. MySQL 8 InnoDB defaults to a 3072-byte limit, so `VARCHAR(255)` under utf8mb4 is fine.

## Primary keys

| Choice | Use when | Notes |
|---|---|---|
| `BIGINT UNSIGNED AUTO_INCREMENT` | Internal IDs, single database | Smallest and fastest. InnoDB clusters rows by the primary key, so sequential values avoid page splits. Prefer `UNSIGNED`. Do not use `SERIAL` as a style copy from Postgres (`SERIAL` in MySQL is `BIGINT`, not the same as Postgres identity). |
| `BINARY(16)` holding UUIDv7 | IDs exposed in URLs, generated across services, merged datasets | MySQL has no `uuidv7()`. Generate UUIDv7 in the app (or a UDF), store with `UUID_TO_BIN(uuid, 0)`. Do not pass swap flag `1` for v7; that swap is for UUIDv1 and would break time-ordering. `UUID()` is UUIDv1; if you use it, store `UUID_TO_BIN(UUID(), 1)`. |
| Natural key | Stable codes such as ISO country codes | Rarely; natural keys change more than people expect. |

UUIDv7 embeds the creation time; do not use it where exposing that time is a problem. Random UUIDv4 as a primary key fragments the InnoDB clustered index; avoid it.

## Data types

| Data | Use | Avoid |
|---|---|---|
| Short or indexed text | `VARCHAR(n)` with a real limit (`email VARCHAR(255)`, `slug VARCHAR(100)`) | `VARCHAR(255)` on every column by habit; `TEXT` for values you index or give a default |
| Long body text | `TEXT` or `MEDIUMTEXT` | Storing large bodies in `VARCHAR` |
| Timestamps | `TIMESTAMP` with the session at `time_zone = '+00:00'`, so the value is stored and read back as UTC. It holds whole seconds, so tie-break an `ORDER BY created_at` with the primary key. Use it for `created_at`, `updated_at`, and every other instant | `DATETIME` for application timestamps; `TIMESTAMP(n)` unless sub-second ordering is a stated requirement. `TIMESTAMP` ends at 2038-01-19 03:14:07 UTC, so a far-future deadline is the one case for `DATETIME` |
| Dates only | `DATE` | Strings |
| Money | `DECIMAL(12,2)` or integer minor units (`amount_cents BIGINT`) | `FLOAT`, `DOUBLE` |
| Booleans | `TINYINT(1) NOT NULL DEFAULT 0`, or `BOOLEAN` (an alias for `TINYINT(1)`) | Nullable booleans (three states by accident) |
| Labels (`type`, `kind`, `role`) | `VARCHAR` + `CHECK (type IN (...))`, or a lookup table | `ENUM` for lists that will change; altering an enum can rebuild the table on older versions |
| Status and flag columns (`status`, `is_deleted`, `audit_state`) | `TINYINT UNSIGNED NOT NULL DEFAULT 1` holding an integer code, with the map in the comment (`COMMENT '状态：0=禁用；1=启用'`) and `CHECK (status IN (0, 1))` | String statuses (`VARCHAR` holding `'enabled'`), `ENUM`, and codes with no comment, so nobody knows what `2` means |
| Flexible attributes | `JSON` | JSON for fields you filter or join on; storing JSON as `TEXT` |
| Case-insensitive text | `_0900_ai_ci` collation, or a unique functional index on `LOWER(email)` | Relying on the app to lowercase |
| IP addresses | `VARBINARY(16)` or `VARCHAR(45)` | A string format you cannot compare consistently |

Declare tables `ENGINE=InnoDB`. Do not leave the engine implicit in scripts that may be replayed on a server whose default is not InnoDB.

## Constraints

- **Nullable is the default; `NOT NULL` needs a reason.** Keep `NOT NULL` only when the product cannot represent the row without the value (a name, an owner, a join key) or when a `DEFAULT` fills it for the insert (`status TINYINT UNSIGNED NOT NULL DEFAULT 1`). Optional text, settings, secondary timestamps, and fields a later feature fills in stay nullable. Every extra `NOT NULL` without a default turns an insert into a full form and makes staged or partial writes fail.
- A nullable column inside a `UNIQUE` key is fine: InnoDB allows many `NULL` values there, and `NULL` never collides with another `NULL`.
- `UNIQUE` for natural keys; in multi-tenant tables, scope it: `UNIQUE (org_id, slug)`.
- `CHECK` is enforced from 8.0.16. Name checks explicitly: `CONSTRAINT task_status_check CHECK (status IN (0, 1, 2))`.
- Status codes are a contract between the script, the API, and the UI. Write the map once in the column comment, mirror it in `CHECK (status IN (0, 1))`, and keep it identical in `database-design.md`. Keep `0` for the default or unknown state, never renumber a code that has shipped, and retire a code by adding a new one and marking the old one deprecated in the comment.
- **No foreign key constraints by default.** Declare `<table>_id` reference columns without `REFERENCES` / `FOREIGN KEY`, and write the intended action in `database-design.md`: `CASCADE` for owned children (an order's line items), `SET NULL` for optional references (a task's assignee), `RESTRICT` for anything whose loss should block the delete. The service layer enforces it; say so in the document.
- Reference columns still match the parent primary key exactly, including `UNSIGNED`. `BIGINT` joined to `BIGINT UNSIGNED` is a type bug even without a constraint.
- Without an FK, InnoDB creates no index. Declare a `KEY` on every reference column you join, filter, or cascade on, unless the primary key or a unique key already leads with it.
- Add the constraints later, only when the user asks, as their own migration: `ALTER TABLE task ADD CONSTRAINT task_project_id_fkey FOREIGN KEY (project_id) REFERENCES project (project_id) ON DELETE CASCADE;` Delete or repair orphan rows first, or the `ALTER` fails.
- There are no exclusion constraints. Overlap rules (bookings) need a generated column plus a unique index, a trigger, or enforcement in the app; say which.

## Indexes

- InnoDB creates an index only when an FK constraint asks for it. With no FK constraints in the script, every reference column needs its own `KEY`, and the design document names the index that serves each reference.
- `PRIMARY KEY` and `UNIQUE` already create an index; do not add a duplicate.
- Composite index order: equality columns first, then range or sort columns. `(project_id, due_at)` serves `WHERE project_id = ? ORDER BY due_at`.
- No partial indexes. Do not emit `CREATE INDEX ... WHERE`. For a hot subset (open tasks, not-deleted rows), use a stored generated column that is `NULL` for the excluded rows and index that column, or a composite index that includes the filter column when the filter is equality. InnoDB still stores the `NULL` index entries, so this is not a true partial index. The application query must filter and sort on the generated column (`WHERE project_id = ? AND due_sort_key IS NOT NULL ORDER BY due_sort_key`). A query that still says `status <> 2 ORDER BY due_at` does not use that index for the filter or the sort. Document the rewritten query in the design document.
- Functional indexes (8.0.13+): `CREATE UNIQUE INDEX app_user_email_lower_key ON app_user ((LOWER(email)));` The query must use the same expression.
- A stored generated column can be indexed; a virtual generated column can also be indexed (the index stores the value).
- Prefix indexes on `TEXT`/`BLOB` (`KEY (body(191))`) are a last resort; prefer a `VARCHAR` with a real limit when you need uniqueness or a full-value lookup.
- Secondary indexes already include the primary key (the clustered index), so a Postgres-style `INCLUDE` covering index is usually unnecessary.
- Full-text: InnoDB `FULLTEXT` indexes; use the `ngram` parser for CJK. Do not use `ILIKE '%term%'` as the plan.
- Invisible indexes (`ALTER TABLE ... ALTER INDEX i INVISIBLE`) are useful to test whether an index is still needed, then drop it.

## Multi-tenancy (no row-level security)

- Shared tables with a `tenant_id` / `org_id` column suit most SaaS apps. Put the tenant column first in composite indexes and inside unique constraints.
- Denormalize `org_id` onto child tables that the app must check, and keep it consistent in the service: read the parent's `org_id` on write, or compare it in the same statement. Without an FK constraint nothing in the database rejects a mismatched pair.
- MySQL has no row-level security. Enforce tenancy in the application, or with views that filter on the current session value (`CURRENT_USER()` or a session variable). State the enforcement point in the design document. Index the columns those checks filter on.

## Partitioning and scale

- Partition only when a table is large (roughly 100M+ rows or hundreds of GB) and queries or retention align with the partition key, usually time. `PARTITION BY RANGE` on a date or unix-timestamp column is the common case; dropping an old partition is far cheaper than `DELETE`.
- Primary keys and unique constraints on a partitioned table must include the partition key.
- InnoDB partitioned tables do not support foreign keys, one more reason the default script leaves them out. If the user later wants real FKs, keep them on the operational tables and partition only append-only tables that can live without them (logs, events).
- Before partitioning, check that the right indexes are in place; most "big table" problems are index problems.

## Migration safety

On tables with real traffic:

- Prefer online DDL: `ALGORITHM=INSTANT` when the change allows it (many `ADD COLUMN` with a constant default are instant), otherwise `ALGORITHM=INPLACE, LOCK=NONE`. If MySQL rejects those, stop and use gh-ost or pt-online-schema-change; do not silently run a table-copy `ALGORITHM=COPY` on a large table.
- Adding `NOT NULL` to an existing column, changing a column's type or character set, or adding a foreign key can copy the table. A late FK also validates every existing row under a lock, so clean orphans first and ship it as its own migration. Use expand and contract: add the new column, dual-write, backfill, switch reads, then drop the old column in a later release.
- Set `lock_wait_timeout` (for example `SET lock_wait_timeout = 5`) so a migration waiting on a lock fails instead of queueing traffic behind it.
- There is no `CREATE INDEX CONCURRENTLY`. An in-place index build is the MySQL equivalent; still build large indexes in their own migration so a failure is easy to retry.
- Rename and type changes break running app versions. Same expand-and-contract rule as above.

## Final checklist

- Keys: every table has a primary key; the type is deliberate; UUID keys are `BINARY(16)`, not `CHAR(36)`, unless the user requires a string form.
- Names: singular table names, `<table>_id` primary keys, foreign key columns named after the referenced primary key.
- Types: `TIMESTAMP` in UTC, `VARCHAR` with real limits, `DECIMAL` or integer cents, `JSON` only for variable attributes, `ENGINE=InnoDB`, `utf8mb4`.
- Status and flag columns are `TINYINT UNSIGNED` codes with the map in the comment and a `CHECK` on the domain; every `created_at` / `updated_at` is `TIMESTAMP`, not `DATETIME`.
- Constraints: `UNIQUE`, `CHECK`, and `NOT NULL` only where the business requires the value or a `DEFAULT` covers the insert; no `REFERENCES` / `FOREIGN KEY` unless the user asked for them. Reference columns match the parent type (including `UNSIGNED`), are indexed, and their `ON DELETE` intent is in `database-design.md`.
- Indexes: one per key query, every reference column indexed, no duplicates of PK or unique indexes, no `WHERE` clauses on indexes.
- `updated_at` maintained by `ON UPDATE CURRENT_TIMESTAMP` or a trigger, not only a default on insert.
- Tenancy enforced in the app or with views; `org_id` present in unique keys and leading index columns.
- Migrations reversible and safe for the table sizes involved (`INSTANT` / `INPLACE, LOCK=NONE`, or an online tool).
