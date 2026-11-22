"""
{{table_comment}}API路由

【AUTO-GENERATED】由 SQL-to-FastAPI-Scaffold 自动生成；表结构变更时只重生成内置 CRUD 区块，
文件末尾「手写业务路由区」中的自定义端点会被保留。若整份文件已手改，请把标记改为 【HAND-WRITTEN】。

约定：
- HTTP 层统一只依赖 Service，不直接依赖 Repository。
- 默认不启用鉴权（接口开箱即用、无需登录）；如需登录鉴权，见文件底部「鉴权启用」注释。
- 字段校验由 Schema 在进入端点前完成。
{% if status_flag_fields %}- 状态/标识位字段通过 PATCH /{{{primary_key_param}}}/status 专用修改。
{% endif %}"""

from fastapi import APIRouter, Depends, Path, Query, status

from service.dependencies import get_{{service_name}}
from service.{{table_name}}_service import {{class_name}}Service
from schemas.{{table_name}} import (
    {{class_name}}Create,
    {{class_name}}Update,
    {{class_name}}Response,
    {% if status_flag_fields %}
    {{class_name}}StatusUpdate,
    {% endif %}
)
from schemas.response import (
    SuccessResponse,
    PaginationResponse,
    success_response,
    paginated_response,
)
from utils.custom_exceptions import handle_service_exceptions


router = APIRouter(prefix="/{{route_prefix}}", tags=["{{table_comment}}管理"])

# ===== 鉴权（默认关闭，接口开箱即用）=====
# 本脚手架生成的 CRUD 接口默认不需要登录。若项目需要登录鉴权，可统一在 router
# 上挂载依赖（推荐），或在单个路由上添加该 Depends：
#   from core.permissions import get_current_active_user
#   router = APIRouter(
#       prefix="/{{route_prefix}}",
#       tags=["{{table_comment}}管理"],
#       dependencies=[Depends(get_current_active_user)],
#   )


@router.get(
    "",
    response_model=PaginationResponse[{{class_name}}Response],
    status_code=status.HTTP_200_OK,
    summary="获取{{table_comment}}列表",
)
@handle_service_exceptions
async def get_{{resource_singular}}_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    service: {{class_name}}Service = Depends(get_{{service_name}}),
):
    """获取{{table_comment}}分页列表"""
    result = await service.get_list(page=page, size=page_size)
    return paginated_response(
        items=result["items"],
        total=result["total"],
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{{{primary_key_param}}}",
    response_model=SuccessResponse[{{class_name}}Response],
    status_code=status.HTTP_200_OK,
    summary="获取{{table_comment}}详情",
)
@handle_service_exceptions
async def get_{{resource_singular}}_detail(
    {{primary_key_param}}: {{primary_key_type}} = Path(..., description="{{primary_key_comment}}"),
    service: {{class_name}}Service = Depends(get_{{service_name}}),
):
    """获取{{table_comment}}详情"""
    result = await service.get_detail({{primary_key_param}})
    return success_response(result)


@router.post(
    "",
    response_model=SuccessResponse[{{class_name}}Response],
    status_code=status.HTTP_201_CREATED,
    summary="创建{{table_comment}}",
)
@handle_service_exceptions
async def create_{{resource_singular}}(
    data: {{class_name}}Create,
    service: {{class_name}}Service = Depends(get_{{service_name}}),
):
    """创建{{table_comment}}"""
    result = await service.create(data)
    return success_response(result, message="{{table_comment}}创建成功")


@router.put(
    "/{{{primary_key_param}}}",
    response_model=SuccessResponse[{{class_name}}Response],
    summary="更新{{table_comment}}",
)
@handle_service_exceptions
async def update_{{resource_singular}}(
    {{primary_key_param}}: {{primary_key_type}} = Path(..., description="{{primary_key_comment}}"),
    data: {{class_name}}Update = ...,
    service: {{class_name}}Service = Depends(get_{{service_name}}),
):
    """更新{{table_comment}}（不含状态/标识位字段）"""
    result = await service.update({{primary_key_param}}, data)
    return success_response(result, message="{{table_comment}}更新成功")


{% if status_flag_fields %}
@router.patch(
    "/{{{primary_key_param}}}/status",
    response_model=SuccessResponse[{{class_name}}Response],
    summary="修改{{table_comment}}状态/标识位",
)
@handle_service_exceptions
async def update_{{resource_singular}}_status(
    {{primary_key_param}}: {{primary_key_type}} = Path(..., description="{{primary_key_comment}}"),
    data: {{class_name}}StatusUpdate = ...,
    service: {{class_name}}Service = Depends(get_{{service_name}}),
):
    """
    专用修改状态/标识位：{% for f in status_flag_fields %}{{f.name}}{% if not loop.last %}、{% endif %}{% endfor %}
    """
    result = await service.update_status({{primary_key_param}}, data)
    return success_response(result, message="{{table_comment}}状态更新成功")
{% endif %}


@router.delete(
    "/{{{primary_key_param}}}",
    response_model=SuccessResponse[None],
    summary="删除{{table_comment}}",
)
@handle_service_exceptions
async def delete_{{resource_singular}}(
    {{primary_key_param}}: {{primary_key_type}} = Path(..., description="{{primary_key_comment}}"),
    service: {{class_name}}Service = Depends(get_{{service_name}}),
):
    """删除{{table_comment}}"""
    await service.delete({{primary_key_param}})
    return success_response(None, message="{{table_comment}}删除成功")


# ===== 手写业务路由区（技能重生成内置 CRUD 时保留本区，请勿删除本行标记）=====
# 在此添加自定义端点；业务编排请写在 Service，本层只做 HTTP 编排。
