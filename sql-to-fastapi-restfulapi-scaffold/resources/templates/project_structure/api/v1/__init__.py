"""API v1 路由包

脚手架生成表模块后，在此追加：
    from api.v1.xxx import router as xxx_router
    v1_router.include_router(xxx_router)
"""

from fastapi import APIRouter

v1_router = APIRouter()

# ---- 脚手架追加区 ----
# from api.v1.{{first_resource}} import router as {{class_name}}Router
# v1_router.include_router({{class_name}}Router)

__all__ = ["v1_router"]
