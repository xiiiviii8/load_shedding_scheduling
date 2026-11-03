"""Generate 20 load-shedding instances (.dzn) of increasing size.

Area types: 1 = critical (hospital), 2 = industrial, 3 = residential.
The horizon starts at 12:00, so even 12-hour instances include the evening peak.
"""
import math, random, csv, os, sys

SIZES = [  # (areas, hours)
    (6, 12), (8, 12), (10, 12), (12, 24), (15, 24), (18, 24), (20, 24),
    (25, 24), (30, 24), (35, 24), (40, 24), (45, 48), (50, 48), (55, 48),
    (60, 48), (70, 48), (80, 48), (90, 72), (100, 72), (120, 72),
]
TIERS = ["S"] * 7 + ["M"] * 7 + ["L"] * 6
START_HOUR = 12


def shortage(hour_of_day, rng):
    """Fraction of demand that cannot be supplied; highest in the evening peak."""
    peak = math.exp(-((hour_of_day - 20) % 24) ** 2 / 8.0) + math.exp(-((hour_of_day - 20) % 24 - 24) ** 2 / 8.0)
    return 0.12 + 0.18 * peak + rng.uniform(-0.03, 0.03)


def make(idx, n_areas, n_hours):
    rng = random.Random(1000 + idx)
    n_crit = max(1, round(0.08 * n_areas))
    n_ind = round(0.25 * n_areas)
    n_res = n_areas - n_crit - n_ind
    areas = ([(1, rng.choice([2, 3, 4])) for _ in range(n_crit)]
             + [(2, rng.choice([20, 25, 30, 40])) for _ in range(n_ind)]
             + [(3, rng.choice([5, 8, 10, 12, 15])) for _ in range(n_res)])
    areas.sort(key=lambda t: (t[0], -t[1]))
    demand = sum(l for _, l in areas)
    supply = [int(demand * (1 - shortage((START_HOUR + h) % 24, rng))) for h in range(n_hours)]
    return areas, supply, demand


def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    for i, (na, nh) in enumerate(SIZES, start=1):
        areas, supply, demand = make(i, na, nh)
        name = f"I{i:02d}"
        with open(os.path.join(out_dir, name + ".dzn"), "w") as f:
            f.write(f"% {name}: {na} areas x {nh} hours, seed {1000 + i}\n")
            f.write(f"nA = {na};\nnH = {nh};\n")
            f.write("atype = [" + ", ".join(str(t) for t, _ in areas) + "];\n")
            f.write("load = [" + ", ".join(str(l) for _, l in areas) + "];\n")
            f.write("supply = [" + ", ".join(map(str, supply)) + "];\n")
        short = [1 - s / demand for s in supply]
        rows.append(dict(id=name, tier=TIERS[i - 1], areas=na, hours=nh, vars=na * nh,
                         critical=sum(t == 1 for t, _ in areas), industrial=sum(t == 2 for t, _ in areas),
                         residential=sum(t == 3 for t, _ in areas), demand_mw=demand,
                         avg_shortage=round(sum(short) / len(short), 3), max_shortage=round(max(short), 3)))
    with open(os.path.join(out_dir, "instances_summary.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    for r in rows:
        print(r)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "instances")
