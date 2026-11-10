# 安装程序与引导流程

Wails 的 `wails build` 只产出可执行文件，**安装程序要自己做**。这份文档讲 Windows 上的完整方案，以及"引导安装程序"（bootstrapper）的思路。

## 先选路线

| 方案 | 界面可控度 | 工作量 | 适用 |
| --- | --- | --- | --- |
| NSIS 默认向导（MUI2） | 低（只能改文案/图标） | 最小 | 内部工具、不挑外观 |
| NSIS + 自绘 WPF 向导 | 完全可控 | 大 | 面向终端用户的产品 |
| Inno Setup | 中（Pascal 脚本可定制页面） | 中 | 想要现代外观但不想完全自绘 |
| MSIX / MSI | 低 | 中 | 企业分发、需要系统级安装 |

**先问清楚**：真的需要自绘吗？NSIS 默认向导换掉图标和品牌位图后，很多产品已经够用。自绘的代价是 PowerShell/WPF 的一堆坑（见后文）。

下面两条路线都讲。

## 路线 A：NSIS 默认向导（快速）

### 最小可用脚本

```nsis
!define APP_NAME "MyApp"
!define APP_VERSION "1.0.0"
!define APP_EXE "MyApp.exe"

Name "${APP_NAME}"
OutFile "dist\${APP_NAME}-${APP_VERSION}-setup.exe"
InstallDir "$PROGRAMFILES64\${APP_NAME}"
RequestExecutionLevel admin

!include "MUI2.nsh"
!define MUI_ICON "appicon.ico"
!define MUI_UNICON "appicon.ico"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"

Section "Main" SecMain
  SetOutPath "$INSTDIR"
  File "build\bin\${APP_EXE}"
  CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
  CreateShortcut "$SMPROGRAMS\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
  WriteUninstaller "$INSTDIR\uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
    "DisplayName" "${APP_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
    "UninstallString" "$INSTDIR\uninstall.exe"
SectionEnd
```

### 品牌化：换位图就能显著提升观感

MUI2 支持替换向导两侧与顶部位图：

```nsis
!define MUI_WELCOMEFINISHPAGE_BITMAP "wizard-side.bmp"     ; 164×314
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "wizard-head.bmp"           ; 150×57
```

位图用脚本从应用图标生成（PS 或 Go 都行），保证品牌一致。

### 必须做的三件事

1. **`RequestExecutionLevel`**：装到 `Program Files` 需要 admin。但双击就弹 UAC 会流失用户——见"提权策略"
2. **卸载段**：不能只 `RMDir /r "$INSTDIR"`，要先停进程、删快捷方式、清注册表
3. **`ShowInstDetails nevershow`**：否则用户会看到一屏文件复制日志

## 路线 B：NSIS 引擎 + 自绘向导

界面完全自绘，NSIS 退化成"执行引擎"。

### 架构

```
setup.exe (NSIS)
  └─ .onInit: 隐藏自身，拉起向导进程，立刻 Quit
       ↓
  wizard.ps1 (PowerShell -STA + WPF)   ← 自绘界面
       ├─ 用户配置选项
       ├─ 点"安装"
       └─ RunAs 重新启动 setup.exe /S   ← 提权，纯执行无界面
```

好处：界面完全可控，安装逻辑仍由 NSIS 保证（文件、注册表、卸载信息都正确）。
代价：PowerShell 的 WPF 有很多坑，且需要目标机有 PowerShell（Windows 自带 5.1，够用）。

### `.onInit` 的三种写法（只有一种对）

| 写法 | 结果 |
| --- | --- |
| `Section` + `nsExec` | 先显示引擎自己的"正在安装"窗口，观感差 |
| `.onInit` + `nsExec` | `nsExec` 把子进程放进 Job，`Quit` 时子进程被杀，向导消失 |
| **`.onInit` + `Exec` + `Quit`** | ✅ 引擎立刻退出，向导独立存活 |

```nsis
Function .onInit
  SetOutPath "$PLUGINSDIR"
  File "/oname=wizard.ps1" "wizard.ps1"
  File "/oname=appicon.png" "appicon.png"
  Exec 'wscript.exe //nologo "$PLUGINSDIR\wizard-launch.vbs" ...'
  Quit
FunctionEnd
```

`Exec` 不等待、不加入 Job，子进程生命周期独立——这是关键。

### 消除控制台闪烁

`Exec 'powershell ...'` 会分配控制台窗口。**`-WindowStyle Hidden` 和 `start /min` 都压不住**，仍会闪一下。

```nsis
; ❌ 会闪
Exec 'cmd /c start "" /min powershell -WindowStyle Hidden -File "..."'
; ❌ 也会闪（ShellExecute powershell.exe 就分配控制台）
Exec 'powershell -File "..."'
```

