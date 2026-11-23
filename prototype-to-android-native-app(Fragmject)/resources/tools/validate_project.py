#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""校验生成的 Android 工程是否符合本技能约定。

用法：
    python validate_project.py <工程目录>
    python validate_project.py <工程目录> --json

只做**静态**检查，不需要 Android SDK / Gradle / 网络。
退出码：0 = 无阻断性错误；1 = 有 error；2 = 参数或路径错误。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SKIP_DIRS = {"build", ".gradle", ".git", ".idea", ".kotlin", "captures"}

# 检查项名称（顺序即为输出顺序）
CHECKS = [
    "settings.gradle.kts 声明 :app 模块",
    "版本目录包含核心依赖",
    "namespace 与 applicationId 一致且已替换占位符",
    "Manifest 只声明一个 Activity",
    "Application 类使用 @HiltAndroidApp",
    "MainActivity 使用 @AndroidEntryPoint 且 setContent",
    "未使用 XML 页面布局",
    "未混用 View 体系（RecyclerView / Fragment）",
    "路由常量与 NavHost 注册一一对应",
    "每个页面有配套 ViewModel 与 UiState",
    "ViewModel 不依赖 Compose 与 Api",
    "页面未直接访问网络层",
    "Room 数据库与 DAO 存在",
    "mock 数据不少于 10 条",
    "列表页具备三态渲染",
    "主题集中且页面无硬编码颜色",
    "字符串资源有效",
    "存在单元测试",
    "包声明与包名一致",
    "构建脚本含 mock 开关与 KSP",
    "无未替换的占位符",
]

ERROR, WARN, OK = "error", "warn", "ok"


# ---------------------------------------------------------------- 基础工具
def read(path):
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:  # noqa: BLE001
        return ""


def walk_files(root, suffixes=None):
    result = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if suffixes and p.suffix.lower() not in suffixes:
            continue
        result.append(p)
    return result


def read_gradle_namespace(root):
    gradle = root / "app" / "build.gradle.kts"
    if not gradle.exists():
        return None
    m = re.search(r'namespace\s*=\s*"([^"]+)"', read(gradle))
    return m.group(1) if m else None


def read_application_id(root):
    gradle = root / "app" / "build.gradle.kts"
    if not gradle.exists():
        return None
    m = re.search(r'applicationId\s*=\s*"([^"]+)"', read(gradle))
    return m.group(1) if m else None


def package_dir(root):
    ns = read_gradle_namespace(root)
    if not ns:
        return None
    candidate = root / "app" / "src" / "main" / "java" / Path(*ns.split("."))
    if candidate.exists():
        return candidate
    # 包名被改过但目录未改的情况，用于给出更明确的错误
    java_root = root / "app" / "src" / "main" / "java"
    if java_root.exists():
        for p in java_root.iterdir():
            if p.is_dir():
                return p
    return None


# ---------------------------------------------------------------- 各检查项
def check_gradle_settings(root, results):
    settings = root / "settings.gradle.kts"
    if not settings.exists():
        results.append((CHECKS[0], ERROR, "未找到 settings.gradle.kts"))
        return
    text = read(settings)
    if 'include(":app")' not in text:
        results.append((CHECKS[0], ERROR, 'settings.gradle.kts 缺少 include(":app")'))
    else:
        results.append((CHECKS[0], OK, ":app 已声明"))


def check_catalog(root, results):
    catalog = root / "gradle" / "libs.versions.toml"
    if not catalog.exists():
        results.append((CHECKS[1], ERROR, "未找到 gradle/libs.versions.toml"))
        return
    text = read(catalog)
    required = {
        "compose-bom": "Compose BOM",
        "material3": "Material3",
        "hilt-android": "Hilt",
        "room-runtime": "Room",
        "retrofit": "Retrofit",
        "coil-compose": "Coil",
        "navigation-compose": "Navigation",
    }
    missing = [label for key, label in required.items() if key not in text]
    if missing:
        results.append((CHECKS[1], ERROR, "缺少依赖：%s" % "、".join(missing)))
    else:
        results.append((CHECKS[1], OK, "核心依赖齐全"))


def check_namespace(root, results):
    ns = read_gradle_namespace(root)
    app_id = read_application_id(root)
    if not ns:
        results.append((CHECKS[2], ERROR, "app/build.gradle.kts 未声明 namespace"))
        return
    if "{{" in ns:
        results.append((CHECKS[2], ERROR, "namespace 占位符未替换：%s" % ns))
        return
    if app_id != ns:
        results.append((CHECKS[2], ERROR, "namespace(%s) 与 applicationId(%s) 不一致" % (ns, app_id)))
        return
    if not re.match(r"^[a-z][a-z0-9]*(\.[a-z][a-z0-9_]*)+$", ns):
        results.append((CHECKS[2], ERROR, "包名不合法：%s" % ns))
        return
    results.append((CHECKS[2], OK, ns))


