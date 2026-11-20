"""The Silk Board corridor cut into 10 segments (smallest grain we model).

Boundaries are at junctions / changes in road width. Each segment has:
  ch      : start-end chainage along the corridor (km) [DPR Table 2-1, traffic plan]
  cw      : at-grade carriageway width per direction (m) [DPR inventory / TCS]
  lanes   : lanes per direction at grade [our reading at ~3-3.5 m per lane]
  spare   : unused width per direction that could become a lane (paver buffer) [DPR TCS]
  signals : signalised junctions inside / at the end of the segment [DPR traffic plan]
  turn    : sharp turn at the start of the segment, if any
  fly_lanes: lanes per direction the proposed elevated corridor adds over this
             segment [DPR 4.1.1; widths 12 m = 2-lane (1 each way), 8.5 m =
             2-lane one-way, 7 m = 1 lane]. Existing Domlur/Ejipura flyovers are
             counted in `existing_fly` (already there today).
  sev     : how bad each package's problems are HERE, relative to the DPR count
             site (segment 3 = 1.0). 0 = absent, 0.5 low, 1 like 100 Ft Rd,
             1.5 worse. E=enforcement (parking, encroachment, junction blocking),
             D=design (bus stops, pedestrians, lanes, median gaps), S=signals,
             M=surface/drainage. [estimate from DPR photos pp.84-95 + news]
  fly     : lanes (both directions together) the proposed Rs 1,300 cr DPR deck adds
             here (12 m = 2 lanes; 7 m = 1 lane; 2 x 8.5 m = 4 lanes) [DPR 4.1.1].
  ejipura : lanes the separate, under-construction Ejipura flyover adds (17 m, 4 lanes).
             Domlur -> Ejipura (segments 5-6) gets NO flyover: the technical
             committee dropped it [DPR p.158].
  google_sb / google_nb: points (lat, lon, heading) used to time the segment
             in each direction. Each was checked: Google's distance = 1.00-1.25x
             straight line (i.e. it drives this road, not a detour).
"""

# Signalised junctions by chainage (km) [DPR traffic-plan.pdf, +-100 m]
SIGNALS = {0.0: "Old Madras Rd", 0.8: "CMH Hospital", 1.4: "CMH Rd / 100 Ft", 1.6: "100 Ft Rd",
           2.3: "12th Main", 2.7: "Domlur", 5.2: "Defence underpass", 6.1: "Ejipura",
           6.8: "Sony World", 8.3: "Sarjapur Rd / St John's", 8.8: "Madiwala", 9.8: "Silk Board"}

SEGMENTS = [
    dict(id=1, name="80 Ft Rd (SV Metro -> CMH Hospital)", ch=(0.0, 0.8), cw=7.5, lanes=2, spare=0.0,
         signals=2, turn=None, fly=2, ejipura=0, sev=dict(E=1.0, D=1.0, S=1.5, M=0.5),
         frictions="metro station, autos, 2W filtering at kerb"),
    dict(id=2, name="CMH Road (CMH -> 100 Ft Rd)", ch=(0.8, 1.4), cw=8.5, lanes=2, spare=0.0,
         signals=1, turn="90 deg right at CMH signal", fly=2, ejipura=0, sev=dict(E=1.0, D=1.0, S=1.0, M=0.5),
         frictions="sharp turns, pedestrians, metro"),
    dict(id=3, name="100 Ft Rd Indiranagar", ch=(1.4, 3.1), cw=6.0, lanes=2, spare=3.5,
         signals=3, turn="90 deg left onto 100 Ft Rd", fly=2, ejipura=0, sev=dict(E=1.0, D=1.0, S=1.0, M=1.0),
         frictions="parking & autos in paver strip, buses stop in lane, shops"),
    dict(id=4, name="Domlur flyover", ch=(3.1, 3.6), cw=8.5, lanes=2, spare=0.0,
         signals=0, turn=None, fly=1, ejipura=0, sev=dict(E=0.2, D=0.2, S=0.0, M=0.5),
         frictions="grade-separated already"),
    dict(id=5, name="IRR: Domlur -> Defence land", ch=(3.6, 4.6), cw=8.5, lanes=2, spare=1.5,
         signals=0, turn=None, fly=0, ejipura=0, sev=dict(E=0.5, D=0.7, S=0.0, M=1.0),
         frictions="bus stops, median gaps"),
    dict(id=6, name="IRR: Defence land -> Ejipura", ch=(4.6, 6.3), cw=8.5, lanes=2, spare=1.5,
         signals=2, turn="30 deg at defence underpass", fly=0, ejipura=0, sev=dict(E=0.7, D=1.0, S=1.0, M=1.0),
         frictions="U-turn at underpass, 22.7 m pinch, flyover works"),
    dict(id=7, name="Ejipura -> Sony World", ch=(6.3, 7.0), cw=7.0, lanes=2, spare=0.0,
         signals=1, turn=None, fly=0, ejipura=4, sev=dict(E=1.5, D=1.5, S=1.0, M=1.5),
         frictions="no median in places, vendors, broken footpaths, waterlogging"),
    dict(id=8, name="Koramangala -> St John's (Ejipura flyover)", ch=(7.0, 8.35), cw=10.5, lanes=3, spare=0.0,
         signals=1, turn=None, fly=0, ejipura=4, sev=dict(E=1.0, D=1.0, S=0.7, M=1.0),
         frictions="flyover construction, Sarjapur Rd ramps"),
    dict(id=9, name="St John's -> Madiwala", ch=(8.35, 8.8), cw=8.4, lanes=2, spare=0.0,
         signals=1, turn=None, fly=4, ejipura=0, sev=dict(E=1.5, D=1.5, S=1.0, M=1.0),
         frictions="hospital, bus stops, checkpost"),
    dict(id=10, name="Hosur Rd: Madiwala -> Silk Board", ch=(8.8, 9.8), cw=15.0, lanes=4, spare=0.0,
         signals=1, turn="90 deg turn at Madiwala", fly=2, ejipura=0, sev=dict(E=1.5, D=1.5, S=1.5, M=1.5),
         frictions="Silk Board queues, metro works, waterlogging"),
]

