#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Logging helpers with optional color support
# ============================================================================

# Detect if color should be used
_init_colors() {
  # Disable color if:
  # - not a TTY
  # - NO_COLOR env var is set
  # - tput is not available
  # - terminal doesn't support at least 8 colors
  if [ -t 1 ] && [ -z "${NO_COLOR:-}" ] && command -v tput >/dev/null 2>&1; then
    if [ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]; then
      USE_COLOR=1
      return 0
    fi
  fi
  USE_COLOR=0
}

_init_colors

# Color codes (only used if USE_COLOR=1)
if [ "$USE_COLOR" -eq 1 ]; then
  C_BOLD=$(tput bold)
  C_BLUE=$(tput setaf 4)
  C_GREEN=$(tput setaf 2)
  C_YELLOW=$(tput setaf 3)
  C_RED=$(tput setaf 1)
  C_RESET=$(tput sgr0)
else
  C_BOLD=""
  C_BLUE=""
  C_GREEN=""
  C_YELLOW=""
  C_RED=""
  C_RESET=""
fi

# Logging functions
step() {
  printf "${C_BOLD}${C_BLUE}▶${C_RESET} %s\n" "$*"
}

info() {
  printf "  %s\n" "$*"
}

ok() {
  printf "${C_GREEN}✓${C_RESET} %s\n" "$*"
}

warn() {
  printf "${C_YELLOW}⚠${C_RESET} %s\n" "$*" >&2
}

error() {
  printf "${C_RED}✗${C_RESET} %s\n" "$*" >&2
}

# ============================================================================
# Main installer logic
# ============================================================================

step "Validating environment"

# Check for Linux
if [ "$(uname -s)" != "Linux" ]; then
  error "This installer is intended for Linux. Unsupported OS detected."
  exit 1
fi
ok "Running on Linux"

# Detect Debian/Ubuntu
if [ -f /etc/os-release ]; then
  . /etc/os-release
  if [[ "${ID_LIKE:-}" != *"debian"* && "${ID:-}" != "debian" && "${ID:-}" != "ubuntu" ]]; then
    warn "This installer was tested on Debian/Ubuntu. Proceeding may fail on $(uname -s)."
  else
    ok "Debian/Ubuntu-based system detected"
  fi
else
  warn "Could not detect OS from /etc/os-release. Proceeding anyway."
fi

# Check for required system packages
step "Checking system dependencies"
REQS=(python3 python3-venv python3-pip)
MISSING=()
for p in "${REQS[@]}"; do
  if ! command -v "$p" >/dev/null 2>&1; then
    MISSING+=("$p")
    info "Missing: $p"
  fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
  step "Installing system packages: ${MISSING[*]}"
  sudo apt-get update --yes >/dev/null 2>&1 || true
  sudo apt-get install --yes "${MISSING[@]}"
  ok "System packages installed"
else
  ok "All required system packages present"
fi

# Make scripts executable EARLY (before any failures can prevent this)
step "Setting executable permissions"
if [ -f run.sh ]; then
  chmod +x run.sh
  ok "run.sh is executable"
fi
if [ -f install.sh ]; then
  chmod +x install.sh
  ok "install.sh is executable"
fi

# Create or reuse virtualenv
VENV_DIR=${VENV_DIR:-venv}
step "Setting up Python virtual environment"

# Check if venv exists and is valid (has activate script)
if [ ! -d "$VENV_DIR" ] || [ ! -f "$VENV_DIR/bin/activate" ]; then
  if [ -d "$VENV_DIR" ]; then
    warn "Virtualenv at $VENV_DIR is corrupted (missing bin/activate). Recreating..."
    rm -rf "$VENV_DIR"
  fi
  python3 -m venv "$VENV_DIR"
  ok "Created virtualenv at $VENV_DIR"
else
  info "Virtualenv already exists at $VENV_DIR (leaving intact)"
fi

# Activate and install requirements
step "Installing Python dependencies"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate" || {
  error "Failed to activate virtualenv at $VENV_DIR/bin/activate"
  exit 1
}
python -m pip install --upgrade pip || {
  error "Failed to upgrade pip"
  exit 1
}
pip install -r requirements.txt || {
  error "Failed to install Python requirements from requirements.txt"
  exit 1
}
ok "Dependencies installed successfully"

