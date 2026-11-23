#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""校验生成的 iOS 工程是否符合本技能约定。

用法：
    python validate_project.py <工程目录>
    python validate_project.py <工程目录> --json

只做**静态**检查，不需要 macOS / Xcode / XcodeGen。
退出码：0 = 无阻断性错误；1 = 有 error；2 = 参数或路径错误。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SKIP_DIRS = {"build", "DerivedData", ".build", ".git", "xcuserdata", "Pods", ".swiftpm"}

CHECKS = [
    "project.yml 存在且工程名合法",
    "最低 iOS 版本不低于 17.0",
    "SPM 依赖包含 Alamofire 与 Kingfisher",
    "App Target / 测试 Target / Scheme 齐全",
    "全工程只有一个 @main",
    "应用入口注入 ModelContainer 与组合根",
    "Info.plist 关键键齐全",
    "Debug / Release 环境配置正确",
    "NavigationStack 路由覆盖 AppRoute",
    "Feature 视图与 ViewModel 配对",
    "View 未直接访问网络层",
    "ViewModel 不依赖 SwiftUI / 网络 / 图片库",
    "Repository 协议与默认实现齐备",
    "@Model 与缓存回落存在",
    "mock 数据不少于 10 条",
    "列表页具备三态渲染",
    "颜色只来自 Asset",
    "中英文本地化 key 一致",
    "存在单元测试",
    "Bundle ID 一致且非占位",
    "未使用 Storyboard / XIB / UIViewController",
    "无未替换的占位符",
]

ERROR, WARN, OK = "error", "warn", "ok"


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


def project_spec(root):
    return read(root / "project.yml") if (root / "project.yml").exists() else ""


def project_name(root):
    m = re.search(r"^name:\s*(\S+)", project_spec(root), re.M)
    return m.group(1).strip("\"'") if m else None


def app_bundle_id(root):
    m = re.search(r"PRODUCT_BUNDLE_IDENTIFIER:\s*(\S+)", project_spec(root))
    return m.group(1).strip("\"'") if m else None


def sources_dir(root):
    name = project_name(root)
    if name:
        candidate = root / name
        if candidate.is_dir():
            return candidate
    for p in root.iterdir():
        if p.is_dir() and (p / "App" / "AppEntry.swift").exists():
            return p
    return None


# ---------------------------------------------------------------- 各检查项
def check_project_name(root, results):
    spec = root / "project.yml"
    if not spec.exists():
        results.append((CHECKS[0], ERROR, "未找到 project.yml"))
        return
    text = read(spec)
    name = project_name(root)
    if not name or "{{" in name:
        results.append((CHECKS[0], ERROR, "project.yml 未声明合法 name"))
        return
    if not re.match(r"^[A-Z][A-Za-z0-9]{2,}$", name):
        results.append((CHECKS[0], ERROR, "工程名不是 PascalCase：%s" % name))
        return
    if not (root / name).is_dir():
        results.append((CHECKS[0], ERROR, "源码目录 %s/ 不存在（目录名必须等于工程名）" % name))
        return
    results.append((CHECKS[0], OK, name))


def check_deployment(root, results):
    text = project_spec(root)
    m = re.search(r"deploymentTarget:\s*[\r\n]+\s*iOS:\s*\"?([\d.]+)\"?", text)
    if not m:
        results.append((CHECKS[1], ERROR, "project.yml 未声明 deploymentTarget.iOS"))
        return
    version = m.group(1)
    try:
        value = float(version)
    except ValueError:
        results.append((CHECKS[1], ERROR, "deploymentTarget 无法解析：%s" % version))
        return
    if value < 17.0:
        results.append((CHECKS[1], ERROR, "iOS %s 低于 17.0，SwiftData 不可用" % version))
        return
    results.append((CHECKS[1], OK, "iOS %s" % version))


def check_packages(root, results):
    text = project_spec(root)
    missing = [name for name in ("Alamofire", "Kingfisher") if ("%s:" % name) not in text]
    if missing:
        results.append((CHECKS[2], ERROR, "缺少 SPM 依赖：%s" % ", ".join(missing)))
        return
    if "packages:" not in text:
        results.append((CHECKS[2], ERROR, "project.yml 缺少 packages 段"))
        return
    results.append((CHECKS[2], OK, "Alamofire + Kingfisher"))


