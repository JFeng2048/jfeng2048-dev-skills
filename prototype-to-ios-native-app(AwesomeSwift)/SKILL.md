---
name: "prototype-to-ios-native-app"
description: "从原型（HTML/CSS 代码、设计图截图或 PRD 页面清单）生成开箱即用的原生 iOS 工程骨架：SwiftUI + MVVM + Combine + SwiftData + Alamofire + Kingfisher，XcodeGen 管理工程，内置登录、权限路由、分页信息流、下拉刷新、表单、设置、暗黑模式、国际化、崩溃捕获与 mock 数据。用户提到「原型转 iOS」「生成 iOS 原生项目」「SwiftUI 脚手架」「照这个页面做 iPhone App」「Xcode 起步工程」时使用。"
---

# Prototype to iOS Native App

## 概述

把**原型**转换成**能用 Xcode 打开直接 Run** 的原生 iOS 工程（iPhone / iPad 通用，SwiftUI 自适应）。

**模板来源**：工程范式对齐开源项目 **AwesomeSwift**（SwiftUI + MVVM + Combine + SwiftData + Alamofire + Kingfisher，中文注释、内置登录/引导/信息流/详情/设置/表单/暗黑模式/国际化/权限/图片选择/Lottie/崩溃捕获），并按 iOS 17+ 的稳定 API 做了现代化适配：

| 参考要点（AwesomeSwift） | 本技能落地方式 |
| --- | --- |
| SwiftUI + MVVM | ✅ 每个 Feature：`XxxView` + `XxxViewModel`（`ObservableObject` + `@Published`） |
| Combine | ✅ 搜索防抖、状态订阅用 Combine（`debounce` / `AnyCancellable`） |
| SwiftData | ✅ `@Model` + `ModelContainer`，远端成功写库、失败回读缓存 |
| Alamofire | ✅ `Session` + `RequestInterceptor` 注入 token + 统一解包 `{code,message,data}` |
| Kingfisher | ✅ `KFImage` 统一占位与错误兜底 |
| 登录 / 引导 / 信息流 / 详情 / 设置 / 表单 | ✅ 登录、信息流、详情、我的（设置入口）四个页面范本 |
| 暗黑模式 | ✅ Asset 颜色集双 appearance，跟随系统 |
| 国际化 | ✅ `zh-Hans` + `en` 两套 `Localizable.strings` |
| 权限 / 图片选择 / Lottie | ⚠️ **按需生成**，不默认加依赖与用途描述 |
| 工程规范 | ✅ XcodeGen `project.yml`（不用手改 `.xcodeproj`）、`Debug/Release` xcconfig |
| 崩溃捕获 | ✅ NSSetUncaughtExceptionHandler + SwiftUI 错误兜底 |

> ⚠️ **不直接生成 `.xcodeproj`**。二进制 pbxproj 无法可靠手写，本技能用 **XcodeGen**（`project.yml`）声明工程，执行 `xcodegen generate` 得到可编译工程；同时也便于版本管理与代码评审。

---

## 前置决策（开工前必须确认）

| # | 决策项 | 可选值 | 默认 |
| --- | --- | --- | --- |
| 1 | **工程名** | PascalCase，如 `SkillSwap`（同时是模块名 / 目录名 / Scheme） | 必问 |
| 2 | **应用显示名** | 中文名，如 `技能互换` | 必问 |
| 3 | **Bundle ID** | 反域名，如 `com.example.skillswap` | 必问 |
| 4 | 最低系统版本 | 17.0 / 18.0 | **17.0**（SwiftData 要求） |
| 5 | 是否需要登录与权限路由 | 是 / 否 | 是 |
| 6 | 是否启用 SwiftData 缓存 | 是 / 否 | 是 |
| 7 | 支持语言 | 仅中文 / 中英双语 | 中英双语 |
| 8 | 是否需要底部 TabBar | 是 / 否 | 否（模板用导航栏入口） |
| 9 | 是否需要真机运行 | 是则需 Apple 开发者 Team | 模拟器优先 |

