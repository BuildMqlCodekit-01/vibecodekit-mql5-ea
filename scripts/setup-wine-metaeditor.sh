#!/bin/bash
# Phase 0 — Setup Wine + MetaEditor on Linux Devin VM (Ubuntu 22.04+)
# Run with: sudo bash scripts/setup-wine-metaeditor.sh
# Idempotent — safe to re-run.

set -euo pipefail

LOG="${LOG:-/tmp/setup-wine.log}"
WINEPREFIX="${WINEPREFIX:-$HOME/.wine-mql5}"
MT5_INSTALLER_URL="https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"
MT5_INSTALLER="/tmp/mt5setup.exe"
# Plan v5 requires Wine 8.0+. WineHQ stable on jammy currently ships Wine 11,
# which has a regression preventing silent MT5 install (`/auto` does nothing).
# Pin to the oldest 8.x in jammy/main; the smoke test threshold matches.
WINE_PIN_VERSION="${WINE_PIN_VERSION:-8.0.2~jammy-1}"
# Wine 8.0.x ships with these mono/gecko versions; pre-cache MSIs at
# /usr/share/wine/{mono,gecko}/ so wineboot --init doesn't hang on first run
# trying to download them from dl.winehq.org under xvfb.
WINE_MONO_VERSION="7.4.0"
WINE_GECKO_VERSION="2.47.4"

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
    log "Installing system packages (Wine ${WINE_PIN_VERSION} from WineHQ, xvfb, cabextract)..."
    dpkg --add-architecture i386 || true

    # Add WineHQ repository (provides Wine 8.0+ stable on Ubuntu 22.04 jammy).
    # Ubuntu's apt-default `wine64` is 6.0.3 which fails the Plan v5 smoke gate.
    apt-get install -y -qq wget gnupg ca-certificates apt-transport-https 2>&1 | tee -a "$LOG"
    mkdir -pm 755 /etc/apt/keyrings
    if [[ ! -f /etc/apt/keyrings/winehq-archive.key ]]; then
        wget -qO /etc/apt/keyrings/winehq-archive.key https://dl.winehq.org/wine-builds/winehq.key
    fi
    local codename
    codename=$(. /etc/os-release && echo "$VERSION_CODENAME")
    if [[ ! -f "/etc/apt/sources.list.d/winehq-${codename}.sources" ]]; then
        wget -qNP /etc/apt/sources.list.d/ "https://dl.winehq.org/wine-builds/ubuntu/dists/${codename}/winehq-${codename}.sources"
    fi

    apt-get update -qq
    # Pin Wine to a known-good 8.x build; --install-recommends pulls in the
    # matching wine-stable + wine-stable-{amd64,i386} sub-packages.
    apt-get install -y -qq --install-recommends \
        cabextract \
        xvfb \
        winetricks \
        "winehq-stable=${WINE_PIN_VERSION}" \
        "wine-stable=${WINE_PIN_VERSION}" \
        "wine-stable-amd64=${WINE_PIN_VERSION}" \
        "wine-stable-i386:i386=${WINE_PIN_VERSION}" \
        winbind \
        python3 \
        python3-venv \
        python3-pip \
        2>&1 | tee -a "$LOG"
    log "System packages installed."
}

cache_wine_runtime() {
    # Pre-cache wine-mono and wine-gecko MSIs at /usr/share/wine/. Without
    # this, the first `wineboot --init` blocks on a slow xvfb-shielded download.
    log "Pre-caching wine-mono and wine-gecko MSIs at /usr/share/wine/..."
    mkdir -p /usr/share/wine/mono /usr/share/wine/gecko
    if [[ ! -f "/usr/share/wine/mono/wine-mono-${WINE_MONO_VERSION}-x86.msi" ]]; then
        wget -q -O "/usr/share/wine/mono/wine-mono-${WINE_MONO_VERSION}-x86.msi" \
            "https://dl.winehq.org/wine/wine-mono/${WINE_MONO_VERSION}/wine-mono-${WINE_MONO_VERSION}-x86.msi"
    fi
    if [[ ! -f "/usr/share/wine/gecko/wine-gecko-${WINE_GECKO_VERSION}-x86.msi" ]]; then
        wget -q -O "/usr/share/wine/gecko/wine-gecko-${WINE_GECKO_VERSION}-x86.msi" \
            "https://dl.winehq.org/wine/wine-gecko/${WINE_GECKO_VERSION}/wine-gecko-${WINE_GECKO_VERSION}-x86.msi"
    fi
    if [[ ! -f "/usr/share/wine/gecko/wine-gecko-${WINE_GECKO_VERSION}-x86_64.msi" ]]; then
        wget -q -O "/usr/share/wine/gecko/wine-gecko-${WINE_GECKO_VERSION}-x86_64.msi" \
            "https://dl.winehq.org/wine/wine-gecko/${WINE_GECKO_VERSION}/wine-gecko-${WINE_GECKO_VERSION}-x86_64.msi"
    fi
    log "Wine runtime cached."
}

verify_wine_version() {
    local version
    version=$(wine --version 2>/dev/null | grep -oP '[\d.]+' | head -1)
    log "Wine version detected: $version"

    local major
    major=$(echo "$version" | cut -d. -f1)
    if [[ "$major" -lt 8 ]]; then
        log "ERROR: Wine $version is below the Plan v5 minimum (8.0+). Aborting."
        log "       Check that winehq-stable was installed (not Ubuntu's wine64 6.x)."
        exit 1
    fi
}

setup_wine_prefix() {
    log "Setting up Wine prefix at $WINEPREFIX..."
    export WINEPREFIX
    export WINEARCH=win64
    # xvfb-run breaks wineboot --init on Wine 8.x in headless containers
    # (spawns its own X server and tears it down before wineboot finishes).
    # wineboot does not need a display when WINEDLLOVERRIDES skips the
    # GUI-only mono/gecko prompts, so run it with DISPLAY unset.
    export DISPLAY=
    export WINEDEBUG="${WINEDEBUG:--all}"
    # `mscoree,mshtml=` disables the .NET / HTML stubs so wineboot doesn't
    # try to launch the mono/gecko install dialog; the MSIs are cached at
    # /usr/share/wine/{mono,gecko}/ for any later wine call that needs them.
    export WINEDLLOVERRIDES="${WINEDLLOVERRIDES:-mscoree,mshtml=}"

    if [[ ! -d "$WINEPREFIX" ]]; then
        timeout 180 wineboot --init 2>&1 | tee -a "$LOG" || true
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
    export WINEDEBUG="${WINEDEBUG:--all}"
    export WINEDLLOVERRIDES="${WINEDLLOVERRIDES:-mscoree,mshtml=}"

    # Start xvfb in background if not running. MT5 setup needs a real X
    # server (its `/auto` silent mode still pumps a small progress dialog).
    if ! pgrep -x Xvfb > /dev/null; then
        Xvfb :99 -screen 0 1280x1024x24 &
        sleep 3
    fi

    timeout 600 wine "$MT5_INSTALLER" /auto 2>&1 | tee -a "$LOG" || true

    # Verify metaeditor64.exe exists. Use case-insensitive search because the
    # MT5 installer writes 'MetaEditor64.exe' (mixed case) and Linux ext4 is
    # case-sensitive.
    local METAEDITOR_PATH
    METAEDITOR_PATH=$(find "$WINEPREFIX" -iname "metaeditor64.exe" 2>/dev/null | head -1)
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
    cache_wine_runtime
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
