#!/usr/bin/env bash
set -euo pipefail

# Installs a lightweight Finder Quick Action service plus stable executable target.

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
SERVICES_DIR="$HOME/Library/Services/OpenSiri AI.workflow/Contents"
mkdir -p "$SERVICES_DIR"
cat > "$SERVICES_DIR/document.wflow" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>actions</key>
  <array>
    <dict>
      <key>action</key>
      <dict>
        <key>AMAccepts</key>
        <dict>
          <key>Container</key><string>List</string>
          <key>Optional</key><true/>
          <key>Types</key><array><string>com.apple.cocoa.path</string></array>
        </dict>
        <key>AMApplication</key><array><string>Automator</string></array>
        <key>AMParameterProperties</key><dict/>
        <key>AMProvides</key><dict/>
        <key>ActionBundlePath</key><string>/System/Library/Automator/Run Shell Script.action</string>
        <key>ActionName</key><string>Run Shell Script</string>
        <key>ActionParameters</key>
        <dict>
          <key>COMMAND_STRING</key><string>"$BIN_DIR/opensiri-finder-selection" "\$@"</string>
          <key>CheckedForUserDefaultShell</key><true/>
          <key>inputMethod</key><integer>1</integer>
          <key>shell</key><string>/bin/bash</string>
          <key>source</key><string></string>
        </dict>
        <key>BundleIdentifier</key><string>com.apple.RunShellScript</string>
        <key>CFBundleVersion</key><string>2.0</string>
      </dict>
    </dict>
  </array>
  <key>connectors</key><dict/>
  <key>workflowMetaData</key>
  <dict>
    <key>serviceInputTypeIdentifier</key><string>com.apple.cocoa.path</string>
    <key>serviceOutputTypeIdentifier</key><string>com.apple.cocoa.string</string>
    <key>serviceProcessesInput</key><integer>0</integer>
    <key>systemImageName</key><string>sparkles</string>
    <key>workflowTypeIdentifier</key><string>com.apple.Automator.servicesMenu</string>
  </dict>
</dict>
</plist>
EOF
echo "Installed Finder Quick Action: $HOME/Library/Services/OpenSiri AI.workflow"
