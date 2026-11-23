# SkillSwap

技能互换 —— 原生 iOS 工程（SwiftUI + MVVM + SwiftData）。

## 技术栈

| 项 | 选型 |
| --- | --- |
| UI | SwiftUI（iOS 17.0+） |
| 架构 | MVVM + Combine 单向状态流 |
| 本地存储 | SwiftData（`@Model`）+ UserDefaults（token） |
| 网络 | Alamofire + `RequestInterceptor` |
| 图片 | Kingfisher |
| 工程生成 | XcodeGen（`project.yml`） |
| 依赖管理 | SPM |

## 目录

```text
SkillSwap/
├── App/          入口与根视图（登录态分流 + 导航栈）
├── Core/         配置、网络、存储、路由、主题、组合根
├── Data/         模型、DTO、仓库、mock
├── Features/     Home / Detail / Login / Mine
└── Resources/    Info.plist、Assets、本地化
```

依赖方向：`Features → Repositories → (DTO | Model | Mock)`。View 不发请求，ViewModel 不碰 SwiftUI。

## 运行

```bash
# 1. 安装 XcodeGen（只需一次）
brew install xcodegen

# 2. 生成工程
cd SkillSwap父目录
xcodegen generate

# 3. 打开并运行
open SkillSwap.xcodeproj
```

- 首次打开会拉取 SPM 依赖（Alamofire / Kingfisher）
- 选 iPhone 模拟器直接 Run（无需签名）
- **真机运行**：在 `project.yml` 的 `settings.base` 里填入 `DEVELOPMENT_TEAM`，重新 `xcodegen generate`

> `*.xcodeproj` 不入库（见 `.gitignore`），所有工程配置以 `project.yml` 为准。

## mock 与真实接口

```ruby
# Configs/Debug.xcconfig
API_BASE_URL = https:/$()/dev-api.example.com/
USE_MOCK = YES
```

> xcconfig 里 `//` 是注释，URL 必须写成 `https:/$()/host`，否则会被截断。

- `USE_MOCK = YES`：数据来自 `Data/Mock/MockData.swift`，无需后端
- 改 `NO` 并填 `API_BASE_URL`：走 Alamofire，接口路径在 `Core/Networking/APITarget.swift` 补

## 新增页面

1. `Features/<Name>/` 下建 `XxxView.swift` + `XxxViewModel.swift`
2. `Core/Router/AppRoute.swift` 加 case
3. `RootView.destination(for:)` 里补 `switch` 分支
4. 文案加到 `zh-Hans.lproj` 与 `en.lproj`（key 必须一致）

## 常见问题

| 现象 | 原因 / 处理 |
| --- | --- |
| `xcodegen: command not found` | 未安装 XcodeGen：`brew install xcodegen` |
| 编译报 SwiftData 相关错误 | 部署目标低于 iOS 17 |
| 真机提示无签名 | `project.yml` 填 `DEVELOPMENT_TEAM` |
| `API_BASE_URL` 变成 `https:` | xcconfig 里 URL 没有用 `$()` 转义 `//` |
| 图片全部空白 | 未联网或 URL 失效；`KFImage` 会回落到 placeholder |
| Swift 6 严格并发报错 | 模板使用 Swift 5 语言模式，迁移需给全局状态加 `@MainActor` |

## 已知取舍

- 模板使用 Swift 5 语言模式（`SWIFT_STRICT_CONCURRENCY = minimal`），便于开箱即用；
- token 默认存 UserDefaults，生产建议换 Keychain；
- 缓存回落只做第一页，避免分页拼接错乱。
