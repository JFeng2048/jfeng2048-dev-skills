"""
{{table_comment}}服务层单元测试（占位）

【HAND-WRITTEN 占位】由 sql-to-fastapi-restfulapi-scaffold 首次生成；已存在则跳过。
目标：面向 {{class_name}}Service 的单元测试（建议使用 conftest 的 sqlite `session` fixture）。

说明：
- 本文件为占位骨架，默认用例可先 skip，待业务稳定后补齐断言。
- 单条 CRUD 可测 Service 对 Repository 的委托；列表/状态等业务逻辑在此补充。
"""

import pytest

from service.{{table_name}}_service import {{class_name}}Service
from schemas.{{table_name}} import (
    {{class_name}}Create,
    {{class_name}}Update,
    {% if status_flag_fields %}
    {{class_name}}StatusUpdate,
    {% endif %}
)


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 {{class_name}}Service 单元测试后移除 skip")
async def test_{{table_name}}_service_create_placeholder(session):
    """占位：创建（委托 Repository.create）"""
    service = {{class_name}}Service(session)
    # data = {{class_name}}Create(...)
    # result = await service.create(data)
    # assert result is not None
    assert False, "请实现 create 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 {{class_name}}Service 单元测试后移除 skip")
async def test_{{table_name}}_service_get_detail_placeholder(session):
    """占位：详情（委托 Repository.get）"""
    service = {{class_name}}Service(session)
    # result = await service.get_detail(...)
    # assert result.{{primary_key_param}} is not None
    assert False, "请实现 get_detail 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 {{class_name}}Service 单元测试后移除 skip")
async def test_{{table_name}}_service_update_placeholder(session):
    """占位：更新（委托 Repository.update）"""
    service = {{class_name}}Service(session)
    # result = await service.update(..., {{class_name}}Update(...))
    assert False, "请实现 update 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 {{class_name}}Service 单元测试后移除 skip")
async def test_{{table_name}}_service_delete_placeholder(session):
    """占位：删除（委托 Repository.delete）"""
    service = {{class_name}}Service(session)
    # await service.delete(...)
    assert False, "请实现 delete 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐列表业务测试后移除 skip")
async def test_{{table_name}}_service_get_list_placeholder(session):
    """占位：分页列表（Service 业务逻辑）"""
    service = {{class_name}}Service(session)
    # result = await service.get_list(page=1, size=10)
    # assert "items" in result and "total" in result
    assert False, "请实现 get_list 单元测试"


{% if status_flag_fields %}
@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐状态变更业务测试后移除 skip")
async def test_{{table_name}}_service_update_status_placeholder(session):
    """占位：状态/标识位变更（Service.update_status）"""
    service = {{class_name}}Service(session)
    # data = {{class_name}}StatusUpdate(...)
    # result = await service.update_status(..., data)
    assert False, "请实现 update_status 单元测试"
{% endif %}


# ---------- 在下方添加更多业务方法的单元测试占位 ----------
# @pytest.mark.asyncio
# @pytest.mark.skip(reason="占位")
# async def test_{{table_name}}_service_custom_business_placeholder(session):
#     service = {{class_name}}Service(session)
#     ...
