# 产品图文案生成器

基于火山引擎 API 的朋友圈文案生成工具，使用 **Tauri + Vue 3 + Python Sidecar** 架构。

## ✨ 特性

- 🖥️ **原生桌面应用** - 打包成 .exe，双击即可运行
- 🔐 **前端配置** - 无需修改配置文件，在界面填写 API Key
- � **无 HTTP 通信** - Tauri 直接调用 Python，更高效
- �🖼️ **多图支持** - 支持上传多张产品图片
- 📝 **多种风格** - 支持多种文案风格模板
- 💰 **余额查询** - 支持查询火山引擎账户余额
- 📊 **Token 统计** - 显示每次调用的 Token 使用量

## 🏗️ 架构

```
┌─────────────────────────────────────────┐
│           Vue 3 前端                     │
│              ↓ invoke()                  │
│         Tauri Command (Rust)             │
│              ↓ stdin/stdout              │
│         Python Sidecar                   │
└─────────────────────────────────────────┘
```

**无 HTTP！前端直接调用 Python**

## 📁 项目结构

```
Moments_Content_Generator/
├── backend/
│   ├── sidecar.py              # Python sidecar（通过 stdin/stdout 通信）
│   └── requirements.txt        # Python 依赖
├── frontend/                   # Tauri + Vue 前端
│   ├── src/                    # Vue 源码
│   │   └── components/
│   │       ├── ConfigPanel.vue     # 配置页面
│   │       ├── GeneratorPanel.vue  # 文案生成页面
│   │       └── BillingPanel.vue    # 账户余额页面
│   └── src-tauri/              # Tauri 配置
│       ├── tauri.conf.json
│       └── src/main.rs         # Rust commands
├── prompts/                    # 文案模板
├── dev.bat                     # 开发启动脚本
└── build.bat                   # 打包脚本
```

## 🚀 快速开始

### 前置要求

- **Node.js** 18+
- **Rust** (安装 Tauri CLI 会自动安装)
- **Python** 3.10+

### 开发模式

```bash
# Windows
dev.bat
```

这会启动 Tauri 开发模式，自动：
1. 启动 Python sidecar
2. 启动 Vue 开发服务器
3. 打开桌面窗口

### 打包为 .exe

```bash
build.bat
```

打包完成后，在 `frontend/src-tauri/target/release/bundle/` 目录下找到安装包。

## ⚙️ 配置说明

首次使用时，在应用的「配置」页面填写：

| 配置项 | 说明 | 获取地址 |
|--------|------|----------|
| API Key | 火山引擎 ARK API Key | [获取](https://console.volcengine.com/ark/region:ark+cn-beijing/apikey) |
| 模型 ID | 模型标识符 | 如 `doubao-seed-2-0-lite-260215` |
| Access Key | 用于余额查询 | [获取](https://console.volcengine.com/iam/keymanage/) |
| Secret Key | 用于余额查询 | 同上 |

## 📝 添加文案风格

在 `prompts/` 目录下添加 `.txt` 文件，文件名即为风格名称。

示例 `prompts/催单朋友圈.txt`:
```
第一条示例文案...

第二条示例文案...
```

用空行分隔多条示例，模型会自动学习风格。

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Element Plus + TypeScript |
| 桌面框架 | Tauri 2.0 (Rust) |
| 后端 | Python Sidecar |
| AI | 火山引擎 ARK SDK |

## 📦 打包说明

打包后的应用结构：
```
文案生成器.exe
├── 前端界面 (Vue → Tauri)
├── Python sidecar (sidecar.exe)
└── prompts/ (文案模板)
```

用户只需双击 exe 即可使用，无需安装 Python 或 Node.js。

## 🔄 与之前方案的区别

| 方案 | 通信方式 | 优点 |
|------|----------|------|
| Gradio | 浏览器 → Python | 简单 |
| Tauri + FastAPI | Vue → HTTP → Python | 前后端分离 |
| **Tauri + Sidecar** | Vue → Rust → Python | **无 HTTP、更原生** |

## 📄 License

MIT
