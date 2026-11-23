# Android 分层与 MVI 约定

生成的所有 Android 工程必须遵循本约定。违反任意一条即视为生成失败。

## 1. 分层

```text
feature/<name>            UI 层（Compose）
    ├── XxxScreen.kt      唯一 @Composable 入口 + private 内部块
    ├── XxxViewModel.kt   状态持有 + 事件处理
    └── XxxUiState.kt     不可变状态（data class）+ Event（sealed interface）
        ↓ 只依赖接口
data/repository            数据接缝（mock / 远端 / 本地缓存都在这层落地）
    ↓
data/remote                Retrofit Api + DTO
data/local                 Room Entity / Dao / Database
data/mock                  MockData
core/                      主题、导航、网络模块、DataStore、通用组件
di/                        Hilt 模块
```

依赖方向**单向**：`feature → repository → (remote | local | mock)`。反向依赖、跨层直连都禁止。

## 2. 数据流（单向）

```text
用户操作 → onEvent(Event) → ViewModel 处理 → Repository
                                     ↓
         Screen 渲染 ← collectAsStateWithLifecycle(UiState)
```

规则：

1. `UiState` **不可变**：`data class`，全部 `val`，更新用 `copy()`
2. 状态用 `MutableStateFlow` 私有 + `asStateFlow()` 暴露
3. 一次性事件（跳转、Toast）用 `Channel` + `receiveAsFlow()`，**不要**塞进 UiState 的布尔位
4. `ViewModel` 里启动协程一律 `viewModelScope`
5. `Screen` 不住持 `NavController` 之外的可变状态

## 3. 三态与边界

每个取数页面必须处理：

| 状态 | 判定 | 呈现 |
| --- | --- | --- |
| Loading | `isLoading && data.isEmpty()` | `LoadingView()` 居中进度 |
| Empty | `!isLoading && data.isEmpty() && error == null` | `EmptyView(text)` |
| Error | `error != null && data.isEmpty()` | `ErrorView(message, onRetry)` |
| Loaded | `data.isNotEmpty()` | 正常内容 |

**缓存回落**：远端失败且本地有缓存时，展示缓存 + 顶部提示，不要直接进 Error。

## 4. Repository 契约

```kotlin
interface SkillRepository {
    suspend fun getSkills(page: Int, pageSize: Int): Result<List<Skill>>
    suspend fun getSkillDetail(id: String): Result<Skill>
}
```

- 返回 `Result<T>`，**不抛异常给 ViewModel**
- 分页语义：`page` 从 0 开始，`pageSize` 取 `AppConfig.PAGE_SIZE`
- mock 与真实实现只在 `Impl` 内通过 `AppConfig.USE_MOCK` 分流
- 远端成功写 Room；失败读 Room 回落
- 捕获异常时**必须先重新抛出 `CancellationException`**，避免取消被吞

```kotlin
try { ... } catch (e: CancellationException) { throw e } catch (e: Exception) { Result.failure(e) }
```

## 5. Hilt 约定

| 位置 | 注解 |
| --- | --- |
| `App.kt` | `@HiltAndroidApp` |
| `MainActivity` | `@AndroidEntryPoint` |
| 每个 ViewModel | `@HiltViewModel` + `@Inject constructor` |
| 单例对象 | `@Singleton` |
| 模块 | `@Module @InstallIn(SingletonComponent::class)`，接口绑定用 `abstract class` + `@Binds` |

**禁止**：`object` 里手写静态单例、在 ViewModel 里 `DaggerXxxComponent.create()`、用 `kapt`。

## 6. 导航约定

- 单 Activity，`NavHost` 唯一
- 路由集中 `Routes` 对象，带参数同时提供工厂函数
- 传参用 path 参数 + `SavedStateHandle` 读取，**不要**传对象
- 登录态变更：`popUpTo(0) { inclusive = true }` 清栈，避免返回键回到登录页

## 7. 线程与性能

- 网络 / 数据库：`suspend` 函数，由 Room / Retrofit 内部切线程；CPU 密集用 `withContext(Dispatchers.Default)`
- 列表：`LazyColumn` + `items(key = { it.id })`，禁止 `Column` + `forEach`
- 图片：Coil `AsyncImage`，必须给 `placeholder` 与 `error`
- 避免在 Composable 里直接 `LaunchedEffect(Unit)` 发请求；请求由 ViewModel `init` 发起

## 8. 错误处理

- 全局：`App` 里设置 `Thread.setDefaultUncaughtExceptionHandler`，记录日志（release 上报，debug 打印）
- 网络层：统一解包 `{ code, message, data }`，`code != 0` 转 `Result.failure`
- 401：清除 token 并跳登录（`TokenStore.clear()` + 导航到 `Routes.LOGIN`）
- 用户可见错误文案中文，日志保留原文

## 9. 构建配置

- 依赖版本只在 `gradle/libs.versions.toml`
- `USE_MOCK` / `BASE_URL` 用 `buildConfigField`，debug 与 release 分开
- `debug` 开 `HttpLoggingInterceptor.Level.BODY`，`release` 关
- `release` 开 `isMinifyEnabled = true` + `proguard-rules.pro`

## 10. 代码风格

- Kotlin 官方风格（4 空格缩进，表达式体优先）
- Composable 命名 PascalCase，可复用组件首参 `modifier: Modifier = Modifier`
- 中文注释，public 类与关键方法写 KDoc
- 单文件不超过 ~300 行，超了拆 `components/`
