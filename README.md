# Is the flyover needed, or is the road just badly run?

### Two proposed Bengaluru elevated corridors, tested on the road that already exists

The animation includes a shared **PCU demand slider (0–24,000 PCU/h per road)** and an **upper-road violation slider (0–100%)**. Actual-PCU budgeting, offered/admitted/outflow readouts and visible entry queues make demand auditable. **Simulation V/C** uses a measured discharge benchmark from this animation (`node traffic_flow_capacity_audit.js`), rather than the different corridor-model capacities. Default V is the **8,000 PCU/h comparison scenario**; 3,996 remains a DPR reference preset and 16,000 overloads both roads. **+5 simulated min** reveals queue growth without waiting. Releasing either slider restarts the comparison and resets measurements.

Live completed-trip travel time can be extrapolated from the 125 m scene to **10, 12 or 15 km**. **End simulation** freezes the run and compares averages, admitted vehicles/cars, completed and unfinished trips, entry queues and percentage changes. The extrapolation repeats the same conditions; it is not a calibrated route forecast, and averages exclude unfinished trips and off-road waiting.

The violation slider includes a live category breakdown. At 100% it adds **8 wrongly parked vehicles**, extra car/auto stops and delivery loading, plus a larger cohort of smaller-gap cutting drivers. Bus frequency and boarding duration stay unchanged. Demand identities/PCUs and lower-road behaviour remain shared/independent respectively; the simulation-capacity benchmark is refreshed for these dynamics.

**Visual comparison:** Open [`traffic_flow_comparison.html`](traffic_flow_comparison.html) in a browser, keeping `traffic_flow_model.js` and `traffic_flow_view.js` beside it (no server or install required). The black-and-white two-way animation now uses continuous mixed-traffic motion informed by reviewed Chennai video frame sequences: bikes filter through narrow gaps, cars follow in staggered positions, and passing traffic reacts to the actual width of parked vehicles. The same autos, cars and buses make passenger stops in both panels, with bays below. Use Play/Pause, 2× speed, Paths, and Restart. [Footage, model equations and assumptions](traffic_flow_sources.md) explain the IDM/MTM-inspired dynamics; this is illustrative, not calibrated. Run `node --test traffic_flow_model.test.js` for interaction and geometry checks.

| Corridor | Proposal | Today (peak, two-way) | Same road, all fixes | Gain |
|---|---|---|---|---|
| **Old Madras Rd → Indiranagar → Domlur → Ejipura → Silk Board** | Rs 1,300 cr, 13 km of deck (DPR Feb 2026) | 3,996 PCU/h (DPR count) | 5,143 PCU/h | **+29%** |
| **Mysore Rd: Sirsi Circle → Satellite Bus Stand → Nayandahalli** | Rs 538 cr tender / Rs 810 cr incl. land | ~5,840 PCU/h (*estimated*, no count exists) | 7,714 PCU/h | **+32%** |

A DPR counts traffic on a road where people park in the lane, buses stop with no bays, pedestrians walk on the carriageway because footpaths are broken, signals are overridden by hand and nobody keeps to a lane. It compares that count with IRC capacity and concludes the road is full.

This model asks two things:

- How much more would the **same lanes** carry if the street were designed and run to standard (IRC:106, HCM)?
- When would demand actually fill that?

> **Plain-language explainers, stretch by stretch with maps, minutes saved and a PDF:**
>
> - [`explainer_silk_board/EXPLAINER_silk_board.md`](explainer_silk_board/EXPLAINER_silk_board.md): the flyover skips Domlur -> Sony World, where the corridor chokes. Fixing the ground saves 8-11 min per trip on a typical day (up to 25 on a bad day) and lifts end-to-end capacity by 42%. The flyover saves about 8 min but adds 0% end to end.
> - [`explainer_mysore_road/EXPLAINER_mysore_road.md`](explainer_mysore_road/EXPLAINER_mysore_road.md): there is no traffic data in the tender. On this short, about 2.5 km stretch the deck covers everything, so the flyover beats fixing the ground (4.5 vs 2.6 min at 10 am). The extra gain is about 1-2 min a day for a commuter, and its two ends (BGS flyover, Nayandahalli) are not analysed.

