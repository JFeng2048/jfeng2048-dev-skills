# 已有项目的增量更新规范（新增表 / 表结构变更 / 表下线）

本规范与 `resources/config/incremental_change_policy.json` 配套：后者是机器可读的策略表，本文是执行流程。
**凡是目标项目已存在骨架（有 `app/factory.py` / `core/database.py` / `pyproject.toml`），必须先走本文流程，禁止按首次生成的口径全量重写。**

---

## 1. 三种场景与判定

| 场景 | 判定条件 | 运行模式 |
|------|----------|----------|
| 首次生成 | 项目骨架不存在 | `greenfield` → 按 `SKILL.md` 步骤 2.0 / `project_baseline.json` 走完整骨架 |
| 已有项目 + 新表 | 骨架存在，且该表 7 类文件全部不存在 | `add_table` |
| 已有项目 + 表结构修改 | 骨架存在，且该表任一文件已存在 | `alter_table` |
| 已有项目 + 表下线 | 用户明确要求移除/下线 | `drop_table`（只出清单，不自动删） |
| 残留文件不成套 | 例如只剩 `models/` 与 `schemas/` | **先询问用户**：补齐 or 重生成，禁止默认覆盖 |

一次给多张表时**逐表独立判定**，同一批次允许 `add_table` 与 `alter_table` 混用。

> 判 `alter_table` 时，"用户又给了一次建表 SQL" 不等于"重新生成一张表"，必须做差异分析。

---

## 2. `alter_table`：差异识别（强制）

### 2.1 取得旧结构

按以下优先级取「旧表结构」，取不到就**不要猜**，改为询问用户：

1. 用户提供的旧版 `CREATE TABLE` / `database/*.sql` 建库脚本
2. 目标项目 `models/{table}.py` 里的 `Column(...)` 定义（`db_name`、类型、`nullable`、`unique`、`default`、`comment`、`primary_key`、`ForeignKey`）
3. `schemas/{table}.py` 字段声明（只作交叉校验，不作唯一依据）
4. 运行库 `information_schema`（**仅在用户明确同意连库时**）

### 2.2 归一化后逐字段对比

归一规则见 `incremental_change_policy.json → baseline_snapshot.normalization`：大小写、反引号、驼峰→snake_case、类型别名（`INT`/`INTEGER`、`BOOL`/`TINYINT(1)`）、忽略列顺序与格式差异。
`status_flag_set` 与 `soft_delete_field` **必须用最新 SQL 重新按 `status_flag_fields.json` 计算**，不沿用旧结论。

### 2.3 输出差异清单（先给用户看，再动手）

```text
表 student：
  [added]    email        VARCHAR(120) NULL COMMENT '邮箱'        risk=low
  [removed]  age          INT                                    risk=high
  [modified] status       TINYINT(1) → TINYINT  NOT NULL → NULL   risk=medium
  [flag]     新增状态位 status → 需同步 Schema/Service/Resource/测试
  [unchanged] 其余 8 列
```

`removed + added` 且语义疑似重命名的，先问用户是「重命名」还是「删旧列 + 加新列」——两者数据语义不同。

详细的「变更类型 → 影响文件 → 动作」查 `incremental_change_policy.json → change_types`。

---

## 3. 影响面矩阵（速查）

| 变更 | Model | Schema | Repository | Service | Resource | 注册 | 测试 | DDL |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 新增表 | 生成 | 生成 | 生成 | 仅不存在时生成 | 生成 | **追加** | 仅不存在时生成 | 建表 |
| 加列 | 覆盖 | 覆盖 | 覆盖 | 待办 | — | — | 待办 | `ADD COLUMN` |
| 删列 | 覆盖 | 覆盖 | 覆盖 | **待办（必须全局查引用）** | 查手写路由 | — | 待办 | `DROP COLUMN` |
| 改类型/约束/默认值 | 覆盖 | 覆盖 | — | 待办 | — | — | 待办 | `MODIFY COLUMN` |
| 新增状态位 | 覆盖 | 覆盖 + `StatusUpdate` | 覆盖 | **须经确认追加 `update_status`** | 加 `PATCH /{pk}/status` | — | 待办 | `ADD COLUMN` |
| 删除状态位 | 覆盖 | 删 `StatusUpdate` | 覆盖 | 待办（移除死代码） | 删 PATCH 与 import | — | 待办 | `DROP COLUMN` |
| 软删字段变化 | 覆盖 | 覆盖 | 覆盖（delete/get 分支） | **待办（get_list 过滤）** | — | — | 待办（删除断言） | 同加/删列 |
| 主键变化 | 覆盖 | 覆盖 | 覆盖 | **待办（方法签名）** | 覆盖 | — | 待办 | 需人工确认 |
| 表重命名 / 删表 | — | — | — | — | — | — | — | **阻断自动执行，只出清单** |

