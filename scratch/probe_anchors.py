"""Probe mid-block anchors with headings; compare Google leg distance to straight-line."""
import json, math, sys, urllib.request
key = [l.split("=", 1)[1].strip() for l in open(".env") if l.startswith("GOOGLE")][0]
A = [("start 80ft Rd", 12.9830, 77.6456), ("100ft Rd N", 12.9770, 77.6409), ("100ft Rd S", 12.9640, 77.6414),
     ("IRR Ejipura-Sony", 12.9384, 77.6310), ("Koramangala-St Johns", 12.93357, 77.62322), ("Silk Board", 12.9180, 77.6228)]
def hv(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[1], a[2], b[1], b[2]))
    return 2*6371000*math.asin(math.sqrt(math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2))
def brg(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[1], a[2], b[1], b[2]))
    y = math.sin(lo2-lo1)*math.cos(la2); x = math.cos(la1)*math.sin(la2)-math.sin(la1)*math.cos(la2)*math.cos(lo2-lo1)
    return int(math.degrees(math.atan2(y, x)) % 360)
def wp(seq, i):
    p = seq[i]; q = seq[i+1] if i+1 < len(seq) else seq[i-1]
    h = brg(p, q) if i+1 < len(seq) else (brg(q, p))
    return {"location": {"latLng": {"latitude": p[1], "longitude": p[2]}, "heading": h}}
for name, seq in [("SOUTH", A), ("NORTH", A[::-1])]:
    ws = [wp(seq, i) for i in range(len(seq))]
    body = {"origin": ws[0], "destination": ws[-1], "intermediates": ws[1:-1], "travelMode": "DRIVE",
            "routingPreference": "TRAFFIC_AWARE_OPTIMAL", "departureTime": sys.argv[1]}
    r = urllib.request.Request("https://routes.googleapis.com/directions/v2:computeRoutes", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "X-Goog-Api-Key": key,
                 "X-Goog-FieldMask": "routes.legs.distanceMeters,routes.legs.duration,routes.legs.staticDuration"})
    legs = json.load(urllib.request.urlopen(r))["routes"][0]["legs"]
    print(name)
    for i, l in enumerate(legs):
        d = l.get("distanceMeters", 0); s = hv(seq[i], seq[i+1])
        print(f"  {seq[i][0]:22s} -> {seq[i+1][0]:22s} straight {s:5.0f} google {d:5d} ratio {d/s:4.2f} t={l['duration']:>6s} static={l['staticDuration']}")
