#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""统一响应码定义（支持中英文文案）。

设计约定：
- 本文件只保留**通用 / HTTP 服务级**响应码，不预置任何具体业务码。
- `RET`：通用 / HTTP 类响应码（成功、参数、认证、权限、限流、数据库、内部错误等）。
- `BusinessCode`：业务响应码扩展位（默认空）。生成目标项目后，若 SQL 脚本或需求中
  出现业务错误码，统一追加到此处，并同步补充 `error_map_CN` / `error_map_EN`。
- `BizCode`：`BusinessCode` 的别名。
- 业务代码中禁止散落魔法数字，统一引用上述常量；取文案统一走 `get_message(code, lang)`。
"""

from typing import Dict


class RET:
    """通用 / HTTP 服务级响应码（整数，4 位）。"""

    OK = 2000
    NODATA = 2001
    DATAEXIST = 2002
    DATAERR = 2003
    PARAMERR = 4000
    SESSIONERR = 4001
    LOGINERR = 4002
    USERERR = 4003
    ROLEERR = 4004
    PWDERR = 4005
    REQERR = 4006
    IPERR = 4007
    URLNOTFOUND = 4040
    INTERNALERR = 5000
    DBERR = 5001
    THIRDERR = 5002
    IOERR = 5003
    UNKOWNERR = 5004
    # 安全防护中间件
    INVALID_REQUEST = 4008
    INTERNAL_ERROR = 5005


class BusinessCode:
    """
    业务响应码扩展位（默认空）。

    约定：
    - 4xxx 客户端业务错误（参数 / 业务校验失败）
    - 5xxx 服务端业务错误（依赖故障 / 落库失败）

    新增业务码时：
    1. 在本类集中追加常量，禁止在业务代码里散落魔法数字；
    2. 同步在 `error_map_CN` 与 `error_map_EN` 补对应文案；
    3. 业务代码通过 `BusinessException(BusinessCode.XXX)` 抛出。
    """

    @classmethod
    def message(cls, code: int, lang: str = "CN") -> str:
        """返回响应码对应描述；未登记返回空串。"""
        return get_message(code, lang)


# 便于直接 `from utils.response_code import BizCode`
BizCode = BusinessCode


error_map_CN: Dict[int, str] = {
    RET.OK: u"成功",
    RET.NODATA: u"无数据",
    RET.DATAEXIST: u"数据已存在",
    RET.DATAERR: u"数据错误",
    RET.PARAMERR: u"参数错误",
    RET.SESSIONERR: u"用户未登录",
    RET.LOGINERR: u"用户登录失败",
    RET.USERERR: u"用户不存在或未激活",
    RET.ROLEERR: u"用户身份错误",
    RET.PWDERR: u"密码错误",
    RET.REQERR: u"非法请求或请求次数受限",
    RET.IPERR: u"IP受限",
    RET.URLNOTFOUND: u"资源不存在",
    RET.INTERNALERR: u"服务器内部错误",
    RET.DBERR: u"数据库查询错误",
    RET.THIRDERR: u"第三方系统错误",
    RET.IOERR: u"文件读写错误",
    RET.UNKOWNERR: u"未知错误",
    RET.INVALID_REQUEST: u"请求被安全防护拦截",
    RET.INTERNAL_ERROR: u"服务器内部错误",
}

error_map_EN: Dict[int, str] = {
    RET.OK: "successfully!",
    RET.NODATA: "no data!",
    RET.DATAEXIST: "data exist!",
    RET.DATAERR: "data error!",
    RET.PARAMERR: "parameter error!",
    RET.SESSIONERR: "user not logged in!",
    RET.LOGINERR: "user login failed!",
    RET.USERERR: "user does not exist or not activation! ",
    RET.ROLEERR: "user role error!",
    RET.PWDERR: "password error!",
    RET.REQERR: "illegal request or limited number of requests",
    RET.IPERR: "IP restricted!",
    RET.URLNOTFOUND: "resource not found!",
    RET.INTERNALERR: "Internal Server Error!",
    RET.DBERR: "database query error",
    RET.THIRDERR: "third party system error",
    RET.IOERR: "file read or write error!",
    RET.UNKOWNERR: "unknown error!",
    RET.INVALID_REQUEST: "request blocked by security protection!",
    RET.INTERNAL_ERROR: "Internal Server Error!",
}

_MESSAGE_MAPS: Dict[str, Dict[int, str]] = {
    "CN": error_map_CN,
    "EN": error_map_EN,
}


def get_message(code: int, lang: str = "CN") -> str:
    """返回响应码描述。

    Args:
        code: 响应码（RET 或 BusinessCode 常量）。
        lang: 语言，支持 ``CN`` / ``EN``；未知值回退到中文。
    """
    return _MESSAGE_MAPS.get((lang or "CN").upper(), error_map_CN).get(code, "")


# HTTP 状态码 -> 通用响应码（用于 StarletteHTTPException 等非自定义异常的响应体 code）
HTTP_STATUS_TO_BIZ_CODE: Dict[int, int] = {
    400: RET.PARAMERR,
    401: RET.SESSIONERR,
    403: RET.ROLEERR,
    404: RET.URLNOTFOUND,
    405: RET.REQERR,
    409: RET.DATAEXIST,
    422: RET.PARAMERR,
    429: RET.REQERR,
    500: RET.INTERNALERR,
    502: RET.THIRDERR,
    503: RET.INTERNALERR,
    504: RET.THIRDERR,
}
