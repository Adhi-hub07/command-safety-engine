# Command Safety Engine — zsh preexec hook
# Sources: <repo>/hooks/csengine.zsh  (via install-hook or setup.sh)
# Kill-switch: CSENGINE_DISABLE=1

if [[ -z "${CSENGINE_DISABLE:-}" ]]; then
  _csengine_bin=""
  if command -v csengine >/dev/null 2>&1; then
    _csengine_bin="csengine"
  elif [[ -n "${CSENGINE_BIN:-}" && -x "${CSENGINE_BIN}" ]]; then
    _csengine_bin="${CSENGINE_BIN}"
  elif [[ -x "$HOME/.csengine/bin/csengine" ]]; then
    _csengine_bin="$HOME/.csengine/bin/csengine"
  fi

  _csengine_check() {
    [[ -n "${CSENGINE_DISABLE:-}" ]] && return 0
    [[ -z "$_csengine_bin" ]] && return 0
    case "$1" in
      csengine*|_csengine*) return 0 ;;
    esac
    local rc
    "$_csengine_bin" check --json "$1" > /tmp/csengine_last.json 2>/dev/null
    rc=$?
    case "$rc" in
      2) print -u2 "[csengine] BLOCKED: dangerous command detected. Set CSENGINE_DISABLE=1 to bypass." ;;
      1) print -u2 "[csengine] WARNING: this command may be risky. Type it again to confirm." ;;
    esac
    return 0
  }

  # zsh's preexec hook cannot stop a command, so blocking is done via an
  # accept-line widget: pressing Enter runs the engine first; BLOCK aborts the
  # command, WARN requires a second Enter to confirm.
  autoload -Uz add-zsh-hook
  add-zsh-hook preexec _csengine_check

  typeset -g _csengine_armed=0
  typeset -g _csengine_pending=""
  _csengine_accept_line() {
    local cmd="${BUFFER:-}"
    [[ -z "$cmd" ]] && { zle accept-line; return; }
    if [[ "$_csengine_armed" == 1 && "$cmd" == "$_csengine_pending" ]]; then
      _csengine_armed=0
      _csengine_pending=""
      zle accept-line
      return
    fi
    _csengine_armed=0
    _csengine_pending=""
    local rc=0
    case "$cmd" in
      csengine*|_csengine*) ;;
      *) "$_csengine_bin" check --audit "$cmd" >/dev/null 2>&1; rc=$? ;;
    esac
    case "$rc" in
      2)
        print -u2 "[csengine] WIDGET-BLOCKED: dangerous command detected. Set CSENGINE_DISABLE=1 to bypass."
        BUFFER=""
        zle accept-line
        ;;
      1)
        zle -M "[csengine] WARNING: this command may be risky. Press Enter again to confirm."
        _csengine_armed=1
        _csengine_pending="$cmd"
        ;;
      *)
        zle accept-line
        ;;
    esac
  }
  zle -N _csengine_accept_line
  # zsh initializes its keymaps lazily and may clobber .zshrc-time bindings,
  # so re-assert the Enter binding before every prompt.
  _csengine_ensure_bound() {
    bindkey -M main '^M' _csengine_accept_line 2>/dev/null
    bindkey -M emacs '^M' _csengine_accept_line 2>/dev/null
    bindkey -M viins '^M' _csengine_accept_line 2>/dev/null
  }
  add-zsh-hook precmd _csengine_ensure_bound
  _csengine_ensure_bound
fi
