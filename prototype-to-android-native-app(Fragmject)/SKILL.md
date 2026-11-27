---
name: "prototype-to-android-native-app"
description: "从 HTML/CSS 原型、设计稿或 PRD 生成可运行的原生 Android 多模块工程，默认采用 Kotlin、Jetpack Compose、build-logic convention plugins，以及 app / feature / core / service 分层架构（兼容标准扁平 feature/<domain> 与大型工程 feature/<domain>/{api,impl}）。用户提到「原型转 Android」「生成 Android 原生项目」「Compose 工程」「把原型做成 Kotlin App」时使用。"
---

# Prototype to Android Native App

## 目标与原则

将原型中的页面、交互和视觉规则落成可运行、可维护的 Android 原生工程。先读取工作区已有工程和原型；已有工程优先沿用其包名、构建基线和用户已有模块，不覆盖或强行迁移无关代码。新建工程默认采用本文的多模块结构。

原型是产品行为和视觉的输入，不是照搬 HTML 的布局实现。保留用户可见流程、信息层级、状态与交互反馈；将布局、导航、权限和生命周期转换为 Android 原生模式。信息不明确时列出待确认项，不臆造业务规则。

## 推荐工程结构

按业务域拆分 `feature/`；公共基础能力归 `core/`；独立系统服务归 `service/`（按需）；`app/` 只负责组装与导航编排。模块应有真实职责，不为凑树形结构创建空目录或空 Gradle module。跨进程 IPC、Service、Receiver 和 Provider 只在业务确实需要时实现。

### 默认标准结构（`app` + `feature` + `core` + `service` + `build-logic`）

```text
<ProjectRoot>/
├── app/                        # 应用入口：Application、MainActivity、NavHost 与全局 DI 装配
│
├── feature/                    # 产品功能（每个 <domain> 为独立模块，或按需拆分为 api/impl）
│   └── <domain>/               # 如 camera / gallery / reveal / studio-gif / studio-splitter / studio-video
│
├── core/                       # 公共基础能力（只按实际需要创建对应模块）
│   ├── common/                 # 协程调度器、Result 封装、通用工具扩展（纯 Kotlin）
│   ├── model/                  # 领域模型、枚举与稳定跨模块数据结构（纯 Kotlin）
│   ├── data/                   # Repository 实现：协调 database / network / storage
│   ├── database/               # Room / Bundled SQLite、DAO、迁移与种子数据
│   ├── designsystem/           # 主题、设计 token、基础 Compose 组件
│   ├── ui/                     # 跨 feature 复用的业务 UI 组件与状态容器
│   ├── camera/                 # 相机系统能力（按需）
│   ├── media/                  # 媒体处理能力：滤镜、切块、编解码等（按需）
│   ├── image/                  # 图像处理引擎（按需）
│   ├── sensor/                 # 传感器能力（按需）
│   ├── storage/                # 文件与媒体存储、MediaStore 导出、DataStore（按需）
│   ├── network/                # HTTP 客户端、鉴权刷新、重试退避（按需）
│   ├── worker/                 # WorkManager 后台调度与状态回写（按需）
│   └── ...                     # 其他横切基础设施（如 router / startup / monitor / ads 等按需引入）
│
├── service/                    # 独立系统服务：前台服务、后台长任务、Bound/IPC Service（按需）
│
├── build-logic/                # 构建逻辑：convention plugins 与架构校验
├── gradle/
│   └── libs.versions.toml                      # 集中依赖与插件版本
├── docs/                       # PRD、原型、数据库设计与开发计划（如已有则保留）
├── AGENTS.md                   # 仓库协作规范（如已有则保留）
├── settings.gradle.kts
├── build.gradle.kts
└── gradle.properties
```

