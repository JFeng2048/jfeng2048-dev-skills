package com.example.skillswap.data.repository

import com.example.skillswap.core.common.safeResult
import com.example.skillswap.core.config.AppConfig
import com.example.skillswap.data.local.dao.SkillDao
import com.example.skillswap.data.local.entity.toDomain as entityToDomain
import com.example.skillswap.data.local.entity.toEntity
import com.example.skillswap.data.mock.MockData
import com.example.skillswap.data.model.Skill
import com.example.skillswap.data.remote.SkillApi
import com.example.skillswap.data.remote.dto.toDomain as dtoToDomain
import kotlinx.coroutines.delay
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 数据接缝：UI 只依赖这个接口。
 * 页面 / ViewModel 不允许直接使用 SkillApi 或 SkillDao。
 */
interface SkillRepository {
    suspend fun getSkills(page: Int, pageSize: Int): Result<List<Skill>>
    suspend fun getSkillDetail(id: String): Result<Skill>
}

@Singleton
class SkillRepositoryImpl @Inject constructor(
    private val api: SkillApi,
    private val dao: SkillDao,
) : SkillRepository {

    /**
     * 列表：mock 与真实分支；真实分支成功后写本地缓存，失败时用缓存兜底。
     */
    override suspend fun getSkills(page: Int, pageSize: Int): Result<List<Skill>> =
        safeResult {
            if (AppConfig.USE_MOCK) {
                delay(300) // 模拟网络延迟，让 Loading 态可见
                return@safeResult MockData.pageSkills(page, pageSize)
            }

            val response = api.getSkills(page = page, pageSize = pageSize)
            if (response.code != 0) {
                error(response.message.ifBlank { "接口返回异常" })
            }
            val remote = response.data.orEmpty().map { it.dtoToDomain() }

            // 首页数据覆盖式写入，后续页追加，保证顺序与 sortIndex 一致
            if (page == 0) dao.clear()
            dao.upsertAll(remote.mapIndexed { index, skill -> skill.toEntity(page * pageSize + index) })
            remote
        }.recoverCatching { error ->
            // 仅首页回落到缓存，避免分页拼接错乱
            if (page == 0) {
                val cached = dao.getAll().map { it.entityToDomain() }
                if (cached.isNotEmpty()) return@recoverCatching cached
            }
            throw error
        }

    override suspend fun getSkillDetail(id: String): Result<Skill> = safeResult {
        if (AppConfig.USE_MOCK) {
            delay(200)
            return@safeResult MockData.skillById(id) ?: error("内容不存在或已下架")
        }

        val response = api.getSkillDetail(id)
        if (response.code != 0) {
            error(response.message.ifBlank { "接口返回异常" })
        }
        response.data?.dtoToDomain() ?: error("数据为空")
    }
}
