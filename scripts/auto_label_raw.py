"""Auto-label raw shell commands and append them to the labeled dataset.

Loads data/raw/commands_raw.csv (columns: command, source), classifies each
command with a deterministic rule-based heuristic (safe / risky / destructive),
and appends the newly labeled rows to data/labeled/commands_labeled.csv.

Commands already present in the labeled dataset are skipped (exact match) so the
training set never contains duplicate rows.

Usage:
    python scripts/auto_label_raw.py
"""

import os
import re

import pandas as pd

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_PATH = os.path.join(THIS_DIR, "..", "data", "raw", "commands_raw.csv")
LABELED_PATH = os.path.join(THIS_DIR, "..", "data", "labeled", "commands_labeled.csv")

LABELS = ("safe", "risky", "destructive")

_FLAGS = re.IGNORECASE

DESTRUCTIVE_PATTERNS = [
    re.compile(r"\bdd\b.*\bof=/dev/", _FLAGS),
    re.compile(r"\bmkfs(\.\w+)?\b", _FLAGS),
    re.compile(r"\bwipefs\b", _FLAGS),
    re.compile(r"\w*\(\)\s*\{[^}]*&[^}]*\}\s*;", _FLAGS),
    re.compile(r"fork\s+while\s+fork", _FLAGS),
    re.compile(r"\.fork\(\)", _FLAGS),
    re.compile(r"loop\s*\{\s*fork\s*\}", _FLAGS),
    re.compile(r"while\s+true;\s*do\s+\$0\s*&\s*done", _FLAGS),
    re.compile(r"base64\b.*(-d|--decode|-D)\b.*\|\s*(bash|sh)\b", _FLAGS),
    re.compile(r"base64\b.*(-d|--decode|-D)\b.*&&\s*(bash|sh)\b", _FLAGS),
    re.compile(r"(curl|wget)\b[^|]*\|\s*(sudo\s+)?(bash|sh)\b", _FLAGS),
    re.compile(r"<\(\s*(curl|wget)\b", _FLAGS),
    re.compile(r"\brm\s+-rf\s+--no-preserve-root\b", _FLAGS),
    re.compile(r"\brm\s+-rf\s+/\s*(--no-preserve-root)?\s*($|&&|;)", _FLAGS),
    re.compile(r"\brm\s+-rf\s+/(etc|boot|var|usr)(\s|$|&&|;)", _FLAGS),
    re.compile(r"\brm\s+-rf\s+/\*(\s|$)", _FLAGS),
    re.compile(r"\bchmod\s+-R\s+777\s+/\s*($|&&|;)", _FLAGS),
    re.compile(r"/dev/tcp/", _FLAGS),
    re.compile(r"\bnc\b.*-e\b", _FLAGS),
    re.compile(r"\bncat\b.*-e\b", _FLAGS),
    re.compile(r"\bsocat\b.*exec:", _FLAGS),
    re.compile(r"mkfifo\b.*\bnc\b", _FLAGS),
    re.compile(r"fsockopen\s*\(", _FLAGS),
    re.compile(r"socket\.socket\(\)", _FLAGS),
    re.compile(r"--checkpoint-action=exec", _FLAGS),
    re.compile(r"--use-compress-program=/bin/sh", _FLAGS),
    re.compile(r"--to-command=/bin/sh", _FLAGS),
    re.compile(r"vim\s+-c\s+':!", _FLAGS),
    re.compile(r"vim\s+-c\s+':py", _FLAGS),
    re.compile(r"awk\s+'BEGIN\s*\{\s*system\(", _FLAGS),
    re.compile(r"find\b.*-exec\s+/bin/sh\b", _FLAGS),
    re.compile(r"os\.system\(\s*['\"]/bin/sh", _FLAGS),
    re.compile(r"pty\.spawn", _FLAGS),
    re.compile(r"perl\s+-e\s+'exec", _FLAGS),
    re.compile(r"less\s+\S*\s*-e\s+'!/bin/sh'", _FLAGS),
    re.compile(r"nmap\s+--interactive", _FLAGS),
    re.compile(r"\benv\s+/bin/sh\b", _FLAGS),
]

