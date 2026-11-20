"""Every number the model uses, and where it comes from.

Corridor: Old Madras Rd -> Indiranagar 100 Ft Rd -> Domlur -> IRR/Ejipura ->
Sony World -> Madiwala -> Central Silk Board (Bengaluru), the route of the
proposed B-SMILE elevated corridor (DPR Feb 2026, Rs 1,300 cr).

Tags used below:
  [DPR]       the project's own Detailed Project Report (docs/silkboardroaddocs)
  [Google]    Google Routes API, data/google_times.csv (fetch_google.py)
  [published] standard / paper / official data, cited
  [estimate]  our judgement - change it and re-run
"""

NAME = "silk_board"
TITLE = "Old Madras Rd -> Silk Board"
FLYOVER = "Rs 1,300 cr elevated corridor (DPR, Feb 2026)"
DEMAND_SOURCE = "DPR peak-hour forecast (Table 5-4)"

# Google Routes points (north end, south end), checked to stay on the at-grade
# road: Google distance within 1.04-1.31x of straight line.  [Google]
GOOGLE_ROUTES = {
    "full":  ((12.98455, 77.64529), (12.91720, 77.62270)),  # Old Madras Rd -> Central Silk Board
    "core":  ((12.97700, 77.64090), (12.94690, 77.64050)),  # 100 Ft Rd -> Domlur -> IRR
    "south": ((12.93357, 77.62322), (12.92435, 77.61797)),  # Koramangala -> Madiwala
}

# ---------------------------------------------------------------- the road
# The capacity model is applied at the DPR traffic-count location:
# 100 Ft Road, Indiranagar -> Domlur. 2 lanes each way on a 6.0 m concrete
# carriageway, with a 3.2-4.8 m paver "buffer" strip on each side that is
# used for parking, auto stands and bus stops [DPR TCS @ ch 2+050, photos p.82].
LANES_PER_DIRECTION = 2
CARRIAGEWAY_M = 6.0

# ---------------------------------------------------------------- traffic today
OBSERVED_PEAK_PCU = 3996   # two-way, 10-11 am, 25 Apr 2025 [DPR Table 5-1]
PEAK_BUSES_TWO_WAY = 112   # 100 standard + 12 mini buses, 10-11 am [DPR Table 5-1]
PEAK_DIRECTION_SHARE = 0.60  # 16,656 of 27,807 vehicles went towards Domlur [DPR p.129]
BUSES_PER_HOUR = PEAK_BUSES_TWO_WAY * PEAK_DIRECTION_SHARE  # ~67 in the peak direction

# Key assumption: in the peak hour the road is already full, so the counted
# flow IS today's practical capacity. Evidence: Google shows peak travel time
# about 2x the early-morning time on this stretch [Google], and the DPR itself
# says v/c > 1 on most arterials [DPR p.13].
TODAY_CAPACITY = OBSERVED_PEAK_PCU

# ---------------------------------------------------------------- best case
# IRC:106-1990 Table 2, 4-lane divided road, design service volume (DSV):
#   arterial     3,600 PCU/h  (no frontage access, NO STANDING VEHICLES, little cross traffic)
#   sub-arterial 2,900 PCU/h  (frontage access, side roads, bus stops)   <- what the DPR used
# DSV is set at LOS C = 0.70 x capacity (IRC:106 cl. 8.1).            [published]
IRC_DSV_ARTERIAL = 3600
IRC_DSV_SUB_ARTERIAL = 2900
DSV_TO_CAPACITY = 0.70
# Best case = same road, same width, same 4 lanes, run as a proper arterial.
BEST_CAPACITY = IRC_DSV_ARTERIAL / DSV_TO_CAPACITY  # 5,143 PCU/h two-way

