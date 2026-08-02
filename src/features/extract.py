"""Feature extraction: turn a command string into the 20-feature vector."""

import posixpath
import re

from src.parser import tokenizer

FEATURE_NAMES = [
    "has_pipe",
    "has_redirect",
    "is_sudo",
    "command_length",
    "token_count",
    "destructive_flag_count",
    "has_wildcard",
    "targets_root_fs",
    "has_network_call",
    "pipes_to_shell",
    "has_chmod_777",
    "has_disk_op",
    "has_fork_bomb_pattern",
    "env_var_manipulation",
    "background_execution",
    "contains_ip_or_url",
    "is_recursive_flag",
    "has_command_substitution",
    "obfuscation_count",
    "whitelist_match",
]

NETWORK_COMMANDS = {"curl", "wget", "nc", "ncat", "socat", "ssh", "scp", "ftp", "telnet", "rsync", "ping"}
DISK_COMMANDS = {"dd", "mkfs", "mkfs.ext4", "mkfs.xfs", "fdisk", "parted", "wipefs", "blkdiscard", "shred", "wipe"}
FLAG_PATTERN = re.compile(r"-(?:[a-zA-Z]*[fry][a-zA-Z]*|y|q)(?!\d)|--(?:force|recursive|yes)")
SUDO_PATTERN = re.compile(r"(^|\s)(sudo|doas|pkexec)(\s|$)")
WILDCARD_PATTERN = re.compile(r"(\*|\?|\[.*?\])")
# wildcards are benign in search/read/list context (find -name '*.py', ls *.log,
# grep '*.conf'); they only signal risk on destructive/overwrite tools.
SAFE_WILDCARD_BASES = {
    "ls", "find", "grep", "rg", "locate", "tree", "du", "echo", "printf", "cat",
    "head", "tail", "less", "more", "cp", "mv", "mkdir", "touch", "sed", "awk",
    "sort", "uniq", "xargs", "for",
}
ROOT_PATHS = ("/", "/etc", "/boot", "/bin", "/usr", "/lib", "/sbin", "/var", "/root", "/dev", "/proc", "/sys")
DESTRUCTIVE_BASES = {"rm", "dd", "mkfs", "mkfs.ext4", "mkfs.xfs", "wipefs", "shred", "fdisk", "parted", "wipe", "blkdiscard", "chmod"}
SYSTEM_DIRS = ("/etc", "/boot", "/bin", "/usr", "/lib", "/sbin", "/var", "/root", "/proc", "/sys")
FORK_BOMB_PATTERN = re.compile(r":\(\)\{.*:&\s*\};.*|:\{\(.*:&.*\}|\{.*\|.*&\s*\};|while\s+true\s*(;|do)|for\s*\(.*\).*\{.*\}.*&")
ENV_MANIP_PATTERN = re.compile(r"(LD_PRELOAD|LD_LIBRARY_PATH|PATH\s*=|PYTHONPATH|IFS\s*=)")
IP_OR_URL_PATTERN = re.compile(
    r"((\d{1,3}\.){3}\d{1,3}|(https?://[^\s/$.?#].[^\s]*)|([a-zA-Z0-9-]+\.(com|net|org|io|ru|cn|info|xyz)))"
)
PIPE_TO_SHELL_PATTERN = re.compile(r"\|[^;|&]*\b(bash|sh|zsh|dash|fish|ksh)(\s|$)|<\s*(bash|sh|zsh)")
CHMOD_777_PATTERN = re.compile(r"chmod\s+[^ ]*777|chmod\s+-R\s+[^ ]*777")


def _targets_root_fs(cmd, base):
    """True when a destructive base command targets a root/system path.

    Path tokens are normalized first so traversal forms like `/tmp/../etc`
    (which resolves to `/etc`) are caught, not just literal system paths.
    """
    if base not in DESTRUCTIVE_BASES:
        return False
    for tok in re.findall(r"/[^\s|&;>'\"$`()\[\]{}]*", cmd):
        norm = posixpath.normpath(tok)
        if norm == "/":
            return True
        if norm in SYSTEM_DIRS or norm.startswith(tuple(d + "/" for d in SYSTEM_DIRS)):
            return True
    return False


def extract_features(command, whitelist=None):
    """Return a dict of 20 features for a single command string."""
    cmd = tokenizer.normalize_space(command)
    tokens = tokenizer.tokenize(cmd)
    words = [t.text for t in tokens if t.kind == "word"]
    base = tokenizer.base_command(cmd)

    features = {
        "has_pipe": int("|" in cmd),
        "has_redirect": int(bool(re.search(r">>|>|2>|&>|<", cmd))),
        "is_sudo": int(bool(SUDO_PATTERN.search(cmd))),
        "command_length": len(cmd),
        "token_count": len(words),
        "destructive_flag_count": len(FLAG_PATTERN.findall(cmd)),
        "has_wildcard": int(bool(WILDCARD_PATTERN.search(cmd)) and base not in SAFE_WILDCARD_BASES),
        "targets_root_fs": int(_targets_root_fs(cmd, base)),
        "has_network_call": int(base in NETWORK_COMMANDS),
        "pipes_to_shell": int(bool(PIPE_TO_SHELL_PATTERN.search(cmd))),
        "has_chmod_777": int(bool(CHMOD_777_PATTERN.search(cmd))),
        "has_disk_op": int(base in DISK_COMMANDS or bool(re.search(r"mkfs|of=/dev", cmd))),
        "has_fork_bomb_pattern": int(bool(FORK_BOMB_PATTERN.search(cmd))),
        "env_var_manipulation": int(bool(ENV_MANIP_PATTERN.search(cmd))),
        "background_execution": int(bool(re.search(r"&\s*$|&\s+disown|nohup\s", cmd))),
        "contains_ip_or_url": int(bool(IP_OR_URL_PATTERN.search(cmd))),
        "is_recursive_flag": int(bool(re.search(r"-[a-zA-Z]*r[a-zA-Z]*\s|--recursive|rm\s+-r", cmd))),
        "has_command_substitution": int(tokenizer.has_command_substitution(cmd)),
        "obfuscation_count": len(tokenizer.detect_obfuscation(cmd)),
        "whitelist_match": 0,
    }

    if whitelist:
        for safe in whitelist:
            if cmd == safe or cmd.startswith(safe + " "):
                features["whitelist_match"] = 1
                break
        if base in {"ls", "cd", "pwd", "echo", "cat", "head", "tail", "grep", "which", "man", "whoami", "date", "uptime", "free"}:
            features["whitelist_match"] = 1

    return features


def feature_vector(features):
    """Convert feature dict to a flat list in FEATURE_NAMES order."""
    return [features[name] for name in FEATURE_NAMES]
