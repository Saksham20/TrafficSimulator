"""Step 6: map-style charts for the explainer.  CORRIDOR=silk_board (default) or mysore_road.

  A_map_travel_speed.png    the road start to end: segments coloured by Google
                            10 am speed (red = slow, green = fast), signals,
                            sharp turns and road width labelled
  B_map_pcu_today_best.png  three maps: PCU today | PCU if done right | uplift
  C_flyover_vs_ground.png   per segment: uplift from fixing the ground vs from flyovers
  D_corridor_throughput.png what gets through end to end (weakest link)

Run after segment_model.py:  CORRIDOR=silk_board python segment_charts.py   -> explainer_<corridor>/*.png + PDF
"""

import json
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize

import segment_model as SM
SEGMENTS, SIGNALS, L = SM.SEGMENTS, SM.SG.SIGNALS, SM.L

OUT = SM.OUT_DIR
GEO = json.load(open(f"data/route_geometry_{SM.NAME}.json"))
ROWS = SM.segment_rows()
BY_ID = {r["seg"]: r for r in ROWS}
LAT0 = 12.95
N = len(SEGMENTS)
ASPECT = 1 / math.cos(math.radians(LAT0))
GOOGLE_CMAP = LinearSegmentedColormap.from_list("google", ["#8b0000", "#e53935", "#fb8c00", "#fdd835", "#43a047"])
SRC = L["sources"]
plt.rcParams.update({"font.size": 11, "figure.dpi": 150, "savefig.bbox": "tight"})


def line(seg):
    return np.array(GEO[f"{seg}_southbound"])


def point_along(seg, frac):
    """Point a given fraction along a segment's road line."""
    P = line(seg)
    d = np.r_[0, np.cumsum(np.hypot(*(np.diff(P, axis=0) * [1, 1 / ASPECT]).T))]
    x = frac * d[-1]
    i = min(np.searchsorted(d, x), len(P) - 1)
    return P[i]


def ch_point(ch):
    for s in SEGMENTS:
        a, b = s["ch"]
        if a <= ch <= b + 1e-9:
            return point_along(s["id"], (ch - a) / (b - a))
    return point_along(SEGMENTS[-1]["id"], 1.0)


def base_axes(ax, title):
    ax.set_aspect(ASPECT)
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_title(title, fontsize=12, loc="left")


def draw_route(ax, values, cmap, norm, width=9):
    for s in SEGMENTS:
        P = line(s["id"])
        ax.plot(P[:, 1], P[:, 0], color="#333333", lw=width + 3, solid_capstyle="round", zorder=1)
        ax.plot(P[:, 1], P[:, 0], color=cmap(norm(values[s["id"]])), lw=width, solid_capstyle="round", zorder=2)
    for s in SEGMENTS[1:]:  # segment boundaries
        p = line(s["id"])[0]
        ax.plot(p[1], p[0], "o", color="white", ms=4, mec="#333333", zorder=3)


def end_labels(ax):
    a, b = line(1)[0], line(N)[-1]
    ax.annotate(f"START: {L['start']}", (a[1], a[0]), xytext=(0, 14), textcoords="offset points",
                fontsize=9, weight="bold", ha="center")
    ax.annotate(f"END: {L['end']}", (b[1], b[0]), xytext=(0, -18), textcoords="offset points",
                fontsize=9, weight="bold", ha="center")


def seg_label(ax, s, text, side=1, fs=8.5):
    p = point_along(s["id"], 0.5)
    ax.annotate(text, (p[1], p[0]), xytext=(side * 18, 0), textcoords="offset points", fontsize=fs,
                ha="left" if side > 0 else "right", va="center",
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#bbbbbb", lw=0.6),
                arrowprops=dict(arrowstyle="-", color="#999999", lw=0.6))


ALL = np.vstack([line(s["id"]) for s in SEGMENTS])
LON_MIN, LON_MAX = ALL[:, 1].min(), ALL[:, 1].max()
LAT_MIN, LAT_MAX = ALL[:, 0].min(), ALL[:, 0].max()
# extent of the road in latitude-degrees (works for north-south and east-west roads)
SPAN = max(LAT_MAX - LAT_MIN, (LON_MAX - LON_MIN) / ASPECT)
LAT_MID = (LAT_MAX + LAT_MIN) / 2


def spread(ys, gap):
    """Push label y-positions apart (top to bottom) so they never overlap."""
    order = np.argsort(-np.array(ys))
    out = np.array(ys, dtype=float)
    for k in range(1, len(order)):
        a, b = order[k - 1], order[k]
        if out[a] - out[b] < gap:
            out[b] = out[a] - gap
    return out


