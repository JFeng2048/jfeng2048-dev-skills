#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""静态检查 Android 多模块工程的结构、依赖方向和组件边界。

用法:
    python validate_project.py <工程目录>
    python validate_project.py <工程目录> --json

不依赖 Android SDK 或网络；静态检查不能替代 Gradle Sync、测试和编译。
退出码: 0 = 无 error；1 = 有 error；2 = 参数或路径错误。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SKIP_DIRS = {"build", ".gradle", ".git", ".idea", ".kotlin", "captures", ".agents", ".codex"}
ERROR, WARN, OK = "error", "warn", "ok"
STABLE_VERSION_RE = re.compile(r"^\d+(?:\.\d+)*(?:-\d+(?:\.\d+)*)?$")
REQUIRED_VERSION_KEYS_TEMPLATE = {
    "agp", "kotlin", "ksp", "hilt", "compileSdk", "targetSdk", "minSdk", "jdk",
    "composeBom", "coreKtx", "lifecycle", "activityCompose", "navigation", "room",
    "datastore", "okhttp", "coroutines", "junit",
}
REQUIRED_VERSION_KEYS_BASE = {
    "agp", "kotlin", "composeBom", "coreKtx", "lifecycle", "activityCompose",
}


def read(path):
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def walk_files(root, suffixes=None):
    if not root.exists():
        return []
    return [
        path for path in root.rglob("*")
        if path.is_file()
        and not any(part in SKIP_DIRS for part in path.parts)
        and (suffixes is None or path.suffix.lower() in suffixes)
    ]


def module_path(root, module):
    if module == ":":
        return root
    return root.joinpath(*module.lstrip(":").split(":"))


def declared_modules(root):
    text = read(root / "settings.gradle.kts")
    modules = set()
    for block in re.findall(r"\binclude\s*\((.*?)\)", text, re.S):
        modules.update(re.findall(r'["\'](:[^"\']+)["\']', block))
    for single in re.findall(r'\binclude\s*["\'](:[^"\']+)["\']', text):
        modules.add(single)
    return modules, text


def project_dependencies(gradle_file):
    return set(re.findall(r'project\(\s*["\'](:[^"\']+)["\']\s*\)', read(gradle_file)))


def add(results, name, level, detail):
    results.append((name, level, detail))


def check_settings(root, results):
    name = "settings 声明 app、core、feature（及可选 service）modules"
    modules, text = declared_modules(root)
    missing = []
    if ":app" not in modules:
        missing.append(":app")
    for required in (":core:common", ":core:designsystem"):
        if required not in modules:
            missing.append(required)
    if not re.search(r'includeBuild\(\s*["\']build-logic["\']\s*\)', text):
        missing.append("included build-logic")
    split_domains = sorted({
        module.split(":")[2]
        for module in modules
        if re.fullmatch(r":feature:[^:]+:api", module)
    })
    flat_domains = sorted({
        module.split(":")[2]
        for module in modules
        if re.fullmatch(r":feature:[^:]+", module)
    })
    for domain in split_domains:
        for suffix in ("api", "impl"):
            expected = ":feature:%s:%s" % (domain, suffix)
            if expected not in modules:
                missing.append(expected)
    if not split_domains and not flat_domains:
        missing.append("at least one :feature:<domain> or :feature:<domain>:api")
    service_modules = sorted(m for m in modules if re.fullmatch(r":service:[^:]+", m))
    if missing:
        add(results, name, ERROR, "缺少声明：" + "、".join(missing))
    else:
        total_domains = len(set(split_domains) | set(flat_domains))
        mode = "api/impl" if split_domains and not flat_domains else ("标准单层" if flat_domains and not split_domains else "混合")
        add(
            results,
            name,
            OK,
            "%s 模式：%d 个 feature domain，%d 个 service，%d 个 Gradle modules"
            % (mode, total_domains, len(service_modules), len(modules)),
        )


