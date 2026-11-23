package com.example.skillswap.feature.detail

import com.example.skillswap.data.model.Skill

/** 详情页状态 */
data class DetailUiState(
    val isLoading: Boolean = true,
    val skill: Skill? = null,
    val error: String? = null,
)
