package com.example.skillswap.feature.root

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import com.example.skillswap.core.datastore.TokenStore
import javax.inject.Inject

/**
 * 根状态：判断是否已登录，决定首个页面。
 *
 * checked = false 时展示启动页，避免闪一下登录页。
 */
data class RootUiState(
    val checked: Boolean = false,
    val loggedIn: Boolean = false,
)

@HiltViewModel
class RootViewModel @Inject constructor(
    tokenStore: TokenStore,
) : ViewModel() {

    val uiState: StateFlow<RootUiState> = tokenStore.token
        .map { token -> RootUiState(checked = true, loggedIn = !token.isNullOrBlank()) }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = RootUiState(),
        )
}
