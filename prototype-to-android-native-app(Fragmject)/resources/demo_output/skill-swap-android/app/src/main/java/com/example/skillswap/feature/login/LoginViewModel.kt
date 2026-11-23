package com.example.skillswap.feature.login

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import com.example.skillswap.core.datastore.TokenStore
import com.example.skillswap.data.repository.AuthRepository
import javax.inject.Inject

/**
 * 登录页 ViewModel：校验 + 调 Repository + 持久化 token。
 */
@HiltViewModel
class LoginViewModel @Inject constructor(
    private val authRepository: AuthRepository,
    private val tokenStore: TokenStore,
) : ViewModel() {

    private val _uiState = MutableStateFlow(LoginUiState())
    val uiState: StateFlow<LoginUiState> = _uiState.asStateFlow()

    fun onUsernameChange(value: String) {
        _uiState.update { it.copy(username = value, error = null) }
    }

    fun onPasswordChange(value: String) {
        _uiState.update { it.copy(password = value, error = null) }
    }

    fun submit() {
        val current = _uiState.value
        if (current.username.isBlank()) {
            _uiState.update { it.copy(error = "请输入账号") }
            return
        }
        if (current.password.length < 6) {
            _uiState.update { it.copy(error = "密码至少 6 位") }
            return
        }

        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }

            authRepository.login(current.username.trim(), current.password)
                .onSuccess { token ->
                    tokenStore.save(token)
                    _uiState.update { it.copy(isLoading = false, loggedIn = true) }
                }
                .onFailure { throwable ->
                    _uiState.update {
                        it.copy(isLoading = false, error = throwable.message ?: "登录失败")
                    }
                }
        }
    }
}
