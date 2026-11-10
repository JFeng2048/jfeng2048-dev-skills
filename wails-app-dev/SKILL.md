---
name: wails-app-dev
description: Wails（v2/v3）桌面应用开发注意事项——无边框窗口与自绘标题栏、安装程序（NSIS 引导 + 自绘向导）、构建打包发布、前端多语言、以及跨层陷阱排查。适用于用 Wails 做桌面应用、给现有应用加无边框/自定义标题栏、做安装程序与卸载、配置多平台打包、或排查"界面点了没反应""打包后功能失效""窗口拖不动""安装时闪控制台"这类 Wails 特有故障。当用户提到 Wails、无边框窗口、frameless、安装包、NSIS、桌面应用打包时使用。
---

# Wails 应用开发注意事项

Wails 用 Go 做后端、Web 技术做界面，但**它不是浏览器**。窗口、安装、打包、进程生命周期都由桌面环境决定，Web 侧的经验在这里经常失效。

这份 skill 收敛 Wails 开发中反复踩到的坑，按主题组织。不绑定任何具体项目，示例都是可迁移的最小形态。

## 五条主线

| 主题 | 你会遇到的问题 |
| --- | --- |
| **无边框窗口** | 拖不动、点不了、最大化后盖住任务栏、圆角丢失、DPI 缩放错位 |
| **安装程序** | 双击弹 UAC、闪控制台黑窗、卸载残留、升级覆盖用户配置 |
| **构建打包** | 前端产物没进包、跨平台编译失败、清单漏文件导致装完失效 |
| **前端集成** | bindings 未生成、多语言切换闪屏、dev 与生产路径不一致 |
| **跨层排查** | 点了没反应、dev 正常装完不行、错误信息不可读 |

按需查阅：

- `references/frameless-window.md` — 无边框窗口与自绘标题栏（**最高频**）
- `references/installer.md` — 安装程序：NSIS 引擎 + 自绘向导
- `references/build-packaging.md` — 构建产物、跨平台、发布
- `references/frontend-i18n.md` — 前端架构、多语言、自动化测试
- `references/gotchas.md` — 陷阱清单与症状索引

动手前过一遍 `assets/checklist.md`。

## 开始之前先确认三件事

### 1. 用 v2 还是 v3

两者 API 差异大，别混着查文档：

| | v2 | v3 |
| --- | --- | --- |
| 窗口 | `runtime.Window*` | `app.Window.New*` |
| 菜单/托盘 | 有限 | 一等公民（`app.NewMenu()`） |
| 多窗口 | 弱 | 原生支持 |
| 状态 | 稳定 | 仍在演进 |

新项目用 v3（托盘、多窗口、菜单能力完整）；已有 v2 项目不必急迁。**本 skill 示例以 v3 为主，v2 差异处标注。**

### 2. 前端构建工具

Wails 只要求前端产物落在一个目录（通常 `frontend/dist`），用什么框架都行。关键是构建命令要接进 `wails.json` / `Taskfile.yml`，让 `wails build` 自动跑。

### 3. 窗口形态

先决定用哪种，后面代码结构差别很大：

```
系统标题栏（默认）    → 零成本，但外观不可控
无边框 + 自绘标题栏   → 外观完全可控，需自己实现拖拽/最大化/关闭/吸附
无边框 + 系统控件叠加 → 折中：自定义布局，仍用系统按钮
```

无边框是最常见诉求，也是最容易踩坑的，详见 `references/frameless-window.md`。

## 核心原则

### 桌面端不是浏览器

Web 侧的习惯在 Wails 里逐条失效：

| Web 习惯 | Wails 里 |
| --- | --- |
| `window.close()` | 未必可用；关闭行为要显式定义（退出 / 隐藏到托盘） |
| 右键菜单随便用 | 默认应禁用（`DefaultContextMenuDisabled`） |
| 刷新页面重载代码 | 生产构建里 DevTools 关闭，`F5` 快捷键不可靠，要自己绑 |
| `localStorage` 可靠 | 可用，但用户数据目录要自己管清理 |
| 网络请求随便发 | 本地文件/系统 API 要走 Go 侧 |
| 弹 `alert` / `confirm` | 会阻塞 WebView，用自绘对话框 |

### 前端与 Go 的边界要早定

```
前端（渲染、交互、格式化）
  ↕ bindings（自动生成，不手改）
Go Service（业务、系统 API、文件、进程）
  ↕
平台实现（Windows/macOS/Linux 差异部分）
```

**判断标准**：需要碰系统（文件、注册表、进程、托盘、窗口）的，一律 Go 侧；纯展示逻辑留前端。

### 平台差异要文件级隔离

Windows 专属 API 不能出现在通用文件里，否则其他平台编译直接失败：

```
autostart_windows.go   //go:build windows
autostart_darwin.go    //go:build darwin
autostart_linux.go     //go:build linux
autostart_other.go     //go:build !windows && !darwin && !linux  (桩)
```

**每个平台都要有同名方法**，否则 bindings 的方法集合会随平台漂移，前端生成的类型不稳定。

## 常见致命错误

| 错误 | 后果 | 见 |
| --- | --- | --- |
| 无边框窗口没设 `--wails-draggable` | 整个窗口拖不动 | frameless-window.md |
| 自定义标题栏按钮没设 `no-drag` | 点按钮变成拖窗口 | frameless-window.md |
| 最大化没处理工作区 | 窗口盖住任务栏 | frameless-window.md |
| 安装器 `RequestExecutionLevel admin` | 双击就弹 UAC，用户取消即退出 | installer.md |
| `Exec powershell` 拉起向导 | 闪控制台黑窗 | installer.md |
| 打包清单漏资源文件 | dev 正常，装完功能失效 | build-packaging.md |
| 平台专属包顶层 import | 其他平台编译失败 | build-packaging.md |
| 改了 Service 没重新生成 bindings | 前端调用 undefined | frontend-i18n.md |
| 用 `location.reload()` 切语言 | 整窗闪白 | frontend-i18n.md |

## 排查方法论

Wails 的故障常常跨层（前端 / Go / 系统 / 打包），盲目改代码效率极低。固定顺序：

1. **先定位层次**：是界面没渲染、Go 没被调用、还是系统层面没生效？
2. **加可观测点**：无控制台时打印不可见，**写文件**。日志落到 `%TEMP%` 或用户数据目录
3. **缩小复现**：单独写最小脚本验证假设，比在千行文件里猜快十倍
4. **对比历史**："之前能用"就 `git log -p` 看那次改动
5. **结构文件改动后立刻验证解析**：XAML/JSON/YAML 用文本替换改完必须马上跑一次解析，别攒着

`references/gotchas.md` 有按症状索引的完整清单。
