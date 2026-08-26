#!/usr/bin/env bash
# Installer for the Embodied Paper Deep Read skill.
# Detects Claude Code / Codex skill directories, copies the skill, and resolves
# the Python dependency so that `python3 <skill-dir>/scripts/...` works afterwards.
set -euo pipefail

SKILL_NAME="embodied-paper-deep-read"
REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SOURCE_DIR="$REPO_ROOT/$SKILL_NAME"

CLAUDE_SKILLS="$HOME/.claude/skills"
CODEX_SKILLS="$HOME/.agents/skills"
TOKEN_FILE="$HOME/.mineru_token"

# Directory contents this installer owns. Anything else in the target (a .venv,
# user edits) is left alone.
MANAGED_DIRS="scripts references publishers agents"
MANAGED_FILES="SKILL.md LICENSE requirements.txt requirements-dev.txt"

DEST=""
DO_CHECK=false
DO_SET_TOKEN=false
DO_UNINSTALL=false
SKIP_DEPS=false
PYTHON=""

usage() {
  cat <<'EOF'
Usage: bash install.sh [options]

Options:
  --dest DIR      Install into DIR instead of the auto-detected skills directories
  --check         Report installation status only, change nothing
  --set-token     Store a MinerU API token in ~/.mineru_token (mode 600)
  --skip-deps     Copy the skill but do not touch Python dependencies
  --uninstall     Remove the installed skill (leaves ~/.mineru_token alone)
  -h, --help      Show this help

With no options: detect the skill directories of Claude Code (~/.claude/skills)
and Codex (~/.agents/skills), install into the ones that exist, resolve the
PyMuPDF dependency, then print a status summary.
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

[ -f "$SOURCE_DIR/SKILL.md" ] || \
  die "run this from the repository root (expected $SOURCE_DIR/SKILL.md)"

# ---------------------------------------------------------------- token

set_token() {
  head_ "MinerU token"
  if [ ! -t 0 ]; then
    die "--set-token needs an interactive terminal"
  fi
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
  say "Tokens last 90 days; re-run this command when MinerU returns 401."
}

# ---------------------------------------------------------------- targets

# Print the skill roots to install into, one per line.
detect_targets() {
  if [ -n "$DEST" ]; then
    printf '%s\n' "$DEST"
    return 0
  fi
  found=""
  if [ -d "$CLAUDE_SKILLS" ]; then
    found="$found$CLAUDE_SKILLS
"
  fi
  if [ -d "$CODEX_SKILLS" ]; then
    found="$found$CODEX_SKILLS
"
  fi
  if [ -n "$found" ]; then
    printf '%s' "$found"
    return 0
  fi
  if [ ! -t 0 ]; then
    printf '%s\n%s\n' "$CLAUDE_SKILLS" "$CODEX_SKILLS"
    return 0
  fi
  printf 'No agent skills directory found yet. Where should the skill go?\n' >&2
  printf '  1) Claude Code   %s\n' "$CLAUDE_SKILLS" >&2
  printf '  2) Codex         %s\n' "$CODEX_SKILLS" >&2
  printf '  3) Both (default)\n' >&2
  printf 'Choose [3]: ' >&2
  read -r choice
  case "$choice" in
    1) printf '%s\n' "$CLAUDE_SKILLS" ;;
    2) printf '%s\n' "$CODEX_SKILLS" ;;
    *) printf '%s\n%s\n' "$CLAUDE_SKILLS" "$CODEX_SKILLS" ;;
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
  if ! "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
    die "$PYTHON is older than Python 3.9. Install a newer Python, then re-run."
  fi
}

has_pymupdf() {
  "$1" -c 'import fitz' >/dev/null 2>&1
}

