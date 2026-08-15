#!/usr/bin/env bash
set -euo pipefail
umask 077

usage() {
  printf 'Usage: %s /path/to/file.pdf [output_dir]\n' "$(basename "$0")"
  printf '\nRequired environment:\n'
  printf '  MINERU_TOKEN            Token created by the user on mineru.net\n'
  printf '\nOptional environment:\n'
  printf '  MINERU_LANGUAGE         Auto-detected when unset\n'
  printf '  MINERU_IS_OCR           true/false, default false\n'
  printf '  MINERU_MODEL_VERSION    vlm/pipeline, default vlm\n'
  printf '  MINERU_PAGE_RANGES      Example: 1-10 or 2,4-6\n'
  printf '  MINERU_TIMEOUT_SECONDS  Polling timeout, default 1800\n'
  printf '  MINERU_POLL_SECONDS     Polling interval, default 5\n'
  printf '  MINERU_REFRESH          true to replace managed full.md/images\n'
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi
if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage >&2
  exit 2
fi

PDF_PATH=$1
OUT_DIR=${2:-mineru_result}
WORK_DIR=${OUT_DIR%/}
[[ -n "$WORK_DIR" ]] || WORK_DIR=/

if [[ ! -f "$PDF_PATH" ]]; then
  printf 'PDF not found: %s\n' "$PDF_PATH" >&2
  exit 1
fi
if [[ -z "${MINERU_TOKEN:-}" ]]; then
  printf 'MINERU_TOKEN is not set. Create a token in your MinerU account and export it securely.\n' >&2
  printf 'Official API documentation: https://mineru.net/doc/docs/index_en/\n' >&2
  printf 'See this repository README. Do not paste the token into chat or commit it.\n' >&2
  exit 2
fi
case "$MINERU_TOKEN" in
  *$'\n'*|*$'\r'*) printf 'MINERU_TOKEN must not contain newlines\n' >&2; exit 2 ;;
  *[!A-Za-z0-9._~+/=-]*) printf 'MINERU_TOKEN contains unsupported characters\n' >&2; exit 2 ;;
esac

for cmd in curl python3; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    printf 'Missing command: %s\n' "$cmd" >&2
    exit 1
  fi
done

IS_OCR=${MINERU_IS_OCR:-false}
MODEL_VERSION=${MINERU_MODEL_VERSION:-vlm}
PAGE_RANGES=${MINERU_PAGE_RANGES:-}
TIMEOUT_SECONDS=${MINERU_TIMEOUT_SECONDS:-1800}
POLL_SECONDS=${MINERU_POLL_SECONDS:-5}
REFRESH=${MINERU_REFRESH:-false}

case "$IS_OCR" in true|false) ;; *) printf 'MINERU_IS_OCR must be true or false\n' >&2; exit 2 ;; esac
case "$REFRESH" in true|false) ;; *) printf 'MINERU_REFRESH must be true or false\n' >&2; exit 2 ;; esac
case "$MODEL_VERSION" in vlm|pipeline) ;; *) printf 'MINERU_MODEL_VERSION must be vlm or pipeline\n' >&2; exit 2 ;; esac
case "$TIMEOUT_SECONDS" in ''|*[!0-9]*) printf 'MINERU_TIMEOUT_SECONDS must be a positive integer\n' >&2; exit 2 ;; esac
case "$POLL_SECONDS" in ''|*[!0-9]*) printf 'MINERU_POLL_SECONDS must be a positive integer\n' >&2; exit 2 ;; esac
if [[ "$TIMEOUT_SECONDS" -le 0 || "$POLL_SECONDS" -le 0 ]]; then
  printf 'Timeout and polling interval must be greater than zero\n' >&2
  exit 2
fi

MARKER_PATH="$WORK_DIR/.embodied-paper-deep-read-mineru"
if [[ -f "$WORK_DIR/full.md" && -f "$MARKER_PATH" && "$REFRESH" != "true" ]]; then
  printf 'Using existing MinerU result: %s/full.md\n' "$WORK_DIR"
  exit 0
fi
if [[ -d "$WORK_DIR" && ! -f "$MARKER_PATH" ]]; then
  if find "$WORK_DIR" -mindepth 1 -maxdepth 1 -print -quit | grep -q .; then
    printf 'Refusing to write into a non-empty unmanaged directory: %s\n' "$WORK_DIR" >&2
    printf 'Choose an empty output directory, normally <paper-folder>/mineru.\n' >&2
    exit 2
  fi
