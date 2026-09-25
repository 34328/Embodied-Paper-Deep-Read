#!/usr/bin/env bash
# Installer for the Embodied Paper Deep Read skill.
# Copies the skill into one selected agent directory and resolves
# the Python dependency so that `python3 <skill-dir>/scripts/...` works afterwards.
set -euo pipefail

SKILL_NAME="embodied-paper-deep-read"
REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SOURCE_DIR="$REPO_ROOT/$SKILL_NAME"

CLAUDE_SKILLS="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
if [ -n "${CODEX_HOME:-}" ]; then
  CODEX_SKILLS="$CODEX_HOME/skills"
elif [ -f "$HOME/.agents/skills/$SKILL_NAME/SKILL.md" ]; then
  CODEX_SKILLS="$HOME/.agents/skills"
elif [ -f "$HOME/.codex/skills/$SKILL_NAME/SKILL.md" ]; then
  CODEX_SKILLS="$HOME/.codex/skills" # Retain an existing Codex installation.
else
  CODEX_SKILLS="$HOME/.agents/skills"
fi
LEGACY_SKILL_NAME="paper-deep-read"
TOKEN_FILE="$HOME/.mineru_token"
FEISHU_READY=false

# Directory contents this installer refreshes. The private dependency venv and
# any files outside this list are left alone.
MANAGED_DIRS="scripts references publishers agents"
MANAGED_FILES="SKILL.md LICENSE requirements.txt requirements-dev.txt"
DEST=""
AGENT="auto"
DO_CHECK=false
DO_SET_TOKEN=false
DO_UNINSTALL=false
SKIP_DEPS=false
PYTHON=""

usage() {
  cat <<'EOF'
Usage: bash install.sh [options]

Options:
  --agent NAME    claude, codex, both, or auto (default; prompts interactively)
  --dest DIR      Install into DIR instead of an agent's skills directory
  --check         Check paper-reading requirements and Feishu CLI/auth; change nothing
  --set-token     Store a MinerU API token in ~/.mineru_token (mode 600)
  --skip-deps     Copy the skill but do not touch Python dependencies
  --uninstall     Remove the installed skill (leaves ~/.mineru_token alone)
  -h, --help      Show this help

Install into one selected agent's user skill root and resolve Python dependencies.
--check returns the paper-reading readiness; Feishu readiness is reported separately.
In non-interactive shells, specify --agent or --dest. MinerU is required; use
--set-token after creating your own token. The old skill named paper-deep-read
is reported, but never modified automatically.
EOF
}

say()  { printf '  %s\n' "$*"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; }
bad()  { printf '  \033[31m✗\033[0m %s\n' "$*"; }
head_() { printf '\n\033[1m%s\033[0m\n' "$*"; }
die()  { printf '\033[31merror:\033[0m %s\n' "$*" >&2; exit 1; }

while [ $# -gt 0 ]; do
  case "$1" in
    --agent) [ $# -ge 2 ] || die "--agent needs claude, codex, both, or auto"; AGENT=$2; shift 2 ;;
    --agent=*) AGENT=${1#--agent=}; shift ;;
    --dest) [ $# -ge 2 ] || die "--dest needs a directory"; DEST=$2; shift 2 ;;
    --dest=*) DEST=${1#--dest=}; shift ;;
    --check) DO_CHECK=true; shift ;;
    --set-token) DO_SET_TOKEN=true; shift ;;
    --skip-deps) SKIP_DEPS=true; shift ;;
    --uninstall) DO_UNINSTALL=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; die "unknown option: $1" ;;
  esac
done

case "$AGENT" in
  claude|codex|both|auto) ;;
  *) die "--agent must be claude, codex, both, or auto" ;;
esac
[ -z "$DEST" ] || [ "$AGENT" = auto ] || die "--dest and --agent cannot be combined"
[ -f "$SOURCE_DIR/SKILL.md" ] || \
  die "run this from the repository root (expected $SOURCE_DIR/SKILL.md)"

# ---------------------------------------------------------------- token

set_token() {
  head_ "MinerU token"
  if [ ! -t 0 ]; then
    die "--set-token needs an interactive terminal"
  fi
  [ ! -L "$TOKEN_FILE" ] || die "refusing to write through a symlink: $TOKEN_FILE"
  if [ -f "$TOKEN_FILE" ]; then
    printf '  %s already exists. Overwrite? [y/N] ' "$TOKEN_FILE"
    read -r reply
    case "$reply" in
      y|Y|yes|YES) ;;
      *) say "kept the existing token"; return 0 ;;
    esac
  fi
  say "Create one at https://mineru.net/apiManage/token"
  say "(China-hosted; turn off any VPN/proxy to reach it.)"
  printf '  Paste your MinerU API token (input hidden): '
  read -r -s token
  printf '\n'
  token=$(printf '%s' "$token" | tr -d '\r\n')
  [ -n "$token" ] || die "empty token, nothing written"
  case "$token" in
    *[!A-Za-z0-9._~+/=-]*) die "token contains unsupported characters" ;;
  esac
  ( umask 077; printf '%s\n' "$token" > "$TOKEN_FILE" )
  chmod 600 "$TOKEN_FILE"
  ok "wrote $TOKEN_FILE (mode 600)"
  say "If MinerU later returns 401, create a fresh token and run this command again."
}

