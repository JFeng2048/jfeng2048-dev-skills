# 原型解析契约（proto_context.json）

所有页面的生成都以 `proto_context.json` 为唯一输入。解析器（`tools/parse_prototype.py`）只产出**结构化初稿**，缺失信息标进 `diagnostics.need_confirm`，由人或模型补齐后再生码。

## 1. 顶层结构

```json
{
  "project": {},
  "design": {},
  "pages": [],
  "navigation": {},
  "permissions": [],
  "diagnostics": {}
}
```

## 2. project

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `project_name` | string | ✅ | 工程名，kebab-case，同时作为 `rootProject.name` |
| `app_title` | string | ✅ | 应用显示名，写入 `strings.xml` 的 `app_name` |
| `package_name` | string | ✅ | 应用包名，必须匹配 `^[a-z][a-z0-9]*(\.[a-z][a-z0-9_]*)+$` |
| `min_sdk` | int | ✅ | 24 / 26 / 29 |
| `target_sdk` | int | ✅ | 默认 35 |
| `compile_sdk` | int | ✅ | 默认 35 |
| `source_type` | string | ✅ | `html` / `image` / `prd` |
| `language` | string | ✅ | 固定 `kotlin` |
| `ui` | string | ✅ | 固定 `compose` |

## 3. design

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `primary_color` | string | 6 位 hex，不带 `#`，如 `2B6DE5` |
| `dark_theme` | bool | 是否生成暗色适配（默认 true，跟随系统） |
| `radius_style` | string | `sm` / `md` / `lg`，映射到 `Dimens.cardRadius` |
| `density` | string | `compact` / `comfortable`，影响列表间距 |

## 4. pages（数组，每项一个页面）

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `page_name` | string | ✅ | 小写 kebab，如 `home`、`order-list` |
| `route` | string | ✅ | 路由，如 `home`、`detail/{skillId}` |
| `screen_class` | string | ✅ | `HomeScreen` |
| `viewmodel_class` | string | ✅ | `HomeViewModel` |
| `layout` | string | ✅ | `list` / `detail` / `form` / `profile` / `grid` |
| `is_home` | bool | | 是否起始页 |
| `needs_auth` | bool | | 是否要求登录（默认 true） |
| `components` | string[] | | 页面内组件，PascalCase |
| `data_model` | string | | 领域模型名，如 `Skill` |
| `data_fields` | string[] | | 字段 camelCase，用于生成模型与 mock |
| `interactions` | object[] | | `{ "event": "tap", "action": "navigate", "to": "detail" }` |
| `states` | string[] | | 必须含 `loading` / `empty` / `error` / `loaded` |
| `notes` | string[] | | 视觉或业务备注 |

### layout 判定规则

| layout | 特征 |
| --- | --- |
| `list` | 重复卡片、垂直滚动、分页 |
| `detail` | 单条内容、标题 + 正文 + 操作按钮 |
| `form` | 多个输入控件 + 提交按钮 |
| `profile` | 头像 + 信息区块 + 设置行 |
| `grid` | 2~4 列宫格入口 |

## 5. navigation

```json
{
  "start_destination": "home",
  "bottom_nav": {
    "enabled": false,
    "items": []
  }
}
```

- `start_destination` 必须是 `pages[].route` 中的一项
- `bottom_nav.items` 的元素为 `{ "route": "home", "label": "首页", "icon": "Home" }`
- 开启底部导航时，`items` 数量必须 2~5，且都在 `pages` 中出现过

## 6. permissions

按需声明，**不要无理由加**：

| 场景 | 权限 |
| --- | --- |
| 联网（几乎所有工程） | `INTERNET` |
| 网络状态判断 | `ACCESS_NETWORK_STATE` |
| 拍照 | `CAMERA` |
| 选图（Android 13+） | `READ_MEDIA_IMAGES` |
| 定位 | `ACCESS_FINE_LOCATION` |

## 7. diagnostics

```json
{
  "parse_errors": [],
  "assumptions": ["布局按关键词推断为 list"],
  "need_confirm": ["页面跳转关系", "空态文案"],
  "extracted_texts": ["技能广场", "暂无数据"]
}
```

`need_confirm` 非空时，生成前必须逐条向用户确认或在输出末尾列出。

## 8. 完整性校验（生成前必做）

- [ ] `package_name` 合法且与 `package_path` 一致
- [ ] 每个 `page.route` 唯一，且 `screen_class` 唯一
- [ ] 每个页面 `states` 含 loading / empty / error
- [ ] `navigation.start_destination` 存在
- [ ] `data_fields` 至少包含 `id`
- [ ] `design.primary_color` 为 6 位 hex
- [ ] `need_confirm` 已处理

可用 `tools/preview_plan.py` 先看生成计划，再落盘。
