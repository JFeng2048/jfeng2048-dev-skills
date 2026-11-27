#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = TOOLS_DIR.parent
sys.path.insert(0, str(TOOLS_DIR))

import render_template
import validate_project


# Deliberately synthetic inputs for syntax and safety tests, never production defaults.
TEST_VERSION = "1.0.0"
VERSIONS = {
    key: TEST_VERSION for key in (
        "gradle", "agp", "kotlin", "compose_bom", "core_ktx", "lifecycle",
        "activity_compose", "navigation", "hilt", "room", "datastore",
        "okhttp", "coroutines", "junit",
    )
}
VERSIONS["ksp"] = "1.0.0-1.0.0"

RESOLUTION = {
    "checked_at": date.today().isoformat(),
    "selection": "latest-stable-compatible",
    "compatibility_verified": True,
    "sources": ["https://example.invalid/release-metadata-fixture"],
}


def version_payload():
    return {"versions": VERSIONS, "resolution": RESOLUTION}


class RenderTemplateTest(unittest.TestCase):
    def test_requires_verified_concrete_versions(self):
        context = {
            "project": {
                "project_name": "sample-app",
                "app_title": "Sample",
                "package_name": "com.example.sample",
                "min_sdk": 24,
                "target_sdk": 35,
                "compile_sdk": 36,
                "jdk": 21,
                "versions": dict(VERSIONS),
                "version_resolution": dict(RESOLUTION),
            },
            "pages": [{"domain": "orders", "page_name": "home", "is_home": True}],
            "design": {},
        }

        mapping, features = render_template.build_mapping(context)

        self.assertEqual(["orders"], [feature["domain"] for feature in features])
        self.assertEqual(VERSIONS["core_ktx"], mapping["{{core_ktx_version}}"])
        self.assertEqual(RESOLUTION["checked_at"], mapping["{{versions_checked_at}}"])
        self.assertIn("example.invalid", mapping["{{versions_sources}}"])

        context["project"]["versions"]["kotlin"] = "<latest-stable>"
        with self.assertRaises(SystemExit):
            render_template.build_mapping(context)

        context["project"]["versions"] = dict(VERSIONS)
        context["project"]["version_resolution"]["checked_at"] = (
            date.today() - timedelta(days=1)
        ).isoformat()
        with self.assertRaises(SystemExit):
            render_template.build_mapping(context)

    def test_parse_render_and_static_validation(self):
        parse_script = TOOLS_DIR / "parse_prototype.py"
        preview_script = TOOLS_DIR / "preview_plan.py"
        render_script = TOOLS_DIR / "render_template.py"
        validate_script = TOOLS_DIR / "validate_project.py"
        prototype = SKILL_DIR / "demo_input" / "index.html"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            versions_file = temp / "versions.json"
            context_file = temp / "proto_context.json"
            output_dir = temp / "sample-app"
            if not prototype.exists():
                prototype = temp / "index.html"
                prototype.write_text("<html><head><title>Orders</title></head><body><h1>Orders</h1></body></html>", encoding="utf-8")
            versions_file.write_text(
                json.dumps(version_payload()),
                encoding="utf-8",
            )

            subprocess.run(
                [
                    sys.executable, str(parse_script), str(prototype),
                    "--package", "com.example.sample",
                    "--project", "sample-app",
                    "--domain", "orders",
                    "--min-sdk", "24",
                    "--target-sdk", "35",
                    "--compile-sdk", "36",
                    "--jdk", "21",
                    "--versions-json", str(versions_file),
                    "--out", str(context_file),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [sys.executable, str(render_script), str(context_file), str(output_dir)],
                check=True,
                capture_output=True,
                text=True,
            )
            preview = subprocess.run(
                [sys.executable, str(preview_script), str(context_file)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertNotIn("renderer 会拒绝", preview.stdout)
            validation = subprocess.run(
                [sys.executable, str(validate_script), str(output_dir), "--json"],
                check=True,
                capture_output=True,
                text=True,
            )

            report = json.loads(validation.stdout)
            self.assertEqual(0, report["errors"])
            catalog = (output_dir / "gradle" / "libs.versions.toml").read_text(encoding="utf-8")
            self.assertIn('androidx-core-ktx = { module = "androidx.core:core-ktx", version.ref = "coreKtx" }', catalog)
            generated_readme = (output_dir / "README.md").read_text(encoding="utf-8")
            self.assertIn(RESOLUTION["checked_at"], generated_readme)
            self.assertNotIn("{{", generated_readme)

            protected_output = temp / "protected-output"
            protected_output.mkdir()
            sentinel = protected_output / "keep.txt"
            sentinel.write_text("keep", encoding="utf-8")
            invalid_context = json.loads(context_file.read_text(encoding="utf-8"))
            invalid_context["project"]["versions"]["kotlin"] = "<latest-stable>"
            invalid_context_file = temp / "invalid-context.json"
            invalid_context_file.write_text(
                json.dumps(invalid_context),
                encoding="utf-8",
            )
            failed_render = subprocess.run(
                [
                    sys.executable, str(render_script), str(invalid_context_file),
                    str(protected_output), "--force",
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, failed_render.returncode)
            self.assertEqual("keep", sentinel.read_text(encoding="utf-8"))

            common_build = output_dir / "core" / "common" / "build.gradle.kts"
            startup_build = output_dir / "core" / "startup" / "build.gradle.kts"
            common_build.write_text(
                common_build.read_text(encoding="utf-8")
                + '\ndependencies { implementation(project(":core:startup")) }\n',
                encoding="utf-8",
            )
            startup_build.write_text(
                startup_build.read_text(encoding="utf-8")
                + '\ndependencies { implementation(project(":core:common")) }\n',
                encoding="utf-8",
            )
            cycle_report = validate_project.run(output_dir)
            self.assertTrue(any(
                level == validate_project.ERROR and "模块依赖环" in detail
                for _, level, detail in cycle_report
            ))


if __name__ == "__main__":
    unittest.main()
