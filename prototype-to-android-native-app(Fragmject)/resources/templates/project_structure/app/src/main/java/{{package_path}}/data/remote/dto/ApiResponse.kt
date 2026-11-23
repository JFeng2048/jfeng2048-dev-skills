package {{package_name}}.data.remote.dto

import kotlinx.serialization.Serializable

/**
 * 统一响应体：{ "code": 0, "message": "ok", "data": ... }
 *
 * 后端约定不一致时，只改这个类 + Repository 的解包逻辑。
 */
@Serializable
data class ApiResponse<T>(
    val code: Int = 0,
    val message: String = "",
    val data: T? = null,
)
