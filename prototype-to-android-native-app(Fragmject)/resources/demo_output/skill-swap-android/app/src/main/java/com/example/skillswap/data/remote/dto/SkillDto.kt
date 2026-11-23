package com.example.skillswap.data.remote.dto

import com.example.skillswap.data.model.Skill
import kotlinx.serialization.Serializable

/** 与后端字段一一对应的传输对象 */
@Serializable
data class SkillDto(
    val id: String,
    val title: String = "",
    val author: String = "",
    val avatar: String = "",
    val tags: List<String> = emptyList(),
    val price: Double = 0.0,
    val description: String = "",
    val createdAt: String = "",
)

/** DTO → 领域模型 */
fun SkillDto.toDomain(): Skill = Skill(
    id = id,
    title = title,
    author = author,
    avatar = avatar,
    tags = tags,
    price = price,
    description = description,
    createdAt = createdAt,
)
