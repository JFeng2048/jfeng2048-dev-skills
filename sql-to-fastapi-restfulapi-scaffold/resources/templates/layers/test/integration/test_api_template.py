"""
{{table_comment}}接口集成测试（直连真实 MySQL）

路径：/api/v1/{{resource_path}}
说明：
- 主键字段：{{primary_key_param}}（类型 {{primary_key_type}}）
{% if soft_delete_field %}- DELETE 为软删除（{{soft_delete_field}}=True/1），记录仍留在表中，详情应 404。
{% else %}- 本表无软删字段，DELETE 为硬删除；删除后详情应 404，库中记录应不存在。
{% endif %}{% if status_flag_fields %}- 状态字段走 PATCH /{pk}/status；通用 PUT 不得携带状态字段（期望 422）。
{% endif %}
【覆盖策略】文件已存在则 skill 跳过（人手维护）。
"""

import uuid

import httpx
import pytest
from sqlalchemy import select

from core import database
from models.{{table_name}} import {{class_name}}


{% for h in unique_helper_fields %}
def _new_{{h.name}}() -> {{h.return_type}}:
    """生成测试用唯一 {{h.name}}，避免多次运行冲突"""
    {% if h.return_type == "int" %}
    return int(f"9{uuid.uuid4().int % 10**15:015d}"[:16])
    {% else %}
    value = f"skill_{{h.name}}_" + uuid.uuid4().hex[:8]
    {% if h.max_length %}
    return value[:{{h.max_length}}]
    {% else %}
    return value
    {% endif %}
    {% endif %}


{% endfor %}
async def _db_row(pk: {{primary_key_type}}) -> {{class_name}} | None:
    async with database.AsyncSessionLocal() as s:
        return (
            await s.execute(
                select({{class_name}}).where({{class_name}}.{{primary_key_param}} == pk)
            )
        ).scalar_one_or_none()


@pytest.mark.asyncio
async def test_{{table_name}}_crud_flow(app):
    """基础 CRUD 集成测试（真实 MySQL）"""
    transport = httpx.ASGITransport(app=app)
    headers = {"Authorization": "Bearer test-token"}
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # --- 生成 Create 请求体：按表字段填写；唯一字段请用 _new_*() ---
        payload = {
            {% for field in create_payload_fields %}
            "{{field.name}}": {{field.example_expr}},
            {% endfor %}
        }

        # 1) 创建
        resp = await client.post("/api/v1/{{resource_path}}", json=payload, headers=headers)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        pk = data["{{primary_key_param}}"]

        row = await _db_row(pk)
        assert row is not None, "创建后未在真实 {{table_name}} 表中找到记录"
        {% if soft_delete_field %}
        assert row.{{soft_delete_field}} in (False, 0)
        {% endif %}

        # 2) 列表
        resp = await client.get(
            "/api/v1/{{resource_path}}",
            params={"page": 1, "page_size": 10},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["meta"]["total"] >= 1

        # 3) 详情
        resp = await client.get(f"/api/v1/{{resource_path}}/{pk}", headers=headers)
        assert resp.status_code == 200, resp.text

        # 4) 更新（不含状态/标识位字段）
        update_payload = {
            {% for field in update_payload_fields %}
            "{{field.name}}": {{field.example_expr}},
            {% endfor %}
        }
        resp = await client.put(
            f"/api/v1/{{resource_path}}/{pk}",
            json=update_payload,
            headers=headers,
        )
        assert resp.status_code == 200, resp.text

        {% if status_flag_fields %}
        # 4b) PUT 携带状态字段应被 Schema 拒绝
        resp = await client.put(
            f"/api/v1/{{resource_path}}/{pk}",
            json={
                {% for f in status_flag_fields %}
                "{{f.name}}": {{f.test_value_locked}},
                {% endfor %}
            },
            headers=headers,
        )
        assert resp.status_code == 422, resp.text

        # 5) 专用改状态
        resp = await client.patch(
            f"/api/v1/{{resource_path}}/{pk}/status",
            json={
                {% for f in status_flag_fields %}
                "{{f.name}}": {{f.test_value_locked}},
                {% endfor %}
            },
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        {% for f in status_flag_fields %}
        assert resp.json()["data"]["{{f.name}}"] == {{f.test_value_locked}}
        {% endfor %}

        resp = await client.patch(
            f"/api/v1/{{resource_path}}/{pk}/status",
            json={
                {% for f in status_flag_fields %}
                "{{f.name}}": {{f.test_value_active}},
                {% endfor %}
            },
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        {% endif %}

        # 删除
        resp = await client.delete(f"/api/v1/{{resource_path}}/{pk}", headers=headers)
        assert resp.status_code == 200, resp.text

        resp = await client.get(f"/api/v1/{{resource_path}}/{pk}", headers=headers)
        assert resp.status_code == 404, resp.text

        row = await _db_row(pk)
        {% if soft_delete_field %}
        assert row is not None, "软删除后记录应仍留在 {{table_name}} 表中"
        assert row.{{soft_delete_field}} in (True, 1)
        {% else %}
        assert row is None, "硬删除后记录应不在 {{table_name}} 表中"
        {% endif %}


# ===========================================================================
# 商业逻辑接口测试占位（后续业务 API 在此补充；默认 skip）
# ===========================================================================

@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐商业逻辑接口测试后移除 skip")
async def test_{{table_name}}_business_api_placeholder(app):
    """
    占位：商业逻辑接口集成测试

    在 Service/Resource 增加非基础 CRUD 业务接口后，在此补充真实请求断言。
    """
    transport = httpx.ASGITransport(app=app)
    headers = {"Authorization": "Bearer test-token"}
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # resp = await client.post("/api/v1/{{resource_path}}/...", json={...}, headers=headers)
        # assert resp.status_code == 200, resp.text
        assert False, "请实现商业逻辑接口集成测试"
