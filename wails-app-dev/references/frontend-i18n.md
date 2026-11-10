# 前端集成与多语言

Wails 允许任意前端技术栈，但有几件事必须在架构阶段定好，否则后期改动成本很高。

## 技术选型

| 选项 | 适用 | 权衡 |
| --- | --- | --- |
| 原生 JS + Vite | 表单/表格为主的管理工具 | 零框架开销，但要自己管渲染 |
| React / Vue | 复杂交互、状态多 | 生态好，包体积大 |
| Svelte | 想要响应式但不想背框架 | 编译期优化，生态中等 |

Wails 的 WebView 是系统提供的（Windows 用 WebView2/Chromium，macOS 用 WKWebView，Linux 用 WebKitGTK）。**注意跨平台渲染差异**——某个 CSS 特性在 Chromium 能用，WKWebView 未必。

## bindings：Go → 前端的桥

### 生成

```bash
wails3 generate bindings -clean=true -time-type=Date
```

产出 `frontend/bindings/` 下的 JS/TS 客户端。**不要手改**，每次改 Go 的 Service 都重新生成。

### 调用

```js
import { DesktopService } from '../bindings/myapp';

const sites = await DesktopService.ListSites();
```

### 常见错误

| 错误 | 原因 |
| --- | --- |
| `undefined is not a function` | 改了 Go 没重新生成 bindings |
| 返回 `null` 而不是报错 | Go 方法返回 `(nil, nil)` |
| 字段名不对 | Go struct 缺 json tag，或 tag 与前端不一致 |
| `Date` 序列化异常 | 用了 `-time-type=Date` 但字段是 string |

**json tag 必须显式写**：

```go
type Site struct {
    ID      string `json:"id"`
    Name    string `json:"name"`
    Enabled bool   `json:"enabled"`
}
```

没有 tag 时 Go 用字段名（`ID` → `ID`），前端习惯 `id`，容易对不上。

### 方法集合要跨平台稳定

如果某个方法只在 Windows 存在，其他平台的 bindings 就少了它，前端代码在不同平台编译出的类型不一致。

```go
// ❌ 只有 Windows 有 GetAutoStart
// ✅ 三个平台都有，非 Windows 返回 (false, nil)
```

## Service 设计

```go
type DesktopService struct {
    baseDir string
}

func (s *DesktopService) ListItems() ([]model.Item, error) { ... }
func (s *DesktopService) DoAction(id string) (string, error) { ... }
```

约定：

- **返回 `(值, error)`**，error 给前端做提示
- **成功时返回一句可读的结果**（"已保存"），而不是空
- **不返回内部结构**，走 DTO
- **长任务要能取消或至少不阻塞 UI**：Go 侧方法同步执行，前端 `await` 期间界面是活的，但按钮要禁用防重复点击

### 防重复点击

```js
let busy = false;
async function doAction() {
    if (busy) return;
    busy = true;
    btn.disabled = true;
    try {
        const msg = await DesktopService.DoAction(id);
        toast(msg);
    } catch (e) {
        toast('操作失败：' + msgOf(e));
    } finally {
        busy = false;          // ← 一定复位
        btn.disabled = false;
    }
}
```

**`finally` 复位是关键**。抛异常后卡死 `busy` 会让按钮永远不可用。

## 事件：Go → 前端推送

除了请求-响应，Go 侧还能主动发事件：

```go
// Go
app.Event.Emit("status-changed", payload)
```

```js
// 前端
window.runtime.EventsOn('status-changed', (payload) => { ... });
```

适用场景：后台任务进度、系统事件（睡眠唤醒、网络变化）、托盘菜单触发。

**注意**：事件是单向的，前端不能返回值。需要确认的交互仍走 Service 方法。

## 多语言（i18n）

### 字典结构

扁平 key，按功能分组：

```js
// locales/zh-CN.js
export const zhCN = {
  'nav.home': '首页',
  'nav.settings': '设置',
  'dialog.save': '保存',
  'error.network': '网络不可用，请稍后重试',
};

// locales/en.js
export const en = {
  'nav.home': 'Home',
  'nav.settings': 'Settings',
  'dialog.save': 'Save',
  'error.network': 'Network unavailable, please retry',
};
```

**两份字典的 key 集合必须完全一致**。用脚本校验，不要靠人眼。

### 使用

```js
t('nav.home')                        // 直接取
t('error.network', { host: 'x' })    // {占位符} 插值
```

### 静态文案：声明式标记

```html
<h3 data-i18n="nav.settings">设置</h3>
<input data-i18n-placeholder="form.hostPh" placeholder="example.com"/>
<button data-i18n-title="tip.save" title="保存">💾</button>
```

标签里的中文/英文只是**回退文本**，启动时整体替换。好处是首屏不闪、无 JS 也能读。

### 切换语言：绝对不要 reload

```js
// ❌ 整窗闪白，丢失当前页面与滚动位置
location.reload();

// ✅ 原地重渲染
function setLang(code) {
    localStorage.setItem('app.lang', code);
    document.documentElement.lang = code;
    applyStatic();                    // 刷所有 data-i18n*
    listeners.forEach((fn) => fn());  // 通知动态内容重绘
}
```

动态内容（JS 渲染的列表、表格）需要注册回调：

