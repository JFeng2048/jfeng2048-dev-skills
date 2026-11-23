package {{package_name}}.feature.mine

/** 我的页面状态 */
data class MineUiState(
    val nickname: String = "同学",
    val isLoading: Boolean = false,
    /** 已退出登录，Screen 观察到后回调导航 */
    val loggedOut: Boolean = false,
)
