package com.example.skillswap.data.mock

import com.example.skillswap.data.model.Skill

/**
 * Mock 数据：与真实接口同形状，用来在无后端时还原界面与交互。
 *
 * 刻意包含：超长标题、空标签、超长描述，方便暴露布局溢出问题。
 */
object MockData {

    /** 12 条，足够触发两页分页 */
    val skills: List<Skill> = List(12) { index ->
        val i = index + 1
        Skill(
            id = i.toString(),
            title = when (i) {
                1 -> "可以教你吉他入门到弹唱，学期内包会"
                2 -> "Canva 海报设计 / 公众号首图 一对一辅导，含源文件"
                3 -> "Python 数据分析入门（pandas + 可视化）"
                else -> "技能互换 #$i：我教你 X，你教我 Y"
            },
            author = "同学$i",
            avatar = "https://picsum.photos/seed/skill$i/200/200",
            // 第 4 条故意留空标签，验证空态与换行
            tags = if (i == 4) emptyList() else listOf("线下", "周末", "免费"),
            price = if (i % 3 == 0) 0.0 else 30.0 + i,
            description = if (i == 5) {
                "这是一个超长描述的边界用例。".repeat(20)
            } else {
                "可线上或线下，时间灵活，欢迎私聊细聊。"
            },
            createdAt = "2026-11-0${(i % 9) + 1}",
        )
    }

    /** 分页切片，语义与真实接口一致：page 从 0 开始 */
    fun pageSkills(page: Int, pageSize: Int): List<Skill> =
        skills.drop(page * pageSize).take(pageSize)

    fun skillById(id: String): Skill? = skills.find { it.id == id }

    /** mock 登录：用户名非空且密码不少于 6 位即通过 */
    fun login(username: String, password: String): String? =
        if (username.isNotBlank() && password.length >= 6) "mock-token-$username" else null
}