> **结构模式选择**：
> - **标准模式（默认优先，如 Luma）**：每个 `:feature:<domain>` 为单个 Gradle module，直接依赖 `:core:*`；页面路由由 `:app` 中的 NavHost 协调，跨域数据与契约由 `:core:model` / `:core:data` 承接。
> - **API/Impl 拆分模式（按需）**：当同一业务域存在跨 feature 强契约调用、独立动态交付或需要隔离编译边界时，才将 `:feature:<domain>` 拆为 `:feature:<domain>:api` + `:feature:<domain>:impl`；不要在小型或单体聚合应用中机械空转套娃。
> - **`service/` 模块**：当系统存在独立生命周期的前台服务、媒体后台导出服务、跨进程 Bound Service 或系统推送/同步服务时，放入 `service/<name>/`（如 `:service:media-export`），由 `:app` 装配或通过 `:core:*` 接口解耦。

每个 Gradle module 有自己的 `build.gradle.kts`。`build-logic` 可作为 included build，按应用、Android library、Compose library、Feature library、纯 Kotlin library 等角色提供 convention plugins。

## 模块依赖硬规则

```text
:app ───────────────> :core:*、:service:* 与需要装配的 :feature:*
:feature:* ─────────> 必需的 :core:*（标准模式，feature 之间禁止互相依赖）
:feature:A:impl ────> :feature:A:api 与 :feature:B:api（仅 API/Impl 拆分模式）
:service:* ─────────> 必需的 :core:*（独立系统服务不得反向依赖 :feature:* 或 :app）
:core:* ────────────> :core:*（单向依赖）
```

- `core` 禁止依赖任何 `feature` 或 `service`；`core` 不导入页面实现、导航目标或业务 UI。
- `feature` 之间禁止直接互相依赖（标准模式下 `:feature:A` 不得依赖 `:feature:B`，页面跳转由 `:app` NavHost 协调，跨域数据通过 `:core:model` 与 `:core:data` 共享）。
- `feature:<domain>:impl` 只能依赖自己的 `api`、必要的 `core` 和其他 feature 的 `api`；禁止依赖其他 feature 的 `impl`。
- `feature:<domain>:api` 只暴露跨模块契约：路由/参数、Service 控制接口、URI/权限常量。Compose 页面、Repository 和组件实现留在 impl。
- `service` 模块只依赖必要的 `:core:*`，禁止依赖 `:feature:*` 或 `:app`。
- `feature`、`service` 与 `core` 都不得依赖 `app`；app 是组合根，不是业务公共库。
- `:core:model` 与 `:core:common` 保持纯 Kotlin（无 Android Framework 依赖），便于单元测试与跨域复用。
- 只有确实需要 Android API、资源或 Manifest 时才使用 Android library plugin；纯领域模型、通用工具与纯接口契约使用纯 Kotlin library plugin。
- 模块依赖图必须无环。创建跨域调用前先判断能否用 `:core:model` / API 契约或路由边界解决。

## 技术版本策略

新建项目时，在生成 Gradle 文件之前核实官方发布信息和兼容矩阵，为 AGP、Gradle、JDK、Kotlin、Compose、KSP、Hilt/Room 编译器及实际用到的依赖选择**当前最新的稳定且互相兼容版本组合**。优先查 Android Developers、Kotlin/Gradle 官方文档、Google Maven 和 Maven Central；不使用未经验证的单个“最新版”拼装，也不默认采用 alpha、beta、RC 或实验 API。

把本次核实出的具体版本写入生成项目的 `gradle/libs.versions.toml`，让该项目可复现；本技能、配置基线和活动模板不得固化过时版本号。已有工程保留其 wrapper、JDK 和 version catalog，除非用户要求升级。无法访问发布信息时，不猜测或声称最新；可以完成原型分析和模块计划，但暂停新工程 Gradle 配置渲染，直到能核验当前版本。

依赖集中在 version catalog，模块脚本不直接写版本号。KSP 与 Kotlin/compiler plugin 等有配套要求时按官方兼容规则成组选择，不能只升级其中一项。

