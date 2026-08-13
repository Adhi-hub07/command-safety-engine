# Command Safety Engine — bash preexec hook
# Sources: <repo>/hooks/csengine.bash  (via install-hook or setup.sh)
#
# Requires bash-preexec.sh to be sourced first. Kill-switch: CSENGINE_DISABLE=1

if [[ -z "${CSENGINE_DISABLE:-}" ]]; then
  # auto-load the vendored bash-preexec.sh if its machinery is missing
  if ! declare -F __bp_install >/dev/null 2>&1; then
    _csengine_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [[ -f "$_csengine_dir/bash-preexec.sh" ]]; then
      source "$_csengine_dir/bash-preexec.sh"
    fi
  fi

  _csengine_bin=""
  if command -v csengine >/dev/null 2>&1; then
    _csengine_bin="csengine"
  elif [[ -n "${CSENGINE_BIN:-}" && -x "${CSENGINE_BIN}" ]]; then
    _csengine_bin="${CSENGINE_BIN}"
  elif [[ -x "$HOME/.csengine/bin/csengine" ]]; then
    # fallback: wrapper installed by setup.sh without requiring PATH changes
    _csengine_bin="$HOME/.csengine/bin/csengine"
  fi

  _csengine_warned=""   # pending WARN command awaiting a confirming retype
  _csengine_check() {
    [[ -n "${CSENGINE_DISABLE:-}" ]] && return 0
    [[ -z "$_csengine_bin" ]] && return 0
    # skip the hook's own commands to avoid loops
    case "$1" in
      csengine*|_csengine*) return 0 ;;
    esac
    # retype-to-confirm: a previously-WARNed identical command is allowed
    if [[ -n "$_csengine_warned" && "$_csengine_warned" == "$1" ]]; then
      _csengine_warned=""
      # snapshot the risky command before it actually runs, so it can be undone
      if [[ -z "${CSENGINE_TX:-}" || "${CSENGINE_TX:-}" != "0" ]]; then
        "$_csengine_bin" check --json --tx --audit "$1" > /tmp/csengine_last.json
      fi
      return 0
    fi
    _csengine_warned=""
    # run once: JSON result + audit log + verdict exit code (0=ALLOW, 1=WARN, 2=BLOCK)
    "$_csengine_bin" check --json --audit "$1" > /tmp/csengine_last.json 2>/dev/null
    local rc=$?
    case "$rc" in
      2) echo "[csengine] BLOCKED: dangerous command detected. Set CSENGINE_DISABLE=1 to bypass." >&2
         return 1 ;;
      1) _csengine_warned="$1"
         echo "[csengine] WARNING: this command may be risky. Type it again to confirm." >&2
         return 1 ;;
    esac
    return 0
  }

  if declare -F __bp_install >/dev/null 2>&1; then
    # bash-preexec calls every preexec_functions entry that exists as a function
    preexec_functions+=(_csengine_check)
    # A non-zero preexec return blocks the command only when extdebug is set
    # (DEBUG-trap path, bash <= 5.2).
    shopt -s extdebug 2>/dev/null
  else
    # bash-preexec not sourced yet; install via PROMPT_COMMAND fallback is not safe,
    # so warn once and instruct the user to source bash-preexec.sh first.
    [[ -n "${CSENGINE_DEBUG:-}" ]] && echo "[csengine] bash-preexec not active. Source hooks/bash-preexec.sh first." >&2
  fi
fi
