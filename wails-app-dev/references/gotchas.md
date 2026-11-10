# 陷阱清单与症状索引

按"你会怎么描述问题"索引。每条给根因和修法。

## 窗口与界面

### 整个窗口拖不动

没有标记可拖拽区域。Wails 无边框窗口没有系统标题栏，必须显式：

```css
.titlebar { --wails-draggable: drag; }
```

### 点按钮没反应，鼠标一移窗口跟着跑

可拖拽区域覆盖了按钮，按钮没反向声明：

```css
.titlebar button { --wails-draggable: no-drag; }
```

### 输入框选不中文字 / 无法拖动选中

同上——拖拽区覆盖了输入区。给输入相关元素加 `no-drag`。

### 最大化后盖住任务栏

用了屏幕尺寸而非工作区。Windows 上任务栏占一部分屏幕，必须用 `RcWork`（工作区）。

如果用 Wails 的 `ToggleMaximise()` 还出现这问题，检查是否自己又设了一次窗口尺寸。

### 窗口四角是尖的，没有圆角

```go
DisableFramelessWindowDecorations: true   // ❌ 连圆角和阴影一起去掉
DisableFramelessWindowDecorations: false  // ✅ 保留
```

### 四角有脏边 / 圆角套圆角

窗口和内容容器的圆角半径不一致。统一，或让容器不设圆角。

### 拖到扩展屏后，窗口跳回主屏

居中逻辑用了主屏工作区。改用 `MonitorFromWindow` 取当前所在屏。

### 125% 缩放的屏上窗口偏小/偏大

没做 DPI 换算。用 `GetDpiForWindow` 拿实际 DPI，`scale = dpi / 96`。

### 点关闭程序没退出

托盘常驻模式下，关闭被 hook 拦住了。真退出要置标记：

```go
var appQuitting atomic.Bool
menu.Add("退出").OnClick(func(*application.Context) {
    appQuitting.Store(true)
    app.Quit()
})
window.RegisterHook(events.Common.WindowClosing, func(e *application.WindowEvent) {
    if appQuitting.Load() { return }
    e.Cancel(); window.Hide()
})
```

### 双击标题栏没最大化

系统标题栏自带，无边框后要自己绑 `dblclick`（记得排除按钮区域）。

### 右键菜单弹出来一堆浏览器选项

```go
DefaultContextMenuDisabled: true
```

输入框可能需要保留原生菜单（复制粘贴），前端单独放行：

```js
document.addEventListener('contextmenu', (e) => {
    const tag = e.target?.tagName?.toLowerCase();
    if (tag === 'input' || tag === 'textarea') return;
    e.preventDefault();
});
```

### F5 刷新无效

生产构建里 DevTools 关闭，WebView 默认快捷键不可靠。自己绑：

```js
document.addEventListener('keydown', (e) => {
    if (e.key === 'F5' || ((e.ctrlKey || e.metaKey) && e.key === 'r')) {
        e.preventDefault();
        location.reload();
    }
});
```

### 改了前端代码，界面没变

前端产物是**编译期嵌入**的，必须重新 `wails build`。开发时用 `wails dev`（有热重载）。

## 安装与打包

### 双击安装就弹 UAC，用户点"否"整个退出

`RequestExecutionLevel admin`。改成 `user`，只在需要提权的引擎步骤 `RunAs` 重启自己。

### 安装时闪一下黑色控制台窗口

`Exec 'powershell ...'` 分配了控制台。`-WindowStyle Hidden` / `start /min` 都压不住。

改用 `wscript.exe` + VBS 的 `WScript.Shell.Run(cmd, 0, False)`。

### 安装时先闪一个"正在安装"窗口

NSIS 用了 `Section` + `nsExec`。改 `.onInit` + `Exec` + `Quit`：

```nsis
Function .onInit
  Exec 'wscript.exe //nologo "$PLUGINSDIR\launch.vbs" ...'
  Quit
FunctionEnd
```

配 `ShowInstDetails nevershow`。

### 向导闪一下就消失

`.onInit` + `nsExec` 会把子进程放进 Job，`Quit` 时被杀。改用 `Exec`（不等待、不入 Job）。

### 卸载后文件还在 / 进程还在

卸载段漏步骤。完整顺序：

1. `taskkill` 应用进程
2. 删快捷方式
3. 从 PATH 移除（如加过）
4. 删用户数据目录（如需要）
5. `RMDir /r "$INSTDIR"`
6. `DeleteRegKey` 卸载信息

### `Bad text encoding: xxx.nsi:1`

`.nsi` 丢了 UTF-8 BOM。`makensis` 不认无 BOM 的 UTF-8 中文。

### 中文显示成乱码 / 问号

`.ps1` 丢 BOM。PowerShell 5.1 读无 BOM 的 UTF-8 会按 ANSI 解释。

### 升级后用户配置全丢

安装器直接覆盖了配置文件。要判断文件存在则跳过，或用 `config|noreplace`。

### `"ARCH" already defined!`

手工传了 `/DARCH=amd64`，但 Wails 的 `wails_tools.nsh` 已定义。删掉手工的。

### `Can't open output file`