def check_build_logic(root, results):
    name = "build-logic convention plugins 存在"
    build_logic_dir = root / "build-logic"
    if not build_logic_dir.is_dir():
        add(results, name, ERROR, "缺少 build-logic 目录")
        return
    if not (build_logic_dir / "settings.gradle.kts").is_file():
        add(results, name, ERROR, "缺少 build-logic/settings.gradle.kts")
        return
    precompiled = list((build_logic_dir / "src").rglob("*.gradle.kts")) if (build_logic_dir / "src").is_dir() else []
    convention_plugins = list((build_logic_dir / "convention" / "src").rglob("*ConventionPlugin.kt")) if (build_logic_dir / "convention" / "src").is_dir() else []
    if precompiled:
        required = [
            "build-logic/build.gradle.kts",
            "build-logic/src/main/kotlin/android.application.gradle.kts",
            "build-logic/src/main/kotlin/android.library.gradle.kts",
            "build-logic/src/main/kotlin/android.compose-library.gradle.kts",
            "build-logic/src/main/kotlin/kotlin.library.gradle.kts",
        ]
        missing = [item for item in required if not (root / item).is_file()]
        if missing:
            add(results, name, ERROR, "缺少：" + "、".join(missing))
        else:
            add(results, name, OK, "included build 与预编译 convention plugins 齐全")
    elif convention_plugins and (build_logic_dir / "convention" / "build.gradle.kts").is_file():
        add(results, name, OK, "included build 与 %d 个 ConventionPlugin 类齐全" % len(convention_plugins))
    else:
        add(results, name, ERROR, "未发现有效的 convention plugins（需 src/main/kotlin/*.gradle.kts 或 convention/*ConventionPlugin.kt）")


def check_catalog(root, results):
    name = "根 version catalog 完整且版本已解析"
    catalog = root / "gradle" / "libs.versions.toml"
    if not catalog.is_file():
        add(results, name, ERROR, "未找到 gradle/libs.versions.toml")
        return
    text = read(catalog)
    required_aliases = [
        "androidx-compose-bom",
        "androidx-navigation-compose",
        "androidx-core-ktx",
    ]
    missing = [alias for alias in required_aliases if alias not in text]
    if "android-gradle-plugin" not in text and "android-gradlePlugin" not in text:
        missing.append("android-gradle-plugin/android-gradlePlugin")
    if "kotlin-gradle-plugin" not in text and "kotlin-gradlePlugin" not in text:
        missing.append("kotlin-gradle-plugin/kotlin-gradlePlugin")
    unresolved = "{{" in text
    versions_block = re.search(r"(?ms)^\[versions\]\s*(.*?)(?=^\[|\Z)", text)
    version_entries = dict(
        re.findall(r'(?m)^\s*([\w.-]+)\s*=\s*"([^"]+)"', versions_block.group(1))
    ) if versions_block else {}
    is_full_template = "hilt" in version_entries and "room" in version_entries
    required_keys = REQUIRED_VERSION_KEYS_TEMPLATE if is_full_template else REQUIRED_VERSION_KEYS_BASE
    missing_versions = sorted(required_keys - version_entries.keys())
    invalid_versions = sorted(
        key for key in version_entries
        if not STABLE_VERSION_RE.fullmatch(version_entries[key])
    )
    sdk_order_invalid = False
    if all(k in version_entries for k in ("minSdk", "targetSdk", "compileSdk")):
        try:
            sdk_order_invalid = not (0 < int(version_entries["minSdk"]) <= int(version_entries["targetSdk"]) <= int(version_entries["compileSdk"]))
        except ValueError:
            sdk_order_invalid = True
    core_ktx_has_version = re.search(
        r'(?m)^\s*androidx-core-ktx\s*=\s*\{[^}]*version\.ref\s*=\s*"coreKtx"',
        text,
    )
    if missing or unresolved or missing_versions or invalid_versions or sdk_order_invalid or not core_ktx_has_version:
        problems = []
        if missing:
            problems.append("缺少别名 " + ", ".join(missing))
        if unresolved:
            problems.append("存在未替换占位符")
        if missing_versions:
            problems.append("缺少具体版本：" + ", ".join(missing_versions))
        if invalid_versions:
            problems.append("版本不是稳定的具体版本：" + ", ".join(invalid_versions))
        if sdk_order_invalid:
            problems.append("SDK 需满足 0 < minSdk <= targetSdk <= compileSdk")
        if not core_ktx_has_version:
            problems.append("androidx-core-ktx 缺少 coreKtx 版本引用")
        add(results, name, ERROR, "；".join(problems))
    elif re.search(r'(?m)^\[versions\]', text):
        add(results, name, OK, "版本集中管理，未发现占位符或动态 selector")
    else:
        add(results, name, ERROR, "缺少 [versions] 表")


