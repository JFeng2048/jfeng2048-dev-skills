package {{package_name}}.feature.mine

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import {{package_name}}.core.datastore.TokenStore
import javax.inject.Inject

/**
 * 我的页面 ViewModel：目前只负责退出登录。
 * 后续接入用户信息接口时，在这里加 loadProfile()。
 */
@HiltViewModel
class MineViewModel @Inject constructor(
    private val tokenStore: TokenStore,
) : ViewModel() {

    private val _uiState = MutableStateFlow(MineUiState())
    val uiState: StateFlow<MineUiState> = _uiState.asStateFlow()

    fun logout() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            tokenStore.clear()
            _uiState.update { it.copy(isLoading = false, loggedOut = true) }
        }
    }
}