# ---------------------------------------------------------------- targets

# Print the skill roots to install into, one per line.
detect_targets() {
  if [ -n "$DEST" ]; then
    printf '%s\n' "$DEST"
    return 0
  fi
  case "$AGENT" in
    claude) printf '%s\n' "$CLAUDE_SKILLS"; return 0 ;;
    codex) printf '%s\n' "$CODEX_SKILLS"; return 0 ;;
    both) printf '%s\n%s\n' "$CLAUDE_SKILLS" "$CODEX_SKILLS"; return 0 ;;
  esac

  if [ ! -t 0 ]; then
    die "cannot determine the current agent in a non-interactive shell; pass --agent claude or --agent codex"
  fi
  printf 'Which agent are you using now? Choose one installation target.\n' >&2
  printf '  1) Claude Code   %s\n' "$CLAUDE_SKILLS" >&2
  printf '  2) Codex         %s\n' "$CODEX_SKILLS" >&2
  printf '  3) Both (optional)\n' >&2
  printf 'Choose 1, 2, or 3: ' >&2
  read -r choice
  case "$choice" in
    1) printf '%s\n' "$CLAUDE_SKILLS" ;;
    2) printf '%s\n' "$CODEX_SKILLS" ;;
    3) printf '%s\n%s\n' "$CLAUDE_SKILLS" "$CODEX_SKILLS" ;;
    *) die "choose 1, 2, or 3" ;;
  esac
}

install_to() {
  local root=$1
  local target="$root/$SKILL_NAME"
  local item
  mkdir -p "$target"
  for item in $MANAGED_DIRS; do
    rm -rf "$target/$item"
    if [ -d "$SOURCE_DIR/$item" ]; then
      cp -R "$SOURCE_DIR/$item" "$target/"
    fi
  done
  for item in $MANAGED_FILES; do
    rm -f "$target/$item"
    if [ -f "$SOURCE_DIR/$item" ]; then
      cp "$SOURCE_DIR/$item" "$target/"
    fi
  done
  find "$target" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
  find "$target" -name '*.pyc' -delete 2>/dev/null || true
  ok "installed to $target"
}

uninstall_from() {
  local root=$1
  local target="$root/$SKILL_NAME"
  if [ ! -d "$target" ]; then
    return 0
  fi
  # Only ever delete a directory that actually looks like this skill.
  if [ ! -f "$target/SKILL.md" ] && [ ! -d "$target/scripts" ]; then
    warn "skipped $target (does not look like the skill)"
    return 0
  fi
  rm -rf "$target"
  ok "removed $target"
}

# ---------------------------------------------------------------- python

resolve_python() {
  PYTHON=$(command -v python3 2>/dev/null || true)
  [ -n "$PYTHON" ] || die "python3 not found. Install Python 3.9 or newer, then re-run."
  if ! python_supported "$PYTHON"; then
    die "$PYTHON is older than Python 3.9. Install a newer Python, then re-run."
  fi
}

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

def pair(package):
    match = re.match(r"^(\d+)\.(\d+)", metadata.version(package))
    return tuple(map(int, match.groups())) if match else (0, 0)

ok = hasattr(fitz, "open") and hasattr(Image, "open")
ok = ok and (1, 23) <= pair("PyMuPDF") < (2, 0)
ok = ok and (9, 0) <= pair("Pillow") < (13, 0)
sys.exit(0 if ok else 1)
' >/dev/null 2>&1
}

