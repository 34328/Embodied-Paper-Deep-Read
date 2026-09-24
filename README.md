# Embodied Paper Deep Read

把一篇具身智能 / 机器人 / VLA / 世界模型论文，读成一份带原图、有页码依据的中文研读文档，默认发布到你自己的飞书「我的文档库」。

支持 **Claude Code** 和 **Codex**。

Skill 本身只依赖标准的 `SKILL.md` 目录结构；能加载这种目录的其他 agent 也可以使用同一份源码。
安装器用 `--dest /path/to/that-agent/skills` 指向它的用户 skill 目录，不会把某个 agent 的专用
配置写进正文流程。

> 授权：源码可见但非开源软件，仅限自然人个人非商业使用。见 [LICENSE](LICENSE) 与文末说明。

## 安装

```bash
git clone https://github.com/34328/Embodied-Paper-Deep-Read.git
cd Embodied-Paper-Deep-Read
bash install.sh --agent both
```

安装脚本会把同一份 skill 安装到 Claude Code 和 Codex 的官方用户目录，并安装
PyMuPDF、Pillow 等本地依赖。它不会替用户创建 MinerU 账号、完成浏览器授权，
也不会把凭据写进仓库。重复运行是幂等的。

安装器覆盖 macOS、Linux 和 WSL（需要 Bash、Python 3.9+、`curl`）；原生 Windows 不在这份
Bash 安装脚本的支持范围内，请在 WSL 中运行。论文下载、MinerU 解析和飞书发布都需要相应的
网络访问。

只使用一个 agent 时可运行 `--agent claude` 或 `--agent codex`。不传 `--agent`
会根据本机可检测到的 agent 自动选择；需要明确安装到两个 agent 时建议始终使用
`--agent both`。Claude Code 使用 `~/.claude/skills`（或 `CLAUDE_CONFIG_DIR/skills`），
Codex 使用 `~/.agents/skills`。旧版 `~/.codex/skills/paper-deep-read` 只会被报告，
不会被脚本自动覆盖或删除。

装完**重启 agent**，然后确认 skill 已被识别。

想检查状态或重装某一项，随时运行：

```bash
bash install.sh --check       # 只体检，不改任何东西
bash install.sh --set-token   # 配置 MinerU token
bash install.sh --uninstall   # 卸载
bash install.sh --help        # 全部选项
```

`--check` 的红色项目表示还不能完成一次 MinerU 精读；黄色项目是可选的飞书发布配置。
安装器会逐个检查目标 agent 和 PyMuPDF/Pillow，而不是只检查某一个 Python 环境。

如果使用其他兼容 agent，可把源码安装到它的 skill 目录：

```bash
bash install.sh --dest /path/to/agent/skills --skip-deps
```

然后按该 agent 的规则重启或重新加载 skill；`--dest` 只复制本 skill 管理的文件。

### 首次可用的最短路径

完整精读必须经过 MinerU。PyMuPDF 只用于页码、公式和表格的定点核对，以及从原 PDF
重渲染高清图片，不能替代 MinerU 的正文解析。