## Results: Silk Board corridor

| Scenario (same 4 lanes) | PCU/h | vs today | Peak trip (10.3 km) | Demand fills it in |
|---|---|---|---|---|
| Worst day (everything breaks) | 2,646 | −34% | 70 min | – |
| **Today** (DPR count + Google) | **3,996** | 0 | **43 min** | 2026 |
| + Enforcement (towing, no stopping, yellow boxes, vendors) | 4,340 | +9% | 40 min | 2029 |
| + Signals (adaptive, no manual override) | 4,205 | +5% | 41 min | 2028 |
| + Street design (bus bays, footpaths, markings, median gaps) | 4,459 | +12% | 39 min | 2029 |
| Enforcement + signals, **no construction** | 4,566 | +14% | 39 min | 2030 |
| Enforcement + signals + design | 5,095 | +27% | 36 min | 2033 |
| Everything fixed = IRC arterial | 5,143 | +29% | 35 min | 2033 |
| + re-use the 3–5 m paver strip as a 3rd lane (IRC 6-lane) | 7,714 | +93% | – | 2045 |

### People per hour

This is the peak hour in both directions, from the DPR vehicle count × occupancy:

| Option | People/h |
|---|---|
| Today | 9,593 |
| Fix the road, no flyover | 10,814 |
| Today + flyover (Rs 1,300 cr, deck full of private vehicles) | 16,827 |
| Fix the road + bus lane in the existing paver strip | 16,489 |
| Fix the road + take 1 lane each way for buses | 13,045 |

Buses are **3% of vehicles but carry 47% of the people**. A bus lane in the existing paver strip moves about as many people as the flyover, for a small fraction of the cost. The flyover number is also flattering, because it assumes no induced traffic.

**Caveat:** the paver strip only exists along about 5 of the 10 km (100 Ft Rd and IRR).

## Results: Mysore Road corridor

| Scenario (same 6 lanes at the 9.8 m pinch) | PCU/h | vs today | Peak trip (2.3 km, westbound) | Demand fills it in |
|---|---|---|---|---|
| Worst day | 3,989 | −32% | 10 min | – |
| **Today** (*estimated*) | **5,840** | 0 | **7.6 min** | 2026 |
| Enforcement + signals, no construction | 6,638 | +14% | 7.1 min | 2030 |
| Enforcement + signals + design | 7,593 | +30% | 6.7 min | 2033 |
| Everything fixed = IRC 6-lane arterial | 7,714 | +32% | 6.7 min | 2034 |
| + widen the 0.7 km Limgappa/Gopalan pinch to 4 lanes (IRC 8-lane) | 10,286 | +76% | – | 2041 |

**The Mysore Road project documents contain no traffic data at all.** That means no count, no PCU figures, no forecast and no speed survey. The Rs 538 cr tender is being floated without a published traffic justification. That finding may matter more for the slides than any number here.

For the model, "today" is estimated as the IRC best case × the same friction factors, using the overlap exponent calibrated on Silk Board. Demand growth is assumed at 3.9%/yr, the Silk Board DPR's rate. Google travel times are real:

| Google travel time, 2.3 km westbound | Minutes |
|---|---|
| 6 am | 5.5 |
| 10 am typical | 7.6 |
| 10 am, bad day | 12 |
| 7 pm, worst hour | 12 (bad day 17) |

The eastbound morning run towards Sirsi Circle is the slowest: 14.5 min at 10 am, 21 on a bad day. That figure is in the explainer.

**Correction (15 Nov):** the first Mysore fetch let Google add a U-turn loop near Sirsi Circle, giving 3.2 km and 11 min. The route is now pinned to the main road (2.3 km). The capacity numbers are unchanged.

The binding problems on this corridor are:

- the Satellite Bus Stand (~800 buses/day, buses stopping at undesignated spots);
- 43 cross roads and 8 fuel stations opening directly onto the main road, with no service road;
- a 0.7 km pinch at 26 m ROW, where RMP-2015 already plans 30–45 m.

## Ghost jams (both corridors)

