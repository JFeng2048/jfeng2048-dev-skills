package com.example.skillswap.feature.detail

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import com.example.skillswap.core.navigation.Routes
import com.example.skillswap.data.repository.SkillRepository
import javax.inject.Inject

/**
 * 详情页 ViewModel。
 *
 * 路由参数通过 SavedStateHandle 获取，不要在 Screen 里取 arguments 再传进来。
 */
@HiltViewModel
class DetailViewModel @Inject constructor(
    private val repository: SkillRepository,
    savedStateHandle: SavedStateHandle,
) : ViewModel() {

    private val skillId: String = savedStateHandle.get<String>(Routes.ARG_SKILL_ID).orEmpty()

    private val _uiState = MutableStateFlow(DetailUiState())
    val uiState: StateFlow<DetailUiState> = _uiState.asStateFlow()

    init {
        load()
    }

    fun retry() {
        load()
    }

    private fun load() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }

            repository.getSkillDetail(skillId)
                .onSuccess { skill ->
                    _uiState.update { it.copy(isLoading = false, skill = skill, error = null) }
                }
                .onFailure { throwable ->
                    _uiState.update {
                        it.copy(isLoading = false, error = throwable.message ?: "加载失败")
                    }
                }
        }
    }
}
