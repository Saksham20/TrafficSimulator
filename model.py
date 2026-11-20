"""Step 2: capacity of the same road under every mix of interventions.

The idea in one line
    capacity = BEST_CAPACITY x product of (friction factor ^ K) over every friction NOT fixed

  * BEST_CAPACITY: the same road run as a proper arterial (IRC:106).
  * friction factor: from the literature, per problem (inputs_<corridor>.py).
  * K: one calibration number. Literature factors overlap (a parked car and a
    bus stop block the same lane), so all are shrunk equally until "today"
    reproduces the counted peak (Silk Board DPR: 3,996 PCU/h). Each problem
    keeps its relative weight. Corridors without a count reuse Silk Board's K.

Travel time (Google-calibrated):
    t = t_6am x (1 + A x (demand / capacity) ^ BETA)
  t_6am = Google 6 am time; A chosen so that today's 10 am time matches Google.

Run:  CORRIDOR=silk_board python model.py      -> outputs/<corridor>/*.csv
"""

import csv
import itertools
import math

from corridor import I, OUT

# ---------------------------------------------------------------- calibration
TODAY_PRODUCT = math.prod(x["today"] for x in I.INTERVENTIONS)
K = I.K_OVERRIDE or math.log(I.TODAY_CAPACITY / I.BEST_CAPACITY) / math.log(TODAY_PRODUCT)
if I.K_OVERRIDE:  # no count on this corridor: today's capacity follows from the frictions
    I.TODAY_CAPACITY = I.BEST_CAPACITY * TODAY_PRODUCT ** K
if I.DEMAND_FORECAST is None:  # no forecast: today's demand grows at I.GROWTH a year
    I.DEMAND_FORECAST = {2026: I.TODAY_CAPACITY, 2051: I.TODAY_CAPACITY * (1 + I.GROWTH) ** 25}


def capacity(fixed=(), state="today"):
    """Two-way capacity (PCU/h) with the interventions in `fixed` done.
    state = 'today' (typical day) or 'worst' (bad day) for everything not fixed."""
    c = I.BEST_CAPACITY
    for x in I.INTERVENTIONS:
        if x["id"] not in fixed:
            c *= x[state] ** K
    return c


def google_route(route="full", direction="forward", model="BEST_GUESS"):
    """{hour: seconds} from data/google_times_<corridor>.csv"""
    out = {}
    for r in csv.DictReader(open(f"data/google_times_{I.NAME}.csv")):
        if (r["route"], r["direction"], r["traffic_model"]) == (route, direction, model):
            out[int(r["hour"])] = int(r["time_s"])
            dist = int(r["distance_m"])
    out["km"] = dist / 1000
    return out


GOOGLE = google_route()
T_FREE = GOOGLE[6]                     # 06:00, near-empty road (still has signals)
T_TODAY_PEAK = GOOGLE[10]              # 10:00 = Silk Board DPR count hour
A = T_TODAY_PEAK / T_FREE - 1          # demand = capacity today -> Google's 10 am time
DIST_KM = GOOGLE["km"]


def travel_minutes(cap, demand=None):
    demand = demand or I.TODAY_CAPACITY
    return T_FREE * (1 + A * (demand / cap) ** I.BETA) / 60


def implied_capacity(seconds):
    """Invert the travel-time curve: what capacity would explain this Google time?"""
    return I.TODAY_CAPACITY / math.sqrt((seconds / T_FREE - 1) / A)


def demand_in(year):
    """Peak-hour demand forecast, interpolated (constant growth between given years)."""
    ys = sorted(I.DEMAND_FORECAST)
    for a, b in zip(ys, ys[1:]):
        if a <= year <= b:
            g = (I.DEMAND_FORECAST[b] / I.DEMAND_FORECAST[a]) ** (1 / (b - a))
            return I.DEMAND_FORECAST[a] * g ** (year - a)
    return I.DEMAND_FORECAST[ys[-1]]


def year_full(cap):
    """First year the demand forecast reaches this capacity."""
    for y in range(min(I.DEMAND_FORECAST), 2052):
        if demand_in(y) >= cap * 0.999:
            return y
    return 2051


