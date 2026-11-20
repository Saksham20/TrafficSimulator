import json, math, urllib.request, sys
sys.path.insert(0,".")
exec(open("scratch/probe_polyline.py").read().split("def route")[0])  # decode, hv, key
def leg(a, b, ha=None, hb=None):
    def ll(p, h):
        d = {"location": {"latLng": {"latitude": p[0], "longitude": p[1]}}}
        if h is not None: d["location"]["heading"] = h
        return d
    body = {"origin": ll(a, ha), "destination": ll(b, hb), "travelMode": "DRIVE", "routingPreference": "TRAFFIC_AWARE_OPTIMAL", "departureTime": "2026-11-17T04:30:00Z"}
    r = urllib.request.Request("https://routes.googleapis.com/directions/v2:computeRoutes", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "X-Goog-Api-Key": key, "X-Goog-FieldMask": "routes.distanceMeters,routes.duration,routes.polyline.encodedPolyline"})
    x = json.load(urllib.request.urlopen(r))["routes"][0]; return x["distanceMeters"], x["duration"], decode(x["polyline"]["encodedPolyline"])
W = -0.00012
tests = {
 "seg3 NB 100ft (Domlur N -> 100ft top)": ((12.96259, 77.64165+W, 0), (12.97700, 77.64085+W, 0)),
 "seg2 NB (100ft top -> CMH jn)": ((12.97700, 77.64085+W, 0), (12.97880, 77.64655-0.00012, 0)),
 "seg2 NB alt (100ft top -> CMH Rd E)": ((12.97760, 77.64085+W, 0), (12.97845+0.00012, 77.64550, 90)),
}
for k, (a, b) in tests.items():
    d, t, P = leg(a, b, a[2], b[2])
    print(k, "straight", round(hv(a[:2], b[:2])), "google", d, t, "lons", min(p[1] for p in P), max(p[1] for p in P))
