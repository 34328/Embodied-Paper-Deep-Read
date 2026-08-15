# Embodied Paper Deep Read

> **授权说明：** 本项目源码可见，但不是 OSI 定义的开源软件。仅允许自然人用于个人、
> 非商业的学习、研究和实验；禁止商用、组织内部使用和再分发。完整条款见
> [Personal Learning License 1.0](LICENSE)。

一个用于具身智能、机器人、视觉—语言—动作模型及相关 AI 论文精读的 Codex skill。它会获取或索引
PDF，建立带页码的证据笔记，筛选论文原图，撰写结构化中文研读文档，并默认发布到用户自己的
飞书“我的文档库”。

## 到底哪个目录才是 skill？

真正需要安装和使用的是仓库中的 **`embodied-paper-deep-read/`**，因为它里面包含入口文件
`SKILL.md`。仓库根目录只是用于发布、说明和测试：

```text
embodied-paper-deep-read/          仓库根目录，不要把整个目录当成 skill 安装
├── README.md                      用户说明
├── LICENSE                        仓库许可证
├── embodied-paper-deep-read/      ✅ 真正的 skill，用户安装这个目录
│   ├── SKILL.md                   skill 入口和工作流
│   ├── scripts/                   下载、PDF 索引、MinerU 和图片处理脚本
│   ├── references/                精读深度、写作和版式规范
│   ├── publishers/                飞书与本地 Markdown 发布规则
│   └── agents/openai.yaml         Codex 界面元数据
├── tests/                         仅供维护者开发测试，普通用户不用运行
└── .github/workflows/ci.yml       GitHub 自动测试，普通用户不用处理
```

普通用户只需要：安装 `embodied-paper-deep-read/`、安装运行依赖、配置飞书 CLI，并按需配置
MinerU。`tests/` 不参与论文精读，也不会被 Codex 当作 skill 加载。

## 默认行为

- 输出语言：中文。
- 发布位置：当前登录用户的飞书“我的文档库”。
- PDF 解析：公开 arXiv 论文优先使用 MinerU；用户上传的非公开 PDF 必须先获得明确同意。
- 无法或不允许上传 MinerU 时：使用本地 PyMuPDF 页级索引继续研读。
- 只有用户请求生成或发布研读文档时才创建飞书文档；不会擅自覆盖已有文档。

## 普通用户安装步骤

### 第一步：安装 skill 和 Python 依赖

克隆仓库后，将 **`embodied-paper-deep-read/`** 复制到 Codex 的个人 skills 目录。不要复制
`tests/`：

```bash
cd /path/to/embodied-paper-deep-read
mkdir -p "$HOME/.agents/skills"
cp -R embodied-paper-deep-read "$HOME/.agents/skills/"
python3 -m pip install -r "$HOME/.agents/skills/embodied-paper-deep-read/requirements.txt"
```

Codex 通常会自动检测新增 skill。如果输入 `$embodied-paper-deep-read` 后没有出现该 skill，请重启
Codex 再试。也可以在 Codex CLI 或 IDE 扩展中运行 `/skills` 查看是否已加载。

### 第二步：安装和配置飞书 CLI

由于本 skill 默认把研读文档发布到用户自己的飞书“我的文档库”，普通用户需要安装飞书官方
维护的 [`@larksuite/cli`](https://github.com/larksuite/cli)。需要 Node.js 16 或更高版本。

```bash
npx @larksuite/cli@latest install
lark-cli config init
lark-cli auth login --domain docs --domain drive
lark-cli auth status --json --verify
```

首次配置与登录会要求用户在浏览器中完成飞书应用配置和授权。请遵循最小权限原则，只授权 Docs
和 Drive 等完成论文发布所需的权限。若 CLI 命令发生变化，以其内置文档为准：

```bash
lark-cli skills read lark-doc
lark-cli docs --help
```

如果不想安装飞书 CLI，可以在提示词中明确要求输出本地 Markdown。

### 第三步：按需配置 MinerU

MinerU 是第三方文档解析服务，脚本会把完整 PDF 上传给 MinerU。请先阅读
[MinerU 官方 API 文档](https://mineru.net/doc/docs/index_en/)，登录 MinerU 官网并在个人中心申请
Precision Extract API Token，然后在当前 shell 会话中通过环境变量配置。为避免 token 进入命令
历史，可以使用隐藏输入：

```bash
# Bash
read -rsp "MinerU API token: " MINERU_TOKEN && printf '\n'
export MINERU_TOKEN

# Zsh
read -rs 'MINERU_TOKEN?MinerU API token: ' && printf '\n'
export MINERU_TOKEN
```

环境变量必须存在于启动 Codex 的环境中。如果使用 Codex CLI，请从设置了该变量的同一个终端
启动 Codex；如果使用桌面应用，请通过操作系统的安全环境变量或密码管理方案注入变量，然后重启
Codex。没有 MinerU token 时，仍可要求 skill 使用本地 PDF 索引，但复杂公式、表格和原图抽取
质量可能下降。

建议把该命令写入本机安全的 shell 配置或密码管理方案。不要把 token：

- 粘贴到聊天中；
- 写进 `SKILL.md`、README、脚本或明文 shell 配置；
- 提交到 Git；
- 放进论文输出目录。

脚本不会读取仓库内的 token 文件，也不会关闭 TLS 证书校验。未配置 token 时会停止并给出配置提示。

## 使用

完成上述配置后，在 Codex 中附上 arXiv 链接或 PDF，并调用：

```text
使用 $embodied-paper-deep-read 精读这篇论文，并把中文研读文档发布到我的飞书文档库：<arXiv URL>
```

英文提示词也可以：

```text
Use $embodied-paper-deep-read to deep-read this paper and publish a Chinese study note to my Feishu documents.
```

也可以明确要求不进行任何第三方上传并输出本地 Markdown：

```text
Use $embodied-paper-deep-read to analyze this local PDF without uploading it, and save the note as local Markdown.
```

每篇论文会在当前工作区得到一个独立目录，其中包含 PDF、页级索引、MinerU 输出（如果启用）、
证据笔记、图像清单和发布状态。MinerU token 与飞书凭据不会写入论文目录。

## 开发与验证

```bash
python3 -m pip install -r embodied-paper-deep-read/requirements-dev.txt
python3 -m unittest discover -s tests -v
python3 -m py_compile embodied-paper-deep-read/scripts/*.py
bash -n embodied-paper-deep-read/scripts/mineru_parse_pdf.sh
```

测试使用临时生成的 PDF，不需要 MinerU token，也不会写入飞书。

## 许可证

本项目采用自定义的 **Personal Learning License 1.0**：

- 仅允许自然人用于个人、非商业的学习、研究、实验和兴趣项目；
- 允许为上述目的在本地运行、复制和私下修改；
- 禁止任何公司、雇主、客户、学校、研究机构、非营利组织或其他组织使用；
- 禁止商业项目、付费服务、SaaS、咨询、课程或内容变现、商业模型训练；
- 禁止重新发布、镜像、转售、转授权或公开分发修改版本；
- 商业或组织用途必须另行取得版权所有者的书面授权。

这是一份源码可见许可证，不属于 OSI 认可的开源许可证。完整且具有约束力的英文条款见
[LICENSE](LICENSE)。论文、论文图片、PyMuPDF、MinerU 和飞书 CLI 仍分别受其原始许可证与
服务条款约束。
