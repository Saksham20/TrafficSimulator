import json, math, urllib.request
key = [l.split("=", 1)[1].strip() for l in open(".env") if l.startswith("GOOGLE")][0]
def hv(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    return 2*6371000*math.asin(math.sqrt(math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2))
def leg(a, b, ha, hb):
    ll = lambda p, h: {"location": {"latLng": {"latitude": p[0], "longitude": p[1]}, "heading": h}}
    body = {"origin": ll(a, ha), "destination": ll(b, hb), "travelMode": "DRIVE", "routingPreference": "TRAFFIC_AWARE_OPTIMAL", "departureTime": "2026-11-17T04:30:00Z"}
    r = urllib.request.Request("https://routes.googleapis.com/directions/v2:computeRoutes", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "X-Goog-Api-Key": key, "X-Goog-FieldMask": "routes.distanceMeters"})
    return json.load(urllib.request.urlopen(r))["routes"][0]["distanceMeters"]
# seg 7 SB: Ejipura -> Sony World (westbound along 12.938). left side = south (lat lower)
for off in [-0.00015, -0.00008, 0, 0.00008]:
    a=(12.93854+off, 77.63287); b=(12.93739+off, 77.62706)
    print("seg7 off", off, round(hv(a,b)), leg(a,b,270,250))
# seg 2 SB: CMH jn -> 100ft top; try via CMH Rd heading west then south
for off in [-0.00012, 0]:
    a=(12.97880, 77.64667); b=(12.97700+off*0, 77.64097)
    print("seg2", round(hv(a,b)), leg(a,b,180,180), leg(a,b,270,180))