1. 安装 skill 和本地依赖：`bash install.sh --agent both`。
2. 在 [MinerU Token 页面](https://mineru.net/apiManage/token) 创建 token，然后运行
   `bash install.sh --set-token`。输入只在终端隐藏读取，保存为权限 600 的
   `~/.mineru_token`；也可以在启动 agent 的同一环境中设置 `MINERU_TOKEN`。
3. 运行 `bash install.sh --check`，确认 MinerU token、两个 Python 依赖和目标 agent 均为绿色。

Token 和浏览器授权无法由脚本代办；这两步会明确停下来提示你操作。

## 使用

在 agent 里附上 arXiv 链接或本地 PDF：

```text
用 embodied-paper-deep-read 精读这篇论文，发布到我的飞书文档库：https://arxiv.org/abs/2503.20020
```

Codex 里用 `$embodied-paper-deep-read` 显式调用，Claude Code 里用 `/embodied-paper-deep-read`，或者直接自然语言描述也能触发。

两个常用变体：

```text
Use embodied-paper-deep-read to deep-read this paper and publish a Chinese study note to my Feishu documents.
用 embodied-paper-deep-read 精读这个本地 PDF。它是内部材料，我确认可以上传到 MinerU，结果存成本地 Markdown。
```

每篇论文会在当前工作区生成一个独立目录，包含 PDF、页级索引、MinerU 输出、证据笔记、图片清单和发布状态。凭据不会写进论文目录。

默认行为：输出中文；发布到当前登录用户的飞书「我的文档库」；只有你明确要求生成或发布时才会创建飞书文档，不会擅自覆盖已有文档。

## 可选：发布到飞书

默认发布后端是飞书。把下面这句话交给 agent，它会按官方指南检查并执行安装：

```text
帮我安装飞书 CLI：https://open.feishu.cn/document/no_class/mcp-archive/feishu-cli-installation-guide.md
```

这句提示词来自[飞书 CLI 官方安装指南](https://open.feishu.cn/document/no_class/mcp-archive/feishu-cli-installation-guide.md)。
Node.js、npm/npx、`@larksuite/cli`、配套 skill、应用配置和登录验证都属于飞书发布依赖。

装好之后说「帮我配置飞书发布」，本 skill 会把授权范围收到只要 Docs 和 Drive —— 发论文文档用不上更多权限。

全程只有一件事必须你本人做：**在浏览器里点授权**。agent 会把授权链接发给你，你确认后它自动继续。

前提是机器上有 Node.js（提供 `npm`/`npx`）。如果不需要飞书，可在提示词中要求输出本地 Markdown；
但 PDF 正文仍必须先经过 MinerU。

## 配置 MinerU（精读必需）

MinerU 是本 skill 的正文解析入口，负责复杂公式、表格、版面和图片的结构化抽取。
PyMuPDF 不再作为正文解析回退；没有 token、没有上传许可、服务失败或超过服务页数限制时，
skill 会停止并说明下一步，不会悄悄输出不完整的精读。

到 **[mineru.net/apiManage/token](https://mineru.net/apiManage/token)** 登录后创建一个 API Token，然后：

```bash
bash install.sh --set-token
```

隐藏输入，写入 `~/.mineru_token`（权限 600）。也可以改用 `MINERU_TOKEN` 环境变量，环境变量优先。
如果接口返回 401，按服务页面重新创建 token 后再运行上面的命令。

> ⚠️ MinerU 是国内服务，**开着 VPN / 代理打不开这个页面**，申请前先关掉。后续调用接口同理。

接口细节和配额见 [API 文档](https://mineru.net/apiManage/docs)。

**隐私边界**：使用 MinerU 会把完整 PDF 上传给第三方。公开的 arXiv 论文可以直接使用；
未发表稿件、在审论文和内部资料必须先得到你的明确同意。若不允许上传，本 skill 会停止，
不会用 PyMuPDF 全文冒充完成。脚本不会关闭 TLS 校验，不会读取仓库内的 token 文件，
也不会把 token 写进日志或输出文档。

## 常见问题

| 症状 | 原因 | 解决 |
|---|---|---|
| agent 里找不到这个 skill | 装完没重启 | 重启 agent；再跑 `bash install.sh --check` 确认装到了哪 |
| `externally-managed-environment` | 系统 Python 受 PEP 668 保护 | 重跑 `bash install.sh`，它会自动改用私有虚拟环境 |
| `could not create .venv` | Debian/Ubuntu 缺 venv 模块 | `sudo apt install python3-venv` 后重跑 |
| `PyMuPDF/Pillow missing or unsupported` | conda / 多 Python 环境或系统 Python 受管控 | 重跑 `bash install.sh`；脚本会尝试私有虚拟环境 |
| `MINERU_TOKEN is not set and ~/.mineru_token does not exist` | 精读所需 token 未配置 | 到 [申请页](https://mineru.net/apiManage/token) 创建后运行 `bash install.sh --set-token` |
| MinerU 返回 `401` | token 无效或已失效 | 重新创建 token 后运行 `bash install.sh --set-token` |
| MinerU 页面打不开 / 请求超时 | 开着 VPN 或代理 | 关掉代理再试，MinerU 是国内服务 |
| lark-cli 报 `unsafe file path` | 传了绝对路径的 `@file` | `cd` 到图片目录，改用 `./fig.png` 这样的相对路径 |
| 发布飞书时提示未登录 / 无权限 | 还没配过飞书 | 对 agent 说「帮我配置飞书发布」，按它给的链接授权 |
| `python3 not found` / 版本过低 | 需要 Python 3.9+ | 装一个新版 Python 后重跑安装 |

## 开发

见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

本项目采用自定义的 **Personal Learning License 1.0**：

- 仅允许自然人用于个人、非商业的学习、研究、实验和兴趣项目；
- 允许为上述目的在本地运行、复制和私下修改；
- 禁止任何公司、雇主、客户、学校、研究机构、非营利组织或其他组织使用；
- 禁止商业项目、付费服务、SaaS、咨询、课程或内容变现、商业模型训练；
- 禁止重新发布、镜像、转售、转授权或公开分发修改版本；
- 商业或组织用途必须另行取得版权所有者的书面授权。

这是一份源码可见许可证，不属于 OSI 认可的开源许可证。完整且具有约束力的英文条款见 [LICENSE](LICENSE)。论文、论文图片、PyMuPDF、MinerU 和飞书 CLI 仍分别受其原始许可证与服务条款约束。