def check_manifest(root, results):
    manifest = root / "app" / "src" / "main" / "AndroidManifest.xml"
    if not manifest.exists():
        results.append((CHECKS[3], ERROR, "未找到 AndroidManifest.xml"))
        return
    text = read(manifest)
    activities = re.findall(r"<activity\b[^>]*android:name=\"([^\"]+)\"", text)
    if len(activities) != 1:
        results.append((CHECKS[3], ERROR, "声明了 %d 个 Activity（应为 1）：%s" % (len(activities), activities)))
        return
    if not activities[0].endswith("MainActivity"):
        results.append((CHECKS[3], WARN, "Activity 不是 MainActivity：%s" % activities[0]))
        return
    if "android.permission.INTERNET" not in text:
        results.append((CHECKS[3], ERROR, "缺少 INTERNET 权限"))
        return
    results.append((CHECKS[3], OK, "只有 MainActivity"))


def check_app_class(root, results):
    manifest = root / "app" / "src" / "main" / "AndroidManifest.xml"
    text = read(manifest) if manifest.exists() else ""
    # 只在 <application ...> 标签内找 android:name，避免误匹配权限声明
    app_tag_match = re.search(r"<application\b[^>]*>", text)
    app_name = ""
    if app_tag_match:
        m = re.search(r'android:name="([^"]+)"', app_tag_match.group(0))
        app_name = m.group(1) if m else ""
    if not app_name:
        results.append((CHECKS[4], ERROR, "Manifest 的 <application> 未声明 android:name"))
        return

    pkg_root = package_dir(root)
    if not pkg_root:
        results.append((CHECKS[4], ERROR, "找不到源码目录"))
        return

    simple = app_name.lstrip(".").split(".")[-1]
    candidates = list(pkg_root.rglob("%s.kt" % simple))
    if not candidates:
        results.append((CHECKS[4], ERROR, "Manifest 指向的 Application 类不存在：%s.kt" % simple))
        return
    if "@HiltAndroidApp" not in read(candidates[0]):
        results.append((CHECKS[4], ERROR, "%s.kt 缺少 @HiltAndroidApp" % simple))
        return
    results.append((CHECKS[4], OK, simple))


def check_main_activity(root, results):
    pkg_root = package_dir(root)
    if not pkg_root:
        results.append((CHECKS[5], ERROR, "找不到源码目录"))
        return
    target = pkg_root / "MainActivity.kt"
    if not target.exists():
        results.append((CHECKS[5], ERROR, "未找到 MainActivity.kt"))
        return
    text = read(target)
    problems = []
    if "@AndroidEntryPoint" not in text:
        problems.append("缺少 @AndroidEntryPoint")
    if "setContent" not in text:
        problems.append("缺少 setContent")
    if "ComponentActivity" not in text:
        problems.append("未继承 ComponentActivity")
    if problems:
        results.append((CHECKS[5], ERROR, "；".join(problems)))
    else:
        results.append((CHECKS[5], OK, "单 Activity + Compose"))


def check_no_xml_layout(root, results):
    layout_dir = root / "app" / "src" / "main" / "res" / "layout"
    xmls = list(layout_dir.glob("*.xml")) if layout_dir.exists() else []
    if xmls:
        results.append((CHECKS[6], ERROR, "存在 XML 布局：%s" % ", ".join(p.name for p in xmls[:5])))
    else:
        results.append((CHECKS[6], OK, "全 Compose"))


def check_no_view_system(root, results):
    hits = []
    for p in walk_files(root / "app" / "src", {".kt", ".java"}):
        text = read(p)
        for kw in ("RecyclerView", "androidx.fragment", "findViewById("):
            if kw in text:
                hits.append("%s(%s)" % (p.name, kw))
                break
    if hits:
        results.append((CHECKS[7], ERROR, "混用 View 体系：%s" % ", ".join(hits[:5])))
    else:
        results.append((CHECKS[7], OK, "纯 Compose"))


