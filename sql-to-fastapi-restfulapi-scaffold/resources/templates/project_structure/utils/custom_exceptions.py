"""自定义异常模块（与具体业务解耦）

约定：
- 只依赖通用响应码 `utils.response_code.RET` 与 `get_message`，不含任何业务码。
- 需要业务错误码时，先把常量追加到 `utils.response_code.BusinessCode`（并补中英文文案），
  再用 `BusinessException(code=BusinessCode.XXX, detail="...")` 抛出。
- 异常同时携带响应码（body.code）与 HTTP 状态码（status_code），由 `app.exceptions` 统一渲染。
"""

from typing import Optional, Any

from utils.response_code import RET, get_message


class BaseAPIException(Exception):
    """API 基础异常：响应码 + HTTP 状态码 + 提示 + 数据。"""

    def __init__(
        self,
        code: int = RET.INTERNALERR,
        status_code: int = 500,
        detail: Optional[str] = None,
        data: Optional[Any] = None,
        lang: str = "CN",
    ):
        self.code = code
        self.status_code = status_code
        self.lang = lang
        self.detail = detail or get_message(code, lang)
        self.data = data
        super().__init__(self.detail)


class AuthenticationException(BaseAPIException):
    """认证异常"""

    def __init__(
        self,
        detail: Optional[str] = None,
        data: Optional[Any] = None,
        lang: str = "CN",
    ):
        super().__init__(
            code=RET.SESSIONERR,
            status_code=401,
            detail=detail,
            data=data,
            lang=lang,
        )


class AuthorizationException(BaseAPIException):
    """授权异常"""

    def __init__(
        self,
        detail: Optional[str] = None,
        data: Optional[Any] = None,
        lang: str = "CN",
    ):
        super().__init__(
            code=RET.ROLEERR,
            status_code=403,
            detail=detail,
            data=data,
            lang=lang,
        )


class ValidationException(BaseAPIException):
    """验证异常"""

    def __init__(
        self,
        detail: Optional[str] = None,
        data: Optional[Any] = None,
        lang: str = "CN",
    ):
        super().__init__(
            code=RET.PARAMERR,
            status_code=422,
            detail=detail,
            data=data,
            lang=lang,
        )


class NotFoundException(BaseAPIException):
    """资源不存在异常"""

    def __init__(
        self,
        detail: Optional[str] = None,
        data: Optional[Any] = None,
        lang: str = "CN",
    ):
        super().__init__(
            code=RET.URLNOTFOUND,
            status_code=404,
            detail=detail,
            data=data,
            lang=lang,
        )


class ConflictException(BaseAPIException):
    """资源冲突异常"""

    def __init__(
        self,
        detail: Optional[str] = None,
        data: Optional[Any] = None,
        lang: str = "CN",
    ):
        super().__init__(
            code=RET.DATAEXIST,
            status_code=409,
            detail=detail,
            data=data,
            lang=lang,
        )


class RateLimitException(BaseAPIException):
    """速率限制异常"""

    def __init__(
        self,
        detail: Optional[str] = None,
        data: Optional[Any] = None,
        lang: str = "CN",
    ):
        super().__init__(
            code=RET.REQERR,
            status_code=429,
            detail=detail,
            data=data,
            lang=lang,
        )


class BusinessException(BaseAPIException):
    """业务异常

    code 默认 `RET.DATAERR`；业务码请使用 `BusinessCode` 中登记的常量。
    """

    def __init__(
        self,
        code: int = RET.DATAERR,
        detail: Optional[str] = None,
        data: Optional[Any] = None,
        status_code: int = 400,
        lang: str = "CN",
    ):
        super().__init__(
            code=code,
            status_code=status_code,
            detail=detail,
            data=data,
            lang=lang,
        )


class DatabaseException(BaseAPIException):
    """数据库异常"""

    def __init__(
        self,
        detail: Optional[str] = None,
        data: Optional[Any] = None,
        lang: str = "CN",
    ):
        super().__init__(
            code=RET.DBERR,
            status_code=500,
            detail=detail,
            data=data,
            lang=lang,
        )


class ResourceNotOwnedException(BaseAPIException):
    """资源不属于当前用户异常 - 防止对象级别授权失效"""

    def __init__(
        self,
        detail: Optional[str] = None,
        data: Optional[Any] = None,
        lang: str = "CN",
    ):
        super().__init__(
            code=RET.ROLEERR,
            status_code=403,
            detail=detail,
            data=data,
            lang=lang,
        )


# ================ 通用身份 / 数据异常 ================

class UserException(BaseAPIException):
    """身份相关异常基类"""
    pass


class UserNotFoundException(UserException):
    """用户不存在异常"""

    def __init__(self, detail: Optional[str] = None, data: Optional[Any] = None):
        super().__init__(code=RET.USERERR, status_code=404, detail=detail, data=data)