def column_labels(ax, items, x, gap, fs=8.5, ha="left", color="black", box=True):
    """items: list of (lat, lon, text). Labels stacked in a column at longitude x."""
    ys = spread([it[0] for it in items], gap)
    for (lat, lon, text), y in zip(items, ys):
        ax.annotate(text, (lon, lat), xytext=(x, y), textcoords="data", fontsize=fs, ha=ha, va="center",
                    color=color,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#bbbbbb", lw=0.6) if box else None,
                    arrowprops=dict(arrowstyle="-", color="#999999", lw=0.6, shrinkA=0, shrinkB=3))


# ---------------------------------------------------------------- A. the road + travel speed
def chart_map_speed():
    fig, ax = plt.subplots(figsize=L.get("map_figsize", (13, 14)))
    speed = {r["seg"]: r["google_kmh_10am"] for r in ROWS}
    norm = Normalize(5, 30)
    draw_route(ax, speed, GOOGLE_CMAP, norm, width=11)
    for ch, name in SIGNALS.items():  # signals
        p = ch_point(ch)
        ax.plot(p[1], p[0], marker="o", ms=11, mfc="#c62828", mec="black", mew=1.2, zorder=5)
        ax.plot(p[1], p[0], marker="o", ms=4, mfc="#ffeb3b", mec="none", zorder=6)
    items = []
    for s in SEGMENTS:
        r = BY_ID[s["id"]]
        p = point_along(s["id"], 0.5)
        items.append((p[0], p[1],
                      f"{s['id']}. {s['name']}\n{r['km']} km | road {s['cw']:g} m each way, {s['lanes']} lanes"
                      + (f" (+{s['spare']:g} m unused strip)" if s["spare"] else "")
                      + f"\n10 am: {r['google_kmh_10am']:.0f} km/h ({r['google_min_10am']:.1f} min)   "
                        f"6 am: {r['google_kmh_6am']:.0f} km/h"))
    span = SPAN
    column_labels(ax, items, LON_MAX + 0.08 * span, gap=L.get("label_gap", 0.062) * span, fs=8.5)
    turns = []
    for s in SEGMENTS:
        if s["turn"]:
            p = line(s["id"])[0]
            turns.append((p[0], p[1], "TURN: " + s["turn"]))
    column_labels(ax, turns, LON_MIN - 0.06 * span, gap=0.045 * span, fs=8.5, ha="right", color="#6a1b9a")
    ax.set_xlim(LON_MIN - 0.3 * span, LON_MAX + 0.45 * span)
    ax.set_ylim(LAT_MID - 0.58 * span, LAT_MID + 0.58 * span)
    end_labels(ax)
    base_axes(ax, L["map_title"] + "\n"
                  "Colour = Google Maps speed at 10 am on a typical Tuesday (like Google's red-to-green traffic layer)")
    sm = plt.cm.ScalarMappable(norm=norm, cmap=GOOGLE_CMAP)
    cb = fig.colorbar(sm, ax=ax, shrink=0.45, pad=0.02, orientation="horizontal")
    cb.set_label("Google speed at 10 am (km/h):  red = crawling, green = flowing")
    ax.plot([], [], "o", ms=10, mfc="#c62828", mec="black", label="Traffic signal")
    ax.plot([], [], "o", ms=5, mfc="white", mec="#333333", label="Segment boundary")
    ax.legend(loc="upper left", fontsize=9, frameon=False)
    tot10 = sum(r["min_today"] for r in ROWS)
    km = sum(SM.google_times()[1].values()) / 1000
    t6 = sum(SM.google_times()[0][i][6] for i in BY_ID) / 60
    fig.text(0.02, 0.02, f"Whole trip at 10 am: {tot10:.0f} min for {km:.1f} km (about {km / tot10 * 60:.0f} km/h). "
             f"At 6 am the same trip takes ~{t6:.0f} min.\n" + L["map_note"] +
             "Widths: project road inventory / cross sections. " + SRC, fontsize=7.5, color="#666666")
    fig.savefig(f"{OUT}/A_map_travel_speed.png")
    plt.close(fig)


