"""Every number the model uses for the Mysore Road corridor, and its source.

Corridor: Sirsi Circle (end of BGS flyover) -> Satellite Bus Stand -> Gali
Anjaneya -> Kimco/BHEL -> Mysore Road Metro / Nayandahalli. Proposed B-SMILE
elevated corridor, 5.2 km, tender Rs 538 cr (Rs 810 cr incl. land, Legislative
Council answer, 12 Mar 2026).

IMPORTANT: the Mysore Road documents contain NO traffic data at all (no count,
no PCU, no forecast, no speed survey). So "today" here is an ESTIMATE:
  today = IRC best case x the frictions below, using the overlap exponent K
  calibrated on Silk Board (the only corridor with a real count).
Google travel times are real and are used for the time curve.

Tags: [doc] project drawings/RFP in docs/mysoreRoaddocs, [news], [Google],
      [published], [estimate]
"""

from inputs_silk_board import hcm_parking_factor, pedestrian_factor  # same formulas

NAME = "mysore_road"
TITLE = "Mysore Rd: Sirsi Circle -> Nayandahalli"
FLYOVER = "Rs 538 cr tender (Rs 810 cr incl. land) elevated corridor"
DEMAND_SOURCE = "Assumed growth 3.9%/yr (Silk Board DPR rate; no Mysore Rd forecast exists)"
SOURCES_LINE = ("Sources: B-SMILE tender drawings & RFP (2026, no traffic data), IRC:106-1990, HCM 2010, "
                "Google Routes API (Nov 2026), The Hindu 2023. 'Today' is estimated - see README.")

# Google points: at-grade, after the BGS flyover ramp touches down (ch ~0.55)
# to before the Nayandahalli flyover. Heading 250 deg pins the westbound start
# (without it Google adds a U-turn loop near Sirsi: 3.2 km instead of 2.3 km).
# Checked: 1.02x (westbound) / 1.12x (eastbound, loops round Satellite stand).
GOOGLE_ROUTES = {
    "full": ((12.95769, 77.55265, 250), (12.94784, 77.53419, 235)),
}

# ---------------------------------------------------------------- the road
# Binding section ch 0.70-1.40 (Limgappa Circle / Gopalan Mall): 26 m ROW,
# 9.8 m and 12.0 m carriageways = 3 lanes each way (one side ~2.8 m lanes).
# Elsewhere 12-15 m per direction [doc: tcs pp.9-12].
LANES_PER_DIRECTION = 3
CARRIAGEWAY_M = 9.8

# ---------------------------------------------------------------- best case
# IRC:106 Table 2, 6-lane divided: arterial 5,400 / sub-arterial 4,300 PCU/h (DSV, LOS C)
IRC_DSV_ARTERIAL = 5400
IRC_DSV_SUB_ARTERIAL = 4300
DSV_TO_CAPACITY = 0.70
BEST_CAPACITY = IRC_DSV_ARTERIAL / DSV_TO_CAPACITY  # 7,714 PCU/h two-way

# Context: the rest of the corridor has 12-15 m per direction (4 lanes). If the
# 9.8 m pinch (0.7 km, RMP-2015 already plans 30-45 m ROW) were widened, the road
# works as an 8-lane divided arterial: IRC 7,200 / 0.70.
BEST_WITH_BUFFER_REUSED = 7200 / DSV_TO_CAPACITY  # 10,286 PCU/h
EXTRA_LABEL = "All fixes + widen the 0.7 km pinch to 4 lanes (IRC 8-lane)"

# No count -> reuse the overlap exponent calibrated on Silk Board.
K_OVERRIDE = 0.308
TODAY_CAPACITY = None  # computed in model.py from the frictions

# ---------------------------------------------------------------- traffic facts
# Satellite (KSRTC) + BMTC bus stands at ch ~2.1: ~800 buses/day [news: The Hindu
# 19 Sep 2023]; plus BMTC through-routes; KSRTC depot 5, BMTC depot 16 at ch 2.75.
BUSES_PER_HOUR = 120   # peak direction, through + stand movements [estimate]


