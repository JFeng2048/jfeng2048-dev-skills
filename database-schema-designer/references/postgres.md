# PostgreSQL Design Reference

Current major version: PostgreSQL 18. Features marked (18) need 18 or later; say so when the user's version is older.

## Contents
- Naming
- Comments
- Primary keys
- Data types
- Constraints
- Indexes
- Newer features worth using
- Multi-tenancy and row-level security
- Partitioning and scale
- Migration safety

## Naming

- `snake_case`, **singular table names** (`user`, `order_item`), singular column names.
- **Primary key: `<table>_id`.** Table `city` has `city_id`, table `order_item` has `order_item_id`. Never a bare `id`.
- **Foreign key: the referenced primary key name.** `city_id` references `city (city_id)`. When one table is referenced twice, prefix the role: `assignee_app_user_id`, `creator_app_user_id`.
- If the singular form is a reserved word (`user`, `order`, `group`), prefix it: `app_user`, `sales_order`.
- Name constraints and indexes so errors are readable: `app_user_email_key`, `task_project_id_fkey`, `idx_task_project_due_open`.

## Comments

- **Every table and every column carries a comment.** PostgreSQL has no inline column comment, so follow each `CREATE TABLE` with `COMMENT ON TABLE` and one `COMMENT ON COLUMN` per column.
- Write the comment in the user's language and state the business meaning, the unit, and the allowed values. Say `'月租金，单位元，来自城市测评'`, not `'租金'` and never `'numeric(10,2)'`.
- `COMMENT ON` replaces the previous value, so re-running the script is safe. Escape a single quote by doubling it (`''`); keep the text on one line.
- Optional but useful: `COMMENT ON CONSTRAINT` for an unusual rule, `COMMENT ON INDEX` for an index whose purpose is not obvious from its columns.
- Comments live in `pg_description` and show up in `psql \d+`; they also feed GUI tools and backend generators. Keep the wording consistent with the `Meaning` column in `database-design.md`.
- A comment does not enforce anything. Rules still need `NOT NULL`, `CHECK`, or `UNIQUE`.

```sql
CREATE TABLE city (
  city_id    bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name       text NOT NULL,
  avg_cost   numeric(10,2) NOT NULL DEFAULT 0,
  status     smallint NOT NULL DEFAULT 1 CHECK (status IN (0, 1)),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE city IS '城市库，评分与成本为 UGC 聚合结果';
COMMENT ON COLUMN city.city_id IS '城市主键';
COMMENT ON COLUMN city.name IS '城市名，与 province 联合唯一';
COMMENT ON COLUMN city.avg_cost IS '月均开销，单位元，由 UGC 测评聚合';
COMMENT ON COLUMN city.status IS '状态：0=停用；1=启用';
COMMENT ON COLUMN city.created_at IS '创建时间（UTC）';
COMMENT ON COLUMN city.updated_at IS '最后更新时间（UTC）';
```

## Primary keys

| Choice | Use when | Notes |
|---|---|---|
| `bigint GENERATED ALWAYS AS IDENTITY` | Internal IDs, single database | Smallest and fastest. Prefer identity over `serial`, which is legacy. |
| `uuid DEFAULT uuidv7()` (18) | IDs exposed in URLs, generated across services, merged datasets | Time-ordered, so inserts stay local in the B-tree index, unlike random UUIDv4. On 17 or earlier, generate UUIDv7 in the app or use `gen_random_uuid()`. |
| Natural key | Stable codes such as ISO country codes | Rarely; natural keys change more than people expect. |

UUIDv7 embeds the creation time; do not use it where exposing that time is a problem.

## Data types

