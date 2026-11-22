# Interview Control

Refine the product until the schema-changing decisions are known, then design. Keep the conversation short enough that the user will finish it.

Do this at the start of the workflow. Interview in the user's language. Never open by asking the user to pick `shallow`, `medium`, or `deep`.

## 1. Classify the input first

Do this silently. Do not ask the user which kind of input they gave.

| Input | What it looks like | What to do |
| --- | --- | --- |
| Brief | A short description. Modules, roles, and flows are not spelled out. Example: "帮我设计一个技能交换 app 的后台数据库". | Ask a few product decisions as numbered choices. Default cap: **4** rounds. |
| Spec | A requirements specification, PRD, or module list that already describes roles, features, and flows. | Read it first. Ask only to confirm gaps that still change the schema. Default cap: **2** rounds. Ask **0** questions when the spec already decides those points. |

A user-set cap always wins, including `0` (no questions; write assumptions and deliver). If the user names `shallow`, `medium`, or `deep`, follow that depth's extra scope in section 5 and do not ask them to confirm the depth. If they say "enough", "直接设计", "就按这些设计", or similar, stop immediately, even if rounds remain.

One round is one assistant message that asks a question. Confirming a garbled answer does not consume another round.

## 2. Which questions are allowed

Ask a question only when the answer would add or remove a table, a relationship, or a column that later queries must filter on.

Ask about the product, not about the database. Do not ask the user to choose primary-key types, index types, normal forms, isolation levels, or ORMs. Infer those and write them under Assumptions.

Each round:

- One decision. Two only when they are facets of that same decision.
- Numbered options written for this product, not a generic checklist.
- The last option is always "其他，我补充".
- The question text stays in product language. Do not explain tables, keys, or indexes in the question.

Skip a question when the conversation, the spec, or the codebase already answers it.

## 3. Brief: product decisions, then stop

From the one-line idea, pick the decisions that change the schema. Usually two to four. Ask the most consequential one first.

Spend rounds in this order:

1. Who it is for, and how the core activity happens.
2. One more product decision only if a different answer would still add or remove a table.
3. Database engine, and only if it is still unknown and a round remains: PostgreSQL, MySQL, or both. Mention SQLite or MongoDB only when the user already hinted at them.

When the cap is hit, stop. Do not ask about volume, growth, retention, audit, compliance, or a query list. Assume them and record the assumptions.

### Example: skill-exchange app

User: "请使用这个技能，帮我设计一个技能交换 app 的后台数据库."

This is a brief. Do not ask which interview depth they want. First round, one decision:

> 这个技能交换，主要给谁用？
>
> 1. 互联网上任何人，不限制地域
> 2. 生活在同一个小范围内的人，比如一个小区或一所大学
> 3. 其他，我补充

If they choose 2, the next round asks how the exchange happens. Do not send both decisions in the first message.

> 技能交换怎么进行？
>
> 1. 线下：双方约定时间和地点，见面互相教，比如一方教吉他，另一方教滑轮
> 2. 线上：通过视频
> 3. 两种都要
> 4. 其他，我补充

A third round is allowed only for a decision that still changes the tables, for example whether a skill is free text or chosen from a catalog, or whether an exchange counts only after both sides confirm. Then stop. If the engine is still unknown and the cap has a round left, ask PostgreSQL / MySQL / both. Otherwise assume PostgreSQL, or MySQL when the user will next use this repo's `sql-to-*` scaffolds, and say so in Assumptions.

Do not continue into ratings, payments, chat, or notifications unless the user brings them up or a remaining round is needed because the answer changes a table. Those become assumptions ("第一版不做支付和站内聊天").

## 4. Spec: read first, confirm only the gaps

1. Read the specification before asking anything.
2. Split the facts into three lists:
   - Already decided (roles, modules, flows the spec states)
   - Still changes the schema (the spec is silent or contradicts itself, and the answer adds or removes a table or relationship)
   - Nice to have (volume, engine taste, naming). Do not ask these.
3. Ask only from the second list, one decision per round, with numbered options, within the cap of 2.
4. If the second list is empty, ask nothing. Start the design. Put the decisions taken from the spec under Assumptions.

Example: the spec already says the users are students of one university, exchanges happen in person, and both sides rate each other after they meet. Do not ask who the audience is or whether it is online. Ask only if something that changes a table is missing, such as "评价是双方都提交才算完成，还是一方提交即可？" If the spec already answers that too, ask nothing.

## 5. Optional depth override

Use this section only when the user names a depth or a cap. It is not the opening question.

| Depth | Default cap | Extra scope beyond sections 3 and 4 |
| --- | --- | --- |
| shallow | 3 | Product decisions only. Engine if still unknown. |
| medium | 6 | Plus the 3–5 main screens or queries, and whether the data is one community or many tenants. |
| deep | 10 | Plus volume, retention, audit, and compliance, still as numbered choices where that is possible. |

A named cap replaces the default. `0` means design now.

Engine details when you do ask or assume:

- Check `docker-compose.yml`, ORM config, a Supabase project, or a MySQL connection string before asking.
- Supabase is not PostgreSQL 18. Read the project's major version.
- If the user will next generate a backend with this repo's `sql-to-*` scaffolds, choose MySQL and write that down. Those skills expect MySQL `CREATE TABLE`.

## 6. When to stop and design

Stop when the cap is reached, the user says to design, or no schema-changing question remains. List the choices the user made and the assumptions for everything not asked. Then produce the schema script (or migrations, when a schema already exists) and `database-design.md`. Do not hold the deliverables for an unanswered nice-to-have question.
