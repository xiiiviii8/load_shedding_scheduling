"""Summarise results/runs.csv into tables and figures for the slides.

Writes results/summary.json (numbers used on the slides) and results/figures/*.png.
"""
import csv, json, sys
from collections import defaultdict
sys.path.insert(0, "scripts")
from style import *

TIMEOUT = 60.0
runs = list(csv.DictReader(open("results/runs.csv")))
inst = list(csv.DictReader(open("instances/instances_summary.csv")))
IDS = [r["id"] for r in inst]
TIER = {r["id"]: r["tier"] for r in inst}

R = {}
for r in runs:
    R[(r["variant"], r["solver"], r["instance"])] = r

def val(r):
    """(maxOff, shed) of the best schedule a run found, or None."""
    if r is None or r["max_off"] == "":
        return None
    return (int(r["max_off"]), int(r["shed"]))

def finish_time(r):
    return float(r["wall_s"]) if r["optimal"] == "1" else None

CONFIGS = [  # (label, variant, solver)
    ("Gecode", "fair-base", "Gecode"),
    ("Chuffed", "fair-base", "Chuffed"),
    ("HiGHS", "fair-base", "HiGHS"),
    ("HiGHS +I", "fair-improved", "HiGHS"),
    ("Gecode +I+S", "fair-improved-search", "Gecode"),
    ("Chuffed +I+S", "fair-improved-search", "Chuffed"),
]

# best known fair value per instance, and whether it is proven optimal
best, proven = {}, {}
for i in IDS:
    # every schedule is feasible for every variant, so efficiency-only schedules also count
    cands = [val(R.get((v, s, i))) for _, v, s in CONFIGS] + [val(R.get(("efficiency", "HiGHS", i)))]
    cands = [c for c in cands if c is not None]
    best[i] = min(cands) if cands else None
    proven[i] = any(R.get((v, s, i), {}).get("optimal") == "1" for _, v, s in CONFIGS)

summary = {"configs": {}, "instances": {}, "tiers": {}}
for label, v, s in CONFIGS:
    rows = [R.get((v, s, i)) for i in IDS]
    n_opt = sum(1 for r in rows if r and r["optimal"] == "1")
    n_found = sum(1 for r in rows if val(r) is not None)
    n_best = sum(1 for i, r in zip(IDS, rows) if val(r) is not None and val(r) == best[i])
    par1 = sum((float(r["wall_s"]) if r and r["optimal"] == "1" else TIMEOUT) for r in rows) / len(IDS)
    gaps = [val(r)[0] - best[i][0] for i, r in zip(IDS, rows) if val(r) is not None]
    summary["configs"][label] = dict(variant=v, solver=s, proven_optimal=n_opt, found=n_found,
                                     best_known=n_best, par1=round(par1, 2),
                                     mean_extra_hours=round(sum(gaps) / len(gaps), 2) if gaps else None,
                                     max_off=[val(r)[0] if val(r) else None for r in rows],
                                     optimal=[bool(r and r["optimal"] == "1") for r in rows],
                                     time=[round(float(r["wall_s"]), 2) if r else None for r in rows])

# price of fairness: fair optimum (best known) vs efficiency-only (HiGHS)
for i in IDS:
    e = R.get(("efficiency", "HiGHS", i))
    ev = val(e)
    summary["instances"][i] = dict(
        tier=TIER[i], best_fair=best[i], fair_proven=proven[i],
        eff=ev, eff_proven=bool(e and e["optimal"] == "1"),
        price_pct=round(100 * (best[i][1] - ev[1]) / ev[1], 2) if best[i] and ev else None)
for t in "SML":
    ids = [i for i in IDS if TIER[i] == t]
    pairs = [i for i in ids if summary["instances"][i]["eff"] and
             (val(R.get(("fair-base", "HiGHS", i))) or val(R.get(("fair-improved", "HiGHS", i))))]
    both = [i for i in pairs if summary["instances"][i]["fair_proven"] and summary["instances"][i]["eff_proven"]]
    if pairs:
        fs = sum(best[i][1] for i in pairs); es = sum(summary["instances"][i]["eff"][1] for i in pairs)
        fm = sum(best[i][0] for i in pairs) / len(pairs); em = sum(summary["instances"][i]["eff"][0] for i in pairs) / len(pairs)
        summary["tiers"][t] = dict(ids=ids, pairs=pairs, n_both_proven=len(both), fair_shed=fs, eff_shed=es,
                                   price_pct=round(100 * (fs - es) / es, 2),
                                   fair_maxoff=round(fm, 1), eff_maxoff=round(em, 1))
    else:
        summary["tiers"][t] = dict(ids=ids, pairs=[], n_both_proven=0)
