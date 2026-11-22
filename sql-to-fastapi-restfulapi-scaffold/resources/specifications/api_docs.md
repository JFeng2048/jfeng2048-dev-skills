# 接口文档

生成或增量改完代码后，从当前 FastAPI 应用导出文档，不按 SQL 手写一份平行的接口清单。

## 文件

| 文件 | 给谁 | 怎么来 |
|------|------|--------|
| `docs/openapi.json` | Apifox、Apipost | `app.openapi()`，覆盖旧文件 |
| `docs/api.md` | 人阅读、评审 | 同一份 OpenAPI 转成 Markdown，覆盖旧文件 |
| `scripts/export_openapi.py` | 导出入口 | 模板原样拷入；目标项目里已有则不覆盖 |

导入 Apifox 或 Apipost 时选择 OpenAPI / Swagger，上传 `docs/openapi.json`。`docs/api.md` 不能当作接口定义导入，平台只会把它存成一篇文档，不会变成可调试的接口。

## 内容

- 路径与代码一致。业务路由挂在 `/api` + `/v1` + `/{route_prefix}`，例如 `/api/v1/student`。
- 列表、详情、创建、更新、删除都在。表有状态字段时包含 `PATCH /{pk}/status`。
- 请求体用生成的 Create / Update / StatusUpdate。响应用 `SuccessResponse` 或 `PaginationResponse` 包住 Response。
- 脚手架默认的 CRUD 不声明鉴权，导入后不要给每条接口自动带 Token。用户后来在路由上加了登录依赖的，重新导出后写在对应接口上。
- 用户写在「手写业务路由区」、并且已经 `include_router` 的接口，会跟着导出。只改 Markdown 或 JSON、不改代码的，下次导出会被盖掉。

## 何时导出

`greenfield`、`add_table`、`alter_table` 在代码落盘后执行：

```text
uv run python scripts/export_openapi.py
```

依赖未安装时先 `uv sync`。脚本不连接数据库。

`drop_table` 只输出待删清单、不改代码，此时不导出。用户按清单改完代码后，再导出一次。

## 禁止

- 手改 `docs/openapi.json` 或 `docs/api.md` 来同步字段、路径或鉴权。
- 用 Markdown 代替 `openapi.json` 作为导入文件。
- 覆盖用户已经改过的 `scripts/export_openapi.py`。