# Ensure .env is ignored by git
step "Configuring git ignore"
if command -v git >/dev/null 2>&1; then
  if ! git check-ignore -q .env 2>/dev/null; then
    if ! grep -qxF ".env" .gitignore 2>/dev/null; then
      printf "\n.env\n" >> .gitignore
      ok ".env added to .gitignore"
    fi
  else
    info ".env already in .gitignore"
  fi
else
  warn "git not found; skipping .gitignore check"
fi

# Interactive creation of .env if missing
step "Configuring application"

# Set defaults for display purposes (will be overridden if .env is created)
PORT=${PORT:-8000}
LOG_LEVEL=${LOG_LEVEL:-INFO}

if [ ! -f .env ]; then
  if [ -t 0 ]; then
    info ".env not found. Creating interactive configuration..."
    info "(Secrets will not be echoed. Press Enter to accept defaults where shown.)"
    printf "\n"

    # read TELEGRAM_BOT_TOKEN silently
    read -s -p "  Telegram bot token (TELEGRAM_BOT_TOKEN): " TELEGRAM_BOT_TOKEN
    printf "\n"
    # read TELEGRAM_CHAT_ID (not secret but required)
    read -p "  Telegram chat id (TELEGRAM_CHAT_ID): " TELEGRAM_CHAT_ID
    # read API_KEY silently
    read -s -p "  API key to protect /alert (API_KEY): " API_KEY
    printf "\n"
    read -p "  Port [8000]: " PORT
    PORT=${PORT:-8000}
    read -p "  Log level [INFO]: " LOG_LEVEL
    LOG_LEVEL=${LOG_LEVEL:-INFO}

    # minimal validation
    if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
      error "Telegram bot token is required."
      exit 1
    fi
    if [ -z "$TELEGRAM_CHAT_ID" ]; then
      error "Telegram chat id is required."
      exit 1
    fi

    # write .env with restrictive permissions
    umask 077
    cat > .env <<ENVEOF
TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID
API_KEY=$API_KEY
HOST=0.0.0.0
PORT=$PORT
LOG_LEVEL=$LOG_LEVEL
INCLUDE_RAW_JSON=false
TELEGRAM_PARSE_MODE=
GUNICORN_WORKERS=3
VENV_DIR=$VENV_DIR
ENVEOF
    chmod 600 .env

    # show masked summary
    mask() {
      local v="$1"
      if [ -z "$v" ]; then
        printf "(not set)"
        return
      fi
      local len=${#v}
      if [ "$len" -le 8 ]; then
        printf "****%s" "${v: -4}"
      else
        printf "%s...%s" "${v:0:4}" "${v: -4}"
      fi
    }

    ok ".env created with configuration:"
    info "  TELEGRAM_BOT_TOKEN=$(mask "$TELEGRAM_BOT_TOKEN")"
    info "  TELEGRAM_CHAT_ID=$(mask "$TELEGRAM_CHAT_ID")"
    info "  API_KEY=$(mask "$API_KEY")"
    info "  PORT=$PORT"
    info "  LOG_LEVEL=$LOG_LEVEL"
  else
    error "Non-interactive shell detected and .env is missing."
    error "Please create .env from .env.example and set TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, API_KEY."
    exit 1
  fi
else
  ok ".env already exists (leaving intact)"
fi

# Success summary
printf "\n"
ok "Installation complete!"
printf "\n"
step "Next steps:"
info "1. Edit .env if you need to change values"
info "   ${C_BLUE}cat .env${C_RESET}"
info ""
info "2. Start locally (in this shell):"
info "   ${C_BLUE}source $VENV_DIR/bin/activate${C_RESET}"
info "   ${C_BLUE}./run.sh${C_RESET}"
info ""
info "3. To install Pulsarr systemd unit (production):"
info "   ${C_BLUE}sudo cp systemd/telegram-alert-sender.service /etc/systemd/system/${C_RESET}"
info "   ${C_BLUE}# unit name is kept as telegram-alert-sender for compatibility${C_RESET}"
info "   ${C_BLUE}sudo systemctl daemon-reload${C_RESET}"
info "   ${C_BLUE}sudo systemctl enable --now telegram-alert-sender${C_RESET}"
info ""
info "4. To test the service:"
info "   ${C_BLUE}curl http://localhost:$PORT/health${C_RESET}"
info ""
