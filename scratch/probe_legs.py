"""Per-segment Google times along the NORTH route line; check each leg ~ polyline distance."""
import json, math, urllib.request
key = [l.split("=", 1)[1].strip() for l in open(".env") if l.startswith("GOOGLE")][0]
def hv(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    return 2*6371000*math.asin(math.sqrt(math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2))
P = json.load(open("scratch/poly_NORTH.json"))[::-1]   # now OMR -> Silk Board order, northbound driving line
cum = [0]
for i in range(1, len(P)): cum.append(cum[-1] + hv(P[i-1], P[i]))
def at(m):
    j = min(range(len(P)), key=lambda i: abs(cum[i]-m)); return tuple(P[j]), cum[j]
bounds = [0, 670, 1290, 3130, 3670, 4630, 6340, 7010, 8320, 8800, 9765]   # chainage from OMR along northbound line
pts = [at(b) for b in bounds]
def leg(a, b, t):
    ll = lambda p: {"location": {"latLng": {"latitude": p[0], "longitude": p[1]}}}
    body = {"origin": ll(a), "destination": ll(b), "travelMode": "DRIVE", "routingPreference": "TRAFFIC_AWARE_OPTIMAL", "departureTime": t}
    r = urllib.request.Request("https://routes.googleapis.com/directions/v2:computeRoutes", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "X-Goog-Api-Key": key, "X-Goog-FieldMask": "routes.distanceMeters,routes.duration"})
    x = json.load(urllib.request.urlopen(r))["routes"][0]; return x["distanceMeters"], x["duration"]
for i in range(len(pts)-1):
    (a, ca), (b, cb) = pts[i], pts[i+1]
    exp = cb - ca
    dn = leg(b, a, "2026-11-17T04:30:00Z")   # northbound = drive from b to a
    print(f"seg {i+1}: {ca:5.0f}-{cb:5.0f} exp {exp:5.0f}  NB google {dn[0]:5d} ({dn[0]/exp:.2f}) {dn[1]}  pts {a} {b}")
