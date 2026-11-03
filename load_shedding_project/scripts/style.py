"""Shared figure style matching the presentation template."""
import glob, os
import matplotlib
matplotlib.use("Agg")
from matplotlib import font_manager
for f in glob.glob(os.path.expanduser("~/.fonts/*.ttf")):
    font_manager.fontManager.addfont(f)
import matplotlib.pyplot as plt

NAVY, INK, MUTED, GRID = "#14213D", "#2A3342", "#6B7280", "#D9D5CA"
ORANGE, ORANGE_L, BLUE, PAPER, CARD = "#B35A12", "#F2A65A", "#2F6FB0", "#F7F6F2", "#FFFFFF"
plt.rcParams.update({
    "font.family": "IBM Plex Sans", "font.size": 11, "text.color": INK,
    "axes.edgecolor": GRID, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 220,
})
