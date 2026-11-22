"""Models 包

导出 ORM 基类；具体业务表模型由脚手架按 DDL 生成后在此追加 import。
"""

from .base import BaseModel, TimestampMixin, SoftDeleteMixin

# 与 core.database.Base 同源，便于 metadata.create_all / 测试建表
from core.database import Base

__all__ = [
    "Base",
    "BaseModel",
    "TimestampMixin",
    "SoftDeleteMixin",
]
