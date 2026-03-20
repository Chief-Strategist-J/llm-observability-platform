#!/bin/bash

HOOK_FILE=".git/hooks/pre-commit"
cat <<EOF > "$HOOK_FILE"
#!/bin/bash
python3 -m flake8 infrastructure/observability
EOF

chmod +x "$HOOK_FILE"
