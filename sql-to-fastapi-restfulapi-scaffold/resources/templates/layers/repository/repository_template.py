"""
{{table_comment}}数据访问层（Repository）

【AUTO-GENERATED】由 sql-to-fastapi-restfulapi-scaffold 生成，可被 skill 覆盖。
禁止在此文件编写业务规则。
Resource/API 层不要直接依赖本 Repository。

职责边界（强制）：
- 本层只做「单表、单条记录」的基础 CRUD，方法名固定为（按增删改查顺序）：
  create / delete / update / get
- 列表分页、过滤、状态变更、跨表流程等一律视为业务逻辑，写在 Service。
"""

from typing import Any, Dict, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.{{table_name}} import {{class_name}}
from schemas.{{table_name}} import {{class_name}}Create, {{class_name}}Update
from utils.custom_exceptions import NotFoundException


class {{class_name}}Repository:
    """
    {{table_comment}}仓储：仅负责单表单条记录的 CRUD（方法顺序：增删改查）
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: {{class_name}}Create) -> {{class_name}}:
        """增：插入一条记录并提交"""
        # exclude_unset：未显式传入的字段交由数据库/模型默认值处理，
        # 避免把 is_deleted / create_time / update_time 等默认列写成 NULL。
        obj = {{class_name}}(**data.model_dump(exclude_unset=True))
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, {{primary_key_param}}: {{primary_key_type}}) -> None:
        """删：有软删字段则软删，否则硬删"""
        obj = await self.get({{primary_key_param}})
        {% if soft_delete_field %}
        setattr(obj, "{{soft_delete_field}}", True)
        await self.db.commit()
        {% else %}
        await self.db.delete(obj)
        await self.db.commit()
        {% endif %}

    async def update(
        self,
        {{primary_key_param}}: {{primary_key_type}},
        data: Union[{{class_name}}Update, Dict[str, Any]],
    ) -> {{class_name}}:
        """改：按主键更新一条记录（仅更新传入字段）"""
        if hasattr(data, "model_dump"):
            fields = data.model_dump(exclude_unset=True)
        else:
            fields = data
        obj = await self.get({{primary_key_param}})
        for key, value in fields.items():
            setattr(obj, key, value)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get(self, {{primary_key_param}}: {{primary_key_type}}) -> {{class_name}}:
        """查：按主键获取一条（软删除视为不存在）"""
        {% if soft_delete_field %}
        obj = await self.db.scalar(
            select({{class_name}}).where(
                {{class_name}}.{{primary_key_param}} == {{primary_key_param}},
                {{class_name}}.{{soft_delete_field}} == False,  # noqa: E712
            )
        )
        {% else %}
        obj = await self.db.scalar(
            select({{class_name}}).where(
                {{class_name}}.{{primary_key_param}} == {{primary_key_param}}
            )
        )
        {% endif %}
        if not obj:
            raise NotFoundException("{{table_comment}}不存在")
        return obj
