#!/bin/bash
# Install script for pylow to fetch the Docker wrapper automatically
# Usage: curl -sSL https://raw.githubusercontent.com/username/pylow/main/install.sh | bash

set -e

echo "📦 Installing pylow CLI..."

# 1. Download or write wrapper script
WRAPPER_PATH="/usr/local/bin/pylow"

sudo bash -c "cat << 'EOF' > $WRAPPER_PATH
#!/bin/bash
# Wrapper to run pylow container with appropriate permissions for eBPF/USDT
docker run --rm -it \\
  --privileged \\
  --pid=host \\
  --net=host \\
  -v /sys/kernel/debug:/sys/kernel/debug:rw \\
  -v /lib/modules:/lib/modules:ro \\
  -v /usr/src:/usr/src:ro \\
  -v /var/run/docker.sock:/var/run/docker.sock \\
  -v \$(pwd):\$(pwd) \\
  -w \$(pwd) \\
  pylow:latest \"\$@\"
EOF"

sudo chmod +x $WRAPPER_PATH

echo "✓ Installed wrapper at $WRAPPER_PATH"
echo "You can now run 'pylow' commands directly!"