```js
onLangChange(() => {
    renderCached();     // 先用缓存同步重绘（无闪烁）
    fetchAndRender();   // 再静默拉新数据补一轮
});
```

### 自查脚本

构建前跑，检查四件事：

| 检查 | 内容 |
| --- | --- |
| A | 两份字典 key 一致且值非空 |
| B | 代码里用到的 key 两份都有 |
| C | HTML 里没有"裸文案"：带文案的行必须挂 `data-i18n*` |
| D | JS 里没有漏翻的硬编码文案 |

**D 的例外**要显式列出（帮助长文、内部常量等），否则会误报。

**踩坑**：解析外部文本里的中文关键字（比如解析中文输出的日志）会被 D 规则判为漏翻。解法是用 Unicode 转义：

```js
const LABEL = {
  enabled: /\u72b6\u6001/,     // 而不是 /状态/
};
```

## 状态与数据流

### 分层的刷新节奏

不是所有数据都该同一频率刷新：

```js
setInterval(refreshStatus, 2000);    // 状态：快
setInterval(refreshDetails, 15000);  // 明细：慢
```

原则：**用户盯着看的快刷，列表类的慢刷**。所有定时器都要在页面隐藏时暂停：

```js
if (document.hidden) return;
```

### 独立容错

多个数据源并行拉取时，一项失败不应拖垮全部：

```js
async function one(label, fn, fallback) {
    try { return await fn(); }
    catch (e) { console.warn(label, e); return fallback; }
}

const [a, b, c] = await Promise.all([
    one('A', () => Service.GetA(), []),
    one('B', () => Service.GetB(), []),
    one('C', () => Service.GetC(), null),
]);
```

**判断标准**：这些数据是否互相独立？独立就必须各自容错。典型错误是把"可选数据"和"必要数据"混在一个 `Promise.all` 里。

### 错误要给人话

Go 侧的错误可能含技术细节，不能直接显示：

```go
// Go：集中翻译
func FriendlyError(err error) string {
    msg := err.Error()
    switch {
    case strings.Contains(msg, "connection refused"):
        return "服务未启动，请先启动后重试"
    case strings.Contains(msg, "permission"):
        return "权限不足，请以管理员身份运行"
    default:
        return clip(msg, 200)     // 兜底：截断，不甩整段
    }
}
```

前端只管展示，不解析错误码。

## 测试：在浏览器里跑前端

Wails 的前端本质是 Web 应用，可以**脱离 Go 后端**在浏览器里测——用 mock 替代 bindings。

### 结构

```
devtest/
├── run.mjs            ← Playwright 脚本
├── mock-service.js    ← Service 的假实现
└── vite.config.mjs    ← 把 bindings 指向 mock
```

```js
// vite.config.mjs
{
  name: 'mock-bindings',
  resolveId(id) {
    if (id.includes('bindings')) return path.resolve(here, 'mock-service.js');
  }
}
```

### 断言

```js
const results = [];
function check(name, ok, detail) {
    results.push({ name, ok, detail });
    console.log((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ' — ' + detail : ''));
}

check('首页渲染', await page.locator('#metric').count() > 0);
check('弹窗可打开', await page.locator('#dialog').isVisible());
```

同时收集控制台错误：

```js
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
page.on('pageerror', (e) => errors.push(e.message));
check('无控制台错误', errors.length === 0, errors.join('; '));
```

### 多场景变体

```bash
node run.mjs            # 默认
node run.mjs en         # 英文界面
node run.mjs offline    # 后端不可用场景
```

用 URL 参数或环境变量切换 mock 行为：

```js
const OFFLINE = /[?&]offline=1/.test(location.search);
export const DesktopService = {
  async GetStatus() {
    if (OFFLINE) throw new Error('connection refused');
    return { running: true };
  },
};
```

**这个能力很重要**：真实后端很难制造"服务未启动"这类状态，mock 可以，且能写进 CI。

### mock 要与契约同步

mock 的字段名必须与 Go struct 的 json tag 一致。改契约时同步改 mock，否则测试通过而真机显示异常。

## 前端资源

### 图标与图片

放在 `frontend/public/`，dev 与生产都走同一路径：

```html
<img src="/appicon.png" alt="app"/>
```

不要用相对路径 `./appicon.png`——打包后路由可能不是根路径。

### 字体

桌面应用**不要**从 CDN 加载字体（离线环境会失败）。要么用系统字体栈，要么把字体文件放进 `public/` 并 `@font-face` 引用。

```css
body {
    font-family: "Segoe UI Variable", "Segoe UI", "PingFang SC",
                 "Microsoft YaHei UI", "Noto Sans CJK SC", sans-serif;
}
```

跨平台字体栈要覆盖三大系统的默认 UI 字体。

## 检查清单

```
□ bindings 已生成，且改动 Go 后重新生成
□ 所有 Go struct 有显式 json tag
□ 方法集合跨平台一致
□ 两份语言字典 key 一致（有自查脚本）
□ 静态文案挂 data-i18n*
□ 切换语言原地重渲染，不 reload
□ 定时刷新分频率，页面隐藏时暂停
□ 并行拉取各自容错
□ 错误信息已翻译成人话
□ 异步按钮有 busy 防重入且 finally 复位
□ 前端资源用绝对路径 /xxx
□ 字体不依赖 CDN
□ devtest 可跑（多语言 + 异常场景）
```
