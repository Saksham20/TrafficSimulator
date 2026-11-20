"""Step 5: a corridor segment by segment.  CORRIDOR=silk_board (default) or mysore_road.

For every segment, peak hour, both directions together:

  TODAY capacity (PCU/h)
      = IRC arterial capacity for its lanes  x  friction penalty here
    IRC arterial: 4-lane 3,600 / 0.7 = 5,143 PCU/h, i.e. 1,286 PCU/h per lane
    (6-lane 7,714 -> 1,286/lane; 8-lane 10,286 -> 1,286/lane). Same per-lane value.
    friction penalty here = product over the 4 packages of
        (package factor at the DPR count site) ^ (severity here)
    so segment 3 (100 Ft Rd, where the DPR counted) reproduces 3,996 PCU/h exactly.

  BEST capacity = IRC arterial capacity for its lanes (all frictions fixed).
      + where a 3-5 m paver strip exists (segments 3, 5, 6) it becomes a bus /
        3rd lane: shown separately as "best + spare strip".

  FLYOVER capacity = TODAY capacity at grade (nothing else fixed)
                     + flyover lanes x 1,800 PCU/h (clean elevated lane).

  What gets through the whole corridor = the SMALLEST capacity along it
  (a chain is as strong as its weakest link). Per-segment numbers show where.

  Travel time per segment: Google 6 am time scaled by the same BPR curve as
  model.py: t = t6 x (1 + A x (demand/capacity)^2), with A per segment set so
  that today's 10 am Google time is reproduced.

  Time saved assumes the SAME traffic as today (no growth, no extra trips
  attracted by new road space). It is the immediate effect.

Run:  CORRIDOR=silk_board python segment_model.py   -> explainer_<corridor>/segments.csv, trip_times.csv
"""

import csv
import math
from collections import defaultdict

import importlib
import os

import inputs_silk_board as SB  # K and the friction factors are calibrated on Silk Board's real count

NAME = os.environ.get("CORRIDOR", "silk_board")
I = importlib.import_module(f"inputs_{NAME}")
SG = importlib.import_module(f"segments_{NAME}")
SEGMENTS, L = SG.SEGMENTS, SG.LABELS
OUT_DIR = f"explainer_{NAME}"                 # everything for the plain-language explainer
PER_LANE_BEST = SB.BEST_CAPACITY / 4          # 1,286 PCU/h per lane (IRC arterial, same for 4/6/8 lanes)
FLYOVER_PCU_PER_LANE = SB.FLYOVER_PCU_PER_LANE  # 1,800
K = math.log(SB.TODAY_CAPACITY / SB.BEST_CAPACITY) / math.log(math.prod(x["today"] for x in SB.INTERVENTIONS))

# factor of each package at the DPR count site (segment 3): product of its members ^ K
PACKAGE = {"Enforce": "E", "Design": "D", "Signals": "S", "Maintain": "M"}
SITE_FACTOR = {code: math.prod(x["today"] ** K for x in SB.INTERVENTIONS if x["bundle"] == b)
               for b, code in PACKAGE.items()}


def google_times():
    """{segment: {hour: seconds}} averaged over both directions, plus distance.

    Each direction's segment times are scaled so they add up EXACTLY to Google's
    whole-route time for that hour (segment-by-segment calls differ from the
    one-shot route by a few % because of how junction waits are split)."""
    seg = defaultdict(dict)
    dist = defaultdict(list)
    for r in csv.DictReader(open(f"data/google_segments_{NAME}.csv")):
        seg[(int(r["segment"]), r["direction"])][int(r["hour"])] = int(r["time_s"])
        dist[int(r["segment"])].append(int(r["distance_m"]))
    full = {}
    for r in csv.DictReader(open(f"data/google_times_{NAME}.csv")):
        if r["route"] == "full" and r["traffic_model"] == "BEST_GUESS":
            d = "southbound" if r["direction"] == "forward" else "northbound"
            full[(d, int(r["hour"]))] = int(r["time_s"])
    t = defaultdict(lambda: defaultdict(list))
    ids = sorted({k[0] for k in seg})
    for d in ("southbound", "northbound"):
        for h in (6, 10, 18):
            k = full[(d, h)] / sum(seg[(i, d)][h] for i in ids)
            for i in ids:
                t[i][h].append(seg[(i, d)][h] * k)
    return ({s: {h: sum(v) / len(v) for h, v in hs.items()} for s, hs in t.items()},
            {s: sum(v) / len(v) for s, v in dist.items()})


