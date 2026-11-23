package {{package_name}}.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import {{package_name}}.data.local.dao.SkillDao
import {{package_name}}.data.local.entity.SkillEntity

/**
 * 本地数据库。
 *
 * exportSchema = false：不生成 schema json，省掉 schemas 目录；
 * 正式项目建议改为 true 并纳入版本管理。
 */
@Database(
    entities = [SkillEntity::class],
    version = 1,
    exportSchema = false,
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun skillDao(): SkillDao
}