def check_targets(root, results):
    text = project_spec(root)
    name = project_name(root) or ""
    problems = []
    if "targets:" not in text:
        problems.append("缺少 targets 段")
    if "type: application" not in text:
        problems.append("缺少 application target")
    if "bundle.unit-test" not in text:
        problems.append("缺少单元测试 target")
    if "schemes:" not in text or "%sTests" % name not in text:
        problems.append("scheme 未包含测试 target")
    if problems:
        results.append((CHECKS[3], ERROR, "；".join(problems)))
    else:
        results.append((CHECKS[3], OK, "app + tests + scheme"))


def check_single_main(root, results):
    src = sources_dir(root)
    if not src:
        results.append((CHECKS[4], ERROR, "找不到源码目录"))
        return
    mains = [p for p in walk_files(src, {".swift"}) if re.search(r"@main\b", read(p))]
    if len(mains) != 1:
        results.append((CHECKS[4], ERROR, "找到 %d 个 @main（应为 1）" % len(mains)))
        return
    results.append((CHECKS[4], OK, mains[0].name))


def check_app_entry(root, results):
    src = sources_dir(root)
    entry = (src / "App" / "AppEntry.swift") if src else None
    if not entry or not entry.exists():
        results.append((CHECKS[5], ERROR, "未找到 App/AppEntry.swift"))
        return
    text = read(entry)
    problems = []
    if ".modelContainer(" not in text:
        problems.append("未挂载 modelContainer")
    if ".environmentObject(" not in text:
        problems.append("未下发 environmentObject")
    if "AppContainer" not in text:
        problems.append("未创建 AppContainer")
    if problems:
        results.append((CHECKS[5], ERROR, "；".join(problems)))
    else:
        results.append((CHECKS[5], OK, "ModelContainer + AppContainer"))


def check_plist(root, results):
    src = sources_dir(root)
    plist = (src / "Resources" / "Info.plist") if src else None
    if not plist or not plist.exists():
        results.append((CHECKS[6], ERROR, "未找到 Resources/Info.plist"))
        return
    text = read(plist)
    problems = []
    for key in ("API_BASE_URL", "USE_MOCK", "UILaunchScreen"):
        if "<key>%s</key>" % key not in text:
            problems.append("缺少 %s" % key)
    if "$(PRODUCT_BUNDLE_IDENTIFIER)" not in text:
        problems.append("CFBundleIdentifier 未使用 $(PRODUCT_BUNDLE_IDENTIFIER)")
    if problems:
        results.append((CHECKS[6], ERROR, "；".join(problems)))
    else:
        results.append((CHECKS[6], OK, "API_BASE_URL / USE_MOCK / 启动屏"))


def check_xcconfig(root, results):
    problems = []
    spec = project_spec(root)
    if "configFiles:" not in spec:
        problems.append("project.yml 未用 configFiles 声明 xcconfig")
    for name, expect_mock in (("Debug.xcconfig", "YES"), ("Release.xcconfig", "NO")):
        path = root / "Configs" / name
        if not path.exists():
            problems.append("缺少 Configs/%s" % name)
            continue
        text = read(path)
        if "API_BASE_URL" not in text:
            problems.append("%s 缺少 API_BASE_URL" % name)
        if re.search(r"API_BASE_URL\s*=\s*https?://", text):
            problems.append("%s 的 URL 未用 $() 转义 //（会被当注释截断）" % name)
        if "$()" not in text:
            problems.append("%s 未使用 $() 转义" % name)
        if ("USE_MOCK = %s" % expect_mock) not in text:
            problems.append("%s 的 USE_MOCK 应为 %s" % (name, expect_mock))
    if problems:
        results.append((CHECKS[7], ERROR, "；".join(problems)))
    else:
        results.append((CHECKS[7], OK, "Debug=YES / Release=NO"))


def check_routes(root, results):
    src = sources_dir(root)
    if not src:
        results.append((CHECKS[8], ERROR, "找不到源码目录"))
        return
    route_file = src / "Core" / "Router" / "AppRoute.swift"
    root_view = src / "App" / "RootView.swift"
    if not route_file.exists() or not root_view.exists():
        results.append((CHECKS[8], ERROR, "缺少 AppRoute.swift 或 RootView.swift"))
        return

    route_text = read(route_file)
    cases = re.findall(r"^\s*case\s+(\w+)", route_text, re.M)
    root_text = read(root_view)

    if "navigationDestination(for:" not in root_text:
        results.append((CHECKS[8], ERROR, "RootView 未使用 navigationDestination(for:) 分发路由"))
        return

    missing = [c for c in cases if (".%s" % c) not in root_text]
    if missing:
        results.append((CHECKS[8], ERROR, "以下路由未在 RootView 处理：%s" % ", ".join(missing)))
        return
    if "NavigationStack" not in root_text:
        results.append((CHECKS[8], WARN, "RootView 未使用 NavigationStack"))
        return
    results.append((CHECKS[8], OK, "%d 条路由均已处理" % len(cases)))