def row(label, fixed=(), state="today"):
    c = capacity(fixed, state)
    return dict(scenario=label, fixed="+".join(fixed) or "-", state_of_rest=state,
                capacity_pcu_h=round(c), vs_today_pct=round(100 * (c / I.TODAY_CAPACITY - 1)),
                peak_minutes=round(travel_minutes(c), 1),
                speed_kmh=round(DIST_KM / travel_minutes(c) * 60, 1),
                road_full_in=year_full(c))


def bundle_ids(*bundles):
    return tuple(x["id"] for x in I.INTERVENTIONS if x["bundle"] in bundles)


def ladder():
    """Worst -> today -> each bundle -> bundles together -> everything."""
    rows = [row("Worst day (everything breaks)", state="worst"),
            row("Today" + (" (calibrated to DPR count)" if not I.K_OVERRIDE else " (estimated)"))]
    for b in I.BUNDLES:
        rows.append(row(f"Today + {b}", bundle_ids(b)))
    rows.append(row("Enforce + Signals (no construction)", bundle_ids("Enforce", "Signals")))
    rows.append(row("Enforce + Signals + Design", bundle_ids("Enforce", "Signals", "Design")))
    rows.append(row("Everything fixed (IRC arterial)", bundle_ids(*I.BUNDLES)))
    return rows


def singles():
    """Each intervention on its own, from today."""
    return [row(x["name"], (x["id"],)) for x in I.INTERVENTIONS]


def all_combinations():
    """All 2^9 = 512 combinations of interventions."""
    ids = [x["id"] for x in I.INTERVENTIONS]
    return [dict(n_fixed=n, fixed="+".join(c) or "-", capacity_pcu_h=round(capacity(c)))
            for n in range(len(ids) + 1) for c in itertools.combinations(ids, n)]


def bundle_pairs():
    """Capacity for every pair of bundles (diagonal = single bundle)."""
    names = list(I.BUNDLES)
    return names, [[capacity(bundle_ids(a, b)) for b in names] for a in names]


def google_check():
    """Capacity that would explain Google's bad / typical / good day at 10 am."""
    out = []
    for m, label in [("PESSIMISTIC", "Google bad day"), ("BEST_GUESS", "Google typical day"),
                     ("OPTIMISTIC", "Google good day")]:
        t = google_route(model=m)[10]
        out.append(dict(google=label, minutes_10am=round(t / 60, 1), implied_capacity=round(implied_capacity(t))))
    return out


# ---------------------------------------------------------------- people per hour
def people():
    """Peak hour, both directions: people moved today vs. two ways of adding capacity.

    Flyover: extra car-lanes (DPR deck) filled with today's private-vehicle mix.
    Bus lane: one kerb lane per direction given to buses (with bays, all fixes
    done on the rest), the other lanes carry today's private mix at the fixed-road capacity.
    """
    mix = I.PEAK_HOUR_VEHICLES
    pcu = sum(n * p for n, p, _ in mix.values())
    ppl = sum(n * o for n, _, o in mix.values())
    private = {k: v for k, v in mix.items() if k != "Bus"}
    ppl_per_pcu_private = sum(n * o for n, _, o in private.values()) / sum(n * p for n, p, _ in private.values())
    bus_load = mix["Bus"][2]
    bus_ppl_today = mix["Bus"][0] * bus_load

    flyover_pcu = 2 * I.FLYOVER_LANES_PER_DIRECTION * I.FLYOVER_PCU_PER_LANE
    best = capacity(bundle_ids(*I.BUNDLES))
    lane_share = (I.LANES_PER_DIRECTION - 1) / I.LANES_PER_DIRECTION   # lanes left for general traffic
    bus_lane_ppl = 2 * I.BUS_LANE_BUSES_PER_HOUR * bus_load

    rows = [
        dict(option="Today (DPR count, 10-11 am)", people_per_hour=round(ppl), pcu=round(pcu),
             note=f"buses are {100 * mix['Bus'][0] / sum(n for n, _, _ in mix.values()):.0f}% of vehicles "
                  f"but carry {100 * bus_ppl_today / ppl:.0f}% of people"),
        dict(option="Fix the road, no flyover (IRC arterial)",
             people_per_hour=round(bus_ppl_today + (best - mix['Bus'][0] * mix['Bus'][1]) * ppl_per_pcu_private),
             pcu=round(best), note="same mix, more of it"),
        dict(option="Today + flyover (DPR deck full)",
             people_per_hour=round(ppl + flyover_pcu * ppl_per_pcu_private), pcu=round(pcu + flyover_pcu),
             note=f"{I.FLYOVER_LANES_PER_DIRECTION} lanes/direction x {I.FLYOVER_PCU_PER_LANE} PCU, private vehicles"),
        dict(option="Fix the road + 1 bus lane each way",
             people_per_hour=round(bus_lane_ppl + best * lane_share * ppl_per_pcu_private),
             pcu=round(best * lane_share + 2 * I.BUS_LANE_BUSES_PER_HOUR * mix["Bus"][1]),
             note=f"takes 1 of {I.LANES_PER_DIRECTION} lanes; {I.BUS_LANE_BUSES_PER_HOUR} buses/h/dir x {bus_load}"),
    ]
    if getattr(I, "BUS_LANE_IN_SPARE_STRIP", False):
        rows.append(dict(option="Fix the road + bus lane in the paver strip",
                         people_per_hour=round(bus_lane_ppl + best * ppl_per_pcu_private),
                         pcu=round(best + 2 * I.BUS_LANE_BUSES_PER_HOUR * mix["Bus"][1]),
                         note="all general lanes kept; bus lane uses the existing 3-5 m strip"))
    return rows