# Context only (not in the model): if the 3-5 m paver buffer were re-used so the
# road worked as a 6-lane divided arterial, IRC:106 gives 5,400 / 0.70.
BEST_WITH_BUFFER_REUSED = 5400 / DSV_TO_CAPACITY  # 7,714 PCU/h
EXTRA_LABEL = "All fixes + paver buffer used as 3rd lane (IRC 6-lane)"

# K: how much the literature factors overlap. Calibrated HERE (the corridor
# with a real count) and reused for corridors without one. None = calibrate.
K_OVERRIDE = None


# ---------------------------------------------------------------- friction formulas
def hcm_parking_factor(manoeuvres_per_hour, lanes=LANES_PER_DIRECTION):
    """HCM 2010 Eq. 18-? : f_p = (N - 0.1 - 18*Nm/3600) / N  (18 s blocked per manoeuvre)."""
    return (lanes - 0.1 - 18 * manoeuvres_per_hour / 3600) / lanes


def hcm_bus_factor(buses_per_hour, lanes=LANES_PER_DIRECTION):
    """HCM 2010: f_bb = (N - 14.4*Nb/3600) / N  (14.4 s blocked per bus stopping in a lane)."""
    return (lanes - 14.4 * buses_per_hour / 3600) / lanes


def pedestrian_factor(peds_per_hour):
    """Dhamaniya & Chandra (2014, TRR 2461): no effect below 200 ped/h, -30% at 1,360 ped/h."""
    p = min(max(peds_per_hour, 200), 1360)
    return 1 - 0.30 * (p - 200) / 1160


def width_factor(metres_lost, width=CARRIAGEWAY_M):
    """Saturation flow is proportional to usable width (Webster/TRRL S = 525 W; IRC:SP:41)."""
    return (width - metres_lost) / width


# ---------------------------------------------------------------- interventions
# Each one: capacity multiplier as reported in the literature for an Indian
# road TODAY, and on a very bad day (WORST). Fixed = 1.0.
# bundle: which package of measures it belongs to.
INTERVENTIONS = [
    dict(id="parking", name="No parking / stopping on carriageway", bundle="Enforce",
         today=hcm_parking_factor(30), worst=hcm_parking_factor(120),
         basis="HCM parking factor; 30 park/stop manoeuvres per hour today, 120 worst [estimate]",
         source="HCM 2010 Ch.18; DPR photos p.82 (cars, 2W, autos parked in buffer)"),
    dict(id="encroach", name="Clear encroachments (vendors, debris, boxes)", bundle="Enforce",
         today=width_factor(0.3), worst=width_factor(1.0),
         basis="Width lost of the 6.0 m carriageway: 0.3 m today, 1.0 m worst [estimate]",
         source="IRC:SP:41 / Webster S=525W; DPR photos p.85 (vendors, debris at Sony World)"),
    dict(id="box", name="Keep junctions clear, no stop-go waves", bundle="Enforce",
         today=0.92, worst=0.85,
         basis="Capacity drop once queues form: 5-20% [published]",
         source="Hall & Agyemang-Duah 1991; Cassidy & Bertini 1999; Srivastava & Geroliminis 2013"),
    dict(id="bus", name="Bus bays at the kerbside stops", bundle="Design",
         today=hcm_bus_factor(BUSES_PER_HOUR), worst=hcm_bus_factor(125),
         basis=f"HCM bus-blockage factor; {BUSES_PER_HOUR:.0f} buses/h today (DPR count), 125 worst (bunching, minibuses)",
         source="HCM 2010; DPR: 46 bus stops, none with a bay"),
    dict(id="peds", name="Continuous footpaths + safe crossings", bundle="Design",
         today=pedestrian_factor(600), worst=pedestrian_factor(1360),
         basis="600 people/h walking/crossing on the carriageway today, 1,360 worst [estimate]",
         source="Dhamaniya & Chandra 2014; TOI 2025 (Ejipura footpaths broken in 4 months)"),
    dict(id="lanes", name="Lane markings + lane discipline", bundle="Design",
         today=0.95, worst=0.88,
         basis="[estimate] weakest number: 2-wheelers can gain from filtering",
         source="Munigety & Mathew 2016 (review); IRC:106 cl. 9.2"),
    dict(id="access", name="Fewer median gaps / U-turns / side entries", bundle="Design",
         today=0.95, worst=0.88,
         basis="[estimate] 108 cross roads on the corridor",
         source="DPR p.20; IRC:106 cl. 9.2 (regulate median openings)"),
    dict(id="signals", name="Adaptive, coordinated signals (no manual override)", bundle="Signals",
         today=1 / 1.18, worst=1 / 1.30,
         basis="Bengaluru adaptive signals raised throughput 18% (K R Rd) to 30% (Hudson Circle)",
         source="BTP BATCS data, Indian Express 10 Oct 2024; manual override 6-17% (The Hindu 2025)"),
    dict(id="surface", name="Smooth surface + working drains", bundle="Maintain",
         today=0.97, worst=0.80,
         basis="[estimate] 100 Ft Rd is white-topped (good); worst = waterlogging",
         source="DPR p.85, p.87 photos (waterlogging at Sony World, Silk Board)"),
]

