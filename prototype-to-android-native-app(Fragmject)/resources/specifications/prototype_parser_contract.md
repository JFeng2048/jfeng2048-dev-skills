# 原型解析契约（proto_context.json）

解析器输出结构化初稿，不直接决定最终业务模块图。生成前必须由 agent/开发者核对业务域、路由、权限与构建版本；HTML 启发式结果不能视为产品事实。

## 1. 顶层结构

```json
{
  "project": {},
  "design": {},
  "features": [],
  "pages": [],
  "navigation": {},
  "permissions": [],
  "diagnostics": {}
}
```

## 2. project

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `project_name` | string | 是 | Gradle root project 名，kebab-case |
| `app_title` | string | 是 | 应用显示名，写入 app 的 `strings.xml` |
| `package_name` | string | 是 | application 包名，匹配合法 Java package |
| `min_sdk` | int/null | 生成前必需 | 按产品设备覆盖要求决定，不由解析器固定 |
| `target_sdk` | int/null | 生成前必需 | 按当前平台/Google Play 要求和产品策略决定 |
| `compile_sdk` | int/null | 生成前必需 | 使用当前可用的稳定 SDK |
| `jdk` | string/null | 生成前必需 | 选择与当前 Gradle/AGP 兼容的 JDK |
| `versions` | object | 生成前必需 | 本次核实出的兼容稳定版本，供模板写入 version catalog |
| `source_type` | string | 是 | `html` / `image` / `prd` |
| `language` | string | 是 | `kotlin` |
| `ui` | string | 是 | `compose`，除非已有工程使用其他体系 |

`versions` 的必需键为 `gradle`、`agp`、`kotlin`、`ksp`、`compose_bom`、`core_ktx`、`lifecycle`、`activity_compose`、`navigation`、`hilt`、`room`、`datastore`、`okhttp`、`coroutines`、`junit`。值必须来自生成时的官方发布信息与兼容矩阵；catalog 对 BOM 管理的 Compose artifacts 不重复声明版本。

版本文件还必须包含 `resolution` 元数据：当天的 `checked_at`（`YYYY-MM-DD`）、`selection`（`latest-stable-compatible`）、`compatibility_verified`（`true`）和非空 HTTPS 官方 `sources` URL 数组。renderer 将这些来源和日期写入生成项目 README，拒绝过期、无元数据或未确认兼容的版本集。

`gradle` / AGP / JDK / Kotlin / Compose / KSP / processor 必须组成可用组合。新工程生成后将已解析的具体版本写入项目文件以便复现；本契约和配置文件不提供过时固定值。已有项目优先沿用自身版本。

## 3. design

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `primary_color` | string | 6 位 hex，不带 `#`；不能可靠推断时标记待确认 |
| `dark_theme` | bool/null | 是否跟随系统适配 |
| `radius_style` | string/null | `sm` / `md` / `lg`，需按原型校准 |
| `density` | string/null | `compact` / `comfortable` |

## 4. features

每个 feature 对应一个业务域，不是一个页面。由生成前的分析合并同一业务域的页面。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `domain` | string | 是 | 小写 kebab-case，如 `auth`、`orders` |
| `pages` | string[] | 是 | 此业务域包含的 `pages[].page_name` |
| `needs_android_manifest` | bool | 否 | 是否有属于本域的 Android 组件 |
| `notes` | string[] | 否 | 模块边界或待确认项 |

module 路径生成规则为 `:feature:<domain>:api` 与 `:feature:<domain>:impl`。按实际需要创建，不因空泛架构图生成空模块。

## 5. pages

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `page_name` | string | 是 | 小写 kebab-case |
| `domain` | string | 是 | 所属 feature domain |
| `route` | string | 是 | 业务路由契约 |
| `screen_class` | string | 是 | 如 `HomeScreen` |
| `viewmodel_class` | string | 是 | 如 `HomeViewModel` |
| `layout` | string | 是 | `list` / `detail` / `form` / `profile` / `grid` / `custom` |
| `is_home` | bool | 否 | 是否为主入口 |
| `needs_auth` | bool/null | 否 | 登录需求；不确定时不要默认强制登录 |
| `components` | string[] | 否 | 页面内组件名 |
| `data_model` | string | 否 | 所属业务模型 |
| `data_fields` | string[] | 否 | 字段名，用于模型/数据分析 |
| `interactions` | object[] | 否 | 用户动作及目标 |
| `states` | string[] | 否 | 适用状态，如 loading/empty/error/loaded |
| `notes` | string[] | 否 | 视觉或业务备注 |

## 6. navigation 与 permissions

`navigation.start_destination` 引用已定义 page route。feature API 声明路由/参数契约，`:core:router` 提供通用协议，impl 注册目的地；不在 core 中维护依赖业务模块的全局硬编码路由表。

权限按需声明，不从模板无条件复制。动态权限需要记录触发用户动作、拒绝后的降级路径和 Android 版本差异。只有静态或跨模块需要的 URI/权限常量才进入 feature API。

## 7. diagnostics

保留 `parse_errors`、`assumptions`、`need_confirm` 与 `extracted_texts`。任何启发式识别都放在 assumptions；module/domain、登录要求、目标 SDK、权限和外部组件导出策略不确定时放进 need_confirm。

## 8. 生成前完整性检查

- [ ] 包名合法，app namespace/applicationId 与目录策略一致
- [ ] 页面 route 唯一，页面都归属真实业务域
- [ ] 一个业务域的页面已合并到同一 feature，而不是按页面建模块
- [ ] `features[].pages` 与 `pages[].domain` 双向一致
- [ ] start destination 存在
- [ ] 权限、登录和组件导出策略已核对
- [ ] min/target/compile SDK 与 JDK 已根据项目需求决定
- [ ] 所需版本已核实为当前最新的稳定兼容组合
- [ ] 待确认项已回答或在交付说明中保留

先运行 `tools/preview_plan.py` 检查模块图和输出路径，再调用 renderer。
