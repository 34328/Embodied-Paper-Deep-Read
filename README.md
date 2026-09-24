# Embodied Paper Deep Read

把具身智能、机器人、VLA、世界模型等论文整理成有页码依据、包含高清原图的中文研读笔记，可发布到飞书或保存为 Markdown。

> 仅供个人非商业学习与研究使用；本项目源码可见，但不属于 OSI 开源软件。详见 [LICENSE](LICENSE)。

## 快速开始

### 安装到当前 Agent

在正在使用的 Agent 中发送：

```text
请从 https://github.com/34328/Embodied-Paper-Deep-Read 安装 embodied-paper-deep-read，
只安装到当前 Agent 的个人 Skills 目录。按仓库 README 配置依赖并运行安装检查，告诉我安装路径和是否需要重启。
若 MinerU Token 尚未配置，请给我 Token 管理页链接，并指导我用终端隐藏输入；不要向聊天索取或输出 Token。
不要安装到其他 Agent 或当前项目的 Skills 目录。
```

Agent 会根据运行环境选择 Codex、Claude Code 或其他兼容 Agent Skills 的个人目录。桌面 Agent 写入本机；云端 Agent 写入其运行环境，未必会保存到用户电脑。

手动安装时，克隆仓库并指定当前 Agent：

```bash
git clone https://github.com/34328/Embodied-Paper-Deep-Read.git
cd Embodied-Paper-Deep-Read
bash install.sh --agent codex   # Claude Code 使用 --agent claude
```

其他兼容 Agent 可用 `--dest /path/to/skills` 指定 Skills 目录。安装脚本支持 macOS、Linux 和 WSL，需要 Bash、Python 3.9+ 与 `curl`；原生 Windows 请在 WSL 中运行。安装完成后重启当前 Agent。

### 配置 MinerU

MinerU 负责解析论文正文。打开 [MinerU Token 管理页](https://mineru.net/apiManage/token) 注册或登录，创建并复制 API Token，然后在终端运行 `bash install.sh --set-token`，按提示粘贴；输入会被隐藏，Token 保存到权限为 `600` 的 `~/.mineru_token`。不要把 Token 发到 Agent 对话中。

### 可选：安装飞书 CLI

打开[飞书 CLI 官网](https://www.feishu.cn/feishu-cli)，在当前 Agent 中发送官网推荐的安装提示：

```text
帮我安装飞书 CLI：https://open.feishu.cn/document/no_class/mcp-archive/feishu-cli-installation-guide.md
```

Agent 会按官方指南安装和配置；浏览器授权由用户本人完成。验证登录状态：`lark-cli auth status`。
官方安装需要 Node.js、npm 和 npx。

### 验证

```bash
bash install.sh --check --agent codex   # Claude Code 使用 --agent claude
```

检查会确认 Skill 目录、PyMuPDF/Pillow 和 MinerU Token 配置。它不会验证 Token 是否有效；用一篇公开 arXiv 论文完成一次精读，才能验证 MinerU 解析是否可用。该操作会把 PDF 上传给 MinerU。[API 文档](https://mineru.net/apiManage/docs)说明单文件上限为 200 MB、200 页。

## 使用

在 Agent 中输入 arXiv 链接或附上本地 PDF，例如：

```text
用 embodied-paper-deep-read 精读这篇论文，并发布到我的飞书文档库：https://arxiv.org/abs/2503.20020
```

Codex 可用 `$embodied-paper-deep-read`，Claude Code 可用 `/embodied-paper-deep-read`，也可以直接描述任务。若希望保存本地文件，可要求输出 Markdown；处理未公开 PDF 时，请明确确认允许上传到 MinerU。

每篇论文生成独立工作目录，保存 PDF、MinerU 解析、证据笔记、图片清单和发布状态。基础模型与方法论文沿用固定研读骨架；数据管线、治理和 benchmark 论文使用对应的专门结构。选中的论文图会从原 PDF 重渲染或裁切为高清版本。

## 隐私与限制

MinerU 会接收完整 PDF。公开论文可直接解析；未发表、在审、内部或其他非公开材料，必须先取得用户对上传的明确许可。没有许可时，停止解析。

PyMuPDF 用于页码核对和高清图片处理，不替代 MinerU 解析正文。Token 与浏览器授权不会写入论文目录。

## 故障排查

- Agent 找不到 Skill：重启 Agent，并用 `install.sh --check --agent <codex|claude>` 确认安装目录。
- MinerU 返回 401：在 Token 管理页重新创建 Token，再运行 `bash install.sh --set-token`。
- Python 依赖未就绪：重跑当前 Agent 的安装命令；Debian/Ubuntu 若提示缺少 venv，可安装 `python3-venv` 后重试。
- 飞书未登录：按上面的官方提示完成配置，并运行 `lark-cli auth status`。

更多安装选项见 `bash install.sh --help`；开发说明见 [CONTRIBUTING.md](CONTRIBUTING.md)。
