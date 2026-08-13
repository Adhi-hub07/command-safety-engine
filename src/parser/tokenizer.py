"""Shell command tokenization with bashlex, falling back to a pure-Python tokenizer."""

import os
import re
import shlex

try:
    import bashlex
    HAS_BASHLEX = True
except ImportError:
    HAS_BASHLEX = False

PIPE_PATTERN = re.compile(r"\s*(\|\s*|\||>\s*&?|&>|\b2>\s*|\b2>&1|\b2>|>>|>|<|<<<|<\s*|<<)\s*")
REDIRECTS = {"|", ">", ">>", "<", "2>", "2>&1", "&>", "<<<", "<<"}

_SUBSTITUTION_RE = re.compile(r"\$\(.*?\)|`[^`]*`|\$\{.*?\}")
_VARIABLE_RE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")
_GLOB_RE = re.compile(r"(\*|\?|\[.*?\])")


class CommandToken:
    __slots__ = ("kind", "text")

    def __init__(self, text, kind="word"):
        self.text = text
        self.kind = kind

    def __repr__(self):
        return f"CommandToken({self.text!r}, {self.kind!r})"


def _expand_variables(text):
    """Resolve known safe environment variables without executing anything."""

    def repl(match):
        name = match.group(1)
        value = os.environ.get(name)
        if value is None:
            return f"${name}"
        return value

    return _VARIABLE_RE.sub(repl, text)


def expand_command(command, aliases=None, env_vars=True):
    """Expand aliases and environment variables for classification."""
    if not command or not command.strip():
        return command
    expanded = command.strip()
    if aliases:
        tokens = expanded.split()
        first = tokens[0] if tokens else ""
        if first in aliases:
            expanded = aliases[first] + " " + " ".join(tokens[1:]).strip()
    if env_vars:
        expanded = _expand_variables(expanded)
    return expanded


def normalize_space(command):
    return re.sub(r"\s+", " ", command.strip())


def tokenize(command):
    """Return a list of CommandToken with pipe/redirect/word kinds."""
    if not command or not command.strip():
        return []
    if HAS_BASHLEX:
        try:
            return _tokenize_bashlex(command)
        except Exception:
            pass
    return _tokenize_fallback(command)


def _tokenize_bashlex(command):
    tokens = []

    def walk(node):
        kind = getattr(node, "kind", None)
        word = getattr(node, "word", None)
        if kind == "command" or kind == "pipeline":
            for part in getattr(node, "parts", []):
                walk(part)
        elif kind == "operator":
            tokens.append(CommandToken(word or node.op, "pipe" if word in ("|", "||") else "redirect"))
        elif kind == "redirect":
            op = getattr(node, "type", None) or getattr(node, "op", ">")
            tokens.append(CommandToken(op, "redirect"))
            output = getattr(node, "output", None)
            word = getattr(output, "word", None) or getattr(node, "word", None)
            if word:
                tokens.append(CommandToken(word, "target"))
        elif kind == "word" and word:
            tokens.append(CommandToken(word, "word"))
        else:
            for child in getattr(node, "parts", []) or []:
                walk(child)

    for node in bashlex.parse(command):
        walk(node)
    return tokens


def _tokenize_fallback(command):
    tokens = []
    try:
        parts = shlex.split(command)
    except ValueError:
        parts = command.split()
    for part in parts:
        if part in REDIRECTS:
            tokens.append(CommandToken(part, "redirect" if part != "|" else "pipe"))
        elif part == "|":
            tokens.append(CommandToken(part, "pipe"))
        else:
            tokens.append(CommandToken(part, "word"))
    return tokens


def split_pipeline_commands(command):
    """Split a command into individual pipeline segments, preserving order."""
    segments = []
    current = []
    for token in tokenize(command):
        if token.kind == "pipe":
            if current:
                segments.append(" ".join(t.text for t in current))
                current = []
        else:
            current.append(token)
    if current:
        segments.append(" ".join(t.text for t in current))
    return segments


def base_command(command):
    """Return the first executable token of a command."""
    if not command or not command.strip():
        return ""
    for token in tokenize(command):
        if token.kind == "word":
            return token.text
        if token.kind == "pipe":
            continue
    try:
        return shlex.split(command)[0]
    except Exception:
        return command.split()[0]


def command_chain(command):
    """Return a tuple of base commands in a chain (split on &&, ;, |)."""
    chain = []
    for segment in re.split(r"\s*(?:&&|\|\||;)\s*", command):
        cmd = base_command(segment)
        if cmd:
            chain.append(cmd)
    return tuple(chain)


def has_command_substitution(command):
    return bool(_SUBSTITUTION_RE.search(command))


def detect_obfuscation(command):
    """Return a list of obfuscation indicators found in the command."""
    indicators = []
    if re.search(r"\\[a-z]", command):
        indicators.append("escaped_chars")
    if _SUBSTITUTION_RE.search(command):
        indicators.append("command_substitution")
    if re.search(r"base64\s+-\s*d", command):
        indicators.append("base64_decode")
    if re.search(r"(?:echo|printf)\s+[\"']?[A-Za-z0-9+/=]{20,}", command):
        indicators.append("encoded_blob")
    if re.search(r"\beval\b", command):
        indicators.append("eval")
    if re.search(r"\b(?:printf|echo)\b[^;|]*\\x[0-9a-f]{2}", command):
        indicators.append("hex_escape")
    return indicators