# extra comparisons used in the discussion
def cmp_shed(a, b):
    """instances where both configs found a schedule: (count a has lower shed, count b lower, mean % change a->b)."""
    out = []
    for i in IDS:
        va, vb = val(R.get(a + (i,))), val(R.get(b + (i,)))
        if va and vb:
            out.append((va[1], vb[1]))
    return dict(n=len(out), b_lower=sum(1 for x, y in out if y < x), a_lower=sum(1 for x, y in out if x < y),
                mean_change_pct=round(sum(100 * (y - x) / x for x, y in out) / len(out), 1) if out else None)
summary["extra"] = {
    "highs_base_vs_I_shed": cmp_shed(("fair-base", "HiGHS"), ("fair-improved", "HiGHS")),
    "gecode_base_vs_IS_shed": cmp_shed(("fair-base", "Gecode"), ("fair-improved-search", "Gecode")),
    "eff_maxoff_I18_I20": [val(R.get(("efficiency", "HiGHS", i))) for i in ("I18", "I19", "I20")],
    "highs_proof_times": [round(float(R[("fair-base", "HiGHS", i)]["wall_s"]), 2) for i in IDS if R[("fair-base", "HiGHS", i)]["optimal"] == "1"],
    "best": {i: best[i] for i in IDS},
}
json.dump(summary, open("results/summary.json", "w"), indent=1)

# ---------- Figure 1: worst-hit outage hours found within 60 s ----------
fig, ax = plt.subplots(figsize=(11.56, 3.89))
fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
x = list(range(1, 21))
lines = [("Gecode", GRAY, (0, (5, 3)), 1.6, "o"),
         ("Chuffed", ORANGE_L, (0, (1, 2)), 2.0, "s"),
         ("Gecode +I+S", BLUE, "-", 1.6, "D"),
         ("Chuffed +I+S", ORANGE, "-", 1.6, "^"),
         ("HiGHS", NAVY, "-", 2.8, "o")]
for label, col, ls, lw, mk in lines:
    c = summary["configs"][label]
    ys = [m if m is not None else float("nan") for m in c["max_off"]]  # gaps break the line
    ax.plot(x, ys, color=col, linestyle=ls, linewidth=lw, label=label.replace(" +I+S", " +IS"), marker=".", markersize=4, zorder=3 if label == "HiGHS" else 2)
    opt_x = [xx for xx, m, o in zip(x, c["max_off"], c["optimal"]) if o]
    opt_y = [m for m, o in zip(c["max_off"], c["optimal"]) if o]
    ax.scatter(opt_x, opt_y, s=26, color=col, marker=mk, zorder=4)
    miss = [xx for xx, m in zip(x, c["max_off"]) if m is None]
    if miss:
        ax.scatter(miss, [0.4] * len(miss), marker="x", s=30, color=col, zorder=4)
eff = [val(R.get(("efficiency", "HiGHS", i))) for i in IDS]
ax.scatter([xx for xx, e in zip(x, eff) if e], [e[0] for e in eff if e], s=30, facecolors="none",
           edgecolors=MUTED, linewidths=1.2, label="Efficiency-only (HiGHS)", zorder=5)
ax.set_xticks([1, 5, 10, 15, 20]); ax.set_xticklabels(["I01", "I05", "I10", "I15", "I20"])
ax.set_xlim(0.5, 20.5); ax.set_ylim(0, None)
ax.set_ylabel("worst-hit area: hours off")
ax.grid(axis="y", color=GRID, linewidth=0.8); ax.set_axisbelow(True)
leg = ax.legend(loc="upper left", ncol=3, frameon=True, fontsize=9.5)
ax.set_ylim(0, 52)
leg.get_frame().set_facecolor(CARD); leg.get_frame().set_edgecolor(GRID)
plt.tight_layout()
plt.savefig("results/figures/fig1_quality.png", facecolor=PAPER)
print(json.dumps({k: {kk: vv for kk, vv in c.items() if kk in ("proven_optimal", "found", "best_known", "par1", "mean_extra_hours")} for k, c in summary["configs"].items()}, indent=0))
print(json.dumps({t: {k: v for k, v in d.items() if k != "ids"} for t, d in summary["tiers"].items()}))
print(json.dumps(summary["extra"]))
