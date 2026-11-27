# Android 多模块架构与模块契约

本规范用于将原型实现为可扩展的 Kotlin/Compose 工程。目标是清晰所有权、可验证依赖方向和安全的平台组件边界，而不是追求模块数量。

## 1. 模块职责

| 模块 | 拥有的职责 | 不应拥有 |
| --- | --- | --- |
| `build-logic` | convention plugins；SDK/JVM/Kotlin/Compose/Feature/DI、测试与静态约束 | 业务逻辑、业务依赖图 |
| `app` | Application、启动/宿主 Activity、NavHost 路由编排、全局配置与模块装配 | feature 页面实现、业务 Repository、领域规则 |
| `feature:<domain>` | **标准模式**：该业务域的 UI、ViewModel、UiState 与域内组件 | 其他 feature 模块的直接依赖 |
| `feature:<domain>:api` | **拆分模式（按需）**：路由/参数、Service 控制接口、URI/权限常量等稳定契约 | UI、Repository/数据实现或可变状态 |
| `feature:<domain>:impl` | **拆分模式（按需）**：该域 UI、ViewModel、业务数据源及业务组件实现 | 其他 feature 的实现细节 |
| `service:<name>` | **独立系统服务（按需）**：前台服务、媒体导出服务、Bound/IPC Service 等 | feature UI 或反向依赖 `:app` / `:feature` |
| `core:common` | 稳定、低变更、纯 Kotlin 的协程调度器、Result 封装与通用工具 | Android Framework 强依赖或业务模型 |
| `core:model` | 纯 Kotlin 领域模型、枚举与稳定跨模块数据结构 | UI 状态或持久化实现细节 |
| `core:data` | 统一 Repository 实现，协调 database / network / storage | 页面状态或 Compose 组件 |
| `core:database` | Room / Bundled SQLite、建表/迁移、DAO 与种子数据 | UI 或具体页面逻辑 |
| `core:storage` | 文件与媒体存储、MediaStore 导出、FileProvider / DataStore | 业务页面状态 |
| `core:designsystem` | 设计 token、主题、可复用基础 Compose 组件 | 某个业务页面或业务文案 |
| `core:ui` | 跨 feature 复用的业务 UI 组件与状态展示壳（按需） | 单个 feature 独占的页面或 Repository |
| `core:camera` / `media` / `image` / `sensor` | 硬件/媒体/图像/传感器系统能力封装（按需） | 业务页面流程与导航 |
| `core:network` / `worker` / `startup` / `router` / `monitor` / `component-runtime` / `ipc` | 网络栈、后台调度、启动 DAG、通用路由、监控、组件运行时或 IPC（按需） | feature 页面或具体业务模型 |

树中的 `core/*`、`feature/*`、`service/*` 通常各自是独立 Gradle module（如 `:core:designsystem`、`:feature:camera`、`:service:media-export`），而不是普通文件夹。按项目真实需要创建模块，不要留下没有代码职责的空模块。

## 2. 依赖图

```text
app
├── core:*（app 直接使用的宿主能力）
├── service:*（按需接入的独立系统服务）
└── feature:*（标准模式）或 feature:*:impl（API/Impl 拆分模式）

feature:alpha      ──> core:*（标准模式，禁止依赖 feature:beta）
feature:alpha:impl ──> feature:alpha:api / feature:beta:api / core:*（拆分模式）
feature:alpha:api  ──> 最少的通用契约，例如 core:model / core:router
service:worker-svc ──> core:*（独立系统服务禁止依赖 feature:* 或 app）

core:* ──> core:*（单向、有明确分层）
```

允许边以外的方向一律禁止：

- `core:* -> feature:*` 或 `core:* -> service:*`
- `service:* -> feature:*` 或 `service:* -> app`
- `feature:A -> feature:B`（标准模式下 feature 间不得互依赖）
- `feature:A:impl -> feature:B:impl`
- `feature:A:api -> feature:A:impl`
- `feature:*:api -> Compose 页面、Repository 实现或数据库实现`
- `feature:*` / `core:* -> app`
- 为打开另一个 feature 的页面而直接引用其 Activity/Composable 实现类

`settings.gradle.kts` 是模块图的唯一显式入口。新增模块时同步更新 settings、version catalog/插件约定、依赖检查和测试。CI 可使用 Gradle dependency insight 或自定义静态检查阻断禁止边。

## 3. API 与路由契约

业务 API 只暴露跨模块必须知道的信息。路由参数使用稳定、可序列化的标识符，不传整个 Entity/DTO。`core:router` 不导入任何 feature；feature API 通过通用 route 类型描述路由，impl 在组合阶段注册页面目标。

跨 feature 数据协作优先定义小而稳定的 API。Service 控制优先公开业务接口，而不是 Binder/Service 类本身；只有真实跨进程时才映射为 AIDL/Messenger 等 IPC 协议。URI 与权限常量由数据 owner 的 feature API 定义，避免调用方重复拼写 authority/path。

## 4. Gradle 与构建约定

- `gradle/libs.versions.toml` 是插件和依赖版本的单一来源；模块脚本不直接写版本号。
- 新工程生成时核实官方最新稳定版本和兼容矩阵，再将本次解析结果写入新项目 catalog；技能文档、基线 JSON 与模板不固化旧版本。
- 保持 AGP、Gradle、JDK、Kotlin、Compose plugin、KSP 及处理器之间兼容；按兼容组合一起选择，不单独追求某一依赖的最高版本。
- convention plugins 按模块角色组织，如 Android application、Android library、Compose library、纯 Kotlin API；避免一个万能插件包含大量业务条件。
- Gradle included build 若需读取根 version catalog，显式导入 `../gradle/libs.versions.toml` 并测试路径，避免 build-logic 自有 catalog 与根 catalog 漂移。
- 仓库、插件解析、依赖锁定和 catalog 可见性沿用现有工程约定；不得为了使用模板覆盖已有设置。
- `applicationId`、签名配置和应用变体配置归 application module，不放入公共 API 或 Android library。
- convention plugin 可以校验依赖/Manifest 规则，但不应隐式增加业务 feature 依赖。

