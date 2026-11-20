"""Google travel time for each segment of a corridor, both directions,
at 6 am (near free flow), 10 am (DPR count hour) and 6 pm (evening peak),
next Tuesday, typical-day traffic model.

Output: data/google_segments_<corridor>.csv   (6 calls per segment)
        data/route_geometry_<corridor>.json  (road shape per segment, for the maps)
        + whole-route times on the same end points if the corridor has no
          matching full-route file yet (Mysore Road)
Run:    CORRIDOR=silk_board python fetch_segments.py   (or mysore_road)
Run:    python fetch_segments.py
"""

import csv

from fetch_google import api_key, next_tuesday, URL  # noqa: F401
import json
import urllib.request
from datetime import timezone

import importlib
import os

NAME = os.environ.get("CORRIDOR", "silk_board")
SG = importlib.import_module(f"segments_{NAME}")
GOOGLE_NB, GOOGLE_SB, SEGMENTS = SG.GOOGLE_NB, SG.GOOGLE_SB, SG.SEGMENTS

HOURS = [6, 10, 18]


def drive(a, b, depart, key):
    def point(p):
        d = {"location": {"latLng": {"latitude": p[0], "longitude": p[1]}}}
        if len(p) > 2:
            d["location"]["heading"] = p[2]
        return d
    body = {"origin": point(a), "destination": point(b), "travelMode": "DRIVE",
            "routingPreference": "TRAFFIC_AWARE_OPTIMAL",
            "departureTime": depart.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={
        "Content-Type": "application/json", "X-Goog-Api-Key": key,
        "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline"})
    for attempt in range(3):
        try:
            r = json.load(urllib.request.urlopen(req, timeout=30))["routes"][0]
            return r["distanceMeters"], int(r["duration"][:-1]), decode(r["polyline"]["encodedPolyline"])
        except OSError:
            if attempt == 2:
                raise


def decode(s):
    """Google encoded polyline -> list of (lat, lon)."""
    pts, i, lat, lng = [], 0, 0, 0
    while i < len(s):
        vals = []
        for _ in range(2):
            shift = res = 0
            while True:
                b = ord(s[i]) - 63
                i += 1
                res |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break
            vals.append(~(res >> 1) if res & 1 else res >> 1)
        lat, lng = lat + vals[0], lng + vals[1]
        pts.append((lat / 1e5, lng / 1e5))
    return pts


def main():
    geometry = {}
    key, day = api_key(), next_tuesday()
    with open(f"data/google_segments_{NAME}.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["segment", "direction", "hour", "distance_m", "time_s", "speed_kmh"])
        for i, s in enumerate(SEGMENTS):
            for direction, a, b in [("southbound", GOOGLE_SB[i], GOOGLE_SB[i + 1]),
                                    ("northbound", GOOGLE_NB[i + 1], GOOGLE_NB[i])]:
                for h in HOURS:
                    d, t, line = drive(a, b, day.replace(hour=h), key)
                    w.writerow([s["id"], direction, h, d, t, round(d / t * 3.6, 1)])
                    if h == 6:
                        geometry[f'{s["id"]}_{direction}'] = line
            print("segment", s["id"], "done")
    json.dump(geometry, open(f"data/route_geometry_{NAME}.json", "w"))
    print(f"wrote data/google_segments_{NAME}.csv + route geometry for", day.date())


if __name__ == "__main__":
    main()
