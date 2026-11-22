# SQL-to-FastAPI-Scaffold Skill

## 概述

`sql-to-fastapi-restfulapi-scaffold` 从 SQL 脚本生成完整的 FastAPI 项目脚手架。

## 功能特性

- ✅ 解析 SQL CREATE TABLE 语句
- ✅ 生成 SQLAlchemy Model
- ✅ 生成 Pydantic Schema（Base / Create / Update / Response；有状态字段时含 StatusUpdate）
- ✅ 生成 Repository（**仅单条** `create` / `delete` / `update` / `get`，可覆盖）
- ✅ 生成 Service（**已存在则跳过**；单条委托 Repository；`get_list` 等业务写在本层）
- ✅ 生成 FastAPI Resource（**统一只依赖 Service**；校验靠 Schema）
- ✅ 生成单元测试占位（`tests/unit/test_{table}_service.py`，已存在则跳过）
- ✅ 生成集成测试（`tests/integration/api/v1/test_{table}.py`：CRUD 可跑 + 业务占位，已存在则跳过）
- ✅ 导出 `docs/openapi.json`（Apifox / Apipost 按 OpenAPI 导入）和给人读的 `docs/api.md`
- ✅ 支持软删除/硬删除自动判断
- ✅ 识别状态/标识位字段，自动生成专用改状态接口（`PATCH /{pk}/status`）
- ✅ 异步 SQLAlchemy（AsyncSession）
- ✅ 中文文档字符串和注释
- ✅ 目标项目默认用 **uv** 管理依赖与启动（`pyproject.toml` + `uv sync` / `uv run`）
- ✅ 目标项目自带 `.gitignore`；Python 版本取生成时本机最新稳定版，不硬编码 3.12
- ✅ `utils/response_code.py` 只含通用/HTTP 服务级响应码（中英文文案）；业务码按 SQL 需要再追加
- ✅ 骨架代码不绑定具体业务：`core/permissions.py` 只使用 JWT 的通用 `roles` / `permissions`
- ✅ **已有项目新增表**：按表增量补齐 7 类文件，并幂等追加路由/依赖注册
- ✅ **已有项目表结构修改**：字段级差异分析（加列/删列/改类型/改约束/改主键/状态位/软删变化），按影响面分层重生成
- ✅ **手写代码保护**：`Service` / 测试 / `README` 绝不整文件覆盖，改为人工待办清单
- ✅ 增量变更输出 DDL 建议、发布顺序与回归验证清单（技能本身不执行 DDL）

## 分层约定

```text
API(Resource) → Service(单条委托 + 列表等业务) → Repository(仅 create/delete/update/get，增删改查顺序) → Model
```

|层|路径|覆盖策略|职责|
|---|---|---|---|
|Repository|`repository/{table}_repository.py`|可覆盖|仅单条 CRUD|
|Service|`service/{table}_service.py`|仅首次生成|单条委托 + 列表/状态等业务|
|Resource|`api/v1/...`|可覆盖基础 CRUD|只调 Service|

## 技能项目结构

```text
sql-to-fastapi-restfulapi-scaffold/
├── docs/
│   ├── Trea中使用skill配置.md
│   ├── claude中使用skill配置.md
│   └── GitHub Copilot中使用sql-to-fastapi-restfulapi-scaffold技能.md
├── resources/
│   ├── config/
│   │   ├── naming_rules.json
│   │   ├── type_mappings.json
│   │   ├── status_flag_fields.json
│   │   ├── package_manager.json    # uv 包管理与启动约定
│   │   ├── project_baseline.json   # utils 等基线包清单与复用策略
│   │   └── incremental_change_policy.json  # 增量模式/差异影响面/覆盖保护/注册幂等
│   ├── specifications/
│   │   ├── coding_standards.md
│   │   ├── incremental_update.md  # 已有项目增量更新流程
│   │   └── api_docs.md            # openapi.json / api.md 导出约定
│   ├── tools/
│   │   └── check_skill_consistency.py
│   └── templates/
│       ├── layers/
│       │   ├── model/
│       │   ├── schema/
│       │   ├── repository/
│       │   ├── service/
│       │   ├── resource/
│       │   └── test/
│       │       ├── unit/
│       │       └── integration/
│       └── project_structure/
│           ├── pyproject.toml      # uv 主依赖清单
│           ├── .python-version     # 占位符，生成时取最新稳定版
│           ├── .gitignore          # 目标项目 Git 忽略规则
│           ├── requirements.txt    # pip 兼容
│           ├── start.py
│           ├── .env.example
│           ├── .env.docker
│           ├── app/
│           ├── api/
│           ├── config/
│           ├── core/
│           ├── models/
│           ├── schemas/
│           ├── repository/
│           ├── service/
│           ├── utils/              # 基线工具包（与 project_baseline 对齐）
│           ├── middleware/         # 基线中间件：安全头 / 限流 / 审计
│           ├── docker/             # 起步 Docker：app + MySQL（Redis 可选）
│           ├── deploy/             # 进阶运维配置（Nginx/监控/日志等）
│           └── scripts/
│               └── export_openapi.py
├── README.md
└── SKILL.md
```