RISKY_PATTERNS = [
    re.compile(r"\bchmod\s+(-R\s+)?777\b", _FLAGS),
    re.compile(r"\brm\s+-rf\b", _FLAGS),
    re.compile(r"\btar\b.*\|\s*(ssh|nc)\b", _FLAGS),
    re.compile(r"\brsync\b.*-av\S*.*@", _FLAGS),
    re.compile(r"\bscp\s+-r\b", _FLAGS),
    re.compile(r"\bscp\b.*(shadow|\.ssh)", _FLAGS),
    re.compile(r"\bkill\s+-9\b", _FLAGS),
    re.compile(r"\bpkill\s+-9\b", _FLAGS),
    re.compile(r"\bkillall\s+-9\b", _FLAGS),
    re.compile(r"(wget|curl)\b.*&&.*\b(tar|unzip)\b", _FLAGS),
    re.compile(r"(wget|curl)\b[^&]*\|\s*(tar|unzip)\b", _FLAGS),
    re.compile(r"git\s+branch\s+-D\b", _FLAGS),
    re.compile(r"\biptables\s+-F\b", _FLAGS),
    re.compile(r"\biptables\s+-P\s+\w+\s+ACCEPT\b", _FLAGS),
    re.compile(r"\bufw\s+disable\b", _FLAGS),
    re.compile(r"systemctl\s+(stop|disable)\s+(firewalld|ufw)", _FLAGS),
    re.compile(r"\bsetenforce\s+0\b", _FLAGS),
    re.compile(r"PermitRootLogin\s+yes", _FLAGS),
    re.compile(r"git\s+push\s+--force", _FLAGS),
    re.compile(r"git\s+reset\s+--hard", _FLAGS),
    re.compile(r"git\s+clean\s+-fdx", _FLAGS),
    re.compile(r"\bhistory\s+-c\b", _FLAGS),
    re.compile(r"unset\s+HISTFILE", _FLAGS),
    re.compile(r"HISTSIZE=0", _FLAGS),
    re.compile(r"\btruncate\s+-s\s*0\b", _FLAGS),
    re.compile(r"\bshred\b", _FLAGS),
    re.compile(r"cat\s+/dev/null\s*>\s*.*bash_history", _FLAGS),
    re.compile(r"docker\s+run\s+--privileged", _FLAGS),
    re.compile(r"docker\s+run\s+--cap-add=ALL", _FLAGS),
    re.compile(r"sudo\s+(pip|npm)\s+install", _FLAGS),
    re.compile(r"crontab\s+-l.*curl", _FLAGS),
    re.compile(r"mount\s+-o\s+remount,rw", _FLAGS),
    re.compile(r"\bdd\s+if=/dev/(zero|urandom|random)\s+of=(?!/dev/)", _FLAGS),
    re.compile(r"NOPASSWD:ALL", _FLAGS),
    re.compile(r"passwd\s+-d\s+root", _FLAGS),
    re.compile(r"usermod\s+-aG\s+sudo", _FLAGS),
    re.compile(r"chmod\s+777\s+/etc/sudoers", _FLAGS),
    re.compile(r"chmod\s+777\s+~?/\.ssh", _FLAGS),
    re.compile(r"chmod\s+777\s+id_rsa", _FLAGS),
    re.compile(r"chmod\s+777\s+/etc/passwd", _FLAGS),
]


def classify_command(cmd: str) -> str:
    """Return 'destructive', 'risky', or 'safe' for a single command string."""
    if not isinstance(cmd, str) or not cmd.strip():
        return "safe"

    for pattern in DESTRUCTIVE_PATTERNS:
        if pattern.search(cmd):
            return "destructive"

    for pattern in RISKY_PATTERNS:
        if pattern.search(cmd):
            return "risky"

    return "safe"


def main():
    if not os.path.isfile(RAW_PATH):
        raise FileNotFoundError(f"Raw dataset not found at {RAW_PATH}")

    raw_df = pd.read_csv(RAW_PATH)
    if "command" not in raw_df.columns or "source" not in raw_df.columns:
        raise ValueError("commands_raw.csv must have columns: command, source")

    raw_df = raw_df.dropna(subset=["command"])
    raw_df["command"] = raw_df["command"].astype(str).str.strip()
    raw_df = raw_df[raw_df["command"] != ""]

    existing = set()
    if os.path.isfile(LABELED_PATH) and os.path.getsize(LABELED_PATH) > 0:
        labeled_df = pd.read_csv(LABELED_PATH)
        existing = set(labeled_df["command"].astype(str).str.strip())
    else:
        labeled_df = None

    raw_df["label"] = raw_df["command"].apply(classify_command)
    new_labeled_df = raw_df[["command", "label", "source"]]
    new_labeled_df = new_labeled_df[~new_labeled_df["command"].isin(existing)]
    skipped = len(raw_df) - len(new_labeled_df)

    os.makedirs(os.path.dirname(LABELED_PATH), exist_ok=True)
    file_exists = os.path.isfile(LABELED_PATH) and os.path.getsize(LABELED_PATH) > 0

    new_labeled_df.to_csv(
        LABELED_PATH,
        mode="a",
        index=False,
        header=not file_exists,
    )

    counts = new_labeled_df["label"].value_counts()
    existing_rows = len(pd.read_csv(LABELED_PATH)) - len(new_labeled_df) if file_exists else 0
    print("=" * 60)
    print(f"Loaded {len(raw_df)} unlabeled commands from {os.path.basename(RAW_PATH)}")
    print("Auto-labeled distribution (this run):")
    for label in LABELS:
        print(f"  {label:<12}: {counts.get(label, 0)}")
    print("-" * 60)
    print(f"Commands already in labeled set (skipped): {skipped}")
    print(f"Rows appended: {len(new_labeled_df)}")
    print(f"Total rows in {os.path.basename(LABELED_PATH)} now: {existing_rows + len(new_labeled_df)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