This is a micro-simulation of one lane, with no bottleneck, no signals and no width change; only driver behaviour varies.

| Behaviour | Max throughput (veh/h/lane) |
|---|---|
| Disciplined | 2,000 |
| Erratic braking | 1,380 |
| + slow restarts | 900 |
| + kerbside stops | 840 |

Stop-and-go waves form and travel backwards with no cause. The real-world equivalents are Sugiyama et al. 2008 (a jam on a ring road with no bottleneck) and Stern et al. 2018 (one smooth driver among 20 or more damps the waves).

## Ground check (Google, Tuesday 17 Nov 2026)

On Silk Board, the model reproduces Google:

| Model | Model time | Google | Google time |
|---|---|---|---|
| Worst day | 70 min | Pessimistic, 10 am | 72 min |
| Today | 43 min | Typical | 43 min |

Google's optimistic day (30 min) implies more capacity than the model's best case, so the best case is not optimistic.

## What this says (and doesn't)

- **It says** about a third of the measured "capacity problem" on both corridors comes from management and design, not lane count.
- **It says** the cheapest package (enforcement + signals, no construction) buys about 3–4 years, and the full at-grade fix buys about 7–8.
- **It says** a bus lane matches the flyover on people moved.
- **It does not say** the corridors never need more capacity. Demand keeps growing and every option fills eventually.
- **The argument is about order:** fix the at-grade road and run buses properly, re-measure, then decide on the Rs 1,300 cr and Rs 538–810 cr structures.
- **Not modelled:** induced demand (Duranton & Turner 2011, elasticity ~1), which works *against* flyovers, and network effects such as bottlenecks moving to the flyover ends.

## How the model works (one slide)

1. **Best case = the same road run properly.** This is the IRC:106-1990 design service volume for an **arterial** (no standing vehicles, controlled access, little cross traffic) ÷ 0.70 to convert LOS C to capacity:
   - 4-lane: 3,600 / 0.7 = 5,143 PCU/h.
   - 6-lane: 5,400 / 0.7 = 7,714 PCU/h.
