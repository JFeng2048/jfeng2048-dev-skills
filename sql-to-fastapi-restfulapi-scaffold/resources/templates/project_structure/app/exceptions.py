"""异常处理器配置"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from config import settings
from utils.logger import get_logger, log_security_event
from utils.custom_exceptions import BaseAPIException
from schemas.response import ErrorResponse, ValidationErrorDetail, ValidationErrorResponse
from utils.response_code import RET, get_message, HTTP_STATUS_TO_BIZ_CODE

logger = get_logger(__name__)


def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BaseAPIException)
    async def api_exception_handler(request: Request, exc: BaseAPIException):
        log_security_event(
            "API_EXCEPTION",
            details={
                "exception_type": exc.__class__.__name__,
                "message": exc.detail,
                "path": str(request.url.path),
                "method": request.method,
            },
        )
        body = ErrorResponse(
            code=exc.code,
            message=exc.detail or get_message(exc.code, exc.lang),
            success=False,
            data=None,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=body.model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"][1:])
            errors.append(
                ValidationErrorDetail(
                    field=field,
                    message=error["msg"],
                    value=error.get("input"),
                )
            )
        logger.warning("Validation error path=%s", request.url.path)
        body = ValidationErrorResponse(
            data=errors, code=RET.PARAMERR, message="数据验证失败", success=False
        )
        return JSONResponse(status_code=422, content=body.model_dump())

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        if exc.status_code == 404:
            code = RET.URLNOTFOUND
        elif exc.status_code == 405:
            code = RET.REQERR
        elif exc.status_code >= 500:
            code = RET.INTERNALERR
        else:
            code = HTTP_STATUS_TO_BIZ_CODE.get(exc.status_code, RET.PARAMERR)
        body = ErrorResponse(
            code=code,
            message=str(exc.detail) if exc.detail else get_message(code),
            success=False,
            data=None,
        )
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        log_security_event(
            "UNHANDLED_EXCEPTION",
            details={
                "exception_type": exc.__class__.__name__,
                "message": str(exc),
                "path": str(request.url.path),
                "method": request.method,
            },
        )
        detail = str(exc) if settings.debug else "服务器内部错误"
        body = ErrorResponse(
            code=RET.INTERNALERR,
            message=detail,
            success=False,
            data=None,
        )
        return JSONResponse(status_code=500, content=body.model_dump())