上一个输出文件还在运行（`setup-test.exe` 没退）。先 `taskkill`。

## 构建与打包

### `NativeCommandError` 但退出码是 0

PowerShell `$ErrorActionPreference = "Stop"` 把外部程序 stderr 当异常。临时放宽 + 自己判 `$LASTEXITCODE`。

### `build constraints exclude all Go files`

平台专属包被 import 进通用文件。拆成 `*_windows.go` / `*_other.go`。

### 换平台编译失败

同上。**每个平台都要有同名方法**，否则 bindings 方法集合漂移。

### Linux 交叉编译报 `undefined: requires_CGO_ENABLED_1_or_build_tag_purego`

Wails Linux 构建需要 `purego` tag：

```bash
go build -tags purego ...
```

或直接用对应平台的 runner / Docker。

### 装完功能失效，dev 环境正常

归档 `files:` 清单漏了资源文件（配置模板、空目录、辅助二进制配置）。

**排查方法**：解压归档，逐个确认运行时需要的文件。

### 前端调用 Go 方法报 undefined

改了 Go 的 Service 没重新生成 bindings：

```bash
wails3 generate bindings -clean=true -time-type=Date
```

### 前端字段名对不上，显示空

Go struct 缺 json tag。Go 默认用字段名（`ID`），前端习惯 `id`。

### 版本号在多个地方不一致

没有单一来源。用 `VERSION` 文件或 `git describe`，构建时注入各处。

## 自绘向导（PowerShell + WPF）

### `TextBlock does not contain a method named 'Add_Click'`

TextBlock 没有 Click 事件。要么用 `Hyperlink`，要么改 `Add_MouseLeftButtonDown`。

### 绑了 `Add_MouseLeftButtonDown` 但点击不触发

**PowerShell 5.1 的 WPF 事件包装下，TextBlock 的鼠标事件不可靠**（实测不触发）。

**结论**：可点击元素一律用 `Button` + `Add_Click`。视觉上用透明模板做成"文字链"的样子。

```xml
<Button x:Name="lnkMore" BorderThickness="0" Background="Transparent" Cursor="Hand">
  <Button.Template>
    <ControlTemplate TargetType="Button">
      <Border Background="{TemplateBinding Background}">
        <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
      </Border>
    </ControlTemplate>
  </Button.Template>
  <Run Text="更多 ▾"/>
</Button>
```

### `Cannot set unknown member 'ControlTemplate.Triggers'`

`XamlReader::Parse` 对 `ControlTemplate.Triggers` 的支持不稳定，**同样的结构有时能解析有时不能**。

**结论**：不要在自绘向导里用 `ControlTemplate.Triggers`。需要"选中态"视觉时，把状态放到 PowerShell 侧用文字表达：

```powershell
$script:optMap = @{ desktop = $true }
$chkDesktop.Content = "$(if ($script:optMap.desktop) {'●'} else {'○'})  创建桌面快捷方式"
```

### `Xxx not recognized`（函数找不到）

PowerShell 顺序执行，函数必须定义在调用之前。检查文件里的定义顺序。

### XAML 解析报 `start tag does not match end tag`

标签配对坏了。常见于**连续多次文本替换**改 XAML。

**教训**：改 XAML 结构时整段重写，不要零散替换；改完立刻解析验证。

### `Could not register named object. Cannot register duplicate name 'xxx'`

`x:Name` 重名。同一作用域内名字必须唯一。

### 向导"点了没反应"

按顺序排查：

1. 加诊断落盘，看回调有没有被调用
2. 元素是否真的存在（`FindName`）
3. 事件通道是否可靠（TextBlock → Button）
4. `$script:` 变量是否初始化

### 折叠区展开后内容被裁

要显式改窗口高度并重新居中：

```powershell
$window.Height = if ($open) { 580 } else { 400 }
Center-OnCurrentMonitor
```

## 进程与系统

### 点了"停止服务"，提示成功但服务还在跑

PID 文件路径相对 CWD，CWD 不对就找不到，命令输出"not running"却**退出码 0**。

**修法**：操作后复核实际状态；复核不过就按可执行文件路径枚举进程强杀。

### 开机自启写了注册表但不生效

检查：

1. 路径带引号吗（`Program Files` 有空格）
2. 值写进的是 `HKCU` 还是 `HKLM`（用户级不需要管理员）
3. 命令里有没有多余参数导致启动失败

### 修改 PATH 后新开的终端读不到

没广播 `WM_SETTINGCHANGE`。要用 `SendMessageTimeout` 广播 `Environment`。

已打开的终端无论如何读不到（系统限制）。

### 写 HKLM 报权限不足

需要管理员。要么应用以管理员运行，要么把写操作放到提权的安装器步骤里。

## 通用排查方法

1. **先定位层次**：界面没渲染 / Go 没被调用 / 系统层面没生效？
2. **加可观测点**：无控制台时打印不可见，**写文件**
3. **缩小复现**：单独写最小脚本验证假设
4. **对比历史**："之前能用"→ `git log -p` 看那次改动
5. **结构文件改完立刻验证解析**：XAML/JSON/YAML 别攒着一起测
6. **不要连续多次文本替换改结构文件**——重写整段更安全
