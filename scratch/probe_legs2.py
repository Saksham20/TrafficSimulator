"""Find via-points that force Google onto CMH Rd -> 100 Ft Rd (the DPR alignment) in both directions."""
import json, math, urllib.request
key = [l.split("=", 1)[1].strip() for l in open(".env") if l.startswith("GOOGLE")][0]
def hv(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    return 2*6371000*math.asin(math.sqrt(math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2))
def leg(a, b, t="2026-11-17T04:30:00Z"):
    ll = lambda p: {"location": {"latLng": {"latitude": p[0], "longitude": p[1]}}}
    body = {"origin": ll(a), "destination": ll(b), "travelMode": "DRIVE", "routingPreference": "TRAFFIC_AWARE_OPTIMAL", "departureTime": t}
    r = urllib.request.Request("https://routes.googleapis.com/directions/v2:computeRoutes", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "X-Goog-Api-Key": key, "X-Goog-FieldMask": "routes.distanceMeters,routes.duration"})
    x = json.load(urllib.request.urlopen(r))["routes"][0]; return x["distanceMeters"], x["duration"]
# candidate points along 80ft Rd, CMH Rd, 100ft Rd (KML-based, nudged)
C = {"80ft mid":(12.98150,77.64590), "CMH jn":(12.97852,77.64600), "CMH Rd mid":(12.97845,77.64350),
     "100ft top":(12.97780,77.64085), "100ft mid":(12.97153,77.64106), "100ft south":(12.96600,77.64135), "Domlur N":(12.96259,77.64165)}
seq = list(C.items())
for i in range(len(seq)-1):
    (na, a), (nb, b) = seq[i], seq[i+1]
    s = hv(a, b); f = leg(a, b); r = leg(b, a)
    print(f"{na:12s} -> {nb:12s} straight {s:5.0f}  S {f[0]:5d} ({f[0]/s:.2f})  N {r[0]:5d} ({r[0]/s:.2f})")
