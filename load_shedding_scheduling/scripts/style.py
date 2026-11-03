"""Shared figure style matching the presentation template."""
import glob, os
import matplotlib
matplotlib.use("Agg")
from matplotlib import font_manager
for f in glob.glob(os.path.expanduser("~/.fonts/*.ttf")):
    font_manager.fontManager.addfont(f)
import matplotlib.pyplot as plt

# use the presentation fonts when installed, otherwise matplotlib's built-in DejaVu fonts (no warnings)
_installed = {f.name for f in font_manager.fontManager.ttflist}
SANS = "IBM Plex Sans" if "IBM Plex Sans" in _installed else "DejaVu Sans"
MONO = "JetBrains Mono" if "JetBrains Mono" in _installed else "DejaVu Sans Mono"

# lavender palette: plum for emphasis, raspberry / rose accents, violet secondary
NAVY, INK, MUTED, GRID = "#2E1A4F", "#2E2742", "#6F6688", "#D9CFEC"
ORANGE, ORANGE_L, BLUE, PAPER, CARD = "#A6376F", "#D06A9A", "#6B4FC2", "#F3EFFC", "#FFFFFF"
GRAY, CODE_BG, CODE_FG, CODE_HI = "#9C95AF", "#24153D", "#ECE6F7", "#F0A9CB"
plt.rcParams.update({
    "font.family": SANS, "font.size": 11, "text.color": INK,
    "axes.edgecolor": GRID, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 220,
})
