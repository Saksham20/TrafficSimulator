import json, math, urllib.request, sys
key = [l.split("=", 1)[1].strip() for l in open(".env") if l.startswith("GOOGLE")][0]
def hv(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    return 2*6371000*math.asin(math.sqrt(math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2))
def leg(a, b, head):
    ll = lambda p: {"location": {"latLng": {"latitude": p[0], "longitude": p[1]}, "heading": head}}
    body = {"origin": ll(a), "destination": ll(b), "travelMode": "DRIVE", "routingPreference": "TRAFFIC_AWARE_OPTIMAL", "departureTime": "2026-11-17T04:30:00Z"}
    r = urllib.request.Request("https://routes.googleapis.com/directions/v2:computeRoutes", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "X-Goog-Api-Key": key, "X-Goog-FieldMask": "routes.distanceMeters,routes.duration"})
    x = json.load(urllib.request.urlopen(r))["routes"][0]; return x["distanceMeters"]
# southbound on 100ft (heading 180) - try east/west offsets of carriageway
for lon_off in [-0.00012, -0.00006, 0, 0.00006, 0.00012]:
    a=(12.97153,77.64106+lon_off); b=(12.96600,77.64135+lon_off)
    print("100ft SB off",lon_off, hv(a,b), leg(a,b,180))
for lat_off in [-0.00012, -0.00006, 0, 0.00006, 0.00012]:
    a=(12.97845+lat_off,77.64350); b=(12.97845+lat_off,77.64150)
    print("CMH WB off",lat_off, hv(a,b), leg(a,b,270))