**图例**：覆盖 = 仅重生成 `【AUTO-GENERATED】` 文件；待办 = 写入「人工待办清单」，不得擅自改手写文件。

### 3.1 三条最容易出事的同步规则

1. **状态位三件套必须同进同退**：`schemas.StatusUpdate` ↔ `service.update_status` ↔ `resource PATCH /{pk}/status`。
   只重生成 Schema + Resource 而不动 Service，Resource 会调用不存在的 `update_status` → 500；只删 Schema 不删 Resource import → 启动 ImportError。
2. **软删字段决定 `Repository.delete` 与 `Service.get_list` 两处逻辑**：Repository 可覆盖，`get_list` 在手写 Service 里，必须列入待办。
3. **主键变化贯穿所有路径参数类型**：Service 的方法签名是手写的，必须列入待办，否则 Resource 传参类型不匹配。

---

## 4. 文件归属与覆盖规则

| 文件 | 归属 | 头标记 | `alter_table` 动作 |
|------|------|--------|-------------------|
| `models/{table}.py` | 生成 | `【AUTO-GENERATED】` | 覆盖 |
| `schemas/{table}.py` | 生成 | `【AUTO-GENERATED】` | 覆盖 |
| `repository/{table}_repository.py` | 生成 | `【AUTO-GENERATED】` | 覆盖 |
| `service/{table}_service.py` | 手写 | `【HAND-WRITTEN】` | **绝不整文件覆盖**；必要时经确认在末尾追加最小方法 |
| `api/v1/{res}/{res}Resource.py` | 生成 + 手写路由 | `【AUTO-GENERATED】` | 重生成内置 CRUD；**保留自定义路由** |
| `tests/unit/test_{table}_service.py` | 手写 | `【HAND-WRITTEN 占位】` | 不覆盖，出待办 |
| `tests/integration/api/v1/test_{table}.py` | 手写 | `【覆盖策略】…` | 不覆盖，出待办 |
| `api/v1/__init__.py`、`service/dependencies.py` | 追加区 | `# ---- 脚手架追加区` | 幂等追加 |
| `models/__init__.py` | 视项目惯例 | — | 仅当项目已有按表导出惯例时追加 |
| `README.md` | 手写 | — | 只更新接口/字段章节 |
| `scripts/export_openapi.py` | 基线 | — | 缺失才补入，已有不覆盖 |
| `docs/openapi.json` `docs/api.md` | 导出 | — | 跑导出脚本覆盖，禁止手改 |
| `utils/**` `middleware/**` `docker/**` `deploy/**` | 基线 | `project_baseline.json` | **完全不碰** |

保护细则：文件存在但**没有生成标记** → 一律视为用户已手改 → 禁止覆盖 → 出待办并询问。

### 4.1 确需向 Service 追加代码时（如新增状态位）

必须按以下顺序，跳任何一步都算违规：

1. 展示准备追加的**完整代码片段**，说明追加位置（`Service` 类末尾「商业逻辑区」）；
2. 取得用户确认；
3. 只追加最小方法，不改任何已有代码；
4. 在变更报告中记录"已追加到手写文件"。

```python
    async def update_status(self, {{primary_key_param}}: {{primary_key_type}}, data: {{ClassName}}StatusUpdate) -> {{ClassName}}Response:
        """修改状态/标识位（技能按新增状态位追加）"""
        obj = await self.repo.update({{primary_key_param}}, data.model_dump(exclude_unset=True))
        return {{ClassName}}Response.model_validate(obj)
```

> 用户不确认时：保留现状，把该方法与 Resource 的 `PATCH` 一起标为「待人工补齐」，并明确提示此时接口会 500。

---

## 5. `add_table`：注册与幂等（强制）

新表除 7 类文件外，**必须补齐以下注册项**，缺任一都会导致启动或导入失败：

1. `api/v1/{resource_singular}/__init__.py`

   ```python
   from .{resource_singular}Resource import router

   __all__ = ["router"]
   ```

   > `api/v1/__init__.py` 用的是 `from api.v1.{resource_singular} import router`。没有这个 `__init__.py`，命名空间包里没有 `router` 属性 → `ImportError`。

2. `api/v1/__init__.py` 追加区：

   ```python
   from api.v1.{resource_singular} import router as {resource_singular}_router
   v1_router.include_router({resource_singular}_router)
   ```

3. `service/dependencies.py` 追加区：`get_{table}_service`（可选 `get_{table}_repository`）。
4. `models/__init__.py`：仅当项目已有按表导出惯例时追加 `import` 与 `__all__`。