## 基线包 utils / middleware / docker / deploy

目标项目若已有常用工具、中间件或部署目录，技能通过 `resources/config/project_baseline.json` 声明：

- 默认 `brownfield_prefer_existing`：检测到对应目录已存在 → **整包跳过**
- 空项目从 `project_structure/` 写入：`utils/`、`middleware/`、`docker/`、`deploy/`、`.env.docker`、`.gitignore`
- **docker**：`Dockerfile` + `docker-compose.yml`（app + MySQL；`--profile redis` 可选）
- **deploy**：进阶运维素材，**不**进入默认 compose 必跑栈
- 层代码 import 必须以 `canonical_imports` 为准
- 禁止为单表新建 `utils/{table}_*.py` 或 `middleware/{table}_*.py`

## 使用方法

### 1 配置技能到目标开发IDE中

- 如果你使用的是 Trae IDE，你可以直接在 IDE 中配置技能环境。
- 操作文档请参考
[Trea IDE 配置技能](docs/Trea中使用skill配置.md)

- 如果你使用的是 Claude Code，你可以通过扩展来配置技能环境。
- 操作文档请参考
[claude code 配置技能](docs/claude中使用skill配置.md)

### 2 准备SQL语句

向技能提供 SQL CREATE TABLE 语句，例如：

```sql
CREATE TABLE student (
    studentID VARCHAR(20) PRIMARY KEY COMMENT '学号',
    userID VARCHAR(22) COMMENT '用户ID',
    name VARCHAR(100) NOT NULL COMMENT '学生姓名',
    phoneNumber VARCHAR(20) COMMENT '电话号码',
    age INT COMMENT '年龄',
    is_deleted BOOLEAN DEFAULT FALSE COMMENT '是否删除',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (userID) REFERENCES sso_user(userID)
);
```

当然也可以使用sql语句初始化项目

### 3 请求技能生成代码

向 AI 开发工具进行对话：

例如：

```sql
请根据以下SQL CREATE TABLE 语句（或者是sql文件），生成对应的 FastAPI 项目脚手架代码：
CREATE TABLE student (
    studentID VARCHAR(20) PRIMARY KEY COMMENT '学号',
    userID VARCHAR(22) COMMENT '用户ID',
    name VARCHAR(100) NOT NULL COMMENT '学生姓名',
    phoneNumber VARCHAR(20) COMMENT '电话号码',
    age INT COMMENT '年龄',
    is_deleted BOOLEAN DEFAULT FALSE COMMENT '是否删除',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (userID) REFERENCES sso_user(userID)
);
```

然后请求使用此技能生成脚手架代码。

## 生成的目标项目代码结构

首次运行时，技能将生成完整的项目结构：

