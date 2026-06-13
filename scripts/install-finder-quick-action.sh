#!/usr/bin/env bash
set -euo pipefail

# Installs a lightweight Finder Quick Action helper script. macOS Services/Shortcuts
# still need to be connected by the user in Shortcuts.app or Automator, but this
# script provides the stable executable target.

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/opensiri-finder-selection" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "$ROOT"
PYTHONPATH=src .venv/bin/eliot-harness --enable-files --files-root "\$PWD" --live-ax --task "Summarize or compare the Finder-selected files."
EOF
chmod +x "$BIN_DIR/opensiri-finder-selection"
echo "Installed: $BIN_DIR/opensiri-finder-selection"
echo "Next: create a Finder Quick Action in Shortcuts.app or Automator that runs this script."