# ---------------------------------------------------------------- B. PCU maps
def chart_map_pcu():
    fig, axes = plt.subplots(1, 3, figsize=(21, 9))
    fig.subplots_adjust(wspace=0.02, top=0.86, bottom=0.1)
    today = {r["seg"]: r["today_pcu"] for r in ROWS}
    best = {r["seg"]: r["best_pcu"] for r in ROWS}
    up = {r["seg"]: r["uplift_pcu"] for r in ROWS}
    norm = Normalize(*L.get("pcu_range", (3500, 7000)))
    cmap = GOOGLE_CMAP  # red = little capacity, green = plenty
    panels = [(axes[0], today, norm, cmap, "1. TODAY\ncapacity (PCU/h)  |  minutes to drive it at 10 am", "today"),
              (axes[1], best, norm, cmap, "2. SAME ROAD, DONE RIGHT\nrules followed + standard design", "best"),
              (axes[2], up, Normalize(0, 3500), plt.cm.Greens, "3. GAIN (2 minus 1)\nextra PCU/h  |  minutes saved", "up")]
    for ax, vals, nm, cm, title, kind in panels:
        draw_route(ax, vals, cm, nm, width=12)
        items = []
        for s in SEGMENTS:
            r = BY_ID[s["id"]]
            p = point_along(s["id"], 0.5)
            if kind == "today":
                t = f"{s['id']}. {r['today_pcu']:,} PCU  |  {r['min_today']:.1f} min"
            elif kind == "best":
                t = f"{s['id']}. {r['best_pcu']:,} PCU  |  {r['min_fix']:.1f} min"
            else:
                t = f"{s['id']}. +{r['uplift_pcu']:,} (+{r['uplift_pct']}%)  |  -{r['saved_fix_min']:.1f} min"
            items.append((p[0], p[1], t))
        span = SPAN
        column_labels(ax, items, LON_MAX + 0.045 * span, gap=L.get("label_gap_pcu", 0.052) * span, fs=9.5)
        ax.set_xlim(LON_MIN - 0.045 * span, LON_MAX + L.get("pcu_right", 0.45) * span)
        ax.set_ylim(LAT_MID - 0.56 * span, LAT_MID + 0.56 * span)
        base_axes(ax, title)
        sm = plt.cm.ScalarMappable(norm=nm, cmap=cm)
        fig.colorbar(sm, ax=ax, shrink=0.55, pad=0.02, orientation="horizontal", label="PCU per hour")
    for ax in axes:
        end_labels(ax)
    s = SM.corridor_summary(ROWS)
    fig.suptitle("How many vehicles each stretch can pass in the peak hour (PCU = car-equivalents, both directions)",
                 x=0.01, y=0.97, ha="left", fontsize=15, weight="bold")
    tt, tf = s["Today"][3], s["Fix the ground (no flyover)"][3]
    fig.text(0.01, 0.015,
             f"Whole trip at 10 am: {tt:.0f} min today -> {tf:.0f} min done right (same traffic as today). "
             f"End to end the corridor passes only as much as its weakest stretch: today ~{s['Today'][0]:,} PCU/h "
             f"({s['Today'][2]}); done right ~{s['Fix the ground (no flyover)'][0]:,} PCU/h. "
             "1 PCU = 1 car; a 2-wheeler = 0.75, auto = 2, bus = 3.7 (IRC:106).\n"
             + L["pcu_note"] + SRC,
             fontsize=8, color="#555555")
    fig.savefig(f"{OUT}/B_map_pcu_today_best.png")
    plt.close(fig)


