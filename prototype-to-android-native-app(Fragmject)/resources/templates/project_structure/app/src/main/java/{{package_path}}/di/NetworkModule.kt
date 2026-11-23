package {{package_name}}.di

import {{package_name}}.BuildConfig
import {{package_name}}.core.config.AppConfig
import {{package_name}}.core.datastore.TokenStore
import {{package_name}}.data.remote.AuthApi
import {{package_name}}.data.remote.SkillApi
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

/**
 * 网络层：Json / OkHttp / Retrofit / Api。
 *
 * 统一在这里加拦截器（token、日志），页面与 ViewModel 不感知。
 */
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    @Provides
    @Singleton
    fun provideJson(): Json = Json {
        ignoreUnknownKeys = true // 后端加字段不崩
        encodeDefaults = true
        explicitNulls = false
    }

    @Provides
    @Singleton
    fun provideOkHttpClient(tokenStore: TokenStore): OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(AppConfig.CONNECT_TIMEOUT_SECONDS, TimeUnit.SECONDS)
        .readTimeout(AppConfig.READ_TIMEOUT_SECONDS, TimeUnit.SECONDS)
        .addInterceptor { chain ->
            // 拦截器是同步上下文，这里阻塞读取一次 token；DataStore 有内存缓存，开销很小
            val token = runBlocking { tokenStore.current() }
            val request = chain.request().newBuilder()
                .apply {
                    if (!token.isNullOrBlank()) {
                        header("Authorization", "Bearer $token")
                    }
                }
                .build()
            chain.proceed(request)
        }
        .addInterceptor(
            HttpLoggingInterceptor().apply {
                level = if (BuildConfig.DEBUG) {
                    HttpLoggingInterceptor.Level.BODY
                } else {
                    HttpLoggingInterceptor.Level.NONE
                }
            },
        )
        .build()

    @Provides
    @Singleton
    fun provideRetrofit(client: OkHttpClient, json: Json): Retrofit = Retrofit.Builder()
        .baseUrl(AppConfig.BASE_URL)
        .client(client)
        .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
        .build()

    @Provides
    @Singleton
    fun provideSkillApi(retrofit: Retrofit): SkillApi = retrofit.create(SkillApi::class.java)

    @Provides
    @Singleton
    fun provideAuthApi(retrofit: Retrofit): AuthApi = retrofit.create(AuthApi::class.java)
}
