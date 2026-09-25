# Embodied Paper Deep Read

把具身智能、机器人、VLA、世界模型等论文整理成有页码依据、包含高清原图的中文研读笔记，默认发布到飞书。

> 🔒 仅供个人非商业学习与研究使用。本项目源码可见，但不属于 OSI 开源软件，详见 [LICENSE](LICENSE)。

## 1. 🧭 安装前检查

### 环境要求

- 支持 **Codex、Claude Code** 和兼容 Agent Skills 格式的 Agent。
- 安装脚本支持 **macOS、Linux、WSL**；需要 Bash、Python 3.9+ 和 `curl`。原生 Windows 请使用 WSL。
- 飞书 CLI 需要 Node.js、npm 和 npx；缺少时，当前 Agent 会根据官方指南补齐安装步骤。
- 桌面 Agent 会安装到这台电脑的个人目录；云端 Agent 会安装到它自己的运行环境，可能不会持久保存到用户电脑。

## 2. 📦 安装到当前 Agent

### 一条提示完成安装

在正在使用的 Agent 中发送下面这段提示。它会识别当前 Agent、检查现有组件并跳过已就绪的步骤；不会把本 Skill 安装到其他 Agent。

```text
请从 https://github.com/34328/Embodied-Paper-Deep-Read 安装 embodied-paper-deep-read，
只安装到当前 Agent 的个人 Skills 目录。按 README 完成依赖配置和第 3–5 步检查。
检查到飞书 CLI、必需指南或授权缺失时，请直接按第 4 步的官方指南补齐，不要让我再发第二条安装提示；已安装且就绪时跳过。
如果 MinerU Token 缺失，请给我 Token 管理页链接，并在终端用隐藏输入配置；不要在聊天中索取、输出或保存 Token。
只在必须由我创建 Token、批准系统级安装或完成浏览器授权时暂停；完成后重新检查，并分别报告“论文精读”和“飞书发布”的状态。
```

### 手动安装

Agent 无法从提示中自动安装时，可手动安装到当前 Agent 的个人目录：

```bash
git clone https://github.com/34328/Embodied-Paper-Deep-Read.git
cd Embodied-Paper-Deep-Read
bash install.sh --agent codex   # Claude Code 使用 --agent claude
```

其他兼容 Agent 可用 `--dest /path/to/skills` 指定它的个人 Skills 目录。安装后重启当前 Agent（如果没有自动发现 Skill）。

## 3. 🔑 配置 MinerU

### 创建并保存 Token

MinerU 负责解析论文正文。打开 [MinerU Token 管理页](https://mineru.net/apiManage/token) 注册或登录、创建并复制 Token，然后在终端运行 `bash install.sh --set-token`；粘贴时输入会被隐藏，Token 保存到权限为 `600` 的 `~/.mineru_token`。不要把 Token 发到聊天中。

### 上传隐私

MinerU 会接收完整 PDF。公开论文可直接解析；未发表、在审、内部或其他非公开材料，上传前必须得到用户明确许可。没有许可时停止解析。

## 4. 📝 安装和授权飞书 CLI

### 检查并补齐缺失项

飞书是默认发布目标，完成本节后才能直接发布到飞书。Agent 会先检查 `lark-cli`、其必需的 `lark-doc` / `lark-shared` 指南和账号授权：**全部就绪时自动跳过**；CLI 已安装但未授权时只补应用配置和登录；CLI 缺失或指南不全时按官方指南补齐，不使用本项目自建的安装流程。

### 官方安装入口

飞书官网提供的 Agent 安装提示：

```text
帮我安装飞书 CLI：https://open.feishu.cn/document/no_class/mcp-archive/feishu-cli-installation-guide.md
```

也可从[飞书 CLI 官网](https://www.feishu.cn/feishu-cli)进入。官方指南会安装 `lark-cli` 及其必需的 CLI Skill；浏览器登录和授权由用户本人完成。缺少 Node.js/npm/npx 时，Agent 会先按当前系统的受支持方式安装运行环境；也可查看 [Node.js 官方下载页](https://nodejs.org/en/download/)。

官方指南中的 `npx skills add` 步骤只安装到**当前 Agent 的用户级目录**：保留指南中的参数，并追加 `--global --agent <当前 Agent 标识>`（例如 Codex 用 `codex`，Claude Code 用 `claude-code`）。不要选全部 Agent，也不要安装到项目目录。

## 5. ✅ 验证安装

### 运行状态检查

在仓库目录运行（Claude Code 将 `codex` 替换为 `claude`）：

```bash
bash install.sh --check --agent codex
```

检查会分开展示两项状态：

- **论文精读**：当前 Agent 的 Skill、PyMuPDF/Pillow 和 MinerU Token 文件及权限。
- **飞书发布**：`lark-cli`、必需的 CLI 指南和账号授权是否就绪。全部就绪时会明确显示“无需安装”。

`--check` 的退出码表示“论文精读”基础条件是否就绪；飞书发布状态请看单独的状态项。
`--check` 与 Skill 内置的 `scripts/check_setup.sh` 共用同一套检查逻辑，不会修改环境。Feishu CLI 未就绪不会阻止论文下载、解析或撰写；用户仅要求本地 Markdown 时可跳过发布端检查。MinerU Token 检查只验证本地配置与文件权限，不会验证 Token 是否仍有效；用一篇公开 arXiv 论文完成一次实际解析才能验证可用性，该操作会上传 PDF。[MinerU API 文档](https://mineru.net/apiManage/docs)列出单文件 200 MB、200 页的限制。

### 常见问题

<details>
<summary>展开查看</summary>

- **Agent 找不到 Skill**：重启当前 Agent，再用上面的 `--check` 确认目标目录。
- **MinerU 返回 401**：在 [Token 管理页](https://mineru.net/apiManage/token)重新创建 Token，然后运行 `bash install.sh --set-token`。
- **飞书显示未授权**：运行 `lark-cli auth status --json --verify`，按官方流程完成应用配置和浏览器登录；不需要重装已存在的 CLI。
- **Debian/Ubuntu 缺少 venv**：安装 `python3-venv` 后重跑当前 Agent 的安装命令。

</details>

## 6. 📚 开始精读

### 示例

在 Agent 中附上 arXiv 链接或本地 PDF：

```text
用 embodied-paper-deep-read 精读这篇论文，并发布到我的飞书文档库：https://arxiv.org/abs/2503.20020
```

Codex 可用 `$embodied-paper-deep-read`，Claude Code 可用 `/embodied-paper-deep-read`，也可以直接描述任务。需要本地文件时，可要求输出 Markdown；每篇论文会生成独立工作目录。研读类别只有模型类和数据类，二者沿用同一套五章骨架；技术报告中出现的数据管线、模型、评测、系统、安全或部署内容，都会按其技术重要性纳入精读。选中的论文图会从 PDF 重渲染或裁切为高清版本。

更多安装选项见 `bash install.sh --help`；开发说明见 [CONTRIBUTING.md](CONTRIBUTING.md)。