def check_module_build_files(root, results):
    name = "settings 中每个 module 都有 build.gradle.kts"
    modules, _ = declared_modules(root)
    missing = []
    for module in sorted(modules):
        path = module_path(root, module) / "build.gradle.kts"
        if not path.is_file():
            missing.append(module)
    if missing:
        add(results, name, ERROR, "缺少：" + "、".join(missing))
    else:
        add(results, name, OK, "%d 个 modules 均有构建脚本" % len(modules))


def check_dependency_boundaries(root, results):
    name = "模块依赖方向无反向边"
    modules, _ = declared_modules(root)
    problems = []
    graph = {}
    for module in sorted(modules):
        gradle_file = module_path(root, module) / "build.gradle.kts"
        dependencies = project_dependencies(gradle_file)
        graph[module] = dependencies & modules
        for dependency in dependencies:
            if dependency not in modules:
                problems.append("%s 引用了未声明模块 %s" % (module, dependency))
            if module.startswith(":core:") and (dependency.startswith(":feature:") or dependency.startswith(":service:")):
                problems.append("%s -> %s（core 不得依赖 feature 或 service）" % (module, dependency))
            if module.startswith(":service:") and (dependency.startswith(":feature:") or dependency == ":app"):
                problems.append("%s -> %s（service 不得依赖 feature 或 app）" % (module, dependency))
            if re.fullmatch(r":feature:[^:]+", module) and dependency.startswith(":feature:") and dependency != module:
                problems.append("%s -> %s（标准模式下 feature 不得互相依赖）" % (module, dependency))
            current = re.fullmatch(r":feature:([^:]+):(api|impl)", module)
            target = re.fullmatch(r":feature:([^:]+):(api|impl)", dependency)
            if current and target:
                if current.group(2) == "api" and target.group(2) == "impl":
                    problems.append("%s -> %s（API 不得依赖实现）" % (module, dependency))
                if current.group(2) == "impl" and target.group(2) == "impl" and current.group(1) != target.group(1):
                    problems.append("%s -> %s（feature impl 不得依赖其他 impl）" % (module, dependency))
            if module != ":app" and dependency == ":app":
                problems.append("%s -> :app（业务/core 不得依赖宿主壳）" % module)

    visited = set()
    visiting = []

    def visit(module):
        if module in visiting:
            cycle_start = visiting.index(module)
            cycle = visiting[cycle_start:] + [module]
            problems.append("模块依赖环：" + " -> ".join(cycle))
            return
        if module in visited:
            return
        visiting.append(module)
        for dependency in sorted(graph.get(module, set())):
            visit(dependency)
        visiting.pop()
        visited.add(module)

    for module in sorted(graph):
        visit(module)

    domains = sorted({
        match.group(1)
        for module in modules
        if (match := re.fullmatch(r":feature:([^:]+):api", module))
    })
    for domain in domains:
        impl = ":feature:%s:impl" % domain
        api = ":feature:%s:api" % domain
        if impl not in modules:
            continue
        if api not in project_dependencies(module_path(root, impl) / "build.gradle.kts"):
            problems.append("%s 未依赖自身 API" % impl)
        if impl not in project_dependencies(root / "app" / "build.gradle.kts"):
            problems.append(":app 未装配 %s" % impl)
    flat_features = sorted(m for m in modules if re.fullmatch(r":feature:[^:]+", m))
    app_deps = project_dependencies(root / "app" / "build.gradle.kts")
    for feat in flat_features:
        if feat not in app_deps:
            problems.append(":app 未装配 %s" % feat)

    if problems:
        add(results, name, ERROR, "；".join(problems[:12]))
    else:
        add(results, name, OK, "app / feature / core / service 依赖边界通过")


