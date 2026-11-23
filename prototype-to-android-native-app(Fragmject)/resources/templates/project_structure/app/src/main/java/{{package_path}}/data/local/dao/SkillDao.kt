package {{package_name}}.data.local.dao

import androidx.room.Dao
import androidx.room.Query
import androidx.room.Upsert
import {{package_name}}.data.local.entity.SkillEntity

/** 技能本地缓存 */
@Dao
interface SkillDao {

    @Query("SELECT * FROM skills ORDER BY sortIndex ASC")
    suspend fun getAll(): List<SkillEntity>

    @Upsert
    suspend fun upsertAll(items: List<SkillEntity>)

    @Query("DELETE FROM skills")
    suspend fun clear()
}
