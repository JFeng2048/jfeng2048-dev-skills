"""认证 / 授权依赖（无状态 JWT 主体，不依赖任何业务表或角色枚举）

JWT 载荷约定（全部可选，缺省为空）：
- ``sub``：主体唯一标识
- ``username``：显示名
- ``roles``：角色标识列表（如 ``["admin"]``，具体取值由项目自定）
- ``permissions``：权限标识列表（如 ``["order:read"]``）
- ``status``：1 启用 / 0 禁用

统一入口：
- ``get_current_user``：验 JWT 后返回 CurrentUser 主体（由载荷推导，不查库）
- ``get_current_active_user``：在启用态校验之后放行
- ``require_roles(*roles)``：命中任一角色即放行
- ``require_permission(perm)``：具备指定权限才放行
- ``require_admin``：``require_roles("admin")`` 的便捷写法

本层**不假定数据库中存在任何用户 / 身份表**，角色与权限完全来自 token 载荷。
若需要「查库校验用户状态 / 读取更多资料」等强一致逻辑，可在此文件自行扩展，
不影响骨架其余部分。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from utils.auth import jwt_authenticator
from utils.custom_exceptions import AuthenticationException, AuthorizationException
from utils.logger import log_security_event

security = HTTPBearer()

# 管理员角色的默认标识；仅作便捷约定，项目可改成自己的角色名
ADMIN_ROLE = "admin"


@dataclass
class CurrentUser:
    """无状态 JWT 主体（由 token 载荷推导，不绑定数据库表）。"""

    user_id: str
    username: str = ""
    status: int = 1
    roles: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)

    @property
    def is_active(self) -> bool:
        return self.status == 1

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def has_any_role(self, roles: List[str]) -> bool:
        return bool(set(roles) & set(self.roles))

    def has_permission(self, perm: str) -> bool:
        return perm in self.permissions


class PermissionChecker:
    """权限检查器（通用规则，基于 CurrentUser 主体）。"""

    @staticmethod
    def check_resource_access(
        current_user: CurrentUser,
        resource_owner_id: str,
        resource_type: str = "general",
    ) -> bool:
        """管理员或资源归属人可访问；其余拒绝并记录审计事件。"""
        if current_user.has_role(ADMIN_ROLE):
            return True
        if current_user.user_id == resource_owner_id:
            return True
        log_security_event(
            "UNAUTHORIZED_RESOURCE_ACCESS",
            user_id=current_user.user_id,
            details={
                "resource_owner": resource_owner_id,
                "resource_type": resource_type,
                "roles": current_user.roles,
            },
        )
        return False

    @staticmethod
    def check_roles(current_user: CurrentUser, roles: List[str]) -> bool:
        """命中任一角色即通过。"""
        if current_user.has_any_role(roles):
            return True
        log_security_event(
            "ROLE_PERMISSION_DENIED",
            user_id=current_user.user_id,
            details={"required_roles": roles, "roles": current_user.roles},
        )
        return False

    @staticmethod
    def check_permission(current_user: CurrentUser, permission: str) -> bool:
        """具备指定权限才通过。"""
        if current_user.has_permission(permission):
            return True
        log_security_event(
            "PERMISSION_DENIED",
            user_id=current_user.user_id,
            details={
                "required_permission": permission,
                "permissions": current_user.permissions,
            },
        )
        return False


def _as_str_list(value) -> List[str]:
    """把 JWT 中的 roles / permissions 归一化成字符串列表。"""
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value]


def _build_current_user(payload: dict) -> CurrentUser:
    """从 JWT 载荷构造无状态主体（不查库）。"""
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationException("令牌中缺少用户信息")
    raw_status = payload.get("status")
    return CurrentUser(
        user_id=str(user_id),
        username=str(payload.get("username", "") or ""),
        status=int(raw_status) if raw_status is not None else 1,
        roles=_as_str_list(payload.get("roles")),
        permissions=_as_str_list(payload.get("permissions")),
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    """从 Bearer Token 推导无状态 CurrentUser 主体（不查询数据库）。"""
    try:
        payload = jwt_authenticator.verify_token(credentials.credentials)
        user = _build_current_user(payload)
        if not user.is_active:
            log_security_event(
                "INACTIVE_USER_ACCESS",
                user_id=user.user_id,
                details={"status": user.status},
            )
            raise AuthenticationException("用户账号已被禁用")
        return user
    except AuthenticationException:
        raise
    except Exception as exc:
        log_security_event("AUTHENTICATION_ERROR", details={"error": str(exc)})
        raise AuthenticationException("身份验证失败") from exc


async def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    if not current_user.is_active:
        raise AuthenticationException("用户账号已被禁用")
    return current_user


async def require_admin(
    current_user: CurrentUser = Depends(get_current_active_user),
) -> CurrentUser:
    if not current_user.has_role(ADMIN_ROLE):
        log_security_event(
            "ADMIN_PERMISSION_DENIED",
            user_id=current_user.user_id,
            details={"roles": current_user.roles},
        )
        raise AuthorizationException("需要管理员权限")
    return current_user


def require_roles(*roles: str):
    """返回「命中任一角色即放行」的 Depends 可调用对象。"""
    required = list(roles)

    async def _dependency(
        current_user: CurrentUser = Depends(get_current_active_user),
    ) -> CurrentUser:
        if not PermissionChecker.check_roles(current_user, required):
            raise AuthorizationException("当前角色无权访问")
        return current_user

    return _dependency


def require_permission(permission: str):
    """返回「具备指定权限才放行」的 Depends 可调用对象。"""

    async def _dependency(
        current_user: CurrentUser = Depends(get_current_active_user),
    ) -> CurrentUser:
        if not PermissionChecker.check_permission(current_user, permission):
            raise AuthorizationException("当前账号缺少所需权限")
        return current_user

    return _dependency


def check_resource_ownership(resource_owner_id: str, resource_type: str = "general"):
    """返回校验资源归属的 Depends 可调用对象。"""

    async def _dependency(
        current_user: CurrentUser = Depends(get_current_active_user),
    ) -> CurrentUser:
        if not PermissionChecker.check_resource_access(
            current_user, resource_owner_id, resource_type
        ):
            raise AuthorizationException("您无权访问此资源")
        return current_user

    return _dependency