def segment_rows():
    G, D = google_times()
    rows = []
    for s in SEGMENTS:
        lanes = 2 * s["lanes"]
        best = lanes * PER_LANE_BEST
        penalty = math.prod(SITE_FACTOR[c] ** s["sev"][c] for c in SITE_FACTOR)
        today = best * penalty
        spare = 2 * PER_LANE_BEST if s["spare"] >= 3 else (PER_LANE_BEST if s["spare"] >= 1.5 else 0)
        fly = today + s["fly"] * FLYOVER_PCU_PER_LANE
        fly_ejipura = fly + s["ejipura"] * FLYOVER_PCU_PER_LANE
        t6, t10, t18 = G[s["id"]][6], G[s["id"]][10], G[s["id"]][18]
        A = t10 / t6 - 1
        # Google shows every segment ~2x slower at 10 am than at 6 am, i.e. each is
        # loaded to about its own capacity today: demand here = today's capacity here.
        # Same traffic (no growth, no induced trips), more capacity -> less delay.
        def minutes(cap):
            return t6 * (1 + A * (today / cap) ** 2) / 60
        ej = s["ejipura"] * FLYOVER_PCU_PER_LANE
        t_best = minutes(best) * 60
        rows.append(dict(
            seg=s["id"], name=s["name"], km=round(s["ch"][1] - s["ch"][0], 2),
            width_m=s["cw"], lanes_each_way=s["lanes"], signals=s["signals"],
            google_kmh_6am=round(D[s["id"]] / t6 * 3.6, 1), google_kmh_10am=round(D[s["id"]] / t10 * 3.6, 1),
            google_kmh_6pm=round(D[s["id"]] / t18 * 3.6, 1), google_min_10am=round(t10 / 60, 1),
            today_pcu=round(today), best_pcu=round(best), uplift_pcu=round(best - today),
            uplift_pct=round(100 * (best / today - 1)),
            best_plus_strip_pcu=round(best + spare),
            flyover_pcu=round(fly), flyover_uplift_pcu=round(fly - today),
            flyover_plus_ejipura_pcu=round(fly_ejipura),
            fix_plus_flyover_pcu=round(best + (s["fly"] + s["ejipura"]) * FLYOVER_PCU_PER_LANE),
            best_min_10am=round(t_best / 60, 1), best_kmh_10am=round(D[s["id"]] / t_best * 3.6, 1),
            # minutes per trip through this stretch at 10 am, under each option
            min_today=round(t10 / 60, 2),
            min_fix=round(minutes(best), 2),
            min_flyover=round(minutes(fly), 2),
            min_ejipura=round(minutes(today + ej), 2),
            min_flyover_ejipura=round(minutes(fly_ejipura), 2),
            min_fix_ejipura=round(minutes(best + ej), 2),
            min_fix_all=round(minutes(best + (s["fly"] + s["ejipura"]) * FLYOVER_PCU_PER_LANE), 2),
        ))
    for r in rows:
        r["saved_fix_min"] = round(r["min_today"] - r["min_fix"], 2)
        r["saved_flyover_min"] = round(r["min_today"] - r["min_flyover"], 2)
    return rows


OPTIONS = [  # label, capacity column, minutes column
    ("Today", "today_pcu", "min_today"),
    ("Flyover (DPR), ground as today", "flyover_pcu", "min_flyover"),
    ("Flyover + Ejipura flyover, ground as today", "flyover_plus_ejipura_pcu", "min_flyover_ejipura"),
    ("Fix the ground (no flyover)", "best_pcu", "min_fix"),
    ("Fix the ground + Ejipura flyover", None, "min_fix_ejipura"),
    ("Fix the ground + flyover + Ejipura flyover", "fix_plus_flyover_pcu", "min_fix_all"),
    ("Fix the ground + flyover", "fix_plus_flyover_pcu", "min_fix_all"),
]


def corridor_summary(rows):
    """What the whole corridor can pass (= its weakest segment) and the 10 am trip time."""
    out = {}
    for label, cap_col, min_col in OPTIONS:
        if "Ejipura" in label and not L["has_second_flyover"]:
            continue
        if label == "Fix the ground + flyover" and L["has_second_flyover"]:
            continue
        if cap_col is None:  # fix + Ejipura: capacity = best + Ejipura lanes where present
            caps = [(r["best_pcu"] + (r["flyover_plus_ejipura_pcu"] - r["flyover_pcu"]), r) for r in rows]
        else:
            caps = [(r[cap_col], r) for r in rows]
        v, r = min(caps, key=lambda x: x[0])
        out[label] = (v, r["seg"], r["name"], round(sum(x[min_col] for x in rows), 1))
    return out


# ---------------------------------------------------------------- start-to-end trip time
CONDITIONS = [("Typical day, 10 am", "BEST_GUESS", 10), ("Typical day, 6 pm", "BEST_GUESS", 18),
              ("Bad day, 10 am", "PESSIMISTIC", 10), ("Bad day, 6 pm", "PESSIMISTIC", 18)]
TRIP_OPTIONS = ([("Today", "today"), (L["flyover"], "flyover"),
                 ("Flyover + Ejipura flyover", "flyover_ej"), ("Fix the ground, no flyover", "fix"),
                 ("Fix the ground + Ejipura flyover", "fix_ej"), ("Fix the ground + both flyovers", "fix_all")]
                if L["has_second_flyover"] else
                [("Today", "today"), (L["flyover"], "flyover"), ("Fix the ground, no flyover", "fix"),
                 ("Fix the ground + flyover", "fix_all")])
