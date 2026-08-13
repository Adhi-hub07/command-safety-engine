"""Extract filesystem paths a command may modify, for snapshotting and undo plans."""

import os
import re

from src.parser import tokenizer

_VALUE_FLAGS = {
    "truncate": {"-s", "--size"},
    "tar": {"-f", "--file", "-C", "--directory", "--strip-components"},
}

_LEADERS = ("sudo", "env", "command", "nohup", "time")


def _rm_args(args):
    return [a for a in args if not a.startswith("-")]


def _chmod_args(args):
    positional = [a for a in args if not a.startswith("-")]
    return positional[1:] if positional else []


def _mv_cp_args(args):
    return [a for a in args if not a.startswith("-")]


def _truncate_args(args):
    out = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in _VALUE_FLAGS["truncate"]:
            i += 2
            continue
        if a.startswith("-"):
            i += 1
            continue
        out.append(a)
        i += 1
    return out


def _dd_args(args):
    return [a[3:] for a in args if a.startswith("of=")]


_HANDLERS = {
    "rm": _rm_args,
    "rmdir": _rm_args,
    "unlink": _rm_args,
    "chmod": _chmod_args,
    "chown": _chmod_args,
    "chgrp": _chmod_args,
    "mv": _mv_cp_args,
    "cp": _mv_cp_args,
    "install": _mv_cp_args,
    "truncate": _truncate_args,
    "dd": _dd_args,
    "touch": _rm_args,
    "tee": _rm_args,
}

_FD_OR_DASH = re.compile(r"^&?-?\d*$")
_GLOB = re.compile(r"[*?\[{]|\$\{|\$\(|`")
_PUNCT_ONLY = re.compile(r"^[:&;{}()=+|,!#@%^*~`\"'\\]+$")


def redirect_targets(tokens):
    """Return file targets of `>` / `>>` / `2>` style redirects in a token list."""
    targets = []
    for i, t in enumerate(tokens):
        if t.kind != "redirect":
            continue
        if t.text in ("<", "<<", "<<<"):
            continue
        for j in range(i + 1, len(tokens)):
            nxt = tokens[j]
            if nxt.kind in ("target", "word"):
                if nxt.text and not _FD_OR_DASH.match(nxt.text):
                    targets.append(nxt.text)
                break
            if nxt.kind == "pipe":
                break
    return targets


def _clean(path):
    path = os.path.expandvars(os.path.expanduser(path))
    if _GLOB.search(path) or "$" in path or _PUNCT_ONLY.match(path):
        return None
    return path


def _abs(path, cwd):
    if not path.startswith("/"):
        path = os.path.join(cwd, path)
    return os.path.normpath(path)


def extract_paths(command, cwd=None):
    """Return a de-duplicated list of absolute paths a command may modify.

    Covers redirect targets plus common mutating commands (rm, mv, cp, chmod,
    chown, truncate, dd, touch, tee). Paths are returned regardless of whether
    they currently exist so undo plans can name files a command would create.
    """
    if cwd is None:
        cwd = os.getcwd()
    paths = []
    for segment in tokenizer.split_pipeline_commands(command):
        tokens = tokenizer.tokenize(segment)
        words = [t.text for t in tokens if t.kind == "word"]
        while words and words[0] in _LEADERS:
            words.pop(0)
        for target in redirect_targets(tokens):
            cleaned = _clean(target)
            if cleaned:
                paths.append(_abs(cleaned, cwd))
        if not words:
            continue
        handler = _HANDLERS.get(words[0])
        if handler:
            for arg in handler(words[1:]):
                cleaned = _clean(arg)
                if cleaned:
                    paths.append(_abs(cleaned, cwd))
    seen, unique = set(), []
    for p in paths:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique
