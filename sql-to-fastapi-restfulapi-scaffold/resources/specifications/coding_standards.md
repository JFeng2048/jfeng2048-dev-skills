# SQL-to-FastAPI-Scaffold 代码规范

## 1. 概述

本文档定义了 SQL-to-FastAPI-Scaffold 生成代码时应遵循的规范和最佳实践。

## 1.1 包管理与启动（uv）

目标项目默认使用 [uv](https://docs.astral.sh/uv/) 管理依赖与启动，细则见 `resources/config/package_manager.json`。

| 文件 | 作用 |
|------|------|
| `pyproject.toml` | **主**依赖清单（PEP 621 + `[dependency-groups].dev`） |
| `.python-version` | uv 使用的 Python 版本钉选 |
| `requirements.txt` | 与运行时依赖同步的 pip 兼容清单 |

推荐命令：

```bash
uv sync
uv run uvicorn start:app --reload
uv run python start.py
uv run pytest -c tests/pytest.ini -v
uv add <package>            # 运行时依赖
uv add --dev <package>      # 开发/测试依赖
```

生成 README 与对话「下一步」时优先写 uv；可附带 `pip install -r requirements.txt` 作为兼容路径。  
`start.py` 须提供 `main()`，便于 `uv run python start.py`。

## 2. 格式规范

### 2.1 缩进与空格

- 使用 4 个空格进行缩进
- 不使用 Tab 字符
- 行尾不留多余空格
- 文件末尾保留一个空行

### 2.2 行宽

- 最大行宽 120 字符
- 超过行宽时合理换行

### 2.3 空行

- 模块级函数或类之间留 2 个空行
- 类内部的方法之间留 1 个空行
- 函数或方法内部逻辑块之间留 1 个空行

### 2.4 导入顺序

导入应按以下顺序分组，组之间留一个空行：

1. 标准库导入
2. 第三方库导入
3. 本地模块导入

示例：

```python
# 标准库
from typing import List, Optional
from datetime import datetime

# 第三方库
from sqlalchemy import Column, String
from pydantic import BaseModel

# 本地模块
from models.base import BaseModel
from schemas.response import SuccessResponse
```

## 3. 命名规范

### 3.1 类名

- 使用大驼峰命名法（PascalCase）
- 首字母大写
- 不使用下划线分隔

### 3.2 函数与方法名

- 使用蛇形命名法（snake_case）
- 全小写
- 用下划线分隔单词

### 3.3 常量

- 使用全大写下划线分隔（UPPER_SNAKE_CASE）
- 在模块顶部定义

### 3.4 私有成员

- 使用单下划线前缀（_private_member）
- 表示非公开接口

## 4. 文档字符串规范

### 4.1 模块文档字符串

每个模块文件顶部应有模块文档字符串：

```python
"""
模块功能描述

此文件由 SQL-to-FastAPI-Scaffold 自动生成
"""
```

### 4.2 类文档字符串

每个类应有类文档字符串：

```python
class ClassName(BaseModel):
    """
    类功能描述
    """
```

### 4.3 方法文档字符串

每个公共方法应有方法文档字符串：

```python
def method_name(self, param: Type) -> ReturnType:
    """
    方法功能描述
    """
```

### 4.4 语言要求

所有文档字符串使用中文。

## 5. SQLAlchemy 模型规范

### 5.1 继承关系

所有模型必须继承 `BaseModel`：

```python
from models.base import BaseModel

class ModelName(BaseModel):
    pass
```

### 5.2 表名

- 使用 `__tablename__` 属性定义表名
- 表名使用蛇形命名法
- 与数据库表名保持一致

### 5.3 字段定义

- 字段名使用蛇形命名法
- 字段定义使用 `Column`
- 必须包含 `comment` 参数说明字段用途
- 约束顺序：`primary_key` → `nullable` → `unique` → `default` → `comment`

### 5.4 外键与关系

- 外键字段命名格式：`{related_table}_id`
- 关系属性命名格式：`{related_table}`
- 使用 `relationship` 定义关系

## 6. Pydantic Schema 规范

### 6.1 基础模型

- `{ClassName}Base`：包含业务字段，不包含主键
- 字段必填使用 `...`，可选使用 `None`

### 6.2 创建模型

- `{ClassName}Create`：继承 Base，添加主键字段
- 包含完整的示例数据

### 6.3 更新模型

- `{ClassName}Update`：所有字段使用 `Optional`
- 设置 `extra = "forbid"` 防止批量赋值
- 不包含主键字段
- **不包含**状态/标识位字段（见 `status_flag_fields.json`）

### 6.4 状态更新模型（有状态字段时）

- `{ClassName}StatusUpdate`：仅含识别出的状态/标识位字段
- 字段必填（`...`），`extra = "forbid"`
- 供专用改状态接口使用，禁止混入通用 Update

### 6.5 响应模型

- `{ClassName}Response`：包含所有字段 + `is_delete` + `add_time`
- 设置 `from_attributes = True`
- 包含完整示例

### 6.6 字段验证器

- 使用 `@field_validator` 装饰器
- 验证器命名格式：`validate_{field_name}`
- 处理 `None` 值情况

## 7. FastAPI Resource 规范

### 7.1 路由前缀

- 文件夹与 Python 标识符使用 `resource_singular`（表名原样，蛇形单数）：`api/v1/{resource_singular}/{resource_singular}Resource.py`
- HTTP 前缀使用另一个变量 `route_prefix`：`APIRouter(prefix="/{route_prefix}")`。它等于 `resource_singular` 把 `_` 换成 `-`，仍然单数。例如 `company_file` → 文件夹 `company_file`、前缀 `/company-file`
- 不要把 `resource_singular` 直接写进 `prefix`，否则 `company_file` 会变成 `/company_file`
- tags 使用中文说明

### 7.2 端点方法

- GET /：获取列表，分页
- GET /{id}：获取详情
- POST /：创建
- PUT /{id}：更新（不含状态/标识位）
- PATCH /{id}/status：修改状态/标识位（**表含状态字段时必须生成**）
- DELETE /{id}：软删除或硬删除（由 Repository 决定，经 Service 委托）

### 7.3 依赖与异常

**必须**：
- 所有端点添加 `@handle_service_exceptions`（或项目等价装饰器）
- 通过 `Depends(get_{table}_service)` 注入 **Service**（**禁止** Resource 直接注入 Repository）
- 请求体/字段格式校验由 Pydantic Schema 在进入端点前完成

**可选**：
- `current_user = Depends(get_current_active_user)` — 仅在启用鉴权时添加（脚手架默认不启用鉴权，接口开箱即用）

### 7.4 OpenAPI 文档

- 必须设置 `summary`、`response_model`、`status_code`

## 8. 分层：API → Service → Repository

### 8.1 总体约定

```text
api (Resource) → service（单条委托 + 列表等业务） → repository（仅 create/delete/update/get，增删改查顺序） → model
（Schema 负责进入 API 前的数据校验）
```

| 层 | 路径 | Skill 覆盖 | 职责 |
|----|------|------------|------|
| utils（基线） | `utils/` | **已存在则跳过**（`project_baseline.json`） | 通用工具；不按表生成 |
| middleware（基线） | `middleware/` | **已存在则跳过** | 安全头 / 限流 / 审计；配置开关默认关 |
| docker（基线） | `docker/` | **已存在则跳过** | 起步 Docker：app + MySQL（Redis 可选） |
| deploy（基线） | `deploy/` | **已存在则跳过** | 进阶运维配置；非默认 compose 必跑 |
| Repository | `repository/{table}_repository.py` | **可覆盖** | 仅单条 CRUD |
| Service | `service/{table}_service.py` | **仅不存在时生成** | 单条委托；列表/状态等业务 |
| Resource | `api/v1/...` | 可覆盖基础 CRUD | HTTP；只调 Service |

### 8.2 Repository 规范

```python
class {{ClassName}}Repository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(...): ...    # 增
    async def delete(...): ...    # 删
    async def update(...): ...    # 改；可接受 Update Schema 或字段字典
    async def get(...): ...       # 查；单条，按主键
```

- 使用异步 SQLAlchemy（`AsyncSession` + `select()`）
- **仅**上述 4 个方法；源码定义顺序固定为 **增删改查**：`create` → `delete` → `update` → `get`
- 禁止 `get_list` / `update_status` / `update_fields` / `exists_by_pk` 等
- 禁止写业务规则（分页列表、跨表流程、复杂校验编排）
- 文件头标注 `AUTO-GENERATED`

### 8.3 Service 规范

```python
class {{ClassName}}Service:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = {{ClassName}}Repository(db)

    # -------------------- 单条 CRUD（委托 Repository）--------------------
    async def create(self, data):
        obj = await self.repo.create(data)
        return {{ClassName}}Response.model_validate(obj)

    async def get_detail(...):
        obj = await self.repo.get(...)
        ...

    async def update(...): ...  # 不含状态字段
    async def delete(...): ...

    # -------------------- 业务逻辑：列表 --------------------
    async def get_list(...):
        # 分页 / 过滤 / 软删排除：在本层用 self.db + Model 查询
        ...

    # -------------------- 业务逻辑：状态/标识位（有则生成）--------------------
    async def update_status(self, pk, data: StatusUpdate):
        obj = await self.repo.update(pk, data.model_dump(exclude_unset=True))
        return {{ClassName}}Response.model_validate(obj)

    # ---------- 在下方添加商业逻辑方法 ----------
```

- **组合** Repository，不要继承 Repository
- 单条操作委托 `repo.create` / `repo.delete` / `repo.update` / `repo.get`
- 列表、状态变更等业务写在本层
- 文件头标注 `HAND-WRITTEN`；已存在则 skill **跳过**

### 8.3.1 状态/标识位字段

识别规则见 `resources/config/status_flag_fields.json`。

- 命中后：Schema `StatusUpdate` + Service `update_status` + Resource `PATCH /{pk}/status`
- Repository 仅 `create/delete/update/get`（增删改查顺序），不暴露 `update_status`
- 软删除字段走 DELETE，不走本规则
- 示例：`{{table_name}}.status` → `PATCH /{{route_prefix}}/{pk}/status`

### 8.4 错误处理

使用基线包 `utils.custom_exceptions`（见 `project_baseline.json` 的 `canonical_imports`）：

```python
from utils.custom_exceptions import NotFoundException, ValidationException, BusinessException
from utils.response_code import RET, BusinessCode

raise NotFoundException("{{table_comment}}不存在")
raise ValidationException("请求参数错误")
raise BusinessException(RET.DATAERR, detail="业务校验失败")
# 有业务码时：先把常量登记到 BusinessCode，并补 error_map_CN / error_map_EN
raise BusinessException(BusinessCode.DEMO_NOT_FOUND, detail="业务对象不存在")
```

Resource 统一：

```python
from utils.custom_exceptions import handle_service_exceptions
```

禁止另造 `BadRequestException` / `BaseException`（旧模板名）或新建 `utils/{table}_exceptions.py`。

### 8.4.1 utils 基线复用

细则见 `resources/config/project_baseline.json`。

| 规则 | 说明 |
|------|------|
| 策略 | 默认 `brownfield_prefer_existing`：目标已有 `utils/` 则整包跳过 |
| 日志 | `from utils.logger import get_logger`（不是 loguru） |
| 响应码 | `from utils.response_code import RET, BusinessCode, get_message`；只预置通用/HTTP 服务级码，业务码按需追加 |
| 脱敏 | `from utils.masking import mask_phone, mask_email` |
| ID | `from utils.ids import new_business_id` |
| 禁止 | 按表生成 utils 模块；utils 内引用 models/service |

### 8.4.2 middleware 基线

企业级常用三件套随骨架拷贝（见 `project_baseline.json` → `packages.middleware`）：

| 中间件 | 作用 | 配置开关（默认 `false`） |
|--------|------|--------------------------|
| `SecurityHeadersMiddleware` | 安全响应头 | `middleware_security_headers_enabled` |
| `RateLimitMiddleware` | 内存令牌桶限流 | `middleware_rate_limit_enabled` |
| `AuditMiddleware` | HTTP 审计 | `middleware_audit_enabled` |

- 注册入口：`app/middleware.py`（CORS 始终注册；上述三套按开关）
- 已有 `middleware/` 则跳过；禁止按表新建中间件文件
- SQL 注入防护依赖 ORM 参数化，不单独做请求体扫描中间件

### 8.4.3 docker / deploy 基线

首次骨架必须从 `project_structure/` 复制（已存在则跳过）：

| 目录/文件 | 作用 |
|-----------|------|
| `docker/` | 起步栈：`Dockerfile` + `compose`（api + mysql；redis 为 profile） |
| `.env.docker` | Compose 环境覆盖 |
| `deploy/` | 进阶：Nginx、库/缓存调优、Prometheus/Grafana、Logstash、Supervisor 等 |

生成 README 时写明 Docker 启动命令（项目根目录）：

```bash
docker compose -f docker/docker-compose.yml up --build
REDIS_HOST=redis docker compose -f docker/docker-compose.yml --profile redis up --build
```

### 8.5 缓存（可选）

数据修改后如项目启用缓存，在 Service 层按需清理，不要在 Repository 强耦合缓存实现。

## 9. 安全规范

### 9.1 输入验证

- 所有用户输入必须通过 Pydantic Schema 验证
- 敏感字段使用适当的验证器

### 9.2 批量赋值保护

- Update 模型必须设置 `extra = "forbid"`
- 不允许未定义的字段被赋值

### 9.3 敏感数据脱敏

- 手机号、邮箱等敏感字段提供 `masked_*` 属性
- 不在响应中返回原始敏感数据

### 9.4 认证与授权

**默认不启用鉴权**：本脚手架生成的 CRUD 接口默认开箱即用、无需登录。

**需要鉴权时（由业务自决，不强制）**：
- `core/permissions` 已提供 `get_current_active_user` / `require_roles(...)` / `require_permission(...)` / `require_admin` 等通用依赖（角色与权限来自 JWT 载荷，不绑定具体业务表或角色枚举）
- 统一在 router 挂载（推荐）：`APIRouter(..., dependencies=[Depends(get_current_active_user)])`；或单个路由参数 `current_user = Depends(get_current_active_user)`
- 执行操作时记录 `current_user.user_id`（可选）

### 9.5 SQL 注入防护

- 使用 SQLAlchemy ORM，不拼接 SQL
- 参数化查询

## 10. 性能规范

### 10.1 缓存

- 数据修改后调用 `self._clear_cache()`
- 合理使用缓存提高性能

### 10.2 分页

- 列表查询必须分页
- 默认分页大小 20，最大 100

### 10.3 查询优化

- 使用索引字段查询
- 避免 N+1 查询问题

## 11. 错误处理规范

### 11.1 错误类型

- `handle_service_exceptions`：统一处理服务层异常
- 错误信息使用中文
- 错误信息清晰具体

### 11.2 错误响应

- 使用统一的响应格式
- 包含错误代码和错误信息

## 12. 示例SQL规范

### 12.1 CREATE TABLE 语句

- 每个字段必须有 `COMMENT`
- 主键使用 `PRIMARY KEY`
- 非空字段使用 `NOT NULL`
- 唯一约束使用 `UNIQUE`
- 默认值使用 `DEFAULT`
- 外键约束使用 `FOREIGN KEY ... REFERENCES ...`

示例：

```sql
CREATE TABLE sample_item (
    item_id BIGINT PRIMARY KEY COMMENT '主键',
    category_id BIGINT COMMENT '分类ID',
    name VARCHAR(100) NOT NULL COMMENT '名称',
    phone VARCHAR(20) COMMENT '联系电话',
    email VARCHAR(100) UNIQUE COMMENT '邮箱',
    sort_no INT DEFAULT 0 COMMENT '排序号',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (category_id) REFERENCES sample_category(category_id)
) COMMENT='示例业务表';
```

## 13. 测试规范

### 13.1 目录与命名

| 类型 | 路径 | 命名 |
|------|------|------|
| 单元（Service） | `tests/unit/` | `test_{table_name}_service.py` |
| 集成（API） | `tests/integration/api/v1/` | `test_{table_name}.py` |

### 13.2 单元测试占位

- 面向 `{{ClassName}}Service`，使用 `session` fixture（sqlite）
- 默认 `@pytest.mark.skip`，不阻塞 CI
- 覆盖单条委托与 `get_list`；有状态字段时含 `update_status` 占位
- 文件已存在则 skill **跳过**

### 13.3 集成测试

- 使用 `app` fixture（真实 MySQL）+ `Authorization: Bearer test-token`
- **必须**生成可执行的基础 CRUD 流程：`POST` → `GET` 列表 → `GET` 详情 → `PUT` →（可选 `PATCH .../status`）→ `DELETE`
- 按软删/硬删校验库表副作用
- 同文件保留商业逻辑接口测试占位（默认 skip）
- 唯一约束字段使用随机值；文件已存在则 skill **跳过**

### 13.4 模板位置

- `resources/templates/layers/test/unit/test_service_template.py`
- `resources/templates/layers/test/integration/test_api_template.py`

## 14. 已有项目增量变更规范

策略源：`resources/config/incremental_change_policy.json`；执行流程：`resources/specifications/incremental_update.md`。凡目标项目已有骨架，本节优先于第 8.1 节的静态覆盖表。

### 14.1 文件头标记（增量保护依据）

| 文件 | 必须包含的标记 | 含义 |
|------|----------------|------|
| `models/{table}.py`、`schemas/{table}.py` | `【AUTO-GENERATED】` | 允许技能按新 DDL 重新生成 |
| `repository/{table}_repository.py` | `【AUTO-GENERATED】` | 允许覆盖；禁止在此写业务 |
| `api/v1/{res}/{res}Resource.py` | `【AUTO-GENERATED】` + 明确的「手写路由区」注释 | 只重生成内置 CRUD，保留手写路由 |
| `service/{table}_service.py` | `【HAND-WRITTEN】` + `在下方添加商业逻辑方法` 区 | **绝不整文件覆盖** |
| `tests/unit/test_{table}_service.py` | `【HAND-WRITTEN 占位】` | 不覆盖 |
| `tests/integration/api/v1/test_{table}.py` | `【覆盖策略】文件已存在则 skill 跳过` | 不覆盖 |
| `api/v1/__init__.py`、`service/dependencies.py` | `# ---- 脚手架追加区` | 只做幂等追加 |

文件存在但**没有**生成标记 → 视为用户已手改 → 禁止覆盖 → 输出人工待办并询问。

### 14.2 变更处理规则

- `add_table`：生成 7 类文件；**必须**同时新建 `api/v1/{resource_singular}/__init__.py`（`from .{res}Resource import router` + `__all__ = ["router"]`），并在追加区幂等注册。追加前全文去重，同 SQL 连跑两次零 diff。
- `alter_table`：先取旧结构 → 归一化后字段级对比 → 输出差异清单 → 高风险项确认 → 按 `change_types` 分层更新。禁止把「重复提供 CREATE TABLE」当作新表直接覆盖。
- `drop_table` / 表重命名：阻断自动执行，只输出清单。

### 14.3 强制同步规则

1. **状态位三件套**：`{ClassName}StatusUpdate` ↔ `Service.update_status` ↔ `PATCH /{pk}/status` 同进同退；`StatusUpdate` 字段必须从通用 `Update` 排除。新增时向手写 Service 追加方法须「展示片段 → 用户确认 → 仅追加最小方法」。
2. **软删字段**：`Repository.delete` / `get` 可覆盖重生成；`Service.get_list` 的软删过滤在手写文件，必须列入待办；集成测试的删除断言同步（软删留行、硬删无行，详情均 404）。
3. **主键**：变化影响所有层路径参数名与类型，Service 方法签名、测试 payload、README 示例一并列入待办。
4. **接口文档**：代码落盘后执行 `uv run python scripts/export_openapi.py`，覆盖 `docs/openapi.json` 与 `docs/api.md`。导入 Apifox 或 Apipost 用 JSON。禁止手改这两份文件来同步字段。细则见 `api_docs.md`。

### 14.4 迁移与验证边界

技能不执行 DDL、不连库、不改写 `database/`、不接 Alembic、不删数据；只输出 MySQL `ddl_hint` 与发布顺序（加列先 DDL 后发代码；删列先发代码后 DDL）。

增量后必须验证：`uv run python -c "import start"` → `uv run pytest tests/ -c tests/pytest.ini -v` → `/docs` 核对 Schema 与端点 → `uv run python scripts/export_openapi.py` → 变化字段最小 CRUD 冒烟 → 同 SQL 重跑零 diff。变更报告须列出「已重生成 / 已追加注册 / 跳过的手写文件与原因 / 人工待办 / DDL 建议 / 验证结果」。