def check_app_identity(root, results):
    name = "app namespace、applicationId 与 Application 类有效"
    gradle = read(root / "app" / "build.gradle.kts")
    manifest = read(root / "app" / "src" / "main" / "AndroidManifest.xml")
    namespace = re.search(r'namespace\s*=\s*["\']([^"\']+)["\']', gradle)
    app_id = re.search(r'applicationId\s*=\s*["\']([^"\']+)["\']', gradle)
    app_class = re.search(r'<application\b[^>]*android:name=["\']([^"\']+)["\']', manifest, re.S)
    if not namespace or not app_id or not app_class:
        add(results, name, ERROR, "缺 namespace、applicationId 或 Manifest application android:name")
        return
    if "{{" in namespace.group(1) + app_id.group(1) + app_class.group(1):
        add(results, name, ERROR, "存在未替换占位符")
        return
    if not re.fullmatch(r"[a-z][a-z0-9]*(?:\.[a-z][a-z0-9_]*)+", app_id.group(1)):
        add(results, name, ERROR, "applicationId 不合法：" + app_id.group(1))
        return
    raw_app_name = app_class.group(1)
    simple_app_name = raw_app_name.rsplit(".", 1)[-1]
    app_source = root / "app" / "src" / "main"
    source_files = walk_files(app_source, {".kt", ".java"})
    application_declared = any(
        re.search(r"\bclass\s+" + re.escape(simple_app_name) + r"\b", read(path))
        and "Application" in read(path)
        for path in source_files
    )
    if not application_declared:
        add(results, name, ERROR, "未找到 Manifest 声明的 Application 类：" + raw_app_name)
    elif app_id.group(1) == namespace.group(1):
        add(results, name, OK, app_id.group(1))
    else:
        add(results, name, OK, "applicationId 与 app namespace 分离：" + app_id.group(1))


def check_manifest_components(root, results):
    name = "Manifest 组件显式设置 exported"
    manifests = walk_files(root, {".xml"})
    components = []
    has_launcher_activity = False
    for path in manifests:
        if path.name != "AndroidManifest.xml":
            continue
        text = read(path)
        if "android.intent.action.MAIN" in text and "android.intent.category.LAUNCHER" in text:
            has_launcher_activity = True
        for tag, attrs in re.findall(r"<(activity|activity-alias|service|receiver|provider)\b([^>]*)>", text, re.S):
            component_name = re.search(r'android:name\s*=\s*["\']([^"\']+)["\']', attrs)
            exported = re.search(r'android:exported\s*=\s*["\'](true|false)["\']', attrs)
            if component_name and not exported:
                components.append("%s:%s 缺 android:exported" % (path.relative_to(root), component_name.group(1)))
    if not has_launcher_activity:
        components.append("未声明 LAUNCHER Activity")
    if components:
        add(results, name, ERROR, "；".join(components[:10]))
    else:
        add(results, name, OK, "组件导出属性显式声明；不强制单 Activity")


