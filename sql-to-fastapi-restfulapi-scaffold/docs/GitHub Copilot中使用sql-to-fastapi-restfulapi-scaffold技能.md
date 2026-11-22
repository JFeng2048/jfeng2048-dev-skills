# GitHub Copilot 中使用 sql-to-fastapi-restfulapi-scaffold 技能指南

## 1. 目的

本文说明如何在 VS Code 的 GitHub Copilot Chat 中使用 `sql-to-fastapi-restfulapi-scaffold`，从 SQL `CREATE TABLE` 生成 FastAPI RESTful 项目脚手架。

适用目录：

- `sql-to/sql-to-fastapi-restfulapi-scaffold/`

## 2. 前置条件

1. 已安装 VS Code。
2. 已安装并登录 GitHub Copilot。
3. 已打开本仓库工作区。
4. 已准备包含 `CREATE TABLE` 的 SQL。

## 3. 核心资源

在 Copilot 对话中明确引用：

- `sql-to/sql-to-fastapi-restfulapi-scaffold/SKILL.md`
- `sql-to/sql-to-fastapi-restfulapi-scaffold/README.md`
- `sql-to/sql-to-fastapi-restfulapi-scaffold/resources/config/naming_rules.json`
- `sql-to/sql-to-fastapi-restfulapi-scaffold/resources/config/type_mappings.json`
- `sql-to/sql-to-fastapi-restfulapi-scaffold/resources/config/project_baseline.json`
- `sql-to/sql-to-fastapi-restfulapi-scaffold/resources/config/status_flag_fields.json`
- `sql-to/sql-to-fastapi-restfulapi-scaffold/resources/specifications/coding_standards.md`
- `sql-to/sql-to-fastapi-restfulapi-scaffold/resources/templates/`

## 4. 推荐交互

1. 打开 Copilot Chat，选择能读取工作区文件的模式。
2. 要求按 `SKILL.md` 生成，并点名上面的配置与模板目录。
3. 粘贴 SQL，或给出 SQL 文件路径。
4. 说明这是首次生成还是往已有项目增量加表。

示例提示：

```text
请使用 sql-to-fastapi-restfulapi-scaffold。
先阅读 SKILL.md、resources/config/naming_rules.json、resources/config/project_baseline.json 和 resources/templates/。
根据下面的 CREATE TABLE 生成 FastAPI 脚手架。
资源文件夹使用表名原样（蛇形单数），路由前缀把下划线换成连字符，禁止复数。
日志使用 utils.logger，不要生成 loguru、app/events.py、config/settings.py、core/dependencies.py。
```

## 5. 生成时核对

- 空项目要复制 `docker/` 与 `deploy/`。`deploy/` 只是进阶运维素材，不进入默认 compose 必跑栈。
- 不生成数据库初始化脚本。
- Repository 方法顺序为 `create` / `delete` / `update` / `get`。
- Resource 只依赖 Service。依赖注册写在 `service/dependencies.py`。
- 表 `company_file` 的目录是 `api/v1/company_file/`，前缀是 `/company-file`。
