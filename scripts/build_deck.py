#!/usr/bin/env python
"""Build the 12-slide hackathon deck (16:9 PDF) with reportlab.

Usage: python scripts/build_deck.py   ->  docs/presentation.pdf
Requires: reportlab, pillow, cairosvg (pip install -r requirements-dev.txt)
"""

import os

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "docs", "presentation.pdf")
ARCH_PNG = os.path.join(REPO, "docs", "architecture.png")

PAGE_W, PAGE_H = landscape(A4)  # 842 x 595 pt, 16:9-ish

BG = HexColor("#0f172a")
PANEL = HexColor("#1e293b")
PANEL_LINE = HexColor("#334155")
TITLE = HexColor("#f8fafc")
BODY = HexColor("#e2e8f0")
MUTED = HexColor("#94a3b8")
BLUE = HexColor("#3b82f6")
PURPLE = HexColor("#a855f7")
TEAL = HexColor("#2dd4bf")
GREEN = HexColor("#22c55e")
AMBER = HexColor("#f59e0b")
RED = HexColor("#ef4444")

SANS = "Helvetica"
SANS_B = "Helvetica-Bold"
MONO = "Courier"
MONO_B = "Courier-Bold"


def wrap(draw, text, font, size, max_w):
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if stringWidth(t, font, size) <= max_w:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_text(draw, x, y, text, font=SANS, size=14, color=BODY, max_w=None):
    if max_w:
        for i, ln in enumerate(wrap(draw, text, font, size, max_w)):
            draw.drawString(x, y - i * (size * 1.25), ln)
        return y - len(wrap(draw, text, font, size, max_w)) * (size * 1.25)
    draw.drawString(x, y, text)
    return y


def bullet(draw, x, y, text, size=13, color=BODY, gap=6, marker="\u25AA", max_w=560):
    mw = stringWidth(marker, SANS, size)
    lines = wrap(draw, text, SANS, size, max_w)
    draw.setFillColor(color)
    for i, ln in enumerate(lines):
        ly = y - i * (size * 1.25)
        if i == 0:
            draw.drawString(x, ly, marker)
        draw.drawString(x + mw + 8, ly, ln)
    return y - len(lines) * (size * 1.25) - gap


def header(draw, num, title, subtitle=None):
    draw.setFillColor(BG)
    draw.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    draw.setStrokeColor(BLUE)
    draw.setLineWidth(3)
    draw.line(48, PAGE_H - 64, 48, PAGE_H - 20)
    draw.setFillColor(TITLE)
    draw.setFont(SANS_B, 25)
    draw.drawString(72, PAGE_H - 52, f"{num}.  {title}")
    if subtitle:
        draw.setFillColor(MUTED)
        draw.setFont(SANS, 12)
        draw.drawString(74, PAGE_H - 78, subtitle)
    draw.setFillColor(HexColor("#475569"))
    draw.setFont(SANS, 9)
    draw.drawRightString(PAGE_W - 40, PAGE_H - 46, "Command Safety Engine  ·  C-DAC Secure OS Hackathon 2026")
    draw.setStrokeColor(HexColor("#334155"))
    draw.setLineWidth(1)
    draw.line(48, 46, PAGE_W - 48, 46)
    draw.setFillColor(MUTED)
    draw.setFont(SANS, 9)
    draw.drawString(48, 30, "csengine · Adhithya J · Track 1: AI @ Application Level")
    draw.drawRightString(PAGE_W - 48, 30, "fully offline · open-source (MIT)")


def panel(draw, x, y, w, h, fill=PANEL, line=PANEL_LINE):
    draw.setFillColor(fill)
    draw.setStrokeColor(line)
    draw.setLineWidth(1)
    draw.roundRect(x, y, w, h, 8, fill=1, stroke=1)


def footer_page(draw, n):
    draw.setFillColor(MUTED)
    draw.setFont(SANS, 9)
    draw.drawCentredString(PAGE_W / 2, 18, f"{n}")