def check_routes(root, results):
    pkg_root = package_dir(root)
    if not pkg_root:
        results.append((CHECKS[8], ERROR, "找不到源码目录"))
        return
    routes_file = pkg_root / "core" / "navigation" / "Routes.kt"
    nav_file = pkg_root / "core" / "navigation" / "AppNavHost.kt"
    if not routes_file.exists() or not nav_file.exists():
        results.append((CHECKS[8], ERROR, "缺少 Routes.kt 或 AppNavHost.kt"))
        return

    consts = re.findall(r'const val (\w+)\s*=\s*"([^"]*)"', read(routes_file))
    # 参数名不是路由，跳过
    route_consts = [(n, v) for n, v in consts if not n.startswith("ARG_")]
    nav_text = read(nav_file)
    missing = [n for n, _ in route_consts if ("Routes.%s" % n) not in nav_text]
    if missing:
        results.append((CHECKS[8], ERROR, "以下路由未在 AppNavHost 注册：%s" % ", ".join(missing)))
        return

    # NavHost 中的 composable 数量应覆盖所有路由常量
    composables = len(re.findall(r"\bcomposable\s*\(", nav_text))
    if composables < len(route_consts):
        results.append((CHECKS[8], WARN, "composable 数量(%d) 少于路由常量(%d)" % (composables, len(route_consts))))
        return
    results.append((CHECKS[8], OK, "%d 条路由均已注册" % len(route_consts)))


def check_screen_vm(root, results):
    pkg_root = package_dir(root)
    if not pkg_root:
        results.append((CHECKS[9], ERROR, "找不到源码目录"))
        return

    screens = [p for p in walk_files(pkg_root / "feature", {".kt"}) if p.name.endswith("Screen.kt")]
    if not screens:
        results.append((CHECKS[9], ERROR, "feature 下没有任何 *Screen.kt"))
        return

    problems = []
    checked = 0
    for screen in screens:
        base = screen.name[: -len("Screen.kt")]
        # 启动页等纯展示页允许没有 ViewModel
        if base in ("Splash", "Guide"):
            continue
        checked += 1
        if not (screen.parent / ("%sViewModel.kt" % base)).exists():
            problems.append("%s 缺少 %sViewModel.kt" % (screen.parent.name, base))
        if not (screen.parent / ("%sUiState.kt" % base)).exists():
            problems.append("%s 缺少 %sUiState.kt" % (screen.parent.name, base))
    if problems:
        results.append((CHECKS[9], ERROR, "；".join(problems)))
    else:
        results.append((CHECKS[9], OK, "%d 个页面配套完整" % checked))


def check_vm_layering(root, results):
    pkg_root = package_dir(root)
    if not pkg_root:
        results.append((CHECKS[10], ERROR, "找不到源码目录"))
        return
    problems = []
    for p in walk_files(pkg_root / "feature", {".kt"}):
        if not p.name.endswith("ViewModel.kt"):
            continue
        text = read(p)
        if "androidx.compose" in text:
            problems.append("%s 引入 Compose" % p.name)
        if re.search(r"import\s+\S+\.data\.remote\.", text):
            problems.append("%s 直接引用 remote 层" % p.name)
        if "import android.content.Context" in text:
            problems.append("%s 持有 Context" % p.name)
    if problems:
        results.append((CHECKS[10], ERROR, "；".join(problems)))
    else:
        results.append((CHECKS[10], OK, "ViewModel 只依赖 Repository"))


def check_screen_no_api(root, results):
    pkg_root = package_dir(root)
    if not pkg_root:
        results.append((CHECKS[11], ERROR, "找不到源码目录"))
        return
    problems = []
    for p in walk_files(pkg_root / "feature", {".kt"}):
        if not p.name.endswith("Screen.kt"):
            continue
        text = read(p)
        if re.search(r"import\s+\S+\.data\.remote\.", text) or "Retrofit" in text or "OkHttpClient" in text:
            problems.append(p.name)
    if problems:
        results.append((CHECKS[11], ERROR, "页面直接访问网络层：%s" % ", ".join(problems)))
    else:
        results.append((CHECKS[11], OK, "页面只走 ViewModel"))


def check_room(root, results):
    pkg_root = package_dir(root)
    if not pkg_root:
        results.append((CHECKS[12], ERROR, "找不到源码目录"))
        return
    db_files = list(walk_files(pkg_root / "data" / "local", {".kt"}))
    if not db_files:
        results.append((CHECKS[12], ERROR, "缺少 data/local 目录"))
        return
    has_db = any("@Database" in read(p) for p in db_files)
    has_dao = any("@Dao" in read(p) for p in db_files)
    has_entity = any("@Entity" in read(p) for p in db_files)
    if not (has_db and has_dao and has_entity):
        missing = []
        if not has_db:
            missing.append("@Database")
        if not has_dao:
            missing.append("@Dao")
        if not has_entity:
            missing.append("@Entity")
        results.append((CHECKS[12], ERROR, "Room 定义不完整，缺少：%s" % ", ".join(missing)))
    else:
        results.append((CHECKS[12], OK, "Database / DAO / Entity 齐全"))


