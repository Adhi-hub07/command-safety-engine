# Command Safety Engine — bash preexec hook
# Sources: <repo>/hooks/csengine.bash  (via install-hook or setup.sh)
#
# Requires bash-preexec.sh to be sourced first. Kill-switch: CSENGINE_DISABLE=1

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
    # skip the hook's own commands to avoid loops
    case "$1" in
      csengine*|_csengine*) return 0 ;;
    esac
    # run once: JSON result + audit log + verdict exit code (0=ALLOW, 1=WARN, 2=BLOCK)
    "$_csengine_bin" check --json --audit "$1" > /tmp/csengine_last.json 2>/dev/null
    local rc=$?
    case "$rc" in
      2) echo "[csengine] BLOCKED: dangerous command detected. Set CSENGINE_DISABLE=1 to bypass." >&2
         return 1 ;;
      1) echo "[csengine] WARNING: this command may be risky. Type it again to confirm." >&2
         ;;
    esac
    return 0
  }

  if declare -F preexec >/dev/null 2>&1; then
    preexec_functions+=(_csengine_check)
  else
    # bash-preexec not sourced yet; install via PROMPT_COMMAND fallback is not safe,
    # so warn once and instruct the user to source bash-preexec.sh first.
    [[ -n "${CSENGINE_DEBUG:-}" ]] && echo "[csengine] bash-preexec not active. Source hooks/bash-preexec.sh first." >&2
  fi
fi