def slide_title(draw):
    draw.setFillColor(TITLE)
    draw.setFont(SANS_B, 34)
    draw.drawString(72, PAGE_H - 140, "COMMAND SAFETY ENGINE")
    draw.setFillColor(TEAL)
    draw.setFont(SANS_B, 20)
    draw.drawString(72, PAGE_H - 172, "An offline AI guard for the Linux shell")
    draw.setFillColor(MUTED)
    draw.setFont(SANS, 13)
    draw.drawString(72, PAGE_H - 200, "C-DAC Secure OS Hackathon 2026 · Track 1 (AI @ Application Level)")
    draw.setFillColor(BODY)
    draw.setFont(SANS, 13)
    draw.drawString(72, 170, "Adhithya J")
    draw.setFillColor(MUTED)
    draw.setFont(SANS, 12)
    draw.drawString(72, 150, "github.com/Adhi-hub07/command-safety-engine")
    draw.setFont(SANS, 12)
    draw.drawString(72, 128, "Demo:  csengine check \"rm -rf /\"  →  BLOCK")
    # terminal mock
    panel(draw, 420, 120, 360, 230, fill=HexColor("#0b1220"), line=HexColor("#1f2937"))
    ty = 320
    draw.setFillColor(HexColor("#10b981"))
    draw.setFont(SANS, 11)
    draw.drawString(440, ty, "kali@host:~$ ls -la")
    draw.drawString(440, ty - 22, "kali@host:~$ git status")
    draw.setFillColor(HexColor("#f59e0b"))
    draw.drawString(440, ty - 44, "kali@host:~$ chmod -R 777 /var/www")
    draw.setFillColor(HexColor("#f87171"))
    draw.setFont(SANS_B, 11)
    draw.drawString(440, ty - 66, "kali@host:~$ rm -rf /")
    draw.setFillColor(HexColor("#fecaca"))
    draw.drawString(440, ty - 88, "[BLOCKED] recursive delete of system root")
    draw.setFillColor(HexColor("#f87171"))
    draw.drawString(440, ty - 110, "[suggested] rm -rf /path/to/folder")
    draw.setFillColor(HexColor("#e2e8f0"))
    draw.drawString(440, ty - 132, "kali@host:~$")


def slide_problem(draw):
    draw.setFillColor(BODY)
    draw.setFont(SANS, 13)
    x = 72
    y = PAGE_H - 120
    y = bullet(draw, x, y, "A single destructive command is often irreversible — and typed by hand or pasted from the web.", 14, gap=8)
    y = bullet(draw, x, y, "Fork bombs, \u201Cdownload-and-run\u201D chains, chmod 777, credential scraping, obfuscated payloads.", 14, gap=8)
    y = bullet(draw, x, y, "No mainstream OS ships a safety layer between the keyboard and the kernel.", 14, gap=8)
    y -= 14
    panel(draw, x, y - 200, 380, 190, fill=HexColor("#0b1220"), line=PANEL_LINE)
    draw.setFillColor(TITLE)
    draw.setFont(SANS_B, 13)
    draw.drawString(x + 16, y - 24, "Why existing tools fall short")
    labels = [
        ("sudo / SELinux", "stop unauthorised actions, not user mistakes"),
        ("blocklists", "brittle strings, false-positive fatigue"),
        ("cloud AI helpers", "can't run on sovereign / air-gapped systems"),
    ]
    yy = y - 54
    for name, desc in labels:
        draw.setFillColor(BLUE)
        draw.setFont(SANS_B, 12)
        draw.drawString(x + 16, yy, name)
        draw.setFillColor(MUTED)
        draw.setFont(SANS, 11)
        draw.drawString(x + 16, yy - 16, desc)
        yy -= 52
    px = 520
    py = y - 20
    panel(draw, px, py - 260, 320, 240, fill=PANEL, line=BLUE)
    draw.setFillColor(BLUE)
    draw.setFont(SANS_B, 13)
    draw.drawString(px + 16, py - 24, "Challenge (verbatim)")
    draw.setFillColor(BODY)
    draw.setFont(SANS, 12)
    challenge = ("Design an intelligent command analysis layer that evaluates Linux commands before "
                 "execution, understands user intent, identifies potential risks, and recommends safer "
                 "alternatives while preserving user control and system security.")
    yy = py - 50
    for ln in wrap(draw, challenge, SANS, 12, 285):
        draw.drawString(px + 16, yy, ln)
        yy -= 17
    draw.setFillColor(GREEN)
    draw.setFont(SANS_B, 13)
    draw.drawString(px + 16, yy - 22, "Our answer")
    draw.setFillColor(BODY)
    draw.setFont(SANS, 12)
    yy = yy - 44
    for ln in wrap(draw, "A fast, accurate, fully offline safety layer that catches dangerous commands "
                          "in real time, explains why, offers a safe alternative, and keeps the user in control.", SANS, 12, 285):
        draw.drawString(px + 16, yy, ln)
        yy -= 17