版本输入文件必须附带 `resolution.checked_at`、`resolution.selection = "latest-stable-compatible"`、`resolution.compatibility_verified = true` 和实际核验的 HTTPS 官方来源；模板 renderer 会拒绝缺失元数据、动态版本、预发布版本或占位值，并把来源写入新工程 README。若不能完成在线核验，不得伪标为 latest-compatible。

## 原型转工程工作流

### 1. 盘点原型和仓库

读取 HTML/CSS、截图、PRD、现有 Gradle 配置和设计资源。抽取页面、业务域、导航关系、用户动作、表单校验、加载/空/错误状态、图片资源、权限需求和视觉 token。

如果工作区已有 Android 工程，先总结当前模块图、构建版本和未提交改动；在其上做最小必要的调整。只有新建工程才套用完整推荐结构。

### 2. 划分业务域与契约

按业务所有权划分 `feature/<domain>`，不是按单个技术层拆 feature。确定采用标准模式（`:feature:<domain>`）还是 API/Impl 拆分模式（`:feature:<domain>:api` + `:feature:<domain>:impl`）。

绘制模块依赖图并核对硬规则。基础视觉 token 与基础控件进入 `core:designsystem`；跨 feature 复用业务 UI 进入 `core:ui`；领域模型进入 `core:model`；平台通用能力进入对应 `core/*`（如 `camera`、`media`、`image`、`sensor`、`storage`、`database`、`data`）；独立系统服务进入 `service/*`。只实例化实际需要的模块，不为结构示例凑空目录。

### 3. 建立构建约定与版本目录

1. 核实当前最新稳定兼容工具链和依赖版本，记录查询来源/日期。
2. 生成版本 JSON，记录具体版本、核验日期、官方 HTTPS 来源和兼容性确认；在根 `gradle/libs.versions.toml` 集中声明版本，项目生成后固定本次解析结果。
3. 通过 `build-logic` 的 convention plugins 统一 SDK、JVM/Kotlin、Compose、Feature、DI/KSP、测试、Manifest 和依赖方向约束。
4. 在 `settings.gradle.kts` 显式 include 所有实际创建的 modules；根脚本只做版本目录、插件和仓库编排。
5. Included build 如需访问根 version catalog，显式导入根 catalog 并验证路径；不要在 build-logic 另造一套重复版本。

### 4. 实现业务 UI 和数据流

在 `feature/<domain>`（或拆分模式下的 `impl`）中实现该域页面。Composable 只渲染状态和发出动作；ViewModel 维护不可变 UiState 并调用 Repository；Repository 编排该域的数据源（本地优先项目可由 `:core:data` 协调 `:core:database` 与 `:core:storage`）。

覆盖原型主路径和实际适用的加载、空、失败、重试、表单无效及重复提交状态。使用生命周期感知的 Flow 收集；长列表用 LazyColumn/LazyGrid 和稳定 key。按原型还原系统栏 inset、字体缩放、窗口尺寸和深色模式，不把 CSS px 当 dp。

### 5. 接入系统组件与启动

- `Application` 只做轻量进程级装配与必要初始化，不在主线程同步阻塞执行数据库迁移、媒体扫描、网络预热或大型 SDK 初始化。
- 如需多阶段并发初始化编排，可引入 `:core:startup`（或由 `app` 轻量协程协调）定义无环任务图，首屏非关键任务延迟执行。
- 全局静态 Receiver、FileProvider 与入口 Activity 放在 `app`；独立系统服务声明在对应 `service/*` 或业务 `feature/*` 的 Manifest。Manifest merge 后的结果是最终校验依据。
- IPC、长任务 Service、Provider 和敏感权限按需设计，不为了“企业级”堆入无业务价值的组件。

### 6. 校验和交付

运行 `resources/tools/validate_project.py`（自动识别标准单层 `feature/<domain>` 与 `feature/<domain>/{api,impl}` 模式），检查模块依赖、版本目录、包名、Manifest/exported、UI 状态与测试；然后按环境运行 Gradle Sync、受影响模块测试和 app 编译。静态校验不能代替 Gradle 构建。

