import json, math, sys, urllib.request
key = [l.split("=", 1)[1].strip() for l in open(".env") if l.startswith("GOOGLE")][0]
def hv(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    return 2*6371000*math.asin(math.sqrt(math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2))
def brg(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    y = math.sin(lo2-lo1)*math.cos(la2); x = math.cos(la1)*math.sin(la2)-math.sin(la1)*math.cos(la2)*math.cos(lo2-lo1)
    return int(math.degrees(math.atan2(y, x)) % 360)
def go(a, b, head=True):
    o = {"location": {"latLng": {"latitude": a[0], "longitude": a[1]}}}
    d = {"location": {"latLng": {"latitude": b[0], "longitude": b[1]}}}
    if head: o["location"]["heading"] = brg(a, b); d["location"]["heading"] = brg(a, b)
    body = {"origin": o, "destination": d, "travelMode": "DRIVE", "routingPreference": "TRAFFIC_AWARE_OPTIMAL", "departureTime": "2026-11-16T21:30:00Z"}
    r = urllib.request.Request("https://routes.googleapis.com/directions/v2:computeRoutes", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "X-Goog-Api-Key": key, "X-Goog-FieldMask": "routes.distanceMeters"})
    return json.load(urllib.request.urlopen(r))["routes"][0]["distanceMeters"]
for a, b in eval(sys.argv[1]):
    s = hv(a, b); f = go(a, b); r = go(b, a)
    print(a, b, f"straight {s:5.0f}  fwd {f:5d} ({f/s:.2f})  rev {r:5d} ({r/s:.2f})")
