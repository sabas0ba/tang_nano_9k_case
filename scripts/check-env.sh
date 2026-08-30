#!/usr/bin/env bash
set -euo pipefail

required_commands=(bash git make pdfinfo pdftoppm python3 rg)
store_dir=${NIX_STORE_DIR:-/nix/store}
failed=0

for command_name in "${required_commands[@]}"; do
  if ! command_path=$(command -v "$command_name" 2>/dev/null); then
    printf 'MISSING %s\n' "$command_name" >&2
    failed=1
    continue
  fi
  resolved_path=$(realpath -e "$command_path")
  case "$resolved_path" in
    "$store_dir"/*) printf 'ok %-8s %s\n' "$command_name" "$resolved_path" ;;
    *)
      printf 'FOREIGN %-8s %s\n' "$command_name" "$resolved_path" >&2
      failed=1
      ;;
  esac
done

if [ "${CASE_ENV:-}" != nix-develop ]; then
  echo "CASE_ENV is not set by the Nix development shell" >&2
  failed=1
fi

if [ ! -f "${DEJAVU_FONT_PATH:-}" ]; then
  echo "DEJAVU_FONT_PATH does not identify a readable font" >&2
  failed=1
fi

if [ ! -f "${FONTCONFIG_FILE:-}" ]; then
  echo "FONTCONFIG_FILE does not identify a readable configuration" >&2
  failed=1
fi

python3 - <<'PY'
import matplotlib
import numpy
import PIL
import reportlab

print(
    "python dependencies:",
    f"numpy={numpy.__version__}",
    f"matplotlib={matplotlib.__version__}",
    f"reportlab={reportlab.Version}",
    f"pillow={PIL.__version__}",
)
PY

exit "$failed"
