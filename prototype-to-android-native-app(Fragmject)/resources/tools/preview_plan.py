#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""根据 proto_context.json 预览将要生成的 Android 工程文件计划。

用法：
    python preview_plan.py <proto_context.json>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BASE_FILES = [
    "settings.gradle.kts",
    "build.gradle.kts",
    "gradle.properties",
    "gradle/libs.versions.toml",
    "gradle/wrapper/gradle-wrapper.properties",
    "local.properties.example",
    ".gitignore",
    "README.md",
    "app/build.gradle.kts",
    "app/proguard-rules.pro",
    "app/src/main/AndroidManifest.xml",
    "app/src/main/res/values/strings.xml",
    "app/src/main/res/values/themes.xml",
]

CORE_FILES = [
    "App.kt",
    "MainActivity.kt",
    "core/common/ResultExt.kt",
    "core/config/AppConfig.kt",
    "core/datastore/TokenStore.kt",
    "core/designsystem/theme/Color.kt",
    "core/designsystem/theme/Type.kt",
    "core/designsystem/theme/Theme.kt",
    "core/designsystem/theme/Dimens.kt",
    "core/designsystem/component/AppTopBar.kt",
    "core/designsystem/component/StateViews.kt",
    "core/navigation/Routes.kt",
    "core/navigation/AppNavHost.kt",
]

DATA_FILES = [
    "data/model/Item.kt",
    "data/remote/ItemApi.kt",
    "data/remote/dto/ApiResponse.kt",
    "data/remote/dto/ItemDto.kt",
    "data/local/AppDatabase.kt",
    "data/local/dao/ItemDao.kt",
    "data/local/entity/ItemEntity.kt",
    "data/mock/MockData.kt",
    "data/repository/ItemRepository.kt",
]


def to_pascal(name):
    """kebab / snake -> PascalCase"""
    return "".join(part[:1].upper() + part[1:] for part in name.replace("_", "-").split("-") if part)


def build_plan(ctx):
    project = ctx.get("project", {})
    pages = ctx.get("pages", [])
    package_path = project.get("package_name", "com.example.app").replace(".", "/")
    root = "app/src/main/java/%s/" % package_path

    files = list(BASE_FILES)
    files += [root + f for f in CORE_FILES]
    files += [root + f for f in DATA_FILES]
    files += [
        root + "di/NetworkModule.kt",
        root + "di/DatabaseModule.kt",
        root + "di/RepositoryModule.kt",
        root + "feature/root/RootViewModel.kt",
        root + "feature/root/SplashScreen.kt",
    ]

    for page in pages:
        feature = page.get("page_name", "page")
        screen = page.get("screen_class") or (to_pascal(feature) + "Screen")
        viewmodel = page.get("viewmodel_class") or (to_pascal(feature) + "ViewModel")
        state_base = viewmodel[:-len("ViewModel")] if viewmodel.endswith("ViewModel") else viewmodel
        files.append(root + "feature/%s/%s.kt" % (feature, screen))
        files.append(root + "feature/%s/%s.kt" % (feature, viewmodel))
        files.append(root + "feature/%s/%sUiState.kt" % (feature, state_base))
        if page.get("layout") == "list":
            files.append(root + "feature/%s/components/ItemCard.kt" % feature)

    files.append("app/src/test/java/%s/MockDataTest.kt" % package_path)
    return package_path, files


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
    package_path, plan = build_plan(ctx)

    print("工程名：%s" % project.get("project_name", ""))
    print("应用标题：%s" % project.get("app_title", ""))
    print("包名：%s（目录：%s）" % (project.get("package_name", ""), package_path))
    print("minSdk / targetSdk：%s / %s" % (project.get("min_sdk", ""), project.get("target_sdk", "")))
    print("主色：#%s" % ctx.get("design", {}).get("primary_color", ""))
    print("页面数：%d" % len(pages))
    print("计划文件数：%d" % len(plan))
    print()

    print("页面清单：")
    for p in pages:
        print("  - %-14s %-10s route=%s  screen=%s" % (
            p.get("page_name", ""),
            p.get("layout", ""),
            p.get("route", ""),
            p.get("screen_class", ""),
        ))
        if p.get("components"):
            print("      组件 %s" % ", ".join(p["components"]))
        if p.get("data_fields"):
            print("      字段 %s" % ", ".join(p["data_fields"]))
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
