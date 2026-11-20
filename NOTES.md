# Work in progress: Silk Board corridor capacity simulation

**Status (14 Nov 2026): BOTH corridors DONE.** Results, assumptions and run steps are in README.md. Charts are in outputs/<corridor>/. Code: inputs_silk_board.py, inputs_mysore_road.py, corridor.py, model.py, ghost_jam.py, charts.py, fetch_google.py. Google data has been fetched for both corridors (Tue 17 Nov 2026).
Mysore Road findings: the docs have NO traffic data. The tender is Rs 538.28 cr (RFP p.3), or Rs 810 cr including land (Legislative Council, 12 Mar 2026). The road has 7 signals, 43 cross roads and 15 bus stops; the Satellite Bus Stand (~800 buses/day) is at ch ~2.1; the binding section is ch 0.7-1.4 at 26 m ROW, 9.8/12.0 m carriageway. Metro pillars run on the south edge from ch 2.8 to 3.45, not in the median. The extracted text is in scratch/doc_text_mysore/.
Segment view (added 14 Nov): segments_silk_board.py, fetch_segments.py, segment_model.py, segment_charts.py, explainer_silk_board/ (EXPLAINER_silk_board.md, PDF, charts A-D, segments.csv). Minutes saved per segment and option are added (same traffic as today, BPR). Severity grades per segment are estimates.
Mysore explainer (15 Nov): segments_mysore_road.py (5 segments, from the BGS ramp touch-down to Nayandahalli, Sirsi Circle excluded); segment code is now generic (CORRIDOR=...); full-route Google points are pinned with headings (the old 3.2 km route included a U-turn loop). Output is in explainer_mysore_road/.
Open items: Street View images (the API is not enabled on the key); per-junction modelling if needed.

## Goal

Simulate the Old Madras Road -> Indiranagar 100 Ft Rd -> Domlur -> IRR/Ejipura -> Sony World -> Madiwala -> Silk Board corridor under a range of conditions:

- **Worst case:** everything breaks down.
- **Today:** calibrated to the DPR traffic count and Google travel times.
- **Best practice:** all interventions applied.
- **In between:** single interventions, and groups of interventions.

The point is to show that the throughput measured today is depressed by friction and indiscipline. A flyover justified on that measured number may not be needed yet. The code must stay simple enough to explain on one slide deck.

## Repo state

- The old code (`bangalore_traffic/`, `dashboard/`, `tests/`, `data/`, `pyproject.toml`) has been deleted for good, as the user agreed. It was never committed, so it can't be recovered from git.
- `README.md` is still the **old** README. Replace it once the new model exists.
- `fetch_google.py` is a **draft**. It imports `inputs.py`, which does not exist yet. Its waypoint logic also needs the fix described in "Google Routes probes" below.
- `.env` holds `GOOGLE_MAPS_API_KEY`. The **Routes API works**. The **Street View Static API returns REQUEST_DENIED** because it is not enabled on the Cloud project, so enable it before fetching images.

## Facts from the docs (DPR = `docs/silkboardroaddocs/dpr-omr-to-silk-board (1).pdf`)

PDF page = printed page + 6.

### Corridor

- **Length:** 0+000 at the Swami Vivekananda Rd metro to 9+800 at Silk Board (10.975 km including the run to Begur Rd).
- **Junctions and stops:** 13 signalised junctions, 108 cross roads and 46 bus stops. None of the bus stops has a bay. There are no service roads.
- **Surface:** white-topped (concrete) from 0 to 4.43 km, asphalt after that.

### Homogeneous sections (from the DPR inventory and `tcs.pdf`)

| Section | Chainage (km) | Carriageway per direction | Median | Signals |
|---|---|---|---|---|
| 80 Ft Rd / CMH | 0-1.4 | 7.4-8.5 m | 0.8-1.0 m | 3 |
| 100 Ft Rd | 1.4-3.1 | 6.0 m concrete + 3.2-4.8 m paver "buffer" | 0.4 m | 3 |
| Domlur flyover | 3.1-3.6 | grade-separated | - | 0 |
| IRR (defence land) | 3.6-6.3 | 8.5 m + 1.5 m buffer, 22.7 m ROW pinch at 5.19 km | 1.5-2.2 m | 2 |
| Ejipura / Sony World | 6.3-7.05 | 6.3-10.5 m, footpaths missing | none | 1 |
| Ejipura flyover zone | 7.05-8.35 | 10-11.5 m (flyover still under construction) | 2.5 m | 0 |
| Sarjapur Rd / Madiwala | 8.35-9.25 | 8.4-14.5 m, very variable | - | 2 |
| Hosur Rd to Silk Board | 9.25-9.8 | 15-19 m | - | 1 |

On 100 Ft Rd, the DPR's own photos show the buffer strip used for parking, auto stands, bus stops and walking.

### Traffic count (DPR PDF pp.135-140)

