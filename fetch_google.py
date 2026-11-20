"""Step 1: pull Google Maps travel times for a corridor.

For each route in the corridor's inputs file (GOOGLE_ROUTES), both directions,
every hour 06:00-22:00 on the next Tuesday, ask the Google Routes API how long
the drive takes:
    BEST_GUESS  = typical day   (all routes)
    PESSIMISTIC = bad day       ("full" route only)
    OPTIMISTIC  = good day      ("full" route only)
Only distance, travel time and Google's no-traffic time are kept.

Route points were checked so Google stays on the at-grade road (not a flyover
or a parallel road): route distance within ~1.0-1.3x of straight line.

Output:  data/google_times_<corridor>.csv
Needs:   GOOGLE_MAPS_API_KEY in .env
Run:     CORRIDOR=silk_board python fetch_google.py      (or CORRIDOR=mysore_road)
"""

import csv
import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone

from corridor import I

IST = timezone(timedelta(hours=5, minutes=30))
HOURS = range(6, 23)
URL = "https://routes.googleapis.com/directions/v2:computeRoutes"


def api_key():
    if os.path.exists(".env"):
        for line in open(".env"):
            if line.startswith("GOOGLE_MAPS_API_KEY="):
                return line.split("=", 1)[1].strip()
    return os.environ["GOOGLE_MAPS_API_KEY"]


def next_tuesday():
    now = datetime.now(IST)
    d = (now + timedelta(days=(1 - now.weekday()) % 7 or 7)).date()
    return datetime(d.year, d.month, d.day, tzinfo=IST)


def drive(a, b, depart, model, key):
    """Returns (metres, seconds with traffic, seconds without traffic).
    a / b may carry a 3rd value = heading (degrees) to pin the carriageway."""
    def point(p):
        d = {"location": {"latLng": {"latitude": p[0], "longitude": p[1]}}}
        if len(p) > 2:
            d["location"]["heading"] = p[2]
        return d
    body = {
        "origin": point(a), "destination": point(b),
        "travelMode": "DRIVE", "routingPreference": "TRAFFIC_AWARE_OPTIMAL",
        "trafficModel": model,
        "departureTime": depart.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={
        "Content-Type": "application/json", "X-Goog-Api-Key": key,
        "X-Goog-FieldMask": "routes.duration,routes.staticDuration,routes.distanceMeters"})
    for attempt in range(3):  # retry network blips
        try:
            r = json.load(urllib.request.urlopen(req, timeout=30))["routes"][0]
            return r["distanceMeters"], int(r["duration"][:-1]), int(r["staticDuration"][:-1])
        except OSError:
            if attempt == 2:
                raise


def main():
    key, day = api_key(), next_tuesday()
    jobs = []
    for name, (a, b) in I.GOOGLE_ROUTES.items():
        models = ["BEST_GUESS", "PESSIMISTIC", "OPTIMISTIC"] if name == "full" else ["BEST_GUESS"]
        for model in models:
            # a heading belongs to the direction of travel: flip it for the reverse trip
            flip = lambda p: (p[0], p[1], (p[2] + 180) % 360) if len(p) > 2 else p
            jobs += [(name, "forward", model, a, b), (name, "reverse", model, flip(b), flip(a))]

    out = f"data/google_times_{I.NAME}.csv"
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["route", "direction", "traffic_model", "hour", "distance_m", "time_s", "static_s", "speed_kmh"])
        for name, direction, model, a, b in jobs:
            slowest = 0
            for h in HOURS:
                dist, t, t0 = drive(a, b, day.replace(hour=h), model, key)
                w.writerow([name, direction, model, h, dist, t, t0, round(dist / t * 3.6, 1)])
                slowest = max(slowest, t)
            print(f"{name:6s} {direction:8s} {model:12s} slowest hour {slowest / 60:5.1f} min")
    print(f"wrote {out}  (date queried: {day.date()})")


if __name__ == "__main__":
    main()