**命名红线**：

- `{{project_name}}` 必须是 **PascalCase 的合法 Swift 模块名**（不能带连字符、空格、中文）
- Bundle ID 全小写点分，与 `project.yml` 中 `PRODUCT_BUNDLE_IDENTIFIER` 一致
- 目录名 = 工程名 = Scheme 名 = 模块名

---

## 技术基线

| 项 | 选型 |
| --- | --- |
| 语言 / UI | Swift 5.10 + SwiftUI（iOS 17+） |
| 架构 | MVVM + Combine 单向状态流 |
| 并发 | async/await（`Task` + `.task`），Combine 仅用于事件流 |
| 本地存储 | SwiftData（`@Model` / `ModelContainer`）；token 用 UserDefaults（可换 Keychain） |
| 网络 | Alamofire 5.9 + `RequestInterceptor` |
| 图片 | Kingfisher 7.x |
| 工程生成 | XcodeGen 2.4x（`project.yml`） |
| 依赖管理 | SPM（`project.yml` 的 `packages`） |
| 配置 | `Configs/Debug.xcconfig` / `Release.xcconfig` → `Info.plist` → `AppConfig` |
| 并发检查 | `SWIFT_STRICT_CONCURRENCY = minimal`（Swift 6 迁移见 README） |

---

## 工程结构

```text
{{project_name}}/
├── project.yml                     # XcodeGen 工程声明（唯一工程配置源）
├── Configs/
│   ├── Debug.xcconfig              # API_BASE_URL / USE_MOCK（开发）
│   └── Release.xcconfig            # 生产环境
├── .gitignore
├── README.md
├── {{project_name}}/               # 主 Target 源码（目录名 = 工程名）
│   ├── App/
│   │   ├── AppEntry.swift          # @main，注入 container 与 ModelContainer
│   │   └── RootView.swift          # 登录态分流 + NavigationStack
│   ├── Core/
│   │   ├── Config/AppConfig.swift
│   │   ├── Networking/{APIClient,APITarget,APIError,AuthInterceptor}.swift
│   │   ├── Storage/{TokenStorage,SessionStore,SwiftDataStack}.swift
│   │   ├── Router/AppRoute.swift
│   │   ├── Theme/AppTheme.swift
│   │   ├── Common/LoadState.swift
│   │   ├── DI/AppContainer.swift
│   │   └── Extensions/View+Modifiers.swift
│   ├── Data/
│   │   ├── Models/Skill.swift
│   │   ├── DTO/{APIResponse,SkillDTO,LoginDTO}.swift
│   │   ├── Repositories/{SkillRepository,AuthRepository}.swift
│   │   └── Mock/MockData.swift
│   ├── Features/
│   │   ├── Home/{HomeView,HomeViewModel}.swift + Components/SkillCard.swift
│   │   ├── Detail/{DetailView,DetailViewModel}.swift
│   │   ├── Login/{LoginView,LoginViewModel}.swift
│   │   └── Mine/{MineView,MineViewModel}.swift
│   └── Resources/
│       ├── Info.plist
│       ├── Assets.xcassets/        # 语义色（浅色/深色）+ AppIcon + AccentColor
│       ├── zh-Hans.lproj/Localizable.strings
│       └── en.lproj/Localizable.strings
└── Tests/
    └── MockDataTests.swift         # XCTest，纯逻辑可跑
```

**四条硬规则**：

1. `View` **只读状态、只发意图**，不写业务、不发网络请求
2. `ViewModel` **只依赖 Repository 协议**，不 `import SwiftUI`、不碰 `Alamofire`
3. `Repository` 是**唯一数据接缝**，mock/真实分支只在这里 + `AppConfig`
4. 颜色只出现在 `AppTheme`（来源于 Asset 色集），页面里禁止 `Color(red:green:blue:)`

---

## 使用流程

### 步骤 1：解析原型 → 页面清单

