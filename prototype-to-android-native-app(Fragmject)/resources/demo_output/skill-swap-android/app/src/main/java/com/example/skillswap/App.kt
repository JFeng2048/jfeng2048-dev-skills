package com.example.skillswap

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

/**
 * 应用入口。
 *
 * 只做两件事：
 * 1. 声明 @HiltAndroidApp 生成 Hilt 组件；
 * 2. 注册全局未捕获异常处理器（避免线上静默崩溃）。
 */
@HiltAndroidApp
class App : Application() {

    override fun onCreate() {
        super.onCreate()
        installCrashHandler()
    }

    private fun installCrashHandler() {
        val defaultHandler = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
            // TODO: 接入真实崩溃上报（如 Firebase Crashlytics / 自建日志）
            android.util.Log.e("AppCrash", "线程 ${thread.name} 崩溃", throwable)
            defaultHandler?.uncaughtException(thread, throwable)
        }
    }
}
