package com.example.skillswap.core.navigation

/**
 * 路由表：所有页面路径集中声明。
 *
 * 约定：
 * - 常量全大写下划线；
 * - 带参数的路由同时提供工厂函数，避免手拼字符串；
 * - 新增页面必须同时在这里与 AppNavHost 注册。
 */
object Routes {
    const val HOME = "home"
    const val MINE = "mine"
    const val LOGIN = "login"

    /** 详情页参数名 */
    const val ARG_SKILL_ID = "skillId"

    /** 详情页占位路由（与 navArgument 的 key 必须一致） */
    const val DETAIL = "detail/{skillId}"

    /** 生成详情页实际路径 */
    fun detail(skillId: String): String = "detail/$skillId"
}
