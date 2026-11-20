"""Step 3: ghost jams - throughput lost to behaviour alone, with NO bottleneck.

A one-lane ring road (3 km) with identical cars. No signals, no junctions,
no width change. Only driver behaviour differs between runs.

Model: Nagel-Schreckenberg cellular automaton (1992), the textbook traffic
micro-simulation, with the "slow-to-start" rule (Barlovic et al. 1998), which
reproduces the capacity drop seen on real roads. Cell = 7.5 m, step = 1 s,
top speed = 2 cells/s (54 km/h).

Each second, every car:
  1. speeds up by 1 (up to the top speed)
  2. slows down to the gap in front (no crashing)
  3. randomly brakes by 1 with probability p_brake  (hesitation, phone, honking, swerving)
     a car that was STOPPED restarts late with probability p_restart
  4. moves
Plus, optionally, random "kerbside stops": a car halts in the lane for some
seconds (bus/auto picking up, someone parking) - like the DPR photos show.

Validated against Sugiyama et al. (2008): 22 cars on a 230 m ring formed a
jam with no cause; here the same thing happens at the same density.

Run:  python ghost_jam.py   -> prints table, writes outputs/ghost_jam.csv
"""

import csv
import os

import numpy as np

CELLS = 400            # 400 x 7.5 m = 3 km ring
VMAX = 2               # cells per second = 54 km/h
STEPS, WARMUP = 3600, 600

BEHAVIOURS = {
    # name: (p_brake, p_restart, kerbside stops per km per hour, stop seconds)
    "Disciplined (smooth, attentive)":       (0.05, 0.05, 0, 0),
    "Erratic driving (random braking)":      (0.25, 0.25, 0, 0),
    "Erratic + slow restarts":               (0.25, 0.60, 0, 0),
    "Erratic + slow restarts + kerb stops":  (0.25, 0.60, 30, 20),
}


def simulate(density, p_brake, p_restart, stops_per_km_h, stop_s, seed=1, record=False):
    """Return (flow veh/h, space-time array or None)."""
    rng = np.random.default_rng(seed)
    n = max(1, int(density * CELLS))
    pos = np.sort(rng.choice(CELLS, n, replace=False))
    vel = np.zeros(n, dtype=int)
    hold = np.zeros(n, dtype=int)               # seconds left in a kerbside stop
    p_stop = stops_per_km_h * (CELLS * 7.5 / 1000) / 3600 / n  # per car per second
    passed, history = 0, []
    for t in range(STEPS):
        gap = (np.roll(pos, -1) - pos - 1) % CELLS
        if n == 1:
            gap[:] = CELLS - 1
        p = np.where(vel == 0, p_restart, p_brake)
        vel = np.minimum(vel + 1, VMAX)
        vel = np.minimum(vel, gap)
        vel = np.where((rng.random(n) < p) & (vel > 0), vel - 1, vel)
        if stop_s:
            new = (rng.random(n) < p_stop) & (hold == 0)
            hold[new] = stop_s
            vel[hold > 0] = 0
            hold[hold > 0] -= 1
        new_pos = pos + vel
        if t >= WARMUP:
            passed += np.sum(new_pos >= CELLS)   # cars crossing the "counter" at cell 0
            if record and t < WARMUP + 300:
                row = np.zeros(CELLS)
                row[pos] = 1
                history.append(row)
        pos = new_pos % CELLS
        order = np.argsort(pos)
        pos, vel, hold = pos[order], vel[order], hold[order]
    flow = passed / (STEPS - WARMUP) * 3600
    return flow, (np.array(history) if record else None)


def fundamental_diagram():
    densities = np.round(np.arange(0.04, 0.62, 0.02), 2)
    rows = []
    for name, params in BEHAVIOURS.items():
        for d in densities:
            flow = np.mean([simulate(d, *params, seed=s)[0] for s in range(3)])
            rows.append(dict(behaviour=name, density_veh_km=round(d * 1000 / 7.5),
                             flow_veh_h=round(flow)))
    return rows


def main():
    rows = fundamental_diagram()
    os.makedirs("outputs", exist_ok=True)
    with open("outputs/ghost_jam.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    best = max(r["flow_veh_h"] for r in rows if r["behaviour"].startswith("Disciplined"))
    print("Ghost-jam simulation: same 1-lane road, no bottleneck, behaviour only")
    for name in BEHAVIOURS:
        q = max(r["flow_veh_h"] for r in rows if r["behaviour"] == name)
        print(f"  {name:40s} max throughput {q:5d} veh/h/lane  ({100 * q / best:3.0f}% of disciplined)")


if __name__ == "__main__":
    main()
