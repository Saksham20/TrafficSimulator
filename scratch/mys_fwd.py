import json, math, urllib.request
exec(open("scratch/probe_polyline.py").read().split("def route")[0])
def route(a, b, h=None):
    def ll(p):
        d={"location": {"latLng": {"latitude": p[0], "longitude": p[1]}}}
        if h is not None: d["location"]["heading"]=h
        return d
    body = {"origin": ll(a), "destination": ll(b), "travelMode": "DRIVE", "routingPreference": "TRAFFIC_AWARE_OPTIMAL", "departureTime": "2026-11-17T04:30:00Z"}
    r = urllib.request.Request("https://routes.googleapis.com/directions/v2:computeRoutes", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "X-Goog-Api-Key": key, "X-Goog-FieldMask": "routes.polyline.encodedPolyline,routes.distanceMeters"})
    x=json.load(urllib.request.urlopen(r))["routes"][0]; return x["distanceMeters"], decode(x["polyline"]["encodedPolyline"])
for h in (None, 250):
    d, P = route((12.95769,77.55265),(12.94784,77.53419), h)
    print("heading", h, "dist", d, "lat range", min(p[0] for p in P), max(p[0] for p in P), "lon range", min(p[1] for p in P), max(p[1] for p in P))