# ---------------------------------------------------------------- C. flyover vs ground, per segment
def chart_flyover_vs_ground():
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(14, 11), sharex=True, gridspec_kw={"hspace": 0.12})
    x = np.arange(len(ROWS))
    w = 0.38
    names = [f"{r['seg']}. {r['name']}" for r in ROWS]
    # top: capacity
    g = [r["uplift_pcu"] for r in ROWS]
    f = [r["flyover_uplift_pcu"] for r in ROWS]
    ax.bar(x - w / 2, g, w, color="#2e7d32", label="Fix the ground: rules + standard design (no new lanes)")
    ax.bar(x + w / 2, f, w, color="#ef6c00", label=f"{L['flyover']} (ground left as today)")
    for i, (a, b) in enumerate(zip(g, f)):
        ax.text(i - w / 2, a + 60, f"+{a:,}", ha="center", fontsize=8.5, color="#2e7d32")
        ax.text(i + w / 2, b + 60, f"+{b:,}" if b else "0\nno deck", ha="center", fontsize=8.5, color="#ef6c00")
    ax.set_ylim(0, max(f) * 1.25)
    ax.set_ylabel("Extra capacity\n(PCU/h, both ways)")
    ax.legend(loc="upper left", fontsize=10, frameon=False)
    ax.set_title("Stretch by stretch: what fixing the ground adds vs what the flyover adds", loc="left",
                 fontsize=14, weight="bold")
    # bottom: minutes saved at 10 am
    gs = [r["saved_fix_min"] for r in ROWS]
    fs = [r["saved_flyover_min"] for r in ROWS]
    ax2.bar(x - w / 2, gs, w, color="#2e7d32")
    ax2.bar(x + w / 2, fs, w, color="#ef6c00")
    for i, (a, b) in enumerate(zip(gs, fs)):
        ax2.text(i - w / 2, a + 0.05, f"{a:.1f}", ha="center", fontsize=8.5, color="#2e7d32")
        ax2.text(i + w / 2, b + 0.05, f"{b:.1f}" if b > 0.05 else "0", ha="center", fontsize=8.5, color="#ef6c00")
    ax2.set_ylim(0, max(gs + fs) * 1.35)
    ax2.set_ylabel("Minutes saved on this stretch\n(10 am, same traffic as today)")
    tg, tf = sum(gs), sum(fs)
    ax2.text(0.99, 0.95, f"Whole trip: fix the ground saves {tg:.1f} min,  flyover saves {tf:.1f} min",
             transform=ax2.transAxes, ha="right", va="top", fontsize=11, weight="bold")
    for a in (ax, ax2):
        if L["gap_span"]:
            a.axvspan(*L["gap_span"], color="#ffcdd2", alpha=0.35, zorder=0)
        a.spines[["top", "right"]].set_visible(False)
    if L["gap_span"]:
        ax.text(sum(L["gap_span"]) / 2, max(f) * 0.95, L["gap_text"], ha="center", va="top", fontsize=9.5,
                color="#b71c1c")
    ax2.set_xticks(x, names, rotation=35, ha="right", fontsize=9)
    fig.subplots_adjust(bottom=0.2, top=0.95)
    fig.text(0.01, 0.0, L["flyover_note"] + "\n"
             "Minutes: Google 10 am time, re-computed with the extra capacity for the same traffic (BPR curve). "
             + SRC, fontsize=8, color="#555555")
    fig.savefig(f"{OUT}/C_flyover_vs_ground.png")
    plt.close(fig)


# ---------------------------------------------------------------- D. end-to-end throughput
def chart_corridor():
    s = SM.corridor_summary(ROWS)
    opts = [("Today", "Today", "#9e9e9e"),
            ("Flyover (DPR), ground as today", f"+ {L['flyover']}", "#ef6c00"),
            ("Flyover + Ejipura flyover, ground as today", "+ flyover + Ejipura flyover", "#ffa726"),
            ("Fix the ground (no flyover)", "Fix the ground, no flyover", "#2e7d32"),
            ("Fix the ground + Ejipura flyover", "Fix the ground + Ejipura flyover", "#66bb6a"),
            ("Fix the ground + flyover + Ejipura flyover", "Fix the ground + both flyovers", "#a5d6a7"),
            ("Fix the ground + flyover", "Fix the ground + flyover", "#a5d6a7")]
    opts = [o for o in opts if o[0] in s]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(16, 6), sharey=True, gridspec_kw={"wspace": 0.05})
    y = np.arange(len(opts))[::-1]
    base_q, base_t = s["Today"][0], s["Today"][3]
    for yi, (k, _, col) in zip(y, opts):
        q, seg, name, t = s[k]
        a1.barh(yi, q, color=col)
        a1.text(q + 60, yi, f"{q:,}  ({100 * (q / base_q - 1):+.0f}%)", va="center", fontsize=10)
        a2.barh(yi, t, color=col)
        a2.text(t + 0.5, yi, f"{t:.0f} min" + (f"  (-{base_t - t:.0f} min)" if k != "Today" else ""),
                va="center", fontsize=10)
    a1.set_yticks(y, [o[1] for o in opts], fontsize=11)
    a1.set_xlim(0, max(s[o[0]][0] for o in opts) * 1.35)
    a2.set_xlim(0, base_t * 1.45)
    a1.set_title("How much traffic can make the WHOLE trip\n(PCU/h, both ways = the weakest stretch)", loc="left",
                 fontsize=12)
    a2.set_title("Start-to-end trip time at 10 am, typical day\n(average of both directions, same traffic as today)",
                 loc="left", fontsize=12)
    for a in (a1, a2):
        a.spines[["top", "right"]].set_visible(False)
    fig.suptitle("End to end: capacity and trip time for each option", x=0.01, ha="left", fontsize=15,
                 weight="bold", y=1.02)
    fig.text(0.01, -0.1, L["d_note"] + "\n"
             "Right: at TODAY's traffic the flyover does cut trip time. With growth, a corridor that cannot pass more "
             "vehicles fills up again and those minutes are lost; extra trips attracted by new roads are not counted.\n"
             + ("The Ejipura flyover is a separate project already under construction. " if L["has_second_flyover"]
                else "") + SRC, fontsize=8, color="#555555")
    fig.savefig(f"{OUT}/D_corridor_throughput.png")
    plt.close(fig)