# Install PyMuPDF so that a plain `python3 <skill>/scripts/x.py` can import it.
# Ladder: already importable -> pip -> pip --user -> private venv per install.
ensure_deps() {
  head_ "Python dependency"
  resolve_python
  say "interpreter: $PYTHON"

  if has_pymupdf "$PYTHON"; then
    ok "PyMuPDF $("$PYTHON" -c 'import fitz; print(fitz.__doc__.split()[1].rstrip(":"))' 2>/dev/null || echo present)"
    return 0
  fi

  say "PyMuPDF missing, installing..."
  if "$PYTHON" -m pip install -r "$SOURCE_DIR/requirements.txt" 2>/dev/null && has_pymupdf "$PYTHON"; then
    ok "installed with pip"
    return 0
  fi
  if "$PYTHON" -m pip install --user -r "$SOURCE_DIR/requirements.txt" 2>/dev/null && has_pymupdf "$PYTHON"; then
    ok "installed with pip --user"
    return 0
  fi

  # PEP 668 externally-managed interpreter: fall back to a venv the scripts
  # re-exec into by themselves (see scripts/_pymupdf.py).
  warn "this interpreter is externally managed, using a private virtualenv instead"
  deps_ok=false
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
        continue
      fi
    fi
    "$venv/bin/python3" -m pip install --quiet --upgrade pip >/dev/null 2>&1 || true
    if "$venv/bin/python3" -m pip install --quiet -r "$SOURCE_DIR/requirements.txt" && has_pymupdf "$venv/bin/python3"; then
      ok "installed into $venv"
      deps_ok=true
    else
      bad "failed to install PyMuPDF into $venv"
    fi
    IFS=$'\n'
  done
  IFS=$saved_ifs
  if [ "$deps_ok" != true ]; then
    die "could not install PyMuPDF. See the troubleshooting table in README.md."
  fi
}

# ---------------------------------------------------------------- status

status() {
  head_ "Status"

  installed=""
  for root in "$CLAUDE_SKILLS" "$CODEX_SKILLS" ${DEST:+"$DEST"}; do
    if [ -f "$root/$SKILL_NAME/SKILL.md" ]; then
      ok "skill installed: $root/$SKILL_NAME"
      installed="yes"
    fi
  done
  if [ -z "$installed" ]; then
    bad "skill not installed anywhere yet — run: bash install.sh"
  fi

  py=$(command -v python3 2>/dev/null || true)
  if [ -z "$py" ]; then
    bad "python3 not found"
  elif has_pymupdf "$py"; then
    say "python3: $py"
    ok "PyMuPDF importable"
  else
    say "python3: $py"
    venv_hit=""
    for root in "$CLAUDE_SKILLS" "$CODEX_SKILLS" ${DEST:+"$DEST"}; do
      if [ -x "$root/$SKILL_NAME/.venv/bin/python3" ]; then
        venv_hit="$root/$SKILL_NAME/.venv"
      fi
    done
    if [ -n "$venv_hit" ]; then
      ok "PyMuPDF in private virtualenv ($venv_hit); scripts re-exec into it automatically"
    else
      bad "PyMuPDF not importable — run: bash install.sh"
    fi
  fi

  if [ -n "${MINERU_TOKEN:-}" ]; then
    ok "MinerU token: MINERU_TOKEN is set in this shell"
  elif [ -f "$TOKEN_FILE" ]; then
    ok "MinerU token: $TOKEN_FILE"
  else
    warn "MinerU token: not configured (optional) — run: bash install.sh --set-token"
  fi

  if command -v lark-cli >/dev/null 2>&1; then
    ok "lark-cli: $(command -v lark-cli)"
  else
    warn "lark-cli: not installed (only needed to publish to Feishu)"
    say "  ask your agent: 帮我配置飞书发布"
  fi
}

# ---------------------------------------------------------------- main

if [ "$DO_SET_TOKEN" = true ]; then
  set_token
  if [ "$DO_CHECK" = true ]; then
    status
  fi
  exit 0
fi

if [ "$DO_UNINSTALL" = true ]; then
  head_ "Uninstall"
  if [ -n "$DEST" ]; then
    uninstall_from "$DEST"
  else
    uninstall_from "$CLAUDE_SKILLS"
    uninstall_from "$CODEX_SKILLS"
  fi
  say "~/.mineru_token was left in place; delete it yourself if you want it gone."
  exit 0
fi

if [ "$DO_CHECK" = true ]; then
  status
  exit 0
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

status

head_ "Next"
say "1. Restart your agent, then check that the skill is listed."
say "2. Ask it to deep-read a paper, for example:"
say "     用 embodied-paper-deep-read 精读这篇论文：https://arxiv.org/abs/2503.20020"
say "3. Optional setup (MinerU token, Feishu publishing): see README.md"
printf '\n'