- One count, on one day (25 Apr 2025), at one location between Indiranagar and Domlur, 6am-8pm.
- 27,807 vehicles = 30,137 PCU in 14 hours.
- Peak hour was 10-11am: 3,869 veh/h = **3,996 PCU/h in both directions combined**.
- Directional split is about 60/40.
- Mix: two-wheelers 42%, cars 29%, autos 12.5%, buses 3.2%, LCVs 3.7%.
- Hourly table is on PDF p.136. Use it for the time-of-day profile.

### How the DPR justifies the flyover

- IRC-106 design service volume for a 4-lane divided road is 2,900 PCU/h; for a 6-lane road it is 4,300.
- It forecasts 5,664 PCU/h by 2033-38 (at 4-5% growth a year).
- It assumes 50% of traffic moves to the elevated road, with no supporting evidence.
- Cost is ₹1,300 cr in total (₹852 cr civil works). EIRR 16.8%, benefit-cost ratio 1.99.
- **Internal contradictions:** current speed is quoted as 20-25, 30-40 and 10-15 km/h in different places, and a "90 min -> 20 min" saving is claimed.

### DULT review (PDF pp.166-170)

- The alignment is not in CMP 2020.
- The 50% diversion figure is unsubstantiated.
- DULT asked for a **traffic simulation**.
- It called the Madiwala rotary infeasible.
- It said improvement needs at-grade and elevated roads designed together.

## Standards and multipliers

Each multiplier is given as [worst, typical today, best practice].

### IRC:106-1990 design service volumes

| Road | Arterial | Sub-arterial | Collector |
|---|---|---|---|
| 4-lane divided | 3,600 | 2,900 | - |
| 6-lane divided | 5,400 | 4,300 | - |

- Design service volume is about 0.7 x capacity.
- **Cl. 8.4:** an arterial with sub-arterial roadside conditions gets the sub-arterial value. That is a code-sanctioned friction penalty of **0.81**. The collector/arterial ratio is about **0.60**.
- **Cl. 9.2:** lists capacity measures to try before building: ban on-street parking, regulate median gaps, control roadside activity, provide pedestrian facilities, improve lane discipline.

### IRC:106 PCU factors (at 5% share / at 10% or more)

| Vehicle | 5% | ≥10% |
|---|---|---|
| Two-wheeler | 0.5 | 0.75 |
| Auto | 1.2 | 2.0 |
| Bus/truck | 2.2 | 3.7 |
| LCV | 1.4 | 2.0 |

### Indian mid-block capacity

- 1,482-2,105 PCU/h/lane on Indian urban arterials (Dhamaniya & Chandra 2014, 2017).

### HCM signal saturation flow

s = 1900·N·f_w·f_p·f_bb·…

- Lane width: f_w = 1 + (W - 3.6)/9
- Parking: f_p = (N - 0.1 - 18·Nm/3600)/N, which is 0.80 at 60 manoeuvres/h
- Bus blockage: f_bb = (N - 14.4·NB/3600)/N, which is 0.88 at 60 buses/h

### Multipliers by factor

| Factor | Multiplier | Basis |
|---|---|---|
| Composite side friction | [0.40, 0.75, 1] | Biswas, Chandra & Ghosh 2020: up to 60.7% capacity loss |
| On-street parking | [0.70, 0.85, 1] | HCM f_p formula |
| Kerbside bus stop, no bay | [0.80, 0.90, 1] | HCM f_bb formula; Pallela & Mehar 2024 |
| Pedestrians on carriageway | [0.70, 0.90, 1] | -30% at 1,360 ped/h, no effect below 200 ped/h (Dhamaniya & Chandra 2014) |
| Lane discipline | [0.85, 0.92, 1] | **Estimate.** Two-wheelers can *gain* from non-lane flow, so this is the weakest factor |
| Signal timing | [0.75, 0.85, 1] | Bengaluru adaptive-signal (BATCS) claims: +18-30% throughput, -20 to -33% travel time |
| Junction blocking | [0.80, 0.90, 1] | Estimate |
| Capacity drop / stop-and-go | [0.85, 0.92, 1] | 5-20% (Hall 1991, Cassidy & Bertini 1999, Srivastava & Geroliminis 2013); ghost jams shown by Sugiyama 2008 and Stern 2018 |
| Median gaps / U-turns | [0.85, 0.93, 1] | Estimate |
| Potholes / poor surface | [0.90, 0.95, 1] | Mostly affects speed rather than capacity |
| Encroachment | [0.80, 0.90, 1] | Treated as lost effective width |

**Do not multiply all of these together.** Group them so they don't double count:

- **Mid-block group:** parking, bus, pedestrians, encroachment, with a floor.
- **Junction group:** signal timing, blocking, capacity drop.
- Corridor capacity = min(mid-block, junction). The junctions will bind.

## Ground reality

### Speeds

- TomTom 2025, city-wide: 36 min per 10 km on average; 13.9 km/h average rush-hour speed (14.6 km/h morning, 13.2 km/h evening).
- DPR: 20-25 km/h on this corridor.

