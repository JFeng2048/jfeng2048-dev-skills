"""api/v1/{{resource_singular}}/ 包初始化。

【AUTO-GENERATED】由 sql-to-fastapi-restfulapi-scaffold 在新增表时生成。
api/v1/__init__.py 使用 `from api.v1.{{resource_singular}} import router`，
因此本文件必须导出 router；缺失会导致 ImportError。
"""

from .{{resource_singular}}Resource import router

__all__ = ["router"]
