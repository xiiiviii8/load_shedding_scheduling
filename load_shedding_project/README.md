# Fair Rotational Load-Shedding Scheduling (MiniZinc)

AI Lab final project (CSP track). One MiniZinc model decides which areas lose power in each hour so that

- **C1** critical areas (hospitals) are never cut,
- **C2** the served load never exceeds the hourly supply,
- **C3** no area is off for more than 2 hours in a row,

and then minimises **F1** the outage hours of the worst-hit area, followed by **F2** the total shed load (MWh).
An efficiency-only variant drops F1, so the difference in shed load is the *price of fairness*.

## Layout

```
model/load_shedding.mzn        the model (switches: fair, improved, search)
instances/I01.dzn ... I20.dzn  20 instances, 6x12 up to 120x72 (areas x hours)
instances/instances_summary.csv
scripts/generate_instances.py  regenerates the instances (seeds 1001-1020)
scripts/run_experiments.py     runs every variant x solver x instance, writes results/runs.csv
scripts/validate_schedule.py   solves one instance, prints the grid, re-checks C1-C3 in Python
scripts/make_figures.py        tables and figures used in the slides
results/runs.csv               one row per run (status, best maxOff, shed, times)
```

## Switches

| switch | meaning |
|---|---|
| `fair=true/false` | lexicographic (maxOff, shed) objective, or shed only |
| `improved=true` | I1 symmetry breaking between identical areas + I2 redundant per-hour bounds |
| `search=true` | S1 search annotation (dom_w_deg, try 'on' first, Luby restarts) — CP solvers only |

## Run

Requires the MiniZinc 2.9 bundle (includes Gecode, Chuffed and HiGHS) on `PATH`.

```bash
python scripts/generate_instances.py instances
minizinc --solver highs -D "fair=true;improved=false;search=false" model/load_shedding.mzn instances/I05.dzn
python scripts/validate_schedule.py I03               # demo: grid + independent check
python scripts/run_experiments.py --timeout 60 --jobs 2
python scripts/make_figures.py
```

Runs in `results/runs.csv` (140 total, 60 s limit each, 2-vCPU Linux container):
fair base model on Gecode, Chuffed and HiGHS; improved model (+I) on HiGHS; improved model with search (+IS)
on Gecode and Chuffed; efficiency-only model on HiGHS. HiGHS can overrun the limit on the 72-hour instances,
so the runner kills any run 30 s after the limit and records it as "no schedule".
Re-run on your own machine before presenting and update the environment line on the setup slide.