# ---------------------------------------------------------------- output
def write(name, rows):
    with open(f"{OUT}/{name}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)


def show(rows, cols):
    print("  " + " | ".join(f"{c:>14s}" if i else f"{c:52s}" for i, c in enumerate(cols)))
    for r in rows:
        print("  " + " | ".join(f"{str(r[c]):>14s}" if i else f"{str(r[c])[:52]:52s}" for i, c in enumerate(cols)))


def main():
    print(f"\n=== {I.TITLE} ===")
    print(f"Overlap exponent K = {K:.2f}" + (" (reused from Silk Board)" if I.K_OVERRIDE else
                                            f" (raw literature product today {TODAY_PRODUCT:.2f})"))
    print(f"Google full route ({DIST_KM:.1f} km): {T_FREE / 60:.0f} min at 6 am, {T_TODAY_PEAK / 60:.0f} min "
          f"at 10 am -> A = {A:.2f}\n")

    cols = ["scenario", "capacity_pcu_h", "vs_today_pct", "peak_minutes", "speed_kmh", "road_full_in"]
    print("LADDER (same road, same lanes, two-way PCU/h; travel time at today's peak demand)")
    lad = ladder()
    show(lad, cols)
    write("ladder", lad)
    print("\nONE INTERVENTION AT A TIME (rest as today)")
    sg = singles()
    show(sorted(sg, key=lambda r: -r["capacity_pcu_h"]), cols)
    write("singles", sg)
    print("\nGOOGLE CHECK (capacity that would explain Google's 10 am time)")
    gc = google_check()
    for g in gc:
        print(f"  {g['google']:20s} {g['minutes_10am']:5.1f} min  -> ~{g['implied_capacity']} PCU/h")
    write("google_check", gc)
    if hasattr(I, "PEAK_HOUR_VEHICLES"):
        print("\nPEOPLE PER HOUR (peak, both directions)")
        pp = people()
        for p in pp:
            print(f"  {p['option']:42s} {p['people_per_hour']:7,d} people/h   ({p['note']})")
        write("people", pp)
    combos = all_combinations()
    write("all_combinations", combos)
    print(f"\n{len(combos)} combinations -> {OUT}/all_combinations.csv")
    print(f"Demand forecast reaches: today's capacity {year_full(I.TODAY_CAPACITY)}, "
          f"all fixes {year_full(I.BEST_CAPACITY)}, {I.EXTRA_LABEL} {year_full(I.BEST_WITH_BUFFER_REUSED)}")


if __name__ == "__main__":
    main()