| 字段 | 示例 |
| --- | --- |
| `page_name` | `home` |
| `route` | `detail(id:)` / `mine` |
| `view_class` | `HomeView` |
| `viewmodel_class` | `HomeViewModel` |
| `layout` | `list` / `detail` / `form` / `profile` / `grid` |
| `components` | `SkillCard`, `EmptyStateView` |
| `data_fields` | `skillID`, `title`, `author`, `price` |
| `interactions` | 点击跳转、下拉刷新、上拉加载、表单提交 |

机器可读中间产物按 `resources/specifications/prototype_parser_contract.md` 输出 `proto_context.json`；HTML 输入可用 `resources/tools/parse_prototype.py`。

### 步骤 2：确认视觉与交互

必须问清：主色、圆角风格、是否暗色、TabBar 项、列表是否分页、空态/错误文案、登录方式、是否需要图片选择/相机（涉及 Info.plist 用途描述）。

推断不出就列入「待确认」，**不要静默臆造**。

### 步骤 3：生成工程骨架

从 `resources/templates/project_structure/` 整目录复制，替换占位符（或用 `resources/tools/render_template.py` 一键完成）：

| 占位符 | 含义 | 示例 |
| --- | --- | --- |
| `{{project_name}}` | 工程名（PascalCase，目录名/模块名/Scheme） | `SkillSwap` |
| `{{app_name}}` | 应用显示名 | `技能互换` |
| `{{bundle_id}}` | Bundle Identifier | `com.example.skillswap` |
| `{{bundle_id_prefix}}` | 反域名前缀（XcodeGen `bundleIdPrefix`） | `com.example` |
| `{{ios_min}}` | 最低系统版本 | `17.0` |
| `{{primary_r}}` / `{{primary_g}}` / `{{primary_b}}` | 主色 RGB 十六进制（两位） | `2B` / `6D` / `E5` |

**目录改名必须做**：`{{project_name}}/` 改成真实工程名，否则模块名与目录不一致。

### 步骤 4：生成页面

四个范本**复制改造**，不要凭空写：

| 布局 | 范本 | 关键实现 |
| --- | --- | --- |
| 列表 / 信息流 | `Features/Home` | `List` + `LoadState` 三态 + 上拉加载 + `.refreshable` + `.searchable` |
| 详情 | `Features/Detail` | `ScrollView` + `safeAreaInset` 底部操作栏 |
| 表单 | `Features/Login` | `TextField`/`SecureField` + 校验 + 提交禁用 |
| 个人中心 / 设置 | `Features/Mine` | 头部信息 + `List` 设置行 + 退出登录确认 |

每个页面**必须**：

- 有 `XxxView.swift` + `XxxViewModel.swift`
- 路由加到 `AppRoute`，并在 `RootView` 的 `navigationDestination` 里 `switch` 处理
- 三态齐全：`idle/loading` → `empty` → `failed` → `loaded`
- 文案走本地化 key（`Text("home.title")`），不硬编码中文到多个文件

### 步骤 5：接入状态与数据

```swift
// ViewModel：单向状态流
@MainActor
final class HomeViewModel: ObservableObject {
    @Published private(set) var state: LoadState<[Skill]> = .idle

    func loadIfNeeded() async {
        guard case .idle = state else { return }
        await reload()
    }
}
```

```swift
// View：只订阅状态
switch viewModel.state {
case .idle, .loading: ProgressView()
case .empty:          ContentUnavailableView(...)
case .failed(let msg): ContentUnavailableView { ... } actions: { Button("common.retry") { ... } }
case .loaded(let list): listView(list)
}
```

### 步骤 6：填充 mock 数据

`Data/Mock/MockData.swift` 必须给出与真实接口**同形状**的数据：

- 12 条（撑满一屏并触发第二页）
- 至少 1 条超长标题、1 条空 `tags`、1 条超长 `detail`
- `Task.sleep(300ms)` 模拟网络延迟，让 Loading 可见
- 分页与搜索语义与真实接口一致

