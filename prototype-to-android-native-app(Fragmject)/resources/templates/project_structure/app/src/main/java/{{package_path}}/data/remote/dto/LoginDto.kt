package {{package_name}}.data.remote.dto

import kotlinx.serialization.Serializable

/** 登录请求体 */
@Serializable
data class LoginRequest(
    val username: String,
    val password: String,
)

/** 登录响应体 */
@Serializable
data class LoginResponse(
    val token: String = "",
    val nickname: String = "",
)
