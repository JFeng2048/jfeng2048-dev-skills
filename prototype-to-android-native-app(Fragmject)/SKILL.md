---
name: "prototype-to-android-native-app"
description: "从原型（HTML/CSS 代码、设计图截图或 PRD 页面清单）生成可直接用 Android Studio 打开并运行的原生 Android 工程骨架：Kotlin + Jetpack Compose Material3 + Hilt + Navigation Compose + Room + Retrofit + Coil，单 Activity + MVI/MVVM 分层，内置登录、权限路由、分页列表、下拉刷新、表单、设置、暗色主题、全局异常与 mock 数据。用户提到「原型转 Android」「生成 Android 原生项目」「Compose 脚手架」「照这个页面做安卓 App」「Kotlin 起步工程」时使用。"
---

# Prototype to Android Native App

## 概述

把**原型**转换成**能直接 `Run` 的原生 Android 工程**，一套 Kotlin + Compose 代码跑手机、平板与折叠屏。

**模板来源**：工程范式对齐开源项目 **Fragmject**（Kotlin + Compose M3 + Hilt + Navigation + Room + Retrofit + Coil，单 Activity、MVI/MVVM、内置登录/列表/表单/设置），并按 2025+ 的稳定版本做了现代化适配：

| 参考要点（Fragmject） | 本技能落地方式 |
| --- | --- |
| 单 Activity + Compose | ✅ `MainActivity` 唯一 Activity，`setContent` 挂根组件 |
| MVI / MVVM | ✅ 每页 `XxxUiState` + `XxxViewModel` + `StateFlow`，单向数据流 |
| Hilt 依赖注入 | ✅ `@HiltAndroidApp` + `@AndroidEntryPoint` + `@HiltViewModel`，KSP 编译 |
| Navigation | ✅ Navigation Compose 类型安全路由表（`Routes` 对象） |
| Room 本地缓存 | ✅ 远端成功写库，请求失败回读缓存 |
| Retrofit + 统一响应 | ✅ `ApiResponse<T>` + kotlinx.serialization + 拦截器注入 token |
| Coil 图片 | ✅ `AsyncImage` 统一占位与错误兜底 |
| 内置页面 | ✅ 登录 / 列表 / 详情 / 我的（设置入口） |
| 中文注释 | ✅ 全量中文注释与文案 |
| 权限、拍照选图、裁剪、沉浸式、大屏适配 | ⚠️ **按需生成**，模板预留接缝（见「内置能力」） |

> ⚠️ **版本基线以稳定可编译为准**。Fragmject 原文提到的 `Navigation3` 仍属实验期，本技能默认用 **Navigation Compose**；用户明确要求 Navigation 3 时，再换成 `androidx.navigation3` 并按官方迁移指南生成。

---

## 前置决策（开工前必须确认）

**先把下面 5 项问清楚再动手，不要自行假设。**

| # | 决策项 | 可选值 | 默认行为 |
| --- | --- | --- | --- |
| 1 | **应用包名** | `com.公司.应用`（全小写） | 必问，不猜 |
| 2 | **工程名 / 应用标题** | `skill-swap-android` / `技能互换` | 必问 |
| 3 | 最低系统版本 `minSdk` | 24 / 26 / 29 | 24（覆盖 99%+ 设备） |
| 4 | 是否需要登录与权限路由 | 是 / 否 | 是 |
| 5 | 是否启用 Room 本地缓存 | 是 / 否 | 是 |
| 6 | 是否要底部导航（首页 / 我的） | 是 / 否 | 否（模板用顶部入口） |
| 7 | 是否要暗色主题 | 跟随系统 / 固定浅色 | 跟随系统 |
| 8 | 是否要多模块（`:core` / `:feature`） | 是 / 否 | 否（单模块，后续可拆） |

**包名红线**：必须是合法 Java 包名（小写、点分层、不以数字开头），生成后 `namespace`、`applicationId`、目录路径三者必须一致。

---

## 技术基线