def check_mock(root, results):
    pkg_root = package_dir(root)
    if not pkg_root:
        results.append((CHECKS[13], ERROR, "找不到源码目录"))
        return
    mock_dir = pkg_root / "data" / "mock"
    files = list(mock_dir.glob("*.kt")) if mock_dir.exists() else []
    if not files:
        results.append((CHECKS[13], ERROR, "缺少 data/mock"))
        return
    text = "\n".join(read(p) for p in files)
    count = 0
    m = re.search(r"List\(\s*(\d+)\s*\)", text)
    if m:
        count = int(m.group(1))
    else:
        count = text.count("id =")
    if count < 10:
        results.append((CHECKS[13], ERROR, "mock 条目可能不足 10 条（检测到 %d）" % count))
    else:
        results.append((CHECKS[13], OK, "约 %d 条 mock 数据" % count))


def check_states(root, results):
    pkg_root = package_dir(root)
    if not pkg_root:
        results.append((CHECKS[14], ERROR, "找不到源码目录"))
        return
    # 找列表页：ViewModel 中有 LoadMore 事件的页面
    list_screens = []
    for p in walk_files(pkg_root / "feature", {".kt"}):
        if p.name.endswith("ViewModel.kt") and "LoadMore" in read(p):
            screen = p.parent / (p.name.replace("ViewModel.kt", "Screen.kt"))
            if screen.exists():
                list_screens.append(screen)
    if not list_screens:
        results.append((CHECKS[14], WARN, "未识别到列表页（无 LoadMore 事件）"))
        return
    problems = []
    for screen in list_screens:
        text = read(screen)
        for kw, label in (("LoadingView", "loading"), ("EmptyView", "empty"), ("ErrorView", "error")):
            if kw not in text:
                problems.append("%s 缺少 %s 态" % (screen.parent.name, label))
    if problems:
        results.append((CHECKS[14], ERROR, "；".join(problems)))
    else:
        results.append((CHECKS[14], OK, "%d 个列表页三态齐全" % len(list_screens)))


def check_theme(root, results):
    pkg_root = package_dir(root)
    if not pkg_root:
        results.append((CHECKS[15], ERROR, "找不到源码目录"))
        return
    theme_dir = pkg_root / "core" / "designsystem" / "theme"
    if not theme_dir.exists():
        results.append((CHECKS[15], ERROR, "缺少 core/designsystem/theme"))
        return
    theme_text = "\n".join(read(p) for p in theme_dir.glob("*.kt"))
    if "MaterialTheme" not in theme_text and "lightColorScheme" not in theme_text:
        results.append((CHECKS[15], WARN, "theme 目录未见 colorScheme 定义"))
        return
    hard_coded = []
    for p in walk_files(pkg_root / "feature", {".kt"}):
        if re.search(r"Color\(0x[0-9A-Fa-f]{8}\)", read(p)):
            hard_coded.append(p.name)
    if hard_coded:
        results.append((CHECKS[15], ERROR, "页面硬编码颜色：%s" % ", ".join(hard_coded)))
    else:
        results.append((CHECKS[15], OK, "颜色仅存在于 theme"))


def check_strings(root, results):
    strings = root / "app" / "src" / "main" / "res" / "values" / "strings.xml"
    if not strings.exists():
        results.append((CHECKS[16], ERROR, "未找到 res/values/strings.xml"))
        return
    text = read(strings)
    m = re.search(r'<string name="app_name">([^<]*)</string>', text)
    if not m:
        results.append((CHECKS[16], ERROR, "strings.xml 缺少 app_name"))
        return
    value = m.group(1).strip()
    if not value or "{{" in value:
        results.append((CHECKS[16], ERROR, "app_name 为空或未替换：%s" % value))
        return
    results.append((CHECKS[16], OK, "app_name = %s" % value))


def check_test(root, results):
    test_dir = root / "app" / "src" / "test"
    files = list(test_dir.rglob("*.kt")) if test_dir.exists() else []
    if not files:
        results.append((CHECKS[17], ERROR, "app/src/test 下没有测试文件"))
        return
    if not any("@Test" in read(p) for p in files):
        results.append((CHECKS[17], WARN, "测试文件里没有 @Test"))
        return
    results.append((CHECKS[17], OK, "%d 个测试文件" % len(files)))


