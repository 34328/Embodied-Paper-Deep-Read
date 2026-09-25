#!/usr/bin/env bash
# Shared setup check for the installed skill and the repository installer.

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
DEFAULT_SKILL_DIR=$(cd "$SCRIPT_DIR/.." && pwd)
TOKEN_FILE="${HOME:-}/.mineru_token"
SKILL_DIRS=()
CHECK_FEISHU=true

REQUIRED_SKILL_FILES="
  SKILL.md
  scripts/fetch_arxiv.py scripts/index_pdf.py scripts/mineru_parse_pdf.sh
  scripts/pdf_page_count.py scripts/render_figures.py scripts/extract_figures.py
  scripts/normalize_cjk_punct.py scripts/_pymupdf.py scripts/check_setup.sh
  references/reading-scope.md references/figure-extraction.md references/content-depth.md
  references/writing-style.md references/doc-structure.md references/beautify.md
  publishers/feishu.md publishers/local-md.md agents/openai.yaml
"

say()  { printf '  %s\n' "$*"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; }
bad()  { printf '  \033[31m✗\033[0m %s\n' "$*"; }
head_() { printf '\n\033[1m%s\033[0m\n' "$*"; }

usage() {
  cat <<'EOF'
Usage: bash scripts/check_setup.sh [options]

Options:
  --skill-dir DIR  Check an installed skill directory (repeatable)
  --skip-feishu    Skip publisher checks when local Markdown is requested
  -h, --help       Show this help

The exit status reflects paper-reading readiness only. Feishu readiness is reported
separately and does not block reading; unresolved Feishu setup affects publishing only.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --skill-dir)
      [ "$#" -ge 2 ] || { usage >&2; exit 2; }
      SKILL_DIRS+=("$2")
      shift 2
      ;;
    --skip-feishu) CHECK_FEISHU=false; shift ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; printf 'Unknown option: %s\n' "$1" >&2; exit 2 ;;
  esac
done
[ "${#SKILL_DIRS[@]}" -gt 0 ] || SKILL_DIRS=("$DEFAULT_SKILL_DIR")

python_supported() {
  "$1" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1
}

has_deps() {
  "$1" -c '
import re
import sys
from importlib import metadata
import fitz
from PIL import Image

def version(package):
    match = re.match(r"^(\d+)\.(\d+)", metadata.version(package))
    return tuple(map(int, match.groups())) if match else (0, 0)

ok = hasattr(fitz, "open") and hasattr(Image, "open")
ok = ok and (1, 23) <= version("PyMuPDF") < (2, 0)
ok = ok and (9, 0) <= version("Pillow") < (13, 0)
sys.exit(0 if ok else 1)
' >/dev/null 2>&1
}

