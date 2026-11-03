"""Run every (model variant, solver, instance) combination and save one CSV row per run.

Usage: python scripts/run_experiments.py [--timeout 60] [--jobs 2] [--out results/runs.csv]
Requires the `minizinc` executable on PATH (MiniZinc 2.9 bundle includes all solvers used).
"""
import argparse, csv, json, os, signal, subprocess, time
from concurrent.futures import ThreadPoolExecutor

MODEL = "model/load_shedding.mzn"
SOLVERS = {"Gecode": "gecode", "Chuffed": "chuffed", "HiGHS": "highs"}
VARIANTS = {  # name: (fair, improved, search)
    "fair-base": (True, False, False),
    "fair-improved": (True, True, False),
    "fair-improved-search": (True, True, True),   # search annotation only affects CP solvers
    "efficiency": (False, True, False),           # no fairness objective: reference for price of fairness
}
# which solvers each variant is run with
PLAN = {
    "fair-base": ["Gecode", "Chuffed", "HiGHS"],
    "fair-improved": ["HiGHS"],
    "fair-improved-search": ["Gecode", "Chuffed"],
    "efficiency": ["HiGHS"],
}


def run_one(variant, solver, inst, timeout_s):
    fair, improved, search = VARIANTS[variant]
    cmd = ["minizinc", "--solver", SOLVERS[solver], "-p", "1", "--json-stream", "-i", "-s",
           "--output-time", "--time-limit", str(int(timeout_s * 1000)),
           "-D", f"fair={str(fair).lower()};improved={str(improved).lower()};search={str(search).lower()}",
           MODEL, f"instances/{inst}.dzn"]
    t0 = time.time()
    # some backends overrun --time-limit on large models; kill the whole process group after a grace period
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        stdout, _ = proc.communicate(timeout=timeout_s + 30)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        stdout, _ = proc.communicate()
    wall = time.time() - t0
    best, best_t, status, stats = None, None, "UNKNOWN", {}
    for line in stdout.splitlines():
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if msg.get("type") == "solution":
            best = json.loads(msg["output"]["raw"])
            best_t = msg.get("time")
            if status == "UNKNOWN":
                status = "SATISFIED"
        elif msg.get("type") == "status":
            status = msg["status"]
        elif msg.get("type") == "statistics":
            stats.update(msg["statistics"])
        elif msg.get("type") == "error":
            status = "ERROR"
    return dict(variant=variant, solver=solver, instance=inst, status=status,
                optimal=int(status == "OPTIMAL_SOLUTION"),
                shed=best["shed"] if best else "", max_off=best["maxOff"] if best else "",
                obj=best["obj"] if best else "",
                wall_s=round(wall, 3), last_sol_s=round(best_t / 1000, 3) if best_t is not None else "",
                solve_s=round(float(stats.get("solveTime", 0)), 3),
                flat_s=round(float(stats.get("flatTime", 0)), 3),
                nodes=stats.get("nodes", ""), failures=stats.get("failures", ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=float, default=60)
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--out", default="results/runs.csv")
    ap.add_argument("--resume", action="store_true", help="append to --out, skipping runs already in it")
    ap.add_argument("--instances", default=",".join(f"I{i:02d}" for i in range(1, 21)))
    ap.add_argument("--variants", default=",".join(VARIANTS))
    a = ap.parse_args()
    tasks = [(v, s, i) for v in a.variants.split(",") for s in PLAN[v]
             for i in a.instances.split(",")]
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    done = set()
    if a.resume and os.path.exists(a.out):
        done = {(r["variant"], r["solver"], r["instance"]) for r in csv.DictReader(open(a.out))}
        tasks = [t for t in tasks if t not in done]
    with open(a.out, "a" if done else "w", newline="") as f, ThreadPoolExecutor(a.jobs) as ex:
        w = None
        for row in ex.map(lambda t: run_one(*t, a.timeout), tasks):
            if w is None:
                w = csv.DictWriter(f, fieldnames=list(row.keys()))
                if not done:
                    w.writeheader()
            w.writerow(row); f.flush()
            print(row["variant"], row["solver"], row["instance"], row["status"],
                  row["shed"], row["max_off"], row["wall_s"], flush=True)


if __name__ == "__main__":
    main()
