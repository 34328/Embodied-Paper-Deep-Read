# Embodied Paper Deep Read

把一篇具身智能 / 机器人 / VLA / 世界模型论文，读成一份带原图、有页码依据的中文研读文档，默认发布到你自己的飞书「我的文档库」。

支持 **Claude Code**、**Codex** 和兼容 Agent Skills 格式的其他 agent。

> 授权：源码可见但非开源软件，仅限自然人个人非商业使用。见 [LICENSE](LICENSE) 与文末说明。

## 安装到当前 Agent

用户只需在正在使用的 Agent 里发出下面这段提示。Agent 会识别自己对应的个人 Skills
目录，只安装到该目录；不需要同时给 Claude Code 和 Codex 安装：

```text
请从 https://github.com/34328/Embodied-Paper-Deep-Read 安装 embodied-paper-deep-read，
只安装到你当前运行的 Agent 的个人 Skills 目录。先识别当前 Agent，再按仓库 README 的安装说明安装；
不要安装到其他 Agent，也不要装进当前项目目录。安装本 Skill 和所需的 Python 依赖后，运行安装检查。
MinerU 是云端解析服务：告诉我如何创建自己的 Token，并通过终端隐藏输入保存；不要让我把 Token 发到聊天里。
不要自动配置飞书；先报告 MinerU 与 Skill 检查结果。最后告诉我需要重启哪个 Agent。
```

如果手动安装，先克隆仓库，再只指定当前 Agent：

```bash
git clone https://github.com/34328/Embodied-Paper-Deep-Read.git
cd Embodied-Paper-Deep-Read
bash install.sh --agent codex   # 当前使用 Codex 时
# 或 bash install.sh --agent claude  # 当前使用 Claude Code 时
```

Codex 默认写入 `$CODEX_HOME/skills`（未设置时为 `~/.codex/skills`）；Claude Code 写入
`~/.claude/skills`（可由 `CLAUDE_CONFIG_DIR` 改写）。其他兼容 Agent Skills 的工具可用
`--dest /path/to/current-agent/skills` 指定其个人 Skills 目录。`--agent both` 仅供确实要
同时安装两份的用户显式选择。桌面 Agent 在本机运行时会安装到这台电脑的用户目录；云端或临时
Agent 只能安装到它自己的运行环境，未必会持久化到用户电脑。

安装脚本支持 macOS、Linux 和 WSL，需要 Bash、Python 3.9+、`curl`；原生 Windows 请使用 WSL。
它会为当前目标 Agent 安装 Skill，并配置 PyMuPDF/Pillow。安装完成后重启该 Agent。

### MinerU 与飞书依赖

MinerU 是远端解析服务，不是需要安装到电脑上的程序。安装脚本已经包含调用它的代码；首次使用前，
用户必须在 [MinerU Token 页面](https://mineru.net/apiManage/token) 登录并创建个人 Token，之后运行：

```bash
bash install.sh --set-token
```

Token 在终端里隐藏输入，保存到 `~/.mineru_token`，权限为 600。`--check` 能确认 Token 已配置和
文件权限正确，但不会验证 Token 是否仍有效；有效性要通过一次实际 MinerU 解析确认。该解析会把 PDF
上传给 MinerU，因此先用公开论文验证。MinerU API 当前限制单文件 200 MB、200 页。

飞书发布是可选项。准备好 Node.js 16+ 与 npm 后，可以一键安装或更新官方 `lark-cli`：

```bash
bash install.sh --agent codex --with-feishu
```

Claude Code 将 `codex` 替换成 `claude`。这里的 CLI 是系统命令；论文研读 Skill 本身仍只安装到当前
Agent 的 Skills 目录。CLI 内含与当前版本匹配的 `lark-doc`、`lark-shared` 使用说明，不需要再向
其他 Agent 目录安装 Skills。脚本不会自动创建飞书应用或替用户授权；随后由当前 Agent
引导用户完成应用配置和浏览器授权。若没有 Node.js，安装脚本会说明前置条件；它不会擅自替用户安装
系统级运行时。

### 验证安装

```bash
bash install.sh --check --agent codex   # Claude Code 用 --agent claude
```

绿色项表示 Skill 目录、Python 依赖、MinerU Token 配置已经就绪；黄色项是可选的飞书发布依赖。
检查成功后，重启当前 Agent，在技能列表中确认 `embodied-paper-deep-read`，再让它精读一篇公开 arXiv
论文完成端到端验证。若需要飞书发布，运行 `lark-cli skills read lark-doc` 确认 CLI 文档能力可用，
再运行 `lark-cli auth status` 确认登录状态。

其他命令：`bash install.sh --set-token` 设置 MinerU Token，`bash install.sh --uninstall` 卸载当前指定
Agent 的 Skill，`bash install.sh --help` 查看选项。

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

## 配置飞书授权

安装并配置好后，对当前 Agent 说「帮我配置飞书发布」。Agent 会引导完成应用配置和登录，
并在需要浏览器授权时停下来等用户操作。精读笔记只申请 Docs 与 Drive 所需权限。若不需要飞书，
可以要求输出本地 Markdown；论文正文仍必须经过 MinerU。

## MinerU 隐私边界

公开的 arXiv 论文可以直接使用 MinerU；未发表稿件、在审论文和内部资料必须先得到明确上传许可。
若不允许上传，Skill 会停止，不会用 PyMuPDF 全文解析冒充完成。脚本不会把 Token 写入仓库或论文目录。
接口细节见 [MinerU API 文档](https://mineru.net/apiManage/docs)。

## 常见问题

| 症状 | 原因 | 解决 |
|---|---|---|
| agent 里找不到这个 skill | 装完没重启或装到了其他 Agent 目录 | 重启当前 Agent；再用 `bash install.sh --check --agent codex` 或 `--agent claude` 检查 |
| `externally-managed-environment` | 系统 Python 受 PEP 668 保护 | 重跑 `bash install.sh --agent codex`（Claude Code 用 `--agent claude`），它会尝试改用私有虚拟环境 |
| `could not create .venv` | Debian/Ubuntu 缺 venv 模块 | 安装 `python3-venv` 后重跑相同的 `--agent` 命令 |
| `PyMuPDF/Pillow missing or unsupported` | conda / 多 Python 环境或系统 Python 受管控 | 重跑 `bash install.sh --agent codex`（Claude Code 用 `--agent claude`）；脚本会尝试私有虚拟环境 |
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
