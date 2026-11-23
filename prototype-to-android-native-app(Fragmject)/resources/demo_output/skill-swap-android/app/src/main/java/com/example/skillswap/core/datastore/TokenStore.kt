package com.example.skillswap.core.datastore

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

/** DataStore 实例必须全局唯一，因此用扩展属性声明在文件级 */
private val Context.appDataStore: DataStore<Preferences> by preferencesDataStore(name = "app_prefs")

/**
 * 登录态存储。
 *
 * 只存 token，不要在这里塞业务数据；业务数据走 Room。
 */
@Singleton
class TokenStore @Inject constructor(
    @ApplicationContext private val context: Context,
) {

    private val tokenKey = stringPreferencesKey("access_token")

    /** token 流，未登录时为 null */
    val token: Flow<String?> = context.appDataStore.data.map { it[tokenKey] }

    suspend fun save(token: String) {
        context.appDataStore.edit { it[tokenKey] = token }
    }

    suspend fun clear() {
        context.appDataStore.edit { it.remove(tokenKey) }
    }

    /** 供 OkHttp 拦截器同步取值 */
    suspend fun current(): String? = token.first()
}
