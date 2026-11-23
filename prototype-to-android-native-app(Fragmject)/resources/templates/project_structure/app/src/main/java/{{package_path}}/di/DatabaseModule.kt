package {{package_name}}.di

import android.content.Context
import androidx.room.Room
import {{package_name}}.data.local.AppDatabase
import {{package_name}}.data.local.dao.SkillDao
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

/**
 * 本地数据库模块。
 * fallbackToDestructiveMigration 仅用于开发期；上线请写 Migration。
 */
@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): AppDatabase =
        Room.databaseBuilder(context, AppDatabase::class.java, "app.db")
            .fallbackToDestructiveMigration()
            .build()

    @Provides
    fun provideSkillDao(database: AppDatabase): SkillDao = database.skillDao()
}
