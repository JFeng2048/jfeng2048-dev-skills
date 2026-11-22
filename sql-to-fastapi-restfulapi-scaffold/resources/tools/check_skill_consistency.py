"""检查 sql-to-fastapi-restfulapi-scaffold 自身是否自洽。

不渲染目标项目。确认骨架里没有已淘汰文件、命名规则与资源模板使用同一套前缀变量，
并校验「已有项目增量更新」的策略、规范、模板标记与各文档引用是否齐全。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
STRUCTURE = SKILL_ROOT / "resources" / "templates" / "project_structure"

OBSOLETE = (
    "app/events.py",
    "app/router.py",
    "config/settings.py",
    "utils/loguru.py",
    "core/dependencies.py",
)


REQUIRED_CHANGE_TYPES = (
    "add_table",
    "add_column",
    "drop_column",
    "rename_column",
    "modify_column_type",
    "modify_nullable",
    "modify_default",
    "modify_unique",
    "add_status_flag",
    "drop_status_flag",
    "change_soft_delete_field",
    "change_primary_key",
    "add_foreign_key",
    "drop_foreign_key",
    "comment_only",
    "rename_table",
    "drop_table",
)


def check_incremental(errors: list[str]) -> None:
    """校验已有项目增量更新相关的资源、标记与文档引用。"""
    config = SKILL_ROOT / "resources" / "config" / "incremental_change_policy.json"
    spec = SKILL_ROOT / "resources" / "specifications" / "incremental_update.md"
    init_template = (
        SKILL_ROOT / "resources" / "templates" / "layers" / "resource" / "resource_init_template.py"
    )
    for path in (config, spec, init_template):
        if not path.is_file():
            errors.append(f"缺少增量更新资源: {path.relative_to(SKILL_ROOT)}")
    if not config.is_file():
        return

    try:
        policy = json.loads(config.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"incremental_change_policy.json 无法解析: {exc}")
        return

    for key in (
        "modes",
        "mode_detection",
        "baseline_snapshot",
        "file_roles",
        "change_types",
        "hand_written_protection",
        "registration",
        "migration",
        "verification",
        "report",
    ):
        if key not in policy:
            errors.append(f"incremental_change_policy.json 缺少 {key}")
    for mode in ("greenfield", "add_table", "alter_table", "drop_table"):
        if mode not in policy.get("modes", {}):
            errors.append(f"incremental_change_policy.json 缺少运行模式 {mode}")
    for change in REQUIRED_CHANGE_TYPES:
        if change not in policy.get("change_types", {}):
            errors.append(f"incremental_change_policy.json 缺少变更类型 {change}")
    for change in ("add_status_flag", "drop_status_flag", "change_soft_delete_field", "change_primary_key"):
        entry = policy.get("change_types", {}).get(change, {})
        if not entry.get("manual_todo"):
            errors.append(f"变更类型 {change} 缺少手写文件待办清单")
    if not policy.get("hand_written_protection", {}).get("rules"):
        errors.append("incremental_change_policy.json 缺少手写保护规则")
    if not policy.get("registration", {}).get("dedupe"):
        errors.append("incremental_change_policy.json 缺少注册幂等规则")

    if spec.is_file() and len(spec.read_text(encoding="utf-8")) < 500:
        errors.append("incremental_update.md 内容过短，疑似占位")

    layers = SKILL_ROOT / "resources" / "templates" / "layers"
    markers = {
        "model/model_template.py": "【AUTO-GENERATED】",
        "schema/schema_template.py": "【AUTO-GENERATED】",
        "repository/repository_template.py": "【AUTO-GENERATED】",
        "resource/resource_template.py": "【AUTO-GENERATED】",
        "service/service_template.py": "【HAND-WRITTEN】",
        "test/unit/test_service_template.py": "【HAND-WRITTEN 占位】",
    }
    for relative, marker in markers.items():
        path = layers / relative
        if not path.is_file():
            errors.append(f"缺少层模板: {relative}")
        elif marker not in path.read_text(encoding="utf-8"):
            errors.append(f"层模板 {relative} 缺少归属标记 {marker}")
    resource_template = layers / "resource" / "resource_template.py"
    if resource_template.is_file() and "手写业务路由区" not in resource_template.read_text(encoding="utf-8"):
        errors.append("resource_template.py 缺少手写路由保护区标记")
    if init_template.is_file() and "import router" not in init_template.read_text(encoding="utf-8"):
        errors.append("resource_init_template.py 未导出 router")

    references = {
        SKILL_ROOT / "SKILL.md": (
            "incremental_change_policy.json",
            "incremental_update.md",
            "alter_table",
            "add_table",
            "步骤 2.2",
            "步骤 2.3",
        ),
        SKILL_ROOT / "README.md": ("已有项目的增量更新", "alter_table", "incremental_change_policy.json"),
        SKILL_ROOT / "resources" / "specifications" / "coding_standards.md": (
            "## 14. 已有项目增量变更规范",
            "incremental_change_policy.json",
        ),
    }
    for path, needles in references.items():
        if not path.is_file():
            errors.append(f"缺少文档: {path.relative_to(SKILL_ROOT)}")
            continue
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                errors.append(f"{path.relative_to(SKILL_ROOT)} 未引用增量内容: {needle}")


def check_baseline_files(errors: list[str]) -> None:
    """校验骨架必带文件、Python 版本占位符与响应码基线。"""
    for relative in (".gitignore", "utils/response_code.py", "core/permissions.py"):
        if not (STRUCTURE / relative).is_file():
            errors.append(f"缺少骨架基线文件: {relative}")

    python_version_file = STRUCTURE / ".python-version"
    if python_version_file.is_file():
        content = python_version_file.read_text(encoding="utf-8").strip()
        if not (content.startswith("{{") and content.endswith("}}")):
            errors.append(".python-version 必须使用 {{python_version}} 占位符，不能硬编码版本号")

    gitignore = STRUCTURE / ".gitignore"
    if gitignore.is_file():
        gitignore_text = gitignore.read_text(encoding="utf-8")
        for needle in ("__pycache__/", ".venv/", ".env"):
            if needle not in gitignore_text:
                errors.append(f".gitignore 缺少必要规则: {needle}")

    response_code_file = STRUCTURE / "utils" / "response_code.py"
    if response_code_file.is_file():
        text = response_code_file.read_text(encoding="utf-8")
        for needle in ("class RET", "class BusinessCode", "def get_message"):
            if needle not in text:
                errors.append(f"utils/response_code.py 缺少 {needle}")


def main() -> int:
    errors: list[str] = []

    for relative in OBSOLETE:
        if (STRUCTURE / relative).exists():
            errors.append(f"淘汰文件仍在骨架中: {relative}")

    check_baseline_files(errors)

    for path in STRUCTURE.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "{%" in text:
            errors.append(f"骨架 Python 含未渲染的 Jinja 控制块: {path.relative_to(SKILL_ROOT)}")

    rules = json.loads(
        (SKILL_ROOT / "resources" / "config" / "naming_rules.json").read_text(encoding="utf-8")
    )
    if "plural_rules" in json.dumps(rules):
        errors.append("naming_rules.json 仍包含 plural_rules")
    route = rules.get("route_prefix", {})
    if route.get("template_variable") != "route_prefix":
        errors.append("naming_rules.json 缺少 route_prefix.template_variable")
    if route.get("examples", {}).get("company_file") != "/company-file":
        errors.append("company_file 的路由前缀不是 /company-file")

    resource = (
        SKILL_ROOT / "resources" / "templates" / "layers" / "resource" / "resource_template.py"
    ).read_text(encoding="utf-8")
    if 'prefix="/{{route_prefix}}"' not in resource:
        errors.append("资源模板的 APIRouter 前缀未使用 route_prefix")
    if 'prefix="/{{resource_singular}}"' in resource:
        errors.append("资源模板仍把 resource_singular 当作 HTTP 前缀")

    readme = (SKILL_ROOT / "README.md").read_text(encoding="utf-8")
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    for label, text in (("README.md", readme), ("SKILL.md", skill)):
        if "create / get / update / delete" in text:
            errors.append(f"{label} 的 Repository 方法顺序仍是 create/get/update/delete")
        if "不生成的文件" in text and "Docker" in text:
            errors.append(f"{label} 仍把 Docker 列进不生成清单")
        for banned in ("events.py", "loguru.py", "config/settings.py"):
            if f"├── {banned}" in text or f"│   ├── {banned}" in text or f"│   └── {banned}" in text:
                errors.append(f"{label} 的目录树仍包含 {banned}")

    copilot = SKILL_ROOT / "docs" / "GitHub Copilot中使用sql-to-fastapi-restfulapi-scaffold技能.md"
    if not copilot.is_file():
        errors.append("缺少 FastAPI 的 Copilot 配置说明")
    flask_doc = SKILL_ROOT / "docs" / "GitHub Copilot中使用sql-to-flask-restfulapi-scaffold技能.md"
    if flask_doc.exists():
        errors.append("FastAPI 技能目录仍保留 Flask 的 Copilot 说明")

    check_incremental(errors)

    if errors:
        print("\n".join(errors))
        return 1
    print("sql-to-fastapi-restfulapi-scaffold consistency ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
