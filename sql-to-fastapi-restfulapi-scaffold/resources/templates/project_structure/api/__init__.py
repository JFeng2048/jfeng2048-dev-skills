"""API 路由包

Greenfield：导出 api_router；create_app 通过 register_routers 挂载。
按表生成的子路由由脚手架追加到 api/v1/__init__.py。
"""

from typing import Any, Dict, List

from fastapi import FastAPI, APIRouter

from . import v1

api_router = APIRouter()
api_router.include_router(v1.v1_router, prefix="/v1")


def register_routers(app: FastAPI, prefix: str = "/api") -> None:
    """注册全部 API 路由（默认 /api/v1/...）"""
    app.include_router(api_router, prefix=prefix)


def _collect_routes(router: APIRouter, prefix: str = "") -> List[Dict[str, Any]]:
    """递归收集路由信息。

    兼容两种 FastAPI 行为：
    - 0.x：include_router 直接把子路由展开到 routes，path 已含前缀；
    - 1.x：include_router 只追加延迟解析的 _IncludedRouter，需要沿
      original_router + include_context.prefix 递归下钻。
    """
    collected: List[Dict[str, Any]] = []
    for route in getattr(router, "routes", []):
        child = getattr(route, "original_router", None)
        if child is not None and hasattr(child, "routes"):
            context = getattr(route, "include_context", None)
            child_prefix = ""
            if context is not None:
                child_prefix = getattr(context, "prefix", "") or ""
            collected.extend(_collect_routes(child, prefix + child_prefix))
            continue

        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None)
        if path and methods:
            collected.append(
                {
                    "path": prefix + path,
                    "methods": sorted(methods),
                    "name": getattr(route, "name", ""),
                }
            )
    return collected


def get_router_info(prefix: str = "/api") -> Dict[str, Any]:
    """返回已注册路由的简要信息（供 /api/info 调试接口使用）"""
    routes = _collect_routes(api_router, prefix)
    return {"prefix": prefix, "total": len(routes), "routes": routes}


__all__ = ["api_router", "register_routers", "get_router_info"]
