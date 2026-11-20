"""Step 4: slide-ready charts -> outputs/*.png

Run:  CORRIDOR=silk_board python charts.py   -> outputs/<corridor>/*.png  (ghost-jam chart -> outputs/)
"""

import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import ghost_jam as G
import model as M
from corridor import I, OUT
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 150, "savefig.bbox": "tight"})
RED, GREY, GREEN, BLUE, ORANGE = "#c0392b", "#7f8c8d", "#27ae60", "#2c7fb8", "#e67e22"
SRC = I.SOURCES_LINE if hasattr(I, "SOURCES_LINE") else "Sources: DPR (B-SMILE, Feb 2026), IRC:106-1990, HCM 2010, Google Routes API (Nov 2026). See README for assumptions."


def footer(fig):
    fig.text(0.01, -0.02, SRC, fontsize=8, color=GREY)


# ---------------------------------------------------------------- 1. ladder
def chart_ladder():
    rows = M.ladder()
    labels = [r["scenario"] for r in rows]
    caps = [r["capacity_pcu_h"] for r in rows]
    colors = [RED] + [GREY] + [BLUE] * (len(rows) - 3) + [GREEN]
    fig, ax = plt.subplots(figsize=(12, 6.5))
    y = np.arange(len(rows))[::-1]
    ax.barh(y, caps, color=colors)
    for yi, r in zip(y, rows):
        ax.text(r["capacity_pcu_h"] + 40, yi, f'{r["capacity_pcu_h"]:,}  ({r["vs_today_pct"]:+d}%)  '
                f'{r["peak_minutes"]:.0f} min', va="center", fontsize=10)
    ax.set_yticks(y, labels)
    ax.axvline(I.IRC_DSV_SUB_ARTERIAL, color=ORANGE, ls="--")
    ax.text(I.IRC_DSV_SUB_ARTERIAL, -0.9, f"IRC {I.IRC_DSV_SUB_ARTERIAL:,}\nsub-arterial", color=ORANGE, fontsize=9, ha="center")
    for yr in (2031, 2036):
        d = M.demand_in(yr)
        ax.axvline(d, color=RED, ls=":", lw=1)
        ax.text(d, -0.9, f"{yr}\ndemand", color=RED, fontsize=9, ha="center")
    ax.set_xlim(0, max(caps) * 1.4)
    ax.set_xlabel(f"Peak-hour capacity, two-way PCU/h  (same {2 * I.LANES_PER_DIRECTION} lanes, no new construction)")
    ax.set_title(f"{I.TITLE}: same road, same lanes, worst day to best practice\n\n"
                 f"(label: capacity, change vs today, {M.DIST_KM:.1f} km trip time at today's peak demand)",
                 loc="left", fontsize=13)
    footer(fig)
    fig.savefig(f"{OUT}/1_capacity_ladder.png")
    plt.close(fig)


# ---------------------------------------------------------------- 2. single interventions
def chart_singles():
    rows = sorted(M.singles(), key=lambda r: r["capacity_pcu_h"])
    fig, ax = plt.subplots(figsize=(11, 5.5))
    gain = [r["capacity_pcu_h"] - I.TODAY_CAPACITY for r in rows]
    ax.barh([r["scenario"] for r in rows], gain, color=BLUE)
    for i, g in enumerate(gain):
        ax.text(g + 3, i, f"+{g} PCU/h", va="center", fontsize=10)
    ax.set_xlabel("Extra peak-hour capacity vs today (PCU/h), one fix at a time")
    ax.set_title("No single fix is a silver bullet.\nThe gain comes from doing them together "
                 f"(all together: +{I.BEST_CAPACITY - I.TODAY_CAPACITY:,.0f} PCU/h)", loc="left", fontsize=13)
    footer(fig)
    fig.savefig(f"{OUT}/2_single_interventions.png")
    plt.close(fig)


# ---------------------------------------------------------------- 3. bundle pairs
def chart_bundle_matrix():
    names, mat = M.bundle_pairs()
    mat = np.array(mat)
    fig, ax = plt.subplots(figsize=(7.5, 6))
    im = ax.imshow(mat, cmap="Greens", vmin=I.TODAY_CAPACITY, vmax=I.BEST_CAPACITY)
    for i in range(len(names)):
        for j in range(len(names)):
            ax.text(j, i, f"{mat[i, j]:,.0f}\n{100 * (mat[i, j] / I.TODAY_CAPACITY - 1):+.0f}%",
                    ha="center", va="center", fontsize=10)
    ax.set_xticks(range(len(names)), names)
    ax.set_yticks(range(len(names)), names)
    ax.set_title(f"Two packages together (diagonal = one package alone)\nPCU/h and change vs today ({I.TODAY_CAPACITY:,.0f})",
                 loc="left", fontsize=13)
    fig.colorbar(im, ax=ax, shrink=0.8, label="PCU/h")
    footer(fig)
    fig.savefig(f"{OUT}/3_package_combinations.png")
    plt.close(fig)