BUNDLES = {
    "Enforce":  "Police the rules: towing, no stopping, yellow boxes, clear vendors",
    "Design":   "Fix the street: bus bays, footpaths, crossings, markings, median gaps",
    "Signals":  "Run the signals properly: adaptive, coordinated, no manual override",
    "Maintain": "Maintain the road: surface and drains",
}

# ---------------------------------------------------------------- demand growth
# DPR's own peak-hour forecast, two-way PCU/h [DPR Table 5-4]. The DPR labels
# the columns "growth for 5/10/15/20/25 years" from 2026.
DEMAND_FORECAST = {2026: 3996, 2031: 4833, 2036: 5664, 2041: 6498, 2046: 8159, 2051: 12064}
FLYOVER_READY_YEAR = 2028  # 24-month build after 2026 tender [DPR]

# ---------------------------------------------------------------- travel time
# Delay above free flow scales with (demand / capacity) ** BETA (BPR form).
# BPR standard is 4; we use 2 to stay conservative (smaller gains).  [published form]
BETA = 2

# ---------------------------------------------------------------- people, not vehicles
# Peak hour 10-11 am, two-way, DPR Table 5-1, grouped. Occupancy = people per
# vehicle incl. driver [estimate; typical Indian CMP values]. Bus 40 is a
# conservative average load for a BMTC bus in the peak (crush load ~80).
PEAK_HOUR_VEHICLES = {  # type: (count, PCU each [IRC:106], occupancy)
    "Two-wheeler": (1975, 0.75, 1.2),
    "Car / taxi / van": (996 + 204, 1.0, 1.5),
    "Auto-rickshaw": (414, 2.0, 1.8),
    "Bus": (112, 3.7, 40),
    "Goods (LCV, truck, goods auto)": (94 + 9 + 34 + 12, 2.0, 1.2),
    "Cycle": (19, 0.5, 1.0),
}
# The DPR flyover: 13 km of deck but mostly 1-2 lanes; "8.3 km four-lane
# equivalent" over ~11 km = ~1.5 lanes per direction on average [DPR p.8].
FLYOVER_LANES_PER_DIRECTION = 1.5
FLYOVER_PCU_PER_LANE = 1800        # clean elevated lane [Dhamaniya & Chandra: 1,500-2,100]
BUS_LANE_BUSES_PER_HOUR = 120      # per direction, kerbside lane with bays [TCQSM: 60-120+]
# The 3.2-4.8 m paver "buffer" on each side of 100 Ft Rd / IRR (ch 1.4-6.3 km)
# is wide enough for a 3.5 m bus lane without taking a general lane [DPR TCS].
# NOTE: only ~5 of the ~10 km has this strip; elsewhere a lane must be taken.
BUS_LANE_IN_SPARE_STRIP = True
FLYOVER_COST_CR = 1300
