"""
{{table_comment}}业务服务（Service）

【HAND-WRITTEN】业务逻辑写在本文件；skill 仅在文件不存在时生成一次，之后不再覆盖。

约定：
- API/Resource 层统一只依赖本 Service，不直接调用 Repository。
- Repository 仅提供单条 CRUD：create / delete / update / get（增删改查顺序）。
- 列表分页、过滤、状态变更、跨表流程等均视为业务逻辑，写在本层。
{% if status_flag_fields %}- 表含状态/标识位字段时，额外提供 update_status（禁止走通用 Update Schema）。
{% endif %}"""

from typing import Any, Dict, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.{{table_name}} import {{class_name}}
from repository.{{table_name}}_repository import {{class_name}}Repository
from schemas.{{table_name}} import (
    {{class_name}}Create,
    {{class_name}}Update,
    {{class_name}}Response,
    {% if status_flag_fields %}
    {{class_name}}StatusUpdate,
    {% endif %}
)


class {{class_name}}Service:
    """
    {{table_comment}}业务服务

    - 单条 CRUD：委托 Repository.create / delete / update / get
    - 列表及其他业务：在本类实现
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = {{class_name}}Repository(db)

    # -------------------- 单条 CRUD（委托 Repository）--------------------

    async def create(self, data: {{class_name}}Create) -> {{class_name}}Response:
        """创建{{table_comment}}"""
        obj = await self.repo.create(data)
        return {{class_name}}Response.model_validate(obj)

    async def get_detail(self, {{primary_key_param}}: {{primary_key_type}}) -> {{class_name}}Response:
        """详情（单条）"""
        obj = await self.repo.get({{primary_key_param}})
        return {{class_name}}Response.model_validate(obj)

    async def update(
        self,
        {{primary_key_param}}: {{primary_key_type}},
        data: {{class_name}}Update,
    ) -> {{class_name}}Response:
        """更新（不含状态/标识位字段；状态请用 update_status）"""
        obj = await self.repo.update({{primary_key_param}}, data)
        return {{class_name}}Response.model_validate(obj)

    async def delete(self, {{primary_key_param}}: {{primary_key_type}}) -> None:
        """删除"""
        await self.repo.delete({{primary_key_param}})

    # -------------------- 业务逻辑：列表 --------------------

    async def get_list(
        self,
        page: int = 1,
        size: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """分页列表（业务逻辑：分页 / 过滤{% if soft_delete_field %} / 排除软删除{% endif %}）"""
        {% if soft_delete_field %}
        conditions = [{{class_name}}.{{soft_delete_field}} == False]  # noqa: E712
        {% else %}
        conditions = []
        {% endif %}
        if filters:
            for field, value in filters.items():
                if value is not None and hasattr({{class_name}}, field):
                    conditions.append(getattr({{class_name}}, field) == value)

        stmt = select({{class_name}}).order_by({{class_name}}.{{primary_key_param}}.asc())
        count_stmt = select(func.count()).select_from({{class_name}})
        for cond in conditions:
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        total = await self.db.scalar(count_stmt) or 0
        offset = (page - 1) * size
        rows = (await self.db.execute(stmt.offset(offset).limit(size))).scalars().all()
        return {
            "items": [{{class_name}}Response.model_validate(item) for item in rows],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size if size else 0,
        }

    {% if status_flag_fields %}
    # -------------------- 业务逻辑：状态/标识位 --------------------

    async def update_status(
        self,
        {{primary_key_param}}: {{primary_key_type}},
        data: {{class_name}}StatusUpdate,
    ) -> {{class_name}}Response:
        """
        修改状态/标识位：{% for f in status_flag_fields %}{{f.name}}{% if not loop.last %}、{% endif %}{% endfor %}

        业务入口在 Service；持久化走 Repository.update（传入字段字典）。
        """
        obj = await self.repo.update(
            {{primary_key_param}},
            data.model_dump(exclude_unset=True),
        )
        return {{class_name}}Response.model_validate(obj)
    {% endif %}

    # ---------- 在下方添加商业逻辑方法 ----------
    # 示例：
    # async def transfer_department(
    #     self,
    #     {{primary_key_param}}: {{primary_key_type}},
    #     new_department_id: int,
    # ) -> {{class_name}}Response:
    #     obj = await self.repo.get({{primary_key_param}})
    #     # ... 业务规则 / 跨表操作 ...
    #     return {{class_name}}Response.model_validate(obj)