**幂等检查**：追加前全文检索同一 `import` / `include_router` / `def get_{table}_service`，已存在则不追加。同一份 SQL 连续跑两次必须零 diff。
`alter_table` 默认不动注册项；仅当 `route_prefix` 或 Service 名变化时，先删旧行再追加新行，禁止新旧并存。

---

## 6. 数据库迁移边界

技能**不执行任何 DDL**、不连接生产库、不生成/改写 `database/` 初始化脚本、不自动接入 Alembic、不删数据也不删文件。

技能**必须**在变更报告里：

- 逐条列出 `ddl_hint`（MySQL 语法建议），标注「需人工确认/执行」；
- 提示发布顺序：**加列先 DDL 后发代码；删列先发代码（停止引用）后 DDL**；
- 提醒备份、灰度与回滚。

示例：

```sql
-- 需人工确认后执行
ALTER TABLE student ADD COLUMN email VARCHAR(120) NULL COMMENT '邮箱';
ALTER TABLE student MODIFY COLUMN status TINYINT NULL COMMENT '状态';
```

---

## 7. 执行顺序（`alter_table`）

1. 判定模式 → 取旧结构 → 输出差异清单（第 2 节）
2. 对 `critical` / `high` 项（删列、改主键、重命名、删表、状态位增删、软删变化）**先向用户确认**
3. 重生成 `models/` → `schemas/` → `repository/`（仅生成标记文件）
4. 重生成 Resource 的内置 CRUD，保留手写路由
5. 幂等检查注册项（默认不动）
6. 汇总「人工待办清单」（手写 Service / 测试 / README）
7. 输出 DDL 建议与发布顺序
8. 按第 8 节验证

---

## 8. 验证清单

```bash
# 1) 导入自检（最易暴露 StatusUpdate / 列名残留 / 注册漏项）
uv run python -c "import start"

# 2) 全量回归
uv run pytest tests/ -c tests/pytest.ini -v

# 3) 启动后看 Schema 与端点
uv run uvicorn start:app --reload    # /docs

# 4) 变化字段最小冒烟：POST 写入 → GET 详情 → PUT 更新 → DELETE

# 5) 同一 SQL 再跑一次，确认零 diff（幂等）
```

---

## 9. 变更报告模板（输出给用户）

```text
运行模式：student = alter_table，course = add_table

【差异清单】
  [added]   student.email  VARCHAR(120)          risk=low
  [flag]    student.status 新增状态位            risk=high（已确认）
  [new]     course 表                           risk=low

【已重生成】
  models/student.py、schemas/student.py、repository/student_repository.py
  api/v1/student/studentResource.py（+ PATCH /student/{student_id}/status，保留 2 个手写路由）
  models/course.py、schemas/course.py、repository/course_repository.py
  service/course_service.py、api/v1/course/courseResource.py
  tests/unit/test_course_service.py、tests/integration/api/v1/test_course.py

【已追加注册（幂等）】
  api/v1/course/__init__.py（新建）、api/v1/__init__.py、service/dependencies.py

【已追加到手写文件（经确认）】
  service/student_service.py → update_status()

【跳过 / 人工待办】
  service/student_service.py：get_list 若需按 email 过滤请自行补
  tests/integration/api/v1/test_student.py：补 email 与 PATCH status 用例（含 PUT 带 status 应 422）
  README.md：补字段与接口示例
  以下文件为手写，技能未覆盖：tests/unit/test_student_service.py

【DDL 建议（需人工确认执行）】
  ALTER TABLE student ADD COLUMN email VARCHAR(120) NULL COMMENT '邮箱';
  -- 加列：先 DDL 后发代码

【验证】
  uv run python -c "import start"        待执行
  uv run pytest tests/ -c tests/pytest.ini -v   待执行
  uv run python scripts/export_openapi.py       待执行
```

---

## 10. 与既有策略的关系

- `project_baseline.json` 管**基线包**（utils / middleware / docker / deploy），增量场景一律 `never_touch`。`scripts/export_openapi.py` 同样只补缺失、不覆盖。
- 接口文档以 `resources/specifications/api_docs.md` 为准：`docs/openapi.json` 给 Apifox / Apipost 导入，`docs/api.md` 给人读。字段或路由变了就重新导出，不手改。
- `incremental_change_policy.json` 管**按表文件**的运行模式、差异影响面、覆盖与保护、注册幂等。
- `SKILL.md` 步骤 2.1 的静态覆盖策略仍然有效；当与本文冲突时，**以本文和 `change_types` 为准**（例如新增状态位要求对手写 Service 追加方法）。
- `status_flag_fields.json`、`naming_rules.json`、`type_mappings.json` 在增量场景照常适用。