```text
fastapi_project/
├── app/
│   ├── __init__.py
│   ├── factory.py                 # lifespan 在工厂内
│   ├── config.py
│   ├── exceptions.py
│   ├── middleware.py
│   └── routes.py
├── config/                        # 唯一配置源：from config import settings
│   ├── __init__.py
│   ├── config_unified.py
│   ├── config_factory.py
│   └── manage.py
├── core/
│   ├── __init__.py
│   ├── database.py
│   ├── cache.py
│   ├── queue.py
│   ├── security.py
│   └── permissions.py
├── models/
│   ├── __init__.py
│   ├── base.py
│   └── student.py                 # 按表生成
├── schemas/
│   ├── __init__.py
│   ├── response.py
│   └── student.py                 # 按表生成
├── repository/                    # 可覆盖：仅 create/delete/update/get（增删改查，单条）
│   ├── __init__.py
│   └── student_repository.py      # 按表生成
├── service/                       # 人手维护：单条委托 + 列表等业务
│   ├── __init__.py
│   ├── dependencies.py            # 追加 get_*_service
│   └── student_service.py         # 按表生成
├── api/
│   ├── __init__.py
│   └── v1/
│       ├── __init__.py
│       └── student/               # 文件夹用表名原样
│           ├── __init__.py        # 导出 router（新表必建）
│           └── studentResource.py # prefix 使用 route_prefix
├── middleware/
│   ├── __init__.py
│   ├── security_headers.py
│   ├── rate_limiter.py
│   └── audit_middleware.py
├── utils/                         # 日志只用 logger.py
│   ├── __init__.py
│   ├── logger.py
│   ├── custom_exceptions.py
│   ├── response_code.py
│   ├── validators.py
│   ├── masking.py
│   ├── ids.py
│   ├── auth.py
│   ├── security.py
│   └── audit.py
├── docker/                        # 起步 compose：app + MySQL
├── deploy/                        # 进阶运维素材，不进入默认 compose
├── start.py
├── pyproject.toml
├── .python-version
├── .gitignore
├── requirements.txt
├── .env.example
└── .env.docker
```

后续添加新表时，生成：

1. **models/{table_name}.py** - SQLAlchemy 数据模型
2. **schemas/{table_name}.py** - Pydantic 验证模型（Base、Create、Update、Response；有状态字段时含 StatusUpdate）
3. **repository/{table_name}_repository.py** - 仅 `create` / `delete` / `update` / `get`（增删改查顺序，可覆盖）
4. **service/{table_name}_service.py** - 单条委托 + `get_list` 等业务（仅不存在时新建；有状态字段时含 `update_status`）
5. **api/v1/{resource_singular}/{resource_singular}Resource.py** - 文件夹用表名原样；`APIRouter` 前缀用 `route_prefix`（`_` 换成 `-`）。统一只调 Service（有状态字段时含 `PATCH /{pk}/status`）
6. **tests/unit/test_{table_name}_service.py** - Service 单元测试占位（仅不存在时新建）
7. **tests/integration/api/v1/test_{table_name}.py** - 接口 CRUD 集成测试 + 商业逻辑占位（仅不存在时新建）
8. **api/v1/{resource_singular}/__init__.py** - 新建并导出 `router`（缺它会导致 `from api.v1.xxx import router` 报 ImportError）
9. **service/dependencies.py**、**api/v1/__init__.py** - 幂等追加注册 `get_*_service` / `include_router`；追加前去重，同一 SQL 连跑两次零 diff

> 增量生成时 **不**覆盖 `utils/**`、`middleware/**`、`docker/**`、`deploy/**`。import 使用 `project_baseline.json` 的 `canonical_imports`。
> 以上是 `add_table`（新增表）的产物；**表结构修改**走另一套差异驱动流程，见下文「已有项目的增量更新」。

**路由结构**：

- `api/__init__.py` → `api_router` (prefix="/api")
- `api/v1/__init__.py` → `v1_router` (prefix="/v1")
- 子路由不额外加前缀，由具体API文件定义

**中间件结构**：

- `middleware/`：基线三件套（`security_headers` / `rate_limiter` / `audit_middleware`）
- `app/middleware.py`：统一注册；CORS 始终开启；安全中间件按 `middleware_*_enabled` 开关（默认关闭）

首次空项目会复制 `docker/` 和 `deploy/`。`deploy/` 是进阶运维素材，不要求随默认 compose 启动。

不生成这些内容：