# ---------------------------------------------------------------- E. start to end trip time
def chart_trip_time():
    trips = SM.trip_times(ROWS)
    conds = ["Typical day, 10 am", "Typical day, 6 pm", "Bad day, 10 am", "Bad day, 6 pm"]
    opts = [o[0] for o in SM.TRIP_OPTIONS]
    colors = (["#9e9e9e", "#ef6c00", "#ffa726", "#2e7d32", "#66bb6a", "#a5d6a7"] if L["has_second_flyover"]
              else ["#9e9e9e", "#ef6c00", "#2e7d32", "#a5d6a7"])
    fig, axes = plt.subplots(1, 2, figsize=(17, 7.5), sharey=True, gridspec_kw={"wspace": 0.04})
    fig.subplots_adjust(left=0.05, right=0.99)
    for ax, d in zip(axes, [SM.TO_END, SM.TO_START]):
        x = np.arange(len(conds))
        w = 0.8 / len(opts)
        for j, (o, col) in enumerate(zip(opts, colors)):
            vals = [next(t for t in trips if t["condition"] == cnd and t["direction"] == d and t["option"] == o)
                    for cnd in conds]
            xs = x + (j - (len(opts) - 1) / 2) * w
            ax.bar(xs, [v["minutes"] for v in vals], w, color=col, label=o)
            for xi, v in zip(xs, vals):
                ax.text(xi, v["minutes"] + 0.8, f"{v['minutes']:.0f}", ha="center", fontsize=8)
                if v["saved_min"] > 0:
                    ax.text(xi, v["minutes"] / 2, f"-{v['saved_min']:.0f}", ha="center", fontsize=7.5,
                            color="white", rotation=90, weight="bold")
        ax.set_xticks(x, conds, fontsize=11)
        ax.set_title(f"{L['start_short']} -> {L['end_short']}" if d == SM.TO_END
                     else f"{L['end_short']} -> {L['start_short']}", loc="left", fontsize=13)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Start-to-end trip time (minutes)")
    axes[0].legend(loc="upper left", fontsize=9.5, frameon=False, ncol=2)
    top = max(t["minutes"] for t in trips if t["direction"] != "round trip")
    axes[0].set_ylim(0, top * 1.2)
    commute = {t["option"]: t for t in trips if t["direction"] == "round trip"}
    fig.suptitle("How long the whole trip takes (number on top) and minutes saved (white, inside the bar)",
                 x=0.01, ha="left", fontsize=15, weight="bold", y=1.0)
    fx, fl = commute["Fix the ground, no flyover"], commute[L["flyover"]]
    fa = commute[opts[-1]]
    fig.text(0.01, -0.06,
             f"Daily commute (there at 10 am, back at 6 pm, typical day): today {commute['Today']['minutes']:.0f} min/day. "
             f"Fix the ground saves {fx['saved_min']:.0f} min/day (~{fx['hours_saved_per_year']} h/year); "
             f"flyover saves {fl['saved_min']:.0f} min/day (~{fl['hours_saved_per_year']} h/year); "
             f"{opts[-1].lower()} saves {fa['saved_min']:.0f} min/day (~{fa['hours_saved_per_year']} h/year), "
             "250 working days.\n"
             "Typical and bad day = Google's 'best guess' and 'pessimistic' whole-route times for Tue 17 Nov 2026. "
             "Savings are for TODAY's traffic; with growth, options that do not raise end-to-end capacity "
             "(flyover alone) lose their minutes first. " + SRC, fontsize=8.5, color="#444444")
    fig.savefig(f"{OUT}/E_trip_time_start_to_end.png")
    plt.close(fig)


