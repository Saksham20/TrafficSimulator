import json, math, urllib.request, sys
sys.path.insert(0, ".")
from segments_silk_board import GOOGLE_SB, GOOGLE_NB
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
for i in range(10):
    a, b = GOOGLE_SB[i], GOOGLE_SB[i+1]
    d, t = leg(a, b, a[2], b[2]); s = hv(a, b)
    na, nb = GOOGLE_NB[i+1], GOOGLE_NB[i]
    d2, t2 = leg(na, nb); s2 = hv(na, nb)
    print(f"seg {i+1:2d}  SB straight {s:5.0f} google {d:5d} ({d/s:.2f}) {t:>6s}   NB straight {s2:5.0f} google {d2:5d} ({d2/s2:.2f}) {t2:>6s}")
