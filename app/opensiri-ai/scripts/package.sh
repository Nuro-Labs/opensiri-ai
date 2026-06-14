#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
swift build -c release

# Generate AppIcon.icns
swift scripts/make_icns.swift

APP="dist/opensiri-ai.app"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp .build/release/OpenSiriAI "$APP/Contents/MacOS/opensiri-ai"

# Copy resources
cp AppIcon.icns "$APP/Contents/Resources/AppIcon.icns"
cp Sources/OpenSiriAI/logo.svg "$APP/Contents/Resources/logo.svg"
cp Sources/OpenSiriAI/icon.svg "$APP/Contents/Resources/icon.svg"

cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key><string>opensiri-ai</string>
  <key>CFBundleIdentifier</key><string>ai.nuro.opensiri</string>
  <key>CFBundleName</key><string>opensiri-ai</string>
  <key>CFBundleDisplayName</key><string>opensiri-ai</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>0.1.0</string>
  <key>LSMinimumSystemVersion</key><string>14.0</string>
  <key>NSHumanReadableCopyright</key><string>Copyright 2026 Nuro AI Labs</string>
  <key>CFBundleIconFile</key><string>AppIcon</string>
</dict>
</plist>
PLIST
echo "$APP"
