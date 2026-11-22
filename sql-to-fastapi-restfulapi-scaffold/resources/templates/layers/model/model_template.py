"""
{{table_comment}}数据模型

【AUTO-GENERATED】此文件由 SQL-to-FastAPI-Scaffold 自动生成；表结构变更时 skill 会覆盖。
若已手工修改本文件，请把标记改为 【HAND-WRITTEN】，skill 将跳过覆盖并输出人工待办。
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, BigInteger, Boolean,
    DateTime, Date, Time, Text, Numeric, Float, JSON,
    ForeignKey
)
from sqlalchemy.orm import relationship
from models.base import BaseModel


class {{class_name}}(BaseModel):
    """
    {{table_comment}}
    """
    __tablename__ = "{{table_name}}"

    {% for field in fields %}
    {{field.name}} = Column(
        "{{field.db_name}}",
        {{field.sqlalchemy_type}},
        {% if field.primary_key %}primary_key=True,{% endif %}
        {% if field.foreign_key %}ForeignKey("{{field.foreign_key}}"),{% endif %}
        {% if not field.not_null %}nullable=True,{% else %}nullable=False,{% endif %}
        {% if field.unique %}unique=True,{% endif %}
        {% if field.default %}default={{field.default}},{% endif %}
        comment="{{field.comment}}"
    )
    {% endfor %}

    {% if foreign_keys %}
    {% for fk in foreign_keys %}
    {{fk.relationship_name}} = relationship(
        "{{fk.related_class}}",
        foreign_keys=[{{fk.field_name}}]
    )
    {% endfor %}
    {% endif %}

    {% for sensitive in sensitive_fields %}
    @property
    def masked_{{sensitive.name}}(self) -> str:
        """
        脱敏后的{{sensitive.comment}}
        """
        if self.{{sensitive.name}} and len(self.{{sensitive.name}}) >= {{sensitive.min_length}}:
            return f"{self.{{sensitive.name}}[:3]}****{self.{{sensitive.name}}[-4:]}"
        return "****"
    {% endfor %}
