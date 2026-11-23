# prototype-to-ios-native-app

## 1. 这个技能是干嘛的

把**原型**（HTML/CSS 代码、设计图截图、PRD 页面清单）转换成**能用 Xcode 直接 Run** 的原生 iOS 工程。

模板范式对齐开源项目 **[AwesomeSwift](https://github.com/JoeyBling/AwesomeSwift)**（SwiftUI + MVVM + Combine + SwiftData + Alamofire + Kingfisher，中文注释、内置登录/信息流/详情/设置/表单/暗黑/国际化），并按 iOS 17+ 稳定 API 做了现代化适配。

| 你提供 | 技能产出 |
| --- | --- |
| 原型 HTML / 设计稿截图 / PRD 页面清单 | XcodeGen 工程声明 + 分层 SwiftUI 代码 + 四个页面范本 + mock 数据 + 单元测试 |

## 2. 技术基线

| 项 | 选型 |
| --- | --- |
| 语言 / UI | Swift 5.10 + SwiftUI（iOS 17.0+） |
| 架构 | MVVM + Combine 单向状态流 |
| 依赖注入 | 手写组合根 `AppContainer`（无第三方 DI） |
| 本地存储 | SwiftData（`@Model` / `ModelContainer`）+ UserDefaults 存 token |
| 网络 | Alamofire 5.9 + `RequestInterceptor` |
| 图片 | Kingfisher 7.x |
| 工程生成 | XcodeGen（`project.yml`，不手写 `.xcodeproj`） |
| 依赖管理 | SPM |
| 并发检查 | `SWIFT_STRICT_CONCURRENCY = minimal`（Swift 5 语言模式） |

> 不直接生成 `.xcodeproj`：pbxproj 是二进制/易冲突格式，手写不可靠。用 `xcodegen generate` 从 `project.yml` 生成，既开箱可用又可版本管理。

## 3. 技能项目结构

```text
prototype-to-ios-native-app/
├── SKILL.md
├── README.md
└── resources/
    ├── config/
    │   ├── naming_rules.json          # 工程名 / 类型 / 路由 / 本地化 key
    │   ├── dependency_baseline.json   # 工具链与 SPM 依赖基线
    │   └── design_tokens.json         # 颜色 / 间距 / 圆角 / 字号
    ├── specifications/
    │   ├── prototype_parser_contract.md  # proto_context.json 契约
    │   ├── architecture_conventions.md   # 分层与 MVVM 约定
    │   └── swiftui_mapping_rules.md      # 原型 → SwiftUI 映射
    ├── templates/
    │   └── project_structure/         # 可运行骨架（4 个页面范本）
    ├── tools/
    │   ├── parse_prototype.py         # HTML → proto_context.json
    │   ├── preview_plan.py            # 预览生成计划
    │   ├── render_template.py         # 按 context 渲染骨架
    │   └── validate_project.py        # 22 项静态校验
    ├── demo_input/index.html
    └── demo_output/skill-swap-ios/    # 示例产物（已通过校验）
```

## 4. 模板里的四个页面范本

| 布局 | 范本 | 关键实现 |
| --- | --- | --- |
| 列表 / 信息流 | `Features/Home` | `List` + `LoadState` 三态 + 上拉加载 + `.refreshable` + `.searchable` + Combine 防抖 |
| 详情 | `Features/Detail` | `ScrollView` + `.safeAreaInset` 底部操作栏 + Alert |
| 表单 | `Features/Login` | `TextField`/`SecureField` + 校验 + 提交禁用 |
| 个人中心 / 设置 | `Features/Mine` | `List` 分组 + `Label` 设置行 + 退出登录二次确认 |

新页面**复制改造**对应范本，不要凭空写。

## 5. 工具用法

### 5.1 解析原型

```bash
python resources/tools/parse_prototype.py 原型.html \
  --project SkillSwap \
  --package-bundle com.example.skillswap \
  --title "技能互换" \
  --out proto_context.json \
  --ios-min 17.0
```

- `--project` 必填，必须是 **PascalCase 合法 Swift 模块名**
- `--package-bundle` 必填，反域名全小写
- `--ios-min` 低于 17.0 会直接报错（SwiftData 依赖）
- 解析结果是**初稿**，重点看 `diagnostics.need_confirm`

### 5.2 预览生成计划

```bash
python resources/tools/preview_plan.py proto_context.json
```

输出工程名、Bundle ID、页面清单、启用能力、计划文件列表。

### 5.3 渲染骨架

```bash
python resources/tools/render_template.py proto_context.json ./SkillSwap --force
```

替换 `{{project_name}}` / `{{bundle_id}}` / `{{primary_r/g/b}}` 等占位符，并把 `{{project_name}}/` 目录改成真实工程名；输出残留占位符清单（应为空）。

### 5.4 校验生成结果

```bash
python resources/tools/validate_project.py ./SkillSwap
python resources/tools/validate_project.py ./SkillSwap --json
```

22 项静态检查（不需要 macOS / Xcode）：

| # | 检查项 | 失败常见原因 |
| --- | --- | --- |
| 1 | `project.yml` 存在且工程名合法 | 用了 kebab-case 或中文名 |
| 2 | 最低 iOS ≥ 17.0 | 复制了老模板 |
| 3 | SPM 含 Alamofire / Kingfisher | 漏改 `packages` |
| 4 | App / 测试 Target / Scheme 齐全 | 手写 pbxproj 时漏 target |
| 5 | 全工程只有一个 `@main` | 多入口 |
| 6 | 入口注入 `modelContainer` + 组合根 | 忘了 `.environmentObject` |
| 7 | Info.plist 关键键齐全 | 缺 `API_BASE_URL` / `USE_MOCK` / `UILaunchScreen` |
| 8 | xcconfig 环境配置正确 | URL 没写 `$()` 转义，被 `//` 注释截断 |
| 9 | `NavigationStack` 覆盖 `AppRoute` | 加了 case 没在 `RootView` 处理 |
| 10 | View 与 ViewModel 配对 | 只写了 View |
| 11 | View 未直接访问网络层 | 页面里 `import Alamofire` |
| 12 | ViewModel 不依赖 SwiftUI / 网络 / 图片库 | VM 里 `import SwiftUI` |
| 13 | Repository 协议 + 默认实现 | 直接把 `APIClient` 塞进 VM |
| 14 | `@Model` 与缓存回落存在 | 忘了 `FetchDescriptor` |
| 15 | mock ≥ 10 条 | mock 太少看不出布局问题 |
| 16 | 列表页三态齐全 | 只有 loading |
| 17 | 颜色只来自 Asset | 页面里 `Color(red:...)` |
| 18 | 中英文本地化 key 一致 | 只加了一种语言 |
| 19 | 存在单元测试 | Tests 为空 |
| 20 | Bundle ID 一致且非占位 | 占位符没替换 |
| 21 | 无 Storyboard / XIB / UIViewController | 混入 UIKit 页面 |
| 22 | 无未替换占位符 | `{{project_name}}` 残留 |

退出码：`0` 通过（可有警告），`1` 有 error，`2` 参数错误。

## 6. 生成后如何运行

```bash
brew install xcodegen          # 只需一次
cd SkillSwap的上级目录
xcodegen generate
open SkillSwap.xcodeproj
```

- 选 iPhone 模拟器直接 Run（mock 已内置）
- 真机需在 `project.yml` 的 `settings.base` 填 `DEVELOPMENT_TEAM`，再 `xcodegen generate`

## 7. mock 与真实接口切换

```ruby
# Configs/Debug.xcconfig
API_BASE_URL = https:/$()/dev-api.example.com/
USE_MOCK = YES
```

改 `USE_MOCK = NO` + 填 `API_BASE_URL`，再按 `Core/Networking/APITarget.swift` 补路径即可，页面与 ViewModel 不用动。

> xcconfig 里 `//` 是注释符，所以 URL 必须写成 `https:/$()/host`。

## 8. 验证情况

| 验证项 | 结果 |
| --- | --- |
| `parse_prototype.py` 解析 `demo_input/index.html` | 通过（layout=list，view=HomeView，主色正确识别 `2B6DE5`，未误取背景灰） |
| `preview_plan.py` 输出计划 | 通过（40 个文件计划，含能力开关与待确认项） |
| `render_template.py` 渲染 `demo_output/skill-swap-ios` | 通过（49 文件，0 残留占位符，1 个 `{{project_name}}` 目录正确改名，主色 RGB 拆分为 2B/6D/E5） |
| `validate_project.py` 校验示例工程 | **22 项全部通过：错误 0，警告 0** |
| Swift 括号配平体检（全量 `.swift`） | 通过（balanced） |
| JSON（配置 + Asset colorset）解析 | 通过 |
| `xcodegen generate` + Xcode 编译 | **未执行**（Windows 环境，无 Xcode） |

复现验证命令：

```bash
python resources/tools/parse_prototype.py resources/demo_input/index.html \
  --project SkillSwap --package-bundle com.example.skillswap \
  --title "技能互换" --out /tmp/ios_proto_context.json

python resources/tools/render_template.py /tmp/ios_proto_context.json \
  resources/demo_output/skill-swap-ios --force

python resources/tools/validate_project.py resources/demo_output/skill-swap-ios
```

> 工程**按官方 API 静态编写并通过结构校验，但未做真实 Xcode 编译**。首次使用请先 `xcodegen generate` + `xcodebuild`，编译报错优先检查 iOS 部署版本与 SPM 依赖解析。

## 9. 与其它技能的关系

| 技能 | 目标平台 | 技术栈 |
| --- | --- | --- |
| **`prototype-to-ios-native-app`（本技能）** | iOS 原生（iPhone / iPad） | SwiftUI + MVVM + SwiftData |
| `prototype-to-android-native-app` | Android 原生 | Kotlin + Compose + Hilt |
| `prototype-to-flutter-app` | Android / iOS / Web / 桌面 | Flutter（Dart） |
| `prototype-to-app-uniappx` | App / 小程序 / H5 | uni-app x（Vue 语法） |
| `prototype-to-taro-app` | 小程序 / H5 / RN | Taro（Vue3 或 React） |

只要 **iOS 原生体验**（SwiftUI、SwiftData、系统能力、App Store 上架）选本技能；要一套代码多端则选 Flutter / uni-app x / Taro。

## 10. 相关文档

| 内容 | 路径 |
| --- | --- |
| 技能定义（AI 读） | `SKILL.md` |
| 原型解析契约 | `resources/specifications/prototype_parser_contract.md` |
| 分层与 MVVM 约定 | `resources/specifications/architecture_conventions.md` |
| 原型 → SwiftUI 映射 | `resources/specifications/swiftui_mapping_rules.md` |
| 依赖基线 | `resources/config/dependency_baseline.json` |
| AwesomeSwift 参考 | <https://github.com/JoeyBling/AwesomeSwift> |
| XcodeGen 文档 | <https://github.com/yonaskolb/XcodeGen> |
| SwiftData 文档 | <https://developer.apple.com/documentation/swiftdata> |
