"""Find at-grade Google boundary points for Mysore Rd segments, both directions."""
import json, math, sys, urllib.request
key = [l.split("=", 1)[1].strip() for l in open(".env") if l.startswith("GOOGLE")][0]
def hv(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    return 2*6371000*math.asin(math.sqrt(math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2))
def leg(a, b, ha=None, hb=None):
    def ll(p, h):
        d = {"location": {"latLng": {"latitude": p[0], "longitude": p[1]}}}
        if h is not None: d["location"]["heading"] = h
        return d
    body = {"origin": ll(a, ha), "destination": ll(b, hb), "travelMode": "DRIVE", "routingPreference": "TRAFFIC_AWARE_OPTIMAL", "departureTime": "2026-11-17T04:30:00Z"}
    r = urllib.request.Request("https://routes.googleapis.com/directions/v2:computeRoutes", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "X-Goog-Api-Key": key, "X-Goog-FieldMask": "routes.distanceMeters,routes.duration"})
    x = json.load(urllib.request.urlopen(r))["routes"][0]; return x["distanceMeters"], x["duration"]
# candidate boundaries from KML vertices (lat, lon), westbound order
B = eval(sys.argv[1])
hw, he = int(sys.argv[2]), int(sys.argv[3])   # headings westbound / eastbound
for i in range(len(B)-1):
    a, b = B[i], B[i+1]
    s = hv(a, b); w = leg(a, b, hw, hw); e = leg(b, a, he, he)
    print(f"{i+1}: straight {s:5.0f}  WB {w[0]:5d} ({w[0]/s:.2f}) {w[1]:>5s}   EB {e[0]:5d} ({e[0]/s:.2f}) {e[1]:>5s}")
