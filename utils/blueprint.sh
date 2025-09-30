#!/usr/bin/env bash
# Usage: ./generate_blueprint.sh config.conf
set -euo pipefail

CONF_FILE="${1:-}"
[ -z "$CONF_FILE" ] && { echo "Usage: $0 config.conf"; exit 1; }
[ ! -f "$CONF_FILE" ] && { echo "Config not found: $CONF_FILE"; exit 1; }

# Load config
source "$CONF_FILE"

[ -d "$INPUT_DIR" ] || { echo "No such dir: $INPUT_DIR"; exit 1; }
[ -f "$IGNORE_FILE" ] || { echo "No such ignore file: $IGNORE_FILE"; exit 1; }

mapfile -t RAW_IGNORES < <(sed -E 's/\r$//' "$IGNORE_FILE")
IGNORES=()
for line in "${RAW_IGNORES[@]}"; do
  [[ -n "$line" && ! "$line" =~ ^[[:space:]]*# ]] && IGNORES+=("$line")
done

should_ignore() {
  local p="${1#./}"
  for pat in "${IGNORES[@]}"; do
    case "$p" in $pat|$pat/*|*/$pat|*/$pat/*) return 0;; esac
  done
  return 1
}

is_text_file() {
  local f="$1"
  if command -v file >/dev/null 2>&1; then
    [[ "$(file -b --mime-encoding -- "$f" || true)" != "binary" ]]
  else
    ! LC_ALL=C grep -qU $'\000' -- "$f"
  fi
}

PROJECT_NAME="$(basename "$INPUT_DIR")"

cat > "$OUTPUT_FILE" <<EOF
#!/usr/bin/env bash
set -euo pipefail
PROJECT="$PROJECT_NAME"
mkdir -p "\$PROJECT"
cd "\$PROJECT"
EOF

(
  cd "$INPUT_DIR"
  find . -type d -print0 | while IFS= read -r -d '' d; do
    [[ "$d" == "." ]] && continue
    if ! should_ignore "$d"; then
      rel="${d#./}"
      printf 'mkdir -p "%s/%s"\n' "\$PROJECT" "${rel//\"/\\\"}"
    fi
  done
) >> "$OUTPUT_FILE"

(
  cd "$INPUT_DIR"
  find . -type l -print0 | while IFS= read -r -d '' l; do
    if ! should_ignore "$l"; then
      rel="${l#./}"; tgt="$(readlink -- "$l")"
      printf 'ln -s "%s" "%s/%s"\n' "${tgt//\"/\\\"}" "\$PROJECT" "${rel//\"/\\\"}"
    fi
  done
) >> "$OUTPUT_FILE"

(
  cd "$INPUT_DIR"
  find . -type f -print0 | while IFS= read -r -d '' f; do
    [[ -L "$f" ]] && continue
    if ! should_ignore "$f"; then
      rel="${f#./}"
      if is_text_file "$f"; then
        printf 'cat > "%s/%s" <<'"'"'EOF'"'"'\n' "\$PROJECT" "${rel//\"/\\\"}"
        cat -- "$f"
        printf '\nEOF\n'
      else
        printf 'base64 -d > "%s/%s" <<'"'"'B64'"'"'\n' "\$PROJECT" "${rel//\"/\\\"}"
        base64 -w 0 -- "$f"; printf '\nB64\n'
      fi
      [[ -x "$f" ]] && printf 'chmod +x "%s/%s"\n' "\$PROJECT" "${rel//\"/\\\"}"
      printf '\n'
    fi
  done
) >> "$OUTPUT_FILE"

chmod +x "$OUTPUT_FILE"
echo "==> Blueprint created: $OUTPUT_FILE"