def check_feature_api(root, results):
    name = "feature api 不泄漏实现"
    modules, _ = declared_modules(root)
    problems = []
    for module in sorted(modules):
        if not re.fullmatch(r":feature:[^:]+:api", module):
            continue
        src = module_path(root, module) / "src"
        for path in walk_files(src, {".kt", ".java"}):
            text = read(path)
            if path.name.endswith("Screen.kt") or "@Composable" in text:
                problems.append("%s 包含 UI" % path.relative_to(root))
            if "RepositoryImpl" in text or re.search(r"\bclass\s+\w+Repository\b", text):
                problems.append("%s 包含 Repository 实现" % path.relative_to(root))
    if problems:
        add(results, name, ERROR, "；".join(problems[:10]))
    else:
        add(results, name, OK, "API module 仅承载跨模块契约")


def check_app_shell(root, results):
    name = "app 不直接引用 feature impl 实现包"
    problems = []
    for path in walk_files(root / "app" / "src", {".kt", ".java"}):
        if re.search(r"import\s+[\w.]+\.feature\.[\w.]+\.impl\.", read(path)):
            problems.append(str(path.relative_to(root)))
    if problems:
        add(results, name, ERROR, "宿主源码直接引用实现类：" + "、".join(problems[:8]))
    else:
        add(results, name, OK, "宿主通过 feature entry 契约装配")


def check_package_namespaces(root, results):
    name = "Android module package 与 namespace 一致"
    modules, _ = declared_modules(root)
    problems = []
    checked = 0
    for module in sorted(modules):
        module_root = module_path(root, module)
        gradle = read(module_root / "build.gradle.kts")
        match = re.search(r'namespace\s*=\s*["\']([^"\']+)["\']', gradle)
        if not match:
            continue
        namespace = match.group(1)
        if "{{" in namespace:
            problems.append("%s namespace 有占位符" % module)
            continue
        for path in walk_files(module_root / "src", {".kt", ".java"}):
            package_match = re.search(r"^\s*package\s+([\w.]+)", read(path), re.M)
            if not package_match:
                problems.append("%s 缺 package 声明" % path.relative_to(root))
            elif package_match.group(1) != namespace and not package_match.group(1).startswith(namespace + "."):
                problems.append("%s package 超出 namespace %s" % (path.relative_to(root), namespace))
            checked += 1
    if problems:
        add(results, name, ERROR, "；".join(problems[:10]))
    else:
        add(results, name, OK, "检查 %d 个 Android module 源文件" % checked)


def check_screen_state(root, results):
    name = "业务页面具备 ViewModel 与 UiState"
    modules, _ = declared_modules(root)
    problems = []
    checked = 0
    for module in sorted(modules):
        if not (re.fullmatch(r":feature:[^:]+:impl", module) or re.fullmatch(r":feature:[^:]+", module)):
            continue
        src = module_path(root, module) / "src" / "main"
        screens = [p for p in walk_files(src, {".kt"}) if p.name.endswith("Screen.kt")]
        for screen in screens:
            if screen.name == "FeatureHomeScreen.kt":
                continue
            checked += 1
            base = screen.name[:-len("Screen.kt")]
            all_kt = walk_files(src, {".kt"})
            all_text = "\n".join(read(p) for p in all_kt)
            peers = {p.name for p in all_kt}
            if base + "ViewModel.kt" not in peers and base + "ViewModel" not in all_text:
                problems.append("%s 缺少 ViewModel" % screen.relative_to(root))
            if base + "UiState.kt" not in peers and base + "UiState" not in all_text:
                problems.append("%s 缺少 UiState" % screen.relative_to(root))
    if problems:
        add(results, name, ERROR, "；".join(problems[:12]))
    elif checked == 0:
        add(results, name, WARN, "模板占位页面除外，尚未发现业务 Screen")
    else:
        add(results, name, OK, "检查 %d 个业务页面" % checked)