## 5. Application 与启动 DAG

`MainApplication` 保持轻量，只注册启动 DAG 和必要的基础设施。`core:startup` 的任务应声明：

- 唯一任务 ID 与依赖任务；
- 是否属于首屏关键路径；
- 执行线程/调度器及并行要求；
- 超时、失败和降级策略；
- 可脱敏记录的耗时指标。

启动图必须无环。只有首屏确实依赖的任务进入关键路径；网络预热、非首屏数据库、远程配置和重型 SDK 按需延迟。不得用同步等待把异步初始化重新阻塞在主线程。
模板执行器通过 observer 上报每个任务的耗时和失败类型；默认只记录任务标识、时长和异常类型，不输出异常消息或业务数据。

启动任务不得记录 token、消息正文、PII 或完整 Intent。初始化器之间的顺序用显式依赖表达，不依赖不稳定的类加载顺序。

`SplashOrShellActivity` 承担启动协调与宿主内容容器，不承载业务流程或重初始化；遵循 Android SplashScreen、返回栈和任务语义。

## 6. Android 组件与 Manifest

Android Manifest 会在构建时合并，最终 merged manifest 才是安全与组件检查依据。

- app Manifest：启动/主壳 Activity、确属全局的静态 Receiver、统一对外 Provider、全局权限与 application 配置。
- feature impl Manifest：该业务域 Activity、Service、Receiver 和 Provider；组件默认仅本应用可访问。
- 所有 Activity/Service/Receiver/Provider 显式设置 `android:exported`。默认 `false`；需要外部入口时记录调用方和权限模型。
- intent-filter 只声明必要 action/category/data，并在接收端再次校验输入。不要以自定义 action 名称代替授权。
- Provider 默认 `exported=false`。对外时限制 authority、URI 路径、读写权限和数据范围。Authority 使用唯一的 manifest placeholder，避免 flavor/feature 冲突。
- 静态 Receiver 仅用于系统实际要求或明确的全局入口；动态 Receiver 使用目标 API 要求的 exported 标志并在生命周期结束时注销。
- Service 必须有清晰启动/停止协议。延迟任务优先 WorkManager；前台 Service 仅用于平台政策允许且用户可感知的持续工作。
- Manifest 权限遵循最小权限和运行时申请要求；不要从模板无条件复制通知、媒体、位置、相机或存储权限。

`core:component-runtime` 可以分为 `activity/`、`service/`、`receiver/`、`provider/` 等能力模块或包；封装必须保留 Android 组件真实生命周期，不替代调用方权限检查。

## 7. IPC、Service 与后台任务

- 只有确实存在进程隔离或跨进程调用需求时才选择 AIDL、Messenger 或受限 Provider。定义接口版本、超时、断连/重连、取消、调用方权限与错误协议。
- 单进程 feature 间调用不包装成 IPC；跨模块进程内调用通过 API 契约。
- 后台可延迟任务优先 WorkManager。只有满足平台前台服务类型、通知和用户可见性要求时才用 Foreground Service。
- 不实现无正当业务理由的保活、静态广播绕过限制或无条件重启任务。

## 8. Repository、数据所有权与取消

业务 Repository 位于各自 feature impl，负责协调数据源、DTO 到领域模型映射、缓存策略和错误语义；UI 不直接访问网络、Room 或 DataStore。

`core:network` 提供传输层和通用认证能力；具体 endpoint、DTO 及错误到业务结果的映射由业务域拥有。`core:storage` 提供共享存储设施，业务 Entity/DAO/迁移由数据 owner 维护。共享数据库必须定义 schema 导出、迁移测试和表所有权，不能用跨 feature 直接 import 代替模块契约。

协程取消必须继续传播，不能被 `catch (Exception)` 转换成普通业务错误。错误 UI 给出可理解反馈和安全重试动作；不要将原始服务端异常或内部 URL 原样展示给用户。

## 9. Feature UI 状态

```text
feature/<domain>/impl/.../ui/
├── <flow>/
│   ├── <Screen>.kt
│   ├── <ViewModel>.kt
│   ├── <UiState>.kt
│   └── components/
└── navigation/
```

- Composable 渲染不可变状态并派发动作；ViewModel 不持有 Activity/View，不直接访问 Retrofit/DAO。
- 页面数据状态按用例覆盖 loading、空、错误、刷新和已有数据时的失败，不为状态表而堆无业务意义字段。
- 一次性导航/提示事件按项目既有 Flow/Channel 约定处理，避免可重复消费的布尔标志。
- 页面组件优先复用 `core:designsystem`；只有稳定且跨域复用的模式才提升到 core。
- UI 测试放在拥有该页面的 feature 模块，公共组件测试放在 designsystem。

## 10. 静态与运行时验证

1. 检查 settings/module graph 和禁止依赖边。
2. 检查 version catalog 是否集中、已核实且兼容，检查模块脚本是否有硬编码版本。
3. Gradle Sync 与依赖解析，编译受影响的 feature api/impl、core 和 app variant。
4. 运行相关单测、Room migration 测试与路由/启动图测试。
5. 检查 merged manifest、exported components、权限和 authority。
6. 在目标 API/屏幕尺寸上验证主流程、返回栈、重建、深色模式与字体缩放。

只报告实际执行的检查。由于 SDK、模拟器或网络不可用而跳过的步骤应明确标注。
