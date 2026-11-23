#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""根据 proto_context.json 预览将要生成的 iOS 工程文件计划。

用法：
    python preview_plan.py <proto_context.json>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BASE_FILES = [
    "project.yml",
    ".gitignore",
    "README.md",
    "Configs/Debug.xcconfig",
    "Configs/Release.xcconfig",
]

SOURCES = [
    "App/AppEntry.swift",
    "App/RootView.swift",
    "Core/Common/LoadState.swift",
    "Core/Config/AppConfig.swift",
    "Core/DI/AppContainer.swift",
    "Core/Extensions/View+Modifiers.swift",
    "Core/Networking/APIClient.swift",
    "Core/Networking/APIError.swift",
    "Core/Networking/APITarget.swift",
    "Core/Networking/AuthInterceptor.swift",
    "Core/Router/AppRoute.swift",
    "Core/Storage/SessionStore.swift",
    "Core/Storage/SwiftDataStack.swift",
    "Core/Storage/TokenStorage.swift",
    "Core/Theme/AppTheme.swift",
    "Data/DTO/APIResponse.swift",
    "Data/DTO/LoginDTO.swift",
    "Data/DTO/SkillDTO.swift",
    "Data/Mock/MockData.swift",
    "Data/Models/Skill.swift",
    "Data/Repositories/AuthRepository.swift",
    "Data/Repositories/SkillRepository.swift",
    "Resources/Info.plist",
    "Resources/Assets.xcassets/Contents.json",
    "Resources/Assets.xcassets/BrandPrimary.colorset/Contents.json",
    "Resources/Assets.xcassets/AccentColor.colorset/Contents.json",
    "Resources/Assets.xcassets/AppIcon.appiconset/Contents.json",
    "Resources/zh-Hans.lproj/Localizable.strings",
    "Resources/en.lproj/Localizable.strings",
]

RESOURCE_COLORSETS = [
    "AppBackground", "Surface", "TextPrimary", "TextSecondary", "Separator",
]


def build_plan(ctx):
    project = ctx.get("project", {})
    name = project.get("project_name", "App")
    pages = ctx.get("pages", [])

    files = list(BASE_FILES)
    files += ["%s/%s" % (name, p) for p in SOURCES]
    files += [
        "%s/Resources/Assets.xcassets/%s.colorset/Contents.json" % (name, c)
        for c in RESOURCE_COLORSETS
    ]

    for page in pages:
        feature = page.get("page_name", "page")
        # 首屏沿用模板内置的 Home，其余页面按 page 生成
        if feature in ("home", "index"):
            continue
        view = page.get("view_class", "PageView")
        vm = page.get("viewmodel_class", "PageViewModel")
        base = "%s/Features/%s/" % (name, feature)
        files.append(base + view + ".swift")
        files.append(base + vm + ".swift")
        if page.get("layout") == "list":
            files.append(base + "Components/%sCard.swift" % page.get("data_model", "Item"))

    files.append("Tests/MockDataTests.swift")
    return name, files


def main():
    if len(sys.argv) < 2:
        print("用法: python preview_plan.py <proto_context.json>")
        return 1

    path = Path(sys.argv[1])
    if not path.exists():
        print("错误：文件不存在 %s" % path)
        return 2

    ctx = json.loads(path.read_text(encoding="utf-8"))
    project = ctx.get("project", {})
    pages = ctx.get("pages", [])
    name, plan = build_plan(ctx)

    print("工程名（模块）：%s" % name)
    print("应用显示名：%s" % project.get("app_title", ""))
    print("Bundle ID：%s" % project.get("bundle_id", ""))
    print("最低 iOS：%s" % project.get("ios_min", ""))
    print("主色：#%s" % ctx.get("design", {}).get("primary_color", ""))
    print("页面数：%d" % len(pages))
    print("计划文件数：%d" % len(plan))
    print()

    print("页面清单：")
    for p in pages:
        print("  - %-14s %-10s view=%s  vm=%s" % (
            p.get("page_name", ""),
            p.get("layout", ""),
            p.get("view_class", ""),
            p.get("viewmodel_class", ""),
        ))
        if p.get("components"):
            print("      组件 %s" % ", ".join(p["components"]))
        if p.get("data_fields"):
            print("      字段 %s" % ", ".join(p["data_fields"]))
    print()

    caps = ctx.get("capabilities", {})
    enabled = [k for k, v in caps.items() if v is True]
    if enabled:
        print("启用能力：%s" % ", ".join(enabled))
        print()

    print("计划生成文件：")
    for f in plan:
        print("  - %s" % f)

    diag = ctx.get("diagnostics", {})
    if diag.get("need_confirm"):
        print()
        print("待确认项：")
        for n in diag["need_confirm"]:
            print("  - %s" % n)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
