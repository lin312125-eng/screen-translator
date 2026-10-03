# 随译 ScreenTranslator

Windows 桌面翻译小工具：**截图翻译** + **剪贴板翻译** + **文本翻译**，常驻系统托盘，全局快捷键一键呼出。

针对"某个应用只有英文界面、无法切换中文"的场景设计：框选屏幕上的英文，立即 OCR 识别并翻译，结果以悬浮窗展示，可复制。

## 功能

| 功能 | 快捷键（可在设置中修改） | 说明 |
|---|---|---|
| 屏幕实时翻译 | `Ctrl+Shift+R` | 框选监控区域（Esc 即全屏），后台自动识别屏幕上英文并实时浮出中文译文，按 `Esc` 停止 |
| 截图翻译 | `Ctrl+Shift+T` | 全屏遮罩 + 鼠标框选区域 → 本地 OCR 识别 → 翻译 → 悬浮窗双语对照 |
| 剪贴板翻译 | `Ctrl+Shift+C` | 复制任意文本后一键翻译（适合软件内无法直接选中的文字） |
| 文本翻译 | `Ctrl+Shift+W` | 打开文本窗口，输入即译（700ms 防抖），支持 15 种目标语言 |
| 设置 | `Ctrl+Shift+S` | 切换引擎、配置大模型 API Key、修改热键 |

**复制即译**：默认开启，在任何应用里复制文本（Ctrl+C）即自动弹出译文，零操作。可在设置中关闭。

**屏幕实时翻译说明**：类似 Edge 网页翻译的全局版——框选区域后，程序每 2.5 秒（可调）检查屏幕变化，识别到英文界面文字就在原文位置实时浮出中文译文。注意：
- 译文以悬浮层呈现，无法替换第三方应用的原文字（系统限制），原文滚动/切换时译文自动更新；
- 覆盖层透明区域鼠标可正常点击穿透，译文块位置会拦截点击（按 `Esc` 可随时停止）；
- 连续滚动页面时翻译请求较多，免费接口可能限流——建议此模式配合大模型 API Key 使用（设置中填入）。

程序常驻系统托盘，托盘菜单也可触发以上所有功能。

## 翻译引擎

- **自动（默认）**：依次尝试 DeepL → Bing → Google，哪个可用用哪个，无需任何 Key。
- **DeepL / Bing / Google 免费接口**：无需 Key，但免费网页接口受网络环境与限流影响（DeepL 免费层对短时间内的连续请求有限流，正常使用频率不受影响；Google 国内网络需代理）。
- **大模型 API（推荐，效果最好）**：OpenAI 兼容接口，翻译更自然、更稳定，支持豆包（火山方舟）、DeepSeek、OpenAI 等，在设置中填入即可，**无需重新打包**。

> 说明：如果你经常遇到免费接口不可用，建议尽快配置大模型 API——注册一个 Key 只需几分钟，个人使用成本极低（DeepSeek 充值 10 元可用很久；火山方舟新用户有免费 token 额度）。

### 大模型 API 配置示例

| 服务 | 接口地址 base_url | 模型 model | 获取 Key |
|---|---|---|---|
| 豆包（火山方舟） | `https://ark.cn-beijing.volces.com/api/v3` | 方舟控制台创建的接入点 ID，如 `doubao-seed-1-6-250615` | 注册火山引擎 → 开通方舟 → 创建 API Key 与推理接入点 |
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` | 官网注册 → 创建 API Key（充值 10 元可用很久） |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` | 需海外网络与账号 |

## 运行方式

### 方式一：直接运行打包好的 exe（推荐）

从 Release 下载 `ScreenTranslator.exe`，双击运行，托盘出现图标即可使用。

### 方式二：源码运行

```bash
pip install -r requirements.txt
python gen_icon.py     # 生成图标（可选）
python main.py
```

## 打包成 exe

```bash
python -m PyInstaller --noconfirm --onefile --windowed --icon assets/icon.ico \
    --name ScreenTranslator main.py
```

产物位于 `dist/ScreenTranslator.exe`（约 60-90MB，内含本地 OCR 模型）。

## 配置

首次运行自动生成 `config.json`（位于 exe 同目录），也可通过设置界面修改：

```json
{
  "engine": "auto",
  "llm": { "base_url": "", "api_key": "", "model": "" },
  "target_lang": "zh-CN",
  "monitor_interval": 2.5,
  "auto_translate_clipboard": true,
  "hotkeys": {
    "screenshot": "ctrl+shift+t",
    "clipboard": "ctrl+shift+c",
    "text": "ctrl+shift+w",
    "settings": "ctrl+shift+s",
    "monitor": "ctrl+shift+r"
  }
}
```

`engine` 可选值：`auto`（推荐，自动回退）、`deepl`、`bing`、`google`、`llm`。

## 说明

- OCR 使用 [RapidOCR](https://github.com/RapidAI/RapidOCR)（PP-OCR 模型），纯本地运行，图片不会上传，离线可用；首次识别需加载模型（约 1-3 秒）。
- 翻译接口会发送文本到对应服务：免费接口发送到 Bing/Google，大模型 API 发送到你配置的服务商。
- 截图选框目前仅覆盖主显示器；多显示器支持见 TODO。

## 技术栈

Python 3.14 · tkinter · mss · keyboard · pystray · RapidOCR(onnxruntime) · PyInstaller

## License

MIT
