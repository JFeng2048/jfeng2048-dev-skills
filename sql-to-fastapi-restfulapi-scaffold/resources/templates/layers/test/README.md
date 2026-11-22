"""测试层模板说明

本目录模板用于按表生成 pytest 测试代码。

文件：
- unit/test_service_template.py
  → 输出：tests/unit/test_{table_name}_service.py
  → 性质：Service 层单元测试占位（默认 skip）

- integration/test_api_template.py
  → 输出：tests/integration/api/v1/test_{table_name}.py
  → 性质：接口集成测试（基础 CRUD 可运行）+ 商业逻辑占位（skip）

生成时由 LLM 填充变量（见 SKILL.md「测试代码生成」章节）。
"""