def check_package_decl(root, results):
    ns = read_gradle_namespace(root)
    pkg_root = package_dir(root)
    if not ns or not pkg_root:
        results.append((CHECKS[18], ERROR, "无法确定包名或源码目录"))
        return
    problems = []
    for p in walk_files(pkg_root, {".kt"}):
        m = re.search(r"^\s*package\s+([\w.]+)", read(p), re.M)
        if not m:
            problems.append("%s 缺少 package 声明" % p.name)
            continue
        pkg = m.group(1)
        if pkg != ns and not pkg.startswith(ns + "."):
            problems.append("%s 的 package(%s) 与 namespace 不一致" % (p.name, pkg))
    if problems:
        results.append((CHECKS[18], ERROR, "；".join(problems[:5])))
    else:
        results.append((CHECKS[18], OK, "全部与 %s 对齐" % ns))


def check_build_flags(root, results):
    gradle = root / "app" / "build.gradle.kts"
    if not gradle.exists():
        results.append((CHECKS[19], ERROR, "未找到 app/build.gradle.kts"))
        return
    text = read(gradle)
    problems = []
    if "USE_MOCK" not in text:
        problems.append("缺少 USE_MOCK buildConfigField")
    if "BASE_URL" not in text:
        problems.append("缺少 BASE_URL buildConfigField")
    if "ksp(" not in text:
        problems.append("未使用 ksp")
    if "kapt(" in text or "kotlin-kapt" in text:
        problems.append("使用了 kapt")
    if problems:
        results.append((CHECKS[19], ERROR, "；".join(problems)))
    else:
        results.append((CHECKS[19], OK, "mock 开关 + KSP"))


def check_placeholders(root, results):
    suffixes = {".kt", ".kts", ".xml", ".toml", ".properties", ".md", ".pro", ".json"}
    leftovers = []
    for p in walk_files(root, suffixes):
        if "{{" in read(p):
            leftovers.append(str(p.relative_to(root)))
    if leftovers:
        results.append((CHECKS[20], ERROR, "占位符未替换：%s" % ", ".join(leftovers[:8])))
    else:
        results.append((CHECKS[20], OK, "无残留占位符"))


# ---------------------------------------------------------------- 主流程
def run(root):
    results = []
    check_gradle_settings(root, results)
    check_catalog(root, results)
    check_namespace(root, results)
    check_manifest(root, results)
    check_app_class(root, results)
    check_main_activity(root, results)
    check_no_xml_layout(root, results)
    check_no_view_system(root, results)
    check_routes(root, results)
    check_screen_vm(root, results)
    check_vm_layering(root, results)
    check_screen_no_api(root, results)
    check_room(root, results)
    check_mock(root, results)
    check_states(root, results)
    check_theme(root, results)
    check_strings(root, results)
    check_test(root, results)
    check_package_decl(root, results)
    check_build_flags(root, results)
    check_placeholders(root, results)
    return results


def main():
    if len(sys.argv) < 2:
        print("用法: python validate_project.py <工程目录> [--json]")
        return 2

    root = Path(sys.argv[1]).resolve()
    as_json = "--json" in sys.argv[2:]

    if not root.exists() or not root.is_dir():
        print("错误：目录不存在 %s" % root)
        return 2

    results = run(root)
    errors = [r for r in results if r[1] == ERROR]
    warnings = [r for r in results if r[1] == WARN]

    if as_json:
        print(json.dumps(
            {
                "root": str(root),
                "total": len(results),
                "errors": len(errors),
                "warnings": len(warnings),
                "items": [
                    {"check": c, "level": lv, "detail": d} for c, lv, d in results
                ],
            },
            ensure_ascii=False,
            indent=2,
        ))
    else:
        icons = {OK: "OK  ", WARN: "WARN", ERROR: "ERR "}
        print("工程：%s" % root)
        print("-" * 78)
        for check, level, detail in results:
            print("[%s] %-42s %s" % (icons[level], check, detail))
        print("-" * 78)
        print("共 %d 项：错误 %d 项，警告 %d 项" % (len(results), len(errors), len(warnings)))
        if errors:
            print("结论：未通过，请修复上述 ERR 项后重试。")
        elif warnings:
            print("结论：通过（有警告，建议复核）。")
        else:
            print("结论：全部通过。")

    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
