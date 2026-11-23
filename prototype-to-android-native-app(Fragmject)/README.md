# prototype-to-android-native-app

## 1. 这个技能是干嘛的

把**原型**（HTML/CSS 代码、设计图截图、PRD 页面清单）转换成**可直接用 Android Studio 打开并运行**的原生 Android 工程。

模板范式对齐开源项目 **[Fragmject](https://github.com/miaowmiaow/fragmject)**（Kotlin + Compose M3 + Hilt + Navigation + Room + Retrofit + Coil，单 Activity、MVI/MVVM），并按 2025+ 稳定版本做现代化适配。

| 你提供 | 技能产出 |
| --- | --- |
| 原型 HTML / 设计稿截图 / PRD 页面清单 | 完整 Gradle 工程 + 分层代码 + 四个页面范本 + mock 数据 + 单元测试 |

## 2. 技术基线

| 项 | 选型 |
| --- | --- |
| 语言 / 构建 | Kotlin 2.1 / AGP 8.7.3 / Gradle 8.11.1 / JDK 17 |
| UI | Jetpack Compose + Material3（BOM 2024.12.01） |
| 架构 | 单 Activity + MVI（`UiState` / `Event` / `StateFlow`） |
| 依赖注入 | Hilt 2.53.1（KSP） |
| 路由 | Navigation Compose 2.8.5 |
| 本地存储 | Room 2.6.1 + DataStore Preferences |
| 网络 | Retrofit 2.11 + OkHttp 4.12 + kotlinx.serialization |
| 图片 | Coil 2.7 |
| minSdk / targetSdk | 24 / 35 |

> Fragmject 原文提到的 `Navigation3` 仍属实验期，本技能默认用 **Navigation Compose**；用户明确要求时才切 `androidx.navigation3`。

## 3. 技能项目结构

```text
prototype-to-android-native-app/
├── SKILL.md
├── README.md
└── resources/
    ├── config/
    │   ├── naming_rules.json           # 包名 / 类名 / 路由 / 资源命名
    │   ├── dependency_baseline.json    # 版本基线与替代方案
    │   └── design_tokens.json          # 颜色 / 间距 / 圆角 / 字号
    ├── specifications/
    │   ├── prototype_parser_contract.md  # proto_context.json 契约
    │   ├── architecture_conventions.md   # 分层与 MVI 约定
    │   └── compose_mapping_rules.md      # 原型 → Compose 映射
    ├── templates/
    │   └── project_structure/          # 可运行骨架（含四个页面范本）
    ├── tools/
    │   ├── parse_prototype.py          # HTML → proto_context.json
    │   ├── preview_plan.py             # 预览生成计划
    │   ├── render_template.py          # 按 context 渲染骨架（替换占位符 / 包路径）
    │   └── validate_project.py         # 21 项静态校验
    ├── demo_input/
    │   └── index.html                  # 示例原型输入
    └── demo_output/
        └── skill-swap-android/         # 示例产物（已通过 21 项校验）
```

## 4. 模板里的四个页面范本

| 布局 | 范本 | 关键实现 |
| --- | --- | --- |
| 列表 | `feature/home` | `LazyColumn` + 三态 + 触底加载 + 刷新按钮 |
| 详情 | `feature/detail` | 可滚动内容 + 底部固定操作栏 + Toast |
| 表单 | `feature/login` | `OutlinedTextField` + 校验 + 提交禁用 + 密码遮罩 |
| 个人中心 / 设置 | `feature/mine` | 头像信息 + 设置行 + 退出登录二次确认 |

新页面**复制改造**对应范本，不要凭空写。

## 5. 工具用法

### 5.1 解析原型

```bash
python resources/tools/parse_prototype.py 原型.html \
  --package com.example.skillswap \
  --project skill-swap-android \
  --title "技能互换" \
  --out proto_context.json \
  --min-sdk 24 \
  --permissions INTERNET,ACCESS_NETWORK_STATE
```

`--package` 必填且必须是合法包名；解析结果是**初稿**，重点看 `diagnostics.need_confirm`。

### 5.2 预览生成计划

```bash
python resources/tools/preview_plan.py proto_context.json
```

输出包名、包路径、页面清单、计划生成的文件列表。

### 5.3 校验生成结果

```bash
python resources/tools/validate_project.py ./skill-swap-android
python resources/tools/validate_project.py ./skill-swap-android --json
```

21 项静态检查（不依赖 Android SDK / Gradle / 网络）：

| # | 检查项 | 失败常见原因 |
| --- | --- | --- |
| 1 | `settings.gradle.kts` 声明 `:app` | 骨架没复制全 |
| 2 | 版本目录包含核心依赖 | 漏 Compose / Hilt / Room / Retrofit / Coil |
| 3 | `namespace` 与 `applicationId` 一致 | 只改了一处，或占位符未替换 |
| 4 | Manifest 只声明一个 Activity | 又建了第二个 Activity |
| 5 | Application 类使用 `@HiltAndroidApp` | 忘记注解或 manifest 没指向它 |
| 6 | `MainActivity` 用 `@AndroidEntryPoint` + `setContent` | 迁移残留 View 写法 |
| 7 | 未使用 XML 页面布局 | 出现 `res/layout/activity_*.xml` |
| 8 | 未混用 View 体系 | 出现 RecyclerView / Fragment |
| 9 | 路由常量与 NavHost 注册一一对应 | 建了目录但忘记 `composable(...)` |
| 10 | 每个页面有配套 ViewModel 与 UiState | 只有 Screen |
| 11 | ViewModel 不依赖 Compose 与 Api | ViewModel 里 import Compose 或 Api |
| 12 | 页面未直接访问网络层 | Screen 里 import `data.remote` |
| 13 | Room 三件套齐全 | 缺 `@Database` / `@Dao` / `@Entity` |
| 14 | mock 数据 ≥ 10 条 | mock 太少看不出布局问题 |
| 15 | 列表页三态齐全 | 只有 loading |
| 16 | 主题集中且页面无硬编码颜色 | `Color(0xFF...)` 出现在 feature |
| 17 | 字符串资源有效 | `app_name` 为空或未替换 |
| 18 | 存在单元测试 | `app/src/test` 为空 |
| 19 | 包声明与包名一致 | 目录改了但 `package` 没改 |
| 20 | 构建脚本含 mock 开关与 KSP | 用了 kapt，或缺 `buildConfigField` |
| 21 | 无未替换占位符 | `{{package_name}}` 等残留 |

退出码：`0` 通过（可有警告），`1` 有 error，`2` 参数错误。

## 6. 生成后如何运行

1. Android Studio 打开工程目录，等待 Gradle Sync
2. 缺 SDK 路径时，复制 `local.properties.example` 为 `local.properties` 填 `sdk.dir`
3. 运行 `app` 到模拟器 / 真机

> 仓库未内置 `gradle-wrapper.jar`（二进制文件），Android Studio 打开会自动补齐，或本机执行 `gradle wrapper --gradle-version 8.11.1`。

## 7. mock 与真实接口切换

```kotlin
// app/build.gradle.kts
debug {
    buildConfigField("boolean", "USE_MOCK", "true")
    buildConfigField("String", "BASE_URL", "\"https://dev-api.example.com/\"")
}
```

改 `USE_MOCK = false` + 填 `BASE_URL`，再按 `data/remote/*Api.kt` 补路径即可，页面与 ViewModel 不用动。

## 8. 验证情况

| 验证项 | 结果 |
| --- | --- |
| `parse_prototype.py` 解析 `demo_input/index.html` | 通过（layout=list，主色正确识别 `2B6DE5`，未误取背景灰） |
| `preview_plan.py` 输出计划 | 通过（45 个文件计划，含包路径） |
| `render_template.py` 渲染 `demo_output/skill-swap-android` | 通过（57 文件，0 残留占位符，2 个 `{{package_path}}` 目录正确展开） |
| `validate_project.py` 校验示例工程 | **21 项全部通过：错误 0，警告 0** |
| Kotlin 括号配平体检（全量 `.kt`） | 通过 |
| Gradle 实际编译（`assembleDebug`） | **未执行**（本机无 Android SDK / Gradle） |

因此工程**按官方 API 静态编写并通过结构校验，但未做真实编译/真机验证**。首次使用请先 `Sync` 一次；若编译报错，优先核对 `gradle/libs.versions.toml` 中 **Kotlin / KSP / AGP** 三者版本是否配套。

复现验证命令：

```bash
python resources/tools/parse_prototype.py resources/demo_input/index.html \
  --package com.example.skillswap --project skill-swap-android \
  --title "技能互换" --page-name home --out /tmp/proto_context.json

python resources/tools/render_template.py /tmp/proto_context.json \
  resources/demo_output/skill-swap-android --force

python resources/tools/validate_project.py resources/demo_output/skill-swap-android
```

## 9. 与其它技能的关系

| 技能 | 目标平台 | 技术栈 |
| --- | --- | --- |
| **`prototype-to-android-native-app`（本技能）** | Android 原生（手机 / 平板 / 折叠屏） | Kotlin + Compose + Hilt |
| `prototype-to-flutter-app` | Android / iOS / Web / 桌面 | Flutter（Dart） |
| `prototype-to-app-uniappx` | App / 小程序 / H5 | uni-app x（Vue 语法） |
| `prototype-to-taro-app` | 小程序 / H5 / RN | Taro（Vue3 或 React） |

只要 **Android 原生体验**（Compose、Hilt、Room、深度系统能力）选本技能；要一套代码多端则选 Flutter / uni-app x / Taro。

## 10. 相关文档

| 内容 | 路径 |
| --- | --- |
| 技能定义（AI 读） | `SKILL.md` |
| 原型解析契约 | `resources/specifications/prototype_parser_contract.md` |
| 分层与 MVI 约定 | `resources/specifications/architecture_conventions.md` |
| 原型 → Compose 映射 | `resources/specifications/compose_mapping_rules.md` |
| 依赖基线 | `resources/config/dependency_baseline.json` |
| Fragmject 参考 | <https://github.com/miaowmiaow/fragmject> |
| Compose 官方文档 | <https://developer.android.com/develop/ui/compose> |