| 项 | 版本 / 选型 |
| --- | --- |
| 语言 | Kotlin 2.1+（K2 编译器） |
| UI | Jetpack Compose + Material3（BOM 管理版本） |
| 构建 | AGP 8.7+ / Gradle 8.11+ / JDK 17 |
| 依赖注入 | Hilt 2.53+（**KSP**，禁止 `kapt`） |
| 路由 | Navigation Compose 2.8+（单 Activity） |
| 本地存储 | Room 2.6+；登录态用 DataStore Preferences |
| 网络 | Retrofit 2.11 + OkHttp 4.12 + kotlinx.serialization |
| 图片 | Coil 2.7（Compose） |
| 异步 | Kotlin Coroutines + Flow |
| 架构 | 单 Activity + MVI（`UiState` / `Event` / 单向数据流） |

---

## 工程结构

```text
{{project_name}}/
├── settings.gradle.kts
├── build.gradle.kts                # 根构建脚本（插件统一声明）
├── gradle.properties
├── gradle/libs.versions.toml       # 版本目录（唯一依赖版本源）
├── local.properties.example
├── app/
│   ├── build.gradle.kts            # namespace / applicationId / buildConfig
│   ├── proguard-rules.pro
│   └── src/
│       ├── main/
│       │   ├── AndroidManifest.xml          # 只声明一个 Activity
│       │   ├── res/values/strings.xml
│       │   ├── res/values/themes.xml
│       │   └── java/{{package_path}}/
│       │       ├── App.kt                    # @HiltAndroidApp
│       │       ├── MainActivity.kt           # 唯一 Activity
│       │       ├── core/
│       │       │   ├── config/AppConfig.kt
│       │       │   ├── datastore/TokenStore.kt
│       │       │   ├── designsystem/
│       │       │   │   ├── theme/{Color,Type,Theme,Dimens}.kt
│       │       │   │   └── component/{StateViews,AppTopBar}.kt
│       │       │   └── navigation/{Routes,AppNavHost}.kt
│       │       ├── data/
│       │       │   ├── model/Skill.kt
│       │       │   ├── remote/{SkillApi,AuthApi}.kt + remote/dto/
│       │       │   ├── local/{AppDatabase}.kt + local/{entity,dao}/
│       │       │   ├── mock/MockData.kt
│       │       │   └── repository/{SkillRepository,AuthRepository}.kt
│       │       ├── di/{NetworkModule,DatabaseModule,RepositoryModule}.kt
│       │       └── feature/                  # 按业务切分，不按技术层平铺
│       │           ├── root/{RootViewModel,SplashScreen}.kt
│       │           ├── home/{HomeScreen,HomeViewModel,HomeUiState}.kt
│       │           │   └── components/SkillCard.kt
│       │           ├── detail/{DetailScreen,DetailViewModel,DetailUiState}.kt
│       │           ├── login/{LoginScreen,LoginViewModel,LoginUiState}.kt
│       │           └── mine/{MineScreen,MineViewModel,MineUiState}.kt
│       └── test/java/{{package_path}}/      # 至少一个可跑单测
```

**四层硬规则**：

1. `feature/*Screen` **只读 UiState、只发 Event**，不写业务、不碰网络
2. `XxxViewModel` **只调 Repository**，不 import Compose、不持有 `Context`
3. `data/repository` 是**唯一数据接缝**，mock 与真实接口切换只改这里 + `AppConfig`
4. `data/remote`、`data/local` 只被 Repository 使用，Screen 禁止直接 import

---

## 使用流程

### 步骤 1：解析原型 → 页面清单

从设计图 / HTML / PRD 中抽出页面，字段见下表：

| 字段 | 示例 |
| --- | --- |
| `page_name` | `home` |
| `route` | `home` / `detail/{skillId}` |
| `screen_class` | `HomeScreen` |
| `viewmodel_class` | `HomeViewModel` |
| `layout` | `list` / `detail` / `form` / `profile` / `grid` |
| `components` | `SkillCard`, `EmptyView` |
| `data_fields` | `id`, `title`, `author`, `price` |
| `interactions` | 点击跳转、下拉刷新、上拉加载、表单提交 |

