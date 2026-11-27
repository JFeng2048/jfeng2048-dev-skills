# prototype-to-android-native-app

将 HTML/CSS 原型、设计稿或 PRD 转换为可运行的原生 Android 多模块工程。默认使用 Kotlin、Jetpack Compose、Gradle convention plugins，并按业务域拆分 feature `api` / `impl`。

## 架构原则

- `app` 是组合根，只负责宿主入口、系统级组件和模块装配。
- `core` 提供横切能力，禁止依赖任何 `feature`。
- `feature:<domain>:impl` 依赖自身 API、必要的 core 和其他 feature 的 API；禁止依赖其他 feature 的 impl。
- 路由与跨域能力通过稳定 API 契约连接，不硬编码跨模块实现类。
- `build-logic` 统一构建约定，`gradle/libs.versions.toml` 集中管理插件和依赖版本。
- Service、Receiver、Provider、IPC 和权限只在实际需要时生成，并遵守最小暴露原则。

## 版本策略

新工程生成时核实官方发布信息和兼容矩阵，选择当前最新的稳定兼容版本；本技能和配置不固定具体版本。生成项目将这次解析结果写入自己的 version catalog，以保证之后可复现。已有工程不自动升级。

## 资源

| 路径 | 用途 |
| --- | --- |
| `SKILL.md` | 原型分析、工程生成、模块与组件边界、验证流程 |
| `resources/specifications/architecture_conventions.md` | 模块职责、依赖规则、启动 DAG、Manifest 与 IPC 安全 |
| `resources/specifications/prototype_parser_contract.md` | `proto_context.json` 数据契约 |
| `resources/specifications/compose_mapping_rules.md` | 原型到 Compose 的映射 |
| `resources/config/dependency_baseline.json` | 最新稳定兼容版本解析策略，不存固定版本 |
| `resources/config/naming_rules.json` | module、源码包与 API/impl 命名边界 |
| `resources/templates/modular_project_structure/` | app/core/feature api+impl/build-logic 多模块模板 |
| `resources/tools/parse_prototype.py` | HTML 原型解析初稿 |
| `resources/tools/preview_plan.py` | 展示预计生成的模块与文件 |
| `resources/tools/render_template.py` | 渲染模块工程模板 |
| `resources/tools/validate_project.py` | 静态校验模块结构与依赖边界 |

## 使用

```bash
python resources/tools/parse_prototype.py 原型.html \
  --package com.example.skillswap \
  --project skill-swap-android \
  --domain skills \
  --title "技能互换" \
  --min-sdk <product-min-sdk> \
  --target-sdk <current-platform-target> \
  --compile-sdk <current-stable-api> \
  --jdk <compatible-jdk> \
  --versions-json versions.json \
  --out proto_context.json

python resources/tools/preview_plan.py proto_context.json
python resources/tools/render_template.py proto_context.json ./skill-swap-android
python resources/tools/validate_project.py ./skill-swap-android
gradle -p ./skill-swap-android validateArchitecture
```

解析产物是初稿。生成前核对页面/业务域、导航、权限和设计 token。`versions.json` 必须记录解析日期、官方来源与兼容性确认；renderer 会拒绝未解析占位符、预发布版本和动态 selector。

`versions.json` 结构如下。尖括号内容仅表示字段位置，执行前必须替换为本次从官方发布信息与兼容矩阵核实的稳定版本和链接，不要复制旧项目里的版本：

```json
{
  "resolution": {
    "checked_at": "YYYY-MM-DD",
    "selection": "latest-stable-compatible",
    "compatibility_verified": true,
    "sources": [
      "https://developer.android.com/build/releases/gradle-plugin",
      "https://docs.gradle.org/current/userguide/compatibility.html",
      "https://kotlinlang.org/docs/gradle-configure-project.html",
      "https://github.com/google/ksp/releases",
      "https://maven.google.com",
      "https://repo.maven.apache.org/maven2"
    ]
  },
  "versions": {
    "gradle": "<resolved>",
    "agp": "<resolved>",
    "kotlin": "<resolved>",
    "ksp": "<resolved-for-kotlin>",
    "compose_bom": "<resolved>",
    "core_ktx": "<resolved>",
    "lifecycle": "<resolved>",
    "activity_compose": "<resolved>",
    "navigation": "<resolved>",
    "hilt": "<resolved>",
    "room": "<resolved>",
    "datastore": "<resolved>",
    "okhttp": "<resolved>",
    "coroutines": "<resolved>",
    "junit": "<resolved>"
  }
}
```

模板不包含 Gradle wrapper 启动脚本和 JAR；有兼容的本机 Gradle 后，可在生成项目目录执行 `gradle wrapper --gradle-version <resolved-gradle> --distribution-type bin`，之后用生成的 wrapper 编译、测试。

版本核验日期必须是运行生成当天；过期 JSON 会被拒绝。来源应覆盖本工程实际使用的插件、库和兼容矩阵。静态校验不替代 Gradle Sync、测试或实际编译。若无法访问官方版本信息，可以先完成原型分析和模块计划，但不要渲染新的 Gradle 配置或声称已使用最新版本。交付时注明所有真正执行过的验证步骤。
