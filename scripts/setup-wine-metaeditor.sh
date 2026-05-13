#!/bin/bash
# Phase 0 — Setup Wine + MetaEditor on Linux Devin VM (Ubuntu 22.04+)
# Run with: sudo bash scripts/setup-wine-metaeditor.sh
# Idempotent — safe to re-run.

set -euo pipefail

LOG="${LOG:-/tmp/setup-wine.log}"
WINEPREFIX="${WINEPREFIX:-$HOME/.wine-mql5}"
MT5_INSTALLER_URL="https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"
MT5_INSTALLER="/tmp/mt5setup.exe"

log() {
    echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log "ERROR: must run with sudo"
        exit 1
    fi
}

install_packages() {
    log "Installing system packages (Wine, xvfb, cabextract)..."
    dpkg --add-architecture i386 || true
    apt-get update -qq
    apt-get install -y -qq \
        wget \
        cabextract \
        xvfb \
        winetricks \
        wine64 \
        wine32:i386 \
        winbind \
        python3 \
        python3-venv \
        python3-pip \
        2>&1 | tee -a "$LOG"
    log "System packages installed."
}

verify_wine_version() {
    local version
    version=$(wine --version 2>/dev/null | grep -oP '[\d.]+' | head -1)
    log "Wine version detected: $version"
    
    local major
    major=$(echo "$version" | cut -d. -f1)
    if [[ "$major" -lt 8 ]]; then
        log "WARN: Wine version < 8.0. Recommended Wine 8.0+. Continuing..."
    fi
}

setup_wine_prefix() {
    log "Setting up Wine prefix at $WINEPREFIX..."
    export WINEPREFIX
    export WINEARCH=win64
    
    if [[ ! -d "$WINEPREFIX" ]]; then
        xvfb-run -a wineboot -i 2>&1 | tee -a "$LOG" || true
        log "Wine prefix initialized."
    else
        log "Wine prefix exists."
    fi
}

download_mt5_installer() {
    if [[ -f "$MT5_INSTALLER" ]]; then
        log "MT5 installer already downloaded."
        return
    fi
    log "Downloading MT5 installer..."
    wget -q -O "$MT5_INSTALLER" "$MT5_INSTALLER_URL"
    log "Download complete: $(du -h "$MT5_INSTALLER" | cut -f1)"
}

install_mt5() {
    log "Installing MT5 (silent mode) under Wine..."
    export WINEPREFIX
    export DISPLAY=:99
    
    # Start xvfb in background if not running
    if ! pgrep -x Xvfb > /dev/null; then
        Xvfb :99 -screen 0 1024x768x24 &
        sleep 2
    fi
    
    timeout 600 wine "$MT5_INSTALLER" /auto 2>&1 | tee -a "$LOG" || true
    
    # Verify metaeditor64.exe exists
    local METAEDITOR_PATH
    METAEDITOR_PATH=$(find "$WINEPREFIX" -name "metaeditor64.exe" 2>/dev/null | head -1)
    if [[ -z "$METAEDITOR_PATH" ]]; then
        log "ERROR: metaeditor64.exe not found after install"
        exit 1
    fi
    log "MetaEditor installed at: $METAEDITOR_PATH"
    
    # Save path for later use
    echo "export METAEDITOR_PATH='$METAEDITOR_PATH'" > "$HOME/.mql5-env"
    echo "export WINEPREFIX='$WINEPREFIX'" >> "$HOME/.mql5-env"
}

setup_python_venv() {
    log "Setting up Python venv..."
    local PROJECT_DIR
    PROJECT_DIR="$(pwd)"
    
    if [[ ! -d ".venv" ]]; then
        python3 -m venv .venv
    fi
    
    source .venv/bin/activate
    pip install --quiet --upgrade pip
    pip install --quiet -e ".[dev]"
    log "Python venv ready: $(which pytest)"
}

verify_smoke() {
    log "Running quick smoke tests..."
    
    # 1. Wine version
    wine --version
    
    # 2. Try compile a demo .mq5 (created by Phase 0 audit script)
    local DEMO_MQ5
    DEMO_MQ5="$(pwd)/tests/fixtures/demo_smoke.mq5"
    if [[ ! -f "$DEMO_MQ5" ]]; then
        log "Creating demo_smoke.mq5..."
        mkdir -p "$(dirname "$DEMO_MQ5")"
        cat > "$DEMO_MQ5" <<'EOF'
//+------------------------------------------------------------------+
//| Demo smoke test — Phase 0 verification                             |
//+------------------------------------------------------------------+
#property version   "1.00"
#property strict

void OnInit()  { Print("Demo init"); }
void OnTick()  { /* no-op */ }
EOF
    fi
    
    log "Smoke setup complete. Run 'pytest tests/gates/phase-0/' to verify."
}

main() {
    check_root
    install_packages
    verify_wine_version
    setup_wine_prefix
    download_mt5_installer
    install_mt5
    setup_python_venv
    verify_smoke
    
    log "==========================================="
    log "Phase 0 setup complete!"
    log "Next: source .venv/bin/activate && pytest tests/gates/phase-0/ -v"
    log "==========================================="
}

main "$@"