可靠方案：用 `wscript.exe`（GUI 子系统程序，不分配控制台）跑一个 VBS，由它隐藏启动 PowerShell。

```vbscript
' wizard-launch.vbs
Set sh = CreateObject("WScript.Shell")
ps1 = WScript.Arguments(0)
args = ""
For i = 1 To WScript.Arguments.Count - 1
    args = args & " " & WScript.Arguments(i)
Next
sh.Run "powershell -NoProfile -STA -ExecutionPolicy Bypass -File """ & ps1 & """" & args, 0, False
```

`Run(cmd, 0, False)`：0 = 窗口隐藏，False = 不等待。

```nsis
Exec 'wscript.exe //nologo "$PLUGINSDIR\wizard-launch.vbs" "$PLUGINSDIR\wizard.ps1" -Self "$EXEPATH"'
```

### 提权策略

**问题**：装到 `Program Files`、写 `HKLM`、改系统 PATH 都需要管理员。但如果安装器一启动就要求 admin，用户双击看到 UAC，点"否"就整个退出——体验很差。

**方案**：向导本身以普通用户运行（`RequestExecutionLevel user`），只在真正需要提权的步骤用 `RunAs` 重新启动自己：

```nsis
RequestExecutionLevel user      ; 双击不弹 UAC
```

```powershell
# 向导里点"安装"时
Start-Process -FilePath $Self -ArgumentList '/S' -Verb RunAs -Wait
```

引擎收到 `/S` 静默执行，此时已在管理员上下文，可以写 `Program Files` 和 `HKLM`。

**注意**：用户可能在 UAC 弹窗点"否"，要捕获并提示"需要管理员权限才能继续"，允许重试，而不是整个向导崩掉。

### 自绘向导的 PowerShell 雷区

详见 `references/gotchas.md`，这里列最致命的四条：

1. **`.ps1` 必须 UTF-8 with BOM**，否则中文乱码
2. **TextBlock 的鼠标事件不触发**——可点击元素一律用 Button
3. **`ControlTemplate.Triggers` 在 `XamlReader::Parse` 下会间歇性失败**——选中态视觉放到 PowerShell 侧用文字表达
4. **函数必须定义在调用之前**——PowerShell 顺序执行

### 向导必须有自检

自绘界面最危险的是"脚本崩了但窗口还是静态空壳"。加 `-SelfTest` 参数，**真实初始化**并校验元素清单：

```powershell
if ($SelfTest) {
    $names = 'btnInstall','btnClose','txtTitle','panelOptions','chkDesktop'
    foreach ($n in $names) {
        if (-not $window.FindName($n)) { throw "缺少元素 $n" }
    }
    Initialize-WelcomeScreen        # 真跑一遍：崩在这里当场爆
    Write-Host "selftest ok"
    exit 0
}
```

每次改完向导先跑自检再打包，能省掉一整轮"装完才发现崩"。

### 无头预览：不跑安装也能看排版

加 `-PreviewPng` 参数，不 `ShowDialog`，直接把窗口渲染成 PNG：

```powershell
$window.Show()
$window.UpdateLayout()
$rtb = New-Object System.Windows.Media.Imaging.RenderTargetBitmap(
    [int]$window.ActualWidth, [int]$window.ActualHeight, 96, 96,
    [System.Windows.Media.PixelFormats]::Pbgra32)
$rtb.Render($window)
$encoder = New-Object System.Windows.Media.Imaging.PngBitmapEncoder
$encoder.Frames.Add([System.Windows.Media.Imaging.BitmapFrame]::Create($rtb))
$fs = [System.IO.File]::Create($PreviewPng); $encoder.Save($fs); $fs.Close()
$window.Close()
```

调间距、字号、折叠态时，看渲染图比跑十次安装快得多。再配 `-PreviewExpand` 预览展开态。

### 多显示器：窗口居中相对当前屏

改窗口高度后重新居中，**不能用主屏工作区**（扩展屏上会跳回主屏）：

