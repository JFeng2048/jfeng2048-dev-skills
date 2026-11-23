#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""用 proto_context.json 把 templates/project_structure 渲染成真实工程。

用法：
    python render_template.py <proto_context.json> <输出目录> [--force]

做的事：
    1. 复制 templates/project_structure；
    2. 把目录名里的 {{package_path}} 换成 com/example/xxx；
    3. 把文件内容里的占位符全部替换；
    4. 输出替换统计，便于自查。

注意：本脚本只负责“套模板”，页面内容仍需按原型生成。
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "project_structure"

# 需要替换内容的文件后缀
TEXT_SUFFIXES = {
    ".kt", ".kts", ".xml", ".toml", ".properties", ".pro",
    ".md", ".json", ".gitignore", ".example", ".cfg",
}


def build_mapping(ctx):
    project = ctx.get("project", {})
    design = ctx.get("design", {})
    package = project.get("package_name", "")
    if not package:
        raise SystemExit("错误：proto_context.json 缺少 project.package_name")

    color = str(design.get("primary_color", "2B6DE5")).lstrip("#").upper()
    return {
        "{{project_name}}": str(project.get("project_name", "android-app")),
        "{{app_name}}": str(project.get("app_title", "Android App")),
        "{{package_name}}": package,
        "{{package_path}}": package.replace(".", "/"),
        "{{primary_color_hex}}": color,
        "{{min_sdk}}": str(project.get("min_sdk", 24)),
        "{{compile_sdk}}": str(project.get("compile_sdk", 35)),
        "{{target_sdk}}": str(project.get("target_sdk", 35)),
    }


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

    out_dir = Path(args.output)
    if out_dir.exists():
        if not args.force:
            print("错误：输出目录已存在（加 --force 覆盖）：%s" % out_dir)
            return 2
        shutil.rmtree(out_dir)

    ctx = json.loads(context_path.read_text(encoding="utf-8"))
    mapping = build_mapping(ctx)

    shutil.copytree(TEMPLATE_DIR, out_dir)
    renamed = rename_entries(out_dir, mapping)
    expanded = expand_package_path_dirs(out_dir, mapping["{{package_path}}"])
    files, replaced = replace_content(out_dir, mapping)

    leftovers = []
    for path in out_dir.rglob("*"):
        if path.is_file() and is_text_file(path) and "{{" in path.read_text(encoding="utf-8", errors="ignore"):
            leftovers.append(str(path.relative_to(out_dir)))

    print(json.dumps(
        {
            "output": str(out_dir),
            "template": str(TEMPLATE_DIR),
            "package_name": mapping["{{package_name}}"],
            "package_path": mapping["{{package_path}}"],
            "renamed_entries": renamed,
            "expanded_package_dirs": expanded,
            "text_files": files,
            "replaced_files": replaced,
            "leftover_placeholders": leftovers,
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0 if not leftovers else 1


if __name__ == "__main__":
    raise SystemExit(main())
