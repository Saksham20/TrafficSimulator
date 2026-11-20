"""The Mysore Road corridor cut into 5 segments (smallest grain we model).

Sirsi Circle (end of the existing BGS flyover) -> Nayandahalli, at grade.
Segment 0 (Sirsi Circle itself, ch 0-0.55) is left out: traffic there is on
the existing BGS flyover ramps and Google routes onto the deck.

Fields as in segments_silk_board.py. Sources:
  widths / lanes: tender typical cross sections (tcs pp.9-12) at ch 0+330,
                  1+025, 1+800, 2+450, 3+250 [doc]
  signals:        traffic-plan.pdf: Signal-2 Old Guddadahalli Rd, 3 Limgappa,
                  4 1st Main, 5 8th Main / Satellite, 6 Gali Anjaneya, 7 Nayandahalli
  fly:            proposed deck lanes, both directions together [concept sheets 1-7, tcs p.1]:
                  20.2 m deck = 2 lanes each way (4); 2 x 8.5 m one-way decks = 4;
                  ch 2.8-3.45 = 8.5 m one-way decks / ramps toward the Nayandahalli flyover (~2-3).
  sev:            friction severity vs Silk Board's 100 Ft Rd (=1.0) [estimate from drawings + news]:
                  Satellite Bus Stand (~800 buses/day, buses stop anywhere - The Hindu 2023),
                  43 cross roads, 8 fuel stations straight onto the carriageway, no service road.
"""

# Signalised junctions by chainage (km), measured from the BGS ramp touch-down
# (ch 0.55 in the tender = 0.0 here) [traffic-plan.pdf, +-100 m]
SIGNALS = {0.13: "Old Guddadahalli Rd", 0.45: "Limgappa Circle", 1.15: "1st Main / Nehru Rd",
           1.45: "8th Main / Satellite", 1.75: "Gali Anjaneya", 2.55: "Nayandahalli (under ORR flyover)"}

SEGMENTS = [
    dict(id=1, name="BGS ramp -> Limgappa Circle", ch=(0.0, 0.42), cw=12.6, lanes=3, spare=0.0,
         signals=1, turn=None, fly=4, ejipura=0, sev=dict(E=1.0, D=1.0, S=1.0, M=1.0),
         frictions="fuel stations, shops, tunnel-road works planned near Kudhure Park"),
    dict(id=2, name="Limgappa Circle -> Gopalan Mall (narrowest)", ch=(0.42, 0.92), cw=9.8, lanes=3, spare=0.0,
         signals=1, turn=None, fly=4, ejipura=0, sev=dict(E=1.2, D=1.2, S=1.0, M=1.0),
         frictions="26 m ROW, ~2.8 m lanes on one side, mall, graveyards, bus shelters"),
    dict(id=3, name="Gopalan Mall -> Satellite Bus Stand", ch=(0.92, 1.44), cw=14.3, lanes=4, spare=0.0,
         signals=1, turn=None, fly=4, ejipura=0, sev=dict(E=1.3, D=1.5, S=1.2, M=1.0),
         frictions="KSRTC + BMTC Satellite bus stands: buses entering, leaving, stopping anywhere"),
    dict(id=4, name="Satellite -> Gali Anjaneya -> Kimco/BHEL", ch=(1.44, 2.27), cw=12.0, lanes=3, spare=0.0,
         signals=2, turn="loop at Satellite / Gali Anjaneya", fly=4, ejipura=0,
         sev=dict(E=1.2, D=1.3, S=1.3, M=1.3),
         frictions="Gali Anjaneya junction, Vrishabhavathi bridge, depots, Kimco/Chord Rd junction"),
    dict(id=5, name="Kimco -> Mysore Road Metro / Nayandahalli", ch=(2.27, 2.55), cw=11.6, lanes=3, spare=0.0,
         signals=1, turn=None, fly=3, ejipura=0, sev=dict(E=1.0, D=1.2, S=1.3, M=1.0),
         frictions="metro pillars on south edge, metro station, ORR junction, trucks, black spot"),
]

# Google timing points (lat, lon) at each boundary. Westbound = toward Nayandahalli
# (KML vertices, Google = 1.00-1.02x straight line). Eastbound points sit on Google's
# eastbound line (it loops round the Satellite stand: segment 4 = 1.32x, real road).
GOOGLE_SB = [  # "southbound" slot = towards the END of the corridor (westbound here); heading pins the carriageway
    (12.95769, 77.55265, 250), (12.95683, 77.54892, 245), (12.95501, 77.54466, 235), (12.95228, 77.54074, 235),
    (12.94959, 77.53675, 235), (12.94784, 77.53419, 235),
]
GOOGLE_NB = [  # "northbound" slot = back towards the START (eastbound here)
    (12.95769, 77.55265), (12.95666, 77.54841), (12.95488, 77.54453), (12.95293, 77.54136),
    (12.94909, 77.53615), (12.94784, 77.53419, 55),
]

# ---------------------------------------------------------------- labels for the explainer
LABELS = dict(
    start="Sirsi Circle (BGS flyover ramp)", end="Nayandahalli (Mysore Rd Metro)",
    start_short="Sirsi Circle", end_short="Nayandahalli",
    trip="Sirsi Circle -> Nayandahalli", length_txt="~2.5 km",
    flyover="Rs 538 cr flyover", flyover_cost="Rs 538 crore (Rs 810 cr with land)",
    has_second_flyover=False, second_flyover=None,
    map_title="Mysore Road: Sirsi Circle -> Nayandahalli, as it is today (2.5 km at grade, 6 signals, 43 side roads, "
              "15 bus stops)",
    map_note="Sirsi Circle itself (first ~0.5 km, on the BGS flyover ramps) is not included. ",
    gap_span=None, gap_text=None,
    label_gap=0.2, label_gap_pcu=0.17, map_figsize=(14, 11), pcu_range=(5000, 10500), pcu_right=0.75,
    flyover_note=("Flyover lanes per tender drawings: 2 x 8.5 m one-way decks (ch 0-1) and a 20.2 m 4-lane deck "
                  "(ch 1-2.4) = 2 lanes each way; 8.5 m decks/ramps toward Nayandahalli. Elevated lane = 1,800 PCU/h."),
    d_note=("Left: here the deck runs over the whole stretch, so the flyover does raise end-to-end capacity - but so "
            "does fixing the ground, at a fraction of the cost."),
    pcu_note=("No traffic count exists for Mysore Road: 'today' is ESTIMATED as the IRC standard for these lanes x the "
              "same friction penalty as Silk Board's counted stretch, scaled by how bad each stretch is. "),
    pdf_title="Mysore Road (Sirsi Circle -> Nayandahalli): does it need a Rs 538 crore flyover?",
    pdf_line=("  Unlike Silk Board, the deck covers the whole stretch, so the flyover does beat fixing the ground here - "
              "but the whole trip is ~2.5 km, savings are 2-7 min, and its traffic lands on the BGS flyover and "
              "Nayandahalli junction (not modelled)."),
    sources="Data: Google Routes API (Tue 17 Nov 2026, typical day), B-SMILE tender drawings (2026, no traffic data), "
            "IRC:106-1990, HCM 2010. Capacities are model estimates, see README.",
)