def check_view_vm(root, results):
    src = sources_dir(root)
    if not src:
        results.append((CHECKS[9], ERROR, "找不到源码目录"))
        return
    views = [p for p in walk_files(src / "Features", {".swift"}) if p.name.endswith("View.swift")]
    if not views:
        results.append((CHECKS[9], ERROR, "Features 下没有 *View.swift"))
        return

    problems = []
    checked = 0
    for view in views:
        base = view.name[: -len("View.swift")]
        if base in ("Splash", "Guide", "Empty"):
            continue
        checked += 1
        if not (view.parent / ("%sViewModel.swift" % base)).exists():
            problems.append("%s 缺少 %sViewModel.swift" % (view.parent.name, base))
    if problems:
        results.append((CHECKS[9], ERROR, "；".join(problems)))
    else:
        results.append((CHECKS[9], OK, "%d 个页面配套完整" % checked))


def check_view_network(root, results):
    src = sources_dir(root)
    if not src:
        results.append((CHECKS[10], ERROR, "找不到源码目录"))
        return
    problems = []
    for p in walk_files(src / "Features", {".swift"}):
        if not p.name.endswith("View.swift") and not p.name.endswith("Card.swift"):
            continue
        text = read(p)
        for kw in ("import Alamofire", "APIClient", "APITarget", "URLSession"):
            if kw in text:
                problems.append("%s 使用了 %s" % (p.name, kw))
                break
    if problems:
        results.append((CHECKS[10], ERROR, "；".join(problems)))
    else:
        results.append((CHECKS[10], OK, "页面只走 ViewModel"))


def check_vm_layering(root, results):
    src = sources_dir(root)
    if not src:
        results.append((CHECKS[11], ERROR, "找不到源码目录"))
        return
    # 只匹配真正的 import 语句行，避免注释里提到模块名被误判
    import_re = re.compile(r"(?m)^\s*import\s+(SwiftUI|UIKit|Kingfisher|Alamofire)\b")
    problems = []
    for p in walk_files(src / "Features", {".swift"}):
        if not p.name.endswith("ViewModel.swift"):
            continue
        m = import_re.search(read(p))
        if m:
            problems.append("%s 引入了 %s" % (p.name, m.group(1)))
    if problems:
        results.append((CHECKS[11], ERROR, "；".join(problems)))
    else:
        results.append((CHECKS[11], OK, "ViewModel 只依赖 Repository"))


def check_repository(root, results):
    src = sources_dir(root)
    if not src:
        results.append((CHECKS[12], ERROR, "找不到源码目录"))
        return
    repo_dir = src / "Data" / "Repositories"
    if not repo_dir.exists():
        results.append((CHECKS[12], ERROR, "缺少 Data/Repositories"))
        return
    text = "\n".join(read(p) for p in repo_dir.glob("*.swift"))
    has_protocol = re.search(r"protocol\s+\w+Repository", text) is not None
    has_impl = re.search(r"final class Default\w+Repository", text) is not None
    if not (has_protocol and has_impl):
        results.append((CHECKS[12], ERROR, "缺少 Repository 协议或 Default 实现"))
        return
    if "APITarget" not in text and "client.request(" not in text:
        results.append((CHECKS[12], WARN, "Repository 未见网络调用（APITarget / client.request）"))
        return
    results.append((CHECKS[12], OK, "协议 + 默认实现"))


def check_swiftdata(root, results):
    src = sources_dir(root)
    if not src:
        results.append((CHECKS[13], ERROR, "找不到源码目录"))
        return
    models = walk_files(src / "Data" / "Models", {".swift"}) if (src / "Data" / "Models").exists() else []
    has_model = any("@Model" in read(p) for p in models)
    repo_text = "\n".join(read(p) for p in walk_files(src / "Data" / "Repositories", {".swift"}))
    has_fallback = "FetchDescriptor" in repo_text
    entry = src / "App" / "AppEntry.swift"
    has_container = entry.exists() and ".modelContainer(" in read(entry)

    problems = []
    if not has_model:
        problems.append("缺少 @Model 模型")
    if not has_container:
        problems.append("AppEntry 未挂载 modelContainer")
    if not has_fallback:
        problems.append("Repository 未实现缓存回落（FetchDescriptor）")
    if problems:
        results.append((CHECKS[13], ERROR, "；".join(problems)))
    else:
        results.append((CHECKS[13], OK, "@Model + 缓存回落"))