机器可读中间产物按 `resources/specifications/prototype_parser_contract.md` 输出 `proto_context.json`；HTML 输入可直接用 `resources/tools/parse_prototype.py` 生成初稿。

### 步骤 2：确认视觉与交互

必须问清：**主色 hex**、圆角风格、是否暗色、是否需要底部导航、列表是否分页、空态/错误文案、登录方式（手机号 / 账号密码 / 第三方）。

推断不出来就列入「待确认」，**不要静默臆造**。

### 步骤 3：生成工程骨架

从 `resources/templates/project_structure/` 整目录复制，替换占位符（也可用 `resources/tools/render_template.py` 一键完成）：

| 占位符 | 含义 | 示例 |
| --- | --- | --- |
| `{{project_name}}` | 工程名（kebab-case） | `skill-swap-android` |
| `{{app_name}}` | 应用标题（显示名） | `技能互换` |
| `{{package_name}}` | 应用包名 | `com.example.skillswap` |
| `{{package_path}}` | 包名路径（目录名） | `com/example/skillswap` |
| `{{primary_color_hex}}` | 主色（不含 `#`） | `2B6DE5` |
| `{{min_sdk}}` | 最低系统版本 | `24` |
| `{{compile_sdk}}` / `{{target_sdk}}` | 编译 / 目标版本 | `35` |

**目录改名必须做**：把 `app/src/main/java/{{package_path}}/` 改名为真实路径，否则包声明与目录不一致。

### 步骤 4：生成页面

按布局选范式（模板已内置四个范本，**复制改造**而不是凭空写）：

| 布局 | 参照模板 | 关键实现 |
| --- | --- | --- |
| 列表 | `feature/home` | `LazyColumn` + 三态 + 上拉加载 + 手动刷新 |
| 详情 | `feature/detail` | `Column` + `verticalScroll` + 底部操作栏 |
| 表单 | `feature/login` | `OutlinedTextField` + 校验 + 提交态禁用 |
| 个人中心 / 设置 | `feature/mine` | 头部信息 + 设置行 + 退出登录 |

每个页面**必须**：

- 有 `XxxScreen.kt`（唯一 `@Composable` 入口）+ `XxxViewModel.kt` + `XxxUiState.kt`
- 在 `Routes` 里声明 route 常量（带参数用 `fun xxx(id: String): String`）
- 在 `AppNavHost` 里 `composable(...)` 注册
- 三态齐全：`isLoading` / `empty` / `error`
- 文案中文，注释中文

### 步骤 5：接入状态与数据

```kotlin
// ViewModel：单向数据流
private val _uiState = MutableStateFlow(HomeUiState())
val uiState: StateFlow<HomeUiState> = _uiState.asStateFlow()

fun onEvent(event: HomeEvent) = when (event) {
    HomeEvent.Refresh -> refresh()
    HomeEvent.LoadMore -> loadMore()
    HomeEvent.Retry -> refresh()
}
```

```kotlin
// Screen：只订阅状态 + 派发事件
val state by viewModel.uiState.collectAsStateWithLifecycle()
HomeContent(state = state, onRefresh = { viewModel.onEvent(HomeEvent.Refresh) })
```

### 步骤 6：填充 mock 数据

`data/mock/MockData.kt` 必须给出与真实接口**同形状**的数据：

- 列表 ≥ 10 条（撑满一屏并触发分页）
- 至少 1 条超长标题、1 条空 `tags`、1 条超长描述
- 用 `delay(300)` 模拟网络延迟，让 Loading 态可见
- 分页函数 `pageSkills(page, pageSize)` 与真实分页语义一致

### 步骤 7：自检

运行 `resources/tools/validate_project.py`，必须 **0 error**：

```bash
python resources/tools/validate_project.py ./skill-swap-android
```

共 21 项检查（清单见 `README.md` 第 5.3 节）；有 error 就修，不要靠肉眼。

---

## 原型 → Compose 映射（最易错）

