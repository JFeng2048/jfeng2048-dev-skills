# Other Engines

For PostgreSQL, use [postgres.md](postgres.md). For MySQL 8.x / 9.x (InnoDB), use [mysql.md](mysql.md). Those two engines are first-class in this skill.

This file covers only SQLite and MongoDB. SQLite still follows the relational workflow, with the type and pragma rules below. MongoDB does not: skip relational keys, foreign keys, and `ON DELETE`, and shape the schema from access patterns.

## SQLite

- Declare tables `STRICT` so column types are enforced.
- No foreign key constraints by default, same as the other engines: declare the reference columns, index them, and enforce the delete behavior in the service. `PRAGMA foreign_keys = ON;` matters only if the user later asks for real FK constraints.
- `INTEGER PRIMARY KEY` is an alias for the rowid and the fastest key.
- Same naming rules as the other engines: singular table names, a `<table>_id` primary key, and foreign key columns named after the referenced primary key.
- `NOT NULL` follows the same rule as the other engines: only fields the row cannot exist without, or fields with a `DEFAULT`; everything optional stays nullable.
- `status` / `is_deleted` are `INTEGER` codes (SQLite has no `TINYINT`), with the map in the `--` comment and `CHECK (status IN (0, 1))`.
- Store timestamps as ISO 8601 `TEXT` in UTC or as Unix epoch `INTEGER`; pick one and be consistent.
- Partial and expression indexes are supported.
- `ALTER TABLE` is limited (no dropping constraints); many changes need the create-copy-rename pattern.
- Use WAL mode (`PRAGMA journal_mode = WAL;`) for concurrent readers.
- SQLite has no `COMMENT` syntax. Satisfy the comment requirement with a `--` comment on the line above every column and a `-- <table>: ...` line above every `CREATE TABLE`; do not skip column comments here.

## MongoDB

- Design from access patterns: list the queries, then shape documents so each common query reads one document or one index range.
- Embed when data is read together, owned by the parent, and bounded (order line items). Reference when data is shared, updated independently, or grows without limit (comments on a popular post).
- Documents are capped at 16 MB; unbounded arrays are the usual way to hit it.
- Enforce shape with `$jsonSchema` validators on the collection (see [schema-templates.md](schema-templates.md)). Give the collection and every property a `description` in the user's language; that is the MongoDB equivalent of table and column comments.
- `required` lists only the fields a document cannot exist without. Give the rest a default in the write path instead of making them mandatory, for the same reason a strict `NOT NULL` on every column makes inserts hard.
- Status and flag fields are integers with the code map in the `description` (`状态：0=禁用；1=启用`), and every instant is a UTC `date`; do not store status as a string.
- Compound index order follows the ESR rule: equality fields, then sort fields, then range fields.
- Multi-document transactions exist but cost more; a schema that needs them for common writes is often better modeled with embedding.
- Denormalized copies (a user's name on each post) need an update path; document which copies are allowed to go stale.