文本模板未打包 Gradle wrapper 启动脚本和 JAR。环境具备兼容 Gradle 后，生成对应版本的 wrapper，再使用 wrapper 执行构建与测试；不可用时使用 Android Studio 配置的 Gradle 运行，并如实报告。

交付说明模块图、原型实现范围、运行命令和实际验证结果。列出尚未确认的交互、后端契约、权限和未验证的设备行为；不得宣称未运行的构建或真机测试已通过。

## Android 组件与安全边界

- Activity、Service、Receiver、Provider 都明确 owner、进程、生命周期、启动条件及外部可达性。`android:exported` 必须显式声明，默认 `false`；需要外部入口时才最小化开放并校验调用方、参数和权限。
- Receiver 校验 action 与 extras；动态 Receiver 使用目标 Android 版本要求的 exported 标志并在生命周期结束时注销。Receiver 仅轻量分发，不执行长任务。
- 可延迟后台工作优先 WorkManager。只有符合 Android 平台政策且用户可感知的持续工作才用前台 Service，不实现无正当理由的保活。
- Provider 默认 `exported="false"`；对外时限制 authority、URI 路径、读写权限和输入大小。禁止开放任意文件/SQL 能力。早初始化 Provider 明确初始化顺序。
- 只有确实跨进程才使用 AIDL、Messenger 或受限 Provider。定义版本兼容、超时、断连/重连、取消、权限与错误协议；普通模块调用不包装成 IPC。
- 权限最小化并按用户动作申请，说明拒绝后的降级路径。密钥和 token 不写日志、不硬编码、不通过 Intent extras 明文跨域传递。
- monitor 的上下文必须脱敏，不采集 token、消息正文等敏感数据。

## Compose 映射规则

| 原型表达 | Android 实现 | 注意事项 |
| --- | --- | --- |
| 垂直/水平布局 | `Column` / `Row` | 用约束适配小屏，不依赖固定像素 |
| 网格和长列表 | `LazyVerticalGrid` / `LazyColumn` | 提供稳定 key，避免创建全量节点 |
| 绝对定位 | `Box` + `Modifier.align` | 不用 offset 模拟整页布局 |
| CSS px / rem | `dp` / `sp` | 字体使用 sp，遵循系统字体缩放 |
| 图片 | Compose 图片组件 | 提供加载/错误状态和内容描述 |
| hover / active | 点击、长按、焦点和 Material interaction | 兼顾键盘、触控和无障碍 |
| CSS transition | `animate*AsState` / `AnimatedVisibility` | 尊重减少动态效果与生命周期 |
| 页面跳转 | `:app` NavHost 或 `:core:router` 契约 | 参数使用稳定 ID，不传整个业务对象 |
| CSS 颜色/token | `core:designsystem` 语义 token | feature 页面不散落硬编码色值 |

交互控件提供语义标签、触控反馈、合适的触控目标，以及明确的禁用/处理中状态。系统返回、进程重建、字体放大、深色模式和窗口尺寸变化都属于原生还原的一部分。

## 建议验证清单

- Gradle Sync、依赖解析、受影响 module 编译和 app 实际 build variant。
- `core` 无 feature 依赖；feature impl 不依赖其他 impl；API 不泄漏实现类型；依赖图无环。
- version catalog 版本均已核实且兼容，模块脚本没有散落版本号。
- Manifest merger report 无意外导出组件、权限、authority 冲突或重复 intent filter。
- startup DAG 无环；关键路径有界，非首屏任务不阻塞首帧。
- 路由参数、进程重建、返回栈、Receiver 重复触发、Provider 非法 URI、Service 断连行为有测试或明确验证。
- UI 覆盖原型关键页面及主要状态；ViewModel/Repository 有单测，组件边界有适用的集成测试。
- 只报告实际运行的命令和结果；未执行的设备、变体或真机测试明确标为未验证。
