# Fair Rotational Load-Shedding Scheduling (MiniZinc)

AI Lab final project (CSP track) · CSE-3214 Artificial Intelligence Laboratory · BAUET

**Team:** Kazi Sadat Nur (0812320205101019) · Nafiu Nahin Nuhana (0812320105101040) · Riasa Arfin (0812320105101046)

When electricity supply is short, which areas should lose power in each hour so that the cuts are fair?
One MiniZinc model decides an on/off value for every area and hour so that

- **C1** critical areas (hospitals) are never cut,
- **C2** the served load never exceeds the hourly supply,
- **C3** no area is off for more than 2 hours in a row,

and then minimises **F1** the outage hours of the worst-hit area, followed by **F2** the total shed load (MWh).
An efficiency-only variant drops F1, so the difference in shed load is the *price of fairness*.

## Main results

- **HiGHS (MIP)** proved the optimum on I01–I07 and found the fairest schedules up to I17
  (worst-hit area off 4 of 24 or 8 of 48 hours), but returned no schedule for the 72-hour instances I18–I20.
- **Gecode and Chuffed (CP)** left the worst-hit area off 3–4× longer. Default Chuffed found a schedule
  on only 4 of 20 instances; with the search annotation S1 it found one on all 20.
- **Price of fairness:** on the small instances, where both models are proven optimal, fairness costs
  2.2% more shed load and halves the worst-hit area's outage (8.0 → 3.9 hours on average).

## Layout

```
model/load_shedding.mzn          the model (switches: fair, improved, search)
instances/I01.dzn ... I20.dzn    20 instances, 6x12 up to 120x72 (areas x hours)
instances/instances_summary.csv  size, demand and shortfall of each instance
scripts/generate_instances.py    regenerates the instances (seeds 1001-1020)
scripts/run_experiments.py       runs every variant x solver x instance, writes results/runs.csv
scripts/validate_schedule.py     solves one instance, prints the grid, re-checks C1-C3 in Python
scripts/make_figures.py          summary numbers (results/summary.json) and the fairness line chart
scripts/make_example_figures.py  worked-example grid (I01) and demo terminal image
scripts/style.py                 shared colours and fonts for the figures
results/runs.csv                 one row per run (status, best maxOff, shed load, times)
results/summary.json             every number quoted in the presentation
results/demo_*.txt               validator output for the worked example and the demo
results/figures/                 PNG versions of the charts
requirements.txt                 Python dependency and the MiniZinc download link
```

## Model switches

Pass them with `-D`, for example `-D "fair=true;improved=false;search=false"`.

| switch | meaning |
|---|---|
| `fair=true/false` | lexicographic (maxOff, shed) objective, or shed load only |
| `improved=true/false` | I1 symmetry breaking between identical areas + I2 redundant per-hour bounds |
| `search=true/false` | S1 search annotation (dom_w_deg, try 'on' first, Luby restarts), used by CP solvers only |

## How to run

Requirements: the MiniZinc 2.10 bundle (includes Gecode, Chuffed and HiGHS) on `PATH`,
and Python 3 with `pip install -r requirements.txt` for the figure scripts. Run every command from the project folder.

```bash
python scripts/validate_schedule.py I03               # demo: solve, print the grid, check C1-C3
python scripts/generate_instances.py instances        # regenerate the 20 instances
minizinc --solver highs -D "fair=true;improved=false;search=false" model/load_shedding.mzn instances/I05.dzn
python scripts/run_experiments.py --timeout 60 --jobs 2
python scripts/make_figures.py
python scripts/make_example_figures.py
```

The full experiment (140 runs, 60 s limit each, 2 parallel jobs) takes about 75 minutes.

## Experiment details

- Variants: fair base model on Gecode, Chuffed and HiGHS; improved model (+I) on HiGHS;
  improved model with search (+IS) on Gecode and Chuffed; efficiency-only model on HiGHS.
- One run per variant × solver × instance, one thread per run. When a run hits the limit, the best schedule found so far is kept.
- HiGHS can overrun the limit on the 72-hour instances, so the runner stops any run 30 s after the limit and records it as "no schedule".
- Columns `nodes` and `failures` in `runs.csv` are empty for runs stopped by the time limit,
  because the solvers only report search statistics when they finish.
- The included `results/runs.csv` was produced on an HP 15s laptop with an AMD Ryzen 5 5500U processor, 8 GB RAM, Windows 11, and MiniZinc 2.10.1 (one thread per run).
  Rerunning on other hardware gives slightly different times and best-found values.
