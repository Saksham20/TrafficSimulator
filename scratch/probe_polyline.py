import json, math, urllib.request
key = [l.split("=", 1)[1].strip() for l in open(".env") if l.startswith("GOOGLE")][0]
def decode(s):
    pts, i, lat, lng = [], 0, 0, 0
    while i < len(s):
        for k in range(2):
            shift = res = 0
            while True:
                b = ord(s[i]) - 63; i += 1; res |= (b & 0x1f) << shift; shift += 5
                if b < 0x20: break
            d = ~(res >> 1) if res & 1 else res >> 1
            if k == 0: lat += d
            else: lng += d
        pts.append((lat / 1e5, lng / 1e5))
    return pts
def hv(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    return 2*6371000*math.asin(math.sqrt(math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2))
def route(a, b):
    ll = lambda p: {"location": {"latLng": {"latitude": p[0], "longitude": p[1]}}}
    body = {"origin": ll(a), "destination": ll(b), "travelMode": "DRIVE", "routingPreference": "TRAFFIC_AWARE_OPTIMAL", "departureTime": "2026-11-17T04:30:00Z"}
    r = urllib.request.Request("https://routes.googleapis.com/directions/v2:computeRoutes", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "X-Goog-Api-Key": key, "X-Goog-FieldMask": "routes.polyline.encodedPolyline,routes.distanceMeters"})
    return decode(json.load(urllib.request.urlopen(r))["routes"][0]["polyline"]["encodedPolyline"])
L = {"B0 SV Metro":(12.98455,77.64529),"B1 CMH jn":(12.97852,77.64651),"B2 CMH/100ft":(12.97836,77.64082),
     "B3 Domlur fly start":(12.9628,77.6415),"B4 Domlur fly end":(12.9575,77.6412),"B5 Defence":(12.9497,77.6391),
     "B6 Ejipura jn":(12.9383,77.6329),"B7 Sony World":(12.9373,77.6269),"B8 St Johns/Sarjapur":(12.9274,77.62076),
     "B9 Madiwala":(12.92435,77.61797),"B10 Silk Board":(12.9172,77.6227)}
for name, (a, b) in [("SOUTH", (L["B0 SV Metro"], L["B10 Silk Board"])), ("NORTH", (L["B10 Silk Board"], L["B0 SV Metro"]))]:
    P = route(a, b)
    cum = [0]
    for i in range(1, len(P)): cum.append(cum[-1] + hv(P[i-1], P[i]))
    print(name, len(P), "pts", round(cum[-1]))
    for k, v in L.items():
        j = min(range(len(P)), key=lambda i: hv(P[i], v))
        print(f"  {k:22s} nearest {hv(P[j], v):5.0f} m  at {cum[j]:6.0f} m")
    json.dump(P, open(f"scratch/poly_{name}.json", "w"))
