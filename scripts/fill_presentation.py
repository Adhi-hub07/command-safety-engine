#!/usr/bin/env python3
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape
from reportlab.lib.colors import Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

D="Calibri"; DB="Calibri-Bold"; SER="Cambria-Bold"
pdfmetrics.registerFont(TTFont(D, "/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf"))
pdfmetrics.registerFont(TTFont(DB, "/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf"))
pdfmetrics.registerFont(TTFont(SER, "/usr/share/fonts/truetype/crosextra/Caladea-Bold.ttf"))

PAGE_W, PAGE_H = 960, 540
GRAY  = Color(0.6, 0.6, 0.6)
DGRAY = Color(0.349, 0.349, 0.349)
BLACK = Color(0,0,0)
DARK  = Color(0.102, 0.102, 0.102)
RI = 905

ASC = {D: 0.711, DB: 0.711, SER: 0.694}   # empirically calibrated (ink top == requested top)

def topdraw(c, x, top, text, font, size, color):
    y = PAGE_H - top - ASC[font]*size
    c.setFont(font, size); c.setFillColor(color)
    c.drawString(x, y, text)

def wrap(c, text, font, size, maxw):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if c.stringWidth(t, font, size) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def bullet(c, x, top, text, size=9.0, font=D, color=DARK, maxw=None, lead=2.2):
    maxw = maxw or (RI - x)
    pad = c.stringWidth("\u2022  ", font, size)
    lines = wrap(c, text, font, size, maxw - pad)
    for i, ln in enumerate(lines):
        if i == 0:
            topdraw(c, x, top, "\u2022  " + ln, font, size, color)
        else:
            topdraw(c, x, top, ln, font, size, color)
        top += size + lead
    return top

def cover(c, name, track, ref):
    topdraw(c, 66, 218, "PROJECT PRESENTATION", D, 13, DGRAY)
    topdraw(c, 68, 260, "[ %s ]" % name, DB, 32, BLACK)
    topdraw(c, 67, 309, "[ %s ]  \u00b7  [ %s ]" % (track, ref), D, 13, GRAY)
    c.showPage()

LABELS = [156, 202, 249]

def content(c, num, title, sections):
    topdraw(c, 65, 53, num, DB, 13, GRAY)
    topdraw(c, 66, 80, title, SER, 32, BLACK)
    for i, (lab, text) in enumerate(sections):
        labtop = LABELS[i]
        topdraw(c, 66, labtop, lab, SER, 20, DARK)
        bullet(c, 66, labtop + 24, text)
    c.showPage()

def main():
    import os, sys
    repo_docs = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(repo_docs, "presentation-stage2-template.pdf")
    c = canvas.Canvas(out, pagesize=landscape((PAGE_W, PAGE_H)))
    c.setTitle("SafeShell - Project Presentation")
    c.setAuthor("Adhithya J")

    cover(c,
          "SOLO ARC \u00b7 SafeShell \u2014 Command Safety Engine",
          "Track 1 \u2014 AI at Application Level",
          "Ref Code")

    content(c, "01", "Design Choice", [
        ("Problem Statement",
         "The shell has no safety net: rm -rf /, dd of=/dev/sda or mkfs "
         "can destroy data in an instant. Users need a layer that "
         "understands command intent before execution, detects risky ops, "
         "explains impact, and suggests safer alternatives."),
        ("Design Approach",
         "Intercept every command pre-execution; classify with three "
         "cross-checking layers (deterministic rules, ML classifier, local "
         "on-device LLM) and hard-block destructive ops. Wrap risky "
         "commands in a transaction: snapshot files, simulate in a sandbox, "
         "keep an undo plan so damage always rolls back."),
        ("Reasoning",
         "Every layer can fail: rules give guaranteed hard-blocks, ML "
         "catches novel vectors, the LLM explains ambiguous ~0.65-confidence "
         "cases in plain language. Transactions turn detection into "
         "reversibility - users stay in control instead of losing data."),
    ])

    content(c, "02", "Architecture", [
        ("Architecture Choices",
         "Three analysis layers (rule engine, ML, LLM) agree on a verdict. "
         "A SafeShell transaction layer then attaches to every WARN "
         "command: extracts target paths, snapshots content + metadata "
         "under ~/.csengine/tx/<id> (sha256-tagged trees), builds an undo "
         "plan (static + LLM). Simulation runs the command in a bubblewrap "
         "sandbox and diffs the filesystem before anything real executes."),
        ("Reasoning",
         "Modular design keeps the fast path (rules + ML, ~0.4 ms) on most "
         "traffic while the LLM reasons only about ambiguous commands. "
         "Transaction/simulation layers are purely additive - shell "
         "behaviour is unchanged, only safety is added. Offline-first "
         "design works on air-gapped systems like BOSS OS."),
    ])

    content(c, "03", "Technology Choices", [
        ("Technologies Used",
         "Python 3.13 + scikit-learn GradientBoosting (Test Acc 0.8225, "
         "Macro-F1 0.7906). Ollama + Qwen 2.5-3B q4 for on-device "
         "explanations. bash DEBUG-trap preexec + zsh Enter-key widget for "
         "blocking hooks. bubblewrap sandbox, sha256+JSON transaction "
         "store, real-PTY end-to-end test harnesses."),
        ("Reasoning",
         "Fully on-device - no cloud API, matching the offline/sovereign "
         "security requirement. GradientBoosting wins on macro-F1 while the "
         "27-rule engine keeps destructive-class recall competitive. "
         "Model-swappable Ollama backend; bwrap needs no kernel changes, so "
         "it runs on stock Ubuntu, Debian and BOSS OS."),
    ])

    content(c, "04", "Demo", [
        ("Demo Walkthrough",
         "1) rm -rf /, mkfs and dd-on-/dev/sda BLOCKED deterministically "
         "(exit 2, audit logged). 2) chmod -R 777 needs confirmation + "
         "shows a simulation diff, then a one-command undo. 3) An obfuscated "
         "hex/base64 command is decoded and the on-device model explains "
         "the hidden payload. 4) 17/17 verification script runs on camera."),
        ("Key Features",
         "3-layer hybrid detection (rules + ML + local LLM) \u2022 "
         "transactional undo with AI-generated plans \u2022 sandbox "
         "simulation of exact impact \u2022 live \u2018thinking\u2019 notice \u2022 ~0.4 ms "
         "rule+ML path \u2022 fully offline \u2022 Ubuntu / Debian / BOSS OS."),
    ])

    c.save()
    print("wrote", out)

main()
