# skill-swap-android

技能互换 —— 原生 Android 工程（Kotlin + Jetpack Compose）。

## 技术栈

| 项 | 选型 |
| --- | --- |
| 语言 / 构建 | Kotlin 2.1 / AGP 8.7 / Gradle 8.11 / JDK 17 |
| UI | Jetpack Compose + Material3 |
| 架构 | 单 Activity + MVI（UiState / Event） |
| 依赖注入 | Hilt（KSP） |
| 路由 | Navigation Compose |
| 本地存储 | Room + DataStore |
| 网络 | Retrofit + OkHttp + kotlinx.serialization |
| 图片 | Coil |

## 目录

```text
app/src/main/java/com/example/skillswap/
├── App.kt                 # Application（@HiltAndroidApp）
├── MainActivity.kt        # 唯一 Activity
├── core/                  # 主题、导航、网络、DataStore、通用组件
├── data/                  # 模型 / DTO / Room / Repository / mock
├── di/                    # Hilt 模块
└── feature/               # 功能模块（home / detail / login / mine / root）
```

分层依赖方向：`feature → repository → (remote | local | mock)`。页面不直接访问网络或数据库。

## 运行

1. 用 **Android Studio** 打开本目录，等待 Gradle Sync（会自动下载依赖）
2. 若提示缺少 SDK 路径，复制 `local.properties.example` 为 `local.properties` 并填写 `sdk.dir`
3. 选择 `app` 配置，运行到模拟器或真机

命令行（可选）：

```bash
./gradlew :app:assembleDebug     # 打包
./gradlew :app:testDebugUnitTest # 单元测试
```

> 仓库没有内置 `gradle-wrapper.jar`（二进制文件）。用 Android Studio 打开会自动补齐；
> 或用本机 Gradle 执行一次 `gradle wrapper --gradle-version 8.11.1`。

## mock 与真实接口

`app/build.gradle.kts` 中：

```kotlin
debug {
    buildConfigField("boolean", "USE_MOCK", "true")
    buildConfigField("String", "BASE_URL", "\"https://dev-api.example.com/\"")
}
```

- 保持 `USE_MOCK = true`：数据来自 `data/mock/MockData.kt`，无需后端
- 改为 `false`：走 Retrofit，接口路径在 `data/remote/*Api.kt` 中补全

## 新增页面

1. `feature/<name>/` 下建 `XxxScreen.kt`、`XxxViewModel.kt`、`XxxUiState.kt`
2. `core/navigation/Routes.kt` 加路由常量
3. `core/navigation/AppNavHost.kt` 加 `composable(...)` 注册
4. 需要网络数据时，在 `data/repository/` 加方法，**不要**在页面里调 Api

## 常见问题

| 现象 | 原因 / 处理 |
| --- | --- |
| Sync 失败：Unsupported class file major version | JDK 版本不对，切到 JDK 17 |
| KSP 报版本不匹配 | `libs.versions.toml` 中 `ksp` 必须与 `kotlin` 主版本一致 |
| Hilt 找不到 ViewModel | 忘记 `@HiltViewModel` 或 `@AndroidEntryPoint` |
| 页面点不进去 | 忘记在 `AppNavHost` 注册 |
| 图片不显示 | 网络图需 `INTERNET` 权限；Coil 需联网 |
