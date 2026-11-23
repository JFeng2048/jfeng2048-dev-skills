# iOS 分层与 MVVM 约定

生成的所有 iOS 工程必须遵循本约定。违反任意一条即视为生成失败。

## 1. 分层

```text
Features/<name>             表现层
    ├── XxxView.swift        SwiftUI 视图，只读 state、只发意图
    └── XxxViewModel.swift   @MainActor ObservableObject，持有 state 与业务编排
        ↓ 只依赖协议
Data/Repositories            数据接缝（mock / 远端 / SwiftData 缓存都在这层）
    ↓
Core/Networking              Alamofire Session / APITarget / APIError / Interceptor
Data/Models                  SwiftData @Model
Data/DTO                     与后端字段一一对应
Core/…                       Theme / Router / Storage / DI / Common
```

依赖方向**单向**：`Features → Repositories → (DTO | Model | Mock)`。反向依赖与跨层直连禁止。

## 2. 状态流（单向）

```text
用户操作 → ViewModel 方法 → Repository
                ↓
        View 渲染 ← @Published state
```

规则：

1. `ViewModel` 用 `@Published private(set) var state` 暴露只读状态
2. `View` 用 `@StateObject` 持有 ViewModel，构造时注入依赖
3. 页面状态统一用 `LoadState<Value>`：`idle / loading / empty / loaded / failed`
4. 一次性提示（Toast / Alert）可用 `@Published var toast: String?`，不要塞进 `LoadState`
5. `ViewModel` 全部标 `@MainActor`，异步用 `Task { await ... }`
6. Combine 只用于**事件流**（搜索防抖、状态合并），不要用它替代 async/await

## 3. 三态与边界

| 状态 | 判定 | 呈现 |
| --- | --- | --- |
| Loading | `.loading` / `.idle` | `ProgressView`，占满可用空间 |
| Empty | `.empty` | `ContentUnavailableView`（iOS 17+） |
| Failed | `.failed(message)` | 图标 + 文案 + 重试按钮 |
| Loaded | `.loaded(value)` | 正常内容 |

**缓存回落**：远端失败且本地已有数据时展示缓存 + 轻提示，不要直接进 Failed。

## 4. Repository 契约

```swift
@MainActor
protocol SkillRepository {
    func fetchSkills(page: Int, pageSize: Int, keyword: String?) async throws -> [Skill]
    func fetchDetail(id: String) async throws -> Skill
}
```

- 一律 `async throws`，错误转 `APIError` 后抛出
- 分页：`page` 从 0 开始，`pageSize` 取 `AppConfig.pageSize`
- mock 与真实分支只在 `Impl` 内用 `AppConfig.useMock` 分流
- 远端成功 upsert SwiftData；失败回读缓存（仅第一页回落，避免分页拼接错乱）
- 不吞 `CancellationError`

## 5. 组合根与依赖注入

```swift
@MainActor
final class AppContainer: ObservableObject {
    let modelContainer: ModelContainer
    let sessionStore: SessionStore
    let skillRepository: SkillRepository
    let authRepository: AuthRepository
}
```

- **唯一装配点**：`AppContainer`，在 `AppEntry` 创建并通过 `.environmentObject` 下发
- 页面通过构造器接收依赖（`HomeView(repository:)`），不直接 `AppContainer.shared.xxx`
- 便于单测：Repository 是协议，测试可注入假实现

## 6. 导航

- 单 `NavigationStack`，路由用 `AppRoute: Hashable`
- 带参路由用关联值：`case detail(id: String)`，禁止拼字符串 URL
- `navigationDestination(for: AppRoute.self)` 里 `switch` 分发
- 登录态切换由 `RootView` 依据 `SessionStore.isLoggedIn` 分支，不手动 push/pop 登录页

## 7. 并发与性能

- 网络/IO 用 async/await；CPU 密集用 `Task.detached` 或 `nonisolated` 函数
- 列表用 `List` + `ForEach`，长列表避免 `ScrollView + VStack`
- 图片用 `KFImage`，给 `.placeholder`，列表里限制尺寸避免大图解码
- 上拉加载在最后一项 `.onAppear` 触发，并加 `hasMore` / `isLoadingMore` 双重防抖

## 8. 错误处理

- 网络层：统一解包 `{code,message,data}`，`code != 0` → `APIError.business`
- 401：清 token + 回登录态（`SessionStore.signOut()`）
- 全局崩溃：`NSSetUncaughtExceptionHandler`（Debug 打印，Release 上报）
- 用户可见文案走本地化 key，日志保留原文

## 9. 配置与环境

- 环境变量放 `Configs/{Debug,Release}.xcconfig`，经 `Info.plist` 的 `$(VAR)` 注入
- `AppConfig` 是唯一读取入口（Bundle → 类型转换）
- xcconfig 中 URL 的 `//` 必须转义成 `/ $() /`（去掉空格），否则被当注释截断

## 10. 代码风格

- Swift 官方风格；类型与关键方法写 `///` 中文文档注释
- 单文件 ≤ 300 行，超了拆 `Components/`
- 禁止 `!` 强解包（常量 URL、已知安全 fallback 除外）
- `View` 拆分为 `body` + `@ViewBuilder private var content` + 私有子视图
- 常量集中在 `AppTheme`，不散落魔法数字