token_file_secure() {
  [ -f "$TOKEN_FILE" ] && [ ! -L "$TOKEN_FILE" ] || return 1
  py=$(command -v python3 2>/dev/null) || return 1
  "$py" - "$TOKEN_FILE" <<'PY' >/dev/null 2>&1
import os, stat, sys
info = os.stat(sys.argv[1])
sys.exit(0 if stat.S_ISREG(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o600 else 1)
PY
}

feishu_auth_ready() {
  local auth_json py
  py=$(command -v python3 2>/dev/null) || return 1
  auth_json=$(lark-cli auth status --json --verify 2>/dev/null) || return 1
  printf '%s\n' "$auth_json" | "$py" -c '
import json, sys
try:
    data = json.load(sys.stdin)
except (ValueError, TypeError):
    sys.exit(1)
user = data.get("identities", {}).get("user", {})
sys.exit(0 if user.get("available") is True and user.get("status") == "ready" and user.get("tokenStatus") == "valid" else 1)
' >/dev/null 2>&1
}

feishu_runtime_status() {
  local tool tool_path
  for tool in node npm npx; do
    if tool_path=$(command -v "$tool" 2>/dev/null) && "$tool" --version >/dev/null 2>&1; then
      ok "$tool is available: $tool_path"
    else
      bad "$tool is missing or cannot start"
    fi
  done
  say "Install or repair Node.js (includes npm/npx): https://nodejs.org/en/download/"
}

feishu_status() {
  local lark_bin lark_version guidance_ready auth_ready
  head_ "Feishu publishing readiness"
  if lark_bin=$(command -v lark-cli 2>/dev/null); then
    if ! lark_version=$(lark-cli --version 2>/dev/null); then
      warn "lark-cli was found but cannot start"
      feishu_runtime_status
      say "Repair the CLI by following the official Feishu guide:"
      say "  https://open.feishu.cn/document/no_class/mcp-archive/feishu-cli-installation-guide.md"
      return 0
    fi
    ok "lark-cli installed: $lark_version ($lark_bin)"
    guidance_ready=true
    if ! lark-cli skills read lark-doc >/dev/null 2>&1 || \
       ! lark-cli skills read lark-shared >/dev/null 2>&1; then
      warn "Feishu CLI guidance is incomplete; install the required CLI Skill from the official guide"
      say "Guide: https://open.feishu.cn/document/no_class/mcp-archive/feishu-cli-installation-guide.md"
      guidance_ready=false
    else
      ok "Feishu CLI guidance is available"
    fi
    if feishu_auth_ready; then
      ok "Feishu user authorization verified"
      auth_ready=true
    else
      warn "lark-cli is installed, but Feishu authorization is not verified"
      say "Complete app setup and browser login, then verify with: lark-cli auth status --json --verify"
      say "Guide: https://open.feishu.cn/document/no_class/mcp-archive/feishu-cli-installation-guide.md"
      auth_ready=false
    fi
    if [ "$guidance_ready" = true ] && [ "$auth_ready" = true ]; then
      ok "Feishu publishing is ready; no installation needed"
    fi
    return 0
  fi
  warn "lark-cli is not installed"
  feishu_runtime_status
  say "Continue setup in the current Agent with the official Feishu guide:"
  say "  帮我安装飞书 CLI：https://open.feishu.cn/document/no_class/mcp-archive/feishu-cli-installation-guide.md"
}

head_ "Paper-reading requirements"
paper_ready=true
py=$(command -v python3 2>/dev/null || true)
if [ -z "$py" ]; then
  bad "python3 not found (Python 3.9+ required)"
  paper_ready=false
elif ! python_supported "$py"; then
  bad "python3 is older than 3.9: $py"
  paper_ready=false
else
  say "python3: $py"
fi

for skill_dir in "${SKILL_DIRS[@]}"; do
  files_ready=true
  for item in $REQUIRED_SKILL_FILES; do
    if [ ! -f "$skill_dir/$item" ]; then
      bad "skill file missing: $skill_dir/$item"
      files_ready=false
      paper_ready=false
    fi
  done
  if [ "$files_ready" = true ]; then
    ok "skill files installed: $skill_dir"
  fi

  venv="$skill_dir/.venv/bin/python3"
  if [ -n "$py" ] && python_supported "$py" && has_deps "$py"; then
    ok "PyMuPDF and Pillow ready for $skill_dir (current Python)"
  elif [ -x "$venv" ] && has_deps "$venv"; then
    ok "PyMuPDF and Pillow ready for $skill_dir (private virtualenv)"
  else
    bad "PyMuPDF/Pillow missing or unsupported for $skill_dir — install the skill dependencies"
    paper_ready=false
  fi
done

if [ -n "${MINERU_TOKEN:-}" ]; then
  ok "MinerU token: MINERU_TOKEN is set (validity not checked)"
elif token_file_secure; then
  ok "MinerU token: $TOKEN_FILE (mode 600; validity not checked)"
elif [ -f "$TOKEN_FILE" ]; then
  bad "MinerU token file must be a regular mode-600 file: $TOKEN_FILE"
  paper_ready=false
else
  bad "MinerU token missing (required) — open https://mineru.net/apiManage/token, then run install.sh --set-token"
  paper_ready=false
fi

head_ "Paper-reading readiness"
if [ "$paper_ready" = true ]; then
  ok "Skill files, Python dependencies, and MinerU token are configured"
else
  warn "Paper-reading setup is incomplete; resolve the items marked ✗ above"
fi

if [ "$CHECK_FEISHU" = true ]; then
  feishu_status
else
  say "Feishu check skipped (--skip-feishu)"
fi

[ "$paper_ready" = true ]