def slide_overview(draw):
    draw.setFillColor(BODY)
    draw.setFont(SANS, 13)
    x, y = 72, PAGE_H - 120
    y = bullet(draw, x, y, "Defence in depth: three independent layers, any layer can only push toward more caution.", 14, gap=10)
    layers = [
        ("Layer 1 · Rule Engine", BLUE, "27 MITRE ATT&CK-aligned rule groups (R001–R027), deterministic, <0.5 ms. Critical rule always BLOCKs."),
        ("Layer 2 · ML Classifier", PURPLE, "GradientBoosting on 20 intent features, 3 classes (safe / risky / destructive), ~0.1 ms."),
        ("Layer 3 · LLM Explainer", TEAL, "Qwen 2.5 3B via Ollama, 100% offline, only for ambiguous commands. Graceful fallback."),
    ]
    yy = y - 18
    for name, col, desc in layers:
        panel(draw, x, yy - 64, 380, 74, fill=PANEL, line=col)
        draw.setFillColor(col)
        draw.setFont(SANS_B, 13)
        draw.drawString(x + 14, yy - 20, name)
        draw.setFillColor(BODY)
        draw.setFont(SANS, 11)
        for ln in wrap(draw, desc, SANS, 11, 350):
            draw.drawString(x + 14, yy - 40, ln)
            yy -= 15
        yy -= 20
    px = 520
    py = PAGE_H - 130
    panel(draw, px, py - 260, 320, 250, fill=PANEL, line=GREEN)
    draw.setFillColor(GREEN)
    draw.setFont(SANS_B, 13)
    draw.drawString(px + 16, py - 24, "Fusion & output")
    rows = [
        ("rule_score", "max severity of matched rules (0–100)"),
        ("ml_risk", "label risk × confidence"),
        ("score", "blend → 0–100"),
        ("BLOCK", "≥ 80  or  critical rule"),
        ("WARN", "45–79, asks to confirm"),
        ("ALLOW", "< 45  or  whitelisted"),
    ]
    yy = py - 50
    for k, v in rows:
        draw.setFillColor(TITLE)
        draw.setFont(MONO_B, 11)
        draw.drawString(px + 16, yy, k)
        draw.setFillColor(MUTED)
        draw.setFont(SANS, 10)
        draw.drawString(px + 150, yy, v)
        yy -= 28
    # top claim
    panel(draw, x, PAGE_H - 210, 380, 70, fill=HexColor("#0b1220"), line=PANEL_LINE)
    draw.setFillColor(TITLE)
    draw.setFont(SANS_B, 13)
    draw.drawString(x + 14, PAGE_H - 178, "On the happy path: zero overhead")
    draw.setFillColor(MUTED)
    draw.setFont(SANS, 11)
    draw.drawString(x + 14, PAGE_H - 198, "whitelisted daily commands skip analysis entirely")


def slide_arch(draw):
    img_w, img_h = 640, 360
    ix = (PAGE_W - img_w) / 2
    iy = 70
    draw.setFillColor(PANEL)
    draw.setStrokeColor(PANEL_LINE)
    draw.roundRect(ix - 12, iy - 12, img_w + 24, img_h + 24, 10, fill=1, stroke=1)
    draw.drawImage(ARCH_PNG, ix, iy, width=img_w, height=img_h, mask="auto")