# Google timing points. Southbound uses headings + east-side offsets (left-hand
# traffic) so Google stays on 80 Ft -> CMH -> 100 Ft Rd like the DPR alignment.
GOOGLE_SB = [  # (lat, lon, heading) at each boundary, OMR -> Silk Board
    (12.98455, 77.64541, 190), (12.97880, 77.64667, 180), (12.97700, 77.64097, 180),
    (12.96259, 77.64177, 180), (12.95778, 77.64144, 180), (12.94967, 77.63939, 200),
    (12.93839, 77.63287, 270), (12.93724, 77.62706, 250), (12.92750, 77.62101, 210),
    (12.92463, 77.61819, 150), (12.91723, 77.62278, 150),
]
GOOGLE_NB = [  # same boundaries, northbound carriageway (west side on 100 Ft Rd); listed OMR -> Silk Board
    (12.98455, 77.64530), (12.97868, 77.64647, 0), (12.97700, 77.64073, 0), (12.96259, 77.64165),
    (12.95778, 77.64132), (12.94967, 77.63927), (12.93854, 77.63275), (12.93739, 77.62694),
    (12.92750, 77.62089), (12.92463, 77.61807), (12.91723, 77.62266),
]

# ---------------------------------------------------------------- labels for the explainer
LABELS = dict(
    start="Old Madras Rd (SV Rd Metro)", end="Central Silk Board",
    start_short="Old Madras Rd", end_short="Silk Board",
    trip="Old Madras Rd -> Silk Board", length_txt="~10 km",
    flyover="Rs 1,300 cr flyover", flyover_cost="Rs 1,300 crore",
    has_second_flyover=True, second_flyover="Ejipura flyover",
    map_title="Old Madras Road -> Silk Board, as it is today (9.8 km, 13 signals*, 108 side roads, 46 bus stops)",
    map_note="*12 signals between the two ends + Begur Rd beyond Silk Board. ",
    gap_span=(3.5, 7.5),
    gap_text="Domlur -> St John's: no new flyover deck\n(stretch 8 has the separate Ejipura flyover)",
    flyover_note=("Flyover lanes per DPR: 12 m deck = 1 lane each way (segments 1-3), 7 m over Domlur = 1 lane, "
                  "2 x 8.5 m Ejipura-Madiwala = 2 lanes each way, 7 m loops to Silk Board. Elevated lane = 1,800 PCU/h."),
    d_note=("Left: the flyover lifts its own stretches, but every through-trip still squeezes through "
            "Domlur -> Sony World on the ground, so end-to-end capacity hardly moves unless the ground is fixed."),
    pcu_note=("Segment 3 (100 Ft Rd) is where the DPR counted 3,996 PCU/h; other segments are scaled by how bad their "
              "parking, bus stops, pedestrians, signals and surface are compared with segment 3. "),
    pdf_title="Old Madras Road -> Silk Board: does it need a Rs 1,300 crore flyover?",
    pdf_line="  The flyover skips Domlur -> Sony World, where the corridor chokes, so its minutes erode as traffic grows.",
    sources="Data: Google Routes API (Tue 17 Nov 2026, typical day), B-SMILE DPR (Feb 2026), IRC:106-1990, HCM 2010. "
            "Capacities are model estimates, see README.",
)
