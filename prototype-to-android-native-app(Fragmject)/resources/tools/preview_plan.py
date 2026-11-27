#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""预览多模块 Android 工程模板和 feature 展开计划。"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "modular_project_structure"


def pascal(name):
    return "".join(part[:1].upper() + part[1:] for part in re.split(r"[-_\s]", name) if part)


def normalized_features(ctx):
    features = ctx.get("features") or []
    pages = ctx.get("pages", [])
    if not features:
        domains = sorted({page.get("domain", "main") for page in pages})
        features = [{"domain": domain, "pages": []} for domain in domains or ["main"]]
    by_domain = {feature["domain"]: dict(feature) for feature in features if feature.get("domain")}
    for feature in by_domain.values():
        feature["pages"] = list(feature.get("pages", []))
    for page in pages:
        domain = page.get("domain", "main")
        feature = by_domain.setdefault(domain, {"domain": domain, "pages": []})
        if page.get("page_name") and page["page_name"] not in feature["pages"]:
            feature["pages"].append(page["page_name"])
    return list(by_domain.values())


def build_plan(ctx):
    package_path = ctx.get("project", {}).get("package_name", "com.example.app").replace(".", "/")
    features = normalized_features(ctx)
    planned = []
    for path in sorted(TEMPLATE_DIR.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(TEMPLATE_DIR).as_posix()
        if "/feature/{{domain}}/" in "/" + rel:
            for feature in features:
                expanded = rel.replace("{{domain}}", feature["domain"])
                expanded = expanded.replace("{{domain_pascal}}", pascal(feature["domain"]))
                expanded = expanded.replace("{{package_path}}", package_path)
                planned.append(expanded)
        else:
            planned.append(rel.replace("{{package_path}}", package_path))
    return package_path, features, planned


def main():
    if len(sys.argv) < 2:
        print("用法: python preview_plan.py <proto_context.json>")
        return 1
    context_path = Path(sys.argv[1])
    if not context_path.exists():
        print("错误：文件不存在 %s" % context_path)
        return 2
    if not TEMPLATE_DIR.is_dir():
        print("错误：多模块模板目录不存在 %s" % TEMPLATE_DIR)
        return 2

    ctx = json.loads(context_path.read_text(encoding="utf-8"))
    project = ctx.get("project", {})
    package_path, features, files = build_plan(ctx)
    print("工程名：%s" % project.get("project_name", ""))
    print("包名：%s（目录：%s）" % (project.get("package_name", ""), package_path))
    print("业务域：%s" % (", ".join(feature["domain"] for feature in features) or "待确认"))
    print("页面数：%d" % len(ctx.get("pages", [])))
    print("计划文件数：%d" % len(files))
    print("SDK：min=%s / target=%s / compile=%s / JDK=%s" % (
        project.get("min_sdk"), project.get("target_sdk"),
        project.get("compile_sdk"), project.get("jdk"),
    ))
    resolution = project.get("version_resolution", {})
    if (
        not project.get("versions")
        or resolution.get("selection") != "latest-stable-compatible"
        or resolution.get("compatibility_verified") is not True
        or resolution.get("checked_at") != date.today().isoformat()
        or not resolution.get("sources")
    ):
        print("⚠️ 缺少今天核验的最新稳定兼容版本元数据；renderer 会拒绝生成 Gradle 配置。")

    print("\n模块图：")
    print("  :app")
    for module in (
        "common", "component-runtime", "designsystem", "ipc",
        "monitor", "network", "router", "startup", "storage",
    ):
        print("  :core:%s" % module)
    for feature in features:
        print("  :feature:%s:api" % feature["domain"])
        print("  :feature:%s:impl -> :feature:%s:api" % (
            feature["domain"], feature["domain"],
        ))

    diagnostics = ctx.get("diagnostics", {})
    if diagnostics.get("need_confirm"):
        print("\n待确认项：")
        for item in diagnostics["need_confirm"]:
            print("  - %s" % item)
    print("\n文件计划：")
    for file_path in files:
        print("  - %s" % file_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