def slide_rules(draw):
    x, y = 72, PAGE_H - 130
    draw.setFillColor(BODY)
    draw.setFont(SANS, 13)
    y = bullet(draw, x, y, "Fast, deterministic first gate — everything else builds on it. Anchored, escaped regexes, not naive substrings.", 14, gap=8)
    groups = [
        ("Destructive / data loss", "R001 rm -rf root · R023 system-file tamper · R024 block-device write · R025 tar --remove-files · R027 --no-preserve-root"),
        ("Denial of service", "R008 fork bomb · R026 git clean · R021 variable delete"),
        ("Credential exposure", "R022 /etc/shadow · /etc/sudoers · ssh keys"),
        ("Supply chain / download-and-run", "R004 curl|bash · wget|sh · curl -o + execute"),
        ("Escalation / integrity", "R007 chmod -R 777 · R017 kill/shutdown · R020 su/sudo misuse"),
    ]
    yy = y - 16
    for name, desc in groups:
        draw.setFillColor(BLUE)
        draw.setFont(SANS_B, 12)
        draw.drawString(x, yy, name)
        draw.setFillColor(BODY)
        draw.setFont(SANS, 11)
        for ln in wrap(draw, desc, SANS, 11, 620):
            draw.drawString(x + 8, yy - 17, ln)
            yy -= 16
        yy -= 10
    panel(draw, x, yy - 44, 380, 58, fill=HexColor("#0b1220"), line=RED)
    draw.setFillColor(RED)
    draw.setFont(SANS_B, 12)
    draw.drawString(x + 14, yy - 20, "Safety-first override")
    draw.setFillColor(MUTED)
    draw.setFont(SANS, 11)
    draw.drawString(x + 14, yy - 38, "critical rule ⇒ BLOCK regardless of ML confidence")


def slide_ml(draw):
    x, y = 72, PAGE_H - 130
    draw.setFillColor(BODY)
    draw.setFont(SANS, 13)
    y = bullet(draw, x, y, "GradientBoosting on 20 hand-crafted intent features — generalises to attacks no rule can enumerate.", 14, gap=8)
    feats = ["pipes/redirects", "root-fs targets", "obfuscation count", "network calls", "disk ops", "wildcards", "recursive flags", "chmod 777", "sudo", "env-var manipulation"]
    fx, fy = x, y - 18
    for i, f in enumerate(feats):
        col = BLUE if i % 3 == 0 else (PURPLE if i % 3 == 1 else TEAL)
        w = 10 + len(f) * 6.2
        draw.setFillColor(col)
        draw.roundRect(fx, fy, w, 24, 6, fill=1, stroke=0)
        draw.setFillColor(HexColor("#0f172a"))
        draw.setFont(SANS_B, 10)
        draw.drawString(fx + 5, fy + 7, f)
        fx += w + 10
        if fx > 620:
            fx = x
            fy -= 32
    fy -= 40
    draw.setFillColor(TITLE)
    draw.setFont(SANS_B, 14)
    draw.drawString(x, fy, "Measured results (honest, reproducible)")
    draw.setFillColor(MUTED)
    draw.setFont(SANS, 11)
    draw.drawString(x + 4, fy - 18, "5-fold CV 0.811 ± 0.033 acc · 0.771 ± 0.048 macro-F1 · held-out 82.2% / 0.791")
    fy -= 40
    # table
    cols = [300, 90, 90, 90, 90, 90]
    headers = ["Model", "Acc", "Macro-F1", "Destr. recall", "Risky recall", "Safe recall"]
    rows = [
        ["GradientBoosting (deployed)", "0.822", "0.791", "0.771", "0.632", "0.934"],
        ["RandomForest", "0.794", "0.772", "0.771", "0.724", "0.836"],
        ["LogisticRegression", "0.815", "0.777", "0.688", "0.645", "0.941"],
    ]
    tx = x
    draw.setFont(SANS_B, 10)
    for i, h in enumerate(headers):
        draw.setFillColor(BLUE)
        draw.drawString(tx + 4, fy, h)
        tx += cols[i]
    fy -= 18
    for r in rows:
        tx = x
        for i, c in enumerate(r):
            draw.setFont(MONO_B if i == 0 else SANS, 10)
            draw.setFillColor(GREEN if i == 0 else BODY)
            draw.drawString(tx + 4, fy, c)
            tx += cols[i]
        fy -= 18
    panel(draw, x, PAGE_H - 200, 380, 60, fill=HexColor("#0b1220"), line=AMBER)
    draw.setFillColor(AMBER)
    draw.setFont(SANS_B, 12)
    draw.drawString(x + 14, PAGE_H - 178, "Data hygiene")
    draw.setFillColor(MUTED)
    draw.setFont(SANS, 10)
    draw.drawString(x + 14, PAGE_H - 194, "666 duplicate rows removed at build; numbers are dedup, not cherry-picked")


