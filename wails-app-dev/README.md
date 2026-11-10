# wails-app-dev

Wails 桌面应用开发注意事项。

不绑定具体项目，覆盖 Wails 开发中反复踩到的坑：无边框窗口、安装程序、构建打包、前端多语言、跨层故障排查。

## 内容

```
wails-app-dev/
├── SKILL.md                        ← 主入口：五条主线、核心原则、致命错误
├── references/
│   ├── frameless-window.md         ← 无边框窗口与自绘标题栏（最高频）
│   ├── installer.md                ← 安装程序：NSIS 引擎 + 自绘向导 + 引导
│   ├── build-packaging.md          ← 构建产物、跨平台、goreleaser、发布
│   ├── frontend-i18n.md            ← 前端架构、bindings、多语言、测试台
│   └── gotchas.md                  ← 陷阱清单：症状 → 根因 → 修法
└── assets/
    └── checklist.md                ← 按改动类型的必做项与漏做后果
```

## 三个主题重点

**无边框窗口**（`frameless-window.md`）
`--wails-draggable` 的正确用法、系统原生窗口按钮比例、关闭语义、最大化用工作区、多显示器与 DPI。

**安装程序**（`installer.md`）
NSIS 默认向导 vs 自绘 WPF 向导两条路线、`.onInit` + `Exec` 消除引擎窗口、`wscript` + VBS 消除控制台闪烁、提权策略、干净卸载、WebView2 引导。

**跨层排查**（`gotchas.md`）
按"你会怎么描述问题"索引，覆盖窗口拖不动、点了没反应、装完功能失效、中文乱码等。

## 使用

```
SKILL.md 了解整体 → 按任务选 references/ → 动手前过 assets/checklist.md
出问题查 references/gotchas.md
```