def check_mock(root, results):
    src = sources_dir(root)
    mock = (src / "Data" / "Mock" / "MockData.swift") if src else None
    if not mock or not mock.exists():
        results.append((CHECKS[14], ERROR, "缺少 Data/Mock/MockData.swift"))
        return
    text = read(mock)
    count = 0
    m = re.search(r"1\.\.\.(\d+)", text)
    if m:
        count = int(m.group(1))
    else:
        count = text.count("skillID:")
    if count < 10:
        results.append((CHECKS[14], ERROR, "mock 条目可能不足 10 条（检测到 %d）" % count))
    else:
        results.append((CHECKS[14], OK, "约 %d 条 mock 数据" % count))


def check_states(root, results):
    src = sources_dir(root)
    if not src:
        results.append((CHECKS[15], ERROR, "找不到源码目录"))
        return
    list_screens = []
    for p in walk_files(src / "Features", {".swift"}):
        if not p.name.endswith("ViewModel.swift"):
            continue
        if "loadMore" not in read(p):
            continue
        view = p.parent / (p.name.replace("ViewModel.swift", "View.swift"))
        if view.exists():
            list_screens.append(view)

    if not list_screens:
        results.append((CHECKS[15], WARN, "未识别到列表页（无 loadMore）"))
        return

    problems = []
    for view in list_screens:
        text = read(view)
        if "case .empty" not in text:
            problems.append("%s 缺少 empty 态" % view.parent.name)
        if "case .failed" not in text:
            problems.append("%s 缺少 failed 态" % view.parent.name)
        if ".loading" not in text and ".idle" not in text:
            problems.append("%s 缺少 loading 态" % view.parent.name)
    if problems:
        results.append((CHECKS[15], ERROR, "；".join(problems)))
    else:
        results.append((CHECKS[15], OK, "%d 个列表页三态齐全" % len(list_screens)))


def check_colors(root, results):
    src = sources_dir(root)
    if not src:
        results.append((CHECKS[16], ERROR, "找不到源码目录"))
        return
    theme = src / "Core" / "Theme" / "AppTheme.swift"
    if not theme.exists():
        results.append((CHECKS[16], ERROR, "缺少 Core/Theme/AppTheme.swift"))
        return
    if 'Color("BrandPrimary")' not in read(theme):
        results.append((CHECKS[16], WARN, "AppTheme 未引用 BrandPrimary 语义色"))
        return

    colorset = src / "Resources" / "Assets.xcassets" / "BrandPrimary.colorset" / "Contents.json"
    if not colorset.exists():
        results.append((CHECKS[16], ERROR, "Assets 缺少 BrandPrimary.colorset"))
        return

    hard_coded = []
    for folder in (src / "Features", src / "App"):
        if not folder.exists():
            continue
        for p in walk_files(folder, {".swift"}):
            if re.search(r"Color\(\s*(red:|white:|hue:)", read(p)):
                hard_coded.append(p.name)
    if hard_coded:
        results.append((CHECKS[16], ERROR, "页面硬编码颜色：%s" % ", ".join(hard_coded)))
    else:
        results.append((CHECKS[16], OK, "颜色仅来自 Asset"))


def check_localization(root, results):
    src = sources_dir(root)
    if not src:
        results.append((CHECKS[17], ERROR, "找不到源码目录"))
        return
    zh = src / "Resources" / "zh-Hans.lproj" / "Localizable.strings"
    en = src / "Resources" / "en.lproj" / "Localizable.strings"
    problems = []
    if not zh.exists():
        problems.append("缺少 zh-Hans.lproj/Localizable.strings")
    if not en.exists():
        problems.append("缺少 en.lproj/Localizable.strings")
    if problems:
        results.append((CHECKS[17], ERROR, "；".join(problems)))
        return

    def keys(path):
        return set(re.findall(r'^\s*"([^"]+)"\s*=', read(path), re.M))

    zh_keys, en_keys = keys(zh), keys(en)
    if not zh_keys:
        results.append((CHECKS[17], ERROR, "中文 strings 没有有效条目"))
        return
    if zh_keys != en_keys:
        diff = sorted(zh_keys.symmetric_difference(en_keys))[:6]
        results.append((CHECKS[17], ERROR, "两种语言 key 不一致：%s" % ", ".join(diff)))
        return
    results.append((CHECKS[17], OK, "%d 个 key 对齐" % len(zh_keys)))