def build_pdf():
    """One PDF: summary page + the four charts, for sharing."""
    import matplotlib.image as mpimg
    from matplotlib.backends.backend_pdf import PdfPages
    trips = SM.trip_times(ROWS)
    T = {(t["condition"], t["direction"], t["option"]): t for t in trips}
    g = lambda cond, opt: T[(cond, SM.TO_END, opt)]
    FL, ALL = L["flyover"], SM.TRIP_OPTIONS[-1][0]
    t6 = sum(SM.google_times()[0][i][6] for i in BY_ID) / 60
    s = SM.corridor_summary(ROWS)
    q0, qf = s["Today"][0], s["Flyover (DPR), ground as today"][0]
    qg = s["Fix the ground (no flyover)"][0]
    cm = {t["option"]: t for t in trips if t["direction"] == "round trip"}
    lines = [
        f"{L['trip']} ({L['length_txt']}) today: {g('Typical day, 10 am', 'Today')['minutes']:.0f} min at 10 am, "
        f"{g('Typical day, 6 pm', 'Today')['minutes']:.0f} min at 6 pm, up to {g('Bad day, 6 pm', 'Today')['minutes']:.0f} "
        f"min on a bad day (6 am: {t6:.0f} min).",
        f"Fix the ground (rules + standard design, no new lanes): saves {g('Typical day, 10 am', 'Fix the ground, no flyover')['saved_min']:.0f}"
        f"-{g('Typical day, 6 pm', 'Fix the ground, no flyover')['saved_min']:.0f} min per trip on a typical day, "
        f"{g('Bad day, 6 pm', 'Fix the ground, no flyover')['saved_min']:.0f} on a bad day; "
        f"{100 * (qg / q0 - 1):+.0f}% vehicles end to end.",
        f"{FL} alone: saves {g('Typical day, 10 am', FL)['saved_min']:.0f} min "
        f"(typical), {g('Bad day, 6 pm', FL)['saved_min']:.0f} (bad day); {100 * (qf / q0 - 1):+.0f}% vehicles end to end.",
        L.get("pdf_line", ""),
        f"Daily commute (10 am there, 6 pm back): today {cm['Today']['minutes']:.0f} min. Fix the ground saves "
        f"{cm['Fix the ground, no flyover']['saved_min']:.0f} min/day (~{cm['Fix the ground, no flyover']['hours_saved_per_year']} h/yr); "
        f"flyover {cm[FL]['saved_min']:.0f} (~{cm[FL]['hours_saved_per_year']} h/yr); "
        f"{ALL.lower()} {cm[ALL]['saved_min']:.0f} (~{cm[ALL]['hours_saved_per_year']} h/yr).",
        "Fix the ground first, re-measure, then decide.",
    ]
    lines = [x for x in lines if x]
    pages = [(L["pdf_title"], lines, None),
             ("1. The road today (Google speed at 10 am)", [], "A_map_travel_speed.png"),
             ("2. Each stretch: capacity and minutes, today vs done right", [], "B_map_pcu_today_best.png"),
             ("3. Fixing the ground vs the flyover: capacity and minutes saved", [], "C_flyover_vs_ground.png"),
             ("4. End to end: capacity and trip time", [], "D_corridor_throughput.png"),
             ("5. Start to end: trip time and minutes saved (typical and bad day)", [], "E_trip_time_start_to_end.png")]
    with PdfPages(f"{OUT}/EXPLAINER_{SM.NAME}.pdf") as pdf:
        for title, text, img in pages:
            fig = plt.figure(figsize=(16.5, 11.7))  # A3 landscape
            if img is None:
                fig.text(0.05, 0.82, title, fontsize=26, weight="bold")
                for i, l in enumerate(text):
                    fig.text(0.05, 0.7 - i * 0.075, l, fontsize=15.5)
                fig.text(0.05, 0.1, "Data: B-SMILE DPR (Feb 2026), IRC:106-1990, HCM 2010, Google Routes API "
                         f"(Tue 17 Nov 2026). Method and caveats: EXPLAINER_{SM.NAME}.md", fontsize=11, color="#666666")
            else:
                ax = fig.add_axes([0.02, 0.02, 0.96, 0.9])
                ax.imshow(mpimg.imread(f"{OUT}/{img}"))
                ax.axis("off")
                fig.text(0.02, 0.95, title, fontsize=20, weight="bold")
            pdf.savefig(fig)
            plt.close(fig)


if __name__ == "__main__":
    for f in [chart_map_speed, chart_map_pcu, chart_flyover_vs_ground, chart_corridor, chart_trip_time, build_pdf]:
        f()
        print("done", f.__name__)