# Install the complete pinned dependency set. Plain `python3 <skill>/scripts/x.py`
# uses the private venv through scripts/_pymupdf.py when global deps are absent.
ensure_deps() {
  head_ "Python dependencies"
  resolve_python
  say "interpreter: $PYTHON"

  if has_deps "$PYTHON"; then
    ok "PyMuPDF and Pillow importable at supported versions"
    return 0
  fi

  say "PyMuPDF or Pillow missing/unsupported, installing..."
  if "$PYTHON" -m pip install -r "$SOURCE_DIR/requirements.txt" >/dev/null 2>&1 && has_deps "$PYTHON"; then
    ok "installed with pip"
    return 0
  fi
  if "$PYTHON" -m pip install --user -r "$SOURCE_DIR/requirements.txt" >/dev/null 2>&1 && has_deps "$PYTHON"; then
    ok "installed with pip --user"
    return 0
  fi

  # PEP 668, permission errors, or an incompatible shared interpreter can all
  # require a private venv. Verify each installed agent independently.
  warn "could not use the current Python environment; trying private virtualenvs"
  deps_ok=true
  saved_ifs=$IFS
  IFS=$'\n'
  for root in $TARGETS; do
    IFS=$saved_ifs
    target="$root/$SKILL_NAME"
    venv="$target/.venv"
    if [ ! -x "$venv/bin/python3" ]; then
      if ! "$PYTHON" -m venv "$venv" 2>/dev/null; then
        bad "could not create $venv"
        say "On Debian/Ubuntu install the venv module first: sudo apt install python3-venv"
        deps_ok=false
        continue
      fi
    fi
    "$venv/bin/python3" -m pip install --quiet --upgrade pip >/dev/null 2>&1 || true
    if "$venv/bin/python3" -m pip install --quiet -r "$SOURCE_DIR/requirements.txt" && has_deps "$venv/bin/python3"; then
      ok "installed into $venv"
    else
      bad "failed to install PyMuPDF and Pillow into $venv"
      deps_ok=false
    fi
    IFS=$'\n'
  done
  IFS=$saved_ifs
  if [ "$deps_ok" != true ]; then
    die "could not install Python dependencies for every target. See README.md."
  fi
}

# ---------------------------------------------------------------- status

status_targets() {
  if [ -n "$DEST" ]; then
    printf '%s\n' "$DEST"
    return 0
  fi
  case "$AGENT" in
    claude) printf '%s\n' "$CLAUDE_SKILLS" ;;
    codex) printf '%s\n' "$CODEX_SKILLS" ;;
    both) printf '%s\n%s\n' "$CLAUDE_SKILLS" "$CODEX_SKILLS" ;;
    auto) detect_targets ;;
  esac
}

legacy_status() {
  local root item
  for root in "$CLAUDE_SKILLS" "$CODEX_SKILLS" "$HOME/.agents/skills"; do
    for item in "$LEGACY_SKILL_NAME"; do
      if [ -f "$root/$item/SKILL.md" ]; then
        warn "older skill still present: $root/$item"
      fi
    done
  done
  say "Older copies named paper-deep-read are never moved or deleted automatically."
}

status() {
  local roots=$1
  local root saved_ifs status_output status_code
  local check_args=()
  saved_ifs=$IFS
  IFS=$'\n'
  for root in $roots; do
    IFS=$saved_ifs
    check_args+=(--skill-dir "$root/$SKILL_NAME")
    IFS=$'\n'
  done
  IFS=$saved_ifs

  if status_output=$(bash "$SOURCE_DIR/scripts/check_setup.sh" "${check_args[@]}"); then
    status_code=0
  else
    status_code=$?
  fi
  printf '%s\n' "$status_output"
  case "$status_output" in
    *"Feishu publishing is ready"*) FEISHU_READY=true ;;
    *) FEISHU_READY=false ;;
  esac

  head_ "Older installations"
  legacy_status
  return "$status_code"
}

# ---------------------------------------------------------------- main

if [ "$DO_SET_TOKEN" = true ]; then
  set_token
  if [ "$DO_CHECK" = true ]; then
    status "$(status_targets)"
  fi
  exit 0
fi

if [ "$DO_UNINSTALL" = true ]; then
  head_ "Uninstall"
  TARGETS=$(status_targets)
  saved_ifs=$IFS
  IFS=$'\n'
  for root in $TARGETS; do
    IFS=$saved_ifs
    uninstall_from "$root"
    IFS=$'\n'
  done
  IFS=$saved_ifs
  say "~/.mineru_token was left in place; delete it yourself if you want it gone."
  legacy_status
  exit 0
fi

if [ "$DO_CHECK" = true ]; then
  status "$(status_targets)"
  exit $?
fi

TARGETS=$(detect_targets)
[ -n "$TARGETS" ] || die "no install target resolved"

head_ "Installing $SKILL_NAME"
saved_ifs=$IFS
IFS=$'\n'
for root in $TARGETS; do
  IFS=$saved_ifs
  install_to "$root"
  IFS=$'\n'
done
IFS=$saved_ifs

if [ "$SKIP_DEPS" = true ]; then
  head_ "Python dependency"
  say "skipped (--skip-deps)"
else
  ensure_deps
fi

if status "$TARGETS"; then
  ok "Paper-reading core is ready; Feishu publishing status is reported separately."
else
  warn "Skill files were installed, but required setup is incomplete. Follow the red status items above."
fi

head_ "Next"
say "1. Restart your agent, then check that the skill is listed."
say "2. If MinerU is missing, create a token and run: bash install.sh --set-token"
say "3. Ask it to deep-read a paper, for example:"
say "     用 embodied-paper-deep-read 精读这篇论文：https://arxiv.org/abs/2503.20020"
if [ "$FEISHU_READY" = true ]; then
  say "4. Feishu CLI and authorization are ready; no installation needed."
else
  say "4. For Feishu publishing, follow the Feishu status instructions above in the current Agent."
fi
printf '\n'
