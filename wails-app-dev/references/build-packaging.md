# 构建、打包与发布

Wails 的构建链有三段：**前端产物 → Go 二进制 → 安装包**。每段都可能出问题，且故障表现往往延迟到最后一步才暴露。

## 构建链

```
wails build
  ├─ 1. 跑前端构建命令（wails.json / Taskfile.yml 配置）
  │      npm run build → frontend/dist
  ├─ 2. Go 编译
  │      //go:embed all:frontend/dist → 单文件 exe
  └─ 3. 产出 build/bin/<app>.exe
         ↓
  安装程序（NSIS / Inno）
         ↓
  发布（GitHub Release / 内部制品库）
```

**关键理解**：前端产物在**编译期嵌进 exe**，不是运行时读目录。所以：

- `frontend/dist` 必须在 `go build` 之前就绪
- 改了前端没重新 `wails build`，exe 里还是旧界面
- 生产构建里 DevTools 默认关闭，改了代码看不到新界面时会很困惑

## 前端产物嵌入

```go
//go:embed all:frontend/dist
var assets embed.FS

func main() {
    app := application.New(application.Options{
        Assets: application.AssetOptions{
            Handler: application.AssetFileServerFS(assets),
        },
    })
}
```

`all:` 前缀很重要——没有它，`embed` 会跳过以 `.` 或 `_` 开头的文件，某些构建工具产出的资源会被漏掉。

## wails.json 配置

```json
{
  "name": "myapp",
  "outputfilename": "MyApp",
  "frontend:install": "npm install",
  "frontend:build": "npm run build",
  "frontend:dev:watcher": "npm run dev",
  "frontend:dev:serverUrl": "auto",
  "author": { "name": "...", "email": "..." },
  "info": {
    "companyName": "...",
    "productName": "MyApp",
    "productVersion": "1.0.0",
    "copyright": "...",
    "comments": "..."
  }
}
```

`info` 段的元数据会写进 exe 的版本资源——文件属性里显示的公司名、产品名、版本都来自这里。**版本号要单一来源**，不要在多处硬编码。

## 版本号管理

版本号通常出现在：

```
wails.json          → info.productVersion
go 代码             → 常量或 ldflags 注入
安装器脚本          → 文件名、注册表
前端 package.json
```

**做法**：单一来源（`VERSION` 文件 / `git describe`），构建脚本读它并注入各处。

```go
// 用 ldflags 注入，避免改代码
var Version = "dev"

// go build -ldflags "-X main.Version=$(git describe --tags)"
```

## 跨平台构建

### 目标平台组合

| 平台 | 架构 | 注意 |
| --- | --- | --- |
| Windows | amd64 / arm64 | 需要 WebView2 |
| macOS | amd64 / arm64 | 需要签名与公证 |
| Linux | amd64 / arm64 | 需要 WebKitGTK 运行时依赖 |

### 交叉编译的硬限制

Wails 的 Linux 构建依赖 CGO（WebKitGTK），**不能**在 Windows 上直接交叉编译。可行方案：

1. CI 里用对应平台的 runner（推荐）
2. Docker 容器（`ghcr.io/wailsapp/wails:latest`）
3. 本地只构建当前平台

**能交叉编译的部分**：纯 Go 的逻辑、不含 GUI 的辅助二进制（比如采集器、CLI 工具）。

### 平台专属代码必须隔离

```go
// autostart_windows.go
//go:build windows

import "golang.org/x/sys/windows/registry"

// autostart_linux.go
//go:build linux

// autostart_darwin.go
//go:build darwin

// autostart_other.go
//go:build !windows && !linux && !darwin
func GetAutoStart() (bool, error) { return false, nil }
```

**致命错误**：把平台专属包 import 进通用文件。编译当前平台没事，换平台立刻炸：

```
imports golang.org/x/sys/windows/registry:
  build constraints exclude all Go files
```

**每个平台都要有同名方法**，否则 bindings 的方法集合随平台漂移，前端生成的类型不稳定。

## goreleaser（多平台发布）

适合"一个仓库出多平台产物 + 归档 + 包管理器包"。

