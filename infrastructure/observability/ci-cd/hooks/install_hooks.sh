#!/bin/bash
GIT_DIR=$(git rev-parse --git-dir)
TEMPLATES_DIR="$(dirname "$0")/templates"
for hook in pre-commit commit-msg pre-push prepare-commit-msg; do
    target="$GIT_DIR/hooks/$hook"
    template="$TEMPLATES_DIR/$hook"
    if [ ! -f "$target" ]; then
        echo "#!/bin/bash" > "$target"
        chmod +x "$target"
    fi
    marker="### OBSERVABILITY_${hook^^} ###"
    if ! grep -q "$marker" "$target"; then
        echo "" >> "$target"
        echo "$marker" >> "$target"
        cat "$template" | grep -v "^#!/bin/bash" >> "$target"
        echo "$marker" >> "$target"
    fi
done
