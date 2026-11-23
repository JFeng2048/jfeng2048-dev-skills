#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""把 HTML 原型解析为 proto_context.json（Android 原生工程初稿）。

用法：
    python parse_prototype.py <原型.html> --package com.example.skillswap \
        --project skill-swap-android --title "技能互换" --out proto_context.json

说明：
    这是一个**启发式**解析器，只做结构化初稿，不追求完美。
    输出需人工或模型核对，尤其是 diagnostics.need_confirm 中的待确认项。
    只依赖标准库。
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

LAYOUT_HINTS = {
    "list": ["list", "feed", "item", "card", "list-item"],
    "grid": ["grid", "row", "col", "cell", "entry"],
    "form": ["form", "input", "textarea", "label", "submit"],
    "detail": ["detail", "article", "content", "description"],
    "profile": ["profile", "avatar", "user-info", "mine"],
}

INTERACTION_HINTS = {
    "@click": "tap",
    "onclick": "tap",
    "href": "navigate",
}

PACKAGE_RE = re.compile(r"^[a-z][a-z0-9]*(\.[a-z][a-z0-9_]*)+$")


def to_pascal(name):
    """kebab / snake -> PascalCase"""
    return "".join(part[:1].upper() + part[1:] for part in re.split(r"[-_\s]", name) if part)


def to_kebab(name):
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1-\2", name)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", s)
    return s.replace("_", "-").lower()


def guess_layout(html):
    lowered = html.lower()
    scores = {}
    for layout, hints in LAYOUT_HINTS.items():
        scores[layout] = sum(lowered.count(h) for h in hints)
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "custom"


def extract_title(html):
    m = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
    if m:
        return m.group(1).strip()
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return ""


def extract_class_names(html):
    names = []
    for m in re.finditer(r'class="([^"]+)"', html):
        for part in m.group(1).split():
            if part and part not in names:
                names.append(part)
    return names


def extract_components(class_names):
    ignore = {
        "page", "container", "wrapper", "row", "col", "flex", "main",
        "content", "box", "inner", "outer", "wrap", "layout",
    }
    hints = ["card", "item", "tag", "avatar", "empty", "nav", "bar", "header"]
    components = []
    for name in class_names:
        base = name.split("__")[0].split("--")[0]
        if base in ignore or len(base) < 3:
            continue
        if any(h in base for h in hints) and base not in components:
            components.append(base)
    return [to_pascal(c) for c in components][:10]


def extract_data_fields(class_names):
    mapping = {
        "avatar": "avatar",
        "img": "avatar",
        "image": "imageUrl",
        "title": "title",
        "name": "author",
        "author": "author",
        "desc": "description",
        "price": "price",
        "tag": "tags",
        "time": "createdAt",
        "date": "createdAt",
        "count": "count",
        "rating": "rating",
        "status": "status",
    }
    fields = ["id"]
    for name in class_names:
        for key, field in mapping.items():
            if key in name.lower() and field not in fields:
                fields.append(field)
    return fields


def extract_interactions(html):
    interactions = []
    lowered = html.lower()
    for attr, event in INTERACTION_HINTS.items():
        if attr in lowered:
            interactions.append({"event": event, "target": "element", "action": "navigate", "to": ""})
    if "pull" in lowered or "refresh" in lowered:
        interactions.append({"event": "pull-down", "action": "refresh"})
    if "load-more" in lowered or "加载更多" in html:
        interactions.append({"event": "scroll-bottom", "action": "load-more"})
    return interactions


def extract_texts(html, limit=20):
    texts = re.findall(r">\s*([\u4e00-\u9fa5][^<>]{0,30})\s*<", html)
    seen = []
    for t in texts:
        t = t.strip()
        if t and t not in seen:
            seen.append(t)
        if len(seen) >= limit:
            break
    return seen


def _saturation(hex_color):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return max(r, g, b) - min(r, g, b)


def extract_primary_color(html):
    """优先取 CSS 变量 --primary，其次取出现最多且饱和度足够的颜色。

    直接取最高频会把背景灰、文字灰当成主色，因此过滤低饱和色。
    """
    m = re.search(r"--[\w-]*primary[\w-]*\s*:\s*#?([0-9a-fA-F]{6})\b", html)
    if m:
        return m.group(1).upper()

    colors = re.findall(r"#([0-9a-fA-F]{6})\b", html)
    if not colors:
        return ""

    candidates = [c.upper() for c in colors if _saturation(c.upper()) >= 24]
    pool = candidates or [c.upper() for c in colors]

    freq = {}
    for c in pool:
        freq[c] = freq.get(c, 0) + 1
    return max(freq, key=lambda k: freq[k])