def slide_llm(draw):
    x, y = 72, PAGE_H - 130
    draw.setFillColor(BODY)
    draw.setFont(SANS, 13)
    y = bullet(draw, x, y, "Layer 3 exists for one reason: explain the decision in plain language when the command is confusing.", 14, gap=8)
    y = bullet(draw, x, y, "Local Qwen 2.5 3B via Ollama — no cloud, no network, no data egress.", 14, gap=8)
    y = bullet(draw, x, y, "Invoked only on demand (ambiguous / flagged / LLM hook), so idle cost is ~0.", 14, gap=8)
    y = bullet(draw, x, y, "0.5 s TCP probe; on absence the rule+ML explanation is returned instantly — safety never waits on the LLM.", 14, gap=8)
    py = PAGE_H - 230
    panel(draw, x, py - 120, 380, 130, fill=HexColor("#0b1220"), line=TEAL)
    draw.setFillColor(TEAL)
    draw.setFont(SANS_B, 13)
    draw.drawString(x + 14, py - 22, "Example — obfuscated command")
    draw.setFillColor(HexColor("#f8fafc"))
    draw.setFont(MONO, 11)
    draw.drawString(x + 14, py - 44, "$ xxd -r -p <<< '77686f616d69'")
    draw.setFillColor(MUTED)
    draw.setFont(SANS, 11)
    yy = py - 66
    for ln in wrap(draw, "Decoding a hex blob is how malware hides. The LLM explains: \u201Cthis decodes the text \u2018whoami\u2019 — a read-only command.\u201D", SANS, 11, 350):
        draw.drawString(x + 14, yy, ln)
        yy -= 16
    px = 520
    py = PAGE_H - 160
    panel(draw, px, py - 230, 320, 220, fill=PANEL, line=GREEN)
    draw.setFillColor(GREEN)
    draw.setFont(SANS_B, 13)
    draw.drawString(px + 16, py - 24, "Privacy & audit")
    items = [
        "commands never stored in plaintext",
        "SHA-256 hashed JSONL audit log",
        "offline by design, no telemetry",
        "override is logged and detectable",
    ]
    yy = py - 52
    for it in items:
        draw.setFillColor(BODY)
        draw.setFont(SANS, 11)
        draw.drawString(px + 16, yy, "\u25AA  " + it)
        yy -= 26
    draw.setFillColor(MUTED)
    draw.setFont(SANS, 10)
    draw.drawString(px + 16, yy - 8, "forensics without storing plaintext")