fi

PDF_BYTES=$(python3 - "$PDF_PATH" <<'PY'
import os, sys
print(os.path.getsize(sys.argv[1]))
PY
)
if [[ "$PDF_BYTES" -gt 209715200 ]]; then
  printf 'PDF exceeds the MinerU Precision Extract API limit of 200 MB\n' >&2
  exit 2
fi

detect_language() {
  command -v pdftotext >/dev/null 2>&1 || { printf 'en\n'; return; }
  pdftotext -f 1 -l 3 -q "$PDF_PATH" - 2>/dev/null | python3 -c '
import sys
text = sys.stdin.read()
cjk = sum(1 for c in text if "一" <= c <= "鿿")
latin = sum(1 for c in text if c.isascii() and c.isalpha())
print("ch" if cjk > max(20, latin * 0.1) else "en")
' 2>/dev/null || printf 'en\n'
}

if [[ -n "${MINERU_LANGUAGE:-}" ]]; then
  LANGUAGE=$MINERU_LANGUAGE
else
  LANGUAGE=$(detect_language)
  printf 'Auto-detected document language: %s\n' "$LANGUAGE"
fi

TASK_DIR=$(mktemp -d "${TMPDIR:-/tmp}/embodied-paper-deep-read-mineru.XXXXXX")
trap 'rm -rf "$TASK_DIR"' EXIT INT TERM
ZIP_PATH="$TASK_DIR/mineru_result.zip"
EXTRACT_DIR="$TASK_DIR/extracted"
AUTH_CONFIG="$TASK_DIR/curl-auth.conf"
FILE_NAME=$(basename "$PDF_PATH")
CURL_ARGS=(--silent --show-error --fail --location --retry 3 --retry-delay 2 --connect-timeout 15)
printf 'header = "Authorization: Bearer %s"\n' "$MINERU_TOKEN" > "$AUTH_CONFIG"
unset MINERU_TOKEN

REQUEST_JSON=$(python3 - "$FILE_NAME" "$LANGUAGE" "$IS_OCR" "$PAGE_RANGES" "$MODEL_VERSION" <<'PY'
import hashlib, json, re, sys
file_name, language, is_ocr, page_ranges, model_version = sys.argv[1:6]
stem = re.sub(r"[^A-Za-z0-9._-]+", "_", file_name).strip("._-") or "paper"
suffix = hashlib.sha256(file_name.encode("utf-8")).hexdigest()[:10]
data_id = f"{stem[:100]}-{suffix}"
item = {"name": file_name, "data_id": data_id, "is_ocr": is_ocr == "true"}
if page_ranges:
    item["page_ranges"] = page_ranges
print(json.dumps({
    "files": [item],
    "model_version": model_version,
    "enable_table": True,
    "enable_formula": True,
    "language": language,
}, ensure_ascii=False))
PY
)

printf 'Creating MinerU extraction task for %s...\n' "$FILE_NAME"
CREATE_RES=$(curl "${CURL_ARGS[@]}" --config "$AUTH_CONFIG" \
  --request POST 'https://mineru.net/api/v4/file-urls/batch' \
  --header 'Content-Type: application/json' \
  --data-raw "$REQUEST_JSON")

