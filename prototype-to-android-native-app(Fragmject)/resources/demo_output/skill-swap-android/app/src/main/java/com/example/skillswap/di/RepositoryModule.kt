package com.example.skillswap.di

import com.example.skillswap.data.repository.AuthRepository
import com.example.skillswap.data.repository.AuthRepositoryImpl
import com.example.skillswap.data.repository.SkillRepository
import com.example.skillswap.data.repository.SkillRepositoryImpl
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

/**
 * 接口绑定：ViewModel 只注入接口，方便替换实现与写单测。
 */
@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {

    @Binds
    @Singleton
    abstract fun bindSkillRepository(impl: SkillRepositoryImpl): SkillRepository

    @Binds
    @Singleton
    abstract fun bindAuthRepository(impl: AuthRepositoryImpl): AuthRepository
}
