package com.example.skillswap.data.model

/**
 * 领域模型（UI 与业务只认这个类型，不直接用 DTO / Entity）。
 */
data class Skill(
    val id: String,
    val title: String,
    val author: String,
    val avatar: String,
    val tags: List<String>,
    val price: Double,
    val description: String,
    val createdAt: String,
) {
    /** 价格展示文案：0 元显示「免费」 */
    val priceText: String
        get() = if (price <= 0.0) "免费" else "¥%.2f".format(price)
}