- 数据库初始化脚本（由用户放入 `database/`）
- 按表的业务规则实现（Service 占位，人手补齐）
- 已淘汰骨架：`app/events.py`、`app/router.py`、`config/settings.py`、`utils/loguru.py`、`core/dependencies.py`

## 特性说明

### 测试代码

按表生成两类测试（模板见 `resources/templates/layers/test/`）：

|类型|路径|内容|
|---|---|---|
|单元占位|`tests/unit/test_{table}_service.py`|面向 Service；默认 `skip`，人手补齐|
|集成|`tests/integration/api/v1/test_{table}.py`|**可跑** CRUD（真实 MySQL）+ 商业逻辑接口 `skip` 占位|

运行示例：

```bash
uv run pytest tests/integration/api/v1/test_admin.py -c tests/pytest.ini -v
```

### 软删除/硬删除

技能会自动检测表中是否有软删除字段（支持以下字段名）：

- `is_deleted`
- `is_delete`
- `deleted`

**软删除逻辑**（有软删除字段时）：

- Service.`get_list()` - 只查询未删除的记录
- Repository.`get()` / `update()` - 只操作未删除的记录
- Repository.`delete()` - 设置软删除字段为 True

**硬删除逻辑**（无软删除字段时）：

- Service.`get_list()` - 查询所有记录
- Repository.`get()` / `update()` - 按主键操作
- Repository.`delete()` - 直接从数据库删除记录

### 状态/标识位专用接口

按 `resources/config/status_flag_fields.json` 识别状态字段（如 `status`、`is_active`、`*_flag` 等；排除软删与密码等）。

命中后额外生成：

|层|产物|
|---|---|
|Schema|`{ClassName}StatusUpdate`；状态字段从通用 `Update` 排除|
|Service|`update_status`（业务入口；内部 `repo.update(字段字典)`）|
|Resource|`PATCH /{pk}/status`|

> Repository **仅** `create` / `delete` / `update` / `get`，不生成 `update_status` / `get_list`。

示例（`sso_user.status`）：

```http
PATCH /api/v1/sso-user/{user_id}/status
Content-Type: application/json

{"status": 0}
```

> 状态变更必须走专用接口，禁止通过通用 `PUT` 修改。

### 依赖注入

在 `service/dependencies.py` 中为每张表生成：

- `get_{table}_service` — **Resource 统一使用**
- `get_{table}_repository` — 一般仅供 Service 内部或特殊场景

```python
from service.dependencies import get_student_service

async def get_student_list(
    ...,
    service: StudentService = Depends(get_student_service),
):
    result = await service.get_list(...)
    ...
```

### 数据验证

自动为以下字段生成验证器：

- 手机号（字段名包含 `phone`）：中国手机号格式验证
- 邮箱（字段名包含 `email`）：邮箱格式验证
- 年龄（字段名为 `age`）：0-150 范围验证
- 性别（字段名包含 `gender` 或 `sex`）：枚举值验证

### 数据脱敏

自动为敏感字段生成脱敏属性：

- 手机号（显示前 3 位 + **** + 后 4 位）
- 邮箱（显示前 3 位 + **** + 后 4 位）

## 已有项目的增量更新

技能不只用于"从零建项目"。目标项目已存在骨架时，**先逐表判定运行模式**（`resources/config/incremental_change_policy.json`），执行流程见 `resources/specifications/incremental_update.md`。

| 你说的 | 模式 | 技能做什么 |
|--------|------|-----------|
| 「把这张新表加到现有项目」 | `add_table` | 生成 7 类文件 + 新建 `api/v1/{resource}/__init__.py` + 幂等追加注册 |
| 「这张表加了几个字段 / 改了类型 / 加了 status」 | `alter_table` | 旧/新结构字段级差异 → 分层重生成 → 手写文件出待办 → DDL 建议 |
| 「这张表要下线」 | `drop_table` | 只输出待删清单与顺序，不自动删文件、不执行 DDL |
| 空项目 | `greenfield` | 生成完整骨架 + 全部表 |

### 用法示例

**新增表**：把新的 `CREATE TABLE` 贴给技能，并说明"加到已有项目"即可。

**表结构修改**（推荐同时给旧版 DDL，可减少歧义）：