```powershell
Add-Type -Namespace W -Name D -MemberDefinition @'
[DllImport("user32.dll")] public static extern IntPtr MonitorFromWindow(IntPtr h, uint f);
[DllImport("user32.dll", CharSet=CharSet.Auto)] public static extern bool GetMonitorInfo(IntPtr m, ref MONITORINFO i);
[DllImport("user32.dll")] public static extern uint GetDpiForWindow(IntPtr h);
[StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
[StructLayout(LayoutKind.Sequential)] public struct MONITORINFO { public int cbSize; public RECT rcMonitor; public RECT rcWork; public uint dwFlags; }
'@

function Center-OnCurrentMonitor {
    $helper = New-Object System.Windows.Interop.WindowInteropHelper($window)
    if ($helper.Handle -eq [IntPtr]::Zero) { return }
    $hMon = [W.D]::MonitorFromWindow($helper.Handle, 2)   # NEAREST
    $mi = New-Object W.D+MONITORINFO
    $mi.cbSize = [System.Runtime.InteropServices.Marshal]::SizeOf($mi)
    if (-not [W.D]::GetMonitorInfo($hMon, [ref]$mi)) { return }
    $dpi = [W.D]::GetDpiForWindow($helper.Handle); if ($dpi -eq 0) { $dpi = 96 }
    $scale = $dpi / 96.0
    $waW = $mi.rcWork.Right - $mi.rcWork.Left
    $waH = $mi.rcWork.Bottom - $mi.rcWork.Top
    $window.Left = $mi.rcWork.Left + (($waW - $window.Width * $scale) / 2) / $scale
    $window.Top  = $mi.rcWork.Top  + (($waH - $window.Height * $scale) / 2) / $scale
}
```

## 引导安装程序（Bootstrapper）

"引导程序"指**先检查环境、必要时先装依赖，再装主程序**的安装器。Wails 应用最常见的依赖是 **WebView2**。

### 为什么需要

- Windows 10 早期版本可能没有 WebView2 Runtime
- Windows 7/8 完全没有（Wails v3 已不支持）
- 企业环境可能禁用了自动更新

### 检测 WebView2

注册表（机器级 + 用户级都要查）：

```
HKLM\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}
HKCU\Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}
```

读 `pv` 值，存在且非空即已安装。

### 安装 WebView2

两种方式：

| 方式 | 大小 | 网络 |
| --- | --- | --- |
| Evergreen Bootstrapper（在线） | ~2 MB | 需要联网 |
| Evergreen Standalone（离线） | ~130 MB | 不需要 |

```nsis
; 在线引导
ExecWait '"$PLUGINSDIR\MicrosoftEdgeWebview2Setup.exe" /silent /install'
```

**产品决策**：内网/离线场景必须用 standalone，否则装到一半失败。

### Wails 自身的处理

v3 的 NSIS 模板（`wails_tools.nsh`）已包含 WebView2 检查与安装逻辑。如果用自己的安装器，要参考它的实现，不要漏掉。

### 引导流程设计

```
启动
 ├─ 检查 WebView2 → 缺失则提示并安装（可选：允许跳过，但应用会起不来）
 ├─ 检查磁盘空间
 ├─ 检查是否已安装旧版本 → 提示升级/卸载
 ├─ 展示许可协议（如果需要）
 ├─ 选择安装位置与选项
 ├─ 复制文件
 ├─ 创建快捷方式 / 注册卸载信息 / 写 PATH（可选）
 └─ 完成页：直接运行 / 打开文档
```

## 卸载要干净

```nsis
Section "Uninstall"
  ; 1. 停进程（文件被占用就删不掉）
  nsExec::Exec 'taskkill /F /IM ${APP_EXE}'

  ; 2. 删快捷方式
  Delete "$DESKTOP\${APP_NAME}.lnk"
  Delete "$SMPROGRAMS\${APP_NAME}.lnk"

  ; 3. 从 PATH 移除（需要 admin）
  ; 4. 删 WebView2 用户数据（如果有独立数据目录）
  RMDir /r "$LOCALAPPDATA\${APP_NAME}"

  ; 5. 删安装目录
  RMDir /r "$INSTDIR"

  ; 6. 删卸载注册表项
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
SectionEnd
```

**只删自己的东西**。`RMDir /r` 的目标路径要逐条确认，别用变量拼出意外路径。

**用户数据要不要删**？配置、缓存、日志通常在 `%APPDATA%` 或 `%LOCALAPPDATA%`。删除会让"卸载重装"丢失设置，保留会留垃圾。折中：卸载时询问，或提供"保留用户数据"选项。

## 升级而非重装

同一个 `AppId` 的安装器应能覆盖升级：

- `InstallDir` 固定
- 用户配置标记为"不覆盖"（NSIS 里判断文件是否存在，存在则跳过）
- 卸载信息里记录版本

**踩坑**：升级时如果直接 `File` 覆盖配置文件，用户改过的设置全丢。要显式判断。

## 检查清单

```
□ RequestExecutionLevel 选对（admin 还是 user + RunAs）
□ 卸载段完整（停进程/快捷方式/PATH/数据/注册表/目录）
□ ShowInstDetails nevershow
□ WebView2 依赖检测（如需）
□ 安装目录固定，支持升级覆盖
□ 用户配置不被升级覆盖
□ 图标、版本信息、公司名正确
□ 安装后在"应用和功能"里显示正确名称与版本
□ 自绘向导：UTF-8 BOM + 自检 + 预览验证
□ 自绘向导：无控制台闪烁（wscript 方案）
□ 自绘向导：多显示器居中相对当前屏
```
