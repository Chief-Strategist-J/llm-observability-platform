#!/usr/bin/env bash
# Audits all bash scripts in the repository for:
# 1. Valid shebang (#!/bin/bash, #!/bin/sh, or #!/usr/bin/env bash)
# 2. Executable permission (+x)
# 3. Presence of safety settings (set -e or set -euo pipefail)
# 4. Basic syntax check (bash -n)

set -euo pipefail

# Get repository root (directory of this script is <root>/scripts)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔍 Running Bash Script Audit..."
echo "Repository Root: $REPO_ROOT"
echo "=================================================="

FAILED=0

# Find all .sh files, excluding node_modules, .git, etc.
while IFS= read -r file; do
    # Relative path for display
    rel_path="${file#"$REPO_ROOT/"}"
    
    echo "Checking: $rel_path"
    
    # 1. Check if executable
    if [ ! -x "$file" ]; then
        echo "   ❌ ERROR: File is not executable. Run 'chmod +x $rel_path'"
        FAILED=1
    fi
    
    # 2. Check shebang
    first_line=$(head -n 1 "$file")
    if [[ ! "$first_line" =~ ^#\!/bin/(bash|sh) ]] && [[ ! "$first_line" =~ ^#\!/usr/bin/env\ (bash|sh) ]]; then
        echo "   ❌ ERROR: Missing or invalid shebang: '$first_line'"
        FAILED=1
    fi
    
    # 3. Check syntax
    if ! bash -n "$file" 2>/dev/null; then
        echo "   ❌ ERROR: Syntax validation failed (bash -n)"
        FAILED=1
    fi
    
    # 4. Check for safety flags (set -e, set -euo pipefail, etc.)
    if ! grep -qE "set -[a-z]*e" "$file"; then
        echo "   ⚠️  WARNING: Script does not set fail-on-error flag ('set -e')"
    fi
    
done < <(find "$REPO_ROOT" -type f -name "*.sh" -not -path "*/.git/*" -not -path "*/node_modules/*")

echo "=================================================="
if [ "$FAILED" -eq 0 ]; then
    echo "✅ Bash script audit completed successfully. All scripts comply!"
    exit 0
else
    echo "❌ Bash script audit failed. Please fix the errors listed above."
    exit 1
fi