# ---------------------------------------------------------------- 4. all 512 combinations
def chart_all_combos():
    combos = M.all_combinations()
    fig, ax = plt.subplots(figsize=(10, 5.5))
    rng = np.random.default_rng(0)
    x = np.array([c["n_fixed"] for c in combos]) + rng.uniform(-0.25, 0.25, len(combos))
    ax.scatter(x, [c["capacity_pcu_h"] for c in combos], s=10, alpha=0.5, color=BLUE)
    ax.axhline(I.TODAY_CAPACITY, color=GREY, ls="--")
    ax.text(9.3, I.TODAY_CAPACITY, " today", va="center", color=GREY)
    ax.axhline(M.capacity(state="worst"), color=RED, ls="--")
    ax.text(9.3, M.capacity(state="worst"), " worst day", va="center", color=RED)
    ax.axhline(I.IRC_DSV_SUB_ARTERIAL, color=ORANGE, ls=":")
    ax.text(9.3, I.IRC_DSV_SUB_ARTERIAL, " IRC sub-arterial", va="center", color=ORANGE)
    ax.set_xlabel("Number of the 9 fixes applied (each dot = one of 512 combinations)")
    ax.set_ylabel("Peak capacity, PCU/h two-way")
    ax.set_title("Every combination of the 9 fixes: capacity rises steadily with each fix done",
                 loc="left", fontsize=13)
    footer(fig)
    fig.savefig(f"{OUT}/4_all_512_combinations.png")
    plt.close(fig)


# ---------------------------------------------------------------- 5. demand vs capacity by year
def chart_years():
    years = np.arange(2026, 2047)
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.plot(years, [M.demand_in(y) for y in years], color=RED, lw=3, label=I.DEMAND_SOURCE)
    lines = [("Today's practical capacity", I.TODAY_CAPACITY, GREY, "--"),
             ("Enforce + Signals (no construction)", M.capacity(M.bundle_ids("Enforce", "Signals")), BLUE, "-"),
             (f"All fixes = IRC {2 * I.LANES_PER_DIRECTION}-lane arterial", I.BEST_CAPACITY, GREEN, "-"),
             (I.EXTRA_LABEL, I.BEST_WITH_BUFFER_REUSED, GREEN, ":")]
    for label, c, col, ls in lines:
        ax.axhline(c, color=col, ls=ls, lw=2)
        ax.text(2046.2, c, f"{label}\n{c:,.0f} -> full in {M.year_full(c)}", va="center", fontsize=9, color=col)
    ax.axvline(I.FLYOVER_READY_YEAR, color="black", lw=1)
    lo = 0.6 * I.TODAY_CAPACITY
    ax.text(I.FLYOVER_READY_YEAR + 0.2, lo * 1.03, "flyover ready", fontsize=9)
    ax.set_ylim(lo, max(I.BEST_WITH_BUFFER_REUSED, M.demand_in(2046)) * 1.1)
    ax.set_xticks(range(2026, 2047, 2))
    ax.set_xlim(2026, 2046)
    ax.set_ylabel("Peak hour, two-way PCU/h")
    ax.set_title(f"{I.TITLE}: when does the road really run out of room?",
                 loc="left", fontsize=13)
    ax.legend(loc="upper left")
    footer(fig)
    fig.savefig(f"{OUT}/5_years_of_headroom.png")
    plt.close(fig)


# ---------------------------------------------------------------- 6. Google ground truth
def chart_google():
    fig, ax = plt.subplots(figsize=(11, 5.5))
    hours = list(range(6, 23))
    for model, col, label in [("PESSIMISTIC", RED, "Google bad day"),
                              ("BEST_GUESS", "black", "Google typical day"),
                              ("OPTIMISTIC", GREEN, "Google good day")]:
        g = M.google_route(model=model)
        ax.plot(hours, [g[h] / 60 for h in hours], color=col, lw=2.5 if model == "BEST_GUESS" else 1.5,
                label=label)
    ax.fill_between(hours, [M.google_route(model="OPTIMISTIC")[h] / 60 for h in hours],
                    [M.google_route(model="PESSIMISTIC")[h] / 60 for h in hours], color=GREY, alpha=0.12)
    for r, col in [(M.row("Model: worst day", state="worst"), RED),
                   (M.row("Model: today"), "black"),
                   (M.row("Model: all fixes", M.bundle_ids(*I.BUNDLES)), GREEN)]:
        ax.scatter([10], [r["peak_minutes"]], s=120, color=col, edgecolor="white", zorder=5, marker="D")
        ax.annotate(f'{r["scenario"]}: {r["peak_minutes"]:.0f} min', (10, r["peak_minutes"]),
                    xytext=(10.4, r["peak_minutes"] + 1.5), fontsize=9, color=col)
    ax.set_xticks(hours, [f"{h}:00" for h in hours], rotation=45)
    ax.set_ylabel(f"Minutes, {I.TITLE} ({M.DIST_KM:.1f} km)")
    ax.set_title("Ground truth: Google Maps travel time across a Tuesday (Nov 2026)\n"
                 "Diamonds = model at 10 am. Model worst / today / best vs Google bad / typical / good day.",
                 loc="left", fontsize=13)
    ax.legend(loc="upper right")
    footer(fig)
    fig.savefig(f"{OUT}/6_google_ground_truth.png")
    plt.close(fig)


