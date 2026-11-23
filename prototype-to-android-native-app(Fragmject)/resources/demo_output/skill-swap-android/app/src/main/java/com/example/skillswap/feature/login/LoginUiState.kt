package com.example.skillswap.feature.login

/** 登录页状态 */
data class LoginUiState(
    val username: String = "",
    val password: String = "",
    val isLoading: Boolean = false,
    val error: String? = null,
    /** 登录成功标记，Screen 观察到后回调跳转 */
    val loggedIn: Boolean = false,
) {
    /** 简单校验：账号非空 + 密码不少于 6 位 */
    val canSubmit: Boolean
        get() = username.isNotBlank() && password.length >= 6 && !isLoading
}
