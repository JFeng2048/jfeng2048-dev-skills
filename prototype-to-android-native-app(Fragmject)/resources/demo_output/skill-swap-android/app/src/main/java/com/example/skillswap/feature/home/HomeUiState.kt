package com.example.skillswap.feature.home

import com.example.skillswap.data.model.Skill

/**
 * 首页状态：不可变，只通过 copy() 更新。
 */
data class HomeUiState(
    /** 首次加载（列表为空时展示整页 Loading） */
    val isLoading: Boolean = false,
    /** 下拉 / 点击刷新（列表已有内容时保留内容） */
    val isRefreshing: Boolean = false,
    /** 上拉加载更多 */
    val isLoadingMore: Boolean = false,
    val skills: List<Skill> = emptyList(),
    val hasMore: Boolean = true,
    val error: String? = null,
)

/** 首页事件：Screen 只能通过它驱动 ViewModel */
sealed interface HomeEvent {
    data object Refresh : HomeEvent
    data object LoadMore : HomeEvent
    data object Retry : HomeEvent
}