class InvalidPasswordException(UserException):
    """密码错误异常"""

    def __init__(self, detail: Optional[str] = None, data: Optional[Any] = None):
        super().__init__(code=RET.PWDERR, status_code=400, detail=detail, data=data)


class UserDisabledException(UserException):
    """用户已禁用异常"""

    def __init__(self, detail: Optional[str] = None, data: Optional[Any] = None):
        super().__init__(code=RET.USERERR, status_code=403, detail=detail, data=data)


class TokenException(BaseAPIException):
    """令牌相关异常基类"""
    pass


class TokenExpiredException(TokenException):
    """令牌过期异常"""

    def __init__(self, detail: Optional[str] = None, data: Optional[Any] = None):
        super().__init__(code=RET.SESSIONERR, status_code=401, detail=detail, data=data)


class InvalidTokenException(TokenException):
    """无效令牌异常"""

    def __init__(self, detail: Optional[str] = None, data: Optional[Any] = None):
        super().__init__(code=RET.SESSIONERR, status_code=401, detail=detail, data=data)


class DataException(BaseAPIException):
    """数据相关异常基类"""
    pass


class DataNotFoundException(DataException):
    """数据不存在异常"""

    def __init__(self, detail: Optional[str] = None, data: Optional[Any] = None):
        super().__init__(code=RET.URLNOTFOUND, status_code=404, detail=detail, data=data)


class DataAlreadyExistsException(DataException):
    """数据已存在异常"""

    def __init__(self, detail: Optional[str] = None, data: Optional[Any] = None):
        super().__init__(code=RET.DATAEXIST, status_code=409, detail=detail, data=data)


class DataValidationException(DataException):
    """数据验证异常"""

    def __init__(self, detail: Optional[str] = None, data: Optional[Any] = None):
        super().__init__(code=RET.PARAMERR, status_code=422, detail=detail, data=data)


# ================ 异常快捷创建函数 ================

def raise_user_not_found(detail: str = "用户不存在") -> None:
    """抛出用户不存在异常"""
    raise UserNotFoundException(detail)


def raise_invalid_password(detail: str = "密码错误") -> None:
    """抛出密码错误异常"""
    raise InvalidPasswordException(detail)


def raise_token_expired(detail: str = "令牌已过期") -> None:
    """抛出令牌过期异常"""
    raise TokenExpiredException(detail)


def raise_permission_denied(detail: str = "权限不足") -> None:
    """抛出权限不足异常"""
    raise AuthorizationException(detail)


def raise_data_not_found(detail: str = "数据不存在") -> None:
    """抛出数据不存在异常"""
    raise DataNotFoundException(detail)


def raise_validation_error(detail: str = "数据验证失败") -> None:
    """抛出数据验证异常"""
    raise ValidationException(detail)


# 便捷的异常抛出函数
def raise_not_found(message: str = "资源不存在"):
    """抛出未找到异常"""
    raise DataNotFoundException(message)


def raise_bad_request(message: str = "请求参数错误"):
    """抛出请求错误异常"""
    raise BusinessException(RET.PARAMERR, detail=message, status_code=400)


def raise_forbidden(message: str = "权限不足"):
    """抛出权限异常"""
    raise AuthorizationException(message)


def raise_unauthorized(message: str = "认证失败"):
    """抛出认证异常"""
    raise AuthenticationException(message)


# ================ 异常装饰器 ================

from functools import wraps
import logging


def handle_exceptions(
    default_message: str = "操作失败",
    log_errors: bool = True
):
    """异常处理装饰器"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except BaseAPIException:
                # 业务异常直接重新抛出
                raise
            except Exception as e:
                if log_errors:
                    logging.error(f"函数 {func.__name__} 发生未处理异常: {str(e)}")
                # 将未知异常转换为业务异常
                raise BusinessException(
                    code=RET.INTERNALERR,
                    detail=default_message,
                    status_code=500,
                )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BaseAPIException:
                raise
            except Exception as e:
                if log_errors:
                    logging.error(f"函数 {func.__name__} 发生未处理异常: {str(e)}")
                raise BusinessException(
                    code=RET.INTERNALERR,
                    detail=default_message,
                    status_code=500,
                )

        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def handle_service_exceptions(func):
    """服务层异常处理装饰器"""
    from functools import wraps
    import inspect

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except BaseAPIException:
            raise
        except Exception as e:
            raise BusinessException(
                code=RET.INTERNALERR,
                detail=f"服务异常: {str(e)}",
                status_code=500,
            )

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BaseAPIException:
            raise
        except Exception as e:
            raise BusinessException(
                code=RET.INTERNALERR,
                detail=f"服务异常: {str(e)}",
                status_code=500,
            )

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