### Silk Board junction

- 17,816 vehicles between 9:30 and 10:30am, on a 285 s signal cycle (Deccan Herald, Jul 2024).
- After the first half of the double-decker flyover opened, queues fell from 19 km to 10 km.

### Signals

- BTP manually overrides adaptive signals 6% of the time on average, and 17% at the ORR-Hosur "Sarjapur" junction.
- BTP says the standard 180 s cycle is "not sufficient".
- On Old Madras Road, traffic on 100 Ft Rd waits through 2+ signal cycles (The Hindu, Oct 2026).

### Parking and footpaths

- Halasuru police station recorded the city's highest number of parking cases, concentrated on 100 Ft Rd and 80 Ft Rd.
- Footpaths under the Ejipura flyover broke within 4 months of being laid.
- Sony World's right-turn ban forces U-turn weaving.

## Google Routes probes (Tue 17 Nov 2026)

The full corridor, OMR (12.98455, 77.64529) to Silk Board (12.9172, 77.6227) with no waypoints:

| Departure | Distance | Travel time | Speed | Free-flow time | Free-flow speed |
|---|---|---|---|---|---|
| 10:00 IST | 10.3 km | 2,604 s | 14.2 km/h | 2,031 s | 18 km/h |

`staticDuration` is Google's free-flow time, and it still includes signal delay.

**Problem: the KML vertices make bad waypoints.** The KML line (`docs/silkboardroaddocs/9 (1).kml`, 43 points, 11.0 km) is a sketch. When its points are snapped to roads, the southbound direction lands on the wrong carriageway, a flyover, or a service road. Southbound legs come out 2-4x longer than the straight-line distance. For example, Domlur -> IRR is 1.04 km straight but Google returns 3.29 km. Northbound legs are mostly fine.

**Fix to apply next:**

- Use about 6 anchor points at junctions, placed on the correct carriageway for each direction.
- Optionally use `via` waypoints with headings or `sideOfRoad`.
- Accept a leg only if Google's distance is within about 1.3x of the straight-line distance.
- The Routes API allows at most 25 intermediate waypoints.

## Model plan (not yet coded; keep it to about 3 files)

1. **`inputs.py`**: sections (length, carriageway width, lanes, signals, bus stops), vehicle mix and PCU factors, the friction multipliers above (worst/today/best), the list of interventions, and the source for each number.
2. **`model.py`**:
   - Mid-block capacity = base lane capacity (about 1,800-2,000 PCU/h/lane) x effective width x friction factors.
   - Junction capacity = saturation flow (HCM-style) x green/cycle ratio x junction factors.
   - The bottleneck is the minimum of the two.
   - A simple cell-transmission (or BPR + queue) run over the DPR hourly demand profile gives travel time and queues.
   - Run all 2^k combinations of the interventions. Report throughput, peak-hour travel time, and the year when demand growth exceeds capacity (compared with the DPR's 5,664 PCU/h forecast).
3. **`ghost_jam.py`**: a Nagel-Schreckenberg ring road that shows throughput lost purely to random braking and behaviour, on the same road.
4. **`make_charts.py`**:
   - Capacity ladder from worst to today to best.
   - Waterfall of each intervention's contribution.
   - Heatmap of intervention combinations.
   - Demand vs capacity by year (when is a flyover actually needed).
   - Model vs Google travel times by hour.
5. **Calibration:** "today" must reproduce Google's peak travel time of about 14-18 km/h and the DPR's observed peak of about 4,000 PCU/h. Tune only the "today" multipliers, and document what was tuned.
6. Write a new README with an assumptions table, then repeat the same work for the Mysore Road corridor.

## Saved artefacts (do NOT redo)
- `scratch/doc_text/*.txt` — full text of every Silk Board PDF, with `=== PAGE n ===` markers.
- `data/dpr_hourly_counts.csv` — DPR Table 5-1 hourly classified counts, 6am–8pm, typed in from the PDF.
- `scratch/t*.py` — the Google Routes probe scripts.
- Git: this folder is **untracked** in the parent repo `MLExperiments`; it has never been committed. The old code deletion is therefore permanent, which is fine because the plan is to rebuild from scratch.

## Rebuilding the temporary files (only if scratch/doc_text is lost)

The PDF text extraction was in `/var/folders/.../opencode/txt/` and may be lost. To regenerate it, run with `.venv/bin/python` (pymupdf is installed):

```python
import pymupdf, glob, os
for f in glob.glob("docs/silkboardroaddocs/*.pdf"):
    d = pymupdf.open(f)
    open("/tmp/" + os.path.basename(f) + ".txt", "w").write(
        "\n".join(f"=== PAGE {i+1} ===\n" + p.get_text() for i, p in enumerate(d)))
```

The `.venv` has pymupdf, numpy, matplotlib and openpyxl installed. Update `requirements.txt` when writing the code.