| 原型写法 | Compose 写法 | 说明 |
| --- | --- | --- |
| `flex-direction: column` | `Column` | 垂直排列 |
| `flex-direction: row` | `Row` | 水平排列 |
| `position: absolute` | `Box` + `Modifier.align` | 不要用 `offset` 硬凑 |
| `display: grid` | `LazyVerticalGrid` | 或 `Row` + `FlowRow` |
| 长列表 / `v-for` | `LazyColumn` + `items(key = { it.id })` | 禁止 `Column` + `forEach` |
| `border-radius` | `RoundedCornerShape(12.dp)` | 走 theme 的 `Dimens` |
| `box-shadow` | `Modifier.shadow(elevation, shape)` 或 `Card` | 优先 `Card` |
| `linear-gradient` | `Brush.linearGradient` + `Modifier.background` | |
| `<img>` | `AsyncImage(model = url)`（Coil） | 必填 `placeholder` / `error` |
| `<input>` | `OutlinedTextField` | 配 `KeyboardOptions` |
| 固定 `px` | `dp` / `sp` | 禁止写裸数字，走 `Dimens` |
| `:hover` / `:active` | `InteractionSource` 或 `clickable` 波纹 | 移动端无 hover |
| CSS 动画 | `animate*AsState` / `AnimatedVisibility` | |
| 滚动吸顶 Header | `LazyColumn` 的 `stickyHeader` | 实验 API 需 `@OptIn` |

**视觉基线**：Material3 组件 + 8dp 间距栅格 + 12dp 卡片圆角；主色只出现在 `theme/Color.kt`，页面里**禁止**出现 `Color(0xFF...)`。

---

## 内置能力（生成时一并产出）

| 能力 | 落点 | 状态 |
| --- | --- | --- |
| 登录 + token 持久化 | `feature/login` + `core/datastore/TokenStore` | ✅ 默认生成 |
| 权限路由（未登录跳登录） | `feature/root/RootViewModel` + `MainActivity` 起始页判定 | ✅ |
| 统一请求封装 + 401 处理 | `core/network` + `data/remote` | ✅ |
| 分页列表 + 上拉加载 + 下拉刷新 | `feature/home` | ✅ |
| 表单校验与提交反馈 | `feature/login` 范式 | ✅ |
| 设置页 / 个人中心 | `feature/mine` | ✅ |
| 暗色主题 | `theme/Theme.kt` 跟随系统 | ✅ |
| 全局异常捕获 | `Thread.setDefaultUncaughtExceptionHandler` + 请求层兜底 | ✅ |
| 沉浸式状态栏 | `enableEdgeToEdge()` + `Scaffold` 内边距 | ✅ |
| Room 缓存 | `data/local` + Repository 回落 | ✅ |
| 拍照 / 选图 / 裁剪 | 权限 + `ActivityResultContracts` | ⚠️ 按需生成 |
| 动态权限封装 | `core/permission` | ⚠️ 按需生成 |
| 大屏 / 折叠屏自适应 | `WindowSizeClass` + 双栏列表详情 | ⚠️ 按需生成 |
| 引导页 | `feature/guide` + DataStore 首次标记 | ⚠️ 按需生成 |
| 底部导航 | `Scaffold` + `NavigationBar` + 嵌套 NavHost | ⚠️ 按需生成 |

⚠️ 项必须**用户明确要求**才生成，并且要说明新增的依赖与权限。

---

## 命名规范

| 对象 | 规则 | 示例 |
| --- | --- | --- |
| 包名 | 全小写点分 | `com.example.skillswap` |
| 目录 | 全小写，按功能 | `feature/home/` |
| Activity | PascalCase，后缀 `Activity` | `MainActivity` |
| 页面 Composable | PascalCase + `Screen` | `HomeScreen` |
| 页面内部块 | private + `Content` | `HomeContent` |
| ViewModel | `<页面>ViewModel` | `HomeViewModel` |
| UiState | `<页面>UiState` | `HomeUiState` |
| Event | `<页面>Event`（sealed interface） | `HomeEvent` |
| Repository | `<领域>Repository` + `Impl` | `SkillRepositoryImpl` |
| API 接口 | `<领域>Api` | `SkillApi` |
| DTO | `<领域>Dto` | `SkillDto` |
| 实体 | `<领域>Entity` | `SkillEntity` |
| 路由常量 | 大写下划线 | `Routes.HOME` |

