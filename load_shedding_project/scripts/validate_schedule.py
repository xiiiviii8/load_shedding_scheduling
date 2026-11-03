"""Solve one instance, print the schedule as a grid, and check it independently.

Usage: python scripts/validate_schedule.py I03 [--solver highs] [--fair true|false] [--time 60]

The checker re-reads the .dzn data and verifies C1-C3 itself, so a bug in the
MiniZinc model cannot hide behind the solver's own report.
"""
import argparse, json, re, subprocess, sys

TYPE_TAG = {1: "H", 2: "I", 3: "R"}  # hospital / industrial / residential


def read_dzn(path):
    text = open(path).read()
    def arr(name):
        return [int(x) for x in re.search(name + r"\s*=\s*\[([^\]]*)\]", text).group(1).split(",")]
    def num(name):
        return int(re.search(name + r"\s*=\s*(\d+)", text).group(1))
    return dict(nA=num("nA"), nH=num("nH"), atype=arr("atype"), load=arr("load"), supply=arr("supply"))


def solve(inst, solver, fair, time_s):
    cmd = ["minizinc", "--solver", solver, "-p", "1", "--output-mode", "json",
           "--time-limit", str(time_s * 1000),
           "-D", f"fair={fair};improved=true;search=true",
           "model/load_shedding.mzn", f"instances/{inst}.dzn"]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    blocks = [b for b in out.split("----------") if b.strip().startswith("{")]
    if not blocks:
        sys.exit("no solution found:\n" + out)
    return json.loads(blocks[-1])["on"], "==========" in out


def check(d, on, K=2):
    errors = []
    for a in range(d["nA"]):
        if d["atype"][a] == 1 and not all(on[a]):
            errors.append(f"C1 violated: critical area {a + 1} is cut")
    for h in range(d["nH"]):
        served = sum(d["load"][a] for a in range(d["nA"]) if on[a][h])
        if served > d["supply"][h]:
            errors.append(f"C2 violated at hour {h + 1}: {served} > {d['supply'][h]}")
    for a in range(d["nA"]):
        run = 0
        for h in range(d["nH"]):
            run = 0 if on[a][h] else run + 1
            if run > K:
                errors.append(f"C3 violated: area {a + 1} off {run} hours in a row ending at hour {h + 1}")
    off = [d["nH"] - sum(row) for row in on]
    shed = sum(d["load"][a] * off[a] for a in range(d["nA"]))
    max_off = max(off[a] for a in range(d["nA"]) if d["atype"][a] != 1)
    return errors, off, shed, max_off


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("instance")
    ap.add_argument("--solver", default="highs")
    ap.add_argument("--fair", default="true")
    ap.add_argument("--time", type=int, default=60)
    a = ap.parse_args()
    d = read_dzn(f"instances/{a.instance}.dzn")
    on, optimal = solve(a.instance, a.solver, a.fair, a.time)
    errors, off, shed, max_off = check(d, on)
    start = 12
    print(f"{a.instance}: {d['nA']} areas x {d['nH']} hours, solver={a.solver}, fair={a.fair}")
    print("area  load " + "".join(f"{(start + h) % 24:02d}"[-2:] + " " for h in range(d["nH"])) + " off")
    for i in range(d["nA"]):
        tag = f"{TYPE_TAG[d['atype'][i]]}{i + 1:<3}"
        cells = "".join(" # " if on[i][h] else " . " for h in range(d["nH"]))
        print(f"{tag:5} {d['load'][i]:4} {cells} {off[i]:3}")
    print("# = power on, . = power off")
    print(f"shed load = {shed} MWh, worst-hit area = {max_off} h off, "
          f"{'proven optimal' if optimal else 'best found within limit'}")
    print("checks C1-C3:", "PASS" if not errors else "FAIL")
    for e in errors[:10]:
        print("  " + e)


if __name__ == "__main__":
    main()