| Data | Use | Avoid |
|---|---|---|
| Text | `text`, with a `CHECK (char_length(x) <= n)` if a limit matters | `varchar(255)` by habit; there is no performance gain |
| Timestamps | `timestamptz`, which stores an absolute UTC instant, for `created_at`, `updated_at`, and every other instant | `timestamp` without time zone (drops the offset and is read back as a wall clock) |
| Dates only | `date` | Strings |
| Money | `numeric(12,2)` or integer minor units (`amount_cents bigint`) | `real`, `double precision`, `money` |
| Booleans | `boolean NOT NULL DEFAULT false` | Nullable booleans (three states by accident) |
| Labels (`type`, `kind`, `role`) | `text` + `CHECK (type IN (...))`, or a lookup table | `ENUM` types for lists that will change |
| Status and flag columns (`status`, `is_deleted`, `audit_state`) | `smallint NOT NULL DEFAULT 1` holding an integer code (PostgreSQL has no `tinyint`), with the map in the column comment (`'状态：0=禁用；1=启用'`) and `CHECK (status IN (0, 1))` | String statuses, `ENUM`, and codes with no comment |
| Flexible attributes | `jsonb` (never `json`) | JSON for fields you filter or join on |
| Case-insensitive text | Unique index on `lower(email)`, or `citext` | Relying on the app to lowercase |
| IP addresses | `inet` | Text |
| Ranges | `tstzrange`, `daterange` | Two columns with no overlap protection |

## Constraints

- **Nullable is the default; `NOT NULL` needs a reason.** Keep `NOT NULL` only when the product cannot represent the row without the value (a name, an owner, a join key) or when a `DEFAULT` fills it for the insert (`status smallint NOT NULL DEFAULT 1`). Optional text, settings, secondary timestamps, and fields a later feature fills in stay nullable. Every extra `NOT NULL` without a default turns an insert into a full form and makes staged or partial writes fail.
- A nullable column inside a `UNIQUE` key is fine: PostgreSQL allows many `NULL` values there, and `NULL` never collides with another `NULL`.
- `UNIQUE` for natural keys; in multi-tenant tables, scope it: `UNIQUE (org_id, slug)`.
- `CHECK` for ranges and allowed values: `CHECK (quantity > 0)`.
- Status codes are a contract between the script, the API, and the UI. Write the map in the column comment, mirror it in `CHECK (status IN (0, 1))`, and keep it identical in `database-design.md`. Keep `0` for the default or unknown state, never renumber a code that has shipped, and retire a code by adding a new one and marking the old one deprecated in the comment.
- **No foreign key constraints by default.** Declare `<table>_id` reference columns without `REFERENCES`, and write the intended action in `database-design.md`: `CASCADE` for owned children (an order's line items), `SET NULL` for optional references (a task's assignee), `RESTRICT` for anything whose loss should block the delete. The service layer enforces it; say so in the document.
- When the user does ask for the constraints, add them in their own migration as `NOT VALID` and validate afterwards (see migration safety).
- Exclusion constraints for no-overlap rules (bookings): `EXCLUDE USING gist (room_id WITH =, during WITH &&)` (needs the `btree_gist` extension).

## Indexes

- Nothing indexes a reference column for you. With no FK constraints in the script, declare an index on every `<table>_id` reference column you join, filter, or delete by, or those joins and deletes scan.
- `PRIMARY KEY` and `UNIQUE` already create an index; do not add a duplicate.
- Composite index order: equality columns first, then range or sort columns. `(project_id, due_at)` serves `WHERE project_id = $1 ORDER BY due_at`.
- Partial indexes for hot subsets: `... WHERE status <> 2`, `... WHERE deleted_at IS NULL`. Also the way to make uniqueness ignore soft-deleted rows.
- Expression indexes must match the query expression: `ON app_user (lower(email))` serves `WHERE lower(email) = $1`.
- Covering indexes with `INCLUDE (col)` enable index-only scans for small, hot reads.
- `jsonb`: a GIN index (`USING gin (attrs jsonb_path_ops)`) for containment queries (`@>`).
- Full-text: a generated `tsvector` column with a GIN index; trigram (`pg_trgm`) GIN for `ILIKE '%term%'`.
- BRIN for huge append-only tables ordered by time (logs, events).
- Skip scan (18): a multicolumn B-tree index can now serve queries that omit the leading column, when that column has few distinct values. It helps, but an index whose leading column matches the filter is still faster.
- Check usage later with `pg_stat_user_indexes` (`idx_scan = 0` means unused) and drop what is not used.

## Newer features worth using

