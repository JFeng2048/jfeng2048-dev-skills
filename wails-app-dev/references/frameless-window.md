# 无边框窗口与自绘标题栏

Wails 的 `Frameless: true` 去掉系统标题栏，代价是**拖拽、最大化、关闭、吸附、圆角、DPI 全部要自己管**。这份文档覆盖全部要点。

## 基础配置

```go
window := app.Window.NewWithOptions(application.WebviewWindowOptions{
    Title:      "My App",
    Width:      1280,
    Height:     800,
    Frameless:  true,
    BackgroundColour: application.NewRGB(255, 255, 255),

    // 关键：保留系统窗口装饰（Win11 圆角 + 阴影 + 阴影动画）
    // 设为 true 会连圆角和阴影一起去掉，得到一个尖角方块
    DisableFramelessWindowDecorations: false,

    // 桌面应用不需要浏览器的右键菜单
    DefaultContextMenuDisabled: true,
    // 生产环境关闭 DevTools
    DevToolsEnabled: false,
})
```

`DisableFramelessWindowDecorations` 是最容易搞错的字段，命名反直觉：

- `false`（默认）：保留 Win11 的圆角与阴影 ✅
- `true`：连装饰一起去掉，尖角、无阴影

## 拖拽：`--wails-draggable`

无边框窗口没有系统标题栏可拖，必须显式标记可拖拽区域：

```css
.titlebar {
    --wails-draggable: drag;
    height: 52px;
    display: flex;
    align-items: center;
    -webkit-user-select: none;   /* 拖拽时别选中文字 */
    user-select: none;
}

/* 标题栏里的按钮必须反向声明，否则点下去变成拖窗口 */
.titlebar button {
    --wails-draggable: no-drag;
}
```

**两条铁律**：

1. 可拖区域必须显式 `drag`
2. 可拖区域内的**任何可交互元素**必须显式 `no-drag`——按钮、输入框、下拉、链接

漏了第 2 条的表现：点按钮没反应，鼠标一移窗口跟着跑。

**不要给整个 `body` 加 `drag`**。那样输入框无法选中文本、按钮全失效。只给标题栏那条。

### 拖拽区要覆盖到"看起来能拖"的地方

常见疏漏：标题栏两侧的空白。用户习惯在空白处拖窗口，如果那里不是 `drag`，体验很差。

```css
.titlebar { --wails-draggable: drag; }
.titlebar .spacer { flex: 1; }        /* 继承 drag，空白可拖 ✅ */
.titlebar .actions { --wails-draggable: no-drag; }   /* 按钮区排除 */
```

### 双击标题栏最大化

系统标题栏自带双击最大化。无边框后要自己实现：

```js
titlebar.addEventListener('dblclick', (e) => {
    if (e.target.closest('button')) return;   // 按钮上双击不触发
    DesktopService.ToggleMaximiseWindow();
});
```

注意排除按钮区域，否则快速点两下按钮会把窗口最大化。

## 窗口按钮

三个按钮：最小化、最大化/还原、关闭。

```html
<div class="win-controls">
  <button class="win-btn" data-window="minimise" aria-label="最小化">
    <svg viewBox="0 0 10 10"><path d="M1 5h8"/></svg>
  </button>
  <button class="win-btn" data-window="maximise" aria-label="最大化或还原">
    <svg viewBox="0 0 10 10"><rect x="1.7" y="1.7" width="6.6" height="6.6"/></svg>
  </button>
  <button class="win-btn close" data-window="hide" aria-label="关闭">
    <svg viewBox="0 0 10 10"><path d="M2.2 2.2l5.6 5.6M7.8 2.2l-5.6 5.6"/></svg>
  </button>
</div>
```

```js
$$('[data-window]').forEach((b) => b.addEventListener('click', async () => {
    const action = b.getAttribute('data-window');
    if (action === 'minimise') await DesktopService.MinimiseWindow();
    else if (action === 'maximise') await DesktopService.ToggleMaximiseWindow();
    else if (action === 'close') handleClose();     // 见下文"关闭语义"
}));
```

### 按系统原生比例排布