### 步骤 7：自检

```bash
python resources/tools/validate_project.py ./SkillSwap
```

22 项检查必须 **0 error**（清单见 `README.md`），再用 `xcodegen generate` 生成工程。

---

## 原型 → SwiftUI 映射（最易错）

| 原型 | SwiftUI | 说明 |
| --- | --- | --- |
| `flex-direction: column` | `VStack(spacing:)` | 间距走 `AppTheme.Spacing` |
| `flex-direction: row` | `HStack` | 对齐用 `alignment:` |
| `position: absolute` | `ZStack` + `.overlay`/`.offset` | 优先 `overlay` |
| `display: grid` | `LazyVGrid` | 入口宫格 |
| 长列表 | `List` + `ForEach` | 不要用 `ScrollView + VStack` 堆长列表 |
| 卡片圆角 | `.clipShape(RoundedRectangle(cornerRadius:style:))` | 走 `AppTheme.Radius` |
| `box-shadow` | `.shadow(color:radius:y:)` | 轻阴影，别重 |
| `linear-gradient` | `LinearGradient` | |
| `<img>` | `KFImage(url)` | 必带 `.placeholder` |
| `<input>` | `TextField` / `SecureField` | 配 `.textInputAutocapitalization(.never)` |
| 固定 `px` | `CGFloat` 常量（`AppTheme`） | 禁止裸数字散落 |
| `:hover` | 无 | 用 `.buttonStyle` 点击反馈 |
| CSS 动画 | `.animation(_:value:)` / `withAnimation` | 不做长动画 |
| 下拉刷新 | `.refreshable { await ... }` | 系统手势 |
| 吸顶头部 | `List` 的 `Section(header:)` 或 `safeAreaInset` | |

**视觉基线**：系统字体（Dynamic Type）+ 8pt 间距栅格 + 12pt 卡片圆角 + 语义色（Asset 双 appearance）。

---

## 内置能力（生成时一并产出）

| 能力 | 落点 | 状态 |
| --- | --- | --- |
| 登录 + token 持久化 | `Features/Login` + `Core/Storage/TokenStorage` | ✅ 默认 |
| 权限路由（未登录进登录页） | `RootView` 依据 `SessionStore.isLoggedIn` 分流 | ✅ |
| 统一请求封装 + 401 处理 | `APIClient` + `APIError` + `AuthInterceptor` | ✅ |
| 分页信息流 + 下拉刷新 + 搜索防抖 | `HomeViewModel`（Combine `debounce`） | ✅ |
| 表单校验与提交反馈 | `LoginView` 范式 | ✅ |
| 设置页 / 个人中心 | `Features/Mine` | ✅ |
| 暗黑模式 | Asset 色集 + 跟随系统 | ✅ |
| 国际化 | `zh-Hans` / `en` 两套 strings | ✅ |
| 全局异常捕获 | `NSSetUncaughtExceptionHandler` + 错误态兜底 | ✅ |
| SwiftData 缓存回落 | `DefaultSkillRepository` | ✅ |
| 图片选择 / 相机 / 相册 | `PhotosPicker` + 用途描述 | ⚠️ 按需 |
| Lottie 动效 | `Lottie` SPM | ⚠️ 按需 |
| 推送 / 深链 | `UNUserNotificationCenter` / `onOpenURL` | ⚠️ 按需 |
| 底部 TabBar | `TabView` + 各自 `NavigationStack` | ⚠️ 按需 |
| 引导页 | `Features/Guide` + `@AppStorage` 首次标记 | ⚠️ 按需 |

⚠️ 项必须**用户明确要求**才生成，并说明新增的依赖、权限与 Info.plist 用途描述。

---

## 命名规范

