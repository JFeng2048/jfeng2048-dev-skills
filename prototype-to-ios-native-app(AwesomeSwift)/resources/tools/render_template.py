#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""用 proto_context.json 把 templates/project_structure 渲染成真实 iOS 工程。

用法：
    python render_template.py <proto_context.json> <输出目录> [--force]

做的事：
    1. 复制 templates/project_structure；
    2. 目录名里的 {{project_name}} 替换成真实工程名；
    3. 文件内容里的占位符全部替换（含主色拆分出的 RGB）；
    4. 输出替换统计与残留占位符。

注意：只负责「套模板」，页面内容仍需按原型生成。
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "project_structure"

TEXT_SUFFIXES = {
    ".swift", ".yml", ".yaml", ".xcconfig", ".plist", ".json",
    ".strings", ".md", ".pro", ".pbxproj", ".xcscheme",
}


def normalize_color(raw, default="2B6DE5"):
    """把 #2B6DE5 / 2b6de5 归一化成 6 位大写 hex"""
    color = str(raw or "").lstrip("#").strip().upper()
    if len(color) == 8:  # 兼容 AARRGGBB
        color = color[2:]
    if len(color) != 6 or any(c not in "0123456789ABCDEF" for c in color):
        return default
    return color


def build_mapping(ctx):
    project = ctx.get("project", {})
    design = ctx.get("design", {})

    name = project.get("project_name", "")
    bundle_id = project.get("bundle_id", "")
    if not name or not bundle_id:
        raise SystemExit("错误：proto_context.json 缺少 project.project_name 或 project.bundle_id")

    color = normalize_color(design.get("primary_color"))
    prefix = project.get("bundle_id_prefix") or ".".join(bundle_id.split(".")[:-1])

    return {
        "{{project_name}}": name,
        "{{app_name}}": str(project.get("app_title", "iOS App")),
        "{{bundle_id}}": bundle_id,
        "{{bundle_id_prefix}}": prefix,
        "{{ios_min}}": str(project.get("ios_min", "17.0")),
        "{{primary_r}}": color[0:2],
        "{{primary_g}}": color[2:4],
        "{{primary_b}}": color[4:6],
    }


def is_text_file(path):
    name = path.name
    if name in (".gitignore",):
        return True
    return path.suffix.lower() in TEXT_SUFFIXES


def rename_entries(root, mapping):
    """自底向上重命名目录 / 文件名中的占位符（不含路径分隔符的值）"""
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
            path.rename(path.with_name(new_name))
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
    parser = argparse.ArgumentParser(description="渲染 iOS 模板为真实工程")
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
    files, replaced = replace_content(out_dir, mapping)

    leftovers = []
    for path in out_dir.rglob("*"):
        if path.is_file() and is_text_file(path) and "{{" in path.read_text(encoding="utf-8", errors="ignore"):
            leftovers.append(str(path.relative_to(out_dir)))

    print(json.dumps(
        {
            "output": str(out_dir),
            "template": str(TEMPLATE_DIR),
            "project_name": mapping["{{project_name}}"],
            "bundle_id": mapping["{{bundle_id}}"],
            "ios_min": mapping["{{ios_min}}"],
            "primary_rgb": [mapping["{{primary_r}}"], mapping["{{primary_g}}"], mapping["{{primary_b}}"]],
            "renamed_entries": renamed,
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