def build_context(args, html):
    page_name = to_kebab(args.page_name)
    title = args.title or extract_title(html) or "首页"
    layout = guess_layout(html)
    class_names = extract_class_names(html)
    components = extract_components(class_names)
    data_fields = extract_data_fields(class_names)
    interactions = extract_interactions(html)
    primary = args.primary_color or extract_primary_color(html) or "2B6DE5"

    screen_class = to_pascal(page_name) + "Screen"
    viewmodel_class = to_pascal(page_name) + "ViewModel"
    route = page_name

    return {
        "project": {
            "project_name": args.project,
            "app_title": title,
            "package_name": args.package,
            "min_sdk": args.min_sdk,
            "target_sdk": args.target_sdk,
            "compile_sdk": args.compile_sdk,
            "source_type": "html",
            "language": "kotlin",
            "ui": "compose",
        },
        "design": {
            "primary_color": primary,
            "dark_theme": True,
            "radius_style": "md",
            "density": "comfortable",
        },
        "pages": [
            {
                "page_name": page_name,
                "route": route,
                "screen_class": screen_class,
                "viewmodel_class": viewmodel_class,
                "layout": layout,
                "is_home": True,
                "needs_auth": True,
                "components": components,
                "data_model": "Item",
                "data_fields": data_fields,
                "interactions": interactions,
                "states": ["loading", "empty", "error", "loaded"],
                "notes": [],
            }
        ],
        "navigation": {
            "start_destination": route,
            "bottom_nav": {"enabled": False, "items": []},
        },
        "permissions": [p.strip() for p in args.permissions.split(",") if p.strip()],
        "diagnostics": {
            "parse_errors": [],
            "assumptions": [
                "布局按关键词频次推断为 %s" % layout,
                "组件由 class 名启发式推断，需人工核对",
                "主色取 HTML 中出现频次最高的 6 位 hex 值",
            ],
            "need_confirm": [
                "页面之间的跳转关系（HTML 通常无法体现）",
                "是否需要登录与权限路由",
                "空态 / 错误态文案",
                "是否需要底部导航",
            ],
            "extracted_texts": extract_texts(html),
        },
    }


def main():
    parser = argparse.ArgumentParser(description="HTML 原型 -> proto_context.json（Android 初稿）")
    parser.add_argument("html", help="原型 HTML 文件路径")
    parser.add_argument("--out", default="proto_context.json", help="输出 JSON 路径")
    parser.add_argument("--project", default="android-app", help="工程名（kebab-case）")
    parser.add_argument("--title", default="", help="应用标题")
    parser.add_argument("--package", required=True, help="应用包名，如 com.example.app")
    parser.add_argument("--min-sdk", type=int, default=24, help="最低系统版本")
    parser.add_argument("--target-sdk", type=int, default=35, help="目标系统版本")
    parser.add_argument("--compile-sdk", type=int, default=35, help="编译系统版本")
    parser.add_argument("--page-name", default="index", help="页面名（kebab-case）")
    parser.add_argument("--primary-color", default="", help="主色 6 位 hex，不带 #")
    parser.add_argument(
        "--permissions",
        default="INTERNET,ACCESS_NETWORK_STATE",
        help="权限列表，逗号分隔（不要写无理由的权限）",
    )
    args = parser.parse_args()

    if not PACKAGE_RE.match(args.package):
        print("错误：包名不合法（应全小写点分，如 com.example.app）：%s" % args.package)
        return 2

    html_path = Path(args.html)
    if not html_path.exists():
        print("错误：文件不存在 %s" % html_path)
        return 2

    html = html_path.read_text(encoding="utf-8", errors="ignore")
    context = build_context(args, html)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8")

    page = context["pages"][0]
    print(json.dumps(
        {
            "output": str(out_path),
            "package_name": context["project"]["package_name"],
            "package_path": context["project"]["package_name"].replace(".", "/"),
            "layout": page["layout"],
            "screen_class": page["screen_class"],
            "components": page["components"],
            "data_fields": page["data_fields"],
            "primary_color": context["design"]["primary_color"],
            "note": "这是初稿，请核对 diagnostics.need_confirm 中的待确认项",
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
