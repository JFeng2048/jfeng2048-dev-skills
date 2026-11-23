# 原型解析契约（proto_context.json）

所有页面生成以 `proto_context.json` 为唯一输入。解析器只产出**结构化初稿**，缺失信息写入 `diagnostics.need_confirm`，补齐后再落码。

## 1. 顶层结构

```json
{
  "project": {},
  "design": {},
  "pages": [],
  "navigation": {},
  "capabilities": {},
  "diagnostics": {}
}
```

## 2. project

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `project_name` | string | ✅ | PascalCase，合法 Swift 模块名（`^[A-Z][A-Za-z0-9]{2,}$`） |
| `app_title` | string | ✅ | 显示名，写入 `CFBundleDisplayName` |
| `bundle_id` | string | ✅ | 反域名，全小写点分 |
| `bundle_id_prefix` | string | ✅ | `bundle_id` 去掉最后一段 |
| `ios_min` | string | ✅ | `17.0` / `18.0`（SwiftData 要求 ≥17） |
| `source_type` | string | ✅ | `html` / `image` / `prd` |
| `language` | string | ✅ | 固定 `swift` |
| `ui` | string | ✅ | 固定 `swiftui` |

## 3. design

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `primary_color` | string | 6 位 hex（不带 `#`），渲染时拆成 RGB 写入 colorset |
| `dark_theme` | bool | 是否生成深色 appearance（默认 true） |
| `radius_style` | string | `sm` / `md` / `lg` |
| `density` | string | `compact` / `comfortable` |

## 4. pages[]

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `page_name` | string | ✅ | 小写 kebab，如 `home` |
| `route` | string | ✅ | `home`（首屏）或 `detail(id:)` |
| `view_class` | string | ✅ | `HomeView` |
| `viewmodel_class` | string | ✅ | `HomeViewModel` |
| `layout` | string | ✅ | `list` / `detail` / `form` / `profile` / `grid` |
| `is_home` | bool | | 是否首屏 |
| `needs_auth` | bool | | 是否要求登录（默认 true） |
| `components` | string[] | | 组件名（PascalCase） |
| `data_model` | string | | 领域模型名，如 `Skill` |
| `data_fields` | string[] | | 字段 camelCase，用于模型与 mock |
| `interactions` | object[] | | `{ "event": "tap", "action": "navigate", "to": "detail" }` |
| `states` | string[] | | 必须含 `loading` / `empty` / `failed` / `loaded` |
| `notes` | string[] | | 视觉或业务备注 |

### layout 判定

| layout | 特征 |
| --- | --- |
| `list` | 重复卡片、纵向滚动、分页、搜索 |
| `detail` | 单条内容 + 底部操作 |
| `form` | 多个输入控件 + 提交按钮 |
| `profile` | 头像 + 信息区 + 设置行 |
| `grid` | 2~4 列宫格 |

## 5. navigation

```json
{
  "root": "login_gate",
  "tab_bar": { "enabled": false, "items": [] },
  "routes": [
    { "case": "detail", "associated": ["id: String"], "view": "DetailView" },
    { "case": "mine", "associated": [], "view": "MineView" }
  ]
}
```

- `root` 固定 `login_gate`（由 `SessionStore.isLoggedIn` 分流）
- `routes[].case` 必须与 `AppRoute` 枚举一致，且在 `RootView` 的 `navigationDestination` 中处理
- `tab_bar.enabled = true` 时 `items` 为 2~5 项，每项含 `route` / `title_key` / `system_image`

## 6. capabilities（按需开关）

```json
{
  "login": true,
  "swiftdata_cache": true,
  "search": true,
  "dark_mode": true,
  "localization": ["zh-Hans", "en"],
  "photo_picker": false,
  "lottie": false,
  "tab_bar": false,
  "guide": false
}
```

`photo_picker = true` 时才允许写 `NSPhotoLibraryUsageDescription`；`lottie` 才允许加 Lottie 包。

## 7. diagnostics

```json
{
  "parse_errors": [],
  "assumptions": ["布局按关键词推断为 list"],
  "need_confirm": ["页面跳转关系", "空态文案"],
  "extracted_texts": ["技能广场", "暂无数据"]
}
```

`need_confirm` 非空时，生成前必须逐条确认或在输出末尾列出。

## 8. 完整性校验（生成前必做）

- [ ] `project_name` 匹配 `^[A-Z][A-Za-z0-9]{2,}$`
- [ ] `bundle_id` 全小写点分，且与 `bundle_id_prefix` 前缀一致
- [ ] 每个 `page.route` / `view_class` / `viewmodel_class` 唯一
- [ ] 每个页面 `states` 含 loading / empty / failed
- [ ] `data_fields` 至少含一个业务主键（不要叫 `id`，用 `<domain>ID`）
- [ ] `design.primary_color` 为 6 位 hex
- [ ] `capabilities` 与实际要生的依赖一致（开 lottie 才加包）
- [ ] `need_confirm` 已处理

用 `tools/preview_plan.py` 先看计划再落盘。
