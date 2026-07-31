# Command Safety Engine — zsh preexec hook
# Sources: <repo>/hooks/csengine.zsh  (via install-hook or setup.sh)
# Kill-switch: CSENGINE_DISABLE=1

if [[ -z "${CSENGINE_DISABLE:-}" ]]; then
  _csengine_bin=""
  if command -v csengine >/dev/null 2>&1; then
    _csengine_bin="csengine"
  elif [[ -n "${CSENGINE_BIN:-}" && -x "${CSENGINE_BIN}" ]]; then
    _csengine_bin="${CSENGINE_BIN}"
  fi

  _csengine_check() {
    [[ -n "${CSENGINE_DISABLE:-}" ]] && return 0
    [[ -z "$_csengine_bin" ]] && return 0
    case "$1" in
      csengine*|_csengine*) return 0 ;;
    esac
    local rc
    "$_csengine_bin" check --json --audit "$1" > /tmp/csengine_last.json 2>/dev/null
    rc=$?
    case "$rc" in
      2) print -u2 "[csengine] BLOCKED: dangerous command detected. Set CSENGINE_DISABLE=1 to bypass."
         return 1 ;;
      1) print -u2 "[csengine] WARNING: this command may be risky. Type it again to confirm."
         ;;
    esac
    return 0
  }

  autoload -Uz add-zsh-hook
  add-zsh-hook preexec _csengine_check
fi
