#!/usr/bin/env bash
# ==============================================================================
# Empty Room — Unix Installer (Linux & macOS)
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/Tech-no-guy/empty-room/main/install.sh | bash
# ==============================================================================

set -e

echo ""
echo "======================================================="
echo "   EMPTY ROOM - SMART SCREEN LOCK"
echo "   Linux / macOS Automated Installer"
echo "======================================================="
echo ""

INSTALL_DIR="$HOME/.empty-room"
APP_DIR="$INSTALL_DIR/app"
VENV_DIR="$INSTALL_DIR/venv"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$INSTALL_DIR" "$BIN_DIR"

# 1. Check Python
echo "[1/4] Checking Python 3..."
PYTHON_BIN=""
for cmd in python3 python; do
  if command -v "$cmd" >/dev/null 2>&1; then
    PYTHON_BIN="$cmd"
    break
  fi
done

if [ -z "$PYTHON_BIN" ]; then
  echo "Error: Python 3 was not found. Please install Python 3.8+."
  exit 1
fi

# 2. Virtualenv
echo "[2/4] Setting up isolated Python virtual environment..."
if [ ! -f "$VENV_DIR/bin/python" ]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet opencv-contrib-python numpy Flask

# 3. Copy/Link files
echo "[3/4] Installing application core..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
if [ -d "$SCRIPT_DIR/core" ]; then
  cp -r "$SCRIPT_DIR"/* "$APP_DIR" 2>/dev/null || true
else
  # Clone or download if run via pipe
  TEMP_ZIP="$INSTALL_DIR/repo.zip"
  curl -sSL "https://github.com/Tech-no-guy/empty-room/archive/refs/heads/main.zip" -o "$TEMP_ZIP"
  unzip -q -o "$TEMP_ZIP" -d "$INSTALL_DIR"
  rm -f "$TEMP_ZIP"
  mv "$INSTALL_DIR/empty-room-main" "$APP_DIR"
fi

# 4. Generate CLI Shim
echo "[4/4] Creating CLI executable at $BIN_DIR/empty-room..."
cat << 'EOF' > "$BIN_DIR/empty-room"
#!/usr/bin/env bash
INSTALL_DIR="$HOME/.empty-room"
APP_DIR="$INSTALL_DIR/app"
VENV_PYTHON="$INSTALL_DIR/venv/bin/python"

export PYTHONPATH="$APP_DIR:$PYTHONPATH"
exec "$VENV_PYTHON" -m core.cli "$@"
EOF

chmod +x "$BIN_DIR/empty-room"

echo ""
echo "Installation complete!"
echo "Make sure $BIN_DIR is in your PATH. (e.g. export PATH=\"$BIN_DIR:\$PATH\")"
echo ""
echo "Commands:"
echo "  empty-room run"
echo "  empty-room configure run"
echo "  empty-room shadow on"
echo "  empty-room shadow off"
echo "  empty-room stop"
echo "  empty-room help"
echo ""
