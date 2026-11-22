"""从当前 FastAPI 应用导出接口文档。

写出两份文件，都覆盖同名旧文件：
- docs/openapi.json  给 Apifox / Apipost 按 OpenAPI 导入
- docs/api.md        给人阅读，不要把它当接口定义导入

在项目根目录执行：uv run python scripts/export_openapi.py
只读取已注册的路由，不连接数据库。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
METHODS = ("get", "post", "put", "patch", "delete")


def load_spec() -> dict:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from start import app

    spec = app.openapi()
    info = spec.setdefault("info", {})
    note = (
        "脚手架生成的业务接口默认不要求登录。"
        "导入 Apifox 或 Apipost 时选择 OpenAPI / Swagger，上传本文件。"
    )
    description = (info.get("description") or "").strip()
    if "Apifox" not in description:
        info["description"] = f"{description}\n\n{note}".strip()
    if not spec.get("servers"):
        spec["servers"] = [{"url": "http://127.0.0.1:8000", "description": "本地"}]
    return spec


def _ref_name(schema: dict | None) -> str:
    if not schema:
        return ""
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    for key in ("anyOf", "allOf", "oneOf"):
        for item in schema.get(key) or []:
            name = _ref_name(item)
            if name:
                return name
    items = schema.get("items")
    if isinstance(items, dict):
        return _ref_name(items)
    return schema.get("type") or ""


def _response_names(operation: dict) -> str:
    names = []
    for code, response in (operation.get("responses") or {}).items():
        content = (response or {}).get("content") or {}
        json_body = content.get("application/json") or {}
        name = _ref_name(json_body.get("schema"))
        names.append(f"{code} {name}".strip())
    return "、".join(names)


def render_markdown(spec: dict) -> str:
    info = spec.get("info") or {}
    lines = [
        f"# {info.get('title') or 'API'}",
        "",
        "这份文档给人阅读和评审。导入 Apifox 或 Apipost 时，选择 OpenAPI / Swagger，上传同目录的 `openapi.json`。不要把本文件当作接口定义导入。",
        "",
        "当前脚手架的业务接口默认不要求登录。某一条接口下面写了「鉴权」的，才是代码里已经挂了登录依赖；重新导出后以代码为准。",
        "",
        "## 接口",
        "",
    ]
    found = False
    for path, item in (spec.get("paths") or {}).items():
        for method in METHODS:
            operation = item.get(method)
            if not operation:
                continue
            found = True
            summary = operation.get("summary") or operation.get("operationId") or ""
            lines.append(f"### {method.upper()} `{path}`")
            lines.append("")
            if summary:
                lines.append(summary)
                lines.append("")
            if operation.get("description"):
                lines.append(operation["description"].strip())
                lines.append("")
            security = operation.get("security")
            lines.append(f"- 鉴权：{security if security else '无'}")
            params = operation.get("parameters") or []
            if params:
                lines.append("- 参数：")
                for param in params:
                    location = param.get("in") or ""
                    name = param.get("name") or ""
                    required = "必填" if param.get("required") else "可选"
                    desc = param.get("description") or ""
                    lines.append(f"  - `{name}`（{location}，{required}）{desc}")
            body = ((operation.get("requestBody") or {}).get("content") or {}).get("application/json") or {}
            body_name = _ref_name(body.get("schema"))
            if body_name:
                lines.append(f"- 请求体：`{body_name}`")
            responses = _response_names(operation)
            if responses:
                lines.append(f"- 响应：{responses}")
            lines.append("")
    if not found:
        lines.append("当前应用没有可导出的业务接口。")
        lines.append("")

    schemas = ((spec.get("components") or {}).get("schemas")) or {}
    if schemas:
        lines.append("## 数据模型")
        lines.append("")
        for name, schema in schemas.items():
            props = schema.get("properties") or {}
            required = set(schema.get("required") or [])
            lines.append(f"### `{name}`")
            lines.append("")
            if not props:
                lines.append(schema.get("description") or "无字段。")
                lines.append("")
                continue
            for prop, meta in props.items():
                kind = _ref_name(meta) or meta.get("type") or ""
                mark = "必填" if prop in required else "可选"
                desc = meta.get("description") or ""
                lines.append(f"- `{prop}` {kind}（{mark}）{desc}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    spec = load_spec()
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "openapi.json").write_text(
        json.dumps(spec, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (DOCS / "api.md").write_text(render_markdown(spec), encoding="utf-8")
    print("wrote docs/openapi.json")
    print("wrote docs/api.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