def hcm_bus_factor_3(buses_per_hour):
    """HCM bus blockage for 3 lanes."""
    return (3 - 14.4 * buses_per_hour / 3600) / 3


def width_factor(metres_lost, width=CARRIAGEWAY_M):
    return (width - metres_lost) / width


# ---------------------------------------------------------------- interventions
# Same 9 frictions as Silk Board; 'today' values reflect Mysore Road evidence.
INTERVENTIONS = [
    dict(id="parking", name="No parking / stopping on carriageway", bundle="Enforce",
         today=hcm_parking_factor(45, lanes=3), worst=hcm_parking_factor(150, lanes=3),
         basis="45 manoeuvres/h today (8 fuel stations, dense shops, no service road), 150 worst [estimate]",
         source="HCM 2010; doc: concept sheets 1-7 (frontage, fuel stations)"),
    dict(id="encroach", name="Clear encroachments (vendors, debris, boxes)", bundle="Enforce",
         today=width_factor(0.5), worst=width_factor(1.5),
         basis="0.5 m of the 9.8 m pinch lost today, 1.5 m worst [estimate]",
         source="IRC:SP:41 / Webster S=525W"),
    dict(id="box", name="Keep junctions clear, no stop-go waves", bundle="Enforce",
         today=0.92, worst=0.85,
         basis="Capacity drop 5-20% [published]",
         source="Hall & Agyemang-Duah 1991; Cassidy & Bertini 1999"),
    dict(id="bus", name="Bus bays + organised bus-stand entry/exit", bundle="Design",
         today=hcm_bus_factor_3(BUSES_PER_HOUR), worst=hcm_bus_factor_3(220),
         basis="HCM bus blockage, 120 buses/h today, 220 worst; buses stop at undesignated spots [news]",
         source="The Hindu 19 Sep 2023 (Satellite bus stand); doc: 15 bus stops, no bays drawn"),
    dict(id="peds", name="Continuous footpaths + safe crossings", bundle="Design",
         today=pedestrian_factor(700), worst=pedestrian_factor(1360),
         basis="700 ped/h on carriageway near bus stand/metro today [estimate]",
         source="Dhamaniya & Chandra 2014; doc: footpath missing at ch 3+250"),
    dict(id="lanes", name="Lane markings + lane discipline", bundle="Design",
         today=0.95, worst=0.88,
         basis="[estimate] same as Silk Board",
         source="IRC:106 cl. 9.2"),
    dict(id="access", name="Fewer median gaps / U-turns / side entries", bundle="Design",
         today=0.93, worst=0.85,
         basis="[estimate] 43 cross roads in 3.5 km (one every ~160 m per side), no service road",
         source="doc: traffic-plan.pdf"),
    dict(id="signals", name="Adaptive, coordinated signals (no manual override)", bundle="Signals",
         today=1 / 1.18, worst=1 / 1.30,
         basis="Bengaluru adaptive signals: +18% to +30% throughput",
         source="BTP BATCS data, Indian Express 10 Oct 2024; 7 signals in 3.5 km [doc]"),
    dict(id="surface", name="Smooth surface + working drains", bundle="Maintain",
         today=0.95, worst=0.80,
         basis="[estimate] asphalt, poorly kept service roads [news]; Vrishabhavathi crossings",
         source="Bangalore Mirror 6 Apr 2026"),
]

BUNDLES = {
    "Enforce":  "Police the rules: towing, no stopping, yellow boxes, clear vendors",
    "Design":   "Fix the street: bus bays, bus-stand access, footpaths, markings, median gaps",
    "Signals":  "Run the signals properly: adaptive, coordinated, no manual override",
    "Maintain": "Maintain the road: surface and drains",
}

# ---------------------------------------------------------------- demand growth
# No forecast exists. Assume today's peak demand = today's capacity (Google shows
# the peak is congested) growing 3.9%/yr - the Silk Board DPR's own 2026-31 rate.
GROWTH = 0.039
DEMAND_FORECAST = None  # filled in by model.py once TODAY_CAPACITY is known
FLYOVER_READY_YEAR = 2028  # 18 months after 2026 tender [doc: RFP]

BETA = 2
FLYOVER_COST_CR = 538