- `uuidv7()` (18) - time-ordered UUID primary keys, see above.
- Virtual generated columns (18) - `GENERATED ALWAYS AS (expr)` is now virtual by default (computed on read, no storage). Virtual columns cannot be indexed; add `STORED` when you need an index on the column or read it constantly.
- Temporal constraints (18) - `PRIMARY KEY (id, valid_period WITHOUT OVERLAPS)` and `UNIQUE (... WITHOUT OVERLAPS)` on range columns, and `FOREIGN KEY (..., PERIOD valid_period)`, for versioned or effective-dated records (prices, contracts, assignments). Needs the `btree_gist` extension when the key mixes scalar and range columns.
- `RETURNING OLD.*, NEW.*` (18) - read before and after values in one `UPDATE`, useful for audit logging without triggers.
- `NULLS NOT DISTINCT` (15) - `UNIQUE NULLS NOT DISTINCT (a, b)` treats nulls as equal, so only one row with `b IS NULL` is allowed.
- `MERGE` (15) - standard upsert-and-delete in one statement; `INSERT ... ON CONFLICT` remains the simple upsert.

## Multi-tenancy and row-level security

- Shared tables with a `tenant_id` / `org_id` column suit most SaaS apps. Put the tenant column first in composite indexes and inside unique constraints.
- Denormalize `org_id` onto child tables that policies must check, and keep it consistent in the service: read the parent's `org_id` on write. Without an FK constraint nothing in the database rejects a mismatched pair.
- Row-level security: `ALTER TABLE t ENABLE ROW LEVEL SECURITY;` plus policies per operation. On Supabase, every table in an exposed schema needs RLS enabled and policies, because clients query it directly with the anon or authenticated key. Index the columns policies filter on.
- Wrap per-row function calls in policies in a subselect so they are evaluated once per query instead of once per row. On Supabase that function is `(select auth.uid())`. On other PostgreSQL databases set a session value in the request and read `(select current_setting('app.user_id', true)::uuid)`. Do not emit `auth.uid()` outside Supabase.

## Partitioning and scale

- Partition only when a table is large (roughly 100M+ rows or hundreds of GB) and queries or retention align with the partition key, usually time. Declarative range partitioning by month is the common case; dropping an old partition is far cheaper than `DELETE`.
- Primary keys and unique constraints on partitioned tables must include the partition key.
- Before partitioning, check that the right indexes and `VACUUM`/autovacuum settings are in place; most "big table" problems are index problems.

## Migration safety

On tables with real traffic:

- `CREATE INDEX CONCURRENTLY` (and `DROP INDEX CONCURRENTLY`) to avoid blocking writes. It cannot run inside a transaction block, so put it in its own migration and disable the tool's wrapping transaction.
- Adding a column with a constant default is instant. Adding `NOT NULL` to an existing column scans the table under a lock. Instead: on 18, `ADD CONSTRAINT x NOT NULL col NOT VALID`, backfill, then `VALIDATE CONSTRAINT x`; on older versions, add `CHECK (col IS NOT NULL) NOT VALID`, backfill, validate, then `SET NOT NULL` (the validated check lets Postgres skip the scan).
- When the user asks for foreign keys, add them as `NOT VALID` and run `VALIDATE CONSTRAINT` in a separate step so validation does not block writes.
- Set `lock_timeout` (for example `SET lock_timeout = '5s'`) so a migration waiting on a lock fails instead of queueing all traffic behind it.
- Rename and type changes break running app versions. Use expand and contract: add the new column, dual-write, backfill, switch reads, then drop the old column in a later release.

## Final checklist

- Keys: every table has a primary key; the type is deliberate.
- Names: singular table names, `<table>_id` primary keys, foreign key columns named after the referenced primary key.
- Types: `timestamptz`, `text`, `numeric` or integer cents, `jsonb` only for variable attributes.
- Status and flag columns are `smallint` codes with the map in the comment and a `CHECK` on the domain; every `created_at` / `updated_at` is `timestamptz`.
- Constraints: `UNIQUE`, `CHECK`, and `NOT NULL` only where the business requires the value or a `DEFAULT` covers the insert; no `REFERENCES` unless the user asked for foreign keys, and then with an explicit `ON DELETE`.
- Indexes: one per key query, every reference column indexed, no duplicates of PK or unique indexes.
- `updated_at` maintained by a trigger or the ORM.
- Tenancy and RLS in place where clients can reach the database.
- Migrations reversible and safe for the table sizes involved.