WORKING_DAYS = 250
TO_END, TO_START = f"to {L['end_short']}", f"to {L['start_short']}"


def trip_times(rows=None):
    """Minutes from start to end of the corridor (and back).

    Uses Google's WHOLE-ROUTE time for each condition (the real door-to-door number),
    split over the 10 segments in proportion to Google's per-segment times. In each
    segment the delay (time above its 6 am time) shrinks as (today cap / new cap)^2.
    Bad-day segment times: typical segment times scaled up to Google's pessimistic
    whole-route time (delay assumed spread like on a typical day)."""
    rows = rows or segment_rows()
    by_id = {r["seg"]: r for r in rows}
    seg = defaultdict(dict)
    for r in csv.DictReader(open(f"data/google_segments_{NAME}.csv")):
        seg[(int(r["segment"]), r["direction"])][int(r["hour"])] = int(r["time_s"]) / 60
    full = defaultdict(dict)
    for r in csv.DictReader(open(f"data/google_times_{NAME}.csv")):
        if r["route"] == "full":
            d = TO_END if r["direction"] == "forward" else TO_START
            full[(r["traffic_model"], d)][int(r["hour"])] = int(r["time_s"]) / 60
    gdir = {TO_END: "southbound", TO_START: "northbound"}
    out = []
    for cond, model, h in CONDITIONS:
        for d, sd in gdir.items():
            k = full[(model, d)][h] / sum(seg[(s["id"], sd)][h] for s in SEGMENTS)
            k6 = full[("BEST_GUESS", d)][6] / sum(seg[(s["id"], sd)][6] for s in SEGMENTS)
            mins = defaultdict(float)
            for s in SEGMENTS:
                r = by_id[s["id"]]
                ej = s["ejipura"] * FLYOVER_PCU_PER_LANE
                caps = dict(today=r["today_pcu"], flyover=r["flyover_pcu"], flyover_ej=r["flyover_plus_ejipura_pcu"],
                            fix=r["best_pcu"], fix_ej=r["best_pcu"] + ej, fix_all=r["fix_plus_flyover_pcu"])
                t6, th = seg[(s["id"], sd)][6] * k6, seg[(s["id"], sd)][h] * k
                for opt, c in caps.items():
                    mins[opt] += t6 + max(th - t6, 0) * (r["today_pcu"] / c) ** 2
            for label, opt in TRIP_OPTIONS:
                out.append(dict(condition=cond, direction=d, option=label, minutes=round(mins[opt], 1),
                                saved_min=round(mins["today"] - mins[opt], 1)))
    # a commuter: to Silk Board at 10 am, back at 6 pm, typical day
    for label, opt in TRIP_OPTIONS:
        go = next(x for x in out if x["condition"] == "Typical day, 10 am" and x["direction"] == TO_END
                  and x["option"] == label)
        back = next(x for x in out if x["condition"] == "Typical day, 6 pm" and x["direction"] == TO_START
                    and x["option"] == label)
        saved = go["saved_min"] + back["saved_min"]
        out.append(dict(condition="Daily commute (10 am there, 6 pm back)", direction="round trip", option=label,
                        minutes=round(go["minutes"] + back["minutes"], 1), saved_min=round(saved, 1),
                        hours_saved_per_year=round(saved * WORKING_DAYS / 60)))
    return out


def main():
    rows = segment_rows()
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(f"{OUT_DIR}/segments.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"{'seg':>3} {'name':42s} {'km':>4} {'today':>6} {'best':>6} {'+%':>4} {'flyover':>8} {'Google 10am km/h':>16}")
    for r in rows:
        print(f"{r['seg']:>3} {r['name'][:42]:42s} {r['km']:4.2f} {r['today_pcu']:6,d} {r['best_pcu']:6,d} "
              f"{r['uplift_pct']:+4d} {r['flyover_pcu']:8,d} {r['google_kmh_10am']:16.1f}")
    trips = trip_times(rows)
    with open(f"{OUT_DIR}/trip_times.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["condition", "direction", "option", "minutes", "saved_min",
                                          "hours_saved_per_year"])
        w.writeheader()
        w.writerows(trips)
    print(f"\nSTART TO END ({L['trip']}), minutes [saved]:")
    for cond in [c[0] for c in CONDITIONS] + ["Daily commute (10 am there, 6 pm back)"]:
        for d in [TO_END, TO_START, "round trip"]:
            xs = [x for x in trips if x["condition"] == cond and x["direction"] == d]
            if xs:
                print(f"  {cond:40s} {d:16s} " + "  ".join(f"{x['option'].split(',')[0][:22]}={x['minutes']:.0f}[{x['saved_min']:.0f}]" for x in xs))
    print("\nWHOLE CORRIDOR (capacity = weakest segment; trip time at 10 am, same traffic as today):")
    for k, (v, seg, name, mins) in corridor_summary(rows).items():
        print(f"  {k:45s} {v:6,d} PCU/h  {mins:5.1f} min   bottleneck: seg {seg} {name}")


if __name__ == "__main__":
    main()