2. **Today = what was counted.** On Silk Board, the peak is saturated (Google's 10 am trip takes ~2× the 6 am trip), so the DPR count *is* today's practical capacity.
3. **The gap is split among 9 frictions.** Each has a factor from a standard or study (table below). The factors overlap, so all are shrunk by one exponent, **K = 0.31**, chosen on Silk Board so that the product equals today/best. Each friction keeps its relative weight.

   `capacity = best × Π (factor_i ^ K)` over the frictions **not** fixed.
4. **Worst day** = each friction's "worst" factor through the same formula.
5. **Travel time** = `t_6am × (1 + A × (demand/capacity)²)`. Both `t_6am` and `A` come from Google's 6 am and 10 am times.
6. **Ghost jams** use the Nagel-Schreckenberg cellular automaton (1992) with slow-to-start (Barlovic 1998).

## Assumptions (all in `inputs_<corridor>.py`; change and re-run)

| Friction | Fix | Silk Bd today / worst | Mysore Rd today / worst | Basis | Type |
|---|---|---|---|---|---|
| Parking / stopping in lane | Towing | 0.88 / 0.65 | 0.89 / 0.72 | HCM parking factor; 30 (SB) and 45 (MR) manoeuvres/h | formula + estimate |
| Encroachment | Clear vendors, debris | 0.95 / 0.83 | 0.95 / 0.85 | Width lost; flow ∝ width (IRC:SP:41) | formula + estimate |
| Junction blocking, stop-go | Yellow boxes | 0.92 / 0.85 | same | Capacity drop 5–20% (Hall 1991; Cassidy & Bertini 1999) | published |
| Buses stopping in lane | Bus bays | 0.87 / 0.75 | 0.84 / 0.71 | HCM bus blockage; 67 buses/h (DPR), 120 (MR, estimated) | formula |
| Pedestrians on carriageway | Footpaths, crossings | 0.90 / 0.70 | 0.87 / 0.70 | −30% at 1,360 ped/h (Dhamaniya & Chandra 2014) | published + estimate |
| Lane discipline | Markings | 0.95 / 0.88 | same | Weakest number; two-wheelers can gain from filtering | estimate |
| Median gaps, side entries | Close / service roads | 0.95 / 0.88 | 0.93 / 0.85 | 108 (SB) and 43 in 3.5 km (MR) cross roads | estimate |
| Signal timing | Adaptive, no override | 0.85 / 0.77 | same | BTP adaptive signals: +18–30% throughput | published (agency) |
| Surface / drainage | Maintain | 0.97 / 0.80 | 0.95 / 0.80 | Waterlogging in DPR photos and news | estimate |

**Known weaknesses (say these on the slide):**

- Silk Board rests on one DPR count, at one location, on one day.
- Mysore Road has no count at all.
- "Today = capacity" assumes the peak is saturated.
- 4 of the 9 factors are estimates.
- Each corridor is treated as one road, not junction by junction.
- PCU factors are IRC's static values.
- Occupancies are assumptions: 2W 1.2, car 1.5, auto 1.8, bus 40.

**Robustness:** the best case is anchored to IRC, so it doesn't depend on the factors. Changing any one estimated factor by ±50% moves the "Enforce + Signals" result by under 1%.

## Charts

| Chart | Silk Board | Mysore Road |
|---|---|---|
| Capacity ladder, worst → today → best | `outputs/silk_board/1_capacity_ladder.png` | `outputs/mysore_road/1_capacity_ladder.png` |
| One fix at a time | `2_single_interventions.png` | same name |
| Package pairs | `3_package_combinations.png` | same name |
| All 512 combinations | `4_all_512_combinations.png` | same name |
| Years until demand fills each option | `5_years_of_headroom.png` | same name |
| Google ground truth by hour | `6_google_ground_truth.png` | same name |
| People per hour: bus lane vs flyover | `8_people_per_hour.png` | – (no vehicle count) |
| Ghost jams | `outputs/7_ghost_jams.png` (shared) | |

## Run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python ghost_jam.py                                   # shared micro-simulation (~20 s)
for c in silk_board mysore_road; do
  CORRIDOR=$c python fetch_google.py                  # optional; needs GOOGLE_MAPS_API_KEY in .env
  CORRIDOR=$c python model.py                         # tables -> outputs/<corridor>/*.csv
  CORRIDOR=$c python charts.py                        # charts -> outputs/<corridor>/*.png
done
for c in silk_board mysore_road; do
  CORRIDOR=$c python fetch_segments.py      # optional: per-segment Google times (6 calls per segment)
  CORRIDOR=$c python segment_model.py       # per-segment + trip tables -> explainer_<corridor>/
  CORRIDOR=$c python segment_charts.py      # maps A-E + PDF -> explainer_<corridor>/
done
```

## Files

| File | Contents |
|---|---|
| `inputs_silk_board.py`, `inputs_mysore_road.py` | Every number, with its source |
| `corridor.py` | Picks the corridor from `CORRIDOR=` |
| `model.py` | Capacity, combinations, travel time, years, people/h |
| `ghost_jam.py` | Behaviour-only micro-simulation |
| `charts.py` | PNGs |
| `fetch_google.py` | Google Routes sampler (whole route) |
| `segments_silk_board.py` | 10 Silk Board segments: widths, lanes, signals, turns, friction severity, flyover lanes, Google points |
| `fetch_segments.py` | Google times and road shape for each segment |
| `segment_model.py`, `segment_charts.py` | Per-segment capacity and minutes (today, done right, flyover), weakest link, maps A-D and the PDF |
| `explainer_silk_board/`, `explainer_mysore_road/` | **Plain-language explainers**: `EXPLAINER_*.md`, PDF, charts A-E, `segments.csv`, `trip_times.csv` |
| `segments_mysore_road.py` | 5 Mysore Rd segments (same fields as Silk Board) |
| `data/dpr_hourly_counts.csv` | Silk Board DPR Table 5-1 |
| `data/google_times_*.csv` | Google travel times |
| `NOTES.md` | Detailed research notes (DPR, standards, ground reality) |
| `scratch/` | Extracted PDF text and route-probe scripts |
