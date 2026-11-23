package com.example.skillswap.feature.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import com.example.skillswap.core.config.AppConfig
import com.example.skillswap.data.repository.SkillRepository
import javax.inject.Inject

/**
 * 首页 ViewModel：只依赖 Repository，不碰 Compose / Context / Api。
 */
@HiltViewModel
class HomeViewModel @Inject constructor(
    private val repository: SkillRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(HomeUiState(isLoading = true))
    val uiState: StateFlow<HomeUiState> = _uiState.asStateFlow()

    /** 已经成功加载的页数，下一页从 page 开始 */
    private var page = 0

    init {
        refresh()
    }

    fun onEvent(event: HomeEvent) {
        when (event) {
            HomeEvent.Refresh -> refresh()
            HomeEvent.Retry -> refresh()
            HomeEvent.LoadMore -> loadMore()
        }
    }

    private fun refresh() {
        viewModelScope.launch {
            _uiState.update {
                it.copy(
                    isLoading = it.skills.isEmpty(),
                    isRefreshing = it.skills.isNotEmpty(),
                    error = null,
                )
            }

            repository.getSkills(page = 0, pageSize = AppConfig.PAGE_SIZE)
                .onSuccess { list ->
                    page = 1
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            isRefreshing = false,
                            skills = list,
                            hasMore = list.size >= AppConfig.PAGE_SIZE,
                            error = null,
                        )
                    }
                }
                .onFailure { throwable ->
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            isRefreshing = false,
                            error = throwable.message ?: "加载失败，请重试",
                        )
                    }
                }
        }
    }

    private fun loadMore() {
        val current = _uiState.value
        if (current.isLoading || current.isRefreshing || current.isLoadingMore || !current.hasMore) {
            return
        }

        viewModelScope.launch {
            _uiState.update { it.copy(isLoadingMore = true) }

            repository.getSkills(page = page, pageSize = AppConfig.PAGE_SIZE)
                .onSuccess { list ->
                    page += 1
                    _uiState.update {
                        it.copy(
                            isLoadingMore = false,
                            skills = it.skills + list,
                            hasMore = list.size >= AppConfig.PAGE_SIZE,
                        )
                    }
                }
                .onFailure { throwable ->
                    _uiState.update {
                        it.copy(
                            isLoadingMore = false,
                            error = throwable.message ?: "加载更多失败",
                        )
                    }
                }
        }
    }
}