Windows 的窗口按钮是 **46px 宽、撑满标题栏高度、直角、hover 才显背景**。自己画的按钮如果做成圆角、有间距、常显背景，会明显"不像 Windows"。

```css
.win-controls {
    display: flex;
    align-items: stretch;
    align-self: stretch;      /* 撑满标题栏高度 */
    margin-right: -12px;      /* 贴到窗口右边缘 */
}
.win-btn {
    width: 46px;
    border: 0;
    border-radius: 0;
    background: transparent;
    display: grid;
    place-items: center;
}
.win-btn:hover { background: rgba(0,0,0,.06); }
.win-btn.close:hover { background: #c0392b; color: #fff; }   /* 关闭按钮红底 */
```

图标用 SVG 线条，统一线宽（`stroke-width: 1.1`），尺寸 10×10。

## 关闭语义：先想清楚"关闭"是什么

无边框窗口没有系统行为兜底，必须显式定义。三种常见语义：

| 语义 | 适用 | 实现 |
| --- | --- | --- |
| 退出程序 | 单窗口工具类应用 | 关闭即 `app.Quit()` |
| 隐藏到托盘 | 需要常驻后台 | 拦截关闭，`window.Hide()` |
| 弹窗询问 | 有未保存状态 | 拦截关闭，弹自绘对话框 |

### 隐藏到托盘 + 真退出

托盘常驻应用的核心模式：

```go
var appQuitting atomic.Bool

// 托盘的"退出"菜单
menu.Add("退出").OnClick(func(*application.Context) {
    appQuitting.Store(true)     // 置位
    app.Quit()
})

// 拦截窗口关闭
window.RegisterHook(events.Common.WindowClosing, func(e *application.WindowEvent) {
    if appQuitting.Load() {
        return                  // 真退出：放行
    }
    e.Cancel()
    window.Hide()               // 否则：隐藏
})
```

**`appQuitting` 是必须的**。没有它，`app.Quit()` 也会被 hook 拦住，程序退不掉。

### 前端弹窗询问

```js
function handleClose() {
    openCloseDialog();      // 自绘对话框：隐藏到托盘 / 直接退出
}
```

不要用浏览器原生 `confirm()`——它会阻塞 WebView 渲染线程，无边框窗口可能卡住不重绘。

## 最大化：工作区不是屏幕

最容易踩的坑：最大化后**窗口盖住任务栏**。

原因：把窗口尺寸设成了屏幕尺寸，但任务栏占了一部分。正确做法是用**工作区**（work area）而非屏幕区域。

### 用 Wails 的 ToggleMaximise

v3 的 `window.ToggleMaximise()` 通常已正确处理。如果自己实现最大化（比如要自定义动画或跨平台一致），必须：

```go
// Windows：取工作区而非屏幕
type RECT struct{ Left, Top, Right, Bottom int32 }
type MONITORINFO struct {
    CbSize    uint32
    RcMonitor RECT
    RcWork    RECT      // ← 工作区（已排除任务栏）
    DwFlags   uint32
}
// MonitorFromWindow + GetMonitorInfo → 用 RcWork
```

**多显示器**还要处理"当前在哪块屏"。见下节。

### 前端状态同步

最大化/还原按钮的图标要跟着变。Wails 可以在窗口尺寸变化时发事件给前端，或前端在点击后自己查状态。

简单做法：点击后立刻按"预期状态"换图标，再异步校正：

```js
async function toggleMax() {
    await DesktopService.ToggleMaximiseWindow();
    const isMax = await DesktopService.IsMaximised();
    document.body.classList.toggle('is-maximised', isMax);
}
```

```css
/* 最大化时去掉圆角，避免四角露出桌面 */
body.is-maximised .window { border-radius: 0; }
```

## 圆角与阴影

Win11 的圆角是系统给的（`DisableFramelessWindowDecorations: false`）。但如果你自己画了内容容器，要注意：

```css
.window {
    border-radius: 8px;       /* 与系统圆角匹配，避免双圆角错位 */
    overflow: hidden;
}
body.is-maximised .window { border-radius: 0; }   /* 最大化时直角 */
```

**不要同时**给窗口和内容容器设不同半径，会出现"圆角套圆角"的脏边。

