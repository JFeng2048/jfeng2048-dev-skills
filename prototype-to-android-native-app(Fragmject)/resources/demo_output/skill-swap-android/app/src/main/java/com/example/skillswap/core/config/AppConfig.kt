package com.example.skillswap.core.config

import com.example.skillswap.BuildConfig

/**
 * 全局配置。
 *
 * USE_MOCK / BASE_URL 来自 build.gradle.kts 的 buildConfigField，
 * 切换 mock 与真实接口只需要改构建脚本，不碰业务代码。
 */
object AppConfig {

    /** 是否使用 mock 数据（debug 默认 true） */
    val USE_MOCK: Boolean = BuildConfig.USE_MOCK

    /** 接口根地址，必须以 / 结尾，否则 Retrofit 会抛异常 */
    val BASE_URL: String = BuildConfig.BASE_URL

    /** 列表分页大小 */
    const val PAGE_SIZE = 10

    /** 连接超时（秒） */
    const val CONNECT_TIMEOUT_SECONDS = 15L

    /** 读取超时（秒） */
    const val READ_TIMEOUT_SECONDS = 20L
}