```text
现有项目里 student 表结构变了，请同步接口代码。
旧：CREATE TABLE student (student_id VARCHAR(20) PRIMARY KEY, name VARCHAR(100) NOT NULL, ...);
新：CREATE TABLE student (student_id VARCHAR(20) PRIMARY KEY, name VARCHAR(100) NOT NULL,
                         email VARCHAR(120), status TINYINT DEFAULT 1, ...);
```

技能会先给出差异清单（`added email`、`flag 新增 status`、`risk` 等），确认高风险项后：

- **覆盖**：`models/` `schemas/` `repository/`（仅带 `【AUTO-GENERATED】` 标记的文件）
- **重生成内置 CRUD、保留手写路由**：`api/v1/{resource}/{resource}Resource.py`
- **绝不覆盖**：`service/*_service.py`、两类测试、`README.md` → 输出人工待办清单
- **同步三件套**：新增状态位时 `StatusUpdate` ↔ `update_status` ↔ `PATCH /{pk}/status` 必须同进同退；其中 `update_status` 位于手写 Service，需**先展示片段、取得确认、再仅追加最小方法**
- **完全不碰**：`utils/` `middleware/` `docker/` `deploy/`，以及已存在的 `scripts/export_openapi.py`
- **重新导出**：`uv run python scripts/export_openapi.py`，覆盖 `docs/openapi.json` 与 `docs/api.md`

### 接口文档

生成或改完接口代码后，技能会在目标项目里补上 `scripts/export_openapi.py`（已有则不覆盖），并运行它写出：

- `docs/openapi.json`：导入 Apifox 或 Apipost 时选 OpenAPI / Swagger，上传这个文件
- `docs/api.md`：给人阅读。平台不会把它转成可调试的接口

文档从当前应用的路由导出，路径和响应包裹与代码一致。默认 CRUD 不带登录。你后来加在应用上的路由，重新导出后会一起出现。字段变了就重新导出，不要手改这两份文件。约定见 `resources/specifications/api_docs.md`。

### DDL 边界

技能**不执行 DDL**、不连库、不改 `database/`、不接 Alembic、不删数据。只在变更报告里给出 MySQL `ddl_hint` 建议和发布顺序：加列先 DDL 后发代码；删列先发代码（停止引用）后 DDL。

### 增量后验证

```bash
uv run python -c "import start"                  # 捕获 import / 列名残留 / 注册漏项
uv run pytest tests/ -c tests/pytest.ini -v
uv run uvicorn start:app --reload               # /docs 核对 Schema 与端点
uv run python scripts/export_openapi.py          # 重写 docs/openapi.json 与 docs/api.md
```

变化字段做 `POST → GET 详情 → PUT → DELETE` 冒烟；再把同一份 SQL 跑一次确认零 diff（幂等）。

## 项目启动（推荐 uv）

生成完成后，按以下步骤启动项目。依赖与虚拟环境默认用 [uv](https://docs.astral.sh/uv/) 管理（约定见 `resources/config/package_manager.json`）。

1. 安装 uv（若尚未安装）

   参见：<https://docs.astral.sh/uv/getting-started/installation/>

2. 同步依赖（创建/更新 `.venv`）

   ```bash
   uv sync
   ```

   > `pyproject.toml` 中 `default-groups = ["dev"]`，会一并安装测试依赖。  
   > 增删依赖：`uv add <package>` / `uv add --dev <package>`

3. 配置环境变量

   ```bash
   cp .env.example .env
   # 编辑 .env 文件，配置数据库连接等
   ```

4. 启动应用

   ```bash
   uv run uvicorn start:app --reload
   # 或
   uv run python start.py
   ```

5. 导出接口文档，并访问在线文档

   ```bash
   uv run python scripts/export_openapi.py
   ```

   - 导入 Apifox 或 Apipost：选择 OpenAPI / Swagger，上传 `docs/openapi.json`
   - 给人看的说明：`docs/api.md`
   - Swagger UI: <http://localhost:8000/docs>
   - ReDoc: <http://localhost:8000/redoc>

### 兼容：未安装 uv 时

```bash
pip install -r requirements.txt
uvicorn start:app --reload
# 或: python start.py
```