## 多显示器与 DPI

### 窗口居中要相对"当前所在屏"

`WindowStartupLocation: CenterScreen` 只在首次显示时生效。后续手动改尺寸再居中时，**不能用主屏工作区**：

```go
// ❌ 主屏工作区：窗口在扩展屏上会跳回主屏
SystemParameters.WorkArea

// ✅ 窗口当前所在的显示器
hMon := MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
GetMonitorInfo(hMon, &mi)      // 用 mi.RcWork
```

完整实现（含 DPI 换算）见 `references/installer.md` 的向导居中一节——同样的逻辑在应用窗口里也适用。

### DPI 缩放

不同显示器可能缩放比不同（100% / 125% / 150%）。跨屏拖动时窗口内容要跟着缩放。

Wails 通常自动处理 WebView 的缩放，但**自绘的窗口尺寸计算**要手动换算：

```go
dpi := GetDpiForWindow(hwnd)     // Win10 1607+
if dpi == 0 { dpi = 96 }
scale := float64(dpi) / 96.0
// WPF 单位 = 物理像素 / scale
```

若发现窗口在 125% 缩放的屏上偏小/偏大，就是漏了这一步。

## 无边框 + 系统控件（折中方案）

不想自己实现拖拽/最大化，但又想自定义外观，可以只隐藏标题栏文字、保留系统控件：

- Windows：`WS_CAPTION` 保留，去掉 `WS_SYSMENU` 的文字部分
- 或使用 `TitleBarHidden` 类选项（v3 版本相关）

这条路的好处是系统行为全对（吸附、双击、Aero Snap），坏处是外观只能小改。**先确认需求是否真的需要完全自绘**，很多"要自定义标题栏"其实只需要换颜色/加 logo。

## 吸附与手势

Windows 的 Aero Snap（拖到屏幕边缘分屏）依赖系统标题栏。无边框后：

- v3 的部分版本支持
- 否则需要自己实现：监听鼠标位置，接近边缘时调 `SetWindowPos`

**评估**：Aero Snap 是重度用户的高频操作，如果丢失会被抱怨。若无法支持，至少在文档里说明。

## 自绘标题栏检查清单

```
□ Frameless: true
□ DisableFramelessWindowDecorations: false   （保留圆角阴影）
□ 标题栏 CSS: --wails-draggable: drag
□ 标题栏内所有可交互元素: --wails-draggable: no-drag
□ 拖拽区覆盖标题栏空白处
□ 双击标题栏切换最大化（排除按钮）
□ 三个窗口按钮：最小化 / 最大化还原 / 关闭
□ 按钮尺寸按系统原生比例（46px 宽、撑满高度、直角）
□ 关闭语义明确（退出 / 托盘 / 询问）
□ 托盘常驻时有 appQuitting 标记
□ 最大化用工作区而非屏幕尺寸
□ 最大化时去掉自绘圆角
□ 多显示器居中相对当前屏
□ DPI 缩放换算
□ user-select: none 防拖拽选中文字
□ 右键菜单已禁用
```

## 常见故障对照

| 症状 | 原因 | 修法 |
| --- | --- | --- |
| 整个窗口拖不动 | 没有 `--wails-draggable: drag` | 给标题栏加 |
| 点按钮变成拖窗口 | 按钮没 `no-drag` | 给可交互元素加 `no-drag` |
| 输入框选不中文字 | 拖拽区覆盖了输入框 | 输入区加 `no-drag` |
| 最大化盖住任务栏 | 用了屏幕尺寸 | 改用工作区 |
| 窗口四角是尖的 | `DisableFramelessWindowDecorations: true` | 改 false |
| 四角有脏边 | 窗口与容器圆角半径不一致 | 统一半径 |
| 拖到扩展屏后居中跳回主屏 | 用了主屏工作区 | `MonitorFromWindow` |
| 125% 缩放屏上窗口偏小 | 没做 DPI 换算 | `GetDpiForWindow` |
| 点关闭程序没退出 | 托盘 hook 拦住了 | 加 `appQuitting` 标记 |
| 双击标题栏没反应 | 没绑 `dblclick` | 自己绑，排除按钮 |