def slide_integration(draw):
    x, y = 72, PAGE_H - 130
    draw.setFillColor(BODY)
    draw.setFont(SANS, 13)
    y = bullet(draw, x, y, "Installs in minutes on Ubuntu / BOSS OS via a single script (setup.sh).", 14, gap=8)
    y = bullet(draw, x, y, "Hooks into bash and zsh (preexec) — every command is judged before it runs.", 14, gap=8)
    y = bullet(draw, x, y, "Rich CLI:  csengine check <cmd>   ·   csengine status   ·   csengine install-hook", 14, gap=8)
    y = bullet(draw, x, y, "Optional bubblewrap sandbox for untrusted downloads.", 14, gap=8)
    # verdict cards
    vy = PAGE_H - 300
    cards = [
        ("ALLOW", GREEN, "daily commands execute instantly", "whitelist or score < 45"),
        ("WARN", AMBER, "asks to confirm / retype", "score 45–79"),
        ("BLOCK", RED, "refuses execution · exit 2", "score ≥ 80 or critical rule"),
    ]
    for i, (name, col, line1, line2) in enumerate(cards):
        cx = x + i * 220
        panel(draw, cx, vy - 90, 200, 100, fill=HexColor("#0b1220"), line=col)
        draw.setFillColor(col)
        draw.setFont(SANS_B, 16)
        draw.drawString(cx + 14, vy - 28, name)
        draw.setFillColor(BODY)
        draw.setFont(SANS, 10)
        draw.drawString(cx + 14, vy - 48, line1)
        draw.setFillColor(MUTED)
        draw.setFont(SANS, 10)
        draw.drawString(cx + 14, vy - 64, line2)
    panel(draw, 520, PAGE_H - 300, 320, 240, fill=PANEL, line=BLUE)
    draw.setFillColor(BLUE)
    draw.setFont(SANS_B, 13)
    draw.drawString(536, PAGE_H - 322, "Exit codes & scripting")
    lines = ["exit 0 → ALLOW (executed)", "exit 3 → WARN (user confirmed)", "exit 2 → BLOCK (refused)", "JSON output for automation"]
    yy = PAGE_H - 350
    for ln in lines:
        draw.setFillColor(BODY)
        draw.setFont(MONO, 11)
        draw.drawString(536, yy, ln)
        yy -= 24


def slide_perf(draw):
    x, y = 72, PAGE_H - 130
    draw.setFillColor(BODY)
    draw.setFont(SANS, 13)
    y = bullet(draw, x, y, "Measured on a Kali VM (scripts/benchmark_latency.py --n 1000):", 14, gap=8)
    rows = [
        ("whitelisted happy path", "~0 ms", GREEN),
        ("feature extraction + rule check", "~0.3 ms mean · ~0.5 ms p95", GREEN),
        ("full pipeline (no LLM resident)", "~2.7 ms mean · ~3 ms p95", GREEN),
        ("full pipeline (LLM pre-warmed)", "tens of ms", AMBER),
    ]
    yy = y - 24
    for name, val, col in rows:
        draw.setFillColor(BODY)
        draw.setFont(SANS, 12)
        draw.drawString(x + 6, yy, "\u25AA  " + name)
        draw.setFillColor(col)
        draw.setFont(MONO_B, 12)
        draw.drawString(x + 360, yy, val)
        yy -= 30
    draw.setFillColor(TITLE)
    draw.setFont(SANS_B, 14)
    draw.drawString(x, yy - 10, "Model training")
    draw.setFillColor(MUTED)
    draw.setFont(SANS, 11)
    draw.drawString(x + 4, yy - 30, "trains on CPU in ~1 s · runs in ~0.1 ms · no GPU · CI retrains on every push")
    yy -= 58
    panel(draw, x, yy - 130, 380, 140, fill=PANEL, line=PURPLE)
    draw.setFillColor(PURPLE)
    draw.setFont(SANS_B, 13)
    draw.drawString(x + 14, yy - 22, "Why GradientBoosting, not deep learning?")
    draw.setFillColor(BODY)
    draw.setFont(SANS, 11)
    yy2 = yy - 44
    for ln in wrap(draw, "Same accuracy at this data scale, trains on a laptop, fully explainable — judges and auditors can read exactly which features fired.", SANS, 11, 350):
        draw.drawString(x + 14, yy2, ln)
        yy2 -= 16
    px = 520
    py = yy - 10
    panel(draw, px, py - 210, 320, 200, fill=PANEL, line=GREEN)
    draw.setFillColor(GREEN)
    draw.setFont(SANS_B, 13)
    draw.drawString(px + 16, py - 24, "Feasibility for target OS")
    feats = [
        "runs on 4 GB RAM / 2 vCPU",
        "BOSS OS (sovereign GNU/Linux) ready",
        "bubblewrap sandbox optional",
        "open-source: Qwen 2.5, scikit-learn, Ollama",
    ]
    yy = py - 52
    for f in feats:
        draw.setFillColor(BODY)
        draw.setFont(SANS, 11)
        draw.drawString(px + 16, yy, "\u25AA  " + f)
        yy -= 30