def check_startup_graph(root, results):
    name = "startup module 定义任务图边界"
    modules, _ = declared_modules(root)
    startup_module = root / "core" / "startup"
    if ":core:startup" not in modules and not startup_module.is_dir():
        add(results, name, OK, "未使用 :core:startup（跳过任务图校验）")
        return
    sources = walk_files(startup_module / "src", {".kt"})
    text = "\n".join(read(path) for path in sources)
    if not sources:
        add(results, name, ERROR, "缺少 :core:startup 源码")
    elif "dependencies" not in text or "StartupTaskGraph" not in text:
        add(results, name, ERROR, "缺少任务依赖图定义")
    elif "cycle" not in text.lower():
        add(results, name, WARN, "未发现依赖环校验逻辑")
    else:
        add(results, name, OK, "存在任务 DAG 与依赖环检查")


def check_tests(root, results):
    name = "存在 app 与 feature 测试"
    modules, _ = declared_modules(root)
    app_tests = walk_files(root / "app" / "src" / "test", {".kt", ".java"})
    feature_tests = []
    core_tests = []
    for module in modules:
        if re.fullmatch(r":feature:[^:]+:impl", module) or re.fullmatch(r":feature:[^:]+", module):
            feature_tests.extend(walk_files(module_path(root, module) / "src" / "test", {".kt", ".java"}))
        elif module.startswith(":core:"):
            core_tests.extend(walk_files(module_path(root, module) / "src" / "test", {".kt", ".java"}))
    no_test_annotation = [
        path for path in app_tests + feature_tests + core_tests
        if "@Test" not in read(path)
    ]
    if not app_tests or not feature_tests:
        missing = []
        if not app_tests:
            missing.append("app")
        if not feature_tests:
            missing.append("feature")
        level = WARN if core_tests else ERROR
        add(results, name, level, "缺少测试：" + "、".join(missing))
    elif no_test_annotation:
        add(results, name, WARN, "部分测试源码未检测到 @Test")
    else:
        add(results, name, OK, "%d 个测试源码文件" % (len(app_tests) + len(feature_tests)))


def check_placeholders(root, results):
    name = "工程无未替换模板占位符"
    text_suffixes = {".kt", ".kts", ".xml", ".toml", ".properties", ".md", ".pro", ".json"}
    leftovers = [
        str(path.relative_to(root))
        for path in walk_files(root, text_suffixes)
        if "{{" in read(path)
    ]
    if leftovers:
        add(results, name, ERROR, "仍有占位符：" + "、".join(leftovers[:12]))
    else:
        add(results, name, OK, "无未替换占位符")


def run(root):
    results = []
    check_settings(root, results)
    check_build_logic(root, results)
    check_catalog(root, results)
    check_module_build_files(root, results)
    check_dependency_boundaries(root, results)
    check_app_identity(root, results)
    check_manifest_components(root, results)
    check_feature_api(root, results)
    check_app_shell(root, results)
    check_package_namespaces(root, results)
    check_screen_state(root, results)
    check_startup_graph(root, results)
    check_tests(root, results)
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
    errors = [item for item in results if item[1] == ERROR]
    warnings = [item for item in results if item[1] == WARN]
    if as_json:
        print(json.dumps({
            "root": str(root),
            "total": len(results),
            "errors": len(errors),
            "warnings": len(warnings),
            "items": [
                {"check": check, "level": level, "detail": detail}
                for check, level, detail in results
            ],
        }, ensure_ascii=False, indent=2))
    else:
        labels = {OK: "OK  ", WARN: "WARN", ERROR: "ERR "}
        print("工程：%s" % root)
        print("-" * 92)
        for check, level, detail in results:
            print("[%s] %-42s %s" % (labels[level], check, detail))
        print("-" * 92)
        print("共 %d 项：错误 %d 项，警告 %d 项" % (len(results), len(errors), len(warnings)))
        if errors:
            print("结论：未通过，请修复 ERR 项后重试。")
        elif warnings:
            print("结论：通过（有警告，建议复核）。")
        else:
            print("结论：全部通过。")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
