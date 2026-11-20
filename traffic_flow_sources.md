# Traffic animation: observation → model

## Footage reviewed (18 November 2026)

Kanagaraj & Treiber, **Self-Driven Particle Model for Mixed Traffic and Other Disordered Flows**, Physica A 509 (2018), 1–11.

- [Paper and figures](https://arxiv.org/html/1805.05076v1), [DOI](https://doi.org/10.1016/j.physa.2018.05.086).
- [Supplement mmc1: observed medium traffic](https://ars.els-cdn.com/content/image/1-s2.0-S0378437118306356-mmc1.mp4).
- [Supplement mmc2: observed congested traffic](https://ars.els-cdn.com/content/image/1-s2.0-S0378437118306356-mmc2.mp4).
- The clips show an elevated, oblique view of a divided urban road in **Chennai**, not a vertical drone view. Six sequential frames at roughly three-second intervals from each clip were inspected, along with the paper's Figures 1 and 6. This is qualitative visual review, not measured trajectory extraction or continuous human playback.
- Supplement mmc3 was also inspected and is a **simulation**, not observed traffic; it was not used as real-world evidence.
- [ITD, Indian Traffic Dataset](https://github.com/teg-iitr/ITD-Indian-traffic-dataset), Agarwal et al. (2024), provides additional context for vehicle classes and lane/filtering analysis. Its restricted raw dataset was not downloaded or fitted.

The source videos remain at the publisher's URLs; they are not bundled with this project. Some YouTube media URLs returned HTTP 403, so the working publisher supplements were used instead.

## What the footage changed

| Observation | Earlier problem | Current implementation |
|---|---|---|
| Staggered following, not just single-file strings | Every vehicle was tied to a lane ID | Continuous longitudinal `u` and lateral `y` coordinates |
| Motorcycles occupy gaps between wider vehicles | A bike behaved like a small car in a whole lane | Physical dimensions and shorter headways; narrow bodies can select narrow paths |
| Cars adjust sideways by fractions of a lane | Every obstruction forced a complete lane closure | Parked rectangles remove only their physical width; partial lateral paths are possible |
| Drivers respond to the nearest relevant conflicts | A lane change incurred an arbitrary fixed speed cap | Strongest width-weighted IDM interaction; closer lateral encroachment increases braking |
| Dense traffic forms irregular, moving clusters | Clockwork arrivals and synchronized movement | Seeded irregular arrival times, heterogeneous speeds and finite acceleration |

The parked cars, auto pickups and bus dwells are **scenario assumptions**, retained from the requested street example. These clips do not establish their frequency or duration. Mixed traffic is not itself a violation, and filtering does not automatically reduce capacity.

## Model implemented

`traffic_flow_model.js` uses metres and seconds. The view stretches road width modestly for readability (8 px/m longitudinally, 10 px/m laterally).

### Longitudinal motion

The free acceleration and desired gap follow the Intelligent Driver Model (IDM; Treiber, Hennecke & Helbing, 2000):

```text
a_free = a · [1 − (v / v0)^4]
s* = s0 + max(0, v·T + v·(v − v_leader) / [2√(a·b)])
interaction = a · (s* / s)^2
```

For a neighbouring vehicle, lateral edge clearance is

```text
sy = |y − y_neighbour| − (width + width_neighbour)/2
weight = exp(−max(0, sy) / 0.22 m)
acceleration = a_free − max_neighbour(weight · interaction)
```

This lateral attenuation and strongest-leader selection are inspired by Eqs. 7–8 of the Mixed Traffic Flow Model (MTM). The implementation clamps emergency deceleration and uses geometric safeguards. It is **not** the paper's calibrated ACC-based MTM. In particular, its local path search replaces the paper's lateral force field, and its collision safeguards can override comfortable acceleration.

### Sideways motion and merging

At staggered decision intervals, drivers evaluate candidate lateral positions by available acceleration, movement cost and a small position preference. A proposed path must clear nearby bodies and account for closing traffic from behind. Lateral velocity relaxes toward the chosen path with bounded lateral acceleration and a speed-dependent steering rate.

The ordered scene strongly prefers lane centres. The mixed scene can choose any usable lateral position. A car partially intruding into another stream becomes a stronger obstacle to its neighbours through the same clearance-weighted following rule; there is no arbitrary merge slowdown, whole-lane reservation or forced gain for the lower panel.

### Passenger stops

The same identified vehicles receive the same stop locations and seeded dwell durations in both scenes. They decelerate and steer toward the kerb or bay, dwell, then accelerate and rejoin. A full managed bay makes its next arrival wait upstream. Bay re-entry checks rear traffic. An upper-panel pickup unable to reach the kerb may stop where it is, visibly obstructing traffic.

### Fair comparison

Both scenes share:

- Offered arrival times and vehicle identities, including vehicles waiting off-screen.
- Vehicle dimensions and distributions of speed, headway, acceleration and braking.
- Passenger-stop identities and dwell duration.

Different: lateral preferences, stopping space and kerbside parking intrusion. Both scenes use the same model equations. Demand is illustrative, not a site measurement; no throughput target is imposed. Queues waiting to enter are reported in the footer rather than silently discarded.

The display begins after a 25-second pre-run to avoid an empty road. Trip counters reset then; this is not a synchronized paired travel-time experiment. Refresh/Restart repeats the seed.

### Configurable demand and violations

The demand slider sets **0–24,000 offered PCU/hour per road**, both directions combined (default 8,000). Each direction gets half the PCU budget. The 3,996 preset is the Silk Board DPR count from `inputs_silk_board.py` (10–11 am, 25 April 2025), not the saturation capacity of this animation. The 8,000 comparison preset lies between the simulated discharge benchmarks at 100% violations. The 16,000 preset overloads both scenes. Maximum demand is 400 PCU/min. No preset is asserted to be representative of all Bengaluru roads.

**Actual-PCU budget:** each direction earns `demandPcuH × dt / 7200` PCU per step. The next seeded vehicle is dispatched when the budget covers its actual PCU cost plus a deterministic dispatch jitter of 0–0.6 PCU; only its actual cost is deducted. Thus cumulative offered PCU plus unspent credit equals the selected cumulative budget to floating-point tolerance, at every step. Credit remains less than the next vehicle's cost plus 0.6 PCU (at most 4.3 PCU per direction). This replaces the old approximate mean-PCU-to-vehicle-rate conversion. The visible audit reports generated vs budgeted PCUs, including the pre-run. Both scenes receive identical vehicle identities and times. Excess demand is retained off-screen; 0 generates no arrivals.

The upper-road violation slider sets **0–100%** (default 100). Its live list shows these categories:

- **Wrong parking:** 0 at zero; then 2/4/6/8 protruding vehicles at successive 25% bands, both directions combined. At 100%: 4 cars, 3 autos and 1 delivery van. Each is a fixed partial-width obstruction, not a whole-lane closure. Off-road display parking is not part of offered demand.
- **Extra car stops:** a seeded 0–35% of otherwise non-stopping cars receive a 4–6 s unscheduled interruption.
- **Extra auto stops:** a seeded 0–55% of otherwise non-stopping autos receive a 4.8–7.2 s pickup/drop-off.
- **Loading:** a seeded 0–20% of otherwise non-stopping delivery vans receive a 6.4–9.6 s in-lane loading stop.
- **Cutting attempts:** 0–60% of car/auto drivers have smaller accepted rear gaps (time-clearance term 0.35 → 0.18 s) and lower lateral movement/target persistence costs. They still check closing speed, lateral clearance and swept-body geometry. No speed penalty is imposed on the receiving lane; its IDM response to the encroaching vehicle produces braking. This represents a more assertive gap-seeking cohort, not a claim that all lateral shifts are illegal.
- **Existing scheduled passenger services:** their in-lane share scales with intensity. Bus identities, frequency and dwell are unchanged; there are no additional bus stops. Bus entry timing can still be delayed by congestion.

Extra stops are assigned only to the upper road without changing the shared incoming vehicle identities, type mix, PCU budget or lower-road dynamics. Thus scheduled services retain matching durations, but unscheduled upper-road interruptions deliberately add stops. Drivers with a stop beyond a parked obstruction first steer past the obstacle before moving toward the kerb. Mixed-traffic filtering remains active even at 0%. These counts/probabilities are illustrative scenario assumptions, not measured violation rates; completed events can be fewer when vehicles are held upstream.

Slider labels update while dragging; releasing/changing a slider restarts both simulations with the same seed, applies the settings during the 25-second pre-run, and resets measurements. This prevents a moving parking obstruction from appearing inside existing traffic and avoids mixing different settings in the PCU window. Restart preserves selected values. Pause is preserved too.

### Simulation capacity benchmark and V/C

V is the selected demand, not the discharge. C is estimated from a deterministic demand sweep of **this animation**, using 120 s warm-up and 480 s measured discharge for each of 6,000, 9,000, 12,000, 18,000 and 24,000 PCU/h. C is the maximum observed discharge over those runs. Entry-backlog fractions are recorded as diagnostics. Reproduce with `node traffic_flow_capacity_audit.js`.

| Upper violations | Upper C (PCU/h) | Lower C (PCU/h) |
|---|---:|---:|
| 0% | 7,871.63 | 8,175.38 |
| 25% | 4,306.88 | 8,175.38 |
| 50% | 3,144.00 | 8,175.38 |
| 75% | 2,230.12 | 8,175.38 |
| 100% | 2,563.12 | 8,175.38 |

Intermediate values are linearly interpolated. The noisy, one-seed envelope is neither an exact saturation capacity nor guaranteed monotonic with intensity. Do not conceal that mixed traffic can outperform strict lanes in some cases. The benchmark does **not** cap or otherwise change the simulation. A regression check repeats the upper-100% and lower maxima; rerun the full audit after changing dynamics, geometry or demand scheduling.

The earlier two-obstruction version had spare capacity at 3,996 PCU/h. With the expanded violation categories, the upper road at 100% can congest even at that demand; the lower road retains its prior behaviour. The benchmark was rerun after this change, rather than reusing old capacities. The 100% upper envelope comes from the 18,000 PCU/h run; the lower envelope from 24,000. Non-monotonic values reflect the one-seed nonlinear model and are not forced into a desired curve.

### Separate corridor-model reference (retained for context, not displayed as simulation C)

`V` is the selected two-way offered PCU/h, not admitted flow or observed discharge. `C` is a **corridor-model reference**, using the formulas and all nine today factors in `inputs_silk_board.py` / `model.py`:

```text
C_best = 3600 / 0.70 ≈ 5143 PCU/h
K = ln(3996 / C_best) / ln(product(today factors))
C_upper(q) = C_best × f_parking^(Kq) × f_bus^(Kq)
                      × product(other today factors^K)
C_lower = C_best
V/C = demandPcuH / C
```

Here `q = violations/100`. The parking and bus factors are the ones represented by this slider; the remaining corridor frictions stay at today values in the upper reference. At 100%, C_upper = 3,996; at 0%, it rises to the Python model's parking-and-bus-fixes capacity but remains below the all-fixes lower reference. Fractional exponents are an illustrative interpolation between fixed and today states, not a calibrated intensity response. Increasing demand changes V, not C. Changing violations changes the upper C, not shared V.

This reference includes corridor effects (signals, access, pedestrians, etc.) absent from the short animation, and its reference width differs. It was the source of the earlier misleading V/C label: the 3,996 default appeared saturated while the animation still had spare capacity. It no longer supplies the UI's C. A test retains parity with the Python formulas for this separate reference.

### PCU outflow display

Each exit event records simulation time, direction and a fixed PCU weight. Both directions are added (not subtracted). The display is `60 × sum(exit PCU) / window_seconds`, with a rolling 60-second window. Before 60 seconds have elapsed since the counter reset, the actual elapsed duration is used and the display identifies the building window. Events at the old boundary expire. Pause and playback speed do not change the definition of a simulated minute.

Weights follow the project's `inputs_silk_board.py` grouping: motorcycle/scooter 0.75, car 1.0, auto 2.0, delivery van (goods LCV) 2.0, bus 3.7. These fixed equivalents are for comparison, not estimates of dynamic PCUs for this geometry. The readout is discharge flow, not net accumulation (`inflow − outflow`) or a calibrated road capacity. Pre-run exits are excluded; Restart resets the window and counts.

### Travel times and end-of-run results

Vehicle centres crossing 0 m and 125 m define admission and completion for all visible counters. Boundary-crossing times are interpolated within each integration step. The arithmetic mean includes all vehicle modes, unweighted by PCU, and only trips admitted after the measurement reset. Vehicles already on-road at reset are excluded from travel samples but may contribute to discharge. Travel includes on-road stopping/queuing. Entry wait is now reported separately (offer time to 0 m crossing for admitted vehicles); it is not multiplied by distance. The queue display also reports PCUs, oldest outstanding wait and on-road slow/stopped vehicles, so congestion is not hidden by completed-trip averages.

The user selects 10, 12 or 15 km; the measured 125 m mean is multiplied by 80, 96 or 120 and converted to minutes. This assumes repetition of the observed conditions, including the stop mix. It is an illustrative extrapolation, not BPR/Google-calibrated route time. No arbitrary congestion uplift is added to make a desired answer.

“End simulation” freezes physics and reveals average time, admitted vehicles, admitted cars specifically, completed post-reset trips, unfinished admissions, and the off-road waiting count for each scene. Percentage change is `(lower − upper) / upper × 100`; zero baselines or missing averages produce no percentage. Unfinished-trip censoring can bias the completed-trip average downward during severe congestion; the summary explicitly reports those trips. Restart and changing demand/violations clear results and begin a new measurement; changing extrapolation distance only rescales times.

## Model parameters and limits

Six road-user categories: motorcycle, scooter, auto-rickshaw, car, delivery van, and bus. Lengths are roughly 1.8–10.3 m, widths 0.65–2.45 m. Desired speeds are approximately 8–12 m/s with per-vehicle variation; headways roughly 0.45–1.1 s before variation. These are illustrative values, not copied claims about calibrated Indian driving behavior.

The two directions use separate carriageways with left-hand traffic. No signal junction, U-turn, wrong-way vehicle, pedestrian road crossing or network spillback is modelled. Pedestrians are boarding/waiting markers. Footage comes from a wider road than this schematic 125 m, two-lanes-per-direction street.

## Verification

```sh
node --test traffic_flow_model.test.js
node traffic_flow_capacity_audit.js
```

Checks include: lateral intrusion affects the receiving follower; a narrow vehicle fits a gap a wider one cannot use at the same speed; side/rear conflicts prevent steering; five minutes of body-overlap checks in both scenes including parked obstacles; demand conservation; matched dwell parameters; recurring stops and departures; and partial lateral movement.

Browser checks cover rendering, playback, pause/restart/path controls and reduced-motion/mobile layout. None of these checks establishes real-world calibration or a predicted percentage capacity improvement.

## Further model reference

[Author's interactive MTM simulator and explanation](https://mtreiber.de/mixedTraffic/info.html). The author explicitly notes that mixed flow can sometimes outperform strict lanes under congestion and that a two-dimensional model is needed for lateral interaction. This animation should be read as an explanation of the selected street events, not proof that lane discipline always increases throughput.