| 对象 | 规则 | 示例 |
| --- | --- | --- |
| 工程 / 模块 / 目录 | PascalCase | `SkillSwap` |
| View | `<Feature>View` | `HomeView` |
| ViewModel | `<Feature>ViewModel` | `HomeViewModel` |
| 组件 | PascalCase，放 `Components/` | `SkillCard` |
| 协议 | 名词 | `SkillRepository` |
| 实现 | `Default<协议名>` | `DefaultSkillRepository` |
| DTO | `<领域>DTO` | `SkillDTO` |
| 路由 | `AppRoute` 枚举，`case detail(id: String)` | |
| 常量 / 主题 | `AppTheme.Spacing.md` | |
| 本地化 key | 点分小写 | `home.empty.title` |
| 资源色 | PascalCase colorset | `BrandPrimary` |

---

## 输出格式

```text
✅ 已生成 iOS 工程：{{project_name}}（SwiftUI + MVVM + SwiftData + Alamofire + Kingfisher）

📁 结构
├── project.yml         XcodeGen 工程声明
├── Configs/            Debug / Release 环境
├── {{project_name}}/   App / Core / Data / Features / Resources
└── Tests/              单元测试

🎨 已还原
- 页面：登录 / 信息流 / 详情 / 我的
- 交互：下拉刷新、上拉加载、搜索防抖、表单校验、退出登录
- 主题：语义色 + 深色模式，主色 {{primary_color}}

▶️ 如何运行
1. 安装 XcodeGen：brew install xcodegen
2. cd 工程目录 && xcodegen generate
3. open {{project_name}}.xcodeproj，选模拟器 Run
（mock 已内置，无需后端；真机需在 project.yml 填 DEVELOPMENT_TEAM）

🔌 如何对接后端
1. Configs/Debug.xcconfig 的 USE_MOCK 改为 NO
2. 修改 API_BASE_URL（注意 // 需写成 https:/$()/host）
3. 按 Core/Networking/APITarget.swift 补真实路径

⚠️ 待确认
- 列表真实字段
- 空态文案
- 是否需要 TabBar / 图片选择
```

---

## 重要提示（红线）

1. **不要手写 `.xcodeproj`** —— 一律改 `project.yml`，再 `xcodegen generate`
2. **不要多 Target 堆页面** —— 单 App Target + SwiftUI 路由
3. **View 不发请求** —— `View → ViewModel → Repository`
4. **不要用 UIKit 页面** —— 不生成 Storyboard / XIB / `UIViewController`
5. **ViewModel 不 import SwiftUI / Alamofire / Kingfisher**
6. **颜色只进 AppTheme** —— 页面里出现 `Color(red:...)` 视为不合格
7. **`identifier` 三处一致** —— 目录名、`project.yml` 的 target/scheme 名、`@testable import`
8. **xcconfig 的 `//` 是注释** —— URL 必须写 `https:/$()/host` 形式，否则被截断
9. **Info.plist 不要放明文密钥** —— 只放 baseURL / 开关 / 用途描述
10. **权限按需** —— 不写无理由的 `NSCameraUsageDescription`
11. **SwiftData 模型主键别叫 `id`** —— 用 `skillID` 之类业务键，避免与 `Identifiable` 冲突
12. **不臆造业务规则** —— 拿不准的列进「待确认」

---

## 资源文件说明

```text
prototype-to-ios-native-app/
├── SKILL.md
├── README.md
└── resources/
    ├── config/
    │   ├── naming_rules.json
    │   ├── dependency_baseline.json
    │   └── design_tokens.json
    ├── specifications/
    │   ├── prototype_parser_contract.md
    │   ├── architecture_conventions.md
    │   └── swiftui_mapping_rules.md
    ├── templates/
    │   └── project_structure/       # 可运行骨架（4 个页面范本 + XcodeGen）
    ├── tools/
    │   ├── parse_prototype.py       # HTML → proto_context.json
    │   ├── preview_plan.py          # 预览生成计划
    │   ├── render_template.py       # 按 context 渲染骨架
    │   └── validate_project.py      # 22 项静态校验
    ├── demo_input/index.html
    └── demo_output/skill-swap-ios/  # 示例产物（已通过校验）
```
