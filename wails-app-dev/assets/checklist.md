# 开发检查清单

按改动类型选一列。左边必做，右边是漏了的后果。

## 新建 Wails 项目

```
□ 确认 v2 还是 v3（API 差异大，别混查文档）
□ 决定窗口形态：系统标题栏 / 无边框自绘 / 无边框+系统控件
□ 前端构建命令接进 wails.json
□ //go:embed all:frontend/dist 带 all: 前缀
□ info 段元数据完整（公司/产品/版本/版权）
□ .gitignore 覆盖 frontend/dist、build/bin、dist
□ 生成一次 bindings 确认前端能调通
```

## 做无边框窗口

```
□ Frameless: true
□ DisableFramelessWindowDecorations: false（保留 Win11 圆角阴影）
□ 标题栏 --wails-draggable: drag
□ 标题栏内所有可交互元素 --wails-draggable: no-drag
□ 拖拽区覆盖标题栏空白处
□ 双击标题栏切换最大化（排除按钮）
□ 三个窗口按钮按系统原生比例（46px 宽、撑满高度、直角）
□ 关闭语义明确（退出 / 托盘 / 询问）
□ 托盘常驻时有 appQuitting 标记
□ 最大化用工作区不是屏幕
□ 最大化时去掉自绘圆角
□ 多显示器居中相对当前屏
□ DPI 缩放换算
□ user-select: none
□ 右键菜单已禁用
```

**验证**：拖动窗口、点每个按钮、双击标题栏、最大化/还原、拖到第二块屏再操作。

## 做安装程序

```
□ RequestExecutionLevel 选对（admin 还是 user + RunAs）
□ 卸载段完整（停进程/快捷方式/PATH/数据/注册表/目录）
□ ShowInstDetails nevershow
□ WebView2 依赖检测（如需）
□ 安装目录固定，支持升级覆盖
□ 用户配置不被升级覆盖
□ 图标、版本、公司名正确
□ .nsi 与 .ps1 已补 UTF-8 BOM
```

自绘向导额外：

```
□ .ps1 补 UTF-8 BOM（每次编辑后）
□ 自检参数：校验元素清单 + 真实初始化
□ 预览参数：渲染 PNG 看排版（含展开态）
□ 无控制台闪烁（wscript + VBS 方案）
□ 多显示器居中相对当前屏
□ 可点击元素用 Button，不用 TextBlock 事件
□ 不用 ControlTemplate.Triggers
□ 函数定义在调用之前
□ UAC 取消时有兜底提示，不整个退出
```

**验证顺序**：自检 → 预览渲染 → `makensis` 编译 → 实际双击安装 → 卸载 → 检查残留。

## 改前端

```
□ npm run build 通过（含 i18n 自查）
□ 两份语言字典 key 一致
□ 静态文案挂 data-i18n*
□ 切换语言原地重渲染（不 reload）
□ 异步按钮有 busy 防重入 + finally 复位
□ 并行拉取各自容错
□ 错误信息已翻译成人话
□ devtest 通过（含 en / 异常场景变体）
□ 无控制台错误
```

## 改 Go Service

```
□ go build ./... 通过
□ go test ./... -count=1（别信 cached）
□ go vet ./...
□ 改了方法签名 → wails3 generate bindings
□ 所有 struct 有显式 json tag
□ 平台专属代码已文件级隔离
□ 每个平台都有同名方法
□ 交叉编译验证（如支持多平台）
```

## 改打包配置

```
□ 归档 files: 清单完整
□ 发行版包配置用 config|noreplace
□ 打包脚本判 $LASTEXITCODE
□ .nsi/.ps1 补 UTF-8 BOM
□ 守卫测试通过
□ 实跑一次完整打包（守卫只查文本）
□ 解压归档确认文件齐全
```

## 提交前

```
□ git status 只剩真正改的文件
□ 生成物未入库（dist / build/bin / frontend/dist / bindings）
□ 构建重写的生成文件已还原（如非本意）
□ 版本号未意外改动
```

## 快速判定表

| 症状 | 最可能原因 | 先查 |
| --- | --- | --- |
| 窗口拖不动 | 没 `--wails-draggable: drag` | 标题栏 CSS |
| 点按钮变拖窗口 | 没 `no-drag` | 按钮 CSS |
| 最大化盖任务栏 | 用了屏幕尺寸 | 最大化逻辑 |
| 扩展屏跳回主屏 | 用主屏工作区 | 居中逻辑 |
| 双击安装弹 UAC | `RequestExecutionLevel admin` | .nsi |
| 安装闪控制台 | `Exec powershell` | .nsi 启动命令 |
| 向导闪一下消失 | `.onInit` + `nsExec` | 改 `Exec` |
| 中文乱码 / 编码报错 | 丢 UTF-8 BOM | .nsi/.ps1 |
| 装完功能失效 | 归档漏文件 | goreleaser `files:` |
| 换平台编译失败 | 平台专属 import | 文件级隔离 |
| 前端方法 undefined | bindings 未重新生成 | generate bindings |
| 切语言整窗闪 | 用了 `location.reload()` | i18n 切换逻辑 |
| 服务没启动时整页空白 | `Promise.all` 连坐 | 改独立容错 |
| 点了没反应 | 初始化崩了 / 事件通道不对 | 诊断落盘 |
