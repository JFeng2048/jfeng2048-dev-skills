package {{package_name}}.data.repository

import {{package_name}}.core.common.safeResult
import {{package_name}}.core.config.AppConfig
import {{package_name}}.data.mock.MockData
import {{package_name}}.data.remote.AuthApi
import {{package_name}}.data.remote.dto.LoginRequest
import kotlinx.coroutines.delay
import javax.inject.Inject
import javax.inject.Singleton

/** 认证数据接缝 */
interface AuthRepository {
    /** 成功返回 token，失败返回 Result.failure */
    suspend fun login(username: String, password: String): Result<String>
}

@Singleton
class AuthRepositoryImpl @Inject constructor(
    private val api: AuthApi,
) : AuthRepository {

    override suspend fun login(username: String, password: String): Result<String> = safeResult {
        if (AppConfig.USE_MOCK) {
            delay(400)
            return@safeResult MockData.login(username, password)
                ?: error("账号或密码不正确（mock：密码至少 6 位）")
        }

        val response = api.login(LoginRequest(username = username, password = password))
        if (response.code != 0) {
            error(response.message.ifBlank { "登录失败" })
        }
        response.data?.token?.takeIf { it.isNotBlank() } ?: error("登录失败：token 为空")
    }
}
