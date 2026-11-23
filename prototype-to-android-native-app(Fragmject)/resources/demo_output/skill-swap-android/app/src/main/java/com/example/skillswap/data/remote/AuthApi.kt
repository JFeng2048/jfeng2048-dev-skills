package com.example.skillswap.data.remote

import com.example.skillswap.data.remote.dto.ApiResponse
import com.example.skillswap.data.remote.dto.LoginRequest
import com.example.skillswap.data.remote.dto.LoginResponse
import retrofit2.http.Body
import retrofit2.http.POST

/** 认证接口 */
interface AuthApi {

    @POST("api/auth/login")
    suspend fun login(@Body body: LoginRequest): ApiResponse<LoginResponse>
}