---

## 输出格式

```text
✅ 已生成 Android 工程：{{project_name}}（Kotlin + Compose M3 + Hilt + Room + Retrofit）

📁 结构
├── app/src/main/java/{{package_path}}/core/      主题、网络、导航、DataStore
├── app/src/main/java/{{package_path}}/data/      模型、DTO、Room、Repository、mock
├── app/src/main/java/{{package_path}}/di/        Hilt 模块
└── app/src/main/java/{{package_path}}/feature/   {{N}} 个功能模块

🎨 已还原
- 页面：登录 / 列表 / 详情 / 我的
- 交互：点击跳转、上拉加载、表单校验、退出登录
- 主题：Material3，主色 {{primary_color}}

▶️ 如何运行
1. 用 Android Studio 打开工程目录
2. 首次打开等待 Gradle Sync（首次会下载依赖）
3. 选择 app 运行到模拟器或真机
（mock 已内置，无需后端）

🔌 如何对接后端
1. app/build.gradle.kts 的 buildConfigField USE_MOCK 改为 false
2. 修改 BASE_URL
3. 按 data/remote/*Api.kt 补真实路径

⚠️ 待确认
- 各列表页的真实字段
- 空态文案
- 是否需要底部导航
```

---

## 重要提示（红线）

1. **单 Activity** —— 新增页面一律用 Navigation Compose，不要建第二个 Activity
2. **不要在 Screen 里发请求** —— 一律 `Screen → ViewModel → Repository`
3. **不要用 XML 布局** —— 全 Compose，`res/layout` 下不应有页面布局
4. **不要混用 View 体系** —— 不生成 `RecyclerView` / `Fragment` / `findViewById`
5. **Hilt 三件套别漏** —— `@HiltAndroidApp`（Application）、`@AndroidEntryPoint`（Activity）、`@HiltViewModel`（ViewModel）
6. **用 KSP，不用 kapt** —— 新工程启用 kapt 会直接编译不过（Kotlin 2.x）
7. **包名三处一致** —— `namespace`、`applicationId`、源码目录路径
8. **颜色只进 theme** —— 页面里出现 `Color(0xFF...)` 视为不合格
9. **mock 要像真数据** —— 条目少、字段空，看不出布局问题
10. **权限按需申请** —— 不要无理由写 `READ_EXTERNAL_STORAGE`、`CAMERA`
11. **不要臆造业务规则** —— 拿不准的列进「待确认」
12. **中文注释与文案** —— 与团队习惯一致

---

## 资源文件说明

```text
prototype-to-android-native-app/
├── SKILL.md
├── README.md
└── resources/
    ├── config/
    │   ├── naming_rules.json          # 命名规则（包、类、文件、路由）
    │   ├── dependency_baseline.json   # 版本基线（含替代方案）
    │   └── design_tokens.json         # 颜色 / 间距 / 圆角 / 字号
    ├── specifications/
    │   ├── prototype_parser_contract.md  # 原型 → proto_context.json 契约
    │   ├── architecture_conventions.md   # 分层与 MVI 约定
    │   └── compose_mapping_rules.md      # Web/原型 → Compose 映射细则
    ├── templates/
    │   └── project_structure/         # 可运行骨架（含四个页面范本）
    ├── tools/
    │   ├── parse_prototype.py         # HTML → proto_context.json
    │   ├── preview_plan.py            # 预览生成计划
    │   ├── render_template.py         # 按 context 渲染骨架（替换占位符/包路径）
    │   └── validate_project.py        # 21 项工程静态校验
    ├── demo_input/
    │   └── index.html                 # 示例原型输入
    └── demo_output/
        └── skill-swap-android/        # 示例产物（已通过 21 项校验）
```