### builds：每个二进制 × 平台

```yaml
builds:
  - id: windows-amd64
    main: .
    binary: myapp
    env: [CGO_ENABLED=0]
    goos: [windows]
    goarch: [amd64]
    ldflags: ["-s -w", "-X main.Version={{.Version}}"]

  - id: helper-windows-amd64      # 辅助二进制
    main: ./helper
    binary: myapp-helper
    goos: [windows]
    goarch: [amd64]
```

### archives：清单必须完整

**最高频的打包事故**：归档 `files:` 漏了资源文件，导致装完功能失效，而 dev 环境完全正常。

```yaml
archives:
  - id: windows-amd64
    ids: [windows-amd64, helper-windows-amd64]
    formats: [zip]
    files:
      - config/*.json              # 配置模板
      - config/cert/.keep          # 空目录用 .keep 占位
      - logs/.keep
      - docs/usage.html
      - README.md
      - LICENSE
```

**自检方法**：解压归档，逐个确认运行时需要的文件都在。特别是：

- 配置模板
- 空目录（用 `.keep`）
- 前端资源（如果没嵌进 exe）
- 辅助二进制的配置文件

### 发行版包（nfpms）

```yaml
nfpms:
  - id: linux-packages
    ids: [linux-pkg]
    package_name: myapp
    formats: [deb, rpm, apk]
    contents:
      - src: dist/linux-pkg_linux_amd64*/myapp
        dst: /usr/bin/
      - src: config/myapp.json
        dst: /etc/myapp/myapp.json
        type: config|noreplace      # ← 升级不覆盖用户配置
```

`config|noreplace` 是关键：否则升级时用户改过的配置被冲掉。

### 归档布局 vs 包布局

两种布局的路径基准不同，配置文件要**分开准备**：

| 布局 | 配置路径 |
| --- | --- |
| 归档（zip/tar.gz） | 相对工作目录，如 `"dir": "logs"` |
| 发行版包（deb/rpm） | FHS 绝对路径，如 `"dir": "/var/log/myapp"` |

所以会有 `config/myapp.json`（归档用）和 `build/packaging/myapp.json`（包用）两份。

## 打包脚本（一键出包）

多平台 + 多步骤时，写一个脚本串起来：

```powershell
# build/package.ps1
$ErrorActionPreference = "Stop"

# 1. 前端
Push-Location frontend; npm run build; Pop-Location

# 2. bindings（如果 Go 的 Service 变了）
& wails3 generate bindings -clean=true -time-type=Date

# 3. Wails 编译
& wails3 build -platform windows/amd64 -tags production

# 4. 主程序 / 辅助二进制
& goreleaser release -f build/goreleaser.yaml --clean --snapshot --skip=publish

# 5. 安装器
& makensis build\installer\setup.nsi
```

### 坑：`$ErrorActionPreference = "Stop"` 与外部命令 stderr

PowerShell 在 `Stop` 模式下，外部程序往 stderr 写任何东西都会被当成 `NativeCommandError` 抛出——**即使退出码是 0**。Wails 和 goreleaser 都会往 stderr 打进度日志。

```
wails3.exe : task: [windows:common:go:mod:tidy] go mod tidy
+ FullyQualifiedErrorId : NativeCommandError
```

修法：包住外部命令时临时放宽，**自己判 `$LASTEXITCODE`**：

```powershell
$prev = $ErrorActionPreference
$ErrorActionPreference = "Continue"
try {
    & wails3 build 2>&1 | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "wails build failed (exit $LASTEXITCODE)" }
} finally {
    $ErrorActionPreference = $prev
}
```

## 资源文件编码

**Windows 特有**：`.nsi` / `.ps1` 必须 UTF-8 with BOM，否则 `makensis` 报 `Bad text encoding` 或中文乱码。

很多编辑器/工具（含 `write` 类文件操作）会去掉 BOM。打包脚本里统一兜底：

```powershell
function Ensure-Utf8Bom([string]$Path) {
    $b = [System.IO.File]::ReadAllBytes($Path)
    if ($b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF) { return }
    $out = New-Object byte[] ($b.Length + 3)
    $out[0]=0xEF; $out[1]=0xBB; $out[2]=0xBF
    [Array]::Copy($b, 0, $out, 3, $b.Length)
    [System.IO.File]::WriteAllBytes($Path, $out)
}
```