def slide_risks(draw):
    x, y = 72, PAGE_H - 130
    cols = [270, 90, 340]
    headers = ["Risk", "Severity", "Mitigation"]
    rows = [
        ["Adversarial bypass via encoding", "High", "decodes base64/hex · obfuscation features feed ML · audit-logged"],
        ["LLM unavailable at demo", "Med", "optional layer · rule+ML always answers in <60 ms · status surfaces it"],
        ["False positives", "Med", "whitelist short-circuit · anchored rules · graded WARN not hard block"],
        ["Model drift", "Low", "CI retrains + 5-fold CV printed on every push"],
        ["User disables protection", "Low", "overrides hashed in audit; repeat BLOCK-overrides detectable"],
    ]
    # table header
    tx = x
    draw.setFont(SANS_B, 11)
    for i, h in enumerate(headers):
        draw.setFillColor(BLUE)
        draw.drawString(tx + 4, y, h)
        tx += cols[i]
    y -= 20
    for r in rows:
        tx = x
        for i, c in enumerate(r):
            draw.setFont(SANS_B if i == 1 else SANS, 10)
            draw.setFillColor(TITLE if i == 0 else (RED if i == 1 and c == "High" else (AMBER if i == 1 else BODY)))
            for ln in wrap(draw, c, draw._fontname, 10, cols[i] - 8):
                draw.drawString(tx + 4, y, ln)
                y -= 14
            tx += cols[i]
        y -= 10
    panel(draw, x, PAGE_H - 230, 380, 60, fill=HexColor("#0b1220"), line=GREEN)
    draw.setFillColor(GREEN)
    draw.setFont(SANS_B, 12)
    draw.drawString(x + 14, PAGE_H - 208, "Fail-safe, not fail-open")
    draw.setFillColor(MUTED)
    draw.setFont(SANS, 10)
    draw.drawString(x + 14, PAGE_H - 224, "any layer can only push the decision toward more caution")


def slide_innovation(draw):
    x, y = 72, PAGE_H - 130
    draw.setFillColor(BODY)
    draw.setFont(SANS, 13)
    items = [
        ("Fusion of rules + ML + LLM", "LLM invoked only on demand — near-zero latency and power draw with plain-language explanations."),
        ("Safety-first critical override", "one critical rule match blocks regardless of ML confidence."),
        ("Fully offline, sovereign-first", "no cloud, no egress; deployable on BOSS OS, aligned with India's AtmaNirbhar mission."),
        ("Zero overhead happy path", "whitelist short-circuit removes the false-positive fatigue that kills other tools."),
        ("Privacy-preserving audit", "commands stored only as truncated SHA-256 hashes."),
        ("Safe-alternative suggestions", "every rule carries a constructive \u201Cdo this instead\u201D — teaches secure habits."),
    ]
    yy = y - 10
    for name, desc in items:
        draw.setFillColor(BLUE)
        draw.setFont(SANS_B, 12)
        draw.drawString(x, yy, "\u25AA  " + name)
        draw.setFillColor(BODY)
        draw.setFont(SANS, 11)
        for ln in wrap(draw, desc, SANS, 11, 620):
            draw.drawString(x + 20, yy - 17, ln)
            yy -= 16
        yy -= 8
    panel(draw, x, PAGE_H - 320, 380, 70, fill=PANEL, line=GREEN)
    draw.setFillColor(GREEN)
    draw.setFont(SANS_B, 12)
    draw.drawString(x + 14, PAGE_H - 296, "C-DAC mission alignment")
    draw.setFillColor(BODY)
    draw.setFont(SANS, 10)
    draw.drawString(x + 14, PAGE_H - 314, "open-source · sovereign OS · no foreign cloud AI · improves govt/enterprise security posture")


