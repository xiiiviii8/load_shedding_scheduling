"""Worked-example grid (fair vs efficiency on I01) and a terminal-style demo image."""
import re, sys
sys.path.insert(0, "scripts")
from style import *
from matplotlib.patches import Rectangle

def parse(path):
    rows = []
    for line in open(path):
        m = re.match(r"^([HIR]\d+)\s+(\d+)\s+((?:\s[#.]\s)+)\s+(\d+)$", line.rstrip("\n"))
        if m:
            cells = [c == "#" for c in m.group(3).split()]
            rows.append((m.group(1), int(m.group(2)), cells, int(m.group(4))))
    s = re.search(r"shed load = (\d+) MWh, worst-hit area = (\d+) h", open(path).read())
    return rows, int(s.group(1)), int(s.group(2))

fair = parse("results/demo_I01_fair.txt"); eff = parse("results/demo_I01_eff.txt")
fig, axes = plt.subplots(2, 1, figsize=(5.28, 3.75))
fig.patch.set_facecolor(CARD)
for ax, (rows, shed, mo), title in zip(axes, [fair, eff], ["Fair model (F1, then F2)", "Efficiency only (F2)"]):
    ax.set_xlim(-2.2, 13.6); ax.set_ylim(len(rows) + 0.2, -1.3); ax.axis("off")
    ax.text(-2.2, -0.95, title, fontsize=10, fontweight="bold", color=NAVY, va="center")
    ax.text(13.6, -0.95, f"shed {shed} MWh · worst {mo} h", fontsize=9, color=ORANGE if title.startswith("Eff") else INK, ha="right", va="center")
    for r, (name, load, cells, off) in enumerate(rows):
        ax.text(-0.25, r + 0.5, f"{name}", fontsize=8.5, ha="right", va="center", color=INK, family="JetBrains Mono")
        for h, on in enumerate(cells):
            ax.add_patch(Rectangle((h + 0.06, r + 0.08), 0.88, 0.84, facecolor=GRID if on else ORANGE, edgecolor="none"))
        ax.text(12.35, r + 0.5, str(off), fontsize=8.5, ha="left", va="center",
                color=ORANGE if off == mo and off > 0 else MUTED, fontweight="bold" if off == mo else "normal")
    for h in range(0, 12, 2):
        ax.text(h + 0.5, len(rows) + 0.05, f"{12 + h}", fontsize=7, ha="center", va="top", color=MUTED)
fig.text(0.985, 0.012, "off h", fontsize=7, ha="right", color=MUTED)
plt.subplots_adjust(left=0.01, right=0.99, top=0.97, bottom=0.05, hspace=0.32)
plt.savefig("results/figures/worked_example_I01.png", facecolor=CARD)

# terminal-style demo image
txt = open("results/demo_I03_fair.txt").read().rstrip("\n").split("\n")
lines = ["$ python scripts/validate_schedule.py I03"] + txt
fig = plt.figure(figsize=(5.92, 3.71)); fig.patch.set_facecolor("#141E34")
for i, l in enumerate(lines):
    col = "#F2A65A" if l.startswith("$") else ("#7FD48A" if "PASS" in l else "#E8E6DF")
    fig.text(0.03, 0.955 - i * 0.0525, l, family="JetBrains Mono", fontsize=9.6, color=col, va="top")
plt.savefig("results/figures/demo_terminal.png", facecolor="#141E34")
print("ok")