PARSED_CREATE=$(printf '%s' "$CREATE_RES" | python3 -c '
import json, sys
res = json.load(sys.stdin)
if res.get("code") != 0:
    message, code = res.get("msg"), res.get("code")
    raise SystemExit(f"Failed to create task: {message} ({code})")
data = res.get("data") or {}
print(data.get("batch_id", ""))
print((data.get("file_urls") or [""])[0])
')
BATCH_ID=$(printf '%s\n' "$PARSED_CREATE" | sed -n '1p')
UPLOAD_URL=$(printf '%s\n' "$PARSED_CREATE" | sed -n '2p')
if [[ -z "$BATCH_ID" || -z "$UPLOAD_URL" ]]; then
  printf 'MinerU response did not include batch_id and upload URL\n' >&2
  exit 1
fi

printf 'Uploading PDF to MinerU...\n'
curl "${CURL_ARGS[@]}" --request PUT --upload-file "$PDF_PATH" "$UPLOAD_URL" >/dev/null

START_TIME=$(date +%s)
printf 'Polling extraction result'
while true; do
  NOW=$(date +%s)
  if [[ $((NOW - START_TIME)) -ge "$TIMEOUT_SECONDS" ]]; then
    printf '\nMinerU extraction timed out after %s seconds (batch %s).\n' "$TIMEOUT_SECONDS" "$BATCH_ID" >&2
    exit 1
  fi
  sleep "$POLL_SECONDS"
  printf '.'
  if ! RES=$(curl "${CURL_ARGS[@]}" --request GET \
    "https://mineru.net/api/v4/extract-results/batch/${BATCH_ID}" \
    --config "$AUTH_CONFIG"); then
    printf 'retrying'
    continue
  fi

  STATE_AND_URL=$(printf '%s' "$RES" | python3 -c '
import json, sys
res = json.load(sys.stdin)
if res.get("code") != 0:
    message, code = res.get("msg"), res.get("code")
    raise SystemExit(f"query failed: {message} ({code})")
items = (res.get("data") or {}).get("extract_result") or []
if not items:
    print("waiting-file")
    print("")
else:
    print(items[0].get("state", "unknown"))
    print(items[0].get("full_zip_url", ""))
')
  STATE=$(printf '%s\n' "$STATE_AND_URL" | sed -n '1p')
  ZIP_URL=$(printf '%s\n' "$STATE_AND_URL" | sed -n '2p')

  if [[ "$STATE" == "done" ]]; then
    printf '\n'
    [[ -n "$ZIP_URL" ]] || { printf 'Completed task did not include a result URL\n' >&2; exit 1; }
    printf 'Downloading MinerU result...\n'
    curl "${CURL_ARGS[@]}" --max-time 1800 "$ZIP_URL" --output "$ZIP_PATH"
    break
  fi
  if [[ "$STATE" == "failed" ]]; then
    printf '\nMinerU extraction failed (batch %s).\n' "$BATCH_ID" >&2
    exit 1
  fi
done

mkdir -p "$EXTRACT_DIR" "$WORK_DIR"
python3 - "$ZIP_PATH" "$EXTRACT_DIR" "$WORK_DIR" <<'PY'
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import tempfile
import zipfile

zip_path, extract_dir, output_dir = map(Path, sys.argv[1:4])
with zipfile.ZipFile(zip_path) as archive:
    for info in archive.infolist():
        path = PurePosixPath(info.filename.replace("\\", "/"))
        mode = (info.external_attr >> 16) & 0o170000
        if path.is_absolute() or ".." in path.parts or mode == stat.S_IFLNK:
            raise SystemExit(f"unsafe path in MinerU zip: {info.filename}")
    archive.extractall(extract_dir)

candidates = list(extract_dir.rglob("full.md"))
if len(candidates) != 1:
    raise SystemExit(f"expected exactly one full.md in MinerU zip, found {len(candidates)}")
source_root = candidates[0].parent
source_images = source_root / "images"
if not source_images.is_dir():
    source_images.mkdir()

output_dir.mkdir(parents=True, exist_ok=True)
marker = output_dir / ".embodied-paper-deep-read-mineru"
unmanaged = [p for p in output_dir.iterdir() if p.name not in {"full.md", "images", marker.name}]
if unmanaged and not marker.exists():
    raise SystemExit(f"refusing to modify unmanaged output directory: {output_dir}")

stage = Path(tempfile.mkdtemp(prefix=".install-", dir=output_dir))
backup = output_dir / ".images-backup"
try:
    shutil.copy2(candidates[0], stage / "full.md")
    shutil.copytree(source_images, stage / "images")
    os.replace(stage / "full.md", output_dir / "full.md")
    if backup.exists():
        shutil.rmtree(backup)
    if (output_dir / "images").exists():
        os.replace(output_dir / "images", backup)
    try:
        os.replace(stage / "images", output_dir / "images")
    except Exception:
        if backup.exists():
            os.replace(backup, output_dir / "images")
        raise
    if backup.exists():
        shutil.rmtree(backup)
    marker.write_text("managed by embodied-paper-deep-read\n", encoding="utf-8")
finally:
    shutil.rmtree(stage, ignore_errors=True)
PY

printf 'Done. Output directory: %s\n' "$WORK_DIR"
printf 'Kept only managed full.md and images/; temporary API responses were removed.\n'
