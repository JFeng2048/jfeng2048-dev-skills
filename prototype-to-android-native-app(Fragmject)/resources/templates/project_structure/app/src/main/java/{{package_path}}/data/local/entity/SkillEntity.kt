package {{package_name}}.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import {{package_name}}.data.model.Skill

/**
 * Room 表：skills。
 *
 * 注意 tags 以逗号拼接存储，避免为 List<String> 引入 TypeConverter。
 * 字段变了要升 version 并写迁移，或者用 fallbackToDestructiveMigration（仅开发期）。
 */
@Entity(tableName = "skills")
data class SkillEntity(
    @PrimaryKey val id: String,
    val title: String,
    val author: String,
    val avatar: String,
    val tags: String,
    val price: Double,
    val description: String,
    val createdAt: String,
    val sortIndex: Int,
)

fun SkillEntity.toDomain(): Skill = Skill(
    id = id,
    title = title,
    author = author,
    avatar = avatar,
    tags = tags.split(",").filter { it.isNotBlank() },
    price = price,
    description = description,
    createdAt = createdAt,
)

fun Skill.toEntity(sortIndex: Int): SkillEntity = SkillEntity(
    id = id,
    title = title,
    author = author,
    avatar = avatar,
    tags = tags.joinToString(","),
    price = price,
    description = description,
    createdAt = createdAt,
    sortIndex = sortIndex,
)