# ---------------------------------------------------------------- 7. ghost jams
def chart_ghost():
    rows = list(csv.DictReader(open("outputs/ghost_jam.csv")))
    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(16, 5), gridspec_kw={"width_ratios": [1.3, 1, 1]})
    cols = [GREEN, ORANGE, RED, "#8e44ad"]
    for name, col in zip(G.BEHAVIOURS, cols):
        r = [x for x in rows if x["behaviour"] == name]
        a1.plot([int(x["density_veh_km"]) for x in r], [int(x["flow_veh_h"]) for x in r], color=col, lw=2,
                label=f'{name} (max {max(int(x["flow_veh_h"]) for x in r):,})')
    a1.set_xlabel("Density (vehicles per km per lane)")
    a1.set_ylabel("Throughput (vehicles per hour per lane)")
    a1.set_title("Same lane, no bottleneck: behaviour alone\ncuts throughput", loc="left")
    a1.legend(fontsize=8, loc="upper right")
    density = 0.22
    for ax, name in [(a2, "Disciplined (smooth, attentive)"), (a3, "Erratic + slow restarts + kerb stops")]:
        flow, hist = G.simulate(density, *G.BEHAVIOURS[name], record=True)
        ax.imshow(hist[:, :200], aspect="auto", cmap="Greys", interpolation="nearest")
        ax.set_title(f"{name.split(' (')[0]}\n{flow:,.0f} veh/h at {density * 1000 / 7.5:.0f} veh/km", loc="left",
                     fontsize=11)
        ax.set_xlabel("Position along road (1.5 km)  ->")
        ax.set_ylabel("Time (s)  ->")
    fig.suptitle("Ghost jams (Nagel-Schreckenberg simulation): black bands = stop-and-go waves "
                 "that travel backwards with no cause", x=0.01, y=1.06, ha="left", fontsize=13)
    fig.subplots_adjust(wspace=0.3)
    fig.text(0.01, -0.03, "Model: Nagel & Schreckenberg 1992 with slow-to-start (Barlovic et al. 1998). "
             "Real-world proof: Sugiyama et al. 2008 (jam with no bottleneck); Stern et al. 2018 (one smooth driver "
             "in 20+ damps the waves).", fontsize=8, color=GREY)
    fig.savefig("outputs/7_ghost_jams.png")
    plt.close(fig)


# ---------------------------------------------------------------- 8. people per hour
def chart_people():
    rows = M.people()
    fig, ax = plt.subplots(figsize=(11, 5))
    colors = [GREY, BLUE, ORANGE, GREEN, GREEN][:len(rows)]
    y = np.arange(len(rows))[::-1]
    ax.barh(y, [r["people_per_hour"] for r in rows], color=colors)
    for yi, r in zip(y, rows):
        ax.text(r["people_per_hour"] + 150, yi, f'{r["people_per_hour"]:,}  ({r["note"]})', va="center", fontsize=9)
    ax.set_yticks(y, [r["option"] for r in rows])
    ax.set_xlim(0, max(r["people_per_hour"] for r in rows) * 1.9)
    ax.set_xlabel("People moved in the peak hour, both directions")
    cost = f" (Rs {I.FLYOVER_COST_CR:,} cr)" if hasattr(I, "FLYOVER_COST_CR") else ""
    ax.set_title(f"Move people, not vehicles: a bus lane on the existing road vs the flyover{cost}",
                 loc="left", fontsize=13)
    fig.text(0.01, -0.06, "Occupancy: 2W 1.2, car 1.5, auto 1.8, bus 40 (peak avg; crush ~80). Flyover deck assumed "
             f"full at {I.FLYOVER_PCU_PER_LANE} PCU/lane with today's private mix (no induced demand counted). "
             f"Bus lane: {I.BUS_LANE_BUSES_PER_HOUR} buses/h/direction.", fontsize=8, color=GREY)
    footer(fig)
    fig.savefig(f"{OUT}/8_people_per_hour.png")
    plt.close(fig)


if __name__ == "__main__":
    import os, sys
    charts = [chart_ladder, chart_singles, chart_bundle_matrix, chart_all_combos, chart_years, chart_google]
    if hasattr(I, "PEAK_HOUR_VEHICLES"):
        charts.append(chart_people)
    if os.path.exists("outputs/ghost_jam.csv"):
        charts.append(chart_ghost)
    for f in charts:
        f()
        print("done", f.__name__)
    print(f"charts in {OUT}/")
