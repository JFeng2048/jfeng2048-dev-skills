# 原型到 Jetpack Compose 映射

原型（HTML/CSS、设计稿或 PRD）与 Compose 不是一一对应关系。保留用户体验意图，并采用原生布局、状态、导航与无障碍语义。

## 1. 布局与尺寸

| 原型 | Compose | 备注 |
| --- | --- | --- |
| 纵向/横向排列 | `Column` / `Row` | 用约束、权重和窗口尺寸适配，不依赖固定像素 |
| 层叠布局 | `Box` + `Modifier.align` | `offset` 只用于视觉微调，不模拟整页绝对布局 |
| 等宽网格 | `LazyVerticalGrid` | 多条目列表使用 lazy 容器 |
| 长列表 | `LazyColumn` + 稳定 `key` | 避免 `Column` 一次性创建全部条目 |
| 整页滚动 | `verticalScroll` 或 `LazyColumn` | 按内容长度和交互选择 |
| 吸顶头部 | `stickyHeader` | 使用前核对当前 Compose API 稳定性 |
| 固定底部操作 | `Scaffold(bottomBar = ...)` | 正确消费 `innerPadding` 与系统 inset |
| CSS px / rem | `dp` / `sp` | 字体使用 `sp` 并支持系统字体缩放 |

间距、颜色、字体和形状优先映射到 `core:designsystem` 的语义 token。不要在 feature 页面散落魔法值；组件只在语义清楚且复用有价值时抽取。

## 2. 视觉样式

| CSS | Compose |
| --- | --- |
| `background-color` | `Modifier.background` / `Surface` |
| `border` | `Modifier.border` |
| `border-radius` | `RoundedCornerShape` + 设计 token |
| `box-shadow` | `Card` / `Surface` 的 Material elevation |
| `linear-gradient` | `Brush.linearGradient` |
| `opacity` | `Modifier.alpha` 或颜色 alpha |
| `font-weight` | `FontWeight` |
| 文本省略 | `maxLines` + `TextOverflow.Ellipsis` |
| 固定内外边距 | `core:designsystem` spacing token |

不必为了追求像素级复刻而引入多层阴影、硬编码绝对坐标或不可访问的颜色对比。需要近似效果时记录差异及理由。

## 3. 控件和交互

| 原型 | Compose | 注意事项 |
| --- | --- | --- |
| 按钮 | `Button` / `OutlinedButton` / `TextButton` | 反馈 loading、disabled 与提交结果 |
| 输入框 | `OutlinedTextField` | 设置键盘类型、错误与辅助文案 |
| 下拉选择 | `ExposedDropdownMenuBox` 或产品合适控件 | 支持键盘与无障碍 |
| 图片 | 项目选定的图片加载器 | 占位、失败回退、内容描述齐全 |
| 标签 | Material chip 或设计系统组件 | 长文本与窄屏测试 |
| Loading | `CircularProgressIndicator` 或骨架屏 | 不遮挡已有可读数据 |
| Toast/提示 | Snackbar 或项目统一反馈组件 | 一次性事件不要用可重复布尔状态 |
| 确认弹窗 | `AlertDialog` | 破坏性动作需明确主次操作 |
| 权限 | Activity Result API / 项目权限封装 | 用户动作触发，拒绝后有降级 |

## 4. 页面状态与业务域

页面由所属 `feature:<domain>:impl` 提供，路由契约由其 `api` 描述，导航协议由 `core:router` 提供。不要再把所有路由硬编码到 core 的 feature 引用表中。

每个取数页面按实际用例处理 loading、空、失败、重试、刷新和已有数据时的失败状态。列表页使用稳定 key 和有界分页；避免在每次重组时触发请求。Composable 展示状态并向上回传用户动作，ViewModel/Repository 边界按架构约定执行。

## 5. 图片与资源

- 图片失败时提供占位/错误状态和有意义的 content description。
- 优先复用项目已有图标库；不因单个图标增加整套大体积依赖。
- 自定义矢量资源放在所属 Android module 的 `res/drawable`。
- 原型远程图可能失效；生成工程应使用确定可访问的资源或明确的本地占位，不假装网络资源验证成功。

## 6. 屏幕与系统适配

- 页面正确处理状态栏、导航栏、键盘与 edge-to-edge inset。
- 至少核对原型目标手机宽度和窄屏；平板/折叠屏按业务布局使用窗口尺寸类别。
- 支持字体缩放、深色模式、横竖屏和进程重建中与该页面相关的状态。
- 控件提供语义、焦点、触控反馈与合适的目标尺寸；减少动态效果偏好按需处理。

## 7. 无法直接映射时

不臆造。选最接近的原生交互，记录 TODO 说明原型与实现的差异，并把产品行为差异列入待确认项。