def slide_roadmap(draw):
    x, y = 72, PAGE_H - 130
    draw.setFillColor(BODY)
    draw.setFont(SANS, 13)
    y = bullet(draw, x, y, "Beyond the hackathon:", 14, gap=10)
    items = [
        ("BOSS OS packaging", ".deb / .rpm for Indian distributions"),
        ("Hindi-first UI", "explanations in more languages"),
        ("Personal allowlists", "per-user adaptive trust"),
        ("Auto-sandbox", "bubblewrap containment for risky-but-required commands"),
        ("Deep integration", "sudo, Docker, IDE terminal hooks"),
    ]
    yy = y - 10
    for name, desc in items:
        draw.setFillColor(TEAL)
        draw.setFont(SANS_B, 12)
        draw.drawString(x, yy, "\u25AA  " + name)
        draw.setFillColor(MUTED)
        draw.setFont(SANS, 11)
        draw.drawString(x + 22, yy, desc)
        yy -= 28
    panel(draw, x, PAGE_H - 330, 380, 80, fill=HexColor("#0b1220"), line=TEAL)
    draw.setFillColor(TITLE)
    draw.setFont(SANS_B, 13)
    draw.drawString(x + 14, PAGE_H - 308, "Status")
    draw.setFillColor(BODY)
    draw.setFont(SANS, 11)
    draw.drawString(x + 14, PAGE_H - 326, "code complete · 44/44 tests · 17/17 demo checks · bash+zsh pty hooks pass")
    draw.setFillColor(TITLE)
    draw.setFont(SANS_B, 26)
    draw.drawString(72, 180, "Thank you")
    draw.setFillColor(MUTED)
    draw.setFont(SANS, 13)
    draw.drawString(72, 155, "Live demo: csengine check \u201Crm -rf /\u201D  →  BLOCK")
    draw.setFillColor(MUTED)
    draw.setFont(SANS, 12)
    draw.drawString(72, 130, "github.com/Adhi-hub07/command-safety-engine")


def main():
    c = canvas.Canvas(OUT, pagesize=(PAGE_W, PAGE_H))
    c.setTitle("Command Safety Engine — C-DAC Secure OS Hackathon 2026")
    c.setAuthor("Adhithya J")

    slide_title(c)
    footer_page(c, 1)
    c.showPage()

    header(c, 1, "The problem", "every terminal keystroke can be the last")
    slide_problem(c)
    footer_page(c, 2)
    c.showPage()

    header(c, 2, "Solution overview", "three-layer defence-in-depth pipeline")
    slide_overview(c)
    footer_page(c, 3)
    c.showPage()

    header(c, 3, "Architecture", "offline, on-device, graded control")
    slide_arch(c)
    footer_page(c, 4)
    c.showPage()

    header(c, 4, "Layer 1 — deterministic rules", "27 MITRE ATT&CK-aligned rule groups")
    slide_rules(c)
    footer_page(c, 5)
    c.showPage()

    header(c, 5, "Layer 2 — machine learning", "generalises to attacks no rule can enumerate")
    slide_ml(c)
    footer_page(c, 6)
    c.showPage()

    header(c, 6, "Layer 3 — LLM explainer", "plain-language answers, still fully offline")
    slide_llm(c)
    footer_page(c, 7)
    c.showPage()

    header(c, 7, "Shell integration & user control", "the hook, the verdicts, the exits")
    slide_integration(c)
    footer_page(c, 8)
    c.showPage()

    header(c, 8, "Performance & feasibility", "measured, not promised")
    slide_perf(c)
    footer_page(c, 9)
    c.showPage()

    header(c, 9, "Risks & mitigations", "honest assessment, engineered in")
    slide_risks(c)
    footer_page(c, 10)
    c.showPage()

    header(c, 10, "Innovation & mission alignment", "why this is different")
    slide_innovation(c)
    footer_page(c, 11)
    c.showPage()

    header(c, 11, "Roadmap & status", "from prototype to sovereign default")
    slide_roadmap(c)
    footer_page(c, 12)
    c.showPage()

    c.save()
    print("wrote", OUT)


if __name__ == "__main__":
    main()
