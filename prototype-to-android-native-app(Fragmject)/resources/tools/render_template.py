#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""用 proto_context.json 把 modular_project_structure 渲染成多模块工程。

用法：
    python render_template.py <proto_context.json> <输出目录> [--force]

做的事：
    1. 复制 templates/modular_project_structure；
    2. 把目录名里的 {{package_path}} 换成 com/example/xxx；
    3. 把文件内容里的占位符全部替换；
    4. 输出替换统计，便于自查。

注意：本脚本只负责“套模板”，页面内容仍需按原型生成。
"""

from __future__ import annotations

import argparse
from datetime import date
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "modular_project_structure"

# 需要替换内容的文件后缀
TEXT_SUFFIXES = {
    ".kt", ".kts", ".xml", ".toml", ".properties", ".pro",
    ".md", ".json", ".gitignore", ".example", ".cfg",
}

VERSION_TOKENS = {
    "{{agp_version}}": "agp",
    "{{gradle_version}}": "gradle",
    "{{kotlin_version}}": "kotlin",
    "{{ksp_version}}": "ksp",
    "{{compose_bom_version}}": "compose_bom",
    "{{core_ktx_version}}": "core_ktx",
    "{{lifecycle_version}}": "lifecycle",
    "{{activity_compose_version}}": "activity_compose",
    "{{navigation_version}}": "navigation",
    "{{hilt_version}}": "hilt",
    "{{room_version}}": "room",
    "{{datastore_version}}": "datastore",
    "{{okhttp_version}}": "okhttp",
    "{{coroutines_version}}": "coroutines",
    "{{junit_version}}": "junit",
}

STABLE_VERSION_RE = re.compile(r"^\d+(?:\.\d+)*(?:-\d+(?:\.\d+)*)?$")


def normalize_features(ctx):
    features = ctx.get("features") or []
    pages = ctx.get("pages", [])
    if not features:
        domains = sorted({page.get("domain", "main") for page in pages})
        features = [{"domain": domain, "pages": []} for domain in domains or ["main"]]

    by_domain = {}
    for feature in features:
        domain = feature.get("domain")
        if not domain:
            continue
        by_domain[domain] = dict(feature)
        by_domain[domain]["pages"] = list(feature.get("pages", []))
    for page in pages:
        domain = page.get("domain", "main")
        feature = by_domain.setdefault(domain, {"domain": domain, "pages": []})
        page_name = page.get("page_name")
        if page_name and page_name not in feature["pages"]:
            feature["pages"].append(page_name)
    if not by_domain:
        raise SystemExit("错误：proto_context.json 至少需要一个 features[].domain 或 pages[].domain")
    return list(by_domain.values())


def build_mapping(ctx):
    project = ctx.get("project", {})
    design = ctx.get("design", {})
    package = project.get("package_name", "")
    if not package:
        raise SystemExit("错误：proto_context.json 缺少 project.package_name")

    sdk = {
        "min_sdk": project.get("min_sdk"),
        "compile_sdk": project.get("compile_sdk"),
        "target_sdk": project.get("target_sdk"),
        "jdk": project.get("jdk"),
    }
    missing_sdk = [key for key, value in sdk.items() if value is None]
    if missing_sdk:
        raise SystemExit("错误：生成前需确定 project.%s" % ", project.".join(missing_sdk))
    try:
        min_sdk = int(sdk["min_sdk"])
        target_sdk = int(sdk["target_sdk"])
        compile_sdk = int(sdk["compile_sdk"])
        jdk = int(sdk["jdk"])
    except (TypeError, ValueError):
        raise SystemExit("错误：min_sdk、target_sdk、compile_sdk 与 jdk 必须是正整数")
    if not (0 < min_sdk <= target_sdk <= compile_sdk):
        raise SystemExit("错误：SDK 需满足 0 < min_sdk <= target_sdk <= compile_sdk")
    if jdk <= 0:
        raise SystemExit("错误：project.jdk 必须是正整数")

    versions = project.get("versions") or {}
    if not isinstance(versions, dict):
        raise SystemExit("错误：project.versions 必须是版本名到具体版本的对象")
    missing_versions = [key for key in VERSION_TOKENS.values() if not versions.get(key)]
    if missing_versions:
        raise SystemExit(
            "错误：project.versions 缺少已核实的版本：%s；请在生成时解析最新稳定兼容版本后再渲染"
            % ", ".join(sorted(set(missing_versions)))
        )
    invalid_versions = []
    for key in VERSION_TOKENS.values():
        value = str(versions[key]).strip()
        if not STABLE_VERSION_RE.fullmatch(value):
            invalid_versions.append(key)
    if invalid_versions:
        raise SystemExit(
            "错误：版本必须是已解析的稳定具体版本，不能使用占位符、预发布版或动态 selector：%s"
            % ", ".join(sorted(set(invalid_versions)))
        )

    resolution = project.get("version_resolution") or {}
    if not isinstance(resolution, dict):
        raise SystemExit("错误：project.version_resolution 必须是对象")
    if resolution.get("selection") != "latest-stable-compatible":
        raise SystemExit(
            "错误：project.version_resolution.selection 必须为 latest-stable-compatible"
        )
    if resolution.get("compatibility_verified") is not True:
        raise SystemExit("错误：必须确认工具链与依赖版本兼容后才能渲染")
    checked_at_text = str(resolution.get("checked_at", ""))
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", checked_at_text):
        raise SystemExit("错误：version_resolution.checked_at 必须是 YYYY-MM-DD 日期")
    try:
        checked_at = date.fromisoformat(checked_at_text)
    except ValueError:
        raise SystemExit("错误：version_resolution.checked_at 必须是 YYYY-MM-DD 日期")
    if checked_at != date.today():
        raise SystemExit(
            "错误：版本核验日期不是今天，请重新查询当前发布信息后再生成"
        )
    sources = resolution.get("sources")
    if not isinstance(sources, list) or not sources or any(
        not isinstance(source, str)
        or urlparse(source).scheme != "https"
        or not urlparse(source).netloc
        for source in sources
    ):
        raise SystemExit("错误：version_resolution.sources 必须列出 HTTPS 官方来源 URL")

    color = str(design.get("primary_color", "2B6DE5")).lstrip("#").upper()
    features = normalize_features(ctx)
    invalid_domains = [
        feature["domain"] for feature in features
        if not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", feature["domain"])
    ]
    if invalid_domains:
        raise SystemExit("错误：feature domain 必须是小写 kebab-case：%s" % ", ".join(invalid_domains))
    mapping = {
        "{{project_name}}": str(project.get("project_name", "android-app")),
        "{{app_name}}": str(project.get("app_title", "Android App")),
        "{{package_name}}": package,
        "{{package_path}}": package.replace(".", "/"),
        "{{primary_color_hex}}": color,
        "{{min_sdk}}": str(min_sdk),
        "{{compile_sdk}}": str(compile_sdk),
        "{{target_sdk}}": str(target_sdk),
        "{{jdk_version}}": str(jdk),
        "{{versions_checked_at}}": checked_at.isoformat(),
        "{{versions_sources}}": "; ".join(source.strip() for source in sources),
        "{{feature_module_includes}}": "\n".join(
            'include(":feature:%s:api", ":feature:%s:impl")' % (f["domain"], f["domain"])
            for f in features
        ),
        "{{feature_impl_dependencies}}": "\n".join(
            '    implementation(project(":feature:%s:impl"))' % f["domain"]
            for f in features
        ),
    }
    for token, key in VERSION_TOKENS.items():
        mapping[token] = str(versions[key])
    return mapping, features


def is_text_file(path):
    name = path.name
    if name in (".gitignore", "gradle.properties", "local.properties.example"):
        return True
    return path.suffix.lower() in TEXT_SUFFIXES


def expand_package_path_dirs(root, package_path):
    """把名为 {{package_path}} 的目录展开成 com/example/xxx 多级目录"""
    parts = package_path.split("/")
    expanded = 0
    # 自底向上，避免父目录改名后子路径失效
    for path in sorted(root.rglob("{{package_path}}"), key=lambda p: len(p.parts), reverse=True):
        if not path.is_dir():
            continue
        target = path.parent
        for part in parts:
            target = target / part
        target.mkdir(parents=True, exist_ok=True)
        for child in list(path.iterdir()):
            shutil.move(str(child), str(target / child.name))
        path.rmdir()
        expanded += 1
    return expanded


def rename_entries(root, mapping):
    """重命名文件名里的占位符（不含路径分隔符的情况）"""
    renamed = 0
    for path in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if "{{" not in path.name:
            continue
        new_name = path.name
        for key, value in mapping.items():
            if "/" in value or "\\" in value:
                continue
            new_name = new_name.replace(key, value)
        if new_name != path.name:
            target = path.with_name(new_name)
            path.rename(target)
            renamed += 1
    return renamed


def expand_feature_templates(root, features, ctx):
    source = root / "feature" / "{{domain}}"
    if not source.exists():
        return 0
    expanded = 0
    pages = ctx.get("pages", [])
    start_route = ctx.get("navigation", {}).get("start_destination", "")
    default_page = next((page for page in pages if page.get("route") == start_route), None)
    if default_page is None:
        default_page = next((page for page in pages if page.get("is_home")), None)
    default_domain = (
        default_page.get("domain", "main")
        if default_page
        else features[0]["domain"]
    )
    for feature in features:
        domain = feature["domain"]
        target = source.parent / domain
        if target.exists():
            raise SystemExit("错误：feature 模板目标已存在：%s" % target)
        shutil.copytree(source, target)
        domain_pages = [
            page for page in pages
            if page.get("domain", "main") == domain
        ]
        start_page = (
            next((page for page in domain_pages if page.get("route") == start_route), None)
            or next((page for page in domain_pages if page.get("is_home")), None)
            or (domain_pages[0] if domain_pages else {})
        )
        is_default = domain == default_domain
        page_route = str(start_page.get("route") or "home").lstrip("/")
        namespaced_route = page_route if page_route.startswith(domain + "/") else "%s/%s" % (domain, page_route)
        feature_title = str(start_page.get("screen_class", domain))
        if feature_title.endswith("Screen"):
            feature_title = feature_title[:-len("Screen")]
        feature_mapping = {
            "{{domain}}": domain,
            "{{domain_pascal}}": "".join(
                part[:1].upper() + part[1:] for part in domain.replace("_", "-").split("-") if part
            ),
            "{{domain_route}}": namespaced_route,
            "{{feature_is_default}}": str(is_default).lower(),
            "{{feature_page_title}}": feature_title,
        }
        rename_entries(target, feature_mapping)
        replace_content(target, feature_mapping)
        expanded += 1
    shutil.rmtree(source)
    return expanded


def replace_content(root, mapping):
    files = 0
    replaced = 0
    for path in root.rglob("*"):
        if not path.is_file() or not is_text_file(path):
            continue
        files += 1
        text = path.read_text(encoding="utf-8", errors="ignore")
        new_text = text
        for key, value in mapping.items():
            if key in new_text:
                new_text = new_text.replace(key, value)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            replaced += 1
    return files, replaced


def main():
    parser = argparse.ArgumentParser(description="渲染 Android 模板为真实工程")
    parser.add_argument("context", help="proto_context.json 路径")
    parser.add_argument("output", help="输出目录")
    parser.add_argument("--force", action="store_true", help="输出目录存在时覆盖")
    args = parser.parse_args()

    context_path = Path(args.context)
    if not context_path.exists():
        print("错误：文件不存在 %s" % context_path)
        return 2
    if not TEMPLATE_DIR.exists():
        print("错误：模板目录不存在 %s" % TEMPLATE_DIR)
        return 2

    requested_output = Path(args.output)
    if requested_output.is_symlink():
        print("错误：输出路径不能是符号链接")
        return 2
    out_dir = requested_output.resolve()
    template_root = TEMPLATE_DIR.resolve()
    if out_dir == template_root or template_root in out_dir.parents or out_dir in template_root.parents:
        print("错误：输出目录不能覆盖模板目录或其父目录")
        return 2
    resolved_context = context_path.resolve()
    if resolved_context == out_dir or out_dir in resolved_context.parents:
        print("错误：proto_context.json 不能位于将被替换的输出目录中")
        return 2
    if out_dir.exists():
        if not args.force:
            print("错误：输出目录已存在（加 --force 覆盖）：%s" % out_dir)
            return 2
        if not out_dir.is_dir():
            print("错误：输出路径已存在但不是目录：%s" % out_dir)
            return 2

    try:
        ctx = json.loads(context_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        print("错误：proto_context.json 格式无效：%s" % error)
        return 2
    mapping, features = build_mapping(ctx)

    out_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".%s-staging-" % out_dir.name,
        dir=out_dir.parent,
    ) as temp_dir:
        staged_project = Path(temp_dir) / "project"
        shutil.copytree(TEMPLATE_DIR, staged_project)
        expanded_features = expand_feature_templates(staged_project, features, ctx)
        renamed = rename_entries(staged_project, mapping)
        expanded = expand_package_path_dirs(staged_project, mapping["{{package_path}}"])
        files, replaced = replace_content(staged_project, mapping)

        leftovers = []
        for path in staged_project.rglob("*"):
            if (
                path.is_file()
                and is_text_file(path)
                and "{{" in path.read_text(encoding="utf-8", errors="ignore")
            ):
                leftovers.append(str(path.relative_to(staged_project)))
        if leftovers:
            print("错误：模板仍有未替换占位符：" + "、".join(leftovers[:12]))
            return 1

        if out_dir.exists():
            shutil.rmtree(out_dir)
        shutil.move(str(staged_project), str(out_dir))

    print(json.dumps(
        {
            "output": str(out_dir),
            "template": str(TEMPLATE_DIR),
            "package_name": mapping["{{package_name}}"],
            "package_path": mapping["{{package_path}}"],
            "features": [feature["domain"] for feature in features],
            "expanded_feature_templates": expanded_features,
            "renamed_entries": renamed,
            "expanded_package_dirs": expanded,
            "text_files": files,
            "replaced_files": replaced,
            "leftover_placeholders": leftovers,
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
