# 原型 → Compose 映射规则

原型（HTML/CSS 或设计稿）与 Compose 不是一一对应关系。本文给出**确定性映射**，避免每次生成风格漂移。

## 1. 布局容器

| 原型 | Compose | 备注 |
| --- | --- | --- |
| `display: block` 纵向堆叠 | `Column` | 默认 `verticalArrangement = Arrangement.spacedBy(Dimens.sm)` |
| `display: flex; flex-direction: row` | `Row` | 对齐用 `verticalAlignment = Alignment.CenterVertically` |
| 层叠 / 绝对定位 | `Box` + `Modifier.align(Alignment.Xxx)` | 禁止用 `offset` 模拟定位 |
| `display: grid`（等宽卡片） | `LazyVerticalGrid(columns = GridCells.Fixed(n))` | 条目多时用 `Adaptive(minSize)` |
| `overflow: scroll` 长列表 | `LazyColumn` + `items(key)` | 必须给 key，避免复用错乱 |
| 整页滚动 | `Column(Modifier.verticalScroll(rememberScrollState()))` | 详情页常用 |
| 吸顶头部 | `LazyColumn { stickyHeader { ... } }` | 需 `@OptIn(ExperimentalFoundationApi::class)` |
| 底部固定按钮 | `Scaffold(bottomBar = { ... })` | 用 `innerPadding`，不要自己加 padding |
| 顶部标题栏 | `Scaffold(topBar = { AppTopBar(title) })` | 统一走 `core/designsystem/component` |

## 2. 视觉样式

| CSS | Compose |
| --- | --- |
| `background-color` | `Modifier.background(color)` 或 `Surface(color = ...)` |
| `border: 1px solid X` | `Modifier.border(1.dp, color, shape)` |
| `border-radius` | `RoundedCornerShape(Dimens.cardRadius)` |
| `box-shadow: 0 2px 8px` | `Card(elevation = CardDefaults.cardElevation(1.dp))` |
| `linear-gradient(...)` | `Brush.linearGradient(listOf(a, b))` + `Modifier.background(brush)` |
| `opacity` | `Modifier.alpha(x)` 或颜色的 alpha 通道 |
| `font-weight: 600` | `FontWeight.SemiBold` |
| `font-size: 14px` | `MaterialTheme.typography.bodyMedium`（14sp） |
| 固定行高 | `lineHeight = 20.sp` |
| `text-overflow: ellipsis` | `maxLines = 1, overflow = TextOverflow.Ellipsis` |
| 多行省略 | `maxLines = 2, overflow = TextOverflow.Ellipsis` |
| `padding: 16px` | `Modifier.padding(16.dp)` → 用 `Dimens.lg` |
| `margin-top: 8px` | `Spacer(Modifier.height(8.dp))` 或 `Arrangement.spacedBy` |

**禁止**：在 `feature/` 下出现 `Color(0xFF...)`、`16.dp` 这类魔法值（统一 `Dimens` / `MaterialTheme`）。

## 3. 控件

| 原型 | Compose |
| --- | --- |
| `<button>` | `Button` / `OutlinedButton` / `TextButton` |
| 卡片列表项 | `Card(onClick = ...)` 或 `Surface(onClick = ...)` |
| `<input>` | `OutlinedTextField` + `KeyboardOptions` + `isError` |
| `<textarea>` | `OutlinedTextField(minLines = 4)` |
| `<select>` | `ExposedDropdownMenuBox` |
| `<img>` | `AsyncImage(model = url, contentDescription = ..., placeholder = ..., error = ...)` |
| 头像 | `AsyncImage` + `Modifier.clip(CircleShape))` |
| 标签 | `AssistChip` / `SuggestionChip` |
| 分割线 | `HorizontalDivider()` |
| 徽标数字 | `BadgedBox` + `Badge` |
| Loading | `CircularProgressIndicator()` |
| Toast | `Toast.makeText(context, ..., Toast.LENGTH_SHORT).show()` |
| 确认弹窗 | `AlertDialog` |
| 权限请求 | 按需生成：`rememberLauncherForActivityResult(RequestPermission())` 或 Accompanist |

## 4. 页面范式（模板已内置）

### 列表页（参照 `feature/home`）

```text
Scaffold(topBar = AppTopBar(title, actions))
└── Box(fillMaxSize)
    ├── isLoading               → LoadingView()
    ├── error != null && empty  → ErrorView(message, onRetry)
    ├── empty                   → EmptyView("暂无数据")
    └── LazyColumn
        ├── items(list, key = id) → Card 条目
        └── footer: loadingMore / 触底加载 / 没有更多了
```

**触底加载**：footer 里 `if (hasMore) LaunchedEffect(list.size) { onLoadMore() }`，不要监听滚动偏移量。

### 详情页（参照 `feature/detail`）

```text
Scaffold(topBar = AppTopBar(title, onBack), bottomBar = { Button("联系TA") })
└── Column(verticalScroll)
    ├── 头图 / 标题 / 作者行
    ├── 标签行 (FlowRow)
    └── 正文段落
```

### 表单页（参照 `feature/login`）

```text
Column(padding = Dimens.lg)
├── OutlinedTextField（label + isError + supportingText）
├── 错误提示（红色 bodySmall）
└── Button(enabled = canSubmit, onClick = submit)
```

### 个人中心（参照 `feature/mine`）

```text
Column
├── 头部：头像 + 昵称 + 简介
├── 设置组：ListTile 风格行（图标 + 标题 + 右箭头）
└── 退出登录按钮
```

## 5. 交互映射

| 原型 | Compose |
| --- | --- |
| `onclick` 跳转 | `onClick: () -> Unit` 回传给 Screen 上层，由 `NavController` 处理 |
| 下拉刷新 | `PullToRefreshBox`（M3 实验 API）或顶部刷新按钮（模板默认） |
| 上拉加载 | footer `LaunchedEffect` |
| 表单校验 | ViewModel 校验，`UiState.canSubmit` 控制按钮 |
| 键盘遮挡 | `Modifier.imePadding()` + `Scaffold` |
| 返回键 | `BackHandler`（仅拦截二次确认场景） |

## 6. 图片与资源

- 原型里的远程图片可能失效：**必须** 提供 `placeholder` 与 `error`
- 本地图标优先用 `androidx.compose.material.icons.Icons.Default.*`，避免引入额外图标库
- 需要自定义矢量图时放 `res/drawable/ic_xxx.xml`，用 `painterResource`
- 大图不要塞 `res/`，走网络 + Coil 缓存

## 7. 屏幕适配

- 尺寸一律 `dp` / `sp`，不写像素
- 默认按 360dp 宽度设计，列表项用 `fillMaxWidth()` 自适应
- 平板 / 折叠屏：按需生成 `WindowSizeClass`，`Expanded` 时列表与详情双栏
- 状态栏沉浸：`enableEdgeToEdge()` + `Scaffold` 的 `innerPadding`

## 8. 无法映射时

不臆造。做法固定：

1. 用最接近的 Material3 组件还原
2. 在文件头注释写 `// TODO: 原型使用 XXX，当前用 YYY 近似实现`
3. 把差异列入输出的「⚠️ 待确认」