## 守卫测试

打包配置最容易"改了没生效"。用自动化测试锁住关键清单：

```go
func TestArchiveShipsConfig(t *testing.T) {
    yaml := readFile(t, "build/goreleaser.yaml")
    for _, want := range []string{
        "config/myapp.json",
        "config/cert/.keep",
        "docs/usage.html",
    } {
        if !strings.Contains(yaml, want) {
            t.Errorf("归档清单缺少 %q", want)
        }
    }
}

func TestInstallerUninstallIsClean(t *testing.T) {
    nsi := readFile(t, "build/installer/setup.nsi")
    for _, want := range []string{
        "taskkill /F /IM MyApp.exe",
        `RMDir /r "$INSTDIR"`,
        "DeleteRegKey HKLM",
    } {
        if !strings.Contains(nsi, want) {
            t.Errorf("卸载段缺少 %q", want)
        }
    }
}
```

**这类测试的价值**：改打包配置时它会失败，提醒你"契约变了，确认一下"。是特性不是麻烦。

## 发布

### GitHub Release

```yaml
release:
  draft: false
  prerelease: auto
  footer: |
    **完整更新日志**: https://github.com/.../compare/{{ .PreviousTag }}...{{ .Tag }}
```

### 代码签名（Windows）

未签名的 exe 会触发 SmartScreen 警告："Windows 已保护你的电脑"。面向终端用户的产品应签名：

```powershell
signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 `
  /f cert.pfx /p $env:CERT_PASSWORD dist\MyApp-setup.exe
```

证书来源：OV/EV 代码签名证书（付费）。EV 证书能立即获得 SmartScreen 信誉。

### macOS 公证

```bash
xcrun notarytool submit MyApp.zip --apple-id ... --team-id ... --password ... --wait
xcrun stapler staple MyApp.app
```

不公证的 app 在用户机器上会被 Gatekeeper 拦截。

## 构建产物不该入库

```
frontend/dist/
frontend/bindings/        ← 部分团队会提交，视协作方式定
build/bin/
dist/
```

`.gitignore` 要覆盖。改完看 `git status`，确认没有生成物混进提交。

**bindings 要不要提交**：如果 CI 会重新生成，不提交；如果前端开发者不跑 Go 工具链，提交更方便。团队约定即可，但要一致。

## 检查清单

```
□ frontend:build 命令已接进 wails.json
□ //go:embed all:frontend/dist 带 all: 前缀
□ info 段元数据完整（公司/产品/版本/版权）
□ 版本号单一来源
□ 平台专属代码已文件级隔离
□ 每个平台都有同名方法（bindings 稳定）
□ 归档 files: 清单完整（配置/资源/空目录）
□ 发行版包配置用 config|noreplace
□ 打包脚本判 $LASTEXITCODE
□ .nsi/.ps1 补 UTF-8 BOM
□ 守卫测试覆盖清单条目
□ 生成物已 gitignore
□ 代码签名 / 公证（面向终端用户时）
```

## 故障对照

| 症状 | 原因 | 修法 |
| --- | --- | --- |
| 改了前端但界面没变 | 没重新 `wails build` | 前端产物是编译期嵌入的 |
| 装完功能失效，dev 正常 | 归档漏资源文件 | 补 `files:` 清单 |
| 换平台编译失败 | 平台专属包顶层 import | 文件级隔离 |
| `build constraints exclude all Go files` | 同上 | 同上 |
| `Bad text encoding` | `.nsi` 丢 BOM | 补 UTF-8 BOM |
| `NativeCommandError` 但退出码 0 | EAP Stop + stderr | 临时 Continue + 判退出码 |
| 升级后用户配置丢失 | 配置文件被覆盖 | `config\|noreplace` 或显式判断 |
| SmartScreen 警告 | 未签名 | 代码签名 |
| 前端调用方法 undefined | bindings 未重新生成 | `wails3 generate bindings` |
