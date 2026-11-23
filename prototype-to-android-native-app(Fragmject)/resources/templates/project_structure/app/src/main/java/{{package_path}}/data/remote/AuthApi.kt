package {{package_name}}.data.remote

import {{package_name}}.data.remote.dto.ApiResponse
import {{package_name}}.data.remote.dto.LoginRequest
import {{package_name}}.data.remote.dto.LoginResponse
import retrofit2.http.Body
import retrofit2.http.POST

/** 认证接口 */
interface AuthApi {

    @POST("api/auth/login")
    suspend fun login(@Body body: LoginRequest): ApiResponse<LoginResponse>
}
