# 开发

面向维护者。普通用户只需要 [README.md](README.md)。

## 仓库结构

```text
Embodied-Paper-Deep-Read/          仓库根目录
├── install.sh                     安装器（平台探测、依赖阶梯、体检、token）
├── embodied-paper-deep-read/      skill 本体，install.sh 复制的就是它
│   ├── SKILL.md                   入口与工作流
│   ├── scripts/                   下载、PDF 索引、MinerU、图片重渲染、标点归一化
│   ├── references/                精读深度、写作与版式规范
│   ├── publishers/                飞书 / 本地 Markdown 发布规则
│   └── agents/openai.yaml         Codex 界面元数据
├── tests/                         维护者测试，不会被当作 skill 加载
└── .github/workflows/ci.yml
```

内层目录名就是 skill 名，改名会同时影响 `SKILL.md` frontmatter、`agents/openai.yaml` 和测试断言。

## 本地验证

```bash
python3 -m pip install -r embodied-paper-deep-read/requirements-dev.txt
python3 -m unittest discover -s tests -v
python3 -m py_compile embodied-paper-deep-read/scripts/*.py
bash -n install.sh
bash -n embodied-paper-deep-read/scripts/mineru_parse_pdf.sh
```

测试使用临时生成的 PDF 和临时 `HOME`，不需要 MinerU token，不发网络请求，也不会写入飞书。

## 依赖解析的工作方式

`install.sh` 按阶梯解析 PyMuPDF：当前 `python3` 已可用 → `pip install` → `pip install --user` → 在已安装的 skill 目录下建 `.venv`。

最后一级会让文档里写的 `python3 <skill-dir>/scripts/x.py` 指向错误的解释器。解决办法不在文档层，而在 `scripts/_pymupdf.py`：`ensure_pymupdf()` 在导入 `fitz` 失败时，会 `os.execv` 重新执行自己到 `<skill-dir>/.venv`，用 `EPDR_PYMUPDF_REEXEC` 环境变量防止循环。三个脚本都在产生任何副作用之前调用它。

因此新增需要 PyMuPDF 的脚本时，照抄现有头部：

```python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pymupdf import ensure_pymupdf

ensure_pymupdf()
```

`sys.path` 那行不能省——`tests/test_skill.py` 用 `load_module()` 按路径加载脚本，此时 scripts 目录不在 `sys.path` 上。

## 约束

- skill 目录内不得出现 `~/.claude` 等本机路径，也不得关闭 TLS 校验（`tests/test_skill.py::test_no_machine_specific_or_insecure_paths` 会检查）。安装器相关的路径逻辑一律放在仓库根的 `install.sh` 里。
- MinerU token 只接受 `MINERU_TOKEN` 环境变量或 `~/.mineru_token`（600），不得读取仓库内的 token 文件。
- 根目录与 skill 目录的 `LICENSE` 必须逐字一致（有测试断言）。
- `install.sh` 需兼容 macOS 自带的 bash 3.2：不要用关联数组、`mapfile`、`${var,,}`。

## 图片分辨率这条链不能断

三个地方互相耦合，改任何一处都要同时看另外两处：

1. `scripts/mineru_parse_pdf.sh` 的落盘块必须把 `layout.json` 和 `full.md`、`images/` 一起保留；
2. `scripts/render_figures.py` 从 `layout.json` 读 MinerU 自己的 bbox，只重做栅格化；
3. `references/figure-extraction.md` 的 "Resolution" 一节和 `SKILL.md` 的完成检查，是让模型真的去执行第 2 步的唯一驱动力。

背景：MinerU 没有任何分辨率参数，出图上限约 1100px，矢量图更低（~685px）。760 CSS px 的图在 2x 屏上需要约 1520 物理像素，直接发 MinerU 的图就是糊的；显示宽度超过像素宽度则会放大，最显眼。

**绝不要自己推断图片边界** —— 基于文本块/绘图矩形的启发式试过两次都翻车（一次把标题作者 URL 吞进 teaser，一次把并排面板切一半）。按图片文件名映射，不要按图号（MinerU 会把 Figure 15 的面板标成 "Figure 14"）。每次渲染都要过宽高比校验，这依赖 `requirements.txt` 里的 Pillow。

`MineruOutputTests` 和 `RenderFiguresTests` 钉住了这条链的两端。