def check_tests(root, results):
    test_dir = root / "Tests"
    files = list(test_dir.rglob("*.swift")) if test_dir.exists() else []
    if not files:
        results.append((CHECKS[18], ERROR, "Tests/ 下没有测试文件"))
        return
    name = project_name(root) or ""
    text = "\n".join(read(p) for p in files)
    problems = []
    if "XCTestCase" not in text:
        problems.append("没有 XCTestCase")
    if ("@testable import %s" % name) not in text:
        problems.append("缺少 @testable import %s" % name)
    if problems:
        results.append((CHECKS[18], ERROR, "；".join(problems)))
    else:
        results.append((CHECKS[18], OK, "%d 个测试文件" % len(files)))


def check_bundle_id(root, results):
    bundle_id = app_bundle_id(root)
    if not bundle_id:
        results.append((CHECKS[19], ERROR, "project.yml 未声明 PRODUCT_BUNDLE_IDENTIFIER"))
        return
    if "{{" in bundle_id:
        results.append((CHECKS[19], ERROR, "Bundle ID 占位符未替换：%s" % bundle_id))
        return
    if not re.match(r"^[a-z][a-z0-9]*(\.[a-z][a-z0-9-]*)+$", bundle_id):
        results.append((CHECKS[19], ERROR, "Bundle ID 不合法：%s" % bundle_id))
        return
    results.append((CHECKS[19], OK, bundle_id))


def check_no_uikit(root, results):
    src = sources_dir(root)
    if not src:
        results.append((CHECKS[20], ERROR, "找不到源码目录"))
        return
    storyboards = [
        p.name for p in walk_files(root, {".storyboard", ".xib"})
    ]
    if storyboards:
        results.append((CHECKS[20], ERROR, "存在 Storyboard / XIB：%s" % ", ".join(storyboards[:5])))
        return
    uikit = []
    for p in walk_files(src, {".swift"}):
        text = read(p)
        if "UIViewController" in text or "UIHostingController" in text:
            uikit.append(p.name)
    if uikit:
        results.append((CHECKS[20], ERROR, "出现 UIKit 控制器：%s" % ", ".join(uikit)))
    else:
        results.append((CHECKS[20], OK, "纯 SwiftUI"))


def check_placeholders(root, results):
    suffixes = {
        ".swift", ".yml", ".yaml", ".xcconfig", ".plist", ".json",
        ".strings", ".md", ".pbxproj", ".xcscheme", ".gitignore",
    }
    leftovers = []
    for p in walk_files(root, suffixes):
        if "{{" in read(p):
            leftovers.append(str(p.relative_to(root)))
    if leftovers:
        results.append((CHECKS[21], ERROR, "占位符未替换：%s" % ", ".join(leftovers[:8])))
    else:
        results.append((CHECKS[21], OK, "无残留占位符"))


# ---------------------------------------------------------------- 主流程
def run(root):
    results = []
    check_project_name(root, results)
    check_deployment(root, results)
    check_packages(root, results)
    check_targets(root, results)
    check_single_main(root, results)
    check_app_entry(root, results)
    check_plist(root, results)
    check_xcconfig(root, results)
    check_routes(root, results)
    check_view_vm(root, results)
    check_view_network(root, results)
    check_vm_layering(root, results)
    check_repository(root, results)
    check_swiftdata(root, results)
    check_mock(root, results)
    check_states(root, results)
    check_colors(root, results)
    check_localization(root, results)
    check_tests(root, results)
    check_bundle_id(root, results)
    check_no_uikit(root, results)
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
                "items": [{"check": c, "level": lv, "detail": d} for c, lv, d in results],
            },
            ensure_ascii=False,
            indent=2,
        ))
    else:
        icons = {OK: "OK  ", WARN: "WARN", ERROR: "ERR "}
        print("工程：%s" % root)
        print("-" * 78)
        for check, level, detail in results:
            print("[%s] %-40s %s" % (icons[level], check, detail))
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
